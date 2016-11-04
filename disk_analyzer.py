import os,sys,re,copy

#quick init
f = sys.argv[1]
h = open(f)
rs = []
txt_usage = "disk_analyzer [trace file]"
txt_installation = "sudo apt-get install build-essential python-dev python-setuptools python-numpy python-scipy libatlas-dev libatlas3gf-base \
sudo apt-get install python-matplotlib \
sudo apt-get install python-sklearn \
setests -v sklearn"

print txt_usage
print txt_installation
print "******"

#read in records (O(n))
for l in h.readlines():
	#read lines, bypassing no ftrace lines and not block rq lines
	if l[0] != ' ':
		continue
	_t1 = re.split(" +",l,0)
	c = _t1[7][0:-1]
	if not re.match("block_rq",c):
		continue 

	#extract elements: k = key (block id), t = time (us), b = block size (bytes), v = dev id (xxx,xxx), s = speed (MB/s), d = duration (us)
	#f = io flag (Flush,Write,Discard,Read,N,Fua,Ahead,Sync,Meta,sEcure, see blktrace.c & blk_types.h)
	#ib = @ blended interval (us)
	#iv = @ same dev interval (us)
	#if = @ same op interval (us)

	k = _t1[-4]
	t = float(_t1[6][0:-1])*1000000
	b = int(_t1[-2])*512
	f = _t1[-7]
	v = _t1[-8]
	if re.match("[0-9]+\,[0-9]+",f):
		f = _t1[-6]
		v = _t1[-7]
	rs.append({"c":c, "t":t, "k":k, "b":b, "d":-1, "s":-1, "f":f, "v":v, "ib":-1, "iv":-1, "if":-1})

#pair issue/complete and calculate speed (O(n))
#forward pairing window = 128 records
lmt = len(rs)
sw = 128
i = 0

while i < lmt:
	#search pair forwardly, dev id && block id should match
	paired = False
	for j in range(i+1, min(lmt, i+sw+1)):
		if rs[j]["k"] == rs[i]["k"] and rs[j]["v"] == rs[i]["v"]:
			rs[i]["d"] = rs[j]["t"] - rs[i]["t"]
			rs[i]["s"] = rs[i]["b"] / rs[i]["d"] * 1000000 / 1024 / 1024
			paired = True
			del rs[j]
			break
	#not paired, del the pending record
	#paired, increment a record
	#then reclculate the search ending
	if not paired:
		del rs[i]
	else:
		i = i + 1
	lmt = len(rs)

#statistics
#O(n) resort
cs = {}
_i = 0
for r in rs:
	if r["v"] not in cs.keys():
		cs.setdefault((r["v"],"ALL"), {"statistics":{}, "record":[]})
	if (r["v"], r["f"]) not in cs.keys():
		cs.setdefault((r["v"],r["f"]), {"statistics":{}, "record":[]})
	cs[(r["v"],"ALL")]["record"].append(r)
	cs[(r["v"],r["f"])]["record"].append(r)

	#update intervals
	if _i >= 1:
		rs[_i]["ib"] = rs[_i]["t"] - rs[_i-1]["t"]
	if len(cs[(r["v"],"ALL")]["record"]) > 1:
		rs[_i]["iv"] = rs[_i]["t"] - cs[(r["v"],"ALL")]["record"][-2]["t"]
	if len(cs[(r["v"],r["f"])]["record"]) > 1:
		rs[_i]["if"] = rs[_i]["t"] - cs[(r["v"],r["f"])]["record"][-2]["t"]
	_i += 1

#per class statistics
from sklearn import cluster, datasets
import numpy as np

kv = 4	#number of k-means classes, use 8 based on experience
for c in cs.keys():
	#total & percentage
	cs[c]["statistics"]["total"] = len(cs[c]["record"])
	cs[c]["statistics"]["percentage"] = round(len(cs[c]["record"])*100.0/cs[(c[0],"ALL")]["statistics"]["total"])

	#sub-class, clustering is only carried out on flags == ALL
	if c[1] == "ALL":
		_t2 = []
		for n in cs[c]["record"]:
			_t2.append(float(n["b"]))
		_t3 = np.reshape(np.array(_t2),(-1,1))
		k_means = cluster.KMeans(k=kv)
		k_means.fit(_t3)
		for _i in range(len(cs[c]["record"])):
			cs[c]["record"][_i]["cb"] = k_means.labels_[_i]	#cb: newly added to records, class based on blocks

#run another round calculation to calculate the details based on cb
def calc(r, k, f):
	_t = []
	for _r in r:
		_t.append(_r[k])
	if f == "avg":
		return np.mean(np.array(_t))
	elif f == "std":
		return np.std(np.array(_t))
	elif f == "median":
		return np.median(np.array(_t))
		
	return 0.0
	
for c in cs.keys():
	#build classes
	cs[c]["record"] = sorted(cs[c]["record"], key = lambda x: x["cb"])
	_t4 = []
	cs[c]["statistics"]["classes"] = []
	for _i in range(len(cs[c]["record"])):
		_r = cs[c]["record"][_i]
		if _r["cb"] not in _t4:
			_t4.append(_r["cb"])
			cs[c]["statistics"]["classes"].append({"start":_i, "end":-1})
			if len(cs[c]["statistics"]["classes"]) > 1:
				cs[c]["statistics"]["classes"][-2]["end"] = _i
	cs[c]["statistics"]["classes"][-1]["end"] = len(cs[c]["record"])

	#run class statistics
	for _c in cs[c]["statistics"]["classes"]:
		_c["total"] = _c["end"] - _c["start"]
		_c["avg_size"] = calc(cs[c]["record"][_c["start"]:_c["end"]], "b", "median");
		_c["std_size"] = calc(cs[c]["record"][_c["start"]:_c["end"]], "b", "std");
		_c["avg_speed"] = calc(cs[c]["record"][_c["start"]:_c["end"]], "s", "median");
		_c["std_speed"] = calc(cs[c]["record"][_c["start"]:_c["end"]], "s", "std");
		_c["avg_latency"] = calc(cs[c]["record"][_c["start"]:_c["end"]], "d", "median");
		_c["std_latency"] = calc(cs[c]["record"][_c["start"]:_c["end"]], "d", "std");
		_c["avg_intv_v"] = calc(cs[c]["record"][_c["start"]:_c["end"]], "iv", "median");
		_c["std_intv_v"] = calc(cs[c]["record"][_c["start"]:_c["end"]], "iv", "std");
		_c["avg_intv_f"] = calc(cs[c]["record"][_c["start"]:_c["end"]], "if", "median");
		_c["std_intv_f"] = calc(cs[c]["record"][_c["start"]:_c["end"]], "if", "std");

#show
indent = "      "
print "trace name = %s"% sys.argv[1]
v_showed = []
for c in sorted(cs.keys()):
	if c[0] not in v_showed:
		print "[%s] ******************************"% c[0]
		v_showed.append(c[0])
	print c[1]
	print "%s total = %d (%.02f%%)"% (indent, cs[c]["statistics"]["total"], cs[c]["statistics"]["percentage"])
	for _c in cs[c]["statistics"]["classes"]:
		print "%s%s size = %.02f(%.02f)B, n = %d(%.02f%%), speed = %.02f(%.02f)MB/s, blended intv = %.02f(%.02f)us, in-group intv = %.02f(%.02f)us, latency = %.02f(%.02f)us"% (indent,indent,
			_c["avg_size"],_c["std_size"],
			_c["total"],_c["total"]*100/cs[c]["statistics"]["total"],
			_c["avg_speed"], _c["std_speed"],
			_c["avg_intv_v"], _c["std_intv_v"],
			_c["avg_intv_f"], _c["std_intv_f"],
			_c["avg_latency"], _c["std_latency"])

	#FIXME: debug use
	if c[1] != "ALL":
		continue
	for i in sorted(cs[c]["record"], key = lambda x : x["t"]):
		print "(t) %s (flag) %s (iv) %s (if) %s (d) %s"% (i["t"], i["f"], i["iv"], i["if"], i["d"])
