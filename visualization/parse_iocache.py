#!/usr/bin/env python3

import os, sys, shutil, re, commands, getopt, string, time, threading

CACHESTAT_RAW = './cachestat.txt'
IOSNOOP_RAW = './iosnoop.txt'
PERF_DAT = './perf.dat'

DATA_CAPACITY = 180
TOTAL_TASK = 'Total'

#cachestat_list = []

class in_node:
    def __init__(self, taskname, readbytes, writebytes, readlatency, writelatency):
       self.taskname = taskname
       self.readkb = float(readbytes / 1024)
       self.writekb = float(writebytes / 1024)
       self.readlatency = float(readlatency)
       self.writelatency = float(writelatency)

class p_node:
    def __init__(self, timestamp, hits, misses, dirties, ratio):
        self.timestamp = timestamp
        self.hits = hits
        self.misses = misses
        self.dirties = dirties
        self.ratio = ratio
        self.inlist = []
        self.tasks = [TOTAL_TASK, 'com.intel.ji']
        for i in self.tasks:
            self.inlist.append(in_node(i, 0, 0, 0, 0))

    def iosnoop(self, inn):
        for i in self.inlist:
            if i.taskname == TOTAL_TASK or i.taskname == inn.taskname:
                i.readkb += inn.readkb
                i.writekb += inn.writekb
                i.readlatency += inn.readlatency
                i.writelatency += inn.writelatency

    def format_dat(self):
        m = "%d %d %d %d %.2f"%(self.timestamp, self.hits, self.misses, self.dirties, self.ratio)
        for i in self.inlist:
            readspeed = 0
            writespeed = 0
            if not i.readlatency == 0: 
                readspeed = i.readkb/i.readlatency
            if not i.writelatency == 0:
                writespeed = i.writekb/i.writelatency
            m += " %.2f %.2f %.2f %.2f"%(i.readkb, i.writekb, readspeed, writespeed)
        m += "\n"
        return m

class p_parser:
    def __init__(self):
        self.plist = []
        self.cachestat_ln = 0
        self.iosnoop_ln = 0

    def parse_cachestat(self):
        #del self.plist[:]

        with open(CACHESTAT_RAW) as f:
            lines = f.readlines()[self.cachestat_ln:]
        for l in lines:
            self.cachestat_ln += 1
            obj = re.search(r'(?P<hits>\d+)(\s+)(?P<misses>\d+)(\s+)(?P<dirties>\d+)(\s+)(?P<ratio1>\d+)\.(?P<ratio2>\d+)?%(\s+)(\d+)(\s+)(\d+)(\s+)(?P<timestamp>\d+)', l)
            if obj:
                n = p_node( int(obj.group('timestamp')), int(obj.group('hits')), int(obj.group('misses')), \
                    int(obj.group('dirties')), float(obj.group('ratio1')+'.'+obj.group('ratio2')) )
                self.plist.append(n)
                #print("... Append p_node: %d"% self.cachestat_ln)
    
    def parse_iosnoop(self):
        with open(IOSNOOP_RAW) as f:
            print(" >==----> %d <----==<"% self.iosnoop_ln)
            lines = f.readlines()[self.iosnoop_ln:]
        for l in lines:
            self.iosnoop_ln += 1
            obj = re.search(r'(?P<timestamp>\d+)\.(\d+)(\s+)(\d+)\.(\d+)(\s+)(?P<comm>[A-Za-z0-9\/\_\-]+)(\s+)(\d+)(\s+)(?P<type>\w+)(\s+)(\d+)\,(\d+)(\s+)(\d+)(\s+)(?P<bytes>\d+)(\s+)(?P<latency1>\d+)\.(?P<latency2>\d+)', l)
            if obj:
                timestamp = int(obj.group('timestamp'))
                for p in self.plist:
                    if timestamp == p.timestamp:
                        readbytes = 0
                        readlatency = 0
                        writebytes = 0
                        writelatency = 0
                        if obj.group('type').find('R') != -1:
                            readbytes = int(obj.group('bytes'))
                            readlatency = float(obj.group('latency1')+'.'+obj.group('latency2'))
                        elif obj.group('type').find('W') != -1:
                            writebytes = int(obj.group('bytes'))
                            writelatency = float(obj.group('latency1')+'.'+obj.group('latency2'))
                        n = in_node(obj.group('comm'), readbytes, writebytes, readlatency, writelatency)
                        #print("in_node ==> %s, %d, %d, %f, %f"% (obj.group('comm'), readbytes/1024, writebytes/1024, readlatency, writelatency))
                        p.iosnoop(n)

                        
    def generate_dat(self):
        d = open(PERF_DAT, 'w')
        sidx = len(self.plist) - DATA_CAPACITY
        if(sidx < 0): sidx = 0
        for i in range(sidx, len(self.plist)):
            #print("... write index %d"% i)
            d.write(self.plist[i].format_dat())
        d.close()

def prepare_env():
    # Kernel configure on: CONFIG_FUNCTION_PROFILER
    os.system('adb root')
    time.sleep(2)
    status, output = commands.getstatusoutput('adb disable-verity')
    if output.find('Verity already disabled') == -1:
        os.system('adb reboot')
        os.system('adb wait-for-device')
        os.system('adb root')
        time.sleep(2)
    os.system('adb remount')
    os.system('adb push busybox /system/xbin')
    os.system('adb push cachestat /system/xbin')
    os.system('adb push iosnoop /system/xbin')
    os.system('rm -rf %s'% PERF_DAT)
    os.system('touch %s'% PERF_DAT)

class cachestat_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        os.system('rm -rf %s'% CACHESTAT_RAW)
        os.system('touch %s'% CACHESTAT_RAW)

    def run(self):
        os.system('adb shell cachestat -t > %s'% CACHESTAT_RAW)

class iosnoop_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        os.system('adb shell rm -rf /data/.ftrace-lock')
        os.system('rm -rf %s'% IOSNOOP_RAW)
        os.system('touch %s'% IOSNOOP_RAW)

    def run(self):
        os.system('adb shell iosnoop -Qts > %s'% IOSNOOP_RAW)

def get_uptime_seconds():
    status, output = commands.getstatusoutput('adb shell cat /proc/uptime')
    return int(output.split()[0].split('.')[0])

def gnuplot_work():
    pparser = p_parser()
    f = os.popen('gnuplot', 'w')
 #   print >>f, "set xrange [-5*pi:5*pi]"
 #   print >>f, "plot sin(x+i*pi/20) lw 2 lc rgb 'orange' title 'shanghai', \
 #       cos(x-i*pi/20) lw 2 lc rgb 'purple' title 'beijing'"
    while (True):
        pparser.parse_cachestat()
        pparser.parse_iosnoop()
        pparser.generate_dat()
        print >>f, "set xtics 10"
        print >>f, "set yrange [0:80000]"
        print >>f, "set y2range [0:270]"
        print >>f, "set ytics 0,5000,80000"
        print >>f, "set y2tics 0,10,270"
        print >>f, "set y2tics nomirror"
        print >>f, \
            "plot '%s' using 1:5 title 'ratio' with lines axes x1y2 lw 3, \
            '%s' using 1:2 title 'hits' with lines axes x1y1 lw 1, \
            '%s' using 1:3 title 'misses' with lines axes x1y1 lw 1, \
            '%s' using 1:4 title 'dirties' with lines axes x1y1 lw 1, \
            '%s' using 1:8 title 'readspeed' with lines axes x1y2 lw 2, \
            '%s' using 1:9 title 'writespeed' with lines axes x1y2 lw 2 \
            "% (PERF_DAT, PERF_DAT, PERF_DAT, PERF_DAT, PERF_DAT, PERF_DAT)
        print >>f, "replot"
        print >>f, "pause 1"
        time.sleep(1)
    f.flush()


if __name__ == "__main__":
    prepare_env()
    c = cachestat_thread()
    i = iosnoop_thread()
    c.start()
    i.start()
    gnuplot_work()

