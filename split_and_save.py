import re


def split_and_save_sections(input_filename):
    """Splits a file into sections based on delimiter, removes trailing string,
    and saves them as separate files."""

    with open(input_filename, "r") as file:
        content = file.read()

    delimiter = r"----- File: (.*?) -----"

    sections = re.split(delimiter, content, flags=re.DOTALL)

    # Remove trailing "-------------------------" and save
    for filename, section in zip(sections[1::2], sections[2::2]):
        filename = filename.strip()

        # Remove trailing string if present
        section = re.sub(
            r"-------------------------+$", "", section, flags=re.MULTILINE
        )

        with open(filename, "w") as outfile:
            outfile.write(section.strip())


if __name__ == "__main__":
    input_filename = "/Users/holtskinner/Downloads/output-import.txt"
    split_and_save_sections(input_filename)
