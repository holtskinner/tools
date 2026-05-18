# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import urllib.parse

import nbformat

# Constants
GITHUB_URL_PREFIX = "https://github.com/GoogleCloudPlatform/generative-ai/blob/main/"
RAW_URL_PREFIX = (
    "https://raw.githubusercontent.com/GoogleCloudPlatform/generative-ai/main/"
)


def fix_links(content, rel_path):
    """Replaces placeholders in the template with notebook-specific links."""
    github_url = f"{GITHUB_URL_PREFIX}{rel_path}"
    raw_url = f"{RAW_URL_PREFIX}{rel_path}"

    # Encoded versions for specific use cases
    # Colab Enterprise needs / encoded but : preserved
    encoded_raw_url = urllib.parse.quote(raw_url, safe=":")

    # Social links need : encoded but / preserved
    encoded_github_url = urllib.parse.quote(github_url, safe="/")

    # Order matters for replacement to avoid partial matches
    content = content.replace(
        "https:%2F%2Fraw.githubusercontent.com%2FGoogleCloudPlatform%2Fgenerative-ai%2Fmain%2Fnotebook_template.ipynb",
        encoded_raw_url,
    )
    content = content.replace(
        "https://raw.githubusercontent.com/GoogleCloudPlatform/generative-ai/main/notebook_template.ipynb",
        raw_url,
    )
    content = content.replace(
        "https%3A//github.com/GoogleCloudPlatform/generative-ai/blob/main/notebook_template.ipynb",
        encoded_github_url,
    )
    content = content.replace(
        "https://github.com/GoogleCloudPlatform/generative-ai/blob/main/notebook_template.ipynb",
        github_url,
    )

    # Fallback for any other occurrences
    content = content.replace("notebook_template.ipynb", rel_path)

    return content


def update_notebooks(base_path="."):
    # Read the new table template
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "new-table.html")
    if not os.path.exists(template_path):
        print(f"Error: {template_path} not found.")
        return

    with open(template_path, encoding="utf-8") as f:
        new_table_template = f.read().strip()

    updated_count = 0
    error_count = 0

    for root, dirs, files in os.walk(base_path):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for file in files:
            if file.endswith(".ipynb"):
                file_path = os.path.join(root, file)
                # Use forward slashes for URLs regardless of OS
                rel_path = os.path.relpath(file_path, ".").replace("\\", "/")

                try:
                    with open(file_path, encoding="utf-8") as f:
                        nb = nbformat.read(f, as_version=4)

                    modified = False
                    for cell in nb.cells:
                        if cell.cell_type == "markdown" and "<table" in cell.source:
                            source = cell.source
                            # Find the start of the table
                            table_idx = source.find("<table")

                            # Check if "vertex-ai" is in the table portion of the cell
                            if "vertex-ai" in source[table_idx:].lower():
                                # Prepare the new content for this specific notebook
                                new_content = fix_links(new_table_template, rel_path)

                                # Replace from <table to the end of the cell
                                # Note: We assume the table/sharing links are at the end of the cell
                                cell.source = source[:table_idx] + new_content
                                modified = True

                            # Only check the first markdown cell containing a table
                            break

                    if modified:
                        with open(file_path, "w", encoding="utf-8") as f:
                            nbformat.write(nb, f)
                        updated_count += 1
                        print(f"Updated: {rel_path}")

                except Exception as e:
                    print(f"Error processing {rel_path}: {e}")
                    error_count += 1

    print("\nSummary:")
    print(f"Total notebooks updated: {updated_count}")
    print(f"Errors encountered: {error_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update notebook tables.")
    parser.add_argument(
        "path", nargs="?", default=".", help="Path to search for notebooks (default: .)"
    )
    args = parser.parse_args()
    update_notebooks(args.path)
