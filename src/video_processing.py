import cv2
import numpy as np
import os
from multiprocessing import Pool, cpu_count
import math
import time
import logging
from datetime import datetime
from s3_connector import download_file_from_s3
from config import S3_CONFIG, APP_CONFIG

# Set up logging
log_file = f"video_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file),
                        logging.StreamHandler()
                    ])


def get_yolo_path(filename):
    """Get the path for YOLO files, downloading from S3 if necessary"""
    local_path = f"{APP_CONFIG['temp_folder']}/{filename}"
    if not os.path.exists(local_path):
        s3_bucket = S3_CONFIG['bucket_name']
        s3_key = f"yolo/{filename}"
        try:
            download_file_from_s3(s3_bucket, s3_key, local_path)
        except Exception as e:
            logging.error(f"Failed to download {filename} from S3: {str(e)}")
            raise
    return local_path


def detect_people_yolo(frame, net, ln, confidence_threshold=0.5):
    (H, W) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    layerOutputs = net.forward(ln)

    boxes = []
    confidences = []
    for output in layerOutputs:
        for detection in output:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]
            if classID == 0 and confidence > confidence_threshold:  # 0 is the class ID for person
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))

    return boxes, confidences


def detect_faces(args):
    frame, frame_number, fps = args
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    if len(faces) > 0:
        return frame_number, frame_number / fps, f"Faces detected: {len(faces)}"
    return None


def resize_frame_with_padding(frame, target_size):
    h, w = frame.shape[:2]
    target_w, target_h = target_size

    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    result = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    x_offset = (target_w - new_w) // 2
    y_offset = (target_h - new_h) // 2
    result[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized

    return result


def extract_subvideo_segment(cap, start_frame, fps, video_duration, duration, target_size, output_path):
    start_time = start_frame / fps
    end_time = min(start_time + np.random.uniform(duration[0], duration[1]), video_duration)

    logging.info(f"Extracting subvideo from {start_time:.2f}s to {end_time:.2f}s")

    # Ensure output file has .mp4 extension
    output_path = os.path.splitext(output_path)[0] + '.mp4'

    # Set up video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, target_size, isColor=True)

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frame_count = 0
    total_frames_to_extract = int((end_time - start_time) * fps)

    while frame_count < total_frames_to_extract:
        ret, frame = cap.read()
        if not ret:
            break

        resized_frame = resize_frame_with_padding(frame, target_size)
        out.write(resized_frame)
        frame_count += 1

        if frame_count % 30 == 0:  # Log progress every 30 frames
            logging.info(f"Processed {frame_count}/{total_frames_to_extract} frames")

    cap.release()
    out.release()

    logging.info(f"Subvideo saved to {output_path}")
    return output_path


def extract_subvideo(video_path, output_path, target_size=(480, 480), duration=(5, 8), confidence_threshold=0.7,
                     max_video_duration=40):
    try:
        start_time = time.time()
        logging.info(f"Opening video file: {video_path}")
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            logging.error(f"Error opening video file: {video_path}")
            return None

        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = total_frames / fps
        logging.info(f"Video loaded. FPS: {fps}, Total frames: {total_frames}, Duration: {video_duration:.2f}s")

        if video_duration > max_video_duration:
            logging.warning(
                f"Video duration ({video_duration:.2f}s) exceeds maximum allowed duration ({max_video_duration}s)")
            return None

        # Load YOLO
        yolo_cfg = get_yolo_path("yolov3.cfg")
        yolo_weights = get_yolo_path("yolov3.weights")

        logging.info(f"Loading YOLO model from:")
        logging.info(f"Config: {yolo_cfg}")
        logging.info(f"Weights: {yolo_weights}")

        logging.info("YOLO files found.")
        net = cv2.dnn.readNetFromDarknet(yolo_cfg, yolo_weights)
        ln = net.getLayerNames()
        try:
            unconnected_layers = net.getUnconnectedOutLayers()
            if isinstance(unconnected_layers, np.ndarray):
                ln = [ln[i - 1] for i in unconnected_layers.flatten()]
            else:
                ln = [ln[i[0] - 1] for i in unconnected_layers]
        except IndexError:
            ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]
        logging.info("YOLO network loaded successfully")

        # Process frames with YOLO
        frames = []
        for i in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                break

            if net is not None and ln is not None:
                boxes, confidences = detect_people_yolo(frame, net, ln, confidence_threshold=confidence_threshold)
                if boxes:
                    logging.info(f"People detected at frame {i} at {i / fps:.2f}s: {len(boxes)}")
                    return extract_subvideo_segment(cap, i, fps, video_duration, duration, target_size, output_path)

            frames.append((frame, i, fps))

            if i % 30 == 0:  # Log progress every 30 frames
                logging.info(f"Processed {i}/{total_frames} frames with YOLO")

        logging.info("No people detected with YOLO. Proceeding with parallel face detection.")

        # Use multiprocessing for face detection
        num_processes = cpu_count()
        chunk_size = math.ceil(len(frames) / num_processes)

        with Pool(processes=num_processes) as pool:
            results = pool.map(detect_faces, frames, chunksize=chunk_size)

        # Filter out None results and sort by frame number
        valid_results = [r for r in results if r is not None]
        valid_results.sort(key=lambda x: x[0])

        if valid_results:
            start_frame, start_time, reason = valid_results[0]
            logging.info(f"Faces detected at frame {start_frame} at {start_time:.2f}s: {reason}")
            return extract_subvideo_segment(cap, start_frame, fps, video_duration, duration, target_size, output_path)

        logging.info("No people or faces detected in the video.")

        # If no interesting content found, use the beginning of the video
        result = extract_subvideo_segment(cap, 0, fps, video_duration, duration, target_size, output_path)

        end_time = time.time()
        logging.info(f"Total processing time: {end_time - start_time:.2f} seconds")

        return result

    except Exception as e:
        logging.error(f"An error occurred during subvideo extraction: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return None
    finally:
        if 'cap' in locals() and cap.isOpened():
            cap.release()


# # Usage example:
# if __name__ == '__main__':
#     result = extract_subvideo('tests/media/videos/peo2.mov', 'tests/media/videos/peo2_sub.mp4')
#     logging.info(f"Script execution completed. Result: {result}")