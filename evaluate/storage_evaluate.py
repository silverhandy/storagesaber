#!/usr/bin/env python

import sys, os, threading, string, time

class dd_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.readfile = 'read.dd'
        self.writefile = 'write.dd'
        self.ddtest = '/data/__ddtest'
        self.drop_cache_cmd = 'adb shell "echo 3 > /proc/sys/vm/drop_caches"'
        clear_cmd = 'rm -rf *.dd'
        os.system(clear_cmd)

    def read_process(self, count):
        os.system(self.drop_cache_cmd)
        dd_cmd = 'adb shell time sh -c "/data/busybox dd if=/dev/block/mmcblk0 of=/dev/null bs=10M count=' + str(count) + '"'
        #print 'exec {' + dd_cmd + '}'
        export_cmd = dd_cmd + '>> ' + self.readfile
        os.system(dd_cmd)

    def write_process(self, count):
        adb_clear_cmd = 'adb shell "rm -rf ' + self.ddtest + '"'
        os.system(adb_clear_cmd)
        adb_prep_cmd = 'adb shell "touch ' + self.ddtest + '"'
        os.system(adb_prep_cmd)
        os.system(self.drop_cache_cmd)
        dd_cmd = 'adb shell time sh -c "/data/busybox dd if=/dev/zero of=' + self.ddtest + ' bs=100M count=' + str(count) + ' conv=fsync"'
        #print 'exec {' + dd_cmd + '}'
        export_cmd = dd_cmd + '>> ' + self.writefile
        os.system(dd_cmd)
        os.system(adb_clear_cmd)

    def run(self):
        for i in range(0, 3):
            self.read_process((i+1)*10)
        for i in range(0, 3):
            self.write_process((i+1)*1)
    
def evaluate_ioperf():
    root_cmd = 'adb root'
    remount_cmd = 'adb remount'
    push_busybox_cmd = 'adb push busybox /data'
    os.system(root_cmd)
    time.sleep(3)
    os.system(remount_cmd)
    os.system(push_busybox_cmd)
    
    t = dd_thread()
    t.start()
        
if __name__ == '__main__':
    evaluate_ioperf()
    
