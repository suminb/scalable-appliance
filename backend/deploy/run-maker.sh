#!/bin/bash

file=$1
name=${file%.*}

cpus=`grep -c "^processor" /dev/cpuinfo`

for i in $(seq `expr $cpus - 1`);
do
    maker -genome $file -nodatastore -base $name --tries 3 &
done;

maker -genome $file -nodatastore -base $name --tries 3
