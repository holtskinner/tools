import os
import re


def process_notebook_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Use regular expression to find and replace the specified pattern
    new_content = re.sub(
        r'<img src="(.+?)" alt="(.+?)">',
        r'<img width="32px" src="\1" alt="\2">',
        content,
    )

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(new_content)


def process_notebooks_in_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".ipynb"):
                file_path = os.path.join(root, file)
                process_notebook_file(file_path)
                print(f"Processed: {file_path}")


if __name__ == "__main__":
    target_directory = "/Users/holtskinner/GitHub/generative-ai/"  # Replace with the actual directory path

    process_notebooks_in_directory(target_directory)
