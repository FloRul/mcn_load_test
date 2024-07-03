#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# On peut passer un argument pour passer l'URL a tester
DNS=${1:-dkmwo6pd6rra6.cloudfront.net}

# Configuration
WEBSOCKET_URL="wss://${DNS}/socket"
ORIGIN="https://${DNS}"
PROMPTS_FOLDER="./datasets"
CONNECTIONS=20
MAX_LATENCY=20  # Maximum acceptable average latency in seconds
MIN_RPS=5      # Minimum acceptable requests per second
MIN_SUCCESS_RATE=95  # Minimum acceptable success rate (percentage)

# Setup virtual environment
python3 -m venv venv || { echo "Failed to create virtual environment"; exit 1; }
source venv/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }

# Install dependencies
pip install websockets urllib3

# Check if prompts folder exists and contains JSON files
if [ ! -d "$PROMPTS_FOLDER" ] || [ -z "$(ls -A $PROMPTS_FOLDER/*.jsonl 2>/dev/null)" ]; then
    echo "Error: No JSONLine files found in $PROMPTS_FOLDER"
    exit 1
fi

# Run the load test
echo "Running load test..."
python main.py "$WEBSOCKET_URL" "$PROMPTS_FOLDER" --origin "$ORIGIN" --connections "$CONNECTIONS" 2>&1 | tee load_test_output.log
python_exit_code=${PIPESTATUS[0]}

echo "Python script exit code: $python_exit_code"

if [ $python_exit_code -ne 0 ]; then
    echo "Load test script failed with exit code $python_exit_code"
    echo "Error details:"
    tail -n 20 load_test_output.log
    exit 1
fi

echo "Load test completed"
exit 0