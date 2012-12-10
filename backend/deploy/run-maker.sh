#!/bin/bash

file=$1
name=${file%.*}

maker -genome $file -nodatastore -base $name --tries 3
