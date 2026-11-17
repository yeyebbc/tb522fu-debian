#!/system/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
set -eu
[ "$(id -u)" = 0 ]
[ "$(getprop ro.boot.slot_suffix)" = _b ]
[ "$(getprop ro.boot.flash.locked)" = 0 ]
node=
for item in /sys/class/block/*; do
    [ -e "$item/partition" ] || continue
    grep -qx PARTNAME=debian "$item/uevent" || continue
    [ -z "$node" ] || { echo 'Duplicate Debian partition'; exit 1; }
    node=$item
done
[ -n "$node" ]
parent=$(dirname "$(readlink -f "$node")")
case "$(readlink -f "$parent/device")" in */1d84000.ufshc/*:0:0:0) ;; *) exit 1;; esac
[ "$(cat "$parent/queue/logical_block_size")" = 4096 ]
[ "$(cat "$node/start")" = 454096896 ]
size=$(cat "$node/size")
case "$size" in
    536870912) ;;
    511705088)
        swap=
        for item in /sys/class/block/*; do
            [ -e "$item/partition" ] || continue
            grep -qx PARTNAME=debian-swap "$item/uevent" || continue
            [ -z "$swap" ] || exit 1
            swap=$item
        done
        [ -n "$swap" ]
        [ "$(dirname "$(readlink -f "$swap")")" = "$parent" ]
        [ "$(cat "$swap/start")" = 965801984 ]
        [ "$(cat "$swap/size")" = 25165824 ]
        [ "$(cat "$swap/partition")" = 18 ]
        # Never mount a filesystem frozen in a saved hibernation image. Only
        # a valid ordinary swap header permits Android's mount-based Action.
        sig=$(dd if="/dev/block/${swap##*/}" bs=4096 count=1 2>/dev/null |
              od -An -tx1 -j4086 -N10 | tr -d ' \n')
        [ "$sig" = 53574150535041434532 ] || {
            echo 'Pending or invalid hibernation image; use host resume/recovery'
            exit 1
        }
        ;;
    *) exit 1;;
esac
dev="/dev/block/${node##*/}"
[ -b "$dev" ]
# Refuse an unclean Linux shutdown. ro,noload must not hide pending recovery.
magic=$(od -An -tu2 -j1080 -N2 "$dev")
state=$(od -An -tu2 -j1082 -N2 "$dev")
incompat=$(od -An -tu4 -j1120 -N4 "$dev")
[ "$((magic))" = 61267 ]
[ "$((state & 1))" = 1 ] && [ "$((state & 2))" = 0 ]
[ "$((incompat & 4))" = 0 ] || { echo 'Debian needs filesystem recovery; use host maintenance'; exit 1; }
root=/data/adb/tb522fu-debian-mount
mkdir -p "$root"
chmod 700 "$root"
grep -q " $root " /proc/mounts && { echo 'Mount point already in use'; exit 1; }
mount -t ext4 -o ro,noload "$dev" "$root"
trap 'umount "$root"' EXIT
partuuid=$(sed -n 's/^PARTUUID=//p' "$node/uevent")
[ "$(cat "$root/etc/tb522fu/root-partuuid")" = "$partuuid" ]
/system/bin/sh "$root/usr/libexec/tb522fu-rotate-boot" linux "$root"
umount "$root"
trap - EXIT
sync
exec /system/bin/reboot
