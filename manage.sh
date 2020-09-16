#!/bin/bash

export PYTHONPATH=/home/ubuntu/trend

pkill --echo gunicorn
sleep 1

gunicorn src.web:wsgi --bind 127.0.0.1:8881 \
                      --log-file $PYTHONPATH/logs/web.log \
                      --log-level info \
                      --daemon

gunicorn src.schedule:wsgi --bind 127.0.0.1:8882 \
                           --log-file $PYTHONPATH/logs/schedule.log \
                           --log-level info \
                           --daemon
