import json
import base64
import re
import os
import uuid
import unicodedata
import string
from functools import partial
from pathlib import Path  # Using pathlib for easier path manipulation

# --- GCS ---
# Import GCS library ONLY if we intend to use it.
# This allows the script to potentially still run without GCS features if needed.
try:
    from google.cloud import storage
    from google.cloud.exceptions import GoogleCloudError

    _GCS_AVAILABLE = True
except ImportError:
    _GCS_AVAILABLE = False
    print("WARNING: google-cloud-storage library not found. GCS upload disabled.")
    print("Install it using: pip install google-cloud-storage")

# --- Configuration ---
# Placeholders now include full GCS path
GCS_PLACEHOLDER_TEMPLATE = "![{filename}]({gcs_uri})"
GCS_OUTPUT_PLACEHOLDER_TEXT = "Image extracted to: {gcs_uri}"
# Local saving fallback (optional, if needed)
LOCAL_IMAGE_DIR = "extracted_images_local_fallback"
LOCAL_PLACEHOLDER_TEMPLATE = "![{filename}](LOCAL_IMAGE_EXTRACTED:{filename})"
LOCAL_OUTPUT_PLACEHOLDER_TEXT = "Image extracted locally to: {filename}"


# --- Helper Functions ---


def slugify(value, allow_unicode=False):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    (Slightly modified from Django's slugify)
    """
    value = str(value).replace(".png", "").replace(".jpg", "").replace(".jpeg", "")

    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    value = re.sub(r"[-\s]+", "-", value).strip("-_")
    # Ensure it's not empty and doesn't start/end weirdly
    if not value:
        return f"image_{uuid.uuid4().hex[:8]}"
    return value


def upload_image_to_gcs(
    img_data,
    img_type,
    base_filename,
    gcs_client,
    bucket_name,
    gcs_full_prefix,
    cell_index,
    unique_id,
):
    """Decodes base64 data and uploads it to GCS."""
    if not _GCS_AVAILABLE or not gcs_client:
        print(f"   GCS client not available. Cannot upload '{base_filename}'.")
        return None  # Cannot upload

    try:
        # Basic sanitization/slugification for filename
        safe_basename = (
            slugify(base_filename)
            if base_filename
            else f"cell_{cell_index}_img_{unique_id}"
        )
        filename = f"{safe_basename}.{img_type}"

        # Construct the full GCS object path
        # Ensure prefix ends with a slash if it's not empty
        blob_path = gcs_full_prefix
        if blob_path and not blob_path.endswith("/"):
            blob_path += "/"
        blob_path += filename

        # Get bucket and blob objects
        bucket = gcs_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        # Decode image data
        img_bytes = base64.b64decode(img_data)

        # Upload data directly from string/bytes
        blob.upload_from_string(img_bytes, content_type=f"image/{img_type}")

        gcs_uri = f"gs://{bucket_name}/{blob_path}"
        print(f"   Uploaded image to: {gcs_uri}")
        return gcs_uri  # Return the full GCS URI

    except base64.binascii.Error as e:
        print(
            f"   Error decoding base64 for '{base_filename}' (cell {cell_index}): {e}"
        )
        return None
    except GoogleCloudError as e:
        print(f"   GCS Error uploading '{filename}' (cell {cell_index}): {e}")
        return None
    except Exception as e:
        print(
            f"   An unexpected error occurred uploading '{base_filename}' (cell {cell_index}): {e}"
        )
        return None


# --- Cell Processing Functions (Modified for GCS URI) ---


def process_markdown_cell(
    cell_content, gcs_client, bucket_name, gcs_full_prefix, cell_index
):
    """Processes a markdown cell's source for base64 images and uploads them."""
    modified = False
    # Regex to find ![alt/filename](data:image/type;base64,data...)
    pattern = r"!\[(.*?)\]\((data:image/(.*?);base64,(.*?))\)"

    def replace_match(match):
        nonlocal modified
        alt_text = match.group(1).strip()
        img_type = match.group(3).strip().lower()
        b64_data = match.group(4).strip()
        # original_data_uri = match.group(2) # Full data:image/... string

        # Use alt text as base filename if available, else generate one
        base_filename = alt_text if alt_text else f"markdown_img_{uuid.uuid4().hex[:6]}"

        # Attempt to upload
        gcs_uri = upload_image_to_gcs(
            b64_data,
            img_type,
            base_filename,
            gcs_client,
            bucket_name,
            gcs_full_prefix,
            cell_index,
            uuid.uuid4().hex[:6],
        )

        if gcs_uri:
            modified = True
            # Return the placeholder using the GCS URI and the base filename
            # Extract filename from URI for the alt text part if needed
            placeholder_filename = gcs_uri.split("/")[-1]
            return GCS_PLACEHOLDER_TEMPLATE.format(
                filename=placeholder_filename,
                gcs_uri=gcs_uri.replace("gs://", "https://storage.googleapis.com/"),
            )
        else:
            # If upload failed, return the original markdown unchanged
            # Optionally add a comment or save locally as fallback
            print(
                f"   Failed to upload image '{base_filename}', keeping original data URI."
            )
            return match.group(0)

    # Use re.sub with the replacement function
    if isinstance(cell_content, list):
        original_source = "".join(cell_content)
        new_source = re.sub(pattern, replace_match, original_source)
        new_source_list = [line + "\n" for line in new_source.splitlines()]
        if new_source_list and not original_source.endswith("\n"):
            if new_source_list[-1].endswith("\n"):
                new_source_list[-1] = new_source_list[-1][:-1]
        elif not new_source_list and not original_source:
            new_source_list = []
        return new_source_list, modified
    elif isinstance(cell_content, str):
        original_source = cell_content
        new_source = re.sub(pattern, replace_match, original_source)
        return new_source, modified
    else:
        return cell_content, False


def process_code_cell_outputs(
    outputs, gcs_client, bucket_name, gcs_full_prefix, cell_index
):
    """Processes code cell outputs for embedded base64 images and uploads them."""
    modified = False
    if not outputs:
        return modified

    for i, output in enumerate(outputs):
        if output.get("output_type") in ("display_data", "execute_result"):
            data = output.get("data", {})
            keys_to_replace = {}

            for key, value in data.items():
                if (
                    key.startswith("image/")
                    and isinstance(value, str)
                    and len(value) > 100
                ):
                    try:
                        base64.b64decode(value)
                        is_b64 = True
                    except (base64.binascii.Error, ValueError):
                        is_b64 = False

                    if is_b64:
                        img_type = key.split("/")[-1].split("+")[0]
                        b64_data = value
                        base_filename = f"cell_{cell_index}_output_{i}_{img_type}"

                        # Attempt to upload
                        gcs_uri = upload_image_to_gcs(
                            b64_data,
                            img_type,
                            base_filename,
                            gcs_client,
                            bucket_name,
                            gcs_full_prefix,
                            cell_index,
                            f"{i}_{uuid.uuid4().hex[:4]}",
                        )

                        if gcs_uri:
                            placeholder_content = GCS_OUTPUT_PLACEHOLDER_TEXT.format(
                                gcs_uri=gcs_uri
                            )
                            keys_to_replace[key] = placeholder_content
                            if "text/plain" not in data:
                                keys_to_replace["text/plain"] = placeholder_content
                            modified = True
                        else:
                            print(
                                f"   Failed to upload output image {i} for cell {cell_index}, keeping original data."
                            )
                            # Optionally keep original or add a failure message

            # Apply the replacements after iterating
            for key, placeholder in keys_to_replace.items():
                data[key] = placeholder
                if key.startswith("image/") and "text/plain" not in data:
                    data["text/plain"] = placeholder

    return modified


# --- Main Processing Function ---


def process_notebook_gcs(
    ipynb_path,
    gcs_bucket_name,
    gcs_base_prefix="generative-ai/",
    notebook_base_dir=None,
    save_backup=False,
):
    """
    Reads an ipynb file, extracts embedded base64 images, uploads them to GCS,
    replaces them with GCS URI placeholders, and saves the modified notebook.

    Args:
        ipynb_path (str): Path to the input .ipynb file.
        gcs_bucket_name (str): Name of the target GCS bucket (e.g., 'github-repo').
        gcs_base_prefix (str): The base directory within GCS under which the
                                notebook's relative path structure will be created
                                (e.g., 'generative-ai/'). Must end with '/' if not empty.
        notebook_base_dir (str, optional): The local base directory corresponding
                                          to `gcs_base_prefix`. Used to calculate
                                          the notebook's relative path for GCS structure.
                                          If None, uploads will go directly under
                                          `gcs_base_prefix` without subdirs.
        save_backup (bool): If True, save a backup of the original notebook locally.
    """
    if not _GCS_AVAILABLE:
        print("ERROR: google-cloud-storage library is required for GCS uploads.")
        return

    input_path = Path(ipynb_path).resolve()  # Get absolute path
    if not input_path.is_file():
        print(f"Error: Input file not found: {input_path}")
        return

    print(f"Processing notebook: {input_path}")
    print(f"Target GCS Bucket: {gcs_bucket_name}")

    # --- Calculate Relative Path for GCS ---
    relative_notebook_dir = ""
    if notebook_base_dir:
        try:
            base_path = Path(notebook_base_dir).resolve()
            # Find relative path of the notebook's *directory* compared to the base
            relative_notebook_dir = input_path.parent.relative_to(base_path)
            print(f"   Relative notebook dir: {relative_notebook_dir}")
        except ValueError:
            print(
                f"Warning: Notebook path '{input_path}' is not inside the base directory '{notebook_base_dir}'."
            )
            print(
                f"         Uploading images directly under '{gcs_base_prefix}' in the bucket."
            )
            relative_notebook_dir = ""  # Fallback to no relative path
        except Exception as e:
            print(f"Warning: Error calculating relative path: {e}")
            relative_notebook_dir = ""
    else:
        print(
            "   No notebook_base_dir provided. Uploading images directly under GCS base prefix."
        )

    # Construct the final GCS prefix for *this notebook's images*
    # Remove potential leading/trailing slashes from parts before joining cleanly
    parts = [
        p
        for p in [
            gcs_base_prefix.strip("/"),
            str(relative_notebook_dir).strip("/"),
            input_path.stem,  # Use notebook filename (without ext) as final subdir
        ]
        if p
    ]
    notebook_gcs_prefix = "/".join(parts)
    # Ensure it ends with a slash
    if notebook_gcs_prefix and not notebook_gcs_prefix.endswith("/"):
        notebook_gcs_prefix += "/"

    print(
        f"   Uploading images to GCS prefix: gs://{gcs_bucket_name}/{notebook_gcs_prefix}"
    )

    # --- Initialize GCS Client ---
    try:
        gcs_client = storage.Client()
        # Verify bucket exists and we have access (optional but good practice)
        gcs_client.lookup_bucket(gcs_bucket_name)
    except GoogleCloudError as e:
        print(
            f"ERROR: Could not connect to GCS or access bucket '{gcs_bucket_name}': {e}"
        )
        print("       Please check authentication and bucket permissions.")
        return
    except Exception as e:
        print(f"ERROR: Failed to initialize GCS Client: {e}")
        return

    # --- Read Notebook ---
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            notebook_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error reading or parsing JSON file: {e}")
        return
    except Exception as e:
        print(f"Error opening file: {e}")
        return

    overall_modified = False

    # --- Iterate Through Cells ---
    for i, cell in enumerate(notebook_data.get("cells", [])):
        cell_modified = False
        if cell.get("cell_type") == "markdown":
            # print(f"Processing Markdown Cell {i}...") # Less verbose now
            source = cell.get("source", [])
            new_source, cell_modified = process_markdown_cell(
                source, gcs_client, gcs_bucket_name, notebook_gcs_prefix, i
            )
            if cell_modified:
                cell["source"] = new_source

        elif cell.get("cell_type") == "code":
            # print(f"Processing Code Cell {i} Outputs...") # Less verbose now
            outputs = cell.get("outputs", [])
            cell_modified = process_code_cell_outputs(
                outputs, gcs_client, gcs_bucket_name, notebook_gcs_prefix, i
            )

        if cell_modified:
            overall_modified = True
            # print(f"   Modified Cell {i}") # Less verbose

    # --- Save Modified Notebook ---
    if overall_modified:
        output_path_str = str(input_path)  # Overwrite original by default
        if save_backup:
            backup_path = output_path_str + ".bak"
            print(f"Saving backup to: {backup_path}")
            try:
                import shutil

                shutil.copy2(output_path_str, backup_path)
            except Exception as e:
                print(f"Warning: Could not create backup file: {e}")

        print(f"Saving modified notebook to: {output_path_str}")
        try:
            with open(output_path_str, "w", encoding="utf-8") as f:
                # Use indent=1 for Colab-like format, no trailing whitespace
                json.dump(
                    notebook_data,
                    f,
                    indent=1,
                    separators=(",", ": "),
                    ensure_ascii=False,
                )
            print("Notebook saved successfully.")
        except Exception as e:
            print(f"Error saving modified notebook: {e}")
            if save_backup:
                print(f"Original notebook backed up at: {backup_path}")
    else:
        print("No embedded images found or modified.")


# --- Example Usage ---
if __name__ == "__main__":
    # --- === CONFIGURATION FOR EXAMPLE === ---
    target_notebook = "/Users/holtskinner/GitHub/generative-ai/gemini/tuning/sft_gemini_automatic_evaluation.ipynb"  # <--- CHANGE THIS
    gcs_bucket = "github-repo"  # <--- Your GCS Bucket
    gcs_prefix = "generative-ai/"  # <--- Base path in GCS for notebooks
    # This local path should correspond to the gcs_prefix structure
    local_notebook_repo_base = "."  # <--- CHANGE THIS

    # --- === SAFETY CHECK === ---
    if "your_notebook" in target_notebook:
        print("=" * 60)
        print(
            "!!! PLEASE UPDATE THE 'target_notebook' AND 'local_notebook_repo_base' VARIABLES"
        )
        print("!!! in the __main__ block with your actual file paths before running.")
        print("=" * 60)
    else:
        process_notebook_gcs(
            ipynb_path=target_notebook,
            gcs_bucket_name=gcs_bucket,
            gcs_base_prefix=gcs_prefix,
            notebook_base_dir=local_notebook_repo_base,
            save_backup=False,
        )
