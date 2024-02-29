import os
import re


def find_authors(notebook_path):
    with open(notebook_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Assuming authors are listed in a markdown cell with the specified format
    match = re.search(
        r"\|Author\(s\) \| \[([\w\s]+)\]\(https:\/\/github\.com\/([\w-]+)\) \|", content
    )

    if match:
        return match.group(1), match.group(2)
    else:
        return None, None


def create_codeowners(codeowners_path, directory, author):
    codeowners_content = f"{directory} @{author}\n"

    with open(codeowners_path, "a", encoding="utf-8") as file:
        file.write(codeowners_content)


def process_directory(directory, codeowners_path):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".ipynb"):
                notebook_path = os.path.join(root, file)
                author_name, author_github = find_authors(notebook_path)

                if author_name and author_github:
                    create_codeowners(codeowners_path, root, author_github)
                    print(f"CODEOWNERS entry created for {author_name} in {root}")


if __name__ == "__main__":
    # Replace 'your_directory_path' with the path to your directory containing Jupyter Notebooks
    directory_path = "/Users/holtskinner/GitHub/generative-ai/"

    # Replace 'your_codeowners_path' with the desired path for the CODEOWNERS file
    codeowners_path = "/Users/holtskinner/GitHub/generative-ai/.github/CODEOWNERS"

    # Initialize or clear the existing CODEOWNERS file
    with open(codeowners_path, "w", encoding="utf-8"):
        pass

    process_directory(directory_path, codeowners_path)
