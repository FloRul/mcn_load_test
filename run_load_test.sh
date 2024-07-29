#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# On peut passer un argument pour passer l'URL a tester
DNS=${1:-dkmwo6pd6rra6.cloudfront.net}

# Configuration
WEBSOCKET_URL="wss://${DNS}/socket"
ORIGIN="https://${DNS}"
OUTPUT_FOLDER="./output"
CONNECTIONS=5
MAX_SAMPLES=50

# Setup virtual environment
python3 -m venv venv || { echo "Failed to create virtual environment"; exit 1; }
source venv/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }

# Install dependencies
pip install -r requirements.txt || { echo "Failed to install dependencies"; exit 1; }

# Check if prompts folder exists and contains JSON files
if [ ! -d "./datasets" ] || [ -z "$(ls -A ./datasets/*.jsonl 2>/dev/null)" ]; then
    echo "Error: No JSONLine files found in ./datasets"
    exit 1
fi

# Run the load test
echo "Running load test..."
python main.py --w "$WEBSOCKET_URL" --max-samples "$MAX_SAMPLES" --o "$ORIGIN" --c "$CONNECTIONS" --out "$OUTPUT_FOLDER" 2>&1 | tee load_test_output.log
python_exit_code=${PIPESTATUS[0]}

echo "Python script exit code: $python_exit_code"

if [ $python_exit_code -ne 0 ]; then
    echo "Load test script failed with exit code $python_exit_code"
    echo "Error details in ./load_test.log"
    exit 1
fi

echo "Load test completed"

# Clean up the OUTPUT_FOLDER content, leaving only the zip files
echo "Cleaning up output folder..."
find "$OUTPUT_FOLDER" -type f ! -name "*.zip" -delete
echo "Output folder cleaned up"

exit 0