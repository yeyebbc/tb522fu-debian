// SPDX-License-Identifier: GPL-2.0-only
/* Inspect a dedicated 12 GiB swap partition before any filesystem is mounted.
 * The shell caller validates the UFS controller, LUN, labels and geometry.
 * A resume attempt returning is always fatal, including a successful write:
 * resume_store() does not return the software_resume() error to userspace.
 */
#define _FILE_OFFSET_BITS 64
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <linux/fs.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <unistd.h>

#define PAGE_BYTES 4096U
#define SWAP_BYTES (UINT64_C(12) * 1024 * 1024 * 1024)
#define NO_IMAGE 0
#define HAS_IMAGE 3
#define BAD_HEADER 1

static uint32_t little32(const unsigned char *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static int header_state(const unsigned char *p, size_t length, uint64_t bytes)
{
    unsigned int i, nonzero = 0;
    if (length != PAGE_BYTES || bytes != SWAP_BYTES ||
        little32(p + 1024) != 1 ||
        little32(p + 1028) != SWAP_BYTES / PAGE_BYTES - 1 ||
        little32(p + 1032) != 0)
        return BAD_HEADER;
    for (i = 1036; i < 1052; i++)
        nonzero |= p[i];
    if (!nonzero)
        return BAD_HEADER;
    if (!memcmp(p + PAGE_BYTES - 10, "SWAPSPACE2", 10))
        return NO_IMAGE;
    if (!memcmp(p + PAGE_BYTES - 10, "S1SUSPEND", 10) &&
        !memcmp(p + PAGE_BYTES - 20, "SWAPSPACE2", 10))
        return HAS_IMAGE;
    return BAD_HEADER;
}

#ifndef RESUME_UNIT_TEST
static void fatal(const char *text)
{
    fprintf(stderr, "TB522FU_RESUME_BLOCKED: %s (errno=%d)\n", text, errno);
    exit(1);
}

static void write_exact(const char *path, const char *text)
{
    int fd = open(path, O_WRONLY | O_CLOEXEC | O_NOFOLLOW);
    size_t n = strlen(text);
    if (fd < 0 || write(fd, text, n) != (ssize_t)n || close(fd))
        fatal(path);
}

int main(int argc, char **argv)
{
    struct stat swap, parent;
    uint64_t bytes;
    unsigned char page[PAGE_BYTES];
    char number[64];
    int fd, state, diskfd, rw = 0;
    if (argc != 4 || (strcmp(argv[1], "inspect") && strcmp(argv[1], "resume")))
        fatal("usage: tb522fu-resume {inspect|resume} /dev/swap-partition /dev/parent");
    if (sysconf(_SC_PAGESIZE) != PAGE_BYTES)
        fatal("unsupported page size");
    fd = open(argv[2], O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    diskfd = open(argv[3], O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0 || diskfd < 0 || fstat(fd, &swap) || fstat(diskfd, &parent) ||
        !S_ISBLK(swap.st_mode) || !S_ISBLK(parent.st_mode) ||
        major(swap.st_rdev) != major(parent.st_rdev) ||
        swap.st_rdev == parent.st_rdev ||
        ioctl(fd, BLKGETSIZE64, &bytes) ||
        pread(fd, page, sizeof(page), 0) != sizeof(page))
        fatal("cannot read validated swap block device");
    state = header_state(page, sizeof(page), bytes);
    if (state == BAD_HEADER)
        fatal("invalid swap geometry, version, UUID or signature");
    if (state == NO_IMAGE) {
        puts("TB522FU_RESUME_NO_IMAGE: valid dedicated swap; ordinary boot permitted");
        return 0;
    }
    puts("TB522FU_RESUME_IMAGE: snapshot present; filesystems must remain untouched");
    fflush(stdout);
    if (!strcmp(argv[1], "inspect"))
        return HAS_IMAGE;
    /* Only the parent and dedicated swap become writable. Root stays RO. */
    if (ioctl(diskfd, BLKROSET, &rw) || ioctl(fd, BLKROSET, &rw))
        fatal("cannot enable resume-device writes");
    close(fd);
    close(diskfd);
    write_exact("/sys/power/resume_offset", "0\n");
    snprintf(number, sizeof(number), "%u:%u\n", major(swap.st_rdev), minor(swap.st_rdev));
    puts("TB522FU_RESUME_ATTEMPT: entering software_resume before any mount");
    fflush(stdout);
    write_exact("/sys/power/resume", number);
    /* A real restore continues in the OLD kernel, never at this instruction. */
    fatal("resume attempt returned; refusing filesystem checks or mounts");
}
#endif
