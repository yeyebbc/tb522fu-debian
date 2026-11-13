/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <glibtop.h>
#include <glibtop/sysinfo.h>
#include <stdio.h>

int main(void)
{
    const glibtop_sysinfo *info = glibtop_get_sysinfo();
    if (!info || !info->ncpu || info->ncpu > GLIBTOP_NCPU)
        return 1;
    for (guint64 i = 0; i < info->ncpu; i++) {
        const char *model = g_hash_table_lookup(info->cpuinfo[i].values, "model name");
        if (!model || !*model)
            return 2;
        printf("%" G_GUINT64_FORMAT "\t%s\n", i, model);
    }
    return 0;
}
