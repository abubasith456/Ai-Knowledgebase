#!/bin/bash

# Install dependencies using uv
echo "Installing requirements using uv..."
uv pip install -r requirements.txt

# Basic import check
echo "Checking imports..."
python3 -c "
try:
    from services.parsing import parse_with_docling
    print('✅ Parsing service imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
except Exception as e:
    print(f'❌ Unexpected error: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Import check failed. Please check your dependencies."
    exit 1
fi

# Start the server
echo "Starting FastAPI server..."
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload