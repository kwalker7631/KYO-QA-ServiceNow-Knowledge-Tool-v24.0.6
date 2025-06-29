@echo off
REM Simple helper to install packages needed for running tests
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest flake8

