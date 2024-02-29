import os
import re


def update_colab_links(file_path):
    with open(file_path, "r") as file:
        content = file.read()

    # Update Colab links
    updated_content = re.sub(
        r'(<a\s+href="https://colab\.research\.google\.com/[^"]+">)\s*<img[^>]+><br>\s*Run in Colab\s*</a>',
        r'\1\n<img width="32px" src="https://lh3.googleusercontent.com/JmcxdQi-qOpctIvWKgPtrzZdJJK-J3sWE1RsfjZNwshCFgE_9fULcNpuXYTilIR2hjwN" alt="Google Cloud Colab Enterprise logo"><br> Run in Colab Enterprise',
        content,
    )

    # Save the updated content
    with open(file_path, "w") as file:
        file.write(updated_content)


def process_notebooks(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".ipynb"):
                file_path = os.path.join(root, file)
                update_colab_links(file_path)


# Specify the directory to process
directory_to_process = "/Users/holtskinner/GitHub/generative-ai/"

# Process Jupyter Notebooks in the specified directory and its subdirectories
process_notebooks(directory_to_process)
