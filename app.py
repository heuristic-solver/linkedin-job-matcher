from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
import json
import uuid
from linkedin_job_matcher import extract_text, analyze_resume, get_jobs_from_rss, match_jobs_to_resume
import threading
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Store job matching progress
progress_store = {}

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png', 'tiff', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Landing page with clean, minimalist design"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    """Handle resume file upload"""
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not supported. Please upload PDF, DOCX, or image files.'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        # Save file
        filename = secure_filename(file.filename)
        filename = f"{session_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'filename': filename,
            'message': 'Resume uploaded successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze/<session_id>')
def analyze_resume_route(session_id):
    """Analyze uploaded resume"""
    try:
        # Initialize progress
        progress_store[session_id] = {'step': 'extracting', 'progress': 10, 'message': 'Extracting text from resume...'}
        
        # Find uploaded file
        files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith(session_id)]
        if not files:
            return jsonify({'error': 'Resume file not found'}), 404
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], files[0])
        
        # Extract text
        progress_store[session_id] = {'step': 'extracting', 'progress': 30, 'message': 'Extracting text from resume...'}
        resume_text = extract_text(filepath)
        
        if not resume_text.strip():
            return jsonify({'error': 'No text could be extracted from the resume'}), 400
        
        # Analyze resume
        progress_store[session_id] = {'step': 'analyzing', 'progress': 60, 'message': 'Analyzing resume with AI...'}
        resume_data = analyze_resume(resume_text)
        
        progress_store[session_id] = {'step': 'complete', 'progress': 100, 'message': 'Resume analysis complete!'}
        
        return jsonify({
            'success': True,
            'resume_data': resume_data,
            'message': 'Resume analyzed successfully'
        })
        
    except Exception as e:
        progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': f'Error: {str(e)}'}
        return jsonify({'error': str(e)}), 500

@app.route('/search-jobs', methods=['POST'])
def search_jobs():
    """Search for jobs and match to resume"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        job_query = data.get('job_query', 'AI Engineer')
        location = data.get('location', 'India')
        resume_data = data.get('resume_data', {})
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        # Start background job matching
        def match_jobs_background():
            try:
                # Search for jobs
                progress_store[session_id] = {'step': 'searching', 'progress': 20, 'message': f'Searching for {job_query} positions...'}
                jobs = get_jobs_from_rss(job_query, location)
                
                if not jobs:
                    progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': 'No jobs found. Try a different query.'}
                    return
                
                # Match jobs to resume
                progress_store[session_id] = {'step': 'matching', 'progress': 50, 'message': 'Matching jobs to your resume...'}
                matched_jobs = match_jobs_to_resume(jobs, resume_data)
                
                # Store results
                progress_store[session_id] = {
                    'step': 'complete',
                    'progress': 100,
                    'message': 'Job matching complete!',
                    'results': matched_jobs
                }
                
            except Exception as e:
                progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': f'Error: {str(e)}'}
        
        # Start background thread
        threading.Thread(target=match_jobs_background, daemon=True).start()
        
        return jsonify({
            'success': True,
            'message': 'Job matching started',
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<session_id>')
def get_progress(session_id):
    """Get progress of job matching"""
    progress = progress_store.get(session_id, {'step': 'not-started', 'progress': 0, 'message': 'Not started'})
    return jsonify(progress)

@app.route('/results/<session_id>')
def get_results(session_id):
    """Get job matching results"""
    progress = progress_store.get(session_id, {})
    if progress.get('step') == 'complete' and 'results' in progress:
        return jsonify({
            'success': True,
            'results': progress['results']
        })
    else:
        return jsonify({'error': 'Results not ready yet'}), 404

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
