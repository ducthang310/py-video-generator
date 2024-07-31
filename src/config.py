import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

S3_CONFIG = {
    'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
    'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
    'region_name': os.getenv('AWS_REGION'),
    'bucket_name': os.getenv('S3_BUCKET_NAME')
}
app_env = os.getenv('APP_ENV')
APP_CONFIG = {
    'app_env': app_env,
    'temp_folder': '/tmp' if app_env in ['production', 'staging'] else 'temp'
}
