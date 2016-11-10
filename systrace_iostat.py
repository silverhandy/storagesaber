# systrace for io stat
__author__ = ['"Chen, Tingjie": <tingjie.chen@intel.com>']

import sys
import os
import shutil
import getopt

BLK_SIZE = 512

CMD_READ_SING_BLK = 17
CMD_READ_MULTI_BLK = 18
CMD_WRITE_SING_BLK = 24
CMD_WRITE_MULTI_BLK = 25

io_dict = {}

io_name_dict = {}
io_name_dict[CMD_READ_SING_BLK] = 'READ_SINGLE_BLK'
io_name_dict[CMD_READ_MULTI_BLK] = 'READ_MULTI_BLK'
io_name_dict[CMD_WRITE_SING_BLK] = 'WRITE_SINGLE_BLK'
io_name_dict[CMD_WRITE_MULTI_BLK] = 'WRITE_MULTI_BLK'

BLKSZ_4K    = 4 * 1024
BLKSZ_8K    = 8 * 1024
BLKSZ_16K   = 16 * 1024
BLKSZ_32K   = 32 * 1024
BLKSZ_64K   = 64 * 1024
BLKSZ_128K  = 128 * 1024
BLKSZ_256K  = 256 * 1024
BLKSZ_512K  = 512 * 1024
BLKSZ_512KP = 0xffff * 1024


class io_blksz_property:
    def __init__(self):
        self.total_time = 0.0
        self.max_time = 0.0
        self.min_time = 0.0
        self.avg_time = 0.0
        self.total_wl = 0
        self.op_num = 0
        self.throughput = 0.0

    def new_operation(self, time, workload):
        self.total_time += time
        self.total_wl += workload
        self.op_num += 1
        
        if (time > self.max_time):
            self.max_time = time

        if (time < self.min_time) or (self.min_time == 0):
            self.min_time = time

    def get_throughput(self):
        if (self.op_num != 0):
            self.avg_time = self.total_time / self.op_num

        if (self.total_time != 0):
            self.throughput = self.total_wl / (self.total_time * 1024 * 1024)
        return self.throughput


class io_property:
    def __init__(self):
        self.total_time = 0.0
        self.max_time = 0.0
        self.min_time = 0.0
        self.avg_time = 0.0
        self.total_wl = 0
        self.max_wl = 0
        self.min_wl = 0
        self.avg_wl = 0
        self.throughput = 0.0
        self.op_num = 0
        self.io_blksz_dict = {}
        self.io_blksz_dict[BLKSZ_4K] = io_blksz_property()
        self.io_blksz_dict[BLKSZ_8K] = io_blksz_property()
        self.io_blksz_dict[BLKSZ_16K] = io_blksz_property()
        self.io_blksz_dict[BLKSZ_32K] = io_blksz_property()
        self.io_blksz_dict[BLKSZ_64K] = io_blksz_property()
        self.io_blksz_dict[BLKSZ_128K] = io_blksz_property()
        self.io_blksz_dict[BLKSZ_256K] = io_blksz_property()
        self.io_blksz_dict[BLKSZ_512K] = io_blksz_property()
        self.io_blksz_dict[BLKSZ_512KP] = io_blksz_property()

    def new_operation(self, time, workload):
        self.op_num += 1
        self.total_time += time
        self.total_wl += workload
        
        if (time > self.max_time):
            self.max_time = time

        if (time < self.min_time) or (self.min_time == 0):
            self.min_time = time

        if (workload > self.max_wl):
            self.max_wl = workload

        if (workload < self.min_wl) or (self.min_wl == 0):
            self.min_wl = workload

        if (workload <= BLKSZ_4K):
            self.io_blksz_dict[BLKSZ_4K].new_operation(time, workload)
        elif (workload <= BLKSZ_8K) and (workload > BLKSZ_4K):
            self.io_blksz_dict[BLKSZ_8K].new_operation(time, workload)
        elif (workload <= BLKSZ_16K) and (workload > BLKSZ_8K):
            self.io_blksz_dict[BLKSZ_16K].new_operation(time, workload)
        elif (workload <= BLKSZ_32K) and (workload > BLKSZ_16K):
            self.io_blksz_dict[BLKSZ_32K].new_operation(time, workload)
        elif (workload <= BLKSZ_64K) and (workload > BLKSZ_32K):
            self.io_blksz_dict[BLKSZ_64K].new_operation(time, workload)
        elif (workload <= BLKSZ_128K) and (workload > BLKSZ_64K):
            self.io_blksz_dict[BLKSZ_128K].new_operation(time, workload)
        elif (workload <= BLKSZ_256K) and (workload > BLKSZ_128K):
            self.io_blksz_dict[BLKSZ_256K].new_operation(time, workload)
        elif (workload <= BLKSZ_512K) and (workload > BLKSZ_256K):
            self.io_blksz_dict[BLKSZ_512K].new_operation(time, workload)
        else:
            self.io_blksz_dict[BLKSZ_512KP].new_operation(time, workload)

    def get_throughput(self):
        if (self.op_num != 0):
            self.avg_wl = self.total_wl / self.op_num
            self.avg_time = self.total_time / self.op_num

        if (self.total_time != 0):
            self.throughput = self.total_wl / (self.total_time * 1024 * 1024)
        return self.throughput

def filter_str_path(path, startstr, finishstr):
    is_working = 0
    cur_start_ms = 0
    cur_finish_ms = 0
    cur_wl = 0
    cur_cmd = 0
    invalid_start_num = 0
    invalid_finish_num = 0

    io_dict[CMD_READ_SING_BLK] = io_property()
    io_dict[CMD_READ_MULTI_BLK] = io_property()
    io_dict[CMD_WRITE_SING_BLK] = io_property()
    io_dict[CMD_WRITE_MULTI_BLK] = io_property()

    if os.path.isfile(path):
        with open(path) as f:
            lines = f.readlines()
        for line in lines:
            if line.find(startstr) != -1:
                if (is_working != 0):
                    invalid_start_num += 1
                    continue
                is_working = 1
                cur_cmd = int(line.split('cmd=')[1].split(',addr=')[0])
                cur_wl = int(line.split('size=0x')[1].split('\\n')[0], 16) * BLK_SIZE
                cur_start_ms = line.split(']')[1].split(':')[0].split()[1]
            if line.find(finishstr) != -1:
                if (is_working == 0):
                    invalid_finish_num += 1
                    continue
                temp_cmd = int(line.split('cmd=')[1].split(',addr=')[0])
                if (cur_cmd != temp_cmd):
                    invalid_finish_num += 1
                    continue
                temp_wl = int(line.split('size=0x')[1].split('\\n')[0], 16) * BLK_SIZE
                if (cur_wl != temp_wl):
                    invalid_finish_num += 1
                    continue
                #print("line =>", line)
                cur_finish_ms = line.split('] ')[1].split(':')[0].split()[1]
                cur_time = float(cur_finish_ms) - float(cur_start_ms)
                if (cur_time < 0):
                    print("Time duration < 0 ...")
                    continue
                io_dict[cur_cmd].new_operation(cur_time, cur_wl)
                is_working = 0
    elif os.path.isdir(path):
        print("Please enter full filename!")
    print("invalid start:%d, invalid finish:%d\n" %(invalid_start_num, invalid_finish_num))
    return io_dict

def get_throughputs(iodict):
    percentage = 0.0
    
    for i in iodict:
        if (iodict[i].op_num == 0):
            continue
        
        print("\nOPERATION  WORKLOAD(KB)    TIME(S) OP_NUM  THROUGHPUT(MB/S) MAX_WL MIN_WL  AVG_WL  MAX_TIME    MIN_TIME    AVG_TIME")
        print("*********************************************************************************************************************")
        print("%s   %2.2f \t%2.5f   %d  %2.2f   \t%d    %d  %d  %2.5f\t\t%2.5f\t\t%2.5f" %(io_name_dict[i], iodict[i].total_wl/1024, \
            iodict[i].total_time, iodict[i].op_num, iodict[i].get_throughput(), iodict[i].max_wl, iodict[i].min_wl, iodict[i].avg_wl, \
            iodict[i].max_time, iodict[i].min_time, iodict[i].avg_time))

        print("\nBLK_SIZE(KB)       PERCENT(NUM)    WORKLOAD(KB)    TIME(S) \tTHROUGHPUT(MB/S)  MAX_TIME    MIN_TIME    AVG_TIME")
        print("-------------------------------------------------------------------------------------------------------------")
        for j in iodict[i].io_blksz_dict:
            if (iodict[i].io_blksz_dict[j].op_num == 0):
                continue
            percentage = float(iodict[i].io_blksz_dict[j].op_num) * 100.00 / float(iodict[i].op_num)
            if (j == BLKSZ_512KP):
                blksz = '>512K'
            elif (j == BLKSZ_4K):
                blksz = '<=' + str(j/1024) + 'K'
            else:
                blksz = '<=' + str(j/1024) + 'K && >' + str(j/2048) + 'K'
            print("%-16s\t%2.2f%%(%d) \t%d  \t%2.5f \t%2.2f\t\t\t%2.5f\t\t%2.5f\t\t%2.5f" %(blksz, percentage, iodict[i].io_blksz_dict[j].op_num, \
                iodict[i].io_blksz_dict[j].total_wl/1024, iodict[i].io_blksz_dict[j].total_time, iodict[i].io_blksz_dict[j].get_throughput(), \
                iodict[i].io_blksz_dict[j].max_time, iodict[i].io_blksz_dict[j].min_time, iodict[i].io_blksz_dict[j].avg_time))

if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], "hp:")
    path = ''
    start_str = 'mmc_blk_rw_start'
    finish_str = 'mmc_blk_rw_end'
    for op, value in opts:
        if op == "-p":
            path = value
            print("Get file {0}".format(path))
            iodict = filter_str_path(path, start_str, finish_str)
            get_throughputs(iodict)
            sys.exit()
        elif op == "-h":
            print("Usage: python systrace_rw_filter.py -p YOUR_FULL_PATH_NAME")
            sys.exit()

