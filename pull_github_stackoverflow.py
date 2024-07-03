import requests
from datetime import datetime, timedelta
import yaml
from typing import Tuple


def get_activity_github(username, token, start_date, end_date):
    api_url = f"https://api.github.com/search/issues?q=involves:{username}+is:issue+is:pr+created:{start_date}..{end_date}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        print(f"GitHub Error: {response.status_code}, {response.text}")
        return None

    return response.json()["items"]


def get_activity_stackoverflow(api_key, user_id, start_date, end_date):
    # Fetch answers
    api_url_answers = f"https://api.stackexchange.com/2.3/users/{user_id}/answers?filter=!6WPIomp1bSN.5"
    params_answers = {
        "site": "stackoverflow",
        "fromdate": start_date,
        "todate": end_date,
        "order": "desc",
        "sort": "activity",
        "key": api_key,
    }
    response_answers = requests.get(api_url_answers, params=params_answers)

    if response_answers.status_code != 200:
        print(
            f"Stack Overflow Answers Error: {response_answers.status_code}, {response_answers.text}"
        )
        return None

    answers = response_answers.json()["items"]

    # Fetch comments
    api_url_comments = f"https://api.stackexchange.com/2.3/users/{user_id}/comments"
    params_comments = {
        "site": "stackoverflow",
        "fromdate": start_date,
        "todate": end_date,
        "order": "desc",
        "sort": "creation",
        "key": api_key,
    }
    response_comments = requests.get(api_url_comments, params=params_comments)

    if response_comments.status_code != 200:
        print(
            f"Stack Overflow Comments Error: {response_comments.status_code}, {response_comments.text}"
        )
        return answers, None

    comments = response_comments.json()["items"]

    return answers, comments


def get_start_end_of_week() -> Tuple[Tuple[str, int], Tuple[str, int]]:
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = today + timedelta(days=6 - today.weekday())

    return (
        (start_of_week.strftime("%Y-%m-%dT00:00:00Z"), int(start_of_week.timestamp())),
        (end_of_week.strftime("%Y-%m-%dT23:59:59Z"), int(end_of_week.timestamp())),
    )


def format_github_as_markdown(issues, username):
    reviewed_issues = []
    contributed_issues = []

    for issue in issues:
        if "(deps):" in issue["title"] or "(deps-dev)" in issue["title"]:
            continue
        target_list = (
            contributed_issues
            if issue["user"]["login"] == username
            else reviewed_issues
        )
        target_list.append(f"- [{issue['title']}]({issue['html_url']})")

    return reviewed_issues, contributed_issues


if __name__ == "__main__":
    with open("keys.yaml", "r", encoding="utf-8") as file:
        api_keys = yaml.safe_load(file)

    (start_date, start_date_ts), (end_date, end_date_ts) = get_start_end_of_week()

    # GitHub
    github_username = "holtskinner"
    github_token = api_keys.get("github_token", "")
    github_issues = get_activity_github(
        github_username, github_token, start_date, end_date
    )

    if github_issues:
        reviewed_issues, contributed_issues = format_github_as_markdown(
            github_issues, github_username
        )

        print("## GitHub\n")

        if contributed_issues:
            print("### Contributed\n")
            print("\n".join(contributed_issues))

        if reviewed_issues:
            print("\n### Reviewed\n")
            print("\n".join(reviewed_issues))

    # Stack Overflow
    stackoverflow_api_key = api_keys.get("stackoverflow_api_key", "")
    stackoverflow_user_id = "6216983"
    stackoverflow_answers, stackoverflow_comments = get_activity_stackoverflow(
        stackoverflow_api_key, stackoverflow_user_id, start_date_ts, end_date_ts
    )

    if stackoverflow_answers:
        print("\n## 🥞 Stack Overflow\n")
        print(
            "\n".join(
                [
                    f"- [{answer['title']}]({answer['share_link']})"
                    for answer in stackoverflow_answers
                ]
            )
        )

    if stackoverflow_comments:
        print(
            "\n".join(
                [
                    f"- https://stackoverflow.com/questions/{comment['post_id']}"
                    for comment in stackoverflow_comments
                ]
            )
        )
