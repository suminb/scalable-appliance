#!/bin/bash

file=$1
name=${file%.*}
echo $name
maker -genome $file -nodatastore -base $name
