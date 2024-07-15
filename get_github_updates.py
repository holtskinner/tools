import requests
from datetime import datetime, timedelta, timezone
import yaml
import re
import json


def extract_title_from_markdown(file_content):
    match = re.search(r"^#\s+(.*)$", file_content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    else:
        return "No Title Found"


def extract_title_from_ipynb(file_content):
    notebook_json = json.loads(file_content)
    cells = notebook_json["cells"]
    for cell in cells:
        if cell["cell_type"] == "markdown" and cell["source"]:
            title_match = re.match(r"^#\s+(.*)$", cell["source"][0].strip())
            if title_match:
                return title_match.group(1).strip()
    return "No Title Found"


def get_new_files_in_last_two_weeks(repo_owner, repo_name, access_token=None):
    base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"

    # Calculate the date two weeks ago from today using timezone-aware objects
    two_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=4)
    iso_two_weeks_ago = two_weeks_ago.isoformat()

    params = {
        "since": iso_two_weeks_ago,
    }

    headers = {}
    if access_token:
        headers["Authorization"] = f"token {access_token}"

    response = requests.get(base_url, params=params, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch commits. Status code: {response.status_code}")
        return []

    commits = response.json()
    new_files = set()

    for commit in commits:
        commit_url = commit["url"]
        commit_details = requests.get(commit_url, headers=headers).json()
        files = commit_details["files"]

        for file in files:
            if file["status"] == "added" and (
                file["filename"].endswith(".ipynb")
                or file["filename"].endswith("README.md")
            ):
                file_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main/{file['filename']}"
                file_content_response = requests.get(file_url)
                if file_content_response.status_code == 200:
                    file_content = file_content_response.text
                    if file["filename"].endswith(".ipynb"):
                        title = extract_title_from_ipynb(file_content)
                    elif file["filename"].endswith("README.md"):
                        title = extract_title_from_markdown(file_content)
                    else:
                        title = "No Title Found"
                    new_files.add((file["filename"], title))

    return sorted(list(new_files))  # Sort the list alphabetically


if __name__ == "__main__":
    with open("keys.yaml", "r", encoding="utf-8") as f:
        api_keys = yaml.safe_load(f)

    # Replace these with your GitHub repository details
    repo_owner = "GoogleCloudPlatform"
    repo_name = "generative-ai"
    access_token = api_keys.get("github_token", "")

    for file_info in get_new_files_in_last_two_weeks(
        repo_owner, repo_name, access_token
    ):
        file_name, title = file_info
        file_link = f"https://github.com/{repo_owner}/{repo_name}/tree/main/{file_name}"
        markdown_bullet = f"- [{title}]({file_link})"
        print(markdown_bullet)
