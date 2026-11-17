#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Exercise the actual bus-walk and DWC functions against power/wakeup oracles."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile


def function(text, signature):
    start = text.index(signature)
    opening = text.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


def check(source):
    common = (source / 'drivers/pci/controller/pci-host-common.c').read_text()
    dwc = (source / 'drivers/pci/controller/dwc/pcie-designware-host.c').read_text()
    functions = '\n'.join((
        function(common, 'static int __pci_host_common_d3cold_possible('),
        function(common, 'bool pci_host_common_d3cold_possible('),
        function(dwc, 'int dw_pcie_suspend_noirq('),
    ))
    prefix = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <errno.h>
typedef uint32_t u32;
enum { PCI_D0, PCI_D3hot, PCI_D3cold };
#define PCI_HOST_D3COLD_ALLOWED 1
#define PCI_HOST_PME_D3COLD_CAPABLE 2
#define DW_PCIE_LTSSM_L2_IDLE 0x15
#define DW_PCIE_LTSSM_DETECT_WAIT 1
#define PCIE_PME_TO_L2_TIMEOUT_US 10000
struct device { void *driver; bool wake; };
struct pci_dev { struct device dev; bool enabled, pme; int current_state; };
struct pci_bus { struct pci_dev *devices; unsigned count; };
struct pci_host_bridge { struct pci_bus *bus; };
struct dw_pcie_rp;
struct ops { void (*pme_turn_off)(struct dw_pcie_rp *);
             void (*deinit)(struct dw_pcie_rp *); };
struct dw_pcie_rp { struct pci_host_bridge *bridge; struct ops *ops;
                    bool skip_l23_ready, skip_pwrctrl_off; };
struct dw_pcie { struct dw_pcie_rp pp; struct device *dev;
                 bool suspended, link; };
static int visits, stopped, deinitialized, pme_calls, pme_error;
static bool pci_is_enabled(struct pci_dev *p) { return p->enabled; }
static bool device_may_wakeup(struct device *d) { return d->wake; }
static bool pci_pme_capable(struct pci_dev *p, int state)
{ assert(state == PCI_D3cold); return p->pme; }
static void pci_walk_bus(struct pci_bus *b,
                         int (*visit)(struct pci_dev *, void *), void *v)
{ for (unsigned i=0; i<b->count; i++) { visits++; if (visit(b->devices+i,v)) break; } }
static bool dw_pcie_link_up(struct dw_pcie *p) { return p->link; }
static int dw_pcie_pme_turn_off(struct dw_pcie *p)
{ (void)p; pme_calls++; return pme_error; }
static u32 dw_pcie_get_ltssm(struct dw_pcie *p)
{ (void)p; return DW_PCIE_LTSSM_L2_IDLE; }
static void dw_pcie_stop_link(struct dw_pcie *p) { (void)p; stopped++; }
static void deinit(struct dw_pcie_rp *p) { (void)p; deinitialized++; }
#define mdelay(t) ((void)(t))
#define udelay(t) ((void)(t))
#define dev_warn(...) ((void)0)
#define read_poll_timeout(op,val,condition,...) ((val=op(pci)), (condition) ? 0 : -ETIMEDOUT)
'''
    main = r'''
int main(void)
{
    /* A D0 endpoint must not hide a later wake-capable endpoint. */
    struct pci_dev devices[] = {
      {{(void*)1, false}, true, false, PCI_D0},
      {{(void*)1, true}, true, true, PCI_D3hot},
    };
    struct pci_bus bus = {devices, 2};
    struct pci_host_bridge bridge = {&bus};
    bool pme = false;
    assert(!pci_host_common_d3cold_possible(&bridge, &pme));
    assert(pme && visits == 2);
    struct ops ops = {.deinit=deinit};
    struct dw_pcie pci = {.pp={.bridge=&bridge, .ops=&ops}, .link=true};
    /* Ordinary suspend must keep a D0 endpoint's controller running. */
    assert(!dw_pcie_suspend_noirq(&pci, false));
    assert(!pci.suspended && !stopped && !deinitialized && !pme_calls);
    /* Forced freeze must shut it down while preserving auxiliary wake power. */
    assert(!dw_pcie_suspend_noirq(&pci, true));
    assert(pci.suspended && stopped==1 && deinitialized==1 && pme_calls==1);
    assert(pci.pp.skip_pwrctrl_off);
    /* A failed link shutdown must not be recorded as a suspended controller. */
    pci.suspended=false; stopped=deinitialized=0; pme_error=-EIO;
    assert(dw_pcie_suspend_noirq(&pci, true)==-EIO);
    assert(!pci.suspended && !stopped && !deinitialized);
    /* A sleeping, non-wake endpoint permits the existing suspend path. */
    pme_error=0; devices[0].current_state=PCI_D3hot; devices[1].dev.wake=false;
    assert(!dw_pcie_suspend_noirq(&pci, false));
    assert(pci.suspended && !pci.pp.skip_pwrctrl_off);
    /* A wake-enabled endpoint without D3cold PME still vetoes normal suspend. */
    devices[1].dev.wake=true; devices[1].pme=false; pme=false;
    assert(!pci_host_common_d3cold_possible(&bridge, &pme) && !pme);
    return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix='pci-hibernation-') as directory:
        directory = Path(directory)
        source_file = directory / 'check.c'
        source_file.write_text(prefix + functions + main)
        binary = directory / 'check'
        subprocess.run([os.environ.get('HOSTCC', 'cc'), '-std=c11', '-Wall',
                        '-Wextra', '-Werror', str(source_file), '-o', str(binary)],
                       check=True)
        subprocess.run([str(binary)], check=True)
    print('PCI hibernation power/wakeup checks passed')


if __name__ == '__main__':
    check(Path(sys.argv[1]))
