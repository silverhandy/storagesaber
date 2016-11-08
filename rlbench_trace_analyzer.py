# rlbench trace analysis

import sys, os, shutil, getopt, commands, string, time

def get_sqlite_1000inserts_thread():
    sqlite_cmd = 'ps -t | grep sqlite'
    status, output = commands.getstatusoutput('adb shell ' + sqlite_cmd)
    #print("status:%s, msg: %s"% (status >> 8, output))
    sqlite_pid = output.split()[1]
    sqlite_run_cmd = 'ps -t | grep ' + sqlite_pid
    status, output = commands.getstatusoutput('adb shell ' + sqlite_run_cmd)
    #print("status:%s, msg: %s"% (status >> 8, output))
    lines = output.splitlines()
    sqlite_run_pid = sqlite_run_tname = ''
    for line in lines:
        #print("line =>", line)
        pos = line.find('Thread-')
        if pos != -1:
            sqlite_run_pid = line.split()[1]
            sqlite_run_tname = line[pos:]
            break
    #print("pid =>", sqlite_run_pid, "tname =>", sqlite_run_tname)
    return (sqlite_run_pid, sqlite_run_tname)

def collect_ftrace_data(ftrace_type):
    start_cmd = './get_ftrace_io.sh ' + ftrace_type + '_start'
    stop_cmd = './get_ftrace_io.sh ' + ftrace_type + '_stop'
    os.system(start_cmd)
    time.sleep(7)
    os.system(stop_cmd)

def get_filename_from_inode(inodeNo):
    filename = ''
    with open('./output/inodes.txt') as f:
        lines = f.readlines()
    for l in lines:
        if l.find(inodeNo) != -1:
            filename = l.split()[2].replace('"', '')
            #print("filename =>", filename)
            break
    return filename

def parse_ftrace_data(ftrace_type, threadLabel):
    ftrace_file = './output/trace_' + ftrace_type + '.ftrace'
    in_action = False
    thread_label = payload = ''
    inode = ['', '']
    pos = ['', '']
    length = ['', '']
    print("thread, filename, pos, length")
    with open(ftrace_file) as f:
        lines = f.readlines()
    for l in lines:
        if ftrace_type == 'ext4':
            if l.find('ext4_da_write_begin:') != -1:
                in_action = True
                thread_label = l.split()[0]
                if thread_label != threadLabel:
                    continue
                payload = l[l.find('ino'):].split()
                #print("******** l, payload", l, payload)
                inode[0] = payload[1]
                pos[0] = payload[3]
                length[0] = payload[5]
            elif l.find('ext4_da_write_end:') != -1:
                if not in_action:
                    continue
                thread_label = l.split()[0]
                if thread_label != threadLabel:
                    continue
                payload = l[l.find('ino'):].split()
                inode[1] = payload[1]
                pos[1] = payload[3]
                length[1] = payload[5]
                copied = payload[7]
                if length[1] == copied and inode[0] == inode[1] and pos[0] == pos[1] and length[0] == length[1]:
                    print("%s, %s, %s, %s"%(thread_label, get_filename_from_inode(inode[0]), pos[0], length[0]))
                in_action = False


def dump_inodes():
    root_cmd = 'root'
    remount_cmd = 'remount'
    disable_verity = 'disable-verity'
    reboot_cmd = 'reboot'
    devices_cmd = 'devices'
    os.system('adb ' + root_cmd)
    time.sleep(2)
    status, output = commands.getstatusoutput('adb ' + disable_verity)
    if output.find('Verity already disabled') == -1:
        os.system('adb ' + reboot_cmd)
        time.sleep(30)
        os.system('adb ' + root_cmd)
        time.sleep(2)
    os.system('adb ' + remount_cmd)
    status, output = commands.getstatusoutput('adb ' + devices_cmd)
    lines = output.splitlines()
    deviceId = ''
    for line in lines:
        pos = line.find('List of devices')
        if pos == -1:
            deviceId = line.split()[0]
            break
    compulse_cmd = './inode/compulse_inodes.py ' + deviceId + ' > ./output/inodes.txt'
    os.system(compulse_cmd)
    return deviceId

if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], "hpc")
    for op, value in opts:
        if op == "-h":
            print("python rlbench_trace_analyzer.py -p => -c")
            sys.exit()
        elif op == "-p":
            deviceId = dump_inodes()
            print("deviceId:", deviceId)
            sys.exit()
        elif op == "-c":
            (threadId, threadName) = get_sqlite_1000inserts_thread()
            collect_ftrace_data('ext4')
            parse_ftrace_data('ext4', threadName+'-'+threadId)
            sys.exit()

