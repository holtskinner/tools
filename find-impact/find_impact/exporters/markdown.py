from typing import List
from datetime import datetime
from find_impact.config import Config
from find_impact.models import ContentItem


class MarkdownExporter:
    def export(self, config: Config, items: List[ContentItem]):
        """Generates a clean, copy-pasteable Markdown report of developer impact."""
        path = config.markdown_report_path
        print(f"Generating Markdown impact report: {path}...")

        # Compute summary metrics
        counts = {"github": 0, "youtube": 0, "stackoverflow": 0, "medium": 0, "rss": 0}
        github_commits = []
        github_prs = []
        github_issues = []
        youtube_videos = []
        so_answers = []
        medium_articles = []
        rss_posts = []

        # Sort items chronologically (newest first)
        sorted_items = sorted(items, key=lambda x: x.parsed_date, reverse=True)

        for item in sorted_items:
            p = item.platform
            counts[p] = counts.get(p, 0) + 1

            if p == "github":
                t = item.extra_metadata.get("type", "")
                if t == "commit":
                    github_commits.append(item)
                elif t == "pull_request":
                    github_prs.append(item)
                elif t == "issue":
                    github_issues.append(item)
                else:
                    github_commits.append(item)
            elif p == "youtube":
                youtube_videos.append(item)
            elif p == "stackoverflow":
                so_answers.append(item)
            elif p == "medium":
                medium_articles.append(item)
            elif p == "rss":
                rss_posts.append(item)

        total_contributions = len(items)

        # Assemble Markdown
        lines = []
        lines.append(f"# Developer Impact Report: {config.developer_name}")
        lines.append(f"**Role:** {config.developer_role} | **Company:** {config.developer_company}")
        lines.append(f"**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        lines.append("## Executive Summary")
        lines.append(
            "Below is an aggregated summary of public developer relations and engineering contributions."
        )
        lines.append("")

        # Summary Table
        lines.append("| Platform | Total Items | Specific Contributions / Metrics |")
        lines.append("| :--- | :---: | :--- |")
        lines.append(
            f"| **GitHub** | {counts['github']} | {len(github_commits)} commits, {len(github_prs)} pull requests, {len(github_issues)} issues |"
        )
        lines.append(
            f"| **YouTube** | {counts['youtube']} | Videos featured on Google Cloud channel |"
        )
        lines.append(
            f"| **Stack Overflow** | {counts['stackoverflow']} | Developer technical assistance answers |"
        )
        lines.append(
            f"| **Medium** | {counts['medium']} | Technical articles in Medium Publications |"
        )
        if counts["rss"] > 0:
            lines.append(
                f"| **Custom Blogs/RSS** | {counts['rss']} | Custom RSS feed contributions |"
            )
        lines.append(
            f"| **TOTALS** | **{total_contributions}** | **Active Tracking Across {sum(1 for c in counts.values() if c > 0)} Platforms** |"
        )
        lines.append("")

        # Section: YouTube
        if youtube_videos:
            lines.append("## YouTube Contributions")
            lines.append(
                f"List of {len(youtube_videos)} recorded/presented videos featured on monitored channels:"
            )
            lines.append("")
            for v in youtube_videos:
                date_str = v.parsed_date.strftime("%Y-%m-%d")
                title_clean = v.title.replace("[YouTube] ", "")
                channel = v.extra_metadata.get("channel_title", "YouTube")
                lines.append(f"- **{date_str}**: [{title_clean}]({v.url}) *(Channel: {channel})*")
            lines.append("")

        # Section: Medium
        if medium_articles:
            lines.append("## Written Publications & Medium Articles")
            lines.append(
                f"List of {len(medium_articles)} technical articles published on Medium publications:"
            )
            lines.append("")
            for art in medium_articles:
                date_str = art.parsed_date.strftime("%Y-%m-%d")
                title_clean = art.title.replace("[Medium] ", "")
                lines.append(f"- **{date_str}**: [{title_clean}]({art.url})")
            lines.append("")

        # Section: Stack Overflow
        if so_answers:
            lines.append("## Stack Overflow Technical Assistance")
            lines.append(
                f"List of {len(so_answers)} public answers helping developers on Stack Overflow:"
            )
            lines.append("")
            for ans in so_answers:
                date_str = ans.parsed_date.strftime("%Y-%m-%d")
                title_clean = ans.title.replace("[Stack Overflow] ", "")
                score = ans.metrics.get("score", 0)
                accepted = " *(Accepted)*" if ans.metrics.get("is_accepted") else ""
                lines.append(
                    f"- **{date_str}**: [{title_clean}]({ans.url}) - Score: {score}{accepted}"
                )
            lines.append("")

        # Section: GitHub
        if counts["github"] > 0:
            lines.append("## GitHub Engineering & Open Source Contributions")
            lines.append(f"Summary of {counts['github']} public commits, PRs, and issues tracked:")
            lines.append("")

            if github_prs:
                lines.append("### Pull Requests")
                for pr in github_prs:
                    date_str = pr.parsed_date.strftime("%Y-%m-%d")
                    # clean title
                    t = pr.title
                    for prefix in ["[GitHub] ", "github "]:
                        if t.lower().startswith(prefix.lower()):
                            t = t[len(prefix) :]
                    lines.append(f"- **{date_str}**: [{t}]({pr.url})")
                lines.append("")

            if github_commits:
                lines.append("### Commits")
                # Show top 30 commits to avoid overflowing
                shown_commits = github_commits[:30]
                for c in shown_commits:
                    date_str = c.parsed_date.strftime("%Y-%m-%d")
                    t = c.title
                    lines.append(f"- **{date_str}**: [{t}]({c.url})")
                if len(github_commits) > 30:
                    lines.append(f"- *...and {len(github_commits) - 30} more commits.*")
                lines.append("")

        # Section: Custom RSS
        if rss_posts:
            lines.append("## Custom Blogs & Other Feeds")
            for post in rss_posts:
                date_str = post.parsed_date.strftime("%Y-%m-%d")
                # Strip platform title
                t = post.title
                feed_name = post.extra_metadata.get("feed_name", "RSS")
                if t.startswith(f"[{feed_name}] "):
                    t = t[len(f"[{feed_name}] ") :]
                lines.append(f"- **{date_str}**: [{t}]({post.url}) *(Source: {feed_name})*")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("*Report compiled automatically by **FindImpact** content tracker.*")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print("Markdown impact report generated successfully.")
