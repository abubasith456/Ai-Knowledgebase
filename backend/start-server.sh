#!/bin/bash

echo "🚀 Starting Knowledge Base Server Setup..."

# Install Python requirements
echo "📦 Installing Python requirements..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install

# Start the server
echo "🌟 Starting FastAPI server..."
python main.py
