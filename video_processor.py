import cv2
import os

def extract_snapshots(video_path, num_snaps, output_dir=None, 
                      start_sec=None, end_sec=None, 
                      img_format='jpg', quality=95, 
                      add_watermark=False, progress_callback=None):
    """
    Extracts evenly spaced snapshots from a video with advanced features.
    
    :param video_path: Path to the video file
    :param num_snaps: Number of snapshots to extract
    :param output_dir: Optional custom output directory
    :param start_sec: Optional start time in seconds
    :param end_sec: Optional end time in seconds
    :param img_format: 'jpg' or 'png'
    :param quality: JPEG quality (0-100) or PNG inverse compression
    :param add_watermark: Boolean to burn timestamp onto image
    :param progress_callback: Callback function(current, total, thumbnail_rgb)
    :return: (output_dir, extracted_count)
    """
    if num_snaps <= 0:
        raise ValueError("Number of snapshots must be greater than 0")

    # Open the video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {video_path}")

    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    if total_frames <= 0 or fps <= 0:
        cap.release()
        raise ValueError("Could not read video properties properly.")

    duration = total_frames / fps

    # Handle Time Range
    start_time = max(0.0, float(start_sec)) if start_sec is not None else 0.0
    end_time = min(duration, float(end_sec)) if end_sec is not None else duration
    
    if start_time >= end_time:
        cap.release()
        raise ValueError(f"Start time ({start_time}s) must be less than end time ({end_time}s).")

    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)
    range_frames = end_frame - start_frame

    # Calculate frame indices to capture
    if num_snaps == 1:
        # Just grab the middle frame of the range
        frame_indices = [start_frame + range_frames // 2]
    else:
        interval = range_frames / num_snaps
        frame_indices = [int(start_frame + i * interval) for i in range(num_snaps)]

    # Handle output directory
    if not output_dir:
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.join(video_dir, f"{video_name}_snaps")
    
    os.makedirs(output_dir, exist_ok=True)

    extracted_count = 0
    img_format = img_format.lower().replace('.', '')
    if img_format not in ['jpg', 'jpeg', 'png']:
        img_format = 'jpg'

    for idx, frame_idx in enumerate(frame_indices):
        # Set frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if ret:
            # Calculate timestamp
            time_sec = frame_idx / fps
            mins = int(time_sec // 60)
            secs = int(time_sec % 60)
            ms = int((time_sec - int(time_sec)) * 100)
            
            time_str = f"{mins:02d}:{secs:02d}.{ms:02d}"
            
            # Add Timestamp Watermark
            if add_watermark:
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 1
                thickness = 2
                
                # Get text size to position it in bottom right
                text_size = cv2.getTextSize(time_str, font, font_scale, thickness)[0]
                text_x = frame.shape[1] - text_size[0] - 20
                text_y = frame.shape[0] - 20
                
                # Add black outline
                cv2.putText(frame, time_str, (text_x, text_y), font, font_scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
                # Add white text
                cv2.putText(frame, time_str, (text_x, text_y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
            
            # Name file: snap_001_00m_02s_50.jpg
            filename = f"snap_{idx+1:03d}_{mins:02d}m_{secs:02d}s_{ms:02d}.{img_format}"
            output_path = os.path.join(output_dir, filename)
            
            # Save the frame
            if img_format in ['jpg', 'jpeg']:
                cv2.imwrite(output_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
            else:
                # PNG compression ranges from 0-9. Map quality (0-100) to compression (9-0)
                compression = int(9 - (quality / 100) * 9)
                cv2.imwrite(output_path, frame, [int(cv2.IMWRITE_PNG_COMPRESSION), compression])
                
            extracted_count += 1
            
            # Generate thumbnail for UI preview
            if progress_callback:
                thumb_height = 250
                aspect_ratio = frame.shape[1] / frame.shape[0]
                thumb_width = int(thumb_height * aspect_ratio)
                
                thumbnail = cv2.resize(frame, (thumb_width, thumb_height))
                # Convert BGR (OpenCV) to RGB (Pillow/Tkinter)
                thumbnail_rgb = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
                
                progress_callback(idx + 1, num_snaps, thumbnail_rgb)

    cap.release()
    return output_dir, extracted_count
