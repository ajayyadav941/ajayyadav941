#!/bin/bash
set -e

cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  echo "ERROR: .venv not found. Create it with: python3 -m venv .venv"
  exit 1
fi

source .venv/bin/activate
mkdir -p reports
rm -f reports/results.xml

pytest -v -s tests/test_bgp.py tests/test_ping.py \
  --junitxml=reports/results.xml

ls -lh reports/results.xml
