def sort_and_deduplicate(file_path):
    """Sorts lines in a file alphabetically (case-sensitive) and removes duplicates."""

    spelling_allow_file = file_path

    with open(spelling_allow_file, "r", encoding="utf-8") as file:
        unique_words = sorted(set(file))

    with open(spelling_allow_file, "w", encoding="utf-8") as file:
        file.writelines(unique_words)


# --- Main Execution ---
if __name__ == "__main__":
    filename = (
        "/Users/holtskinner/GitHub/generative-ai/.github/actions/spelling/allow.txt"
    )
    sort_and_deduplicate(filename)
    print(f"File '{filename}' has been sorted and deduplicated.")
