from db_connector import execute_query
from datetime import datetime
import os
import logging


def get_local_media(image_folder, video_folder):
    """Retrieve media from local folders."""
    media = []

    for folder, media_type in [(image_folder, 'image'), (video_folder, 'video')]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                media.append({
                    'path': file_path,
                    'type': media_type,
                    'created_at': datetime.fromtimestamp(os.path.getctime(file_path))
                })

    return media

def update_video_status(account_id, year, video_path):
    query = """
    UPDATE videos
    SET status = 'DONE', "videoPath" = %s
    WHERE "accountId" = %s AND year = %s
    """
    try:
        execute_query(query, (video_path, account_id, year))
        logging.info(f"Updated video status for account {account_id} and year {year}")
    except Exception as e:
        logging.error(f"Error updating video status: {str(e)}")
        raise