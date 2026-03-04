#!/bin/bash
# Force Python 3.11
export PYTHON_VERSION=3.11.0

# Install dependencies
pip install -r requirements.txt

# Run the app
uvicorn main:app --host 0.0.0.0 --port $PORT
