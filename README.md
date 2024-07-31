# HighlightReel Video Generator

## Project Purpose

The Video Generator is a Python-based application designed to create personalized videos for users. It automatically compiles a user's images and videos from the past year into an engaging 30-second video, complete with animations and optional background music.

Key features:
- Processes both images and videos
- Applies various animations to images (fade, zoom, slide, rotate)
- Resizes and crops media to a consistent size (347x400 pixels)
- Adds optional background music
- Supports both local files and media stored in a database/S3 bucket

## Project Structure
```
video-video-generator/
    │
    ├── src/
    │   ├── main.py
    │   ├── video_generator.py
    │   ├── image_processing.py
    │   ├── video_processing.py
    │   ├── user_data.py
    │   ├── db_connector.py
    │   ├── s3_connector.py
    │   └── config.py
    │
    ├── tests/
    │   ├── test_video_generator.py
    │   ├── test_image_processing.py
    │   └── test_video_processing.py
    │
    ├── requirements.txt
    └── README.md
```

## Installation

1. Clone the repository: 
```
git clone https://github.com/yourusername/video-video-generator.git
cd video-video-generator
```

2. Create a virtual environment (optional but recommended):
```
python -m venv venv
source venv/bin/activate  # On Windows, use venv\Scripts\activate
```

3. Install the required packages:
```
pip install -r requirements.txt
```

4. Set up your configuration:
   - Copy `.env.example` to `.env`
   - Edit `.env` with your database and S3 credentials



## Running in Production

1. Ensure your database is set up and contains the necessary user and media information.

2. Run the main script:
```
python src/main.py
```

3. The script will generate video videos for all active users and save them in the `temp/videos/` directory.

For processing local files instead of database media:
```
python src/main.py --local --image-folder /path/to/images --video-folder /path/to/videos --audio /path/to/audio.mp3
```

## Running Tests

To run all tests:
```
pytest tests
```

To run tests for a specific module:
```
pytest tests/test_video_generator.py
pytest tests/test_image_processing.py
pytest tests/test_video_processing.py
```