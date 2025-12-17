from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
import json
import uuid
from linkedin_job_matcher import extract_text, analyze_resume, get_jobs_from_rss, match_jobs_to_resume
from matching.analytics import calculate_resume_strength_score, analyze_skills_gap, extract_key_metrics
from intelligence.market_intel import get_salary_insights, get_market_demand_trends, get_competition_analysis, get_industry_insights
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
            return jsonify({'error': 'File type not supported. Please upload PDF, DOCX, or image files (JPG, PNG, TIFF, BMP).'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'error': f'File size exceeds maximum of {app.config["MAX_CONTENT_LENGTH"] / (1024*1024):.1f}MB'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        # Save file
        filename = secure_filename(file.filename)
        if not filename:
            filename = f"resume_{session_id[:8]}"
        filename = f"{session_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
        except Exception as e:
            return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
        
        # Verify file was saved
        if not os.path.exists(filepath):
            return jsonify({'error': 'File upload failed'}), 500
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'filename': filename,
            'message': 'Resume uploaded successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload error: {str(e)}'}), 500

@app.route('/analyze/<session_id>')
def analyze_resume_route(session_id):
    """Analyze uploaded resume"""
    try:
        # Initialize progress
        progress_store[session_id] = {'step': 'extracting', 'progress': 10, 'message': 'Extracting text from resume...'}
        
        # Find uploaded file
        try:
            files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith(session_id)]
            if not files:
                progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': 'Resume file not found. Please upload again.'}
            return jsonify({'error': 'Resume file not found'}), 404
        except Exception as e:
            progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': f'Error accessing upload folder: {str(e)}'}
            return jsonify({'error': 'Error accessing upload folder'}), 500
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], files[0])
        
        # Extract text
        progress_store[session_id] = {'step': 'extracting', 'progress': 30, 'message': 'Extracting text from resume...'}
        try:
            resume_text = extract_text(filepath)
        except Exception as e:
            progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': f'Error extracting text: {str(e)}'}
            return jsonify({'error': f'Failed to extract text from resume: {str(e)}'}), 500
        
        if not resume_text or not resume_text.strip():
            progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': 'No text could be extracted from the resume. The file might be corrupted or unsupported.'}
            return jsonify({'error': 'No text could be extracted from the resume. Please ensure it\'s a valid PDF, DOCX, or image file.'}), 400
        
        # Analyze resume
        progress_store[session_id] = {'step': 'analyzing', 'progress': 60, 'message': 'Analyzing resume...'}
        try:
            resume_data = analyze_resume(resume_text)
            if not resume_data:
                progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': 'Failed to analyze resume. Please try again.'}
                return jsonify({'error': 'Resume analysis failed'}), 500
            
            # Check if it's a quota error but still has fallback data
            if 'quota_error' in resume_data and resume_data.get('quota_error'):
                # Still return the data but with warning
                progress_store[session_id] = {'step': 'complete', 'progress': 100, 'message': 'Resume analyzed (using fallback mode - API quota exceeded)', 'resume_data': resume_data}
                return jsonify({
                    'success': True,
                    'resume_data': resume_data,
                    'warning': 'API quota exceeded. Resume analyzed using fallback mode.',
                    'message': 'Resume analyzed successfully (fallback mode)'
                })
            
            # Check if fallback mode was used
            if 'quota_warning' in resume_data:
                progress_store[session_id] = {'step': 'complete', 'progress': 100, 'message': 'Resume analyzed (fallback mode)', 'resume_data': resume_data}
                return jsonify({
                    'success': True,
                    'resume_data': resume_data,
                    'warning': resume_data.get('quota_warning'),
                    'message': 'Resume analyzed successfully'
                })
            
        except Exception as e:
            # Even if there's an exception, try fallback parsing
            print(f"Exception in resume analysis: {e}")
            try:
                from linkedin_job_matcher import parse_resume_fallback
                resume_data = parse_resume_fallback(resume_text)
                progress_store[session_id] = {'step': 'complete', 'progress': 100, 'message': 'Resume analyzed (fallback mode)', 'resume_data': resume_data}
                return jsonify({
                    'success': True,
                    'resume_data': resume_data,
                    'warning': 'Resume analyzed using fallback mode due to API issues.',
                    'message': 'Resume analyzed successfully'
                })
            except:
                progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': f'Analysis error: {str(e)}'}
                return jsonify({'error': f'Resume analysis failed: {str(e)}'}), 500
        
        progress_store[session_id] = {'step': 'complete', 'progress': 100, 'message': 'Resume analysis complete!', 'resume_data': resume_data}
        
        return jsonify({
            'success': True,
            'resume_data': resume_data,
            'message': 'Resume analyzed successfully'
        })
        
    except Exception as e:
        progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': f'Unexpected error: {str(e)}'}
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/search-jobs', methods=['POST'])
def search_jobs():
    """Search for jobs and match to resume"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        session_id = data.get('session_id')
        job_query = data.get('job_query', 'AI Engineer')
        location = data.get('location', 'India')
        resume_data = data.get('resume_data', {})
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        if not resume_data:
            return jsonify({'error': 'Resume data required. Please analyze your resume first.'}), 400
        
        # Start background job matching
        def match_jobs_background():
            try:
                # Search for jobs
                progress_store[session_id] = {'step': 'searching', 'progress': 20, 'message': f'Searching for {job_query} positions in {location}...'}
                try:
                    jobs = get_jobs_from_rss(job_query, location)
                except Exception as e:
                    progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': f'Error searching jobs: {str(e)}'}
                    return
                
                if not jobs or len(jobs) == 0:
                    progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': 'No jobs found. Try a different query or location.'}
                    return
                
                # Match jobs to resume
                progress_store[session_id] = {'step': 'matching', 'progress': 50, 'message': f'Matching {len(jobs)} jobs to your resume...'}
                try:
                    matched_jobs = match_jobs_to_resume(jobs, resume_data, job_query)
                except Exception as e:
                    progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': f'Error matching jobs: {str(e)}'}
                    return
                
                if not matched_jobs or len(matched_jobs) == 0:
                    progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': 'No matches found. Please try again.'}
                    return
                
                # Store results
                progress_store[session_id] = {
                    'step': 'complete',
                    'progress': 100,
                    'message': f'Found {len(matched_jobs)} matching jobs!',
                    'results': matched_jobs
                }
                
            except Exception as e:
                progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': f'Unexpected error: {str(e)}'}
        
        # Start background thread
        thread = threading.Thread(target=match_jobs_background, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Job matching started',
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Request error: {str(e)}'}), 500

@app.route('/progress/<session_id>')
def get_progress(session_id):
    """Get progress of job matching"""
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 400
    
    progress = progress_store.get(session_id, {'step': 'not-started', 'progress': 0, 'message': 'Not started'})
    
    # Ensure response always has required fields
    if 'step' not in progress:
        progress['step'] = 'not-started'
    if 'progress' not in progress:
        progress['progress'] = 0
    if 'message' not in progress:
        progress['message'] = 'Not started'
    
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

@app.route('/analytics/<session_id>', methods=['POST'])
def get_resume_analytics(session_id):
    """Get advanced resume analytics"""
    try:
        data = request.get_json()
        resume_data = data.get('resume_data', {})
        
        if not resume_data:
            return jsonify({'error': 'Resume data required'}), 400
        
        # Calculate resume strength
        strength_analysis = calculate_resume_strength_score(resume_data)
        
        # Extract key metrics
        key_metrics = extract_key_metrics(resume_data)
        
        # Combine analytics
        analytics = {
            'strength_analysis': strength_analysis,
            'key_metrics': key_metrics,
            'resume_data': resume_data,
            'timestamp': time.time()
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/ats-score/<session_id>', methods=['POST'])
def get_ats_score(session_id):
    """Return ATS-friendly score for a previously analyzed resume"""
    try:
        data = request.get_json() or {}
        resume_data = data.get('resume_data', {})
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        if not resume_data:
            # Try stored resume data from prior analysis
            stored = progress_store.get(session_id, {})
            resume_data = stored.get('resume_data', {})
        
        if not resume_data:
            return jsonify({'error': 'Resume data not found for this session. Please upload/analyze first.'}), 400
        
        strength = calculate_resume_strength_score(resume_data)
        ats_score = min(100, max(0, int(strength['scores'].get('overall', 0))))
        
        return jsonify({
            'success': True,
            'ats_score': ats_score,
            'scores': strength['scores'],
            'insights': strength['insights']
        })
    except Exception as e:
        return jsonify({'error': f'ATS calculation error: {str(e)}'}), 500

@app.route('/skills-gap', methods=['POST'])
def analyze_skills_gap_route():
    """Analyze skills gap between resume and job"""
    try:
        data = request.get_json()
        resume_data = data.get('resume_data', {})
        job_description = data.get('job_description', '')
        
        if not resume_data or not job_description:
            return jsonify({'error': 'Resume data and job description required'}), 400
        
        gap_analysis = analyze_skills_gap(resume_data, job_description)
        
        return jsonify({
            'success': True,
            'gap_analysis': gap_analysis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search-jobs-advanced', methods=['POST'])
def search_jobs_advanced():
    """Advanced job search with filters"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        job_query = data.get('job_query', 'AI Engineer')
        location = data.get('location', 'India')
        resume_data = data.get('resume_data', {})
        
        # Advanced filters
        salary_min = data.get('salary_min')
        salary_max = data.get('salary_max')
        job_type = data.get('job_type')  # 'full-time', 'part-time', 'contract', 'remote', 'all'
        experience_level = data.get('experience_level')  # 'entry', 'mid', 'senior', 'all'
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        # Start background job matching with filters
        def match_jobs_background_advanced():
            try:
                print(f"[{session_id}] Starting job search for: {job_query} in {location}")
                progress_store[session_id] = {'step': 'searching', 'progress': 20, 'message': f'Searching for {job_query} positions...'}
                
                # Fetch jobs
                print(f"[{session_id}] Fetching jobs from RSS feeds...")
                jobs = get_jobs_from_rss(job_query, location)
                print(f"[{session_id}] Found {len(jobs)} jobs")
                
                if not jobs or len(jobs) == 0:
                    print(f"[{session_id}] No jobs found")
                    progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': 'No jobs found. Try a different query or location.'}
                    return
                
                # Apply filters
                print(f"[{session_id}] Applying filters (type: {job_type}, level: {experience_level})...")
                filtered_jobs = _apply_job_filters(jobs, salary_min, salary_max, job_type, experience_level)
                print(f"[{session_id}] {len(filtered_jobs)} jobs after filtering")
                
                if not filtered_jobs or len(filtered_jobs) == 0:
                    print(f"[{session_id}] No jobs after filtering")
                    progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': 'No jobs match your filters. Try adjusting your criteria.'}
                    return
                
                # Match jobs to resume
                print(f"[{session_id}] Matching {len(filtered_jobs)} jobs to resume...")
                progress_store[session_id] = {'step': 'matching', 'progress': 50, 'message': f'Matching {len(filtered_jobs)} jobs to your resume...'}
                
                matched_jobs = match_jobs_to_resume(filtered_jobs, resume_data, job_query)
                print(f"[{session_id}] Matched {len(matched_jobs)} jobs successfully")
                
                if not matched_jobs or len(matched_jobs) == 0:
                    print(f"[{session_id}] No matched jobs")
                    progress_store[session_id] = {'step': 'error', 'progress': 0, 'message': 'Job matching completed but no results. Please try again.'}
                    return
                
                # Store results
                progress_store[session_id] = {
                    'step': 'complete',
                    'progress': 100,
                    'message': f'Found {len(matched_jobs)} matching jobs!',
                    'results': matched_jobs
                }
                print(f"[{session_id}] Job search complete: {len(matched_jobs)} results")
                
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"[{session_id}] ERROR in background job matching:")
                print(error_trace)
                progress_store[session_id] = {
                    'step': 'error', 
                    'progress': 0, 
                    'message': f'Error: {str(e)}',
                    'error_details': str(e)
                }
        
        thread = threading.Thread(target=match_jobs_background_advanced, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Advanced job search started',
            'session_id': session_id
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in search_jobs_advanced route: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500

def _apply_job_filters(jobs, salary_min, salary_max, job_type, experience_level):
    """Apply filters to job list"""
    filtered = jobs.copy()
    
    # Filter by job type (if job descriptions contain keywords)
    if job_type and job_type != 'all':
        job_type_keywords = {
            'full-time': ['full-time', 'full time', 'permanent'],
            'part-time': ['part-time', 'part time'],
            'contract': ['contract', 'contractor', 'freelance'],
            'remote': ['remote', 'work from home', 'wfh', 'distributed']
        }
        
        keywords = job_type_keywords.get(job_type.lower(), [])
        if keywords:
            filtered = [j for j in filtered if any(kw in j.get('description', '').lower() or kw in j.get('title', '').lower() for kw in keywords)]
    
    # Filter by experience level
    if experience_level and experience_level != 'all':
        exp_keywords = {
            'entry': ['junior', 'entry', 'graduate', 'intern', 'associate'],
            'mid': ['mid-level', 'mid level', 'experienced'],
            'senior': ['senior', 'lead', 'principal', 'architect', 'manager']
        }
        
        keywords = exp_keywords.get(experience_level.lower(), [])
        if keywords:
            filtered = [j for j in filtered if any(kw in j.get('title', '').lower() or kw in j.get('description', '').lower() for kw in keywords)]
    
    # Note: Salary filtering would require extracting salary from job descriptions
    # This is a simplified version - in production, you'd parse salary ranges
    
    return filtered

@app.route('/market-intelligence', methods=['POST'])
def get_market_intelligence():
    """Get market intelligence for job search"""
    try:
        data = request.get_json()
        job_title = data.get('job_title', '')
        location = data.get('location', 'India')
        experience_level = data.get('experience_level', 'mid')
        skills = data.get('skills', [])
        
        if not job_title:
            return jsonify({'error': 'Job title required'}), 400
        
        # Get all market intelligence
        salary_insights = get_salary_insights(job_title, location, experience_level)
        demand_trends = get_market_demand_trends(job_title, skills)
        competition = get_competition_analysis(job_title, location)
        industry = get_industry_insights(job_title)
        
        return jsonify({
            'success': True,
            'market_intelligence': {
                'salary_insights': salary_insights,
                'demand_trends': demand_trends,
                'competition': competition,
                'industry': industry
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use port 5003 to avoid conflicts with other services
    # You can override with PORT environment variable
    port = int(os.environ.get('PORT', 5003))
    print(f"Starting server on http://0.0.0.0:{port}")
    print(f"Access the application at: http://localhost:{port}")
    app.run(debug=False, host='0.0.0.0', port=port)
