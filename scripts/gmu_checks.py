#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Execute GPU component lifetime/error paths without hardware accesses."""
from pathlib import Path
import subprocess
import tempfile


FUNCTIONS = {
    'available': ('msm_gpu_devfreq.c', 'static bool has_devfreq('),
    'devfreq': ('msm_gpu_devfreq.c', 'void msm_devfreq_cleanup('),
    'preempt': ('adreno/a6xx_preempt.c', 'void a6xx_preempt_fini('),
    'bind': ('adreno/a6xx_gmu.c', 'static int a6xx_gmu_bind('),
    'unbind': ('adreno/adreno_device.c', 'static void adreno_unbind('),
}


def lifecycle_functions(source):
    root = Path(source) / 'drivers/gpu/drm/msm'
    result = {}
    for name, (path, signature) in FUNCTIONS.items():
        text = (root / path).read_text()
        start = text.index(signature)
        result[name] = text[start:text.index('\n}\n', start) + 3]
    return result


HARNESS = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define container_of(p, t, m) ((t *)((char *)(p) - offsetof(t, m)))
#define WARN_ON(x) ((x) ? (++warnings, true) : false)
#define WARN_ON_ONCE(x) ((void)WARN_ON(x))

struct device { void *data; bool pm_enabled; };
struct platform_device { struct device dev; };
struct mutex { bool initialized; };
struct timer_list { bool pending; };
struct drm_gem_object { int refs; };
struct vm { int pins; };
struct msm_gpu;
struct msm_gpu_funcs { void (*destroy)(struct msm_gpu *); };
struct msm_gpu_devfreq { void *devfreq; int boost_freq; };
struct msm_gpu {
    struct msm_gpu_devfreq devfreq;
    struct platform_device *pdev;
    const struct msm_gpu_funcs *funcs;
    struct vm *vm;
    void *cooling;
    int nr_rings;
};
struct adreno_gpu { struct msm_gpu base; };
struct a6xx_gmu { struct device *dev; struct mutex lock; bool initialized; };
struct a6xx_gpu {
    struct adreno_gpu base;
    struct a6xx_gmu gmu;
    struct timer_list preempt_timer;
    bool preempt_timer_initialized;
    struct drm_gem_object *preempt_bo[4], *preempt_smmu_bo[4];
    struct drm_gem_object *preempt_postamble_bo;
};
struct msm_drm_private { struct platform_device *gpu_pdev; };
static unsigned int cases, warnings, pm_enables, pm_disables, bind_calls;
static unsigned int idle_cancel, boost_cancel, cooling_remove, freq_remove;
static unsigned int qos_remove, opp_votes, destroyed, timer_stops;
static int bind_result;
static bool notifier_registered, gmu_destroyed;
static struct timer_list *active_timer;

struct adreno_gpu *to_adreno_gpu(struct msm_gpu *gpu)
{ return container_of(gpu, struct adreno_gpu, base); }
struct a6xx_gpu *to_a6xx_gpu(struct adreno_gpu *gpu)
{ return container_of(gpu, struct a6xx_gpu, base); }
struct msm_drm_private *msm_drm_get_priv(struct device *dev)
{ return dev->data; }
struct msm_gpu *dev_to_gpu(struct device *dev) { return dev->data; }
void mutex_init(struct mutex *lock) { lock->initialized = true; }
void pm_runtime_enable(struct device *dev)
{ assert(!dev->pm_enabled); dev->pm_enabled = true; ++pm_enables; }
void pm_runtime_disable(struct device *dev)
{ assert(dev->pm_enabled); dev->pm_enabled = false; ++pm_disables; }
bool pm_runtime_enabled(struct device *dev) { return dev->pm_enabled; }
int bind_resources(struct a6xx_gpu *gpu, struct device *dev)
{
    assert(gpu->gmu.dev == dev && gpu->gmu.lock.initialized);
    assert(dev->pm_enabled && !gpu->gmu.initialized);
    ++bind_calls;
    return bind_result;
}
void *of_device_get_match_data(struct device *dev)
{ (void)dev; return bind_resources; }
void timer_shutdown_sync(struct timer_list *timer)
{ timer->pending = false; ++timer_stops; }
void msm_gem_kernel_put(struct drm_gem_object *bo, struct vm *vm)
{
    if (!bo) return;
    assert(!active_timer->pending);
    assert(bo->refs == 1 && vm->pins > 0);
    --bo->refs;
    --vm->pins;
}
void cancel_idle_work(struct msm_gpu_devfreq *df)
{ (void)df; ++idle_cancel; }
void cancel_boost_work(struct msm_gpu_devfreq *df)
{ (void)df; ++boost_cancel; }
void devfreq_cooling_unregister(void *cooling)
{ assert(cooling); ++cooling_remove; }
void devm_devfreq_remove_device(struct device *dev, void *df)
{
    assert(dev && df && notifier_registered);
    notifier_registered = false;
    ++freq_remove;
}
void dev_pm_qos_remove_request(int *request)
{
    (void)request;
    /* A still-registered devfreq notifier can re-vote after GPU suspension. */
    if (notifier_registered) ++opp_votes;
    ++qos_remove;
}
int adreno_system_suspend(struct device *dev)
{
    (void)dev;
    /* GMU component unbind has already released its resources. */
    assert(!gmu_destroyed);
    return 0;
}
void destroy_gpu(struct msm_gpu *gpu) { (void)gpu; ++destroyed; }

ACTUAL_FUNCTIONS

static void check_preempt(void)
{
    for (unsigned int count = 0; count <= 9; ++count) {
        struct a6xx_gpu a = {0};
        struct drm_gem_object bos[9] = {0};
        struct vm vm = {0};
        struct msm_gpu *gpu = &a.base.base;
        gpu->vm = &vm;
        gpu->nr_rings = 4;
        active_timer = &a.preempt_timer;
        timer_stops = 0;
        for (unsigned int i = 0; i < count; ++i) {
            bos[i].refs = 1;
            ++vm.pins;
            if (i == 8) a.preempt_postamble_bo = &bos[i];
            else if (i & 1) a.preempt_smmu_bo[i / 2] = &bos[i];
            else a.preempt_bo[i / 2] = &bos[i];
        }
        if (count == 9) {
            a.preempt_timer_initialized = true;
            a.preempt_timer.pending = true;
            /* A fallback may reduce nr_rings after an earlier init failure. */
            gpu->nr_rings = 1;
        }
        a6xx_preempt_fini(gpu);
        assert(vm.pins == 0 && !a.preempt_timer_initialized);
        assert(timer_stops == (count == 9));
        for (unsigned int i = 0; i < ARRAY_SIZE(bos); ++i)
            assert(bos[i].refs == 0);
        a6xx_preempt_fini(gpu);
        assert(vm.pins == 0 && timer_stops == (count == 9));
        ++cases;
    }
}

static void check_devfreq(void)
{
    for (unsigned int present = 0; present < 2; ++present) {
        struct platform_device pdev = {0};
        struct msm_gpu gpu = {.pdev = &pdev, .cooling = &pdev};
        idle_cancel = boost_cancel = cooling_remove = freq_remove = 0;
        qos_remove = opp_votes = 0;
        notifier_registered = present;
        if (present) gpu.devfreq.devfreq = &pdev;
        msm_devfreq_cleanup(&gpu);
        assert(!gpu.devfreq.devfreq && !notifier_registered && !opp_votes);
        assert(idle_cancel == present && boost_cancel == present);
        assert(cooling_remove == present && freq_remove == present);
        assert(qos_remove == present);
        /* Cleanup may run again after a failed component-master bind. */
        msm_devfreq_cleanup(&gpu);
        assert(qos_remove == present && freq_remove == present);
        ++cases;
    }
}

static void check_bind(void)
{
    const int errors[] = {0, -517, -ENOMEM, -ENODEV, -EIO};
    for (unsigned int i = 0; i < ARRAY_SIZE(errors); ++i) {
        struct a6xx_gpu a = {0};
        struct device dev = {0};
        struct platform_device pdev = {.dev = {.data = &a.base.base}};
        struct msm_drm_private priv = {.gpu_pdev = &pdev};
        struct device master = {.data = &priv};
        pm_enables = pm_disables = bind_calls = 0;
        bind_result = errors[i];
        assert(a6xx_gmu_bind(&dev, &master, NULL) == errors[i]);
        assert(pm_enables == 1 && bind_calls == 1);
        assert(a.gmu.initialized == !errors[i]);
        assert(dev.pm_enabled == !errors[i]);
        if (errors[i]) {
            assert(pm_disables == 1);
            /* A deferred probe must leave PM balanced before retrying. */
            bind_result = 0;
            assert(a6xx_gmu_bind(&dev, &master, NULL) == 0);
            assert(pm_enables == 2 && pm_disables == 1);
            assert(a.gmu.initialized && dev.pm_enabled);
        }
        pm_runtime_disable(&dev);
        assert(pm_enables == pm_disables);
        ++cases;
    }
    struct device dev = {0};
    struct platform_device pdev = {0};
    struct msm_drm_private priv = {.gpu_pdev = &pdev};
    struct device master = {.data = &priv};
    pm_enables = pm_disables = bind_calls = warnings = 0;
    assert(a6xx_gmu_bind(&dev, &master, NULL) == -ENODEV);
    assert(warnings == 1 && !pm_enables && !pm_disables && !bind_calls);
    ++cases;
}

static void check_unbind(void)
{
    const struct msm_gpu_funcs funcs = {.destroy = destroy_gpu};
    for (unsigned int enabled = 0; enabled < 2; ++enabled) {
        struct msm_gpu gpu = {.funcs = &funcs};
        struct platform_device pdev = {.dev = {.data = &gpu}};
        struct msm_drm_private priv = {.gpu_pdev = &pdev};
        struct device master = {.data = &priv};
        pdev.dev.pm_enabled = enabled;
        gmu_destroyed = true;
        destroyed = 0;
        adreno_unbind(&pdev.dev, &master, NULL);
        assert(destroyed == 1 && !priv.gpu_pdev);
        ++cases;
    }
}

int main(void)
{
    check_preempt();
    check_devfreq();
    check_bind();
    check_unbind();
    printf("GMU lifecycle: %u resource/error cases passed\n", cases);
    return 0;
}
'''


def execute_lifecycle_functions(functions):
    actual = '\n'.join(functions[name] for name in FUNCTIONS)
    harness = HARNESS.replace('ACTUAL_FUNCTIONS', actual)
    with tempfile.TemporaryDirectory(prefix='tb522fu-gmu-check-') as directory:
        c = Path(directory) / 'check.c'
        binary = Path(directory) / 'check'
        c.write_text(harness)
        subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                        '-Wno-unused-parameter', str(c), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


def check_gmu_lifecycle(source):
    execute_lifecycle_functions(lifecycle_functions(source))
