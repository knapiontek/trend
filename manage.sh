#!/bin/bash

export PYTHONPATH=.

pkill --echo gunicorn
sleep 1

gunicorn src.web:wsgi --bind 127.0.0.1:8881 \
                      --worker-class eventlet \
                      --log-file $PYTHONPATH/logs/web.log \
                      --log-level info \
                      --timeout 90 \
                      --daemon

gunicorn src.schedule:wsgi --bind 127.0.0.1:8882 \
                           --worker-class eventlet \
                           --log-file $PYTHONPATH/logs/schedule.log \
                           --log-level info \
                           --timeout 90 \
                           --daemon
