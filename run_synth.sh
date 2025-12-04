#!/bin/bash

# Install dependencies
pip install -r requirements.txt --break-system-packages

# Run the synthesizer
streamlit run sh101_synth.py --server.headless true
