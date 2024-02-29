import requests
from datetime import datetime, timedelta
import yaml
from typing import Tuple


def get_weekly_activity_github(username, token, start_of_week, end_of_week):
    api_url = f"https://api.github.com/search/issues?q=involves:{username}+is:issue+is:pr+created:{start_of_week}..{end_of_week}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        print(f"GitHub Error: {response.status_code}, {response.text}")
        return None

    return response.json()["items"]


def get_weekly_activity_stackoverflow(api_key, user_id, start_of_week, end_of_week):
    api_url = f"https://api.stackexchange.com/2.3/users/{user_id}/answers?filter=!6WPIomp1bSN.5"
    params = {
        "site": "stackoverflow",
        "fromdate": start_of_week,
        "todate": end_of_week,
        "order": "desc",
        "sort": "activity",
        "key": api_key,
    }
    response = requests.get(api_url, params=params)

    if response.status_code != 200:
        print(f"Stack Overflow Error: {response.status_code}, {response.text}")
        return None

    return response.json()["items"]


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
        target_list = (
            contributed_issues
            if issue["user"]["login"] == username
            else reviewed_issues
        )
        target_list.append(f"- [{issue['title']}]({issue['html_url']})")

    return reviewed_issues, contributed_issues


def format_stackoverflow_as_markdown(answers):
    return [f"- [{answer['title']}]({answer['share_link']})" for answer in answers]


if __name__ == "__main__":
    with open("keys.yaml", "r", encoding="utf-8") as file:
        api_keys = yaml.safe_load(file)

    (start_of_week, start_of_week_ts), (end_of_week, end_of_week_ts) = (
        get_start_end_of_week()
    )

    # GitHub
    github_username = "holtskinner"
    github_token = api_keys.get("github_token", "")
    github_issues = get_weekly_activity_github(
        github_username, github_token, start_of_week, end_of_week
    )

    if github_issues:
        reviewed_issues, contributed_issues = format_github_as_markdown(
            github_issues, github_username
        )

        print("GitHub Activity:")

        if contributed_issues:
            print("\nContributed:")
            print("\n".join(contributed_issues))

        if reviewed_issues:
            print("\nReviewed:")
            print("\n".join(reviewed_issues))

    # Stack Overflow
    stackoverflow_api_key = api_keys.get("stackoverflow_api_key", "")
    stackoverflow_user_id = "6216983"
    stackoverflow_answers = get_weekly_activity_stackoverflow(
        stackoverflow_api_key, stackoverflow_user_id, start_of_week_ts, end_of_week_ts
    )

    if stackoverflow_answers:
        print("\nStack Overflow Activity:")
        print("\n".join(format_stackoverflow_as_markdown(stackoverflow_answers)))
