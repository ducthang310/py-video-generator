import logging
import json
import os

from dotenv import load_dotenv
from video_generator import process_and_upload_video
from media_collector import get_account_media
from config import S3_CONFIG, APP_CONFIG
from user_data import update_video_status
from utils import create_temp_folder

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def test_run(account_id, year, audio_file=None):
    media_items = get_account_media(account_id, year)
    process_user_media(account_id, year, media_items, audio_file)


def process_user_media(account_id, year, media_items, audio_file=None):
    if not media_items:
        logger.warning(f"No media items found for user {account_id} in year {year}. Skipping video generation.")
        return

    try:
        logger.info(f"Generating video for user {account_id}")

        create_temp_folder(f"videos/{account_id}")
        output_path = f"{APP_CONFIG['temp_folder']}/videos/{account_id}/{year}.mp4"
        s3_bucket = S3_CONFIG['bucket_name']

        s3_key = process_and_upload_video(
            media_items,
            output_path,
            audio_path=audio_file,
            target_size=(480, 480),
            frame_rate=24,
            s3_bucket=s3_bucket
        )

        if s3_key:
            update_video_status(account_id, year, s3_key)
            logger.info(f"Highlight reel for user {account_id} uploaded to S3: {s3_key}")
        else:
            logger.error(f"Failed to generate or upload video for user {account_id}")

    except Exception as e:
        logger.error(f"Error generating video for user {account_id}: {str(e)}")
        raise


def process_sqs_message(message):
    data = json.loads(message)
    account_id = data.get('accountId')
    year = data.get('year')

    if not account_id or not year:
        logger.error(f"Invalid message format: {message}")
        return

    try:
        media_items = get_account_media(account_id, year)
        # process_user_media(account_id, year, media_items)
        logger.info(f"Successfully processed video for account {account_id} and year {year}")
        logger.info(f"media items", media_items)
    except Exception as e:
        logger.error(f"Error processing video for account {account_id} and year {year}: {str(e)}")


if __name__ == "__main__":
    import boto3

    sqs = boto3.client('sqs')
    queue_url = os.getenv('SQS_QUEUE_URL')

    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20
        )

        messages = response.get('Messages', [])

        for message in messages:
            process_sqs_message(message['Body'])
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
