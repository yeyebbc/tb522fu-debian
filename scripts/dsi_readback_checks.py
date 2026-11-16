#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Run actual DSI transfer functions against targeted-read/broadcast-write cases."""
from pathlib import Path
import subprocess
import tempfile

from panel_readback_checks import function


def check_dsi_readback(source, host_text=None, manager_text=None):
    root = Path(source) / 'drivers/gpu/drm/msm/dsi'
    host = (root / 'dsi_host.c').read_text() if host_text is None else host_text
    manager = ((root / 'dsi_manager.c').read_text()
               if manager_text is None else manager_text)
    actual = '\n'.join([
        function(manager, 'bool msm_dsi_manager_cmd_xfer_trigger('),
        *(function(host, name) for name in (
            'static int dsi_cmd_dma_tx(', 'static int dsi_cmds2buf_tx(',
            'int msm_dsi_host_cmd_tx(', 'int msm_dsi_host_cmd_rx(')),
        function(manager, 'int msm_dsi_manager_cmd_xfer('),
    ])
    with tempfile.TemporaryDirectory(prefix='tb522fu-dsi-readback-') as directory:
        c = Path(directory) / 'check.c'
        binary = Path(directory) / 'check'
        c.write_text(HARNESS.replace('ACTUAL_SOURCE', actual))
        # Kernel message lengths are unsigned; retain the kernel's comparison policy.
        subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                        '-Wno-sign-compare', str(c), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


HARNESS = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef uint8_t u8;
typedef uint32_t u32;
#define DSI_0 0
#define IS_SYNC_NEEDED() sync_needed
#define MIPI_DSI_MODE_VIDEO 1
#define MSM_DSI_VER_MAJOR_6G 6
#define MSM_DSI_6G_VER_MINOR_V1_1 1
#define REG_DSI_RDBK_DATA_CTRL 1
#define DSI_RDBK_DATA_CTRL_CLR 1
#define MIPI_DSI_SET_MAXIMUM_RETURN_PACKET_SIZE 0x37
#define MIPI_DSI_RX_ACKNOWLEDGE_AND_ERROR_REPORT 0x02
#define MIPI_DSI_RX_GENERIC_SHORT_READ_RESPONSE_1BYTE 0x11
#define MIPI_DSI_RX_GENERIC_SHORT_READ_RESPONSE_2BYTE 0x12
#define MIPI_DSI_RX_DCS_SHORT_READ_RESPONSE_1BYTE 0x21
#define MIPI_DSI_RX_DCS_SHORT_READ_RESPONSE_2BYTE 0x22
#define MIPI_DSI_RX_GENERIC_LONG_READ_RESPONSE 0x1a
#define MIPI_DSI_RX_DCS_LONG_READ_RESPONSE 0x1c
#define pr_err(...) ((void)0)
#define pr_warn(...) ((void)0)
#define DBG(...) ((void)0)
#define y900_pr(...) ((void)0)
#define wmb() ((void)0)
#define msecs_to_jiffies(ms) (ms)
struct mipi_dsi_host { int id; };
struct mipi_dsi_msg { unsigned channel, type; const void *tx_buf; unsigned tx_len;
 void *rx_buf; unsigned rx_len; };
struct msm_dsi_host;
struct ops { int (*dma_base_get)(struct msm_dsi_host *, uint64_t *); };
struct msm_dsi_cfg_handler { const struct ops *ops; unsigned major, minor; };
struct drm_display_mode { int hdisplay; };
struct msm_dsi_host { struct mipi_dsi_host base;
 const struct msm_dsi_cfg_handler *cfg_hnd; int id, dma_comp, format, mode_flags;
 struct drm_display_mode *mode; u8 rx_buf[64]; };
struct msm_dsi { struct mipi_dsi_host *host; };
static struct msm_dsi_host hosts[2];
static struct msm_dsi links[2];
static bool sync_needed, prepared[2];
static int packet, commits, commit_ids[8], commit_packets[8], waits, restored[2];
static int fail_wait, fail_iova, fail_add, prepare_error, rx_count;
static struct msm_dsi *dsi_mgr_get_dsi(int id) { return &links[id]; }
static struct msm_dsi_host *to_msm_dsi_host(struct mipi_dsi_host *h)
{ return &hosts[h->id]; }
static int get_base(struct msm_dsi_host *h, uint64_t *base)
{ *base=0x1000u+0x10000u*h->id; return packet==fail_iova ? -ENXIO : 0; }
static void reinit_completion(int *c) { *c=0; }
static void dsi_wait4video_eng_busy(struct msm_dsi_host *h) { (void)h; }
static int wait_for_completion_timeout(int *c, int timeout)
{ (void)c; assert(timeout==200); waits++; return packet==fail_wait ? 0 : 1; }
static void msm_dsi_host_cmd_xfer_commit(struct mipi_dsi_host *h, u32 base, u32 len)
{
 assert(prepared[h->id] && base && len && commits<8);
 commit_ids[commits]=h->id; commit_packets[commits++]=packet;
}
static int dsi_cmd_dma_add(struct msm_dsi_host *h, const struct mipi_dsi_msg *m)
{ (void)h; packet++; return packet==fail_add ? -EIO : (int)m->tx_len+4; }
static int mipi_dsi_pixel_format_to_bpp(int format) { (void)format; return 24; }
static void dsi_write(struct msm_dsi_host *h, int reg, int value)
{ assert(prepared[h->id] && reg==REG_DSI_RDBK_DATA_CTRL && (value==0 || value==1)); }
static int dsi_cmd_dma_rx(struct msm_dsi_host *h, u8 *buf, int bytes, int size)
{
 assert(bytes==4 && size==1 && prepared[h->id]); rx_count++;
 buf[0]=MIPI_DSI_RX_DCS_SHORT_READ_RESPONSE_1BYTE; buf[1]=0x9c; return 4;
}
static int dsi_short_read1_resp(u8 *b, const struct mipi_dsi_msg *m)
{ *(u8 *)m->rx_buf=b[1]; return 1; }
static int dsi_short_read2_resp(u8 *b, const struct mipi_dsi_msg *m)
{ (void)b; (void)m; assert(false); return 0; }
static int dsi_long_read_resp(u8 *b, const struct mipi_dsi_msg *m)
{ (void)b; (void)m; assert(false); return 0; }
static int msm_dsi_host_xfer_prepare(struct mipi_dsi_host *h,
                                    const struct mipi_dsi_msg *m)
{
 (void)m; assert(!prepared[h->id]);
 if(prepare_error==h->id)return -EIO;
 prepared[h->id]=true; return 0;
}
static void msm_dsi_host_xfer_restore(struct mipi_dsi_host *h,
                                     const struct mipi_dsi_msg *m)
{ (void)m; assert(prepared[h->id]); prepared[h->id]=false; restored[h->id]++; }
ACTUAL_SOURCE
static void setup(bool sync)
{
 static const struct ops ops={.dma_base_get=get_base};
 static const struct msm_dsi_cfg_handler cfg={.ops=&ops,.major=6,.minor=1};
 static struct drm_display_mode mode={.hdisplay=1000};
 memset(hosts,0,sizeof(hosts)); memset(prepared,0,sizeof(prepared));
 memset(restored,0,sizeof(restored));
 sync_needed=sync; packet=commits=waits=rx_count=0;
 fail_wait=fail_iova=fail_add=0; prepare_error=-1;
 for(int i=0;i<2;i++) {
  hosts[i].base.id=hosts[i].id=i; hosts[i].cfg_hnd=&cfg;
  hosts[i].mode=&mode; hosts[i].mode_flags=MIPI_DSI_MODE_VIDEO;
  links[i].host=&hosts[i].base;
 }
}
int main(void)
{
 const u8 command=0x0a; u8 response=0;
 struct mipi_dsi_msg read={.tx_buf=&command,.tx_len=1,.rx_buf=&response,.rx_len=1};
 struct mipi_dsi_msg write={.tx_buf=&command,.tx_len=1};
 for(int sync=0;sync<2;sync++)for(int id=0;id<2;id++) {
  setup(sync); response=0;
  assert(msm_dsi_manager_cmd_xfer(id,&read)==1 && response==0x9c);
  assert(packet==2 && commits==2 && waits==2 && rx_count==1);
  for(int j=0;j<2;j++)assert(commit_ids[j]==id && commit_packets[j]==j+1);
  assert(restored[id]==1 && restored[1-id]==0 && !prepared[0] && !prepared[1]);
  setup(sync);
  int ret=msm_dsi_manager_cmd_xfer(id,&write);
  if(sync && id==0)assert(ret==1 && packet==0 && commits==0 && waits==0);
  else {
   assert(ret==5 && packet==1 && waits==1);
   assert(commits==(sync ? 2 : 1));
   if(sync)assert(commit_ids[0]==0 && commit_ids[1]==1);
   else assert(commit_ids[0]==id);
   assert(restored[id]==1 && restored[1-id]==(int)sync);
  }
  assert(!prepared[0] && !prepared[1]);
 }
 for(int id=0;id<2;id++)for(int failure=0;failure<3;failure++) {
  setup(true);
  if(failure==0)fail_wait=2;
  if(failure==1)fail_iova=2;
  if(failure==2)fail_add=2;
  const int errors[]={-ETIMEDOUT,-ENXIO,-EIO};
  assert(msm_dsi_manager_cmd_xfer(id,&read)==errors[failure]);
  assert(!rx_count && restored[id]==1 && restored[1-id]==0);
  setup(true);
  if(failure==0)fail_wait=1;
  if(failure==1)fail_iova=1;
  if(failure==2)fail_add=1;
  assert(msm_dsi_manager_cmd_xfer(id,&read)==-EINVAL);
  assert(!rx_count && restored[id]==1 && restored[1-id]==0);
 }
 setup(true); prepare_error=1;
 assert(msm_dsi_manager_cmd_xfer(1,&write)==-EIO);
 assert(restored[0]==1 && !restored[1] && !commits && !prepared[0]);
 setup(true); prepare_error=0;
 assert(msm_dsi_manager_cmd_xfer(0,&read)==-EIO && !commits && !rx_count);
 puts("DSI routing: both read commands target one prepared host; writes broadcast unchanged; errors restore hosts");
 return 0;
}
'''
