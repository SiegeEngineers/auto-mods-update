#! /bin/bash

cd "$(dirname "$(realpath "$0")")";

source ./venv/bin/activate
./fetchCookie.py
