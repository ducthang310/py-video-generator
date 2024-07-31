import cv2
import numpy as np
from moviepy.editor import VideoClip, concatenate_videoclips


def resize_and_crop_image(image_path, target_size=(480, 480)):
    """Resize and crop an image to fit the target size while maintaining aspect ratio."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise IOError(f"Unable to read image: {image_path}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert to RGB
        print(f"Image shape after reading: {img.shape}")

        height, width = img.shape[:2]
        aspect_ratio = width / height
        target_aspect = target_size[0] / target_size[1]

        if aspect_ratio > target_aspect:
            # Image is wider, crop the width
            new_width = int(height * target_aspect)
            start_x = (width - new_width) // 2
            img = img[:, start_x:start_x + new_width]
        else:
            # Image is taller, crop the height
            new_height = int(width / target_aspect)
            start_y = (height - new_height) // 2
            img = img[start_y:start_y + new_height, :]

        resized_img = cv2.resize(img, target_size)
        print(f"Image shape after resize: {resized_img.shape}")
        return resized_img
    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
        return None


def apply_animation(img, effect_type, t):
    """Apply animation effect to an image."""
    if not isinstance(img, np.ndarray):
        print(f"Error: Expected numpy array, got {type(img)}")
        return np.zeros((480, 480, 3), dtype=np.uint8)  # Return a black image as fallback

    print(f"Applying {effect_type} animation, t={t}")
    print(f"Image shape in apply_animation: {img.shape}")

    if effect_type == 'fade':
        alpha = 1 - abs(1 - 2 * t)  # Fade in and out
        return (img * alpha).astype('uint8')
    elif effect_type == 'zoom':
        scale = 1 + (0.5 * t)  # Zoom in by 50% over the duration
        center_x, center_y = img.shape[1] // 2, img.shape[0] // 2
        trans_mat = cv2.getRotationMatrix2D((center_x, center_y), 0, scale)
        return cv2.warpAffine(img, trans_mat, (img.shape[1], img.shape[0]))
    elif effect_type == 'slide':
        offset = int(img.shape[1] * t)  # Slide from left to right
        slide_img = np.zeros_like(img)
        slide_img[:, :img.shape[1] - offset] = img[:, offset:]
        return slide_img
    elif effect_type == 'rotate':
        angle = 360 * t  # Rotate 360 degrees over the duration
        center_x, center_y = img.shape[1] // 2, img.shape[0] // 2
        trans_mat = cv2.getRotationMatrix2D((center_x, center_y), angle, 1)
        return cv2.warpAffine(img, trans_mat, (img.shape[1], img.shape[0]))
    return img


def create_animated_clip(image_path, duration=3, animation_type='fade', target_size=(480, 480)):
    """Create an animated clip from an image with resizing and cropping."""
    img = resize_and_crop_image(image_path, target_size)
    if img is None:
        return None

    print(f"Image shape in create_animated_clip: {img.shape}")

    def make_frame(t):
        return apply_animation(img.copy(), animation_type, t / duration)

    # Create a VideoClip with the make_frame function
    clip = VideoClip(make_frame, duration=duration)

    return clip


def generate_video_from_images(image_paths, output_path, frame_rate=24, target_size=(480, 480)):
    """Generate a video from a list of image paths with animations."""
    clips = []
    effects = ['fade', 'zoom', 'slide', 'rotate']

    for idx, image_path in enumerate(image_paths):
        effect_type = effects[idx % len(effects)]
        print(f"Processing image {idx + 1}/{len(image_paths)}: {image_path}")
        clip = create_animated_clip(image_path, animation_type=effect_type, target_size=target_size)
        if clip is not None:
            clip = clip.resize(target_size)
            clips.append(clip)

    if not clips:
        print("No valid clips to process.")
        return None

    final_clip = concatenate_videoclips(clips)

    try:
        final_clip.write_videofile(
            output_path,
            fps=frame_rate,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            bitrate='5000k',
            ffmpeg_params=["-pix_fmt", "yuv420p"]  # This ensures better compatibility
        )
        return output_path
    except Exception as e:
        print(f"Error writing video file: {str(e)}")
        return None