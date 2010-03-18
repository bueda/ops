#!/bin/bash

export DJANGO_DEPLOYMENT_TYPE="PRODUCTION"
source ../buedaenv/bin/activate
./manage.py dumpdata --indent=2 feedback > ~/feedback.json
mysql -h django-rds.cvks7ybkczu6.us-east-1.rds.amazonaws.com -u peplin -peiBaequ4 < reset.sql
./manage.py syncdb --noinput
./manage.py migrate
