#!/bin/bash

# Update and install system dependencies
apt-get update
apt-get install -y portaudio19-dev python3-distutils

# Upgrade pip and install setuptools and wheel
pip install --upgrade pip setuptools wheel

# Install Python dependencies
pip install -r requirements.txt
