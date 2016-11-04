#!/usr/bin/env python

import sys, os, shutil, getopt, threading, string, time

class io_thread(threading.Thread):
    def __init__(self, type, model, size):
        threading.Thread.__init__(self)
        self.utbin = 'rw_ut'
        self.type = type
        self.model = model
        self.size = size
        if self.type == 'in':
            self.utfile = '/data/unittest'
        elif self.type == 'ex':
            self.utfile = '/storage/sdcard1/unittest'
        root_cmd = 'adb root'
        remount_cmd = 'adb remount'
        push_ut_cmd = 'adb push ' + self.utbin + ' /data'
        x_mode_cmd = 'adb shell "chmod 777 /data/' + self.utbin + '"'
        os.system(root_cmd)
        #os.system(remount_cmd)
        os.system(push_ut_cmd)
        os.system(x_mode_cmd)
    
    def link_file(self):
        link_cmd = 'adb shell "dd if=/dev/zero of=' + self.utfile + ' bs=10m count=' + str(int(self.size)/10) + '"'
        print("CMD: " + link_cmd)
        os.system(link_cmd)
    
    def unlink_file(self):
        unlink_cmd = 'adb shell "rm -rf ' + self.utfile + '"'
        print("CMD: " + unlink_cmd)
        os.system(unlink_cmd)

    def execute_ut(self):
        sync_cmd = 'adb shell "sync"'
        trim_cmd = 'adb shell "vdc fstrim dotrim && sleep 2"'
        exec_cmd = 'adb shell "/data/' + self.utbin + ' ' + self.utfile + ' 0"' 
        print("CMD: " + exec_cmd)
        os.system(sync_cmd)
        os.system(trim_cmd)
        #for i in range(0, 5):
        #print("------------ execute unittest for %d times" %(i))
        os.system(exec_cmd)
 
    def run(self):
        self.unlink_file()
        self.link_file()
        self.execute_ut()
        self.unlink_file()

class atrace_thread(threading.Thread):
    def __init__(self, type, model, size):
        threading.Thread.__init__(self)
        self.type = type
        self.model = model
        self.size = size
        
    def atrace_get(self):
        atrace_cmd = 'adb shell "atrace mmc -t 20" > atrace_' + str(self.type) + '_' + str(self.model) + '_' + str(self.size) + 'm.txt'
        print("CMD: " + atrace_cmd)
        os.system(atrace_cmd)
    
    def run(self):
        self.atrace_get()

def get_throughput(type, model, size):
    io_t = io_thread(type, model, size)
    tr_t = atrace_thread(type, model, size)
    
    io_t.start()
    tr_t.start()

if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], "ht:m:n:")
    type = ''
    model = ''
    size = ''
    for op, value in opts:
        if op == "-t":
            type = value
            print("Get file {0}".format(type))
        elif op == "-m":
            model = value
            print("Get file {0}".format(model))
        elif op == "-n":
            size = value
            print("Get file {0}".format(size))
            get_throughput(type, model, size)
            sys.exit()
        elif op == "-h":
            print("Usage: python ut_io.py -t in|ex -m rr|sr|rw|sw -n YOUR_SIZE(M)")
            sys.exit()
