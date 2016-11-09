#!/bin/bash

adb root
sleep 2
adb push iozone /data
adb shell chmod 0777 /data/iozone

echo "============== start iozone test ================"
adb shell /data/iozone -i 0 -i 1 -i 2 -f /storage/sdcard1/iozone_test -s 200m -r 64k -+r -Rb ./izone_test.xls