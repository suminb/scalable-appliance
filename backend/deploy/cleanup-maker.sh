#!/bin/bash
name=${WORK_FILE%.*}
mv $name.maker.output/${name}_datastore/*/*/*.gff $name.gff

echo "DONE!"
