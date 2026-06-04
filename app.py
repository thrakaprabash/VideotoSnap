import os
import tempfile
import shutil
import zipfile
import io
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from video_processor import extract_snapshots

app = Flask(__name__)
# Allow large video uploads (e.g. 500 MB)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024 

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

    if file:
        filename = secure_filename(file.filename)
        
        # Create a temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        
        try:
            video_path = os.path.join(temp_dir, filename)
            file.save(video_path)
            
            output_dir = os.path.join(temp_dir, 'snaps')
            os.makedirs(output_dir, exist_ok=True)
            
            # Extract snapshots using existing core logic
            extract_snapshots(video_path, num_snaps, output_dir=output_dir, img_format=img_format)
            
            # Create ZIP file in memory to allow clean up of temp_dir
            zip_filename = f"{os.path.splitext(filename)[0]}_snaps.zip"
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(output_dir):
                    for f in files:
                        file_path = os.path.join(root, f)
                        zipf.write(file_path, arcname=f)
            
            zip_buffer.seek(0)
            
        except Exception as e:
            # Clean up on error
            shutil.rmtree(temp_dir, ignore_errors=True)
            return jsonify({'error': str(e)}), 500
            
        # Clean up temporary files synchronously since we loaded zip in memory
        shutil.rmtree(temp_dir, ignore_errors=True)
            
        return send_file(
            zip_buffer, 
            as_attachment=True, 
            download_name=zip_filename,
            mimetype='application/zip'
        )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
