#!/usr/bin/env python3
"""Exercise the kernel's actual frequency calculation with independent radio fixtures."""
from pathlib import Path
import argparse, subprocess, tempfile

p = argparse.ArgumentParser()
p.add_argument('kernel', type=Path)
a = p.parse_args()
base = a.kernel / 'drivers/net/wireless/ath/ath12k'
reg = (base / 'reg.c').read_text().split('int ath12k_regd_update(', 1)[1]
calc = reg[reg.index('\treg_cap = &ab->hal_reg_cap[ar->pdev_idx];'):reg.index('\t/* If one of the radios')]
mac = (base / 'mac.c').read_text()
update = mac[mac.index('void ath12k_mac_update_freq_range('):mac.index('static void ath12k_mac_update_ch_list(')]
pre = r'''
#include <stdbool.h>
#include <stdint.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef uint32_t u32;
#define NL80211_BAND_2GHZ 0
#define NL80211_BAND_5GHZ 1
#define NL80211_BAND_6GHZ 3
#define WMI_HOST_WLAN_2GHZ_CAP 1
#define WMI_HOST_WLAN_5GHZ_CAP 2
#define MHZ_TO_KHZ(x) ((x)*1000)
#define KHZ_TO_MHZ(x) ((x)/1000)
#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))
#define ath12k_dbg(...) ((void)0)
struct ath12k_reg_freq { u32 start_freq, end_freq; };
struct ath12k_wmi_hal_reg_capabilities_ext_arg {u32 low_2ghz_chan, high_2ghz_chan, low_5ghz_chan, high_5ghz_chan;};
struct ath12k_pdev { struct {struct {u32 phy_id;} band[4];u32 supported_bands;} cap; struct ath12k_reg_freq reg_freq_2ghz,reg_freq_5ghz,reg_freq_6ghz; };
struct ath12k_base { struct {bool single_pdev_only;} *hw_params; struct ath12k_wmi_hal_reg_capabilities_ext_arg hal_reg_cap[4]; };
struct ath12k { struct ath12k_base *ab;struct ath12k_pdev *pdev;u32 pdev_idx;bool supports_6ghz;struct {struct {void *channels;} sbands[4];} mac;struct ath12k_reg_freq freq_range; };
'''
body = r'''
static void compute(struct ath12k *ar) {
 struct ath12k_base *ab=ar->ab;
 struct ath12k_pdev *pdev=ar->pdev;
 struct ath12k_wmi_hal_reg_capabilities_ext_arg *reg_cap;
 u32 phy_id,freq_low,freq_high;
CALC
}
static void check(struct ath12k *ar,u32 low,u32 high) {
 compute(ar); assert(ar->freq_range.start_freq==low*1000);assert(ar->freq_range.end_freq==high*1000);
}
int main(void) {
 struct ath12k_base ab={0}; typeof(*ab.hw_params) hw={.single_pdev_only=true}; ab.hw_params=&hw;
 struct ath12k_pdev p={0};struct ath12k ar={.ab=&ab,.pdev=&p,.supports_6ghz=true};
 p.cap.band[0].phy_id=1;p.cap.band[1].phy_id=2;p.cap.supported_bands=3;
 ab.hal_reg_cap[1]=(struct ath12k_wmi_hal_reg_capabilities_ext_arg){2300,2500,0,0};
 ab.hal_reg_cap[2]=(struct ath12k_wmi_hal_reg_capabilities_ext_arg){0,0,4900,7125};
 ar.mac.sbands[0].channels=&p;ar.mac.sbands[1].channels=&p;ar.mac.sbands[3].channels=&p;
 p.reg_freq_2ghz=(struct ath12k_reg_freq){2402,2482};
 p.reg_freq_5ghz=(struct ath12k_reg_freq){5170,5835};
 p.reg_freq_6ghz=(struct ath12k_reg_freq){INT32_MAX,0};
 check(&ar,2402,5835); /* CN: 6 GHz hardware must not erase legal 5 GHz. */
 p.reg_freq_6ghz=(struct ath12k_reg_freq){5945,7125};check(&ar,2402,7125);
 /* Country update removes 6 GHz again; stale upper limit must be reset. */
 p.reg_freq_6ghz.end_freq=0;check(&ar,2402,5835);
 /* Split 6 GHz radio receives rules for all bands but owns only 6 GHz. */
 hw.single_pdev_only=false;ar.pdev_idx=2;ar.mac.sbands[0].channels=NULL;ar.mac.sbands[1].channels=NULL;
 p.reg_freq_6ghz=(struct ath12k_reg_freq){5945,7125};check(&ar,5945,7125);
 /* Split 5 GHz radio must not inherit the 6 GHz rule span. */
 ar.mac.sbands[3].channels=NULL;ar.mac.sbands[1].channels=&p;check(&ar,5170,5835);
 puts("PASS: single-radio CN/US ranges, country reset, split radios and band indices");
}
'''.replace('CALC', calc)
with tempfile.TemporaryDirectory() as tmp:
    src = Path(tmp) / 'ranges.c'
    src.write_text(pre + update + body)
    exe = Path(tmp) / 'ranges'
    subprocess.run(['cc', '-std=gnu11', '-O2', '-Wall', '-Wextra', '-Werror', str(src), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
