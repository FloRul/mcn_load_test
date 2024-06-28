# WebSocket Load Tester for AWS API Gateway

This project provides a set of tools to perform load testing on WebSocket endpoints, specifically designed for AWS API Gateway. It includes a Python script for executing the load test and a PowerShell script for running the test and analyzing results.

## Features

- Concurrent WebSocket connections
- Customizable number of connections and prompts
- Progress tracking during test execution
- Detailed latency statistics (average, median, min, max, 95th and 99th percentiles)
- JSON summary output for easy integration with other tools
- Configurable thresholds for test pass/fail criteria

## Requirements

- Python 3.9+
- PowerShell (for Windows users)
- `websockets` Python library

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/FloRul/mcn_load_test.git
   cd mcn-load-tester
   ```

2. (Optional) Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: .\venv\Scripts\Activate.ps1
   ```

3. Install the required Python package:
   ```bash
   pip install websockets
   ```

## Usage

1. Prepare your test prompts:
   Create a file named `prompts.txt` with one prompt per line. For example:

   ```text
   Hello, how are you?
   What's the weather like today?
   Tell me a joke.
   ```

2. Configure the test parameters:
   Open `run.sh` and modify the following variables as needed:

   ```text
   $WEBSOCKET_URL = "wss://your-api-gateway-url.execute-api.region.amazonaws.com/stage"
   $ORIGIN = "https://example.com"
   $PROMPTS_FILE = "prompts.txt"
   $CONNECTIONS = 20
   $MAX_LATENCY = 0.5
   $MIN_RPS = 100
   $MIN_SUCCESS_RATE = 95
   ```

3. Run the load test:

   To overrode default DNS, pass it as argument.

    ```bash
    bash ./run_load_test.sh  discussion.test.robco.si.gouv.qc.ca
    ```

4. Review the results:

   - The script will display a summary of the test results in the console.
   - A detailed JSON summary will be saved in `load_test_summary.json`.

## Understanding the Results

The load test provides the following metrics:

- Total Requests: The total number of WebSocket messages sent
- Successful Requests: The number of messages that received a response without errors
- Total Time: The duration of the entire test
- Requests per second: The average number of requests processed per second
- Latency statistics: Average, median, min, max, 95th percentile, and 99th percentile latencies

The test will fail if:

- The average latency exceeds `MAX_LATENCY`
- The requests per second fall below `MIN_RPS`
- The success rate (percentage of successful requests) is below `MIN_SUCCESS_RATE`

## Customizing the Test

To modify the test behavior or add new features:

1. Edit `load_test.py` to change the core load testing logic.
2. Modify `run.sh` to adjust how the test is executed and how results are processed.
