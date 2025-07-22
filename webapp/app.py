from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import sys
import os
sys.path.append('..')
from pdf_translator import PDFTranslator
import threading
import time
import uuid
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Allowed extensions
ALLOWED_EXTENSIONS = {'pdf'}

# Create folders if not exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

# Initialize the PDF translator
translator = PDFTranslator(output_dir=app.config['DOWNLOAD_FOLDER'])

# Store active translations
active_translations = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def translate_pdf_background(file_path, source_lang, task_id, filename):
    """Background task for PDF translation"""
    try:
        socketio.emit('translation_status', {
            'task_id': task_id, 
            'status': 'processing', 
            'message': f'Processing {filename}...'
        })
        
        # Translate PDF
        translated_path = translator.translate_single_pdf(
            file_path, 
            source_lang=source_lang
        )
        
        active_translations[task_id] = {
            'status': 'completed',
            'translated_file': os.path.basename(translated_path),
            'original_file': filename
        }
        
        socketio.emit('translation_status', {
            'task_id': task_id,
            'status': 'completed',
            'message': f'Translation of {filename} completed!',
            'download_url': f'/download/{os.path.basename(translated_path)}'
        })
        
    except Exception as e:
        active_translations[task_id] = {
            'status': 'failed',
            'error': str(e)
        }
        
        socketio.emit('translation_status', {
            'task_id': task_id,
            'status': 'failed',
            'message': f'Translation failed: {str(e)}'
        })

@app.route('/')
def index():
    supported_languages = translator.get_supported_languages()
    return render_template('index.html', languages=supported_languages)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    files = request.files.getlist('files[]')
    source_lang = request.form.get('source_lang', 'auto')
    
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    task_ids = []
    
    for file in files:
        if file and allowed_file(file.filename):
            # Generate unique task ID
            task_id = str(uuid.uuid4())
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{task_id}_{filename}")
            file.save(filepath)
            
            # Initialize task tracking
            active_translations[task_id] = {
                'status': 'queued',
                'original_file': filename
            }
            
            # Start background translation
            thread = threading.Thread(
                target=translate_pdf_background,
                args=(filepath, source_lang, task_id, filename)
            )
            thread.daemon = True
            thread.start()
            
            task_ids.append(task_id)
    
    return jsonify({'task_ids': task_ids, 'message': f'Started processing {len(task_ids)} file(s)'})

@app.route('/batch')
def batch_translate():
    supported_languages = translator.get_supported_languages()
    return render_template('batch.html', languages=supported_languages)

@app.route('/status/<task_id>')
def get_status(task_id):
    if task_id in active_translations:
        return jsonify(active_translations[task_id])
    else:
        return jsonify({'error': 'Task not found'}), 404

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        flash('File not found', 'error')
        return redirect(url_for('index'))

@app.route('/api/languages')
def get_languages():
    return jsonify(translator.get_supported_languages())

@app.route('/about')
def about():
    return render_template('about.html')

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
