import os
from config import APP_CONFIG


def create_temp_folder(folder_path):
    """
    Creates a nested folder structure in the temp directory if it doesn't exist.

    :param folder_path: Path of the folder to create, can include nested folders
    :return: Full path of the created (or existing) folder
    """
    # Get the base temp directory from APP_CONFIG
    base_temp_dir = APP_CONFIG['temp_folder']

    # Full path of the folder to be created
    full_path = os.path.join(base_temp_dir, folder_path)

    try:
        # Create the folder (and any necessary parent folders)
        os.makedirs(full_path, exist_ok=True)
        print(f"Folder ready: {full_path}")
    except OSError as e:
        print(f"Error creating folder {full_path}: {e}")
        raise

    return full_path


# Example usage
if __name__ == "__main__":
    new_folder_path = create_temp_folder("videos/account-123")
    print(f"Folder path: {new_folder_path}")