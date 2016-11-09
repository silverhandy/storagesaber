#!/bin/bash

adb root
sleep 2
adb push iozone /data
chmod 0777 /data/iozone

adb shell "sync && echo 3 > /proc/sys/vm/drop_caches"

echo "============== create test file ================"
adb shell /data/iozone -ec -+n -L$1 -S$2 -s$3 -f /data/iozone.tmp -r512k -i0 -w > /dev/null

echo "============== random read/write process ======="
adb shell /data/iozone -ec -+n -L$1 -S$2 -s$3 -f /data/iozone.tmp -w -+N -I -r4k -i2 -O

echo "============== sequential write process ========"
adb shell /data/iozone -ec -+n -L$1 -S$2 -s$3 -f /data/iozone.tmp -w -+N -I -r512k -i0

echo "============== sequential read process ========="
adb shell /data/iozone -ec -+n -L$1 -S$2 -s$3 -f /data/iozone.tmp -w -+N -I -r512k -i1

