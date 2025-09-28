#!/bin/bash

echo "🚀 Starting Knowledge Base Server Setup..."

# Install Python requirements
echo "📦 Installing Python requirements..."
pip install -r requirements.txt

# Install Playwright system dependencies
echo "🎭 Installing Playwright system dependencies..."
playwright install-deps

echo "🎭 Installing Playwright browsers..."
playwright install

echo "✅ Setup complete!"
# Remove this line: python main.py
