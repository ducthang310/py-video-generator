import boto3
import os
from config import S3_CONFIG


def get_s3_client():
    """Create and return an S3 client."""
    return boto3.client('s3',
                        aws_access_key_id=S3_CONFIG['aws_access_key_id'],
                        aws_secret_access_key=S3_CONFIG['aws_secret_access_key'],
                        region_name=S3_CONFIG['region_name'])


def download_file_from_s3(bucket_name, object_key, local_path):
    """Download a file from S3 to a local path."""
    s3 = get_s3_client()
    s3.download_file(bucket_name, object_key, local_path)


def upload_file_to_s3(local_path, bucket_name, object_key):
    """Upload a local file to S3."""
    s3 = get_s3_client()
    s3.upload_file(local_path, bucket_name, object_key)


def upload_spotlight_and_cleanup(local_path, bucket_name, object_key, temp_files):
    """
    Upload the spotlight video to S3 and delete local files.

    :param local_path: Path to the local spotlight video file
    :param bucket_name: S3 bucket name
    :param object_key: S3 object key for the uploaded file
    :param temp_files: List of temporary files to be deleted
    :return: S3 URL of the uploaded spotlight video
    """
    try:
        # Upload the spotlight video to S3
        upload_file_to_s3(local_path, bucket_name, object_key)

        # Generate the S3 URL for the uploaded file
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"

        # Delete the local spotlight video file
        os.remove(local_path)

        # Delete temporary files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        return s3_url
    except Exception as e:
        print(f"Error uploading spotlight video and cleaning up: {str(e)}")
        raise