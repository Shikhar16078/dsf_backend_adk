import os

def load_instructions_file(filename: str, default: str = "") -> str:
    """
    Loads instruction or description text from a given file path.

    Args:
        filename (str): Path to the file to read (relative or absolute).
        default (str): Default string to return if the file is not found or fails to load.

    Returns:
        str: The file contents if successful, or the fallback default string.
    """

    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()

    except FileNotFoundError:
        # If the file doesn't exist, log a warning and fall back to the default value.
        print(f"[WARNING] File not found: {filename}. Using default.")

    except Exception as e:
        # Catch any other exception (e.g. permission issues, IO errors) and log it.
        print(f"[ERROR] Failed to load {filename}: {e}")

    # Return the fallback default string if anything goes wrong.
    return default