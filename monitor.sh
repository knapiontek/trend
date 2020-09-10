#!/bin/bash

pwd

while true;
do
  echo "%CPU %MEM ARGS $(date)" && ps -e -o pcpu,pmem,args --sort=pmem,pcpu | cut -d" " -f1-5 | tail -n 4
  sleep 60
done
