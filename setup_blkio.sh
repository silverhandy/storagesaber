#!/bin/bash

adb root

sleep 2

#adb shell 'mount -t tmpfs cgroup_root /sys/fs/cgroup'
#adb shell 'mkdir /sys/fs/cgroup/blkio'
adb shell 'mount -t cgroup -o blkio none /sys/fs/cgroup/blkio'
adb shell 'mkdir -p /sys/fs/cgroup/blkio/launch_boost/'
adb shell 'echo 1000 > /sys/fs/cgroup/blkio/launch_boost/blkio.weight'
adb shell 'echo 100 > /sys/fs/cgroup/blkio/blkio.weight'

adb shell 'chmod 666 /sys/fs/cgroup/blkio/launch_boost/cgroup.procs'
adb shell 'echo > /sys/fs/cgroup/blkio/launch_boost/cgroup.procs'
