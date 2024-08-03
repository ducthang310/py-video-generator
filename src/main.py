try:
  import unzip_requirements
except ImportError:
  pass

from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
from image_processing import generate_video_from_images
from video_processing import extract_subvideo
from s3_connector import upload_spotlight_and_cleanup
import os
import logging
import json
from dotenv import load_dotenv
from media_collector import get_account_media

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_spotlight_video(media_items, output_path, audio_path=None, target_size=(480, 480), frame_rate=24):
    """Generate a spotlight video from a list of media items."""
    video_clips = []
    image_paths = []
    temp_files = []

    for item in media_items:
        if item['type'] == 'image':
            image_paths.append(item['path'])
        elif item['type'] == 'video':
            if image_paths:
                temp_output = f"temp_image_group_{len(video_clips)}.mp4"
                generate_video_from_images(image_paths, temp_output, frame_rate=frame_rate, target_size=target_size)
                video_clips.append(VideoFileClip(temp_output))
                temp_files.append(temp_output)
                image_paths = []

            # Handle different video extensions
            file_name, file_extension = os.path.splitext(item['path'])
            temp_sub_video_path = f"{file_name}_sub{file_extension}"

            sub_video_path = extract_subvideo(item['path'], temp_sub_video_path)
            if sub_video_path is None:
                print(f"Error when extracting subvideo from: {item['path']}")
                continue
            video_clips.append(VideoFileClip(sub_video_path))
            temp_files.append(sub_video_path)

    # Handle any remaining images
    if image_paths:
        temp_output = f"temp_image_group_{len(video_clips)}.mp4"
        generate_video_from_images(image_paths, temp_output, frame_rate=frame_rate, target_size=target_size)
        video_clips.append(VideoFileClip(temp_output))
        temp_files.append(temp_output)

    # Concatenate all video clips
    final_video = concatenate_videoclips(video_clips)

    # Resize the final video to ensure it matches the target size
    final_video = final_video.resize(target_size)

    if audio_path:
        audio = AudioFileClip(audio_path)
        # Ensure the audio is not longer than the video
        audio = audio.subclip(0, min(final_video.duration, audio.duration))
        final_video = final_video.set_audio(audio)

    # Write the final video file
    final_video.write_videofile(
        output_path,
        fps=frame_rate,
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        bitrate='5000k'
    )

    # Clean up temporary files
    for clip in video_clips:
        clip.close()
    for file in temp_files:
        if os.path.exists(file):
            os.remove(file)

    return output_path


def process_and_upload_spotlight(media_items, output_path, audio_path=None, target_size=(480, 480), frame_rate=24,
                                 s3_bucket=None):
    """Generate spotlight video, optionally upload to S3, and clean up."""
    local_path = generate_spotlight_video(media_items, output_path, audio_path, target_size, frame_rate)

    if s3_bucket:
        s3_key = f"spotlights/{os.path.basename(output_path)}"
        upload_spotlight_and_cleanup(local_path, s3_bucket, s3_key, [])
        return s3_key
    else:
        return local_path


def lambda_handler(event, context):
    for record in event['Records']:
        message = json.loads(record['body'])
        account_id = message.get('accountId')
        year = message.get('year')

        if not account_id or not year:
            continue

        try:
            media_items = get_account_media(account_id, year)
            process_and_upload_spotlight(media_items, f"spotlights/{account_id}_{year}.mp4")
        except Exception as e:
            logger.error(f"Error processing spotlight for account {account_id} and year {year}: {str(e)}")

    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete')
    }