#!/bin/bash
while true;
    do curl --data "hostname="`curl -s http://169.254.169.254/latest/meta-data/public-hostname` http://acic2012.iplantcollaborative.org/update_worker;
    sleep 10; 
done
