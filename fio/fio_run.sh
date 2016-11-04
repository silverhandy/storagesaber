#!/bin/bash

for i in {1..50}; do
    echo "fio run for $i times"
    adb root
    sleep 20
    adb shell 'sync'
    adb shell 'echo 3 > /proc/sys/vm/drop_caches'
    adb shell 'rm -rf ./data/fio/random-*'
    adb shell 'rm -rf ./data/fio/sequential-*'
    ./get_ftrace_io.sh filemap_start
    adb shell './data/fio/fio ./data/fio/fio_task'
    sleep 106 
    ./get_ftrace_io.sh filemap_stop
done
