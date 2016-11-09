#!/usr/bin/env python

import sys, os, threading, string, time

class dd_thread(threading.Thread):
    def __init__(self, no):
        threading.Thread.__init__(self)
        self.thread_no = no

    def run(self):
        print "ram thread(%d)"%(self.thread_no)
        dd_dev = '/dev/__ddtest'
        #drop_cache_cmd = 'adb shell "echo 3 > /proc/sys/vm/drop_caches"'
        clear_cmd = 'adb shell rm -rf ' + dd_dev + str(self.thread_no)
        dd_cmd = 'adb shell dd if=/dev/zero of=' + dd_dev + str(self.thread_no) + ' bs=10M'
        while(1):
            #print 'exec {' + str(self.thread_no) + ': ' +  drop_cache_cmd + '}'
            #os.system(drop_cache_cmd)
            print 'exec {' + clear_cmd + '}'
            os.system(clear_cmd)
            print 'exec {' + dd_cmd + '}'
            os.system(dd_cmd)
            
    
def ram_dd_test():
    root_cmd = 'adb root'
    drop_cache_cmd = 'adb shell "echo 3 > /proc/sys/vm/drop_caches"'
    os.system(root_cmd)
    os.system(drop_cache_cmd)
    
    thread_num = string.atoi(sys.argv[1])
    if thread_num <= 0:
        thread_num = 20
    print "dd thread num: " + str(thread_num)
    
    for i in range(0, thread_num):
        t = dd_thread(i)
        t.start()
        
if __name__ == '__main__':
    ram_dd_test()
    
