import matplotlib.pyplot as plt
import json
from collections import Counter

# Load and parse the JSON data
with open("results/main-2024-07-08_21-49-56-summary.json", "r") as file:
    json_data = file.read()

    data = json.loads(json_data)

    # Extract relevant information
    accuracy = data["metrics"]["classification_accuracy"]["average"]
    failed_responses = data["metrics"]["classification_accuracy"]["failed_responses"]

    # Count the occurrences of each intent
    intent_counts = Counter(response["prompt"]["Intent"] for response in failed_responses)

    # Prepare data for plotting
    intents = list(intent_counts.keys())
    counts = list(intent_counts.values())

    # Create the bar plot
    plt.figure(figsize=(10, 6))
    plt.bar(intents, counts)
    plt.title("Misclassification Trend")
    plt.xlabel("Intent")
    plt.ylabel("Count")

    # Add value labels on top of each bar
    for i, count in enumerate(counts):
        plt.text(i, count, str(count), ha="center", va="bottom")

    # Add a text box with summary information
    summary_text = f"Total failed responses: {len(failed_responses)}\n"
    summary_text += f"Classification accuracy: {accuracy:.2%}"
    plt.text(
        0.95,
        0.95,
        summary_text,
        transform=plt.gca().transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    # Display the plot
    plt.tight_layout()
    plt.show()

    # Print detailed information about failed responses
    print("\nDetailed Failed Responses:")
    for i, response in enumerate(failed_responses, 1):
        print(f"\nFailed Response {i}:")
        print(f"Expected Intent: {response['prompt']['Intent']}")
        print(f"Actual Intent: {response['response']['intent'] or 'Not classified'}")
        print(f"Question: {response['prompt']['Question']}")
        print(f"Response: {response['response']['message']}")
