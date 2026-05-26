import os
import requests
from typing import List, Dict, Any, Optional
from find_impact.config import Config
from find_impact.models import ContentItem
from find_impact.fetchers.base import BaseFetcher


class GitHubFetcher(BaseFetcher):
    @property
    def name(self) -> str:
        return "GitHub"

    def fetch(self, config: Config) -> List[ContentItem]:
        username = config.github_username
        if not username:
            print("GitHub username not configured. Skipping.")
            return []

        token = os.environ.get("GITHUB_TOKEN")
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if token:
            headers["Authorization"] = f"token {token}"
            # Ensure the cloak preview header is included for commit search if needed
            headers_search = headers.copy()
            headers_search["Accept"] = "application/vnd.github.cloak-preview"
        else:
            headers_search = {"Accept": "application/vnd.github.cloak-preview"}

        items: List[ContentItem] = []

        # 1. Fetch via User Events API (fast and doesn't hit Search API rate limits)
        print(f"Fetching GitHub events for user: {username}...")
        events_url = f"https://api.github.com/users/{username}/events/public"
        try:
            # Fetch first 3 pages of events (up to 90 events)
            for page in range(1, 4):
                params = {"page": page, "per_page": 30}
                res = requests.get(events_url, headers=headers, params=params)
                if res.status_code == 200:
                    events = res.json()
                    if not events:
                        break
                    for event in events:
                        parsed_items = self._parse_event(event)
                        items.extend(parsed_items)
                elif res.status_code == 403:
                    print("GitHub API Rate limit exceeded for Events. Try setting GITHUB_TOKEN.")
                    break
                else:
                    print(f"Warning: Failed to fetch GitHub events page {page}: {res.status_code}")
                    break
        except Exception as e:
            print(f"Error fetching GitHub events: {e}")

        # 2. Fetch via Global Commit Search API (deeper search, queries commit messages across repositories)
        print(f"Searching GitHub commits for author: {username}...")
        search_url = "https://api.github.com/search/commits"
        query = f"author:{username}"
        # Filter by orgs if specified
        if config.github_orgs:
            query += " " + " ".join([f"org:{org}" for org in config.github_orgs])

        params = {"q": query, "sort": "author-date", "order": "desc", "per_page": 50}
        try:
            res = requests.get(search_url, headers=headers_search, params=params)
            if res.status_code == 200:
                search_data = res.json()
                for item in search_data.get("items", []):
                    commit_item = self._parse_search_commit(item)
                    if commit_item:
                        items.append(commit_item)
            elif res.status_code == 403:
                print(
                    "GitHub Commit Search API rate limit or access denied. (Search requires a valid token or has lower rate limit). Skipping search."
                )
            else:
                print(f"Warning: GitHub search API returned status {res.status_code}: {res.text}")
        except Exception as e:
            print(f"Error searching GitHub commits: {e}")

        # Remove duplicate items by id (using dict keys)
        unique_items: Dict[str, ContentItem] = {}
        for item in items:
            unique_items[item.id] = item

        return list(unique_items.values())

    def _parse_event(self, event: Dict[str, Any]) -> List[ContentItem]:
        """Parses a single GitHub event into one or more ContentItems."""
        event_type = event.get("type")
        repo_name = event.get("repo", {}).get("name", "")
        created_at = event.get("created_at", "")

        items: List[ContentItem] = []

        if event_type == "PushEvent":
            # Pushed commits
            payload = event.get("payload", {})
            commits = payload.get("commits", [])
            for commit in commits:
                sha = commit.get("sha", "")
                message = commit.get("message", "")
                # Only include commits that look like they were authored by the user
                # (Simple check: event actor username matches config, which we assume is True)
                first_line = message.split("\n")[0] if message else "Pushed commit"
                commit_url = f"https://github.com/{repo_name}/commit/{sha}"

                items.append(
                    ContentItem(
                        id=f"github-commit-{sha}",
                        title=f"[{repo_name}] {first_line}",
                        url=commit_url,
                        platform="github",
                        publish_date=created_at,
                        summary=message,
                        extra_metadata={"repo": repo_name, "type": "commit", "sha": sha},
                    )
                )

        elif event_type == "PullRequestEvent":
            payload = event.get("payload", {})
            action = payload.get("action", "")
            pr = payload.get("pull_request", {})

            # Track PRs opened or merged by user
            if action in ["opened", "closed"] and pr:
                is_merged = pr.get("merged", False)

                title_prefix = "Merged Pull Request" if is_merged else "Opened Pull Request"
                pr_title = pr.get("title", "")
                pr_url = pr.get("html_url", "")
                pr_number = pr.get("number")

                # Check if it was indeed our user
                items.append(
                    ContentItem(
                        id=f"github-pr-{pr_url}",
                        title=f"[{repo_name}] {title_prefix} #{pr_number}: {pr_title}",
                        url=pr_url,
                        platform="github",
                        publish_date=created_at,
                        summary=pr.get("body", "") or f"Pull request in {repo_name}",
                        metrics={
                            "comments": pr.get("comments", 0),
                            "commits": pr.get("commits", 0),
                            "additions": pr.get("additions", 0),
                            "deletions": pr.get("deletions", 0),
                        },
                        extra_metadata={
                            "repo": repo_name,
                            "type": "pull_request",
                            "pr_number": pr_number,
                            "action": action,
                            "merged": is_merged,
                        },
                    )
                )

        elif event_type == "IssuesEvent":
            payload = event.get("payload", {})
            action = payload.get("action", "")
            issue = payload.get("issue", {})

            if action == "opened" and issue:
                issue_title = issue.get("title", "")
                issue_url = issue.get("html_url", "")
                issue_number = issue.get("number")

                items.append(
                    ContentItem(
                        id=f"github-issue-{issue_url}",
                        title=f"[{repo_name}] Opened Issue #{issue_number}: {issue_title}",
                        url=issue_url,
                        platform="github",
                        publish_date=created_at,
                        summary=issue.get("body", "") or f"Issue in {repo_name}",
                        metrics={"comments": issue.get("comments", 0)},
                        extra_metadata={
                            "repo": repo_name,
                            "type": "issue",
                            "issue_number": issue_number,
                        },
                    )
                )

        return items

    def _parse_search_commit(self, search_item: Dict[str, Any]) -> Optional[ContentItem]:
        """Parses an item from the Commit Search API response into a ContentItem."""
        try:
            sha = search_item.get("sha", "")
            repo = search_item.get("repository", {})
            repo_name = repo.get("full_name", "")

            commit = search_item.get("commit", {})
            message = commit.get("message", "")
            first_line = message.split("\n")[0] if message else "Commit"

            author = commit.get("author", {})
            date_str = author.get("date", "")
            commit_url = (
                search_item.get("html_url", "") or f"https://github.com/{repo_name}/commit/{sha}"
            )

            return ContentItem(
                id=f"github-commit-{sha}",
                title=f"[{repo_name}] {first_line}",
                url=commit_url,
                platform="github",
                publish_date=date_str,
                summary=message,
                extra_metadata={"repo": repo_name, "type": "commit", "sha": sha},
            )
        except Exception as e:
            print(f"Warning: Failed to parse search commit item: {e}")
            return None
