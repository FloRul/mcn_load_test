# WebSocket Load Tester for AWS API Gateway

This project provides a set of tools to perform load testing on WebSocket endpoints, specifically designed for AWS API Gateway. It includes a Python script for executing the load test and a PowerShell script for running the test and analyzing results.

## Features

- Concurrent WebSocket connections
- Customizable number of connections and prompts
- Progress tracking during test execution
- Detailed latency statistics (average, median, min, max, 95th and 99th percentiles)
- JSON summary output for easy integration with other tools
- Configurable thresholds for test pass/fail criteria
- Customizable metrics for evaluating responses

## Requirements

- Python 3.9+
- PowerShell (for Windows users) or bash shell
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

## Usage

1. Prepare your test prompts:
   Add into ./datasets a jsonl file with the following format : {"Intent":"dqgeneral","Question":"Je cherche des donnees..."}

2. Configure the test parameters:
   Open `run.sh` and modify the following variables as needed:
   ```text
   $WEBSOCKET_URL = "wss://your-api-gateway-url.execute-api.region.amazonaws.com/stage"
   $ORIGIN = "https://example.com"
   $PROMPTS_FOLDER = "./datasets"
   $CONNECTIONS = 20
   ```

3. Run the load test:
   To override default DNS, pass it as argument.
   ```bash
   source ./run.sh  discussion.test.robco.si.gouv.qc.ca
   ```

4. Review the results:
   - The script will display a summary of the test results in the console.
   - A detailed JSON summary will be saved in `main-YYYY-MM-DD_HH-MM-SS-summary.json`.

## Understanding the Results

The load test provides the following metrics:

- Total Requests: The total number of WebSocket messages sent
- Successful Requests: The number of messages that received a response without errors
- Total Time: The duration of the entire test
- Requests per second: The average number of requests processed per second
- Latency statistics: Average, median, min, max, 95th percentile, and 99th percentile latencies
- Custom metrics: Results of user-defined metrics for evaluating responses
- The list of failed query-response pairs according to their respective metric configuration

## Customizing the Test

To modify the test behavior or add new features:

1. Edit `main.py` to change the core load testing logic.
2. Modify `run.sh` to adjust how the test is executed and how results are processed.

## Customizing the Metrics

The load tester supports custom metrics to evaluate the quality and correctness of responses. To add or modify metrics:

1. Open `main.py` and locate the `get_metrics()` function.

2. Define new metric functions or modify existing ones. Each metric function should take two arguments (input and output) and return a float value.

3. Create a new `Metric` object for each metric you want to use. The `Metric` constructor takes three arguments:
   - `name`: A string identifier for the metric
   - `function`: The metric function you defined
   - `failure_condition`: (Optional) A function that determines if a response is considered a failure based on the metric score

4. Add your new `Metric` objects to the list returned by `get_metrics()`.

Example of adding a new metric:

```python
def get_metrics() -> List[Metric]:
    def new_metric(input: dict, output: dict) -> float:
        # Your metric logic here
        return score

    return [
        # Existing metrics
        Metric("classification_accuracy", classification_accuracy, failure_condition=lambda _, __, score: score == 0.0),
        Metric("ref_recall_count", ref_recall_count, failure_condition=lambda _, __, score: score == 0.0),
        # New metric
        Metric("new_metric_name", new_metric, failure_condition=lambda _, __, score: score < 0.5),
    ]
```

The results of your custom metrics will be included in the JSON summary output, showing the average score and any failed responses for each metric.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.