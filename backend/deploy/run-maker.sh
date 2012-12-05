#!/bin/bash

file=$1
name=${file%.*}
echo $name
touch $name.gff
python setoption.py maker_opts.ctl maker_gff $name.gff
maker -genome $file -nodatastore -base $name --tries 3
