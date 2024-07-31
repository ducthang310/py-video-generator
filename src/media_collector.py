import os
from db_connector import execute_query
from s3_connector import download_file_from_s3
from config import S3_CONFIG, APP_CONFIG


def get_account_media(account_id, year):
    """
    Fetch media items for a given account and year.

    :param account_id: ID of the account
    :param year: Year to fetch media for
    :return: List of media items
    """
    query = """
    SELECT f.id, f.path, f.name, p."createdAt", p."imageId", p."videoId"
    FROM posts p
    JOIN files f ON (p."imageId" = f.id OR p."videoId" = f.id)
    WHERE p."accountId" = %s
      AND EXTRACT(YEAR FROM p."createdAt") = %s
    ORDER BY p."createdAt" ASC
    LIMIT 1000
    """

    results = execute_query(query, (account_id, year))

    all_media = [
        {
            'id': row[0],
            'type': 'image' if row[4] is not None else 'video',
            's3Key': f"{row[1]}/{row[2]}",
            'created_at': row[3]
        }
        for row in results
    ]

    # Process to select media items
    selected_media = []
    month_counts = {month: 0 for month in range(1, 13)}

    for item in all_media:
        month = item['created_at'].month
        if month_counts[month] == 0 or len(selected_media) < 12:
            selected_media.append(item)
            month_counts[month] += 1

        if len(selected_media) == 15:
            break

    # If we have less than 12 items, add more from available months
    while len(selected_media) < 12 and len(selected_media) < len(all_media):
        for item in all_media:
            if item not in selected_media:
                selected_media.append(item)
                if len(selected_media) == 12 or len(selected_media) == len(all_media):
                    break

    # Sort the final selected media by created_at in ascending order
    selected_media.sort(key=lambda x: x['created_at'])

    return download_media_items(selected_media)


def download_media_items(media_items):
    """
    Download media items from S3 to local storage.

    :param media_items: List of media items to download
    :return: List of media items with local paths
    """
    downloaded_items = []
    for item in media_items:
        local_path = os.path.join(APP_CONFIG['temp_folder'], item['s3Key'])
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        try:
            download_file_from_s3(S3_CONFIG['bucket_name'], item['s3Key'], local_path)
            downloaded_items.append({
                'type': item['type'],
                'path': local_path
            })
        except Exception as e:
            print(f"Error downloading file {item['s3Key']}: {str(e)}")

    return downloaded_items