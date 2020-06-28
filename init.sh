#!/usr/bin/env bash

cd /var/ton-work

echo "Update global config"
wget $global_config -O /var/ton-work/test.rocks.config.json

echo "Start gunicorn -w $core_count"
while [ 1 = 1 ]
do
gunicorn -w $core_count --threads 16 --capture-output --log-level debug --bind 0.0.0.0:4800 tonlib_http:app --access-logfile /var/ton-work/logs/access.log --error-logfile /var/ton-work/logs/error.log
date -u  >> /var/ton-work/logs/http.log
echo "gunicorn exited" >> /var/ton-work/logs/http.log
done
