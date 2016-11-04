#!/bin/bash

function trace_help() {
	echo "Help: <========================="
	echo "./get_ftrace.sh block_start | block_stop | ext4_start | ext4_stop | pagecache_start | pagecache_stop"
}

if [ ! -n "$1" ]; then
	trace_help
elif [ $1 = "block_start" ]; then
	adb shell "echo 1 > /d/tracing/events/block/enable"
	adb shell "echo > /d/tracing/trace"
	adb shell "echo 1 > /d/tracing/tracing_on"
	echo "block start"
elif [ $1 = "block_stop" ]; then
	adb shell "cat /d/tracing/trace" > ./trace_block_$(date +%T).ftrace
	adb shell "echo 0 > /d/tracing/tracing_on"
	adb shell "echo 0 > /d/tracing/events/block/enable"
	echo "block stopped"
elif [ $1 = "ext4_start" ]; then
	adb shell "echo 1 > /d/tracing/events/ext4/enable"
	adb shell "echo > /d/tracing/trace"
	adb shell "echo 1 > /d/tracing/tracing_on"
	echo "ext4 start"
elif [ $1 = "ext4_stop" ]; then
	adb shell "cat /d/tracing/trace" > ./trace_ext4_$(date +%T).ftrace
	adb shell "echo 0 > /d/tracing/tracing_on"
	adb shell "echo 0 > /d/tracing/events/ext4/enable"
	echo "ext4 stopped"
elif [ $1 = "syscalls_start" ]; then
	adb shell "echo 1 > /d/tracing/events/syscalls/enable"
	adb shell "echo 1 > /d/tracing/events/block/enable"
	adb shell "echo 1 > /d/tracing/events/ext4/enable"
	adb shell "echo > /d/tracing/trace"
	adb shell "echo 1 > /d/tracing/tracing_on"
	echo "syscalls start"
elif [ $1 = "syscalls_stop" ]; then
	adb shell "cat /d/tracing/trace" > ./trace_syscalls_$(date +%T).ftrace
	adb shell "echo 0 > /d/tracing/tracing_on"
	adb shell "echo 0 > /d/tracing/events/syscalls/enable"
	adb shell "echo 0 > /d/tracing/events/block/enable"
	adb shell "echo 0 > /d/tracing/events/ext4/enable"
	echo "syscalls stopped"
elif [ $1 = "filemap_start" ]; then
	adb shell "echo 1 > /d/tracing/events/filemap/enable"
	adb shell "echo 1 > /d/tracing/events/vmscan/enable"
	adb shell "echo > /d/tracing/trace"
	adb shell "echo 1 > /d/tracing/tracing_on"
	echo "filemap_start\n----------------------\n" > ./pagecache.vmstat
	adb shell 'cat /proc/meminfo' >> ./pagecache.vmstat
	echo "filemap start"
elif [ $1 = "filemap_stop" ]; then
	echo "filemap_stop\n----------------------\n" >> ./pagecache.vmstat
	adb shell 'cat /proc/meminfo' >> ./pagecache.vmstat
	mv ./pagecache.vmstat ./filemap_$(date +%T).vmstat
	adb shell "cat /d/tracing/trace" > ./trace_filemap_$(date +%T).ftrace
	adb shell "echo 0 > /d/tracing/tracing_on"
	adb shell "echo 0 > /d/tracing/events/filemap/enable"
	adb shell "echo 0 > /d/tracing/events/vmscan/enable"
	echo "filemap stopped"
elif [ $1 = "pagecache_start" ]; then
	adb shell 'cd /d/tracing;echo 0 > function_profile_enabled;echo nop > current_tracer;echo 1 > events/filemap/enable;printf "trace_mm_filemap_add_to_page_cache\ntrace_mm_filemap_delete_from_page_cache\n" > set_ftrace_filter;echo function > current_tracer'
	adb shell "cd /d/tracing;echo > /d/tracing/trace;echo 1 > tracing_on;echo 1 > function_profile_enabled"
	adb shell 'cat /proc/meminfo' > ./pagecache.vmstat
elif [ $1 = "pagecache_start" ]; then
	adb shell 'cd /d/tracing;echo 0 > function_profile_enabled;echo nop > current_tracer;echo 1 > events/filemap/enable;printf "trace_mm_filemap_add_to_page_cache\ntrace_mm_filemap_delete_from_page_cache\n" > set_ftrace_filter;echo function > current_tracer'
	adb shell "cd /d/tracing;echo > /d/tracing/trace;echo 1 > tracing_on;echo 1 > function_profile_enabled"
	adb shell 'cat /proc/meminfo' > ./pagecache.vmstat
	echo "pagecache trace start"
elif [ $1 = "pagecache_stop" ]; then
	adb shell 'cat /proc/meminfo' >> ./pagecache.vmstat
	mv ./pagecache.vmstat ./pagecache_$(date +%T).vmstat
	adb shell 'cat /d/tracing/trace_stat/function*' > ./pagecache_$(date +%T).ftrace
#	adb shell 'cat /d/tracing/trace' > ./trace_pagecache_$(date +%T).ftrace
	adb shell "cd /d/tracing;echo 0 > tracing_on;echo 0 > function_profile_enabled;echo > set_ftrace_filter;echo 0 > events/filemap/enable;echo nop > current_tracer"
	echo "pagecache trace stop"
elif [ $1 = "hitratio_start" ]; then
	adb shell 'cd /d/tracing;echo 0 > function_profile_enabled;echo nop > current_tracer;printf "mark_page_accessed\nmark_buffer_dirty\nadd_to_page_cache_lru\naccount_page_dirtied\n" > set_ftrace_filter;echo function > current_tracer'
	adb shell "cd /d/tracing;echo 1 > tracing_on;echo 1 > function_profile_enabled"
	echo "hitratio trace start"
elif [ $1 = "hitratio_stop" ]; then
	adb shell 'cat /d/tracing/trace_stat/function*' > ./hitratio_$(date +%T).ftrace
	adb shell "cd /d/tracing;echo 0 > tracing_on;echo 0 > function_profile_enabled;echo > set_ftrace_filter;echo nop > current_tracer"
	echo "hitratio trace stopped"
else
	trace_help
	exit 1
fi

exit 0
