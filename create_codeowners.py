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


def process_directory(directory, codeowners_path, parent_folder):

    with open(codeowners_path, "r", encoding="utf-8") as file:
        codeowners_content = file.read()

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".ipynb"):
                notebook_path = os.path.join(root, file)
                author_name, author_github = find_authors(notebook_path)

                if author_name and author_github:
                    if author_github not in codeowners_content:
                        new_path = f"/{root}/{file}".replace(parent_folder, "")
                        print(
                            f"{new_path}\t@{author_github} @GoogleCloudPlatform/generative-ai-devrel"
                        )

                    # print(f"CODEOWNERS entry created for {author_name} in {root}")


if __name__ == "__main__":
    # Replace 'your_directory_path' with the path to your directory containing Jupyter Notebooks
    parent_folder = "/Users/holtskinner/GitHub/"
    directory_path = "/Users/holtskinner/GitHub/generative-ai/"

    # Replace 'your_codeowners_path' with the desired path for the CODEOWNERS file
    codeowners_path = "/Users/holtskinner/GitHub/generative-ai/.github/CODEOWNERS"

    process_directory(directory_path, codeowners_path, parent_folder)
