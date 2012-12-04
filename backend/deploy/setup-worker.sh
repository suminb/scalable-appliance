#!/bin/bash
set -e -x
export WORK_DIR=/home/ubuntu
export PROJECT="ACIC-TEST"
su ubuntu -l -c "work_queue_worker -a -s $WORK_DIR -o $WORK_DIR/worker.log -d all -N $PROJECT -z 5000 -t 86400 &"
