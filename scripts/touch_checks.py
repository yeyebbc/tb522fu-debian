#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Execute touch SPI ordering against the actual DRM panel lifecycle."""
from pathlib import Path
import re
import subprocess
import tempfile


def function(text, signature):
    match = re.search(r'^' + re.escape(signature) + r'[^;{}]*\n\{', text, re.MULTILINE)
    assert match, 'Missing function definition: ' + signature
    start = match.start()
    return text[start:text.index('\n}\n', start) + 3]


def lifecycle_source(source, touch_text=None):
    root = Path(source)
    touch = touch_text if touch_text is not None else (root / 'drivers/input/touchscreen/nt36536/nt36536.c').read_text()
    panel = (root / 'drivers/gpu/drm/drm_panel.c').read_text()
    start = touch.index('static struct drm_panel_follower_funcs nt36536_panel_follower_funcs =')
    table = touch[start:touch.index('\n};', start) + 3]
    callbacks = re.findall(r'\.panel_\w+\s*=\s*(\w+)', table)
    names = [('static bool ', 'nvt_panel_resume_allowed'), ('static bool ', 'nvt_panel_is_on'),
             ('static void ', 'nvt_set_touch_awake_state'), ('static bool ', 'nvt_commit_follower_awake'),
             ('static int32_t ', 'nvt_ts_suspend'), ('static int32_t ', 'nvt_ts_resume'),
             ('static void ', 'nvt_resume_work')]
    parts = [function(touch, prefix + name + '(') for prefix, name in names]
    parts += [function(touch, 'static int ' + name + '(') for name in callbacks]
    parts.append(table)
    parts += [function(panel, 'void ' + name + '(') for name in
              ('drm_panel_prepare', 'drm_panel_unprepare', 'drm_panel_enable', 'drm_panel_disable')]
    parts += [function(panel, 'int drm_panel_add_follower('), function(panel, 'void drm_panel_remove_follower(')]
    return '\n'.join(parts)


HARNESS = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define container_of(p,t,m) ((t *)((char *)(p)-offsetof(t,m)))
#define READ_ONCE(x) (x)
#define likely(x) (x)
#define NVT_LOG(...) ((void)0)
#define NVT_ERR(...) ((void)0)
#define dev_warn(...) ((void)0)
#define dev_info(...) ((void)0)
#define DRM_DEV_INFO(...) ((void)0)
#define NVT_TOUCH_ESD_PROTECT 0
#define MT_PROTOCOL_B 0
#define EVENT_MAP_HOST_CMD 0x50
#define BTN_TOUCH 0
#define IS_ERR(p) (false)
#define PTR_ERR(p) (-ENODEV)
struct mutex { int held; };
static void mutex_lock(struct mutex *m) { assert(!m->held); m->held=1; }
static void mutex_unlock(struct mutex *m) { assert(m->held); m->held=0; }
#define spin_lock_irqsave(p,f) do { (void)(p); (f)=0; } while (0)
#define spin_unlock_irqrestore(p,f) do { (void)(p); (void)(f); } while (0)
struct list_head { struct list_head *next,*prev; };
static void init_list(struct list_head *h) { h->next=h->prev=h; }
static void list_add_tail(struct list_head *n,struct list_head *h) {
 n->prev=h->prev; n->next=h; h->prev->next=n; h->prev=n;
}
static void list_del_init(struct list_head *n) { n->prev->next=n->next; n->next->prev=n->prev; init_list(n); }
#define list_for_each_entry(p,h,m) \
 for(struct list_head *it=(h)->next; it!=(h) && ((p)=container_of(it,__typeof__(*(p)),m),1); it=it->next)
struct device { int refs; };
struct spi_device { struct device dev; int irq; };
struct work_struct { void (*run)(struct work_struct *); bool pending; };
struct drm_panel;
struct drm_panel_follower;
struct drm_panel_follower_funcs {
 int (*panel_prepared)(struct drm_panel_follower *);
 int (*panel_unpreparing)(struct drm_panel_follower *);
 int (*panel_enabled)(struct drm_panel_follower *);
 int (*panel_disabling)(struct drm_panel_follower *);
};
struct drm_panel_follower {
 struct drm_panel *panel; struct list_head list;
 struct drm_panel_follower_funcs *funcs;
};
struct drm_panel_funcs {
 int (*prepare)(struct drm_panel *); int (*unprepare)(struct drm_panel *);
 int (*enable)(struct drm_panel *); int (*disable)(struct drm_panel *);
};
struct drm_panel {
 bool prepared,enabled; struct device *dev; void *backlight;
 struct drm_panel_funcs *funcs; struct mutex follower_lock; struct list_head followers;
};
enum { NVT_IC_SUSPEND_IN,NVT_IC_SUSPEND_OUT,NVT_IC_RESUME_IN,NVT_IC_RESUME_OUT };
struct nvt_ts_data {
 struct drm_panel_follower panel_follower; struct spi_device *client;
 struct work_struct resume_work; void *event_wq; struct mutex lock;
 int lifecycle_lock,ic_state,gesture_command_delayed,resume_count;
 bool touch_awake,is_panel_follower,resources_ready,panel_on,stopping;
 bool dev_pm_suspend,irq_requested,irq_enabled,db_wakeup,pen_input_dev_enable,chip_identified;
 const char *fw_name; void *input_dev;
};
static struct nvt_ts_data data,*ts=&data;
static struct spi_device spi;
static struct drm_panel panel;
static struct device panel_dev;
static bool powered,initialized,accepting,fail_prepare,fail_enable,fail_disable,fail_firmware,defer_work;
static int downloads,early_downloads,sleep_writes,late_sleep_writes,wake_refs,cancels;
static unsigned int waited;
static void pm_stay_awake(struct device *d) { (void)d; wake_refs++; }
static void pm_relax(struct device *d) { (void)d; assert(wake_refs); wake_refs--; }
static void nvt_irq_enable(bool on) { ts->irq_enabled=on; }
static void enable_irq_wake(int irq) { (void)irq; }
static void msleep(unsigned int ms) { waited+=ms; }
static int nvt_ts_check_chip_ver_trim(void) { return 0; }
static int nvt_update_firmware_no_eng_reset(const char *name) {
 (void)name; downloads++;
 if (!initialized) { early_downloads++; return -EHOSTDOWN; }
 return fail_firmware ? -EIO : 0;
}
static int nvt_update_firmware(const char *name) { (void)name; assert(false); return -EIO; }
static int __nvt_set_pen_state(bool on) { (void)on; return 0; }
static void nvt_restore_pen_scan(void) {}
static void release_pen_event(void) {}
static void input_report_key(void *dev,int key,int value) { (void)dev; (void)key; (void)value; }
static void input_mt_sync(void *dev) { (void)dev; }
static void input_sync(void *dev) { (void)dev; }
static int CTP_SPI_WRITE(struct spi_device *dev,uint8_t *buf,int count) {
 (void)dev; assert(count==2 && buf[0]==0x50 && buf[1]==0x11);
 sleep_writes++;
 if (!accepting) { late_sleep_writes++; return -EHOSTDOWN; }
 return 0;
}
static bool queue_work(void *queue,struct work_struct *work) {
 assert(queue); work->pending=true;
 if (!defer_work) { work->pending=false; work->run(work); }
 return true;
}
static void cancel_work_sync(struct work_struct *work) { work->pending=false; cancels++; }
static int backlight_enable(void *bl) { (void)bl; return 0; }
static int backlight_disable(void *bl) { (void)bl; return 0; }
static struct drm_panel *find_panel_by_dev(struct device *dev) { (void)dev; return &panel; }
static void get_device(struct device *dev) { dev->refs++; }
static void put_device(struct device *dev) { assert(dev->refs); dev->refs--; }
static void drm_panel_put(struct drm_panel *p) { (void)p; }
ACTUAL_SOURCE
static int prepare(struct drm_panel *p) { (void)p; if(fail_prepare)return -EIO; powered=true; return 0; }
static int enable(struct drm_panel *p) { (void)p; assert(powered); if(fail_enable)return -EIO; initialized=accepting=true; return 0; }
static int disable(struct drm_panel *p) { (void)p; if(fail_disable)return -EIO; initialized=accepting=false; return 0; }
static int unprepare(struct drm_panel *p) { (void)p; powered=false; return 0; }
static struct drm_panel_funcs panel_ops={ .prepare=prepare,.unprepare=unprepare,.enable=enable,.disable=disable };
static void setup(void) {
 memset(&data,0,sizeof(data)); memset(&panel,0,sizeof(panel)); memset(&panel_dev,0,sizeof(panel_dev));
 powered=initialized=accepting=fail_prepare=fail_enable=fail_disable=fail_firmware=defer_work=false;
 downloads=early_downloads=sleep_writes=late_sleep_writes=wake_refs=cancels=0; waited=0;
 panel.dev=&panel_dev; panel.funcs=&panel_ops; init_list(&panel.followers);
 data.client=&spi; data.event_wq=&data; data.resources_ready=data.is_panel_follower=data.irq_requested=true;
 data.chip_identified=true; data.gesture_command_delayed=-1; data.resume_work.run=nvt_resume_work;
 data.panel_follower.funcs=&nt36536_panel_follower_funcs;
 assert(drm_panel_add_follower(&spi.dev,&data.panel_follower)==0);
}
static void clean(void) {
 drm_panel_remove_follower(&data.panel_follower);
 assert(!panel_dev.refs && !panel.follower_lock.held && !data.lock.held && !wake_refs);
 assert(!data.resume_work.pending && !data.touch_awake && !data.irq_enabled);
}
static int contract(bool condition,const char *name) { if(!condition){fprintf(stderr,"touch phase violation: %s\n",name);return 1;}return 0; }
int main(void) {
 setup();
 for(int cycle=0;cycle<3;cycle++) {
  drm_panel_prepare(&panel);
  if(contract(downloads==cycle && !data.touch_awake,"firmware before panel initialization"))return 1;
  drm_panel_enable(&panel);
  if(contract(downloads==cycle+1 && data.touch_awake && data.irq_enabled,"touch unavailable after enable"))return 1;
  drm_panel_disable(&panel);
  if(contract(sleep_writes==cycle+1 && !late_sleep_writes,"sleep command after panel/DSI disable"))return 1;
  drm_panel_unprepare(&panel);
 }
 clean();
 setup(); fail_enable=true; drm_panel_prepare(&panel); drm_panel_enable(&panel);
 assert(!downloads && !data.touch_awake && !data.irq_enabled);
 fail_enable=false; drm_panel_enable(&panel); assert(downloads==1 && data.touch_awake); clean();
 setup(); fail_prepare=true; drm_panel_prepare(&panel); assert(!panel.prepared && !downloads); clean();
 setup(); drm_panel_prepare(&panel); drm_panel_enable(&panel); fail_disable=true; drm_panel_disable(&panel);
 assert(panel.enabled && !data.touch_awake && sleep_writes==1); fail_disable=false; drm_panel_disable(&panel);
 assert(sleep_writes==1 && !late_sleep_writes); clean();
 setup(); fail_firmware=true; drm_panel_prepare(&panel); drm_panel_enable(&panel);
 assert(downloads==1 && !data.touch_awake && !data.irq_enabled && !wake_refs); clean();
 setup(); defer_work=true; drm_panel_prepare(&panel); drm_panel_enable(&panel);
 assert(data.resume_work.pending && !downloads); drm_panel_disable(&panel);
 assert(!data.resume_work.pending && !downloads); clean();
 setup(); data.resources_ready=false; drm_panel_prepare(&panel); drm_panel_enable(&panel);
 assert(!downloads && !data.resume_work.pending); clean();
 setup(); data.stopping=true; drm_panel_prepare(&panel); drm_panel_enable(&panel);
 assert(!downloads && !data.resume_work.pending); clean();
 setup(); drm_panel_prepare(&panel); drm_panel_enable(&panel); clean();
 assert(panel.enabled && sleep_writes==1 && !late_sleep_writes);
 data.resources_ready=true; data.stopping=false; assert(drm_panel_add_follower(&spi.dev,&data.panel_follower)==0);
 assert(downloads==2 && data.touch_awake && data.irq_enabled); clean();
 puts("touch panel lifecycle: repeated wake, failed enable/prepare/disable/firmware, deferred work, stop and hot attach/removal passed");
 return 0;
}
'''


def check_touch_panel_lifecycle(source, touch_text=None):
    actual = lifecycle_source(source, touch_text)
    with tempfile.TemporaryDirectory(prefix='tb522fu-touch-check-') as directory:
        c = Path(directory) / 'check.c'
        binary = Path(directory) / 'check'
        c.write_text(HARNESS.replace('ACTUAL_SOURCE', actual))
        subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', str(c), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
