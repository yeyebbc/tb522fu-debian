#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Exercise real PM noirq entry/unwind code with wake IRQ accounting oracles."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile


def function(text, signature):
    start = text.index(signature)
    opening = text.index('{', start)
    end, depth = opening + 1, 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


def check(source):
    text = (source / 'drivers/base/power/main.c').read_text()
    functions = '\n'.join((
        'static bool dpm_wake_irqs_armed;' if 'static bool dpm_wake_irqs_armed;' in text else '',
        function(text, 'void dpm_resume_noirq('),
        function(text, 'int dpm_suspend_noirq('),
    ))
    prefix = r'''
#include <assert.h>
#include <stdbool.h>
#include <errno.h>
enum { PM_EVENT_FREEZE, PM_EVENT_QUIESCE, PM_EVENT_SUSPEND,
       PM_EVENT_HIBERNATE, PM_EVENT_THAW, PM_EVENT_RESTORE, PM_EVENT_RECOVER };
typedef struct { int event; } pm_message_t;
static int arms, disarms, disabled, resumed, error;
static void device_wakeup_arm_wake_irqs(void) { arms++; }
static void device_wakeup_disarm_wake_irqs(void) { disarms++; }
static void suspend_device_irqs(void) { disabled++; }
static void resume_device_irqs(void) { resumed++; }
static int dpm_noirq_suspend_devices(pm_message_t state)
{ (void)state; return error; }
static void dpm_noirq_resume_devices(pm_message_t state) { (void)state; }
static pm_message_t resume_event(pm_message_t state)
{ (void)state; return (pm_message_t){PM_EVENT_RECOVER}; }
'''
    main = r'''
static void cycle(int event, int completion, int expected_arms, int failure)
{
    int a=arms, d=disarms, s=disabled, r=resumed;
    error=failure;
    assert(dpm_suspend_noirq((pm_message_t){event}) == failure);
    if (!failure)
        dpm_resume_noirq((pm_message_t){completion});
    assert(arms-a == expected_arms && disarms-d == expected_arms);
    assert(disabled-s == 1 && resumed-r == 1);
    assert(arms == disarms);
}
int main(void)
{
    /* Snapshot, restore, and failures must not create false wake events. */
    cycle(PM_EVENT_FREEZE, PM_EVENT_THAW, 0, 0);
    cycle(PM_EVENT_QUIESCE, PM_EVENT_RESTORE, 0, 0);
    cycle(PM_EVENT_FREEZE, PM_EVENT_RECOVER, 0, -EIO);
    cycle(PM_EVENT_QUIESCE, PM_EVENT_RECOVER, 0, -EIO);
    /* Real sleep/final poweroff retain wake IRQs and balanced error cleanup. */
    cycle(PM_EVENT_SUSPEND, PM_EVENT_RESTORE, 1, 0);
    cycle(PM_EVENT_HIBERNATE, PM_EVENT_RESTORE, 1, 0);
    cycle(PM_EVENT_SUSPEND, PM_EVENT_RECOVER, 1, -EIO);
    cycle(PM_EVENT_HIBERNATE, PM_EVENT_RECOVER, 1, -EIO);
    /* A subsequent snapshot must not inherit a previous sleep's armed flag. */
    cycle(PM_EVENT_FREEZE, PM_EVENT_THAW, 0, 0);
    cycle(PM_EVENT_QUIESCE, PM_EVENT_RECOVER, 0, -EIO);
    return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix='hibernation-wake-irqs-') as directory:
        directory = Path(directory)
        source_file = directory / 'check.c'
        source_file.write_text(prefix + functions + main)
        binary = directory / 'check'
        subprocess.run([os.environ.get('HOSTCC', 'cc'), '-std=c11', '-Wall',
                        '-Wextra', '-Werror', str(source_file), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    print('Hibernation wake IRQ and error-unwind checks passed')


if __name__ == '__main__':
    check(Path(sys.argv[1]))
