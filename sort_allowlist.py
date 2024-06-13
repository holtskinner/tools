def sort_and_deduplicate(file_path):
    """Sorts lines in a file alphabetically (case-sensitive) and removes duplicates."""

    with open(file_path, "r", encoding="utf-8") as file:
        words = file.readlines()  # Read all lines into a list

    unique_words = list(set(words))  # Remove duplicates
    unique_words.sort(key=str.lower)  # Sort alphabetically

    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(unique_words)  # Write the sorted, unique lines back


# --- Main Execution ---
if __name__ == "__main__":
    filename = (
        "/Users/holtskinner/GitHub/generative-ai/.github/actions/spelling/allow.txt"
    )
    sort_and_deduplicate(filename)
    print(f"File '{filename}' has been sorted and deduplicated.")
