import argparse
from typing import List

from find_impact.config import Config
from find_impact.cache import CacheManager
from find_impact.models import ContentItem

# Fetchers
from find_impact.fetchers.github import GitHubFetcher
from find_impact.fetchers.stackoverflow import StackOverflowFetcher
from find_impact.fetchers.medium import MediumFetcher
from find_impact.fetchers.youtube import YouTubeFetcher
from find_impact.fetchers.rss import CustomRSSFetcher

# Exporters
from find_impact.exporters.terminal import TerminalExporter
from find_impact.exporters.html import HTMLExporter
from find_impact.exporters.markdown import MarkdownExporter


def main():
    parser = argparse.ArgumentParser(
        description="FindImpact - Keep track of external-facing DevRel content and contributions."
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config.yaml",
        help="Path to configuration YAML file (default: config.yaml)",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Bypass cache and force-fetch fresh entries from all APIs",
    )
    parser.add_argument(
        "--no-html", action="store_true", help="Skip generating the interactive HTML dashboard"
    )
    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="Skip generating the Markdown copy-paste impact report",
    )

    args = parser.parse_args()

    print("========================================")
    print("      🔍 Starting FindImpact Core       ")
    print("========================================")

    # 1. Load config
    config = Config(args.config)
    print(f"Tracking content for: {config.developer_name} ({config.developer_role})")

    # 2. Setup caching
    cache_mgr = CacheManager(config.cache_path)
    if args.force:
        print("Force flag set. Bypassing existing cache and initiating direct sync...")
        cached_items = []
    else:
        cached_items = cache_mgr.load()
        print(f"Loaded {len(cached_items)} items from local cache: '{config.cache_path}'")

    # 3. Instantiate fetchers
    fetchers = [
        GitHubFetcher(),
        StackOverflowFetcher(),
        MediumFetcher(),
        YouTubeFetcher(),
        CustomRSSFetcher(),
    ]

    newly_fetched: List[ContentItem] = []

    # 4. Fetch content across platforms with error isolation
    for fetcher in fetchers:
        print("----------------------------------------")
        print(f"Syncing platform: {fetcher.name}...")
        try:
            items = fetcher.fetch(config)
            print(f"Success: Fetched {len(items)} items from {fetcher.name}")
            newly_fetched.extend(items)
        except Exception as e:
            print(f"Error: Sync failed for fetcher '{fetcher.name}': {e}")
            print("Skipping to preserve flow...")

    print("----------------------------------------")
    print(f"Sync complete. Fetched {len(newly_fetched)} new/updated items.")

    # 5. Merge and cache
    merged_items = cache_mgr.merge_and_save(newly_fetched)
    print(f"Total tracking database size: {len(merged_items)} items.")

    # 6. Exporters
    # A. Terminal
    terminal = TerminalExporter()
    terminal.export(config, merged_items)

    # B. HTML
    if not args.no_html:
        html_exp = HTMLExporter()
        html_exp.export(config, merged_items)

    # C. Markdown
    if not args.no_markdown:
        md_exp = MarkdownExporter()
        md_exp.export(config, merged_items)

    print("========================================")
    print("🎉 FindImpact run completed successfully!")
    print("========================================")


if __name__ == "__main__":
    main()
