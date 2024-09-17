#!/bin/sh 

sudo /usr/bin/mkdir -p /gsn
sudo mount -t nfs -o nolock,hard 10.2.4.94:/gsn-dcc-data-prod-us-east-2-74hfx024y /gsn
