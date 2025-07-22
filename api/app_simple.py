from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO
import sys
import os
import threading
import uuid
from pdf_translator import PDFTranslator

# Flask App Config
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Use threading explicitly (avoids eventlet/gevent problems)
socketio = SocketIO(app, cors_allowed_origins="*")

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
        # Update status first
        active_translations[task_id]['status'] = 'processing'
        
        # Notify client: processing started
        socketio.emit('translation_status', {
            'task_id': task_id,
            'status': 'processing',
            'message': f"Processing {filename}..."
        })

        translated_path = translator.translate_single_pdf(file_path, source_lang=source_lang)

        # Update task store
        active_translations[task_id] = {
            'status': 'completed',
            'translated_file': os.path.basename(translated_path),
            'original_file': filename,
            'download_url': f'/download/{os.path.basename(translated_path)}'
        }

        # Notify client: done
        socketio.emit('translation_status', {
            'task_id': task_id,
            'status': 'completed',
            'download_url': f'/download/{os.path.basename(translated_path)}'
        })

    except Exception as e:
        active_translations[task_id] = {
            'status': 'failed',
            'error': str(e),
            'original_file': filename
        }

        # Notify client: error
        socketio.emit('translation_status', {
            'task_id': task_id,
            'status': 'failed',
            'message': str(e)
        })

@app.route('/')
def index():
    supported_languages = translator.get_supported_languages()
    return render_template('index_simple.html', languages=supported_languages)

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
            task_id = str(uuid.uuid4())
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{task_id}_{filename}")
            file.save(filepath)

            active_translations[task_id] = {
                'status': 'queued',
                'original_file': filename
            }

            # Start background thread (async_mode='threading' makes this safe)
            thread = threading.Thread(
                target=translate_pdf_background,
                args=(filepath, source_lang, task_id, filename)
            )
            thread.daemon = False  # Don't use daemon mode to ensure SocketIO works
            thread.start()

            task_ids.append(task_id)

    return jsonify({'task_ids': task_ids, 'message': f'Started processing {len(task_ids)} file(s)'})

@app.route('/batch')
def batch_translate():
    supported_languages = translator.get_supported_languages()
    return render_template('batch_simple.html', languages=supported_languages)

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

