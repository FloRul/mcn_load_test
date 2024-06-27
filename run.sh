#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Configuration
WEBSOCKET_URL="wss://dkmwo6pd6rra6.cloudfront.net/socket"
ORIGIN="https://dkmwo6pd6rra6.cloudfront.net"
PROMPTS_FILE="prompts.txt"
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
echo "Running WebSocket load test..."
python websocket_load_tester.py "$WEBSOCKET_URL" "$PROMPTS_FILE" --origin "$ORIGIN" --connections "$CONNECTIONS"

# Read the JSON summary
if [ -f "load_test_summary.json" ]; then
    echo "Load test summary:"
    cat load_test_summary.json

    # Extract metrics from the JSON summary
    avg_latency=$(jq -r '.latency.average' load_test_summary.json)
    rps=$(jq -r '.requests_per_second' load_test_summary.json)
    total_requests=$(jq -r '.total_requests' load_test_summary.json)
    successful_requests=$(jq -r '.successful_requests' load_test_summary.json)

    # Calculate success rate
    success_rate=$(echo "scale=2; $successful_requests / $total_requests * 100" | bc)

    # Check if the metrics are within acceptable ranges
    if (( $(echo "$avg_latency > $MAX_LATENCY" | bc -l) )); then
        echo "Average latency ($avg_latency s) exceeds maximum threshold ($MAX_LATENCY s)"
        exit 1
    fi

    if (( $(echo "$rps < $MIN_RPS" | bc -l) )); then
        echo "Requests per second ($rps) is below minimum threshold ($MIN_RPS)"
        exit 1
    fi

    if (( $(echo "$success_rate < $MIN_SUCCESS_RATE" | bc -l) )); then
        echo "Success rate ($success_rate%) is below minimum threshold ($MIN_SUCCESS_RATE%)"
        exit 1
    fi

    echo "Load test passed successfully!"
else
    echo "Error: load_test_summary.json not found"
    exit 1
fi

exit 0