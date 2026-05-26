from typing import List
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from find_impact.config import Config
from find_impact.models import ContentItem


class TerminalExporter:
    def __init__(self):
        self.console = Console()

    def export(self, config: Config, items: List[ContentItem]):
        """Renders a beautiful summary dashboard in the terminal."""
        self.console.print()

        # Header banner
        title_text = Text.assemble(
            ("[", "bold white"),
            ("🚀 ", "bold green"),
            ("FindImpact Dashboard", "bold cyan"),
            (" ]", "bold white"),
            ("\n"),
            (
                f"Developer: {config.developer_name} | {config.developer_role} | {config.developer_company}",
                "italic dark_orange",
            ),
        )
        self.console.print(Panel(title_text, border_style="cyan", expand=False))
        self.console.print()

        # Compute summary metrics
        counts = {"github": 0, "youtube": 0, "stackoverflow": 0, "medium": 0, "rss": 0}
        github_commits = 0
        github_prs = 0
        so_accepted = 0
        so_score = 0

        for item in items:
            p = item.platform
            if p in counts:
                counts[p] += 1

            # Additional metric aggregation
            if p == "github":
                t = item.extra_metadata.get("type", "")
                if t == "commit":
                    github_commits += 1
                elif t == "pull_request":
                    github_prs += 1
            elif p == "stackoverflow":
                so_score += item.metrics.get("score", 0)
                if item.metrics.get("is_accepted"):
                    so_accepted += 1

        # Create Metric Cards
        cards = [
            Panel(
                f"[bold purple]{counts['github']}[/bold purple] Items\n[dim]Commits: {github_commits}\nPRs: {github_prs}[/dim]",
                title="[bold white]GitHub[/bold white]",
                border_style="purple",
            ),
            Panel(
                f"[bold red]{counts['youtube']}[/bold red] Videos\n[dim]Tracked Channels: {len(config.youtube_channels)}[/dim]",
                title="[bold white]YouTube[/bold white]",
                border_style="red",
            ),
            Panel(
                f"[bold dark_orange]{counts['stackoverflow']}[/bold dark_orange] Answers\n[dim]Total Score: {so_score}\nAccepted: {so_accepted}[/dim]",
                title="[bold white]Stack Overflow[/bold white]",
                border_style="dark_orange",
            ),
            Panel(
                f"[bold green]{counts['medium']}[/bold green] Articles\n[dim]Pubs Scanned: {len(config.medium_publications)}[/dim]",
                title="[bold white]Medium[/bold white]",
                border_style="green",
            ),
        ]

        # Add RSS card if enabled
        if counts["rss"] > 0 or any(f.get("enabled") for f in config.custom_rss_feeds):
            cards.append(
                Panel(
                    f"[bold blue]{counts['rss']}[/bold blue] Posts\n[dim]Custom Feeds[/dim]",
                    title="[bold white]Custom RSS[/bold white]",
                    border_style="blue",
                )
            )

        self.console.print("[bold yellow]📊 IMPACT METRICS SUMMARY[/bold yellow]")
        self.console.print(Columns(cards))
        self.console.print()

        # Recent items table
        self.console.print("[bold yellow]📅 RECENT DEVREL CONTRIBUTIONS[/bold yellow]")
        table = Table(show_header=True, header_style="bold magenta", expand=True)
        table.add_column("Date", width=12, style="cyan")
        table.add_column("Platform", width=16)
        table.add_column("Contribution Title", style="white")
        table.add_column("Details", style="dim")

        # Sort items by date descending, grab top 15 for console summary
        sorted_items = sorted(items, key=lambda x: x.parsed_date, reverse=True)
        recent_items = sorted_items[:15]

        for item in recent_items:
            # Format Date
            date_str = (
                item.parsed_date.strftime("%Y-%m-%d")
                if item.parsed_date != datetime.min
                else item.publish_date.split("T")[0]
            )

            # Format Platform Badge
            p = item.platform
            if p == "github":
                plat_badge = "[bold purple]GitHub[/bold purple]"
                t = item.extra_metadata.get("type", "commit")
                details = (
                    f"Commit ({item.extra_metadata.get('sha', '')[:7]})"
                    if t == "commit"
                    else t.replace("_", " ").title()
                )
            elif p == "youtube":
                plat_badge = "[bold red]YouTube[/bold red]"
                details = item.extra_metadata.get("channel_title", "Video")
            elif p == "stackoverflow":
                plat_badge = "[bold dark_orange]Stack Overflow[/bold dark_orange]"
                details = f"Score: {item.metrics.get('score', 0)}" + (
                    " (Accepted)" if item.metrics.get("is_accepted") else ""
                )
            elif p == "medium":
                plat_badge = "[bold green]Medium[/bold green]"
                details = "Article"
            else:
                plat_badge = f"[bold blue]{item.extra_metadata.get('feed_name', 'RSS')}[/bold blue]"
                details = "Post"

            table.add_row(date_str, plat_badge, item.title, details)

        self.console.print(table)
        self.console.print(
            f"[dim]Showing latest 15 of {len(items)} tracked items. Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
        )
        self.console.print()
