#!/usr/bin/env python3

import os,sys,re,copy,getopt

#quick init
record = []
rw_chaos = 0
txt_installation = "sudo apt-get install build-essential python-dev python-setuptools python-numpy python-scipy libatlas-dev libatlas3gf-base \
sudo apt-get install python-matplotlib \
sudo apt-get install python-sklearn \
setests -v sklearn"

SECTOR = 512
CMD_READ_MULTI = 18
CMD_WRITE_MULTI = 25

def parse_lines(path):
	ts = te = 0.0; ms = me = 0; rs = re = 0; ws = we = 0
	rw_state = 0
	with open(path) as f:
		lines = f.readlines()
	for l in lines:
		if l[0] != ' ':
			continue
		if l.find("mmc_blk_rw_start") != -1:
			print("__tingjie")
			if rw_state == 1:
				global rw_chaos
				rw_chaos += 1
			ts = float(l.split(']')[1].split(':')[0].split()[1])
			ms = int(l.split('cmd=')[1].split(',addr=')[0])
			rs = int(l.split('addr=0x')[1].split(',size=')[0], 16)
			ws = int(l.split('size=0x')[1].split('\\n')[0], 16) * SECTOR
			print("** start ts:%f ms:%d, addr:%x, wl:%d" %(ts, ms, rs, ws))
			rw_state = 1
			continue
		elif l.find("mmc_blk_rw_end") != -1:
			if rw_state != 1:
				rw_chaos += 1
			te = float(l.split(']')[1].split(':')[0].split()[1])
			me = int(l.split('cmd=')[1].split(',addr=')[0])
			re = int(l.split('addr=0x')[1].split(',size=')[0], 16)
			we = int(l.split('size=0x')[1].split('\\n')[0], 16) * SECTOR
			#print("## end te:%f me:%d, addr:%x, wl:%d" %(te, me, re, we))
			rw_state = 0
			if ms == me and rs == re and ws == we:
				record.append({"s": ts, "t":te-ts, "m":ms, "r":rs, "w":ws})
				print("^^ append: t %f, m %d r %x w %d" %(te-ts, ms, rs, ws))
			continue
		else:
			continue 

def process_record():
	tr_tp = tw_tp = 0.0; tr_wl = tw_wl = 0; tr_dr = tw_dr = 0.0
	for i in record:
		if i["m"] == CMD_READ_MULTI:
			tr_wl += i["w"]
			tr_dr += i["t"]
		elif i["m"] == CMD_WRITE_MULTI:
			tw_wl += i["w"]
			tw_dr += i["t"]

	if tr_dr != 0.0:
		tr_tp = float(tr_wl) / (tr_dr * 1024 * 1024)
	if tw_dr != 0.0:
		tw_tp = float(tw_wl) / (tw_dr * 1024 * 1024)
	print("average throughput: read %f MB/s, write %f MB/s, rw_chaos %d" %(tr_tp, tw_tp, rw_chaos))

	print("command,start,duration,address,workload,interval,throughput")
	last = 0
	for i in record:
		print("%d,%d,%d,%x,%d,%d,%f" %(i["m"], int(i["s"]*1000000), int(i["t"]*1000000), i["r"], i["w"], int(i["s"]*1000000)-last, i["w"]/(i["t"]*1024*1024)))
		last = int(i["s"]*1000000)

if __name__ == "__main__":
	opts, args = getopt.getopt(sys.argv[1:], "hp:")
	for op, value in opts:
		if op == "-p":
			path = value
			print("Get file {0}".format(path))
			parse_lines(path)
			process_record()
			sys.exit()
		elif op == "-h":
			print("Usage: python mmc_analyzer.py -p YOUR_FULL_PATH_NAME")
			sys.exit()
