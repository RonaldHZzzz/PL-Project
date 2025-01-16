#!/usr/bin/env bash

set -o errexit

#poetry install

#pip install -r requirements.txt

python manage.py collecstatic --no-input
python manage.py migrate 