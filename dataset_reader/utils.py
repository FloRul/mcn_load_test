import json
from os import listdir
from os.path import isfile, join
from typing import Any, List, Dict


def read_files(folder_path: str, print_prompts: bool = False) -> List[Dict[str, Any]]:
    all_file_paths = get_all_file_paths(folder_path)
    prompts: List[Dict[str, Any]] = []

    if print_prompts:
        print(f"Files detected in the {folder_path} folder: {all_file_paths}")

    for file_path in all_file_paths:
        full_path = join(folder_path, file_path)
        if print_prompts:
            print(f"-> Reading file {full_path}")
        prompts.extend(read_file(full_path, print_prompts))

    if print_prompts:
        print(
            f"Total number of prompts in all {len(all_file_paths)} files: {len(prompts)}"
        )

    return prompts


def read_file(file_path: str, print_prompts: bool = False) -> List[Dict[str, Any]]:
    prompts: List[Dict[str, Any]] = []

    with open(file_path, "r", encoding="utf8") as json_file:
        for line in json_file:
            try:
                result = json.loads(line)
                prompts.append(
                    {"Intent": result["Intent"], "Question": result["Question"]}
                )
            except json.JSONDecodeError:
                print(f"Warning: Skipping invalid JSON in file {file_path}")

    if print_prompts:
        print(f"Prompt count in the file {file_path}: {len(prompts)}")

    return prompts


def get_all_file_paths(folder_path: str) -> List[str]:
    return [file for file in listdir(folder_path) if isfile(join(folder_path, file))]