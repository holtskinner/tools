import requests
from datetime import datetime, timedelta, timezone
import yaml


def get_new_files_in_last_two_weeks(repo_owner, repo_name, access_token=None):
    base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"

    # Calculate the date two weeks ago from today using timezone-aware objects
    two_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=2)
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
                new_files.add(file["filename"])

    return sorted(list(new_files))  # Sort the list alphabetically


if __name__ == "__main__":
    with open("keys.yaml", "r", encoding="utf-8") as f:
        api_keys = yaml.safe_load(f)

    # Replace these with your GitHub repository details
    repo_owner = "GoogleCloudPlatform"
    repo_name = "generative-ai"
    access_token = api_keys.get("github_token", "")

    print("New files added in the last two weeks (sorted alphabetically):")
    for f in get_new_files_in_last_two_weeks(repo_owner, repo_name, access_token):
        print(f"https://github.com/GoogleCloudPlatform/generative-ai/tree/main/{f}")
