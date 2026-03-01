// ===== GLOBAL VARIABLES =====
let currentSessionId = null;
let currentResumeData = null;
let progressInterval = null;
let parsedCardVisible = false;
let latestParsedResume = null;

let selectedStyle = 'professional';
let currentResumeHTML = null;
let currentJobForResume = null;
let availableStyles = {};

// ===== DOM ELEMENTS =====
const elements = {
    uploadArea: document.getElementById('upload-area'),
    resumeFile: document.getElementById('resume-file'),
    uploadBtn: document.getElementById('upload-btn'),
    progressSection: document.getElementById('progress-section'),
    progressFill: document.getElementById('progress-fill'),
    progressTitle: document.getElementById('progress-title'),
    progressDescription: document.getElementById('progress-description'),
    analyticsSection: document.getElementById('analytics-section'),
    analyticsGrid: document.getElementById('analytics-grid'),
    jobSearchSection: document.getElementById('job-search-section'),
    marketIntelSection: document.getElementById('market-intel-section'),
    intelGrid: document.getElementById('intel-grid'),
    resultsSection: document.getElementById('results-section'),
    resultsGrid: document.getElementById('results-grid'),
    jobQuery: document.getElementById('job-query'),
    location: document.getElementById('location'),
    jobType: document.getElementById('job-type'),
    experienceLevel: document.getElementById('experience-level'),
    searchBtn: document.getElementById('search-btn'),
    advancedSearchBtn: document.getElementById('advanced-search-btn'),
    atsCheckBtn: document.getElementById('ats-check-btn'),
    platformSelect: document.getElementById('platform-select'),
    parsedToggleBtn: document.getElementById('parsed-toggle-btn'),
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

    // Search events - ensure elements exist before adding listeners
    if (elements.searchBtn) {
        elements.searchBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Find Matching Jobs button clicked');
            handleJobSearch();
        });
    } else {
        console.error('Search button not found!');
        // Try to find it again after a delay
        setTimeout(() => {
            const searchBtn = document.getElementById('search-btn');
            if (searchBtn) {
                searchBtn.addEventListener('click', handleJobSearch);
                console.log('Search button found and listener attached');
            }
        }, 1000);
    }
    
    if (elements.advancedSearchBtn) {
        elements.advancedSearchBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            handleMarketIntelligence();
        });
    }

    if (elements.atsCheckBtn) {
        elements.atsCheckBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            await handleAtsCheck();
        });
    }
    if (elements.parsedToggleBtn) {
        elements.parsedToggleBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            parsedCardVisible = !parsedCardVisible;
            renderParsedResumeCard();
        });
    }

    // Modal events
    elements.closeSuccess.addEventListener('click', () => hideModal('success-modal'));
    elements.closeError.addEventListener('click', () => hideModal('error-modal'));

    // Filter events
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', handleFilterChange);
    });

    // Sort events
    document.getElementById('sort-select')?.addEventListener('change', handleSortChange);
    // Platform filter
    elements.platformSelect?.addEventListener('change', () => filterJobs(currentScoreFilter));

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
            hideProgressSection();
            showError(data.error || 'Upload failed. Please try again.');
        }
    } catch (error) {
        hideLoading();
        hideProgressSection();
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
            
            // Fetch analytics
            setTimeout(() => {
                fetchResumeAnalytics(data.resume_data);
            }, 500);
            
            setTimeout(() => {
                showJobSearchSection();
            }, 1500);
        } else {
            updateProgressStep('error', 0, data.error || 'Analysis failed.');
            hideProgressSection();
            showError(data.error || 'Analysis failed. Please re-upload your resume.');
        }
    } catch (error) {
        updateProgressStep('error', 0, 'Network error during analysis.');
        hideProgressSection();
        showError('Network error during analysis. Please try again.');
    }
}

async function handleJobSearch() {
    console.log('Job search button clicked');
    console.log('Session ID:', currentSessionId);
    console.log('Resume Data:', currentResumeData ? 'Present' : 'Missing');
    
    // Check if resume has been uploaded and analyzed
    if (!currentSessionId || !currentResumeData) {
        showError('Please upload and analyze your resume first. Click "Upload" above to get started.');
        // Scroll to upload section
        document.querySelector('.hero-section')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
    }

    const jobQuery = elements.jobQuery?.value?.trim() || '';
    const location = elements.location?.value?.trim() || 'India';
    const jobType = elements.jobType?.value || 'all';
    const experienceLevel = elements.experienceLevel?.value || 'all';

    if (!jobQuery) {
        showError('Please enter a job query (e.g., "AI Engineer", "Data Scientist").');
        elements.jobQuery?.focus();
        return;
    }

    console.log('Starting job search:', { jobQuery, location, jobType, experienceLevel });

    // Immediately show loading state on button
    const searchButton = elements.searchBtn;
    if (searchButton) {
        const originalText = searchButton.innerHTML;
        searchButton.disabled = true;
        searchButton.style.opacity = '0.7';
        searchButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        
        // Store original content to restore later
        searchButton.dataset.originalHtml = originalText;
    }

    // Show progress section immediately and scroll to it
    showProgressSection();
    updateProgressStep('searching', 10, 'Initializing job search...');
    
    // Scroll to progress section for better visibility
    setTimeout(() => {
        elements.progressSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);

    try {
        console.log('Sending job search request...', {
            session_id: currentSessionId,
            job_query: jobQuery,
            location: location,
            job_type: jobType,
            experience_level: experienceLevel,
            has_resume_data: !!currentResumeData
        });

        const response = await fetch('/search-jobs-advanced', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                job_query: jobQuery,
                location: location,
                job_type: jobType,
                experience_level: experienceLevel,
                resume_data: currentResumeData
            })
        });

        console.log('Response status:', response.status, response.statusText);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Server error response:', errorText);
            throw new Error(`Server error: ${response.status} ${response.statusText}. ${errorText}`);
        }

        const data = await response.json();
        console.log('Job search response:', data);

        if (data.success) {
            console.log('Job search started successfully, starting progress polling...');
            // Clear any existing interval
            if (progressInterval) {
                clearInterval(progressInterval);
            }
            // Start polling for progress
            startProgressPolling();
        } else {
            const errorMsg = data.error || 'Job search failed. Please try again.';
            console.error('Job search failed:', errorMsg);
            updateProgressStep('error', 0, errorMsg);
            showError(errorMsg);
            restoreSearchButton();
        }
    } catch (error) {
        console.error('Job search error:', error);
        console.error('Error stack:', error.stack);
        const errorMsg = `Network error: ${error.message}. Please check your connection and try again.`;
        updateProgressStep('error', 0, errorMsg);
        showError(errorMsg);
        restoreSearchButton();
    }
}

function restoreSearchButton() {
    const searchButton = elements.searchBtn;
    if (searchButton && searchButton.dataset.originalHtml) {
        searchButton.disabled = false;
        searchButton.style.opacity = '1';
        searchButton.innerHTML = searchButton.dataset.originalHtml;
        delete searchButton.dataset.originalHtml;
    }
}

async function fetchResumeAnalytics(resumeData) {
    try {
        const response = await fetch(`/analytics/${currentSessionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                resume_data: resumeData
            })
        });

        const data = await response.json();
        if (data.success) {
            displayAnalytics(data.analytics);
        }
    } catch (error) {
        console.error('Error fetching analytics:', error);
    }
}

function displayAnalytics(analytics) {
    if (!elements.analyticsSection || !elements.analyticsGrid) return;
    
    elements.analyticsSection.classList.remove('hidden');
    elements.analyticsGrid.innerHTML = '';
    elements.analyticsGrid.className = 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6';
    latestParsedResume = analytics.resume_data || null;
    renderParsedResumeCard();
    
    const strength = analytics.strength_analysis;
    const metrics = analytics.key_metrics;
    
    // Overall Score Card
    const overallCard = createAnalyticsCard(
        'Overall Resume Score',
        `${strength.scores.overall}/100`,
        getScoreColor(strength.scores.overall),
        [
            `Skills: ${strength.scores.skills}/100`,
            `Experience: ${strength.scores.experience}/100`,
            `Education: ${strength.scores.education}/100`,
            `Summary: ${strength.scores.summary}/100`
        ]
    );
    elements.analyticsGrid.appendChild(overallCard);
    
    // Key Metrics Card
    const metricsCard = createAnalyticsCard(
        'Key Metrics',
        '',
        '',
        [
            `Total Skills: ${metrics.total_skills}`,
            `Years Experience: ~${metrics.years_experience}`,
            `Education Level: ${metrics.education_level}`,
            `Programming Languages: ${metrics.programming_languages}`
        ]
    );
    elements.analyticsGrid.appendChild(metricsCard);
    
    // Strengths Card
    if (strength.insights.strengths.length > 0) {
        const strengthsCard = createAnalyticsCard(
            'Strengths',
            `${strength.insights.strengths.length} identified`,
            'success',
            strength.insights.strengths
        );
        elements.analyticsGrid.appendChild(strengthsCard);
    }
    
    // Recommendations card removed per request

    // ATS Score card (if available from prior fetch)
    if (analytics.ats_score_card) {
        renderAtsCard(analytics.ats_score_card);
    }
}

function createAnalyticsCard(title, value, colorClass, items) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col gap-4';
    
    const badgeClass = colorClass || '';
    card.innerHTML = `
        <div class="flex items-start justify-between gap-3">
            <div class="text-slate-900 font-semibold text-lg">${escapeHtml(title)}</div>
            ${value ? `<div class="inline-flex items-center rounded-lg px-3 py-1 text-sm font-semibold ${badgeClass}">${escapeHtml(value)}</div>` : ''}
        </div>
        <div class="analytics-card-body text-sm text-slate-700">
            <ul class="space-y-2">
                ${items.map(item => `<li class="flex items-start gap-2"><span class="mt-1 h-2 w-2 rounded-full bg-slate-300"></span><span>${escapeHtml(item)}</span></li>`).join('')}
            </ul>
        </div>
    `;
    return card;
}

function getScoreColor(score) {
    if (score >= 80) return 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100';
    if (score >= 60) return 'bg-amber-50 text-amber-700 ring-1 ring-amber-100';
    return 'bg-rose-50 text-rose-700 ring-1 ring-rose-100';
}

function renderParsedResumeCard() {
    if (!elements.analyticsGrid) return;
    const existing = document.getElementById('parsed-resume-card');
    if (existing) existing.remove();
    if (!parsedCardVisible || !latestParsedResume) return;
    
    const card = document.createElement('div');
    card.id = 'parsed-resume-card';
    card.className = 'bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col gap-3 col-span-1 md:col-span-2 xl:col-span-3';
    card.innerHTML = `
        <div class="flex items-center justify-between">
            <div class="text-slate-900 font-semibold">Parsed Resume (debug)</div>
            <button class="text-xs text-slate-500 hover:text-slate-700" id="close-parsed-card">Hide</button>
        </div>
        <pre class="text-xs bg-slate-50 border border-slate-100 rounded p-3 overflow-auto max-h-64">${escapeHtml(JSON.stringify(latestParsedResume, null, 2))}</pre>
    `;
    elements.analyticsGrid.prepend(card);
    const closeBtn = document.getElementById('close-parsed-card');
    if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            parsedCardVisible = false;
            renderParsedResumeCard();
        });
    }
}

async function handleMarketIntelligence() {
    if (!elements.jobQuery || !elements.location) {
        showError('Please enter job query and location first.');
        return;
    }
    
    const jobQuery = elements.jobQuery.value.trim();
    const location = elements.location.value.trim();
    const experienceLevel = elements.experienceLevel?.value || 'mid';
    
    if (!jobQuery) {
        showError('Please enter a job query.');
        return;
    }
    
    showLoading('Fetching market intelligence...');
    
    try {
        const skills = currentResumeData?.skills || [];
        const skillsList = Array.isArray(skills) ? skills : (typeof skills === 'string' ? skills.split(',') : []);
        
        const response = await fetch('/market-intelligence', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                job_title: jobQuery,
                location: location,
                experience_level: experienceLevel,
                skills: skillsList
            })
        });
        
        const data = await response.json();
        hideLoading();
        
        if (data.success) {
            displayMarketIntelligence(data.market_intelligence);
        } else {
            showError(data.error || 'Failed to fetch market intelligence.');
        }
    } catch (error) {
        hideLoading();
        showError('Network error fetching market intelligence.');
    }
}

function displayMarketIntelligence(intel) {
    if (!elements.marketIntelSection || !elements.intelGrid) return;
    
    elements.marketIntelSection.classList.remove('hidden');
    elements.intelGrid.innerHTML = '';
    
    // Salary Insights
    if (intel.salary_insights) {
        const salary = intel.salary_insights.salary_range;
        const salaryCard = createIntelCard(
            'Salary Insights',
            `$${salary.min.toLocaleString()} - $${salary.max.toLocaleString()}`,
            'primary',
            intel.salary_insights.insights
        );
        elements.intelGrid.appendChild(salaryCard);
    }
    
    // Market Demand
    if (intel.demand_trends) {
        const demand = intel.demand_trends;
        const demandCard = createIntelCard(
            'Market Demand',
            `${demand.demand_score}/100 - ${demand.trend}`,
            demand.demand_score >= 80 ? 'success' : 'warning',
            [...demand.market_insights, ...demand.recommendations]
        );
        elements.intelGrid.appendChild(demandCard);
    }
    
    // Competition Analysis
    if (intel.competition) {
        const comp = intel.competition;
        const compCard = createIntelCard(
            'Competition Level',
            comp.competition_level.replace('_', ' ').toUpperCase(),
            comp.competition_level.includes('high') ? 'warning' : 'primary',
            [...comp.insights, ...comp.tips]
        );
        elements.intelGrid.appendChild(compCard);
    }
    
    // Industry Insights
    if (intel.industry) {
        const industry = intel.industry;
        const industryCard = createIntelCard(
            'Industry Insights',
            industry.industry,
            'primary',
            [
                `Growth Rate: ${industry.growth_rate}`,
                `Outlook: ${industry.outlook}`,
                ...industry.recommendations
            ]
        );
        elements.intelGrid.appendChild(industryCard);
    }
    
    elements.marketIntelSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function createIntelCard(title, subtitle, colorClass, items) {
    const card = document.createElement('div');
    card.className = 'intel-card';
    card.innerHTML = `
        <div class="intel-card-header">
            <h3>${escapeHtml(title)}</h3>
            <div class="intel-subtitle ${colorClass}">${escapeHtml(subtitle)}</div>
        </div>
        <div class="intel-card-body">
            <ul>
                ${items.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
            </ul>
        </div>
    `;
    return card;
}

function startProgressPolling() {
    console.log('Starting progress polling for session:', currentSessionId);
    
    // Clear any existing interval
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    
    let pollCount = 0;
    const maxPolls = 150; // 5 minutes max (150 * 2 seconds)
    
    progressInterval = setInterval(async () => {
        pollCount++;
        console.log(`Progress poll #${pollCount} for session: ${currentSessionId}`);
        
        try {
            const response = await fetch(`/progress/${currentSessionId}`);
            
            if (!response.ok) {
                throw new Error(`Progress fetch failed: ${response.status}`);
            }
            
            const progress = await response.json();
            console.log('Progress update:', progress);

            updateProgressFromServer(progress);

            if (progress.step === 'complete' && progress.results) {
                console.log('Job search complete! Displaying results...');
                clearInterval(progressInterval);
                progressInterval = null;
                updateProgressStep('complete', 100, 'Job search complete! Displaying results...');
                restoreSearchButton();
                setTimeout(() => {
                    displayJobResults(progress.results);
                }, 1000);
            } else if (progress.step === 'error') {
                console.error('Job search error:', progress.message);
                clearInterval(progressInterval);
                progressInterval = null;
                updateProgressStep('error', 0, progress.message);
                showError(progress.message);
                restoreSearchButton();
            } else if (pollCount >= maxPolls) {
                console.warn('Max polls reached, stopping polling');
                clearInterval(progressInterval);
                progressInterval = null;
                updateProgressStep('error', 0, 'Job search is taking longer than expected. Please try again.');
                restoreSearchButton();
            }
        } catch (error) {
            console.error('Error fetching progress:', error);
            if (pollCount >= 5) { // Only stop after 5 failed attempts
            clearInterval(progressInterval);
                progressInterval = null;
                updateProgressStep('error', 0, 'Error fetching progress. Please refresh and try again.');
                showError('Unable to fetch job search progress. Please try again.');
                restoreSearchButton();
            }
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
    
    // Always scroll to progress section when showing it
    setTimeout(() => {
        elements.progressSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 50);
    
    // Reset all steps
    progressSteps.forEach(stepId => {
        document.getElementById(stepId)?.classList.remove('active', 'completed');
    });
    
    // Add a subtle pulse animation to draw attention
    const progressCard = document.querySelector('.progress-card');
    if (progressCard) {
        progressCard.style.animation = 'pulse 2s ease-in-out infinite';
    }
}

function hideProgressSection() {
    elements.progressSection.classList.add('hidden');
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

// ===== ATS CHECKER =====
async function handleAtsCheck() {
    if (!currentSessionId || !currentResumeData) {
        showError('Please upload and analyze your resume first.');
        return;
    }
    showLoading('Calculating ATS score...');
    try {
        const response = await fetch(`/ats-score/${currentSessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resume_data: currentResumeData })
        });
        const data = await response.json();
        hideLoading();
        if (!data.success) {
            showError(data.error || 'ATS score not available.');
            return;
        }
        renderAtsCard({
            score: data.ats_score,
            scores: data.scores
        });
        // Scroll into view
        elements.analyticsSection?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
        hideLoading();
        showError('ATS score request failed. Please try again.');
    }
}

function renderAtsCard(atsData) {
    if (!elements.analyticsSection || !elements.analyticsGrid) return;
    elements.analyticsSection.classList.remove('hidden');
    let existing = document.getElementById('ats-score-card');
    if (existing) {
        existing.remove();
    }
    const card = document.createElement('div');
    card.className = 'analytics-card';
    card.id = 'ats-score-card';
    const score = atsData.score ?? atsData.ats_score ?? 'N/A';
    card.innerHTML = `
        <div class="analytics-card-header">
            <h3>ATS Score</h3>
            <span class="analytics-value primary">${score}%</span>
        </div>
        <div class="analytics-card-body">
            <ul>
                <li>Skills score: ${atsData.scores?.skills ?? 'N/A'}</li>
                <li>Experience score: ${atsData.scores?.experience ?? 'N/A'}</li>
                <li>Education score: ${atsData.scores?.education ?? 'N/A'}</li>
                <li>Summary score: ${atsData.scores?.summary ?? 'N/A'}</li>
            </ul>
        </div>
    `;
    elements.analyticsGrid.prepend(card);
}

// function createJobCard(job) {
//     const card = document.createElement('div');
//     card.className = 'job-card rounded-xl border border-slate-200 bg-white shadow-sm p-5 flex flex-col gap-3 hover:shadow-md hover:-translate-y-0.5 transition cursor-pointer';
//     card.dataset.score = job.score || 0;
//     card.dataset.company = job.company || '';
//     card.dataset.date = job.published || '';
//     card.dataset.site = job.site || '';

//     const score = parseFloat(job.score) || 0;
//     const scoreBadge = score >= 80
//         ? 'bg-emerald-50 text-emerald-700'
//         : score >= 60
//             ? 'bg-amber-50 text-amber-700'
//             : 'bg-rose-50 text-rose-700';
    
//     const atsScore = job.ats_score !== undefined && job.ats_score !== null ? parseInt(job.ats_score) : null;
//     const descGenerated = job.description_generated ? '<span class="inline-flex items-center rounded-full px-2 py-1 text-[11px] font-semibold bg-slate-100 text-slate-600">Generated</span>' : '';
//     card.innerHTML = `
//         <div class="flex items-start justify-between gap-3">
//             <div class="space-y-1">
//                 <div class="text-base font-semibold text-slate-900">${escapeHtml(job.title || 'N/A')}</div>
//                 <div class="text-sm text-slate-600">${escapeHtml(job.company || 'N/A')}</div>
//             </div>
//             <div class="flex items-center gap-2">
//                 <div class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${scoreBadge}">${score}% Match</div>
//                 ${atsScore !== null ? `<div class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold bg-sky-50 text-sky-700">ATS ${atsScore}%</div>` : ''}
//             </div>
//         </div>
        
//         <div class="text-sm text-slate-700 leading-relaxed">
//             <div class="flex items-center gap-2 mb-1">${descGenerated}</div>
//             ${escapeHtml(job.description || 'No description available').substring(0, 180)}...
//         </div>
        
//         <div class="flex flex-wrap items-center gap-3 text-xs text-slate-500">
//             <span class="inline-flex items-center gap-1"><i class="fas fa-building"></i> ${escapeHtml(job.site || 'N/A')}</span>
//             <span class="inline-flex items-center gap-1"><i class="fas fa-calendar"></i> ${formatDate(job.published)}</span>
//         </div>
        
//         ${job.explanation ? `
//             <div class="mt-2 border-t border-slate-200 pt-3 space-y-2">
//                 <h4 class="text-sm font-semibold text-slate-800 inline-flex items-center gap-1"><i class="fas fa-lightbulb text-amber-400"></i> AI Insights</h4>
//                 <p class="text-xs text-slate-600">
//                     ${escapeHtml(job.explanation).substring(0, 200)}...
//                 </p>
//                 ${job.recommended_improvements ? `
//                     <div class="text-xs text-slate-700 space-y-1">
//                         <strong class="text-slate-800">Recommendations:</strong>
//                         ${Array.isArray(job.recommended_improvements) ? `
//                             <ul class="list-disc list-inside space-y-1">
//                                 ${job.recommended_improvements.slice(0, 3).map(improvement => 
//                                     `<li>${escapeHtml(improvement)}</li>`
//                                 ).join('')}
//                             </ul>
//                         ` : `
//                             <p>${escapeHtml(job.recommended_improvements).substring(0, 150)}...</p>
//                         `}
//                     </div>
//                 ` : ''}
//             </div>
//         ` : job.error ? `
//             <div class="mt-2 border-t border-slate-200 pt-3 space-y-1">
//                 <h4 class="text-sm font-semibold text-rose-600 inline-flex items-center gap-1"><i class="fas fa-exclamation-triangle"></i> Analysis Issue</h4>
//                 <p class="text-xs text-rose-600">
//                     ${escapeHtml(job.error || 'Unable to analyze this job at the moment.')}
//                 </p>
//             </div>
//         ` : ''}
//     `;

//     // Add click handler to open job link
//     card.addEventListener('click', () => {
//         if (job.link && job.link !== 'N/A') {
//             window.open(job.link, '_blank');
//         }
//     });

//     return card;
// }
function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card rounded-xl border border-slate-200 bg-white shadow-sm p-5 flex flex-col gap-3 hover:shadow-md hover:-translate-y-0.5 transition';
    card.dataset.score = job.score || 0;
    card.dataset.company = job.company || '';
    card.dataset.date = job.published || '';
    card.dataset.site = job.site || '';

    const score = parseFloat(job.score) || 0;
    const scoreBadge = score >= 80
        ? 'bg-emerald-50 text-emerald-700'
        : score >= 60
            ? 'bg-amber-50 text-amber-700'
            : 'bg-rose-50 text-rose-700';
    
    const atsScore = job.ats_score !== undefined && job.ats_score !== null ? parseInt(job.ats_score) : null;
    const descGenerated = job.description_generated ? '<span class="inline-flex items-center rounded-full px-2 py-1 text-[11px] font-semibold bg-slate-100 text-slate-600">Generated</span>' : '';
    
    card.innerHTML = `
        <div class="flex items-start justify-between gap-3">
            <div class="space-y-1">
                <div class="text-base font-semibold text-slate-900">${escapeHtml(job.title || 'N/A')}</div>
                <div class="text-sm text-slate-600">${escapeHtml(job.company || 'N/A')}</div>
            </div>
            <div class="flex items-center gap-2">
                <div class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${scoreBadge}">${score}% Match</div>
                ${atsScore !== null ? `<div class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold bg-sky-50 text-sky-700">ATS ${atsScore}%</div>` : ''}
            </div>
        </div>
        
        <div class="text-sm text-slate-700 leading-relaxed">
            <div class="flex items-center gap-2 mb-1">${descGenerated}</div>
            ${escapeHtml(job.description || 'No description available').substring(0, 180)}...
        </div>
        
        <div class="flex flex-wrap items-center gap-3 text-xs text-slate-500">
            <span class="inline-flex items-center gap-1"><i class="fas fa-building"></i> ${escapeHtml(job.site || 'N/A')}</span>
            <span class="inline-flex items-center gap-1"><i class="fas fa-calendar"></i> ${formatDate(job.published)}</span>
        </div>
        
        ${job.explanation ? `
            <div class="mt-2 border-t border-slate-200 pt-3 space-y-2">
                <h4 class="text-sm font-semibold text-slate-800 inline-flex items-center gap-1"><i class="fas fa-lightbulb text-amber-400"></i> AI Insights</h4>
                <p class="text-xs text-slate-600">
                    ${escapeHtml(job.explanation).substring(0, 200)}...
                </p>
                ${job.recommended_improvements ? `
                    <div class="text-xs text-slate-700 space-y-1">
                        <strong class="text-slate-800">Recommendations:</strong>
                        ${Array.isArray(job.recommended_improvements) ? `
                            <ul class="list-disc list-inside space-y-1">
                                ${job.recommended_improvements.slice(0, 3).map(improvement => 
                                    `<li>${escapeHtml(improvement)}</li>`
                                ).join('')}
                            </ul>
                        ` : `
                            <p>${escapeHtml(job.recommended_improvements).substring(0, 150)}...</p>
                        `}
                    </div>
                ` : ''}
            </div>
        ` : job.error ? `
            <div class="mt-2 border-t border-slate-200 pt-3 space-y-1">
                <h4 class="text-sm font-semibold text-rose-600 inline-flex items-center gap-1"><i class="fas fa-exclamation-triangle"></i> Analysis Issue</h4>
                <p class="text-xs text-rose-600">
                    ${escapeHtml(job.error || 'Unable to analyze this job at the moment.')}
                </p>
            </div>
        ` : ''}
        
        <!-- Action Buttons -->
        <div class="mt-3 flex gap-2 border-t border-slate-200 pt-3">
            <button 
                class="view-job-btn flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-slate-100 text-slate-700 px-4 py-2 text-sm font-semibold hover:bg-slate-200 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-slate-500"
            >
                <i class="fas fa-external-link-alt"></i>
                View Job
            </button>
            <button 
                class="generate-resume-btn flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 text-white px-4 py-2 text-sm font-semibold hover:bg-emerald-700 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-emerald-600"
            >
                <i class="fas fa-file-alt"></i>
                Generate Resume
            </button>
        </div>
    `;

    // Add event listener for View Job button
    const viewBtn = card.querySelector('.view-job-btn');
    if (viewBtn) {
        viewBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (job.link && job.link !== 'N/A') {
                window.open(job.link, '_blank');
            }
        });
    }

    // Add event listener for Generate Resume button
    const generateBtn = card.querySelector('.generate-resume-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            showResumeGenerator(job);
        });
    }

    return card;
}

// ===== FILTERING & SORTING =====
let currentScoreFilter = 'all';
function handleFilterChange(e) {
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');

    const filter = e.target.dataset.filter;
    currentScoreFilter = filter;
    filterJobs(filter);
}

function filterJobs(filter) {
    const jobCards = document.querySelectorAll('.job-card');
    const platformFilter = elements.platformSelect?.value || 'all';
    
    jobCards.forEach(card => {
        const score = parseFloat(card.dataset.score) || 0;
        const site = (card.dataset.site || '').toLowerCase();
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

        if (platformFilter !== 'all' && site !== platformFilter.toLowerCase()) {
            show = false;
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
    console.error('Error:', message);
    if (elements.errorMessage && elements.errorModal) {
    elements.errorMessage.textContent = message;
    elements.errorModal.classList.remove('hidden');
    } else {
        // Fallback: use alert if modal elements not found
        alert('Error: ' + message);
    }
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
async function initializeResumeGenerator() {
    try {
        const response = await fetch('/resume-styles');
        const data = await response.json();
        
        if (data.success) {
            availableStyles = data.styles;
            renderStyleOptions(data.styles);
        }
    } catch (error) {
        console.error('Error loading resume styles:', error);
    }
}

// Render style selection cards
function renderStyleOptions(styles) {
    const container = document.getElementById('style-options');
    if (!container) return;
    
    container.innerHTML = '';
    
    Object.keys(styles).forEach(styleKey => {
        const style = styles[styleKey];
        const card = document.createElement('div');
        card.className = `style-card bg-white border-2 border-slate-200 rounded-lg p-4 text-center ${styleKey === selectedStyle ? 'selected' : ''}`;
        card.dataset.style = styleKey;
        
        card.innerHTML = `
            <div class="font-semibold text-slate-900 mb-1">${style.name}</div>
            <div class="text-xs text-slate-600">${style.description}</div>
            <div class="mt-2 text-xs font-mono" style="color: ${style.accent_color}">${style.accent_color}</div>
        `;
        
        card.addEventListener('click', () => selectStyle(styleKey));
        container.appendChild(card);
    });
}

// Select a style
function selectStyle(styleKey) {
    selectedStyle = styleKey;
    
    document.querySelectorAll('.style-card').forEach(card => {
        if (card.dataset.style === styleKey) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    });
}

// Show resume generator for a specific job
function showResumeGenerator(job) {
    if (!currentResumeData) {
        showError('Please analyze your resume first');
        return;
    }
    
    currentJobForResume = job;
    
    const section = document.getElementById('resume-generator-section');
    if (section) {
        section.classList.remove('hidden');
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Preview resume
async function previewResume() {
    if (!currentResumeData || !currentJobForResume) {
        showError('Missing resume data or job information');
        return;
    }
    
    showLoading('Generating tailored resume...');
    
    try {
        const response = await fetch('/generate-resume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                resume_data: currentResumeData,
                job_description: currentJobForResume.description || '',
                job_title: currentJobForResume.title || 'Position',
                style: selectedStyle
            })
        });
        
        const data = await response.json();
        hideLoading();
        
        if (data.success) {
            currentResumeHTML = data.resume.html;
            displayResumePreview(data.resume);
            displayRelevanceAnalysis(data.resume.relevance, data.resume.recommendations);
            
            // Enable download button
            document.getElementById('download-resume-btn').disabled = false;
        } else {
            showError(data.error || 'Failed to generate resume');
        }
    } catch (error) {
        hideLoading();
        showError('Error generating resume: ' + error.message);
    }
}

// Display resume preview in modal
function displayResumePreview(resume) {
    const modal = document.getElementById('resume-preview-modal');
    const content = document.getElementById('resume-preview-content');
    
    if (content) {
        content.innerHTML = resume.html;
    }
    
    if (modal) {
        modal.classList.remove('hidden');
    }
}

// Display relevance analysis
function displayRelevanceAnalysis(relevance, recommendations) {
    const analysisSection = document.getElementById('relevance-analysis');
    if (!analysisSection) return;
    
    analysisSection.classList.remove('hidden');
    
    // High relevance skills
    const highList = document.getElementById('high-relevance-list');
    if (highList) {
        highList.innerHTML = relevance.skills.high
            .map(skill => `<li class="flex items-center gap-1"><i class="fas fa-check-circle text-xs"></i> ${skill}</li>`)
            .join('') || '<li class="text-slate-400">None</li>';
    }
    
    // Medium relevance skills
    const mediumList = document.getElementById('medium-relevance-list');
    if (mediumList) {
        mediumList.innerHTML = relevance.skills.medium
            .map(skill => `<li class="flex items-center gap-1"><i class="fas fa-circle text-xs"></i> ${skill}</li>`)
            .join('') || '<li class="text-slate-400">None</li>';
    }
    
    // Low relevance skills
    const lowList = document.getElementById('low-relevance-list');
    if (lowList) {
        lowList.innerHTML = relevance.skills.low
            .slice(0, 5)
            .map(skill => `<li class="opacity-60">${skill}</li>`)
            .join('') || '<li class="text-slate-400">None</li>';
    }
    
    // Recommendations
    const recList = document.getElementById('recommendations-list');
    if (recList && relevance.recommendations) {
        recList.innerHTML = relevance.recommendations
            .map(rec => `<li>${rec}</li>`)
            .join('') || '<li>Resume looks good for this position!</li>';
    }
}


// Download resume as PDF
function downloadResumePDF() {
    if (!currentResumeHTML) {
        showError('Please preview the resume first');
        return;
    }
    
    // Create a temporary window with the resume
    const printWindow = window.open('', '_blank');
    printWindow.document.write(currentResumeHTML);
    printWindow.document.close();
    
    // Wait for content to load, then print
    setTimeout(() => {
        printWindow.print();
    }, 500);
}

// Close preview modal
function closeResumePreview() {
    const modal = document.getElementById('resume-preview-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Add event listeners for resume generator
document.addEventListener('DOMContentLoaded', () => {
    // Initialize resume generator
    initializeResumeGenerator();
    
    const previewBtn = document.getElementById('preview-resume-btn');
    if (previewBtn) {
        previewBtn.addEventListener('click', previewResume);
    }
    
    const downloadBtn = document.getElementById('download-resume-btn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadResumePDF);
    }
    
    const closePreviewBtn = document.getElementById('close-preview-btn');
    if (closePreviewBtn) {
        closePreviewBtn.addEventListener('click', closeResumePreview);
    }
    
    const modalCloseBtn = document.getElementById('modal-close-btn');
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', closeResumePreview);
    }
    
    const modalDownloadBtn = document.getElementById('modal-download-btn');
    if (modalDownloadBtn) {
        modalDownloadBtn.addEventListener('click', downloadResumePDF);
    }
});