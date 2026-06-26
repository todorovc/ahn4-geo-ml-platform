#!/usr/bin/env bash
set -e
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/ingest/requirements.txt
pip install -r apps/processing/requirements.txt
