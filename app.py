import os
import tempfile
import shutil
import zipfile
import uuid
import threading
import json
import time
from flask import Flask, render_template, request, send_file, jsonify, Response, abort
from werkzeug.utils import secure_filename
from video_processor import extract_snapshots

app = Flask(__name__)
# Allow large video uploads (e.g. 500 MB)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024 

# In-memory task tracker
tasks = {}

def global_cleanup_task():
    while True:
        time.sleep(3600) # Run every hour
        current_time = time.time()
        to_delete = []
        for task_id, task_info in tasks.items():
            if 'created_at' in task_info and current_time - task_info['created_at'] > 3600:
                to_delete.append(task_id)
        
        for task_id in to_delete:
            shutil.rmtree(tasks[task_id]['temp_dir'], ignore_errors=True)
            del tasks[task_id]

# Start cleanup thread
threading.Thread(target=global_cleanup_task, daemon=True).start()

def process_video_task(task_id, video_path, num_snaps, temp_dir, **kwargs):
    try:
        tasks[task_id]['status'] = 'processing'
        output_dir = os.path.join(temp_dir, 'snaps')
        os.makedirs(output_dir, exist_ok=True)
        
        def progress_callback(current, total, thumb_rgb=None):
            tasks[task_id]['progress'] = int((current / total) * 100)
            
        extract_snapshots(
            video_path, 
            num_snaps, 
            output_dir=output_dir,
            progress_callback=progress_callback,
            **kwargs
        )
        
        tasks[task_id]['status'] = 'completed'
        
    except Exception as e:
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['error'] = str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    try:
        num_snaps = int(request.form.get('num_snaps', 20))
        if num_snaps <= 0:
            return jsonify({'error': 'Number of snapshots must be greater than 0'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid number of snaps'}), 400
        
    img_format = request.form.get('format', 'jpg')
    
    # Optional Advanced Parameters
    start_sec = request.form.get('start_sec')
    end_sec = request.form.get('end_sec')
    start_sec = float(start_sec) if start_sec else None
    end_sec = float(end_sec) if end_sec else None
    
    quality = int(request.form.get('quality', 95))
    add_watermark = request.form.get('add_watermark') == 'true'

    if file:
        filename = secure_filename(file.filename)
        task_id = str(uuid.uuid4())
        temp_dir = tempfile.mkdtemp()
        
        video_path = os.path.join(temp_dir, filename)
        file.save(video_path)
        
        tasks[task_id] = {
            'status': 'starting',
            'progress': 0,
            'temp_dir': temp_dir,
            'created_at': time.time(),
            'video_filename': filename
        }
        
        # Start background thread
        thread = threading.Thread(
            target=process_video_task,
            args=(task_id, video_path, num_snaps, temp_dir),
            kwargs={
                'img_format': img_format,
                'start_sec': start_sec,
                'end_sec': end_sec,
                'quality': quality,
                'add_watermark': add_watermark
            }
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({'task_id': task_id})

@app.route('/status/<task_id>')
def task_status(task_id):
    def generate_events():
        while True:
            if task_id not in tasks:
                yield f"data: {json.dumps({'status': 'error', 'error': 'Task not found'})}\n\n"
                break
                
            task_info = tasks[task_id]
            yield f"data: {json.dumps({'status': task_info['status'], 'progress': task_info.get('progress', 0), 'error': task_info.get('error', '')})}\n\n"
            
            if task_info['status'] in ['completed', 'error']:
                break
                
            time.sleep(0.5)
            
    return Response(generate_events(), mimetype='text/event-stream')

@app.route('/results/<task_id>', methods=['GET'])
def get_results(task_id):
    if task_id not in tasks or tasks[task_id]['status'] != 'completed':
        return jsonify({'error': 'Invalid task or task not completed'}), 400
        
    temp_dir = tasks[task_id]['temp_dir']
    output_dir = os.path.join(temp_dir, 'snaps')
    
    if not os.path.exists(output_dir):
        return jsonify({'files': []})
        
    files = sorted(os.listdir(output_dir))
    return jsonify({'files': files})

@app.route('/results/<task_id>/<filename>', methods=['GET'])
def serve_result(task_id, filename):
    if task_id not in tasks:
        abort(404)
        
    temp_dir = tasks[task_id]['temp_dir']
    output_dir = os.path.join(temp_dir, 'snaps')
    file_path = os.path.join(output_dir, secure_filename(filename))
    
    if not os.path.exists(file_path):
        abort(404)
        
    return send_file(file_path)

@app.route('/results/<task_id>/<filename>', methods=['DELETE'])
def delete_result(task_id, filename):
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
        
    temp_dir = tasks[task_id]['temp_dir']
    output_dir = os.path.join(temp_dir, 'snaps')
    file_path = os.path.join(output_dir, secure_filename(filename))
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/download/<task_id>')
def download_result(task_id):
    if task_id not in tasks or tasks[task_id]['status'] != 'completed':
        return "Invalid task or task not completed", 400
        
    task_info = tasks[task_id]
    temp_dir = task_info['temp_dir']
    output_dir = os.path.join(temp_dir, 'snaps')
    
    video_filename = task_info.get('video_filename', 'video')
    zip_filename = f"{os.path.splitext(video_filename)[0]}_snaps.zip"
    zip_path = os.path.join(temp_dir, zip_filename)
    
    # Generate ZIP on the fly
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if os.path.exists(output_dir):
            for f in os.listdir(output_dir):
                file_path = os.path.join(output_dir, f)
                if os.path.isfile(file_path):
                    zipf.write(file_path, arcname=f)
    
    # Allow cleanup later
    def cleanup():
        time.sleep(120) # Wait 2 minutes before deleting to allow download to complete
        shutil.rmtree(temp_dir, ignore_errors=True)
        if task_id in tasks:
            del tasks[task_id]
            
    threading.Thread(target=cleanup, daemon=True).start()
    
    return send_file(
        zip_path, 
        as_attachment=True, 
        download_name=zip_filename,
        mimetype='application/zip'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
