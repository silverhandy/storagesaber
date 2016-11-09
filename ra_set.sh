#!/bin/bash

echo "BEFORE ra set ------------"
echo "mmcblk0 ra:"
adb shell cat /sys/block/mmcblk0/queue/read_ahead_kb
echo "dm-0 ra:"
adb shell cat /sys/block/dm-0/queue/read_ahead_kb
echo "dm-1 ra:"
adb shell cat /sys/block/dm-1/queue/read_ahead_kb
echo "verity prefetch:"
adb shell cat /sys/module/dm_verity/parameters/prefetch_cluster

adb shell "echo $1 > /sys/block/mmcblk0/queue/read_ahead_kb"
adb shell "echo $1 > /sys/block/dm-0/queue/read_ahead_kb"
adb shell "echo $1 > /sys/block/dm-1/queue/read_ahead_kb"
adb shell "echo $2 > /sys/module/dm_verity/parameters/prefetch_cluster"

echo "AFTER ra set ------------"
echo "mmcblk0 ra:"
adb shell cat /sys/block/mmcblk0/queue/read_ahead_kb
echo "dm-0 ra:"
adb shell cat /sys/block/dm-0/queue/read_ahead_kb
echo "dm-1 ra:"
adb shell cat /sys/block/dm-1/queue/read_ahead_kb
echo "verity prefetch:"
adb shell cat /sys/module/dm_verity/parameters/prefetch_cluster


