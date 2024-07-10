import datetime
import json
from langfuse import Langfuse
from dotenv import load_dotenv
import os
from typing import Generator
from tqdm import tqdm

load_dotenv()
langfuse = Langfuse(
    secret_key=os.environ.get("LANGFUSE_SECRET_KEY", ""),
    public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
    host=os.environ.get("LANGFUSE_HOST"),
)


def is_langfuse_enabled():
    try:
        return langfuse.auth_check()
    except Exception as e:
        print(f"Langfuse is not enabled or not properly authenticated: {str(e)}")
        return False


def read_prompts(folder_path: str) -> Generator[dict, None, None]:
    for filename in os.listdir(folder_path):
        if filename.endswith(".jsonl"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf8") as file:
                for line in file:
                    try:
                        prompt = json.loads(line)
                        yield prompt
                    except (json.JSONDecodeError, KeyError):
                        print(f"Warning: Skipping invalid line in {filename}")


def main():
    if is_langfuse_enabled():
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dataset_name = os.environ.get(
            "LANGFUSE_DATASET_NAME", "load_test_dataset_" + current_time
        )
        langfuse.create_dataset(
            name=dataset_name,
            description="dataset created for load testing",
            metadata={
                "author": "Florian Rumiel",
                "date": current_time,
                "type": "automated",
            },
        )

        for prompt in tqdm(
            read_prompts("datasets"), desc="Uploading prompts to dataset"
        ):
            langfuse.create_dataset_item(
                dataset_name=dataset_name,
                input=prompt["Question"],
                metadata={
                    "intent": prompt.get("Intent", ""),
                    "refCount": prompt.get("RefCount", 0),
                },
            )

        print(f"Successfully uploaded prompts to dataset {dataset_name}")


if __name__ == "__main__":
    main()
