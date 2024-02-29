import requests
from datetime import datetime, timedelta


def get_weekly_activity_github(username, token):
    api_url = f"https://api.github.com/search/issues?q=involves:{username}+is:issue+is:pr+created:{get_start_of_week()}..{get_end_of_week()}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        return response.json()["items"]
    else:
        print(f"GitHub Error: {response.status_code}, {response.text}")
        return None


def get_weekly_activity_stackoverflow(api_key, user_id):
    api_url = f"https://api.stackexchange.com/2.3/users/{user_id}/answers?filter=!6WPIomp1bSN.5"
    params = {
        "site": "stackoverflow",
        "fromdate": get_start_of_week_timestamp(),
        "todate": get_end_of_week_timestamp(),
        "order": "desc",
        "sort": "activity",
        "key": api_key,
    }
    response = requests.get(api_url, params=params)

    if response.status_code == 200:
        return response.json()["items"]
    else:
        print(f"Stack Overflow Error: {response.status_code}, {response.text}")
        return None


def get_start_of_week():
    start_of_week = datetime.today() - timedelta(days=datetime.today().weekday())
    return start_of_week.strftime("%Y-%m-%dT00:00:00Z")


def get_end_of_week():
    end_of_week = datetime.today() + timedelta(days=6 - datetime.today().weekday())
    return end_of_week.strftime("%Y-%m-%dT23:59:59Z")


def get_start_of_week_timestamp():
    start_of_week = datetime.today() - timedelta(days=datetime.today().weekday())
    return int(start_of_week.timestamp())


def get_end_of_week_timestamp():
    end_of_week = datetime.today() + timedelta(days=6 - datetime.today().weekday())
    return int(end_of_week.timestamp())


def format_github_as_markdown(issues):
    markdown_list = []
    for issue in issues:
        markdown_list.append(f"- [{issue['title']}]({issue['html_url']})")

    return markdown_list


def format_stackoverflow_as_markdown(answers):
    markdown_list = []
    for answer in answers:
        question_title = answer["title"]
        answer_link = answer["share_link"]
        markdown_list.append(f"- [{question_title}]({answer_link})")

    return markdown_list


if __name__ == "__main__":
    # GitHub
    github_username = "holtskinner"
    github_token = "YOUR_GITHUB_TOKEN"
    github_issues = get_weekly_activity_github(github_username, github_token)

    if github_issues:
        github_markdown_output = format_github_as_markdown(github_issues)

    # Stack Overflow
    stackoverflow_api_key = ""
    stackoverflow_user_id = "6216983"
    stackoverflow_answers = get_weekly_activity_stackoverflow(
        stackoverflow_api_key, stackoverflow_user_id
    )

    if stackoverflow_answers:
        stackoverflow_markdown_output = format_stackoverflow_as_markdown(
            stackoverflow_answers
        )

    # Print combined results
    if github_issues:
        print("GitHub Activity:")
        print("\n".join(github_markdown_output))

    if stackoverflow_answers:
        print("\nStack Overflow Activity:")
        print("\n".join(stackoverflow_markdown_output))
