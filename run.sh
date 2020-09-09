#!/bin/bash

export PYTHONPATH=/home/ubuntu/trend

pkill --echo gunicorn
sleep 3

authbind gunicorn src.web:server \
  --bind :443 \
  --keyfile /home/ubuntu/certs/privkey1.pem \
  --certfile /home/ubuntu/certs/cert1.pem \
  --ca-certs /home/ubuntu/certs/chain1.pem \
  --daemon
