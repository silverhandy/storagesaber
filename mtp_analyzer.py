#!/usr/bin/env python3

import os,sys,re,copy,getopt

#quick init
record = []
txt_installation = "sudo apt-get install build-essential python-dev python-setuptools python-numpy python-scipy libatlas-dev libatlas3gf-base \
sudo apt-get install python-matplotlib \
sudo apt-get install python-sklearn \
setests -v sklearn"

def parse_lines(path, strmp):
	ts = te = 0.0;
	in_process = 0
	es = ee = 0
	with open(path) as f:
		lines = f.readlines()
    	for l in lines:
		if l[0] != ' ':
			continue

		if l.find(strmp) == -1:
			continue

		if l.find("tracing_mark_write: S|") != -1:
			ts = float(l.split(']')[1].split(':')[0].split()[1])
			if (in_process == 1):
				es += 1
			in_process = 1
			continue
		elif l.find("tracing_mark_write: F|") != -1:
			te = float(l.split(']')[1].split(':')[0].split()[1])
			if (in_process == 0):
				ee += 1
			in_process = 0
			record.append({"s": ts, "t": te-ts})
			continue
		else:
			continue 

def process_record(strmp, xfer):
	t_tp = t_dr = t_wl = 0.0
	for i in record:
		if i["t"] > 10:
			continue
		t_wl += xfer
		t_dr += i["t"]

	t_tp = t_wl / (t_dr * 1024 * 1024)
	print("%s average throughput: %f MB/s" %(strmp, t_tp))

	print("start,duration,workload,interval,throughput")
	last = 0
	for i in record:
		print("%d,%d,%x,%d,%f" %(int(i["s"]*1000000), int(i["t"]*1000000), xfer, int(i["s"]*1000000)-last, xfer/(i["t"]*1024*1024)))
		last = int(i["s"]*1000000) + int(i["t"]*1000000)

if __name__ == "__main__":
	opts, args = getopt.getopt(sys.argv[1:], "hp:s:x:")
	path = strmp = ''; xfer = 0
	for op, value in opts:
		if op == "-p":
			path = value
			print("Get file {0}".format(path))
		elif op == "-s":
			strmp = value
			print("Get str {0}".format(strmp))
		elif op == "-x":
			xfer = int(value)
			print("Get xfer {0}".format(xfer))
			parse_lines(path, strmp)
			process_record(strmp, xfer)
			sys.exit()
		elif op == "-h":
			print("Usage: python mmc_analyzer.py -p YOUR_FULL_PATH_NAME -s STRING -x XFER_SIZE")
			sys.exit()
