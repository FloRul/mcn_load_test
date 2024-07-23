# WebSocket Load Tester for AWS API Gateway

This project provides a set of tools to perform load testing on WebSocket endpoints, specifically designed for AWS API Gateway. It includes Python scripts for executing the load test and a bash script for setting up the environment and running the test.

## Features

- Concurrent WebSocket connections
- Customizable number of connections and prompts
- Progress tracking during test execution
- Detailed latency statistics (average, median, min, max, 95th and 99th percentiles)
- JSON output for both detailed results and summary
- Customizable metrics for evaluating responses
- Error logging
- Automated setup and execution via bash script

## Requirements

- Python 3.9+
- Bash shell (for running the setup script)
- Dependencies listed in `requirements.txt`

## Installation and Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/FloRul/mcn_load_test.git
   cd mcn_load_test
   ```

2. Ensure you have the necessary permissions to execute the bash script:
   ```bash
   chmod +x run_load_test.sh
   ```

## Usage

1. Prepare your test prompts:
   Create a folder named `datasets` in the project root, containing JSONL files with prompts in the following format:
   ```json
   {"Intent": "dqgeneral", "Question": "Je cherche des donnees...", "RefCount": "2"}
   ```

2. Run the load test using the bash script:
   ```bash
   ./run_load_test.sh [DNS]
   ```
   Where `[DNS]` is an optional argument to specify the DNS to test. If not provided, it defaults to `dkmwo6pd6rra6.cloudfront.net`.

   The script will:
   - Set up a virtual environment
   - Install dependencies from `requirements.txt`
   - Run the load test with the specified (or default) parameters
   - Output the result files in the output folder


## Configuration

You can modify the following variables in the `run_load_test.sh` script to customize the test:

- `WEBSOCKET_URL`: The WebSocket URL to test (default: `wss://${DNS}/socket`)
- `ORIGIN`: The origin for the WebSocket connection (default: `https://${DNS}`)
- `CONNECTIONS`: The number of concurrent connections (default: 20)
- `OUTPUT_FOLDER`: The folder where the results zip file will be placed

## Understanding the Results

The load test provides the following metrics:

- Total Requests: The total number of WebSocket messages sent
- Successful Requests: The number of messages that received a response without errors
- Total Time: The duration of the entire test
- Requests per second: The average number of requests processed per second
- Latency statistics: Average, median, min, max, 95th percentile, and 99th percentile latencies
- Custom metrics: Results of user-defined metrics for evaluating responses

## Customizing the Metrics

To add or modify metrics, edit the `get_metrics()` function in `main.py`. See the "Customizing the Metrics" section in the code comments for detailed instructions.

## Error Handling and Logging

- The Python script logs errors to `load_test.log`.
- The bash script logs all output to `load_test_output.log`.
- If the Python script fails, the bash script will display the last 20 lines of the log for quick debugging.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
