#!/bin/bash

export PYTHONPATH=/home/ubuntu/trend

pkill --echo gunicorn
sleep 1

gunicorn src.web:wsgi --bind 127.0.0.1:8000 --daemon

