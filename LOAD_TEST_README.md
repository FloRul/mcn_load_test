# Dynamic WebSocket Load Tester for Chatbot Response Testing

This solution is designed to perform dynamic load testing on a chatbot using WebSocket connections. It includes a Python-based load tester and a shell script to set up and run the test with increasing connection counts.

## Table of Contents

1. [Overview](#overview)
2. [Components](#components)
3. [Setup](#setup)
4. [Usage](#usage)
5. [Configuration](#configuration)
6. [Output](#output)
7. [Visualization](#visualization)

## Overview

The Dynamic WebSocket Load Tester is a tool for evaluating the performance and scalability of a chatbot by simulating multiple concurrent connections with incremental increases. It uses WebSocket connections to communicate with the chatbot, sends predefined prompts, and collects various metrics on the responses, including latency and error rates.

## Components

The solution consists of the following main components:

1. `run_dynamic_load_test.py`: The main Python script that performs the dynamic load testing.
2. `core.py`: Contains the `WebSocketTester` and `Metric` classes for managing the load test and computing metrics.
3. `run_dynamic_load_test.sh`: A shell script for setting up the environment and running the dynamic load test.

## Setup

To set up the environment and run the dynamic load test, follow these steps:

1. Ensure you have Python 3 installed on your system.
2. Place your test prompts in JSON Line (`.jsonl`) format in the `./datasets` directory.
3. Make sure you have the required Python packages listed in `requirements.txt`.

## Usage

To run the dynamic load test, execute the `run_dynamic_load_test.sh` script:

```bash
./run_dynamic_load_test.sh
```

The script will:
1. Create and activate a virtual environment
2. Install the required dependencies
3. Run the dynamic load test
4. Save the results and generate visualizations

## Configuration

The dynamic load test can be configured using the following parameters in the `run_dynamic_load_test.sh` script:

- `WEBSOCKET_URL`: The WebSocket URL for connecting to the chatbot
- `ORIGIN`: The origin for the WebSocket connection
- `OUTPUT_FOLDER`: The folder to save output files
- `MAX_CONNECTIONS`: The maximum number of concurrent connections to simulate
- `STEP_SIZE`: The number of new connections added in each step
- `THINK_TIME`: The time to wait between steps (in seconds)
- `MAX_SAMPLES`: The maximum number of prompts to sample (-1 for all samples)
- `PROMPTS_FOLDER`: The folder containing prompt JSONL files
- `QUEUE_SIZE`: The maximum number of messages in the queue per connection

## Output

The dynamic load test generates the following outputs:

1. A JSON file with detailed results for each connection count
2. A PNG file with a plot visualizing the test results
3. A log file (`dynamic_load_test_output.log`) containing the test execution details

## Visualization

The `plot_results` function in `run_dynamic_load_test.py` creates a visualization of the test results, including:

1. Average latency vs. number of connections
2. Maximum latency vs. number of connections
3. General error rate vs. number of connections
4. Client error rate vs. number of connections
5. Unexpected error rate vs. number of connections

This visualization is saved as a PNG file in the output folder.

---