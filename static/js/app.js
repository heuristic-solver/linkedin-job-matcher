// ===== GLOBAL VARIABLES =====
let currentSessionId = null;
let currentResumeData = null;
let progressInterval = null;

// ===== DOM ELEMENTS =====
const elements = {
    uploadArea: document.getElementById('upload-area'),
    resumeFile: document.getElementById('resume-file'),
    uploadBtn: document.getElementById('upload-btn'),
    progressSection: document.getElementById('progress-section'),
    progressFill: document.getElementById('progress-fill'),
    progressTitle: document.getElementById('progress-title'),
    progressDescription: document.getElementById('progress-description'),
    jobSearchSection: document.getElementById('job-search-section'),
    resultsSection: document.getElementById('results-section'),
    resultsGrid: document.getElementById('results-grid'),
    jobQuery: document.getElementById('job-query'),
    location: document.getElementById('location'),
    searchBtn: document.getElementById('search-btn'),
    loadingOverlay: document.getElementById('loading-overlay'),
    successModal: document.getElementById('success-modal'),
    errorModal: document.getElementById('error-modal'),
    successMessage: document.getElementById('success-message'),
    errorMessage: document.getElementById('error-message'),
    closeSuccess: document.getElementById('close-success'),
    closeError: document.getElementById('close-error'),
    loadingText: document.getElementById('loading-text')
};

// Progress steps
const progressSteps = ['step-upload', 'step-analyze', 'step-search', 'step-match'];

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    initializeNavigation();
    initializeFileUpload();
});

// ===== EVENT LISTENERS =====
function initializeEventListeners() {
    // File upload events
    elements.uploadArea.addEventListener('click', () => elements.resumeFile.click());
    elements.uploadArea.addEventListener('dragover', handleDragOver);
    elements.uploadArea.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea.addEventListener('drop', handleDrop);
    elements.resumeFile.addEventListener('change', handleFileSelect);
    elements.uploadBtn.addEventListener('click', handleResumeUpload);

    // Search events
    elements.searchBtn.addEventListener('click', handleJobSearch);

    // Modal events
    elements.closeSuccess.addEventListener('click', () => hideModal('success-modal'));
    elements.closeError.addEventListener('click', () => hideModal('error-modal'));

    // Filter events
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', handleFilterChange);
    });

    // Sort events
    document.getElementById('sort-select')?.addEventListener('change', handleSortChange);

    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

// ===== NAVIGATION =====
function initializeNavigation() {
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
        });
    }

    // Smooth scrolling for nav links
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

// ===== FILE UPLOAD HANDLING =====
function initializeFileUpload() {
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        elements.uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDragOver(e) {
    elements.uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    elements.uploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    elements.uploadArea.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelection(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFileSelection(file);
    }
}

function handleFileSelection(file) {
    // Validate file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                         'image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp'];
    
    if (!allowedTypes.includes(file.type)) {
        showError('Please select a PDF, DOCX, or image file.');
        return;
    }

    // Validate file size (16MB max)
    if (file.size > 16 * 1024 * 1024) {
        showError('File size must be less than 16MB.');
        return;
    }

    // Update UI
    elements.uploadArea.classList.add('file-selected');
    elements.uploadArea.querySelector('.upload-title').textContent = file.name;
    elements.uploadArea.querySelector('.upload-subtitle').textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;
    elements.uploadBtn.disabled = false;

    // Update icon
    const icon = elements.uploadArea.querySelector('.upload-icon i');
    icon.className = 'fas fa-check-circle';
    icon.style.color = '#34C759';
}

// ===== API CALLS =====
async function handleResumeUpload() {
    const file = elements.resumeFile.files[0];
    if (!file) {
        showError('Please select a file first.');
        return;
    }

    showLoading('Uploading your resume...');

    try {
        const formData = new FormData();
        formData.append('resume', file);

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            currentSessionId = data.session_id;
            hideLoading();
            showSuccess('Resume uploaded successfully!');
            
            // Start analysis
            setTimeout(() => {
                hideModal('success-modal');
                startResumeAnalysis();
            }, 1500);
        } else {
            hideLoading();
            showError(data.error || 'Upload failed. Please try again.');
        }
    } catch (error) {
        hideLoading();
        showError('Network error. Please check your connection and try again.');
    }
}

async function startResumeAnalysis() {
    // Show progress section
    showProgressSection();
    updateProgressStep('analyzing', 10, 'Analyzing your resume with AI...');

    try {
        const response = await fetch(`/analyze/${currentSessionId}`);
        const data = await response.json();

        if (data.success) {
            currentResumeData = data.resume_data;
            updateProgressStep('complete', 100, 'Resume analysis complete!');
            
            setTimeout(() => {
                showJobSearchSection();
            }, 1500);
        } else {
            updateProgressStep('error', 0, data.error || 'Analysis failed.');
        }
    } catch (error) {
        updateProgressStep('error', 0, 'Network error during analysis.');
    }
}

async function handleJobSearch() {
    if (!currentSessionId || !currentResumeData) {
        showError('Please upload and analyze your resume first.');
        return;
    }

    const jobQuery = elements.jobQuery.value.trim();
    const location = elements.location.value.trim();

    if (!jobQuery) {
        showError('Please enter a job query.');
        return;
    }

    // Show progress section again
    showProgressSection();
    updateProgressStep('searching', 20, 'Searching for matching jobs...');

    try {
        const response = await fetch('/search-jobs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                job_query: jobQuery,
                location: location,
                resume_data: currentResumeData
            })
        });

        const data = await response.json();

        if (data.success) {
            // Start polling for progress
            startProgressPolling();
        } else {
            updateProgressStep('error', 0, data.error || 'Job search failed.');
        }
    } catch (error) {
        updateProgressStep('error', 0, 'Network error during job search.');
    }
}

function startProgressPolling() {
    progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/progress/${currentSessionId}`);
            const progress = await response.json();

            updateProgressFromServer(progress);

            if (progress.step === 'complete' && progress.results) {
                clearInterval(progressInterval);
                setTimeout(() => {
                    displayJobResults(progress.results);
                }, 1000);
            } else if (progress.step === 'error') {
                clearInterval(progressInterval);
                updateProgressStep('error', 0, progress.message);
            }
        } catch (error) {
            clearInterval(progressInterval);
            updateProgressStep('error', 0, 'Error fetching progress.');
        }
    }, 2000);
}

function updateProgressFromServer(progress) {
    const stepMap = {
        'extracting': { step: 'analyzing', progress: 20, message: progress.message },
        'analyzing': { step: 'analyzing', progress: 40, message: progress.message },
        'searching': { step: 'searching', progress: 60, message: progress.message },
        'matching': { step: 'matching', progress: 80, message: progress.message },
        'complete': { step: 'complete', progress: 100, message: progress.message }
    };

    const mappedProgress = stepMap[progress.step] || progress;
    updateProgressStep(mappedProgress.step, mappedProgress.progress, mappedProgress.message);
}

// ===== UI UPDATES =====
function showProgressSection() {
    elements.progressSection.classList.remove('hidden');
    
    // Only auto-scroll if the user is near the top of the page or the upload section
    const scrollPosition = window.pageYOffset;
    const heroHeight = document.querySelector('.hero-section')?.offsetHeight || 800;
    
    if (scrollPosition < heroHeight * 1.2) {
        elements.progressSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    // Reset all steps
    progressSteps.forEach(stepId => {
        document.getElementById(stepId)?.classList.remove('active', 'completed');
    });
}

function showJobSearchSection() {
    elements.progressSection.classList.add('hidden');
    elements.jobSearchSection.classList.remove('hidden');
    
    // Only scroll if the progress section was visible to the user
    const progressSectionRect = elements.progressSection.getBoundingClientRect();
    const wasProgressVisible = progressSectionRect.top < window.innerHeight && progressSectionRect.bottom > -100;
    
    if (wasProgressVisible) {
        elements.jobSearchSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function updateProgressStep(step, progress, message) {
    elements.progressFill.style.width = `${progress}%`;
    elements.progressTitle.textContent = getProgressTitle(step);
    elements.progressDescription.textContent = message;

    // Update step indicators
    const stepMap = {
        'analyzing': 1,
        'searching': 2,
        'matching': 3,
        'complete': 4
    };

    const currentStepIndex = stepMap[step] || 0;
    
    progressSteps.forEach((stepId, index) => {
        const stepElement = document.getElementById(stepId);
        if (!stepElement) return;

        stepElement.classList.remove('active', 'completed');
        
        if (index < currentStepIndex - 1) {
            stepElement.classList.add('completed');
        } else if (index === currentStepIndex - 1) {
            stepElement.classList.add('active');
        }
    });
}

function getProgressTitle(step) {
    const titles = {
        'analyzing': 'Analyzing Your Resume',
        'searching': 'Searching for Jobs',
        'matching': 'Matching Jobs to Your Profile',
        'complete': 'Analysis Complete!'
    };
    return titles[step] || 'Processing...';
}

function displayJobResults(jobs) {
    elements.progressSection.classList.add('hidden');
    elements.jobSearchSection.classList.add('hidden');
    elements.resultsSection.classList.remove('hidden');
    
    // Only scroll to results if user hasn't manually scrolled away from the progress section
    const progressSectionRect = elements.progressSection.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const isProgressSectionVisible = progressSectionRect.top < viewportHeight && progressSectionRect.bottom > 0;
    
    if (isProgressSectionVisible) {
        elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    renderJobCards(jobs);
    
    // Ensure all jobs are displayed by default
    filterJobs('all');
    
    // Make sure "All Jobs" filter button is active
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.filter === 'all') {
            btn.classList.add('active');
        }
    });
}

function renderJobCards(jobs) {
    elements.resultsGrid.innerHTML = '';

    // Display all jobs without filtering
    jobs.forEach(job => {
        const jobCard = createJobCard(job);
        elements.resultsGrid.appendChild(jobCard);
    });

    // Add stagger animation
    const cards = elements.resultsGrid.querySelectorAll('.job-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease-out';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';
    card.dataset.score = job.score || 0;
    card.dataset.company = job.company || '';
    card.dataset.date = job.published || '';

    const score = parseFloat(job.score) || 0;
    const scoreClass = score >= 80 ? 'high' : score >= 60 ? 'medium' : 'low';
    
    card.innerHTML = `
        <div class="job-header">
            <div>
                <div class="job-title">${escapeHtml(job.title || 'N/A')}</div>
                <div class="job-company">${escapeHtml(job.company || 'N/A')}</div>
            </div>
            <div class="match-score ${scoreClass}">${score}% Match</div>
        </div>
        
        <div class="job-description">
            ${escapeHtml(job.description || 'No description available').substring(0, 200)}...
        </div>
        
        <div class="job-meta">
            <span><i class="fas fa-building"></i> ${escapeHtml(job.site || 'N/A')}</span>
            <span><i class="fas fa-calendar"></i> ${formatDate(job.published)}</span>
        </div>
        
        ${job.explanation ? `
            <div class="job-recommendations">
                <h4><i class="fas fa-lightbulb"></i> AI Insights</h4>
                <p style="font-size: var(--font-size-xs); margin-bottom: var(--space-2);">
                    ${escapeHtml(job.explanation).substring(0, 200)}...
                </p>
                ${job.recommended_improvements ? `
                    <div style="margin-top: var(--space-3);">
                        <strong style="font-size: var(--font-size-xs);">Recommendations:</strong>
                        ${Array.isArray(job.recommended_improvements) ? `
                            <ul style="margin-top: var(--space-1);">
                                ${job.recommended_improvements.slice(0, 3).map(improvement => 
                                    `<li>${escapeHtml(improvement)}</li>`
                                ).join('')}
                            </ul>
                        ` : `
                            <p style="font-size: var(--font-size-xs); margin-top: var(--space-1);">
                                ${escapeHtml(job.recommended_improvements).substring(0, 150)}...
                            </p>
                        `}
                    </div>
                ` : ''}
            </div>
        ` : job.error ? `
            <div class="job-recommendations">
                <h4><i class="fas fa-exclamation-triangle"></i> Analysis Issue</h4>
                <p style="font-size: var(--font-size-xs); color: var(--error-color);">
                    ${escapeHtml(job.error || 'Unable to analyze this job at the moment.')}
                </p>
            </div>
        ` : ''}
    `;

    // Add click handler to open job link
    card.addEventListener('click', () => {
        if (job.link && job.link !== 'N/A') {
            window.open(job.link, '_blank');
        }
    });

    return card;
}

// ===== FILTERING & SORTING =====
function handleFilterChange(e) {
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');

    const filter = e.target.dataset.filter;
    filterJobs(filter);
}

function filterJobs(filter) {
    const jobCards = document.querySelectorAll('.job-card');
    
    jobCards.forEach(card => {
        const score = parseFloat(card.dataset.score) || 0;
        let show = true;

        switch (filter) {
            case 'high':
                show = score >= 80;
                break;
            case 'medium':
                show = score >= 60 && score < 80;
                break;
            case 'low':
                show = score < 60;
                break;
            case 'all':
            default:
                show = true; // Show all jobs by default
        }

        if (show) {
            card.style.display = 'block';
            // Re-animate the card
            card.style.opacity = '0';
            card.style.transform = 'translateY(10px)';
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 50);
        } else {
            card.style.display = 'none';
        }
    });
}

function handleSortChange(e) {
    const sortBy = e.target.value;
    const jobCards = Array.from(document.querySelectorAll('.job-card'));
    
    jobCards.sort((a, b) => {
        switch (sortBy) {
            case 'score':
                return parseFloat(b.dataset.score) - parseFloat(a.dataset.score);
            case 'date':
                return new Date(b.dataset.date) - new Date(a.dataset.date);
            case 'company':
                return a.dataset.company.localeCompare(b.dataset.company);
            default:
                return 0;
        }
    });

    // Re-append sorted cards
    const container = elements.resultsGrid;
    container.innerHTML = '';
    jobCards.forEach(card => container.appendChild(card));
}

// ===== UTILITY FUNCTIONS =====
function showLoading(text = 'Loading...') {
    elements.loadingText.textContent = text;
    elements.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    elements.loadingOverlay.classList.add('hidden');
}

function showSuccess(message) {
    elements.successMessage.textContent = message;
    elements.successModal.classList.remove('hidden');
}

function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorModal.classList.remove('hidden');
}

function hideModal(modalId) {
    document.getElementById(modalId)?.classList.add('hidden');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch {
        return dateString;
    }
}

function handleKeyboardShortcuts(e) {
    // ESC to close modals
    if (e.key === 'Escape') {
        hideModal('success-modal');
        hideModal('error-modal');
    }
    
    // Enter to trigger upload when file is selected
    if (e.key === 'Enter' && !elements.uploadBtn.disabled) {
        handleResumeUpload();
    }
}

// ===== PERFORMANCE OPTIMIZATIONS =====
// Debounce function for search input
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function for scroll events
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Intersection Observer for animations
const observeElements = () => {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.job-card, .upload-card, .progress-card').forEach(el => {
        observer.observe(el);
    });
};

// Initialize observers when DOM is ready
document.addEventListener('DOMContentLoaded', observeElements);
