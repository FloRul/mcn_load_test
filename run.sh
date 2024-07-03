#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# On peut passer un argument pour passer l'URL a tester
DNS=${1:-dkmwo6pd6rra6.cloudfront.net}

# Configuration
WEBSOCKET_URL="wss://${DNS}/socket"
ORIGIN="https://${DNS}"
PROMPTS_FILE="./datasets/redirection.jsonl"
CONNECTIONS=20
MAX_LATENCY=20  # Maximum acceptable average latency in seconds
MIN_RPS=5      # Minimum acceptable requests per second
MIN_SUCCESS_RATE=95  # Minimum acceptable success rate (percentage)

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install websockets

# Create prompts file if it doesn't exist
if [ ! -f "$PROMPTS_FILE" ]; then
    echo "Creating sample prompts file..."
    echo -e "Hello, how are you?\nWhat's the weather like today?\nTell me a joke." > "$PROMPTS_FILE"
fi
# Run the load test
echo "Running load test..."
python load_test.py "$WEBSOCKET_URL" "$PROMPTS_FILE" --origin "$ORIGIN" --connections "$CONNECTIONS"
python_exit_code=$?

echo "Python script exit code: $python_exit_code"

if [ $python_exit_code -ne 0 ]; then
    echo "Load test script failed with exit code $python_exit_code"
    exit 1
fi

echo "Load test completed"
exit 0
