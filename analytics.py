import matplotlib.pyplot as plt
from collections import Counter
import os


class Analytics:
    def __init__(self, results_folder: str, output_folder: str, suffix: str):
        self.results_folder = results_folder
        self.output_folder = output_folder
        self.suffix = suffix

    def get_latest_summary(self):
        latest_file = max(
            (f for f in os.listdir(self.results_folder) if f.endswith("-summary.json")),
            key=lambda f: os.path.getmtime(os.path.join("results", f)),
        )
        # Construct the file path
        return os.path.join("results", latest_file)

    def plot_failed_responses_summary(self, data: dict):
        # Extract relevant information
        failed_responses = (
            data.get("metrics", {})
            .get("classification_accuracy", {})
            .get("failed_responses", [])
        )

        # Count the occurrences of each intent
        intent_counts = Counter(
            response["prompt"]["Intent"] for response in failed_responses
        )

        # Prepare data for plotting
        intents = list(intent_counts.keys())
        counts = list(intent_counts.values())

        # Calculate the total number of responses
        total_responses = sum(counts)

        # Calculate the distribution of each intent
        intent_distribution = {
            intent: count / total_responses for intent, count in intent_counts.items()
        }

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
        summary_text += "Intent Distribution:\n"
        for intent, distribution in intent_distribution.items():
            summary_text += f"{intent}: {distribution:.2%} ({intent_counts[intent]}/{total_responses})\n"

        # Show the plot
        plt.text(
            0.8,
            0.8,
            summary_text,
            transform=plt.gca().transAxes,
            fontsize=12,
            verticalalignment="center",
            horizontalalignment="center",
            bbox=dict(facecolor="white", alpha=0.5),
        )
        plt.savefig(
            os.path.join(self.output_folder, f"failed_responses_summary-{self.suffix}.png"),
            dpi=300,
        )

    def plot_intent_distribution(self, data: dict):
        # Extract relevant information
        per_intent = data["per_intent"]

        # Prepare data for plotting
        intents = list(per_intent.keys())
        counts = list(per_intent.values())

        # Create the pie chart
        plt.figure(figsize=(10, 6))
        plt.pie(counts, labels=intents, autopct="%1.1f%%")
        plt.title("Intent Distribution")

        # Show the plot
        plt.savefig(
            os.path.join(self.output_folder, f"intent_distribution-{self.suffix}.png"),
            dpi=300,
        )
