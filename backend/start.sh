#!/bin/bash

# Install dependencies using uv
echo "Installing requirements using uv..."
uv pip install -r requirements.txt

# Start the server
echo "Starting FastAPI server..."
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload