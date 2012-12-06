#!/bin/bash

file=$1
name=${file%.*}
echo $name
<<<<<<< HEAD
=======
touch $name.gff
python setoption.py maker_opts.ctl maker_gff $name.gff
>>>>>>> 43d28ecea668073691cf03873e045c793f51ab37
maker -genome $file -nodatastore -base $name --tries 3
