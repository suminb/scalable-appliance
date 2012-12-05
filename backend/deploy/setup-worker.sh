#!/bin/bash
set -e -x
export WORK_DIR=/home/ubuntu
export PROJECT="ACIC-TEST"
export SERVER="http://acic2012.iplantcollaborative.org/register_worker/"
curl --data="hostname=`hostname`" $SERVER
su ubuntu -l -c "work_queue_worker -a -s $WORK_DIR -o $WORK_DIR/worker.log -d all -N $PROJECT -z 5000 -t 86400 -b 15 &"
