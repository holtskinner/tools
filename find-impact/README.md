# FindImpact

**FindImpact** is a modern, light-weight, and extensible Python-based content and reach tracker designed for Developer Relations Engineers. It helps you keep track of your external-facing contributions published across multiple internet platforms, gather impact metrics, and compile them into stunning reports.

## Features

- **Multi-Platform Sync**: Consolidates contributions from:
  - **YouTube**: Tracks videos featuring you or uploaded on specified channels (supporting both YouTube Data API and Zero-Auth Channel RSS fallbacks).
  - **GitHub**: Collects global commit history, pull requests, and issue activities.
  - **Stack Overflow**: Retrieves developer technical answers and reputation metrics.
  - **Medium**: Scans Medium publication feeds (e.g. Google Cloud Community) or direct user feeds for technical articles, filtering by author.
  - **Custom RSS Feeds**: Parses any generic feed (e.g., personal blogs, Dev.to articles, podcasts).
- **Persistent Local Caching**: Automatically saves retrieved items to prevent API rate-limiting, and retains historical logs that may fall off active feed pages (such as GitHub events).
- **Stunning Multi-Format Reports**:
  - **Rich Console UI**: Prints beautiful, color-coded terminal dashboards summarizing reach.
  - **Interactive HTML Dashboard**: Generates a gorgeous, responsive, client-side glassmorphic dashboard complete with Chart.js charts, real-time search, filters, and embedded video previews.
  - **Copy-Paste Markdown**: Compiles clean Markdown reports formatted specifically for quarterly/yearly performance reviews.

---

## Installation & Setup

We recommend using [uv](https://github.com/astral-sh/uv) for package and environment management.

To set up the project and install all dependencies:
```bash
uv run python -m find_impact.main --help
```
This will automatically create a virtual environment and install dependencies (`requests`, `feedparser`, `rich`, `pyyaml`, `jinja2`).

---

## Configuration

FindImpact is configured via a single YAML file named `config.yaml` located in the root of the project.

Modify `config.yaml` to specify your own profile handles:
```yaml
developer:
  name: "Holt Skinner"
  role: "Staff Developer Relations Engineer"
  company: "Google Cloud AI"

sources:
  github:
    username: "holtskinner"
    orgs: ["GoogleCloudPlatform", "google-gemini"] # Filter commits/events by org

  stackoverflow:
    user_id: 123456 # Replace with your Stack Overflow user ID

  medium:
    username: "holtskinner"
    publications: ["google-cloud"] # Scans and filters https://medium.com/feed/google-cloud

  youtube:
    channels:
      - name: "Google Cloud Tech"
        id: "UCzM5Vv1xN5I5S1b35_Gv6hA"
    search_queries: ["Holt Skinner"]

  custom_rss:
    - name: "Personal Blog"
      url: "https://yourblog.com/feed"
      enabled: false
```

### Environment Variables

The tool runs out-of-the-box with **zero authentication** using public endpoints. However, to bypass public limits or query full historical lists, you can set the following:

- `GITHUB_TOKEN`: A GitHub Personal Access Token (PAT) used to fetch commit search results without rate limits.
- `YOUTUBE_API_KEY`: A YouTube Data API v3 key used to perform deep search queries across channel uploads. (If not provided, the tool automatically falls back to parsing public channel RSS streams for recent uploads).

---

## Usage

Run the tool using `uv`:
```bash
uv run python -m find_impact.main
```

### Command Line Arguments

- `-c, --config`: Specify a custom config YAML file path (default: `config.yaml`).
- `-f, --force`: Bypass local cache and force-fetch fresh entries directly from all APIs.
- `--no-html`: Skip generating the interactive HTML dashboard.
- `--no-markdown`: Skip generating the Markdown copy-paste impact report.

*Example:*
```bash
# Force fetch and use a custom configuration
uv run python -m find_impact.main -f --config my_custom_config.yaml
```

---

## Output Formats

- **Terminal Console**: Displays immediate KPIs and latest 15 contributions.
- **HTML Dashboard**: Saved to `dashboard.html` by default. Double-click the file to open it in any web browser.
- **Markdown Report**: Saved to `impact_report.md` by default. Ready to be copied directly into performance documents.
