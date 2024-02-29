import os
import subprocess


def get_initial_commit_hash(file_path, repo_path):
    # Use git command to get the hash of the first commit for a file, considering moved or renamed files
    cmd = ["git", "log", "--pretty=format:%H", "--", file_path]
    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)

    # Check if the command was successful
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip().splitlines()[
            -1
        ]  # Get the last commit hash in the list
    else:
        return None


def get_initial_author(commit_hash, repo_path):
    # Use git command to get the author of a specific commit
    cmd = ["git", "show", "--format=%an|%ae", "--no-patch", commit_hash]
    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)

    # Check if the command was successful
    if result.returncode == 0:
        return result.stdout.strip().split("|")
    else:
        return None


def get_github_url(repo_url, commit_hash):
    # Generate GitHub URL for a specific commit hash
    return f"{repo_url}/commit/{commit_hash}"


def contains_author_word(file_path):
    # Check if the file content contains the word "Author"
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        return "Author" in content


def format_author_output(author_info):
    # Format the author information as requested
    return f"|Author(s)| [{author_info[0]}](mailto:{author_info[1]}) |"


def extract_initial_authors(repo_path, repo_url, file_extension=".ipynb"):
    # List files with the specified extension in the repository, excluding those containing the word "Author"
    cmd = ["git", "ls-files", "--", f"*{file_extension}"]
    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)

    # Check if the command was successful
    if result.returncode == 0:
        files = result.stdout.strip().split("\n")

        # Dictionary to store initial authors and commit URLs for each file
        initial_data = {}

        for file in files:
            file_path = os.path.join(repo_path, file)

            # Exclude files containing the word "Author" in their content
            if not contains_author_word(file_path):
                initial_commit_hash = get_initial_commit_hash(file_path, repo_path)

                if initial_commit_hash:
                    author_info = get_initial_author(initial_commit_hash, repo_path)

                    if author_info:
                        commit_url = get_github_url(repo_url, initial_commit_hash)

                        # Store the result in the dictionary
                        initial_data[file] = {
                            "author_info": author_info,
                            "commit_url": commit_url,
                        }

        return initial_data
    else:
        return None


if __name__ == "__main__":
    # Set the path to your locally cloned GitHub repository
    repo_path = "/Users/holtskinner/GitHub/generative-ai/"

    # Set the GitHub repository URL
    repo_url = "https://github.com/GoogleCloudPlatform/generative-ai"  # Replace with your repository URL

    # Extract initial authors and commit URLs for Jupyter notebook files (excluding those containing "Author" in content)
    data = extract_initial_authors(repo_path, repo_url)

    if data is not None:
        # Print the results
        for file, info in data.items():
            author_output = format_author_output(info["author_info"])
            print(
                f"| File: {file} |\n{author_output}\n| Commit URL | {info['commit_url']} |\n"
            )
    else:
        print("Error retrieving Jupyter notebook files.")
