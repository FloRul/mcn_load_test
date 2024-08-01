#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# On peut passer un argument pour passer l'URL a tester
DNS=${1:-discussion.test.robco.si.gouv.qc.ca}

# Configuration
WEBSOCKET_URL="wss://${DNS}/socket"
ORIGIN="https://${DNS}"
OUTPUT_FOLDER="./output"
MAX_CONNECTIONS=500
STEP_SIZE=5
THINK_TIME=2
MAX_SAMPLES=-1
PROMPTS_FOLDER="./datasets"
QUEUE_SIZE=10

# Setup virtual environment
python3 -m venv venv || { echo "Failed to create virtual environment";  }
source venv/bin/activate || { echo "Failed to activate virtual environment"; }

# Install dependencies
pip install -r requirements.txt || { echo "Failed to install dependencies";}

# Check if prompts folder exists and contains JSONL files
if [ ! -d "$PROMPTS_FOLDER" ] || [ -z "$(ls -A $PROMPTS_FOLDER/*.jsonl 2>/dev/null)" ]; then
    echo "Error: No JSONL files found in $PROMPTS_FOLDER"
fi

# Create output folder if it doesn't exist
mkdir -p "$OUTPUT_FOLDER"

# Run the dynamic load test
echo "Running dynamic load test..."
python run_dynamic_load_test.py \
    --ws "$WEBSOCKET_URL" \
    --origin "$ORIGIN" \
    --max-connections "$MAX_CONNECTIONS" \
    --step-size "$STEP_SIZE" \
    --think-time "$THINK_TIME" \
    --output "$OUTPUT_FOLDER" \
    --prompts-folder "$PROMPTS_FOLDER" \
    --max-samples "$MAX_SAMPLES" \
    --queue-size "$QUEUE_SIZE" \
    2>&1 | tee dynamic_load_test_output.log

python_exit_code=${PIPESTATUS[0]}

echo "Python script exit code: $python_exit_code"

if [ $python_exit_code -ne 0 ]; then
    echo "Dynamic load test script failed with exit code $python_exit_code"
    echo "Error details in ./dynamic_load_test_output.log"
    # exit 1
fi

echo "Dynamic load test completed"

# exit 0