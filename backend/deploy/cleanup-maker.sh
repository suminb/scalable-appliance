#!/bin/bash

name=${WORK_FILE%.*}
mv $name.maker.output/${name}_datastore/*/*/*.gff $name.gff

sleep 2m
echo "DONE!"
