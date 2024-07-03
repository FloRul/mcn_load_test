import json
from Prompt import Prompt
from os import listdir
from os.path import isfile, join




def readFiles(folder_path: str, printPrompts = False) -> list[Prompt]:

    allFilesPath = getAllFilesPath(folder_path)
    prompts: list[Prompt] = []
    print(f"files detected in the {folder_path} folder : {allFilesPath}") if printPrompts else False
        
    for file_path in allFilesPath:

        print (f"-> reading file {folder_path}/{file_path} ") if printPrompts else False
        prompts.extend(readFile(f"{folder_path}/{file_path}", printPrompts))

    print (f"total number of prompts in all {len(allFilesPath)} files: {len(prompts)} ") if printPrompts else False
    return prompts


def readFile(file_path: str, printPrompts = False) -> list[Prompt]:

    prompts: list[Prompt] = []

    with open(file_path, 'r', encoding='utf-8-sig') as json_file :
        json_list = list(json_file)
        
        
    for json_str in json_list:
        result = json.loads(json_str)
        prompts.append(Prompt(result["Intent"], result["Question"]))


    print(f"Prompt count in the file {file_path} : {len(prompts)}") if printPrompts else False


    return prompts

def getAllFilesPath(folder_path: str) -> list[str]:
    return [file for file in listdir(folder_path) if isfile(join(folder_path, file))]