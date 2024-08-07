# WebSocket Tester for Chatbot Response Testing

This solution is designed to test the response of a chatbot using WebSocket connections. It includes a Python-based tester and a shell script to set up and run the test.

## Table of Contents

1. [Overview](#overview)
2. [Components](#components)
3. [Setup](#setup)
4. [Usage](#usage)
5. [Configuration](#configuration)
6. [Output](#output)
7. [Analytics](#analytics)

## Overview

The WebSocket Load Tester is a tool for evaluating the performance and accuracy of a chatbot by simulating multiple concurrent connections and analyzing the responses. It uses WebSocket connections to communicate with the chatbot, sends predefined prompts, and collects various metrics on the responses.

## Components

The solution consists of the following main components:

1. `run_quality_test.py`: The main Python script that performs the testing.
2. `core.py`: Contains the `WebSocketLoadTester` and `Metric` classes for managing the quality test and computing metrics.
3. `analytics.py`: Provides functionality for generating visual analytics of the test results.
4. `run_quality_test.sh`: A shell script for setting up the environment and running the quality test.

## Setup

To set up the environment and run the quality test, follow these steps:

1. Ensure you have Python 3 installed on your system.
2. Place your test prompts in JSON Line (`.jsonl`) format in the `./datasets` directory.
3. Make sure you have the required Python packages listed in `requirements.txt`.

## Usage

To run the quality test, execute the `run_quality_test.sh` script after making sure the values are correct:

```bash
./run_quality_test.sh
```

The script will:
1. Create and activate a virtual environment
2. Install the required dependencies
3. Run the quality test
4. Clean up the output folder, keeping only the zip files with results

## Configuration

The quality test can be configured using the following parameters in the `run_quality_test.sh` script:

- `WEBSOCKET_URL`: The WebSocket URL for connecting to the chatbot
- `ORIGIN`: The origin for the WebSocket connection
- `OUTPUT_FOLDER`: The folder to save output files
- `CONNECTIONS`: The number of concurrent connections to simulate
- `MAX_SAMPLES`: The maximum number of samples to use (-1 for all samples)

## Output

The quality test generates the following outputs:

1. JSON files with detailed results
2. A summary JSON file with aggregated statistics
3. PNG files with visualizations of the results
4. A zip file containing all the output files

## Analytics

The `Analytics` class in `analytics.py` provides two main visualizations:

1. `plot_failed_responses_summary`: Creates a bar plot showing the distribution of misclassified intents.
2. `plot_intent_distribution`: Generates a pie chart displaying the distribution of intents in the test dataset.

These visualizations are automatically generated and saved as PNG files in the output folder.

---