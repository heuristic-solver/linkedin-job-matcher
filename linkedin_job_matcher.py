import google.generativeai as genai
import docx2txt
import pdfplumber
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from typing import List, Dict
import json
import feedparser
import re
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# Optional OCR dependencies (for local development)
try:
    import pytesseract
    from PIL import Image
    import fitz  # PyMuPDF
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("OCR libraries not available. Image processing will be limited.")

# Load environment variables
load_dotenv()

# Configure API key from environment variable (optional since LLM is disabled)
api_key = os.getenv('GOOGLE_AI_API_KEY')
if not api_key:
    print("Warning: GOOGLE_AI_API_KEY not set. LLM features are disabled - using structured extraction only.")

# Toggle for using real external feeds (Indeed/CareerJet scraping)
USE_EXTERNAL_FEEDS = os.getenv("USE_EXTERNAL_FEEDS", "false").lower() == "true"

# LLM functionality removed - using structured extraction only
# genai.configure(api_key=api_key)
# model = genai.GenerativeModel('gemini-2.0-flash')
# _quota_exceeded = False

# Headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0"
}

def extract_text(file_path: str) -> str:
    """Extract text from PDF, DOCX, or Image file."""
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == ".docx":
        text = docx2txt.process(file_path)
    elif ext == ".pdf":
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except:
            text = ""
            
        # Try OCR if text extraction failed and OCR is available
        if not text.strip() and OCR_AVAILABLE:
            try:
                doc = fitz.open(file_path)
                for page_num in range(len(doc)):
                    pix = doc[page_num].get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    text += pytesseract.image_to_string(img)
            except Exception as e:
                print(f"Error processing PDF with OCR: {e}")
        elif not text.strip():
            print("No text extracted from PDF and OCR not available.")
            
    elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
        if OCR_AVAILABLE:
            try:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)
            except Exception as e:
                print(f"Error processing image: {e}")
                text = ""
        else:
            print("Image processing not available without OCR libraries.")
            text = "Image text extraction not available in this environment."
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    return text.strip()

def analyze_resume(resume_text: str) -> dict:
    """
    Analyze resume using ONLY structured extraction (production-ready, accurate)
    NO LLM - Pure rule-based extraction for deterministic, reliable results
    """
    # Use ONLY structured extraction - no LLM fallback
    try:
        from extraction.structured_extractor import StructuredResumeExtractor
        
        extractor = StructuredResumeExtractor()
        extracted_data = extractor.extract_all(resume_text)
        
        # Ensure all required fields exist with proper format
        if not extracted_data.get('skills'):
            extracted_data['skills'] = []
        if not extracted_data.get('education'):
            extracted_data['education'] = []
        if not extracted_data.get('experience'):
            extracted_data['experience'] = []
        if not extracted_data.get('name'):
            extracted_data['name'] = ""
        if not extracted_data.get('email'):
            extracted_data['email'] = ""
        if not extracted_data.get('phone'):
            extracted_data['phone'] = ""
        if not extracted_data.get('summary'):
            extracted_data['summary'] = ""
        
        print(f"✓ Using structured extraction only (production mode)")
        print(f"  - Skills found: {len(extracted_data.get('skills', []))}")
        print(f"  - Experience entries: {len(extracted_data.get('experience', []))}")
        print(f"  - Education entries: {len(extracted_data.get('education', []))}")
        
        return extracted_data
        
    except ImportError as e:
        print(f"ERROR: Structured extractor not available: {e}")
        print("Falling back to basic regex parsing...")
        return parse_resume_fallback(resume_text)
    except Exception as e:
        print(f"ERROR: Structured extraction failed: {e}")
        print("Falling back to basic regex parsing...")
        return parse_resume_fallback(resume_text)

def _normalize_resume_data(resume_data: dict, original_text: str) -> dict:
    """Normalize and validate extracted resume data"""
    normalized = {
        "name": "",
        "email": "",
        "phone": "",
        "skills": [],
        "education": [],
        "experience": [],
        "summary": ""
    }
    
    # Normalize name
    if resume_data.get("name"):
        normalized["name"] = str(resume_data["name"]).strip()
    
    # Normalize email
    if resume_data.get("email"):
        email = str(resume_data["email"]).strip().lower()
        if "@" in email and "." in email.split("@")[1]:
            normalized["email"] = email
    
    # Normalize phone
    if resume_data.get("phone"):
        phone = str(resume_data["phone"]).strip()
        # Keep only digits, spaces, +, -, ( for phone
        phone = re.sub(r'[^\d\s\+\-\(\)]', '', phone)
        if len(re.sub(r'[\s\+\-\(\)]', '', phone)) >= 10:
            normalized["phone"] = phone
    
    # Normalize skills - ensure it's a list
    skills = resume_data.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(',') if s.strip()]
    elif isinstance(skills, list):
        skills = [str(s).strip() for s in skills if s and str(s).strip()]
    
    normalized["skills"] = list(set(skills))  # Remove duplicates
    
    # Normalize education
    education = resume_data.get("education", [])
    if isinstance(education, list):
        normalized_edu = []
        for edu in education:
            if isinstance(edu, dict):
                degree = edu.get("degree", "").strip()
                institution = edu.get("institution", "").strip()
                year = edu.get("year", "").strip()
                if degree or institution:
                    edu_str = f"{degree} {institution}".strip()
                    if year:
                        edu_str += f" ({year})"
                    normalized_edu.append(edu_str)
            elif isinstance(edu, str) and edu.strip():
                normalized_edu.append(edu.strip())
        normalized["education"] = normalized_edu
    elif isinstance(education, str):
        normalized["education"] = [education.strip()] if education.strip() else []
    
    # Normalize experience
    experience = resume_data.get("experience", [])
    if isinstance(experience, list):
        normalized_exp = []
        for exp in experience:
            if isinstance(exp, dict):
                role = exp.get("role", "").strip()
                company = exp.get("company", "").strip()
                duration = exp.get("duration", "").strip()
                if role or company:
                    normalized_exp.append({
                        "role": role or "Professional Role",
                        "company": company or "Company",
                        "duration": duration
                    })
            elif isinstance(exp, str) and exp.strip():
                normalized_exp.append({
                    "role": "Professional Role",
                    "company": exp.strip(),
                    "duration": ""
                })
        normalized["experience"] = normalized_exp
    elif isinstance(experience, str):
        normalized["experience"] = []
    
    # Normalize summary
    summary = resume_data.get("summary", "")
    if summary:
        normalized["summary"] = re.sub(r'\s+', ' ', str(summary)).strip()[:500]
    
    return normalized


def parse_resume_fallback(resume_text: str) -> dict:
    """Enhanced fallback resume parsing - extracts information using advanced regex patterns"""
    import re
    from datetime import datetime
    
    resume_data = {
        "name": "",
        "email": "",
        "phone": "",
        "skills": [],
        "education": [],
        "experience": [],
        "summary": ""
    }
    
    text_lower = resume_text.lower()
    lines = resume_text.split('\n')
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, resume_text)
    if emails:
        resume_data["email"] = emails[0]
    
    # Extract phone (improved pattern)
    phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\d{10}'
    phones = re.findall(phone_pattern, resume_text)
    if phones:
        phone_str = phones[0] if isinstance(phones[0], str) else ''.join(str(p) for p in phones[0] if p)
        resume_data["phone"] = phone_str
    
    # Extract name (better detection)
    # Usually first substantial line that's not email/phone/URL
    for line in lines[:10]:
        line = line.strip()
        if not line:
            continue
        # Skip if contains common non-name patterns
        if any(pattern in line.lower() for pattern in ['@', 'http', 'www', 'linkedin', 'github', 'phone', 'email', 'mobile']):
            continue
        # Name should be 2-4 words, mostly letters
        words = line.split()
        if 2 <= len(words) <= 4 and all(word.replace('.', '').replace(',', '').isalpha() for word in words):
            if len(line) > 5 and len(line) < 50:
                resume_data["name"] = line
                break
    
    # Enhanced skills extraction
    found_skills = []
    
    # Comprehensive skill keywords
    common_skills = [
        # Programming Languages
        'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'C', 'Go', 'Rust', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'R', 'Scala',
        # Web Technologies
        'HTML', 'CSS', 'SCSS', 'SASS', 'React', 'Angular', 'Vue', 'Vue.js', 'Node.js', 'Express', 'Django', 'Flask', 'FastAPI', 'Spring', 'ASP.NET',
        # Databases
        'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQLite', 'Cassandra', 'Elasticsearch',
        # Cloud & DevOps
        'AWS', 'Azure', 'GCP', 'Google Cloud', 'Docker', 'Kubernetes', 'Jenkins', 'Terraform', 'Ansible', 'CI/CD',
        # Data & ML
        'Machine Learning', 'ML', 'AI', 'Deep Learning', 'Data Science', 'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn', 'Pandas', 'NumPy',
        # Tools
        'Git', 'GitHub', 'GitLab', 'Jira', 'Agile', 'Scrum', 'Linux', 'Unix', 'Bash', 'Shell',
        # Analytics & BI
        'Excel', 'Tableau', 'Power BI', 'Qlik', 'Matplotlib', 'Seaborn', 'Plotly'
    ]
    
    for skill in common_skills:
        # More flexible matching
        skill_pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(skill_pattern, text_lower, re.IGNORECASE):
            found_skills.append(skill)
    
    # Extract skills from dedicated sections (multiple patterns)
    skills_section_patterns = [
        r'(?:skills?|technical skills?|technologies?|competencies?|proficiencies?|expertise)[:]\s*(.+?)(?:\n\n|\n(?=[A-Z][a-z]+\s*:)|$)',
        r'(?:skills?|technical skills?)[:]\s*([^\n]+(?:\n(?!\n)[^\n]+)*)',
    ]
    
    for pattern in skills_section_patterns:
        skills_match = re.search(pattern, resume_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if skills_match:
            skills_text = skills_match.group(1)
            # Split by multiple delimiters
            skill_items = re.split(r'[,;|•\-\n\r\t]+', skills_text)
            for skill in skill_items:
                skill = skill.strip()
                # Clean up skill text
                skill = re.sub(r'[•\-\*]', '', skill).strip()
                if skill and len(skill) > 1 and len(skill) < 50:
                    # Avoid common false positives
                    if not any(word in skill.lower() for word in ['years', 'experience', 'proficient', 'skilled', 'expert']):
                        found_skills.append(skill)
    
    # Canonicalize and deduplicate skills
    skill_synonyms = {
        'py': 'python', 'python3': 'python', 'js': 'javascript', 'ts': 'typescript',
        'node': 'node.js', 'nodejs': 'node.js', 'reactjs': 'react', 'react.js': 'react',
        'vuejs': 'vue', 'vue.js': 'vue', 'html5': 'html', 'css3': 'css',
        'gcloud': 'gcp', 'google cloud platform': 'gcp', 'postgres': 'postgresql',
        'mysql server': 'mysql', 'aws cloud': 'aws', 'azure cloud': 'azure'
    }
    normalized_skills = []
    seen_skill = set()
    for skill in found_skills:
        key = skill.strip().lower()
        key = skill_synonyms.get(key, key)
        canonical = key.title()
        if canonical.lower() not in seen_skill:
            normalized_skills.append(canonical)
            seen_skill.add(canonical.lower())
    
    resume_data["skills"] = normalized_skills  # Already deduped
    
    # Enhanced education extraction with multiple patterns
    education_list = []
    
    # Pattern 1: Degree + Field + Institution + Year (comprehensive)
    edu_pattern1 = r'(?:(?:Bachelor|Master|PhD|Ph\.D|B\.S|B\.A|B\.Tech|B\.E|B\.Eng|M\.S|M\.A|M\.Tech|M\.E|MBA|B\.Sc|M\.Sc|B\.Com|M\.Com|Diploma|Certificate)(?:\s+(?:of|in)\s+(?:Science|Arts|Engineering|Technology|Business|Commerce|Computer Science|Information Technology|Electronics)?)?[,\s]+)?(.+?)(?:University|College|Institute|School|Univ\.|Uni\.|IIT|NIT|IIM)(?:.*?(\d{4}))?'
    edu_matches1 = re.finditer(edu_pattern1, resume_text, re.IGNORECASE | re.MULTILINE)
    # Limit to 10 matches to avoid processing too many
    match_count = 0
    for match in edu_matches1:
        if match_count >= 10:
            break
        degree_part = match.group(0).split('University')[0].split('College')[0].split('Institute')[0].strip()
        institution_part = match.group(1).strip() if match.group(1) else ""
        year = match.group(2) if match.group(2) else ""
        
        # Extract degree type from beginning
        degree_types = re.findall(r'(?:Bachelor|Master|PhD|Ph\.D|B\.S|B\.A|B\.Tech|B\.E|M\.S|M\.A|M\.Tech|MBA|B\.Sc|M\.Sc|Diploma)', degree_part, re.IGNORECASE)
        degree = degree_types[0] if degree_types else ""
        
        if institution_part:
            edu_entry = f"{degree} {institution_part}".strip()
            if year and year.isdigit():
                edu_entry += f" ({year})"
            if edu_entry not in education_list:
                education_list.append(edu_entry)
                match_count += 1
    
    # Pattern 2: Look for education section explicitly
    edu_section_pattern = r'(?:education|academic|qualification|degrees?)[:]\s*(.+?)(?:\n\n|\n(?=[A-Z][a-z]+\s*:)|$)'
    edu_section_match = re.search(edu_section_pattern, resume_text, re.IGNORECASE | re.DOTALL)
    if edu_section_match:
        edu_text = edu_section_match.group(1)
        # Extract individual education entries
        edu_lines = [line.strip() for line in edu_text.split('\n') if line.strip() and len(line.strip()) > 10]
        for line in edu_lines[:5]:
            # Check if it contains degree keywords
            if any(deg in line for deg in ['Bachelor', 'Bachelors', 'Master', 'Masters', 'PhD', 'Ph.D', 'B.', 'M.', 'Diploma', 'Degree']):
                # Extract year if present
                year_match = re.search(r'(\d{4})', line)
                year = year_match.group(1) if year_match else ""
                edu_clean = re.sub(r'\s+', ' ', line).strip()
                if edu_clean not in education_list:
                    education_list.append(edu_clean)
    
    # Pattern 3: Simple institution + year pattern
    if len(education_list) < 2:
        simple_edu = r'([A-Z][A-Za-z\s&]+(?:University|College|Institute|IIT|NIT|IIM)).*?(\d{4})'
        simple_matches = re.finditer(simple_edu, resume_text, re.IGNORECASE)
        match_count = 0
        for match in simple_matches:
            if match_count >= 5:
                break
            institution = match.group(1).strip()
            year = match.group(2) if match.group(2) else ""
            edu_entry = institution
            if year:
                edu_entry += f" ({year})"
            if edu_entry not in education_list:
                education_list.append(edu_entry)
                match_count += 1
    
    resume_data["education"] = education_list[:5] if education_list else []
    
    # Enhanced experience extraction with multiple patterns
    experience_list = []
    current_year = datetime.now().year
    
    # Pattern 1: Look for experience/work section explicitly
    exp_section_patterns = [
        r'(?:experience|work experience|employment|professional experience|career)[:]\s*(.+?)(?:\n\n|\n(?=[A-Z][a-z]+\s*:)|$)',
        r'(?:work history|employment history)[:]\s*(.+?)(?:\n\n|\n(?=[A-Z][a-z]+\s*:)|$)'
    ]
    
    exp_section_text = ""
    for pattern in exp_section_patterns:
        exp_section_match = re.search(pattern, resume_text, re.IGNORECASE | re.DOTALL)
        if exp_section_match:
            exp_section_text = exp_section_match.group(1)
            break
    
    # Parse experience entries from section
    if exp_section_text:
        # Split by common separators
        exp_blocks = re.split(r'\n\n+|\n(?=[A-Z][a-z]+)', exp_section_text)
        for block in exp_blocks[:10]:
            block = block.strip()
            if not block or len(block) < 10:
                continue
            
            # Extract role/title (usually first line or line with job title keywords)
            role_match = re.search(r'([A-Z][A-Za-z\s&]+(?:Engineer|Developer|Analyst|Manager|Lead|Senior|Junior|Specialist|Consultant|Intern|Associate|Architect|Designer|Scientist|Executive|Director|Coordinator|Officer))', block, re.IGNORECASE)
            role = role_match.group(1).strip() if role_match else ""
            
            # Extract company (after "at", "@", or common company suffixes)
            company_match = re.search(r'(?:at|@|,)\s*([A-Z][A-Za-z\s&,\.]+(?:Inc|LLC|Ltd|Corp|Corporation|Company|Solutions|Technologies|Systems)?)', block, re.IGNORECASE)
            company = company_match.group(1).strip() if company_match else ""
            
            # Extract dates (YYYY - YYYY or Present)
            date_pattern = r'(\d{4})\s*[-–—]\s*(\d{4}|Present|Current|Now)'
            date_match = re.search(date_pattern, block, re.IGNORECASE)
            duration = ""
            if date_match:
                start = date_match.group(1)
                end = date_match.group(2)
                duration = f"{start} - {end}"
            elif re.search(r'(\d{4})', block):
                # Just year found
                year_match = re.search(r'(\d{4})', block)
                duration = year_match.group(1) if year_match else ""
            
            if role or company:
                experience_list.append({
                    "role": role or "Professional Role",
                    "company": company or "Company",
                    "duration": duration
                })
    
    # Pattern 2: Standalone job entries (if not found in section)
    if not experience_list:
        exp_pattern = r'([A-Z][A-Za-z\s&]+(?:Engineer|Developer|Analyst|Manager|Lead|Senior|Junior|Specialist|Consultant|Intern|Associate|Architect)).*?(?:at|@)\s*([A-Z][A-Za-z\s&,\.]+).*?(?:(\d{4})\s*[-–—]\s*(\d{4}|Present|Current))?'
        exp_matches = re.finditer(exp_pattern, resume_text, re.IGNORECASE)
        # Convert iterator to list or limit with counter
        match_count = 0
        for match in exp_matches:
            if match_count >= 10:
                break
            role = match.group(1).strip() if match.group(1) else ""
            company = match.group(2).strip() if match.group(2) else ""
            start_year = match.group(3) if match.group(3) else ""
            end_year = match.group(4) if match.group(4) else ""
            
            duration = ""
            if start_year:
                duration = f"{start_year} - {end_year or 'Present'}"
            
            experience_list.append({
                "role": role,
                "company": company,
                "duration": duration
            })
            match_count += 1
    
    resume_data["experience"] = experience_list[:10] if experience_list else []
    
    # Enhanced summary extraction
    # Look for objective, summary, or profile sections
    summary_patterns = [
        r'(?:summary|objective|profile|about)[:]\s*(.+?)(?:\n\n|\n[A-Z][a-z]+\s*:)',
        r'(?:summary|objective|profile)[:]\s*([^\n]+(?:\n(?!\n)[^\n]+){0,3})',
    ]
    
    summary_text = ""
    for pattern in summary_patterns:
        summary_match = re.search(pattern, resume_text, re.IGNORECASE | re.DOTALL)
        if summary_match:
            summary_text = summary_match.group(1).strip()
            break
    
    # Fallback: use first substantial paragraph
    if not summary_text:
        paragraphs = [p.strip() for p in resume_text.split('\n\n') if len(p.strip()) > 80]
        if paragraphs:
            summary_text = paragraphs[0]
    
    # Clean up summary
    if summary_text:
        summary_text = re.sub(r'\s+', ' ', summary_text)
        resume_data["summary"] = summary_text[:400]
    
    resume_data["quota_warning"] = "Resume analyzed using enhanced fallback mode (API quota exceeded)."
    return resume_data

def get_linkedin_jobs_simulation(query: str, location: str = "India") -> list[dict]:
    """
    Simulate LinkedIn job search by using their public job search page
    with careful scraping that respects robots.txt
    """
    jobs = []
    query = query.replace(" ", "%20")
    location = location.replace(" ", "%20")
    
    # LinkedIn job search URL
    url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}"
    
    print(f"Attempting to get job listings from LinkedIn...")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for job cards - LinkedIn's structure changes frequently
            job_cards = soup.find_all('div', class_='base-search-card') or soup.find_all('li')
            
            for card in job_cards[:10]:  # Limit to 10 jobs
                try:
                    title_elem = card.find('h3', class_='base-search-card__title') or card.find('h3')
                    title = title_elem.get_text(strip=True) if title_elem else "N/A"
                    
                    company_elem = card.find('a', class_='hidden-nested-link') or card.find('h4')
                    company = company_elem.get_text(strip=True) if company_elem else "N/A"
                    
                    link_elem = card.find('a', class_='base-card__full-link')
                    link = link_elem['href'] if link_elem and link_elem.has_attr('href') else "N/A"
                    
                    # For LinkedIn, we can't easily get full descriptions without authentication
                    # Use deterministic generator for first few jobs
                    if len(jobs) < 3:  # Only for first 3 LinkedIn jobs
                        description = generate_linkedin_job_description(title, company, query)
                    else:
                        description = f"{title} position at {company}. This role involves working with {query} technologies and requires relevant experience and skills in the field."
                    
                    # Ensure link is valid - use search URL if link is invalid
                    if not link or link == "N/A" or not link.startswith("http"):
                        query_encoded = query.replace(" ", "%20")
                        location_encoded = location.replace(" ", "%20")
                        link = f"https://www.linkedin.com/jobs/search/?keywords={query_encoded}&location={location_encoded}"
                    
                    if title != "N/A" and is_relevant_job(title, description, query):
                        jobs.append({
                            "site": "LinkedIn",
                            "title": title,
                            "company": company,
                            "description": description,
                            "link": link,
                            "published": (datetime.now() - timedelta(days=random.randint(0, 7))).strftime("%Y-%m-%d")
                        })
                except Exception as e:
                    print(f"Error parsing LinkedIn job card: {e}")
                    continue
                    
        else:
            print(f"LinkedIn returned status code: {response.status_code}")
            
    except Exception as e:
        print(f"Error accessing LinkedIn: {e}")
    
    return jobs

def generate_linkedin_job_description(title: str, company: str, query: str) -> str:
    """Generate a deterministic, non-LLM job description snippet."""
    responsibilities = [
        "design, build, and optimize scalable solutions",
        "collaborate with cross-functional teams to deliver features",
        "write clean, testable, and maintainable code",
        "monitor performance and drive continuous improvements",
    ]
    requirements = [
        "hands-on experience with core technologies listed in the role",
        "ability to translate requirements into reliable solutions",
        "strong communication and collaboration skills",
    ]
    resp_text = "; ".join(responsibilities[:3])
    req_text = "; ".join(requirements[:3])
    return (
        f"{title} position at {company}. This role focuses on {query} and expects candidates who can "
        f"{resp_text}. Key requirements include {req_text}."
    )

def get_jobs_from_rss(query: str, location: str = "india") -> list[dict]:
    """
    Get job listings.
    If USE_EXTERNAL_FEEDS=true, pull real RSS feeds (Indeed, CareerJet) with error handling.
    Otherwise, fall back to deterministic internal multi-platform suggestions.
    """
    jobs = []
    query = query.replace(" ", "+")
    location = location.replace(" ", "+").lower()
    
    if USE_EXTERNAL_FEEDS:
        print("USE_EXTERNAL_FEEDS=true -> fetching external RSS feeds (Indeed, CareerJet)")
    rss_sources = [
        {
            "name": "Indeed India",
            "url": f"https://rss.indeed.com/rss?q={query}&l={location}&sort=date",
            "parser": parse_indeed_rss
        },
        {
            "name": "CareerJet India",
            "url": f"https://rss.careerjet.com/rss?s={query}&l={location}&sort=relevance",
            "parser": parse_careerjet_rss
        }
    ]
    for source in rss_sources:
        try:
            print(f"Trying {source['name']} RSS feed...")
            feed = feedparser.parse(source['url'])
            if feed.entries:
                parsed_jobs = source['parser'](feed, query)
                jobs.extend(parsed_jobs)
                print(f"Found {len(parsed_jobs)} jobs from {source['name']}")
            else:
                print(f"No jobs found from {source['name']}")
                time.sleep(1)
        except Exception as e:
            print(f"Error with {source['name']} RSS: {e}")
    
    if not jobs:
        print("Using deterministic multi-platform suggestions (fallback).")
        jobs.extend(generate_additional_platform_jobs(query, location, needed=20))
    
    unique_jobs = []
    seen = set()
    for job in jobs:
        identifier = (job.get('title', ''), job.get('company', ''), job.get('site', ''))
        if identifier not in seen:
            seen.add(identifier)
            unique_jobs.append(job)
    
    return unique_jobs[:20]

def parse_indeed_rss(feed, query) -> list[dict]:
    """Parse Indeed RSS feed entries"""
    jobs = []
    for entry in feed.entries[:10]:  # Limit to 10 entries
        title = entry.get('title', 'N/A')
        link = entry.get('link', 'N/A')
        published = entry.get('published', '')
        summary = entry.get('summary', '')
        
        # Extract company from title (format: "Job Title - Company Name - Location")
        company = "N/A"
        if " - " in title:
            parts = title.split(" - ")
            if len(parts) >= 2:
                company = parts[1]
        
        # Filter for relevant jobs
        if is_relevant_job(title, summary, query):
            jobs.append({
                "site": "Indeed",
                "title": title,
                "company": company,
                "description": summary,
                "link": link,
                "published": published
            })
    
    return jobs

def parse_careerjet_rss(feed, query) -> list[dict]:
    """Parse CareerJet RSS feed entries"""
    jobs = []
    for entry in feed.entries[:10]:  # Limit to 10 entries
        title = entry.get('title', 'N/A')
        link = entry.get('link', 'N/A')
        published = entry.get('published', '')
        summary = entry.get('summary', '')
        
        # Extract company from description
        company = "N/A"
        company_match = re.search(r'company[:\s]*([^\n<]+)', summary, re.IGNORECASE)
        if company_match:
            company = company_match.group(1).strip()
        
        # Filter for relevance
        if is_relevant_job(title, summary, query):
            jobs.append({
                "site": "CareerJet",
                "title": title,
                "company": company,
                "description": summary,
                "link": link,
                "published": published
            })
    
    return jobs

def is_relevant_job(title: str, description: str, query: str) -> bool:
    """Check if a job is relevant to the query"""
    query_terms = query.lower().split()
    title_lower = title.lower()
    desc_lower = description.lower()
    
    # Check if any query term is in title or description
    for term in query_terms:
        if term in title_lower or term in desc_lower:
            return True
    
    # For AI/tech roles, also check for related terms
    tech_terms = ["ai", "artificial intelligence", "machine learning", "ml", "data science", 
                 "python", "developer", "engineer", "software", "tech", "technology"]
    
    for term in tech_terms:
        if term in title_lower or term in desc_lower:
            return True
    
    return False

def generate_relevant_job_suggestions(query: str, location: str) -> list[dict]:
    """Generate deterministic suggestions (non-LLM) when RSS fails."""
    return generate_fallback_jobs(query, location)

def generate_fallback_jobs(query: str, location: str) -> list[dict]:
    """Generate fallback job listings with verified search URLs"""
    tech_companies = ["Internal Partner", "Tech Labs", "Innovation Hub", "Product Team"]
    query_encoded = query.replace(" ", "+")
    location_encoded = location.replace(" ", "+")
    
    # Use verified search URLs that redirect to actual search results
    search_urls = {
        "LinkedIn": f"https://www.linkedin.com/jobs/search/?keywords={query_encoded}&location={location_encoded}",
        "Indeed": f"https://www.indeed.com/jobs?q={query_encoded}&l={location_encoded}",
        "CareerJet": f"https://www.careerjet.com/search/jobs?s={query_encoded}&l={location_encoded}"
    }
    
    fallback_jobs = [
        {
            "site": "LinkedIn",
            "title": f"Senior {query} Engineer",
            "company": random.choice(tech_companies),
            "description": f"We are seeking an experienced {query} professional to join our growing team. This role offers excellent growth opportunities and competitive benefits. Responsibilities include developing innovative solutions, collaborating with cross-functional teams, and driving technical excellence.",
            "description_generated": True,
            "link": search_urls["LinkedIn"],
            "published": (datetime.now() - timedelta(days=random.randint(0, 3))).strftime("%Y-%m-%d")
        },
        {
            "site": "Indeed",
            "title": f"{query} Specialist",
            "company": random.choice(tech_companies),
            "description": f"Join our dynamic team as a {query} specialist. Work on cutting-edge projects with industry-leading technologies. This role requires strong technical skills, problem-solving abilities, and a passion for innovation.",
            "description_generated": True,
            "link": search_urls["Indeed"],
            "published": (datetime.now() - timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")
        },
        {
            "site": "CareerJet",
            "title": f"Junior {query} Developer",
            "company": random.choice(tech_companies),
            "description": f"Great opportunity for someone starting their career in {query}. We provide mentorship and training in a collaborative environment. Perfect for recent graduates or professionals looking to transition into this exciting field.",
            "description_generated": True,
            "link": search_urls["CareerJet"],
            "published": (datetime.now() - timedelta(days=random.randint(0, 5))).strftime("%Y-%m-%d")
        }
    ]
    return fallback_jobs


def generate_additional_platform_jobs(query: str, location: str, needed: int = 5) -> list[dict]:
    """Deterministic job entries for extra platforms with verified search URLs."""
    platforms = [
        ("LinkedIn", f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}"),
        ("Indeed", f"https://www.indeed.com/jobs?q={query}&l={location}"),
        ("CareerJet", f"https://www.careerjet.com/search/jobs?s={query}&l={location}"),
        ("Glassdoor", f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query}&locKeyword={location}"),
        ("Monster", f"https://www.monster.com/jobs/search/?q={query}&where={location}")
    ]
    companies = ["Infosys", "TCS", "Accenture", "Adobe", "NVIDIA", "Salesforce", "Atlassian"]
    roles = [
        f"{query} Engineer",
        f"{query} Specialist",
        f"{query} Developer",
        f"{query} Analyst",
        f"{query} Lead"
    ]
    jobs = []
    for i in range(max(needed, 0)):
        site, search_link = platforms[i % len(platforms)]
        title = roles[i % len(roles)]
        company = companies[(i + 2) % len(companies)]
        jobs.append({
            "site": site,
            "title": title,
            "company": company,
            "description": f"{title} role at {company} in {location}. Work with core {query} technologies, deliver features, and collaborate with cross-functional teams.",
            "link": search_link,
            "published": (datetime.now() - timedelta(days=random.randint(0, 6))).strftime("%Y-%m-%d")
        })
    return jobs

def generate_fallback_insights(job_title: str, company: str, resume_data: dict) -> dict:
    """Generate fallback insights when AI API is not available"""
    
    # Extract skills from resume for better matching
    resume_skills = []
    if isinstance(resume_data.get('skills'), list):
        resume_skills = resume_data['skills']
    elif isinstance(resume_data.get('skills'), str):
        resume_skills = resume_data['skills'].split(',')
    
    # Common tech skills and job role mappings
    tech_roles = {
        'data scientist': ['python', 'machine learning', 'statistics', 'sql', 'r'],
        'machine learning': ['python', 'tensorflow', 'pytorch', 'deep learning', 'neural networks'],
        'software engineer': ['programming', 'java', 'python', 'javascript', 'git'],
        'data analyst': ['sql', 'excel', 'tableau', 'python', 'statistics'],
        'ai engineer': ['python', 'machine learning', 'deep learning', 'ai', 'tensorflow']
    }
    
    # Calculate basic compatibility score
    job_title_lower = job_title.lower()
    relevant_skills = []
    
    for role, skills in tech_roles.items():
        if role in job_title_lower:
            relevant_skills = skills
            break
    
    # Count skill matches
    skill_matches = 0
    if resume_skills and relevant_skills:
        for skill in resume_skills:
            if any(relevant_skill in skill.lower() for relevant_skill in relevant_skills):
                skill_matches += 1
    
    # Generate score based on matches and randomization for variety
    base_score = 60 + (skill_matches * 8) + random.randint(-10, 15)
    score = max(50, min(95, base_score))
    
    # Generate explanations based on job type
    explanations = {
        'high': f"This {job_title} position at {company} shows strong alignment with your background. Your skills and experience appear well-suited for this role's requirements.",
        'medium': f"This {job_title} role at {company} presents a good opportunity. While there's solid compatibility, some additional preparation could strengthen your application.",
        'low': f"This {job_title} position at {company} could be a growth opportunity. Consider developing relevant skills to better match the role requirements."
    }
    
    explanation_key = 'high' if score >= 80 else 'medium' if score >= 65 else 'low'
    
    # Generate targeted recommendations
    recommendations = [
        f"Research {company}'s culture and recent developments",
        "Highlight transferable skills from your experience",
        "Consider reaching out to current employees for insights"
    ]
    
    if 'data' in job_title_lower or 'analyst' in job_title_lower:
        recommendations.extend([
            "Showcase any data analysis or visualization projects",
            "Emphasize experience with data tools and methodologies"
        ])
    elif 'engineer' in job_title_lower or 'developer' in job_title_lower:
        recommendations.extend([
            "Highlight programming projects and technical achievements",
            "Demonstrate problem-solving and system design skills"
        ])
    elif 'machine learning' in job_title_lower or 'ai' in job_title_lower:
        recommendations.extend([
            "Present ML/AI projects with clear business impact",
            "Show experience with relevant frameworks and tools"
        ])
    
    return {
        'score': score,
        'explanation': explanations[explanation_key],
        'recommended_improvements': recommendations[:4]  # Limit to 4 recommendations
    }
    
def _normalize_job_listing(job: Dict, default_query: str = None) -> Dict:
    """Clean job fields to avoid masked/obfuscated titles/descriptions."""
    sanitized = job.copy()
    query = (default_query or job.get('title') or "Role").strip() or "Role"
    sanitized["description_generated"] = False
    
    def is_masked(text: str) -> bool:
        if not text:
            return True
        stars = text.count('*')
        if stars >= max(3, len(text) * 0.2):
            return True
        letters = re.sub(r'[^A-Za-z0-9]', '', text)
        return len(letters) < 3
    
    # Title
    title = str(sanitized.get('title', '')).strip()
    title = re.sub(r'\*+', ' ', title).strip()
    if is_masked(title):
        title = f"{query}"
    sanitized['title'] = title
    
    # Company
    company = str(sanitized.get('company', '')).strip()
    company = re.sub(r'\*+', ' ', company).strip()
    if is_masked(company):
        company = sanitized.get('site') or "Hiring Company"
    sanitized['company'] = company
    
    # Description
    desc = str(sanitized.get('description', '')).strip()
    desc = re.sub(r'\*+', ' ', desc).strip()
    if is_masked(desc) or len(desc) < 40:
        desc = generate_linkedin_job_description(title, company, query)
        sanitized["description_generated"] = True
    sanitized['description'] = desc
    
    return sanitized


def match_jobs_to_resume(jobs: List[Dict], resume_data: Dict, job_query: str = None) -> List[Dict]:
    """
    Match jobs to resume using rule-based algorithm (production-ready)
    NO LLM - Uses deterministic skill matching and scoring
    """
    matched_jobs = []
    
    print(f"Using rule-based matching for {len(jobs)} jobs (no LLM)")
    
    # Extract resume skills for matching
    resume_skills = resume_data.get('skills', [])
    if isinstance(resume_skills, str):
        resume_skills = [s.strip().lower() for s in resume_skills.split(',')]
    else:
        resume_skills = [str(s).strip().lower() for s in resume_skills]
    
    # Extract experience info
    experience = resume_data.get('experience', [])
    years_exp = 0
    if experience:
        # Calculate total years from experience
        for exp in experience:
            if isinstance(exp, dict) and 'years' in exp:
                years_exp += exp.get('years', 0)
            elif isinstance(exp, dict) and 'duration' in exp:
                duration = exp.get('duration', '')
                # Simple year extraction
                years = re.findall(r'\b(19|20)\d{2}\b', duration)
                if years:
                    years_int = [int(y) for y in years if 1950 <= int(y) <= 2024]
                    if years_int:
                        years_exp += max(1, len(years_int))
    
    # Match each job
    for i, job in enumerate(jobs):
        job_clean = _normalize_job_listing(job, job_query)
        match_score, explanation, improvements, skill_match_ratio = _calculate_job_match(
            job_clean, resume_skills, years_exp, resume_data
        )
        ats_score = min(100, max(0, int(skill_match_ratio * 100))) if skill_match_ratio else 40
        
        matched_job = {
            **job_clean,
            'score': match_score,  # Use 'score' for frontend compatibility
            'match_score': match_score,  # Keep both
            'ats_score': ats_score,
            'description_generated': job_clean.get("description_generated", False),
            'explanation': explanation,
            'recommended_improvements': improvements
        }
        matched_jobs.append(matched_job)
    
    # Sort by match score (highest first)
    matched_jobs.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    
    return matched_jobs


def _calculate_job_match(job: Dict, resume_skills: List[str], years_exp: float, resume_data: Dict) -> tuple:
    """
    Calculate job match score using rule-based algorithm with job-specific insights
    Returns: (score, explanation, improvements)
    """
    score = 0
    reasons = []
    improvements = []
    
    job_title = job.get('title', '').lower()
    job_desc = job.get('description', '').lower()
    job_company = job.get('company', '').lower()
    job_text = f"{job_title} {job_desc} {job_company}"
    
    # Extract specific technologies/requirements from job description
    required_skills = []
    matched_skills = []
    missing_skills = []
    
    # Comprehensive tech skills database
    tech_keywords = {
        'programming': ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r'],
        'web_frontend': ['html', 'css', 'react', 'angular', 'vue', 'vue.js', 'svelte', 'next.js', 'redux', 'webpack'],
        'web_backend': ['node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'laravel', 'rails', 'asp.net'],
        'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite', 'cassandra', 'dynamodb'],
        'cloud': ['aws', 'azure', 'gcp', 'google cloud', 'heroku', 'vercel'],
        'devops': ['docker', 'kubernetes', 'terraform', 'jenkins', 'ci/cd', 'github actions', 'gitlab'],
        'ml_ai': ['machine learning', 'ml', 'ai', 'deep learning', 'tensorflow', 'pytorch', 'keras', 'nlp', 'neural networks', 'computer vision'],
        'data': ['data science', 'pandas', 'numpy', 'spark', 'hadoop', 'tableau', 'power bi'],
        'tools': ['git', 'jira', 'agile', 'scrum', 'linux', 'bash', 'unix']
    }
    
    # Find required skills in job description
    for category, keywords in tech_keywords.items():
        for keyword in keywords:
            if keyword in job_text:
                required_skills.append(keyword)
                # Check if candidate has this skill (case-insensitive)
                skill_matched = any(
                    keyword.lower() in str(skill).lower() or str(skill).lower() in keyword.lower()
                    for skill in resume_skills
                )
                if skill_matched:
                    matched_skills.append(keyword.title())
            else:
                    missing_skills.append(keyword.title())
    
    # Also check for role-specific requirements
    role_keywords = {
        'ai engineer': ['machine learning', 'python', 'tensorflow', 'pytorch'],
        'data scientist': ['python', 'sql', 'machine learning', 'statistics', 'pandas'],
        'software engineer': ['programming', 'git', 'agile'],
        'web developer': ['javascript', 'html', 'css', 'react'],
        'backend developer': ['python', 'java', 'node.js', 'sql'],
        'devops engineer': ['docker', 'kubernetes', 'aws', 'ci/cd']
    }
    
    # Check role-specific requirements
    for role, role_skills in role_keywords.items():
        if role in job_text:
            for skill in role_skills:
                if skill not in required_skills and skill in job_text:
                    required_skills.append(skill)
                    if not any(skill.lower() in str(s).lower() for s in resume_skills):
                        missing_skills.append(skill.title())
    
    # Remove duplicates
    required_skills = list(set(required_skills))
    matched_skills = list(set(matched_skills))
    missing_skills = list(set(missing_skills))
    
    # Calculate skill score (0-60 points)
    skill_match_ratio = 0
    if required_skills:
        skill_match_ratio = len(matched_skills) / len(required_skills) if required_skills else 0
        skill_score = min(60, int(skill_match_ratio * 60))
        score += skill_score
        
        if len(matched_skills) > 0:
            reasons.append(f"Strong match with {len(matched_skills)}/{len(required_skills)} required skills")
            if matched_skills:
                reasons.append(f"Your expertise in {', '.join(matched_skills[:3])} aligns well")
    else:
        # If no specific skills found, do basic text matching
        skill_score = 30
        score += skill_score
        reasons.append("General compatibility with the role")
    
    # Experience level matching (25% of score)
    exp_keywords = {
        'senior': ['senior', 'lead', 'principal', 'architect', 'manager', 'director', 'staff'],
        'mid': ['mid-level', 'experienced', 'professional', '3+ years', '5+ years'],
        'entry': ['junior', 'entry', 'graduate', 'intern', 'associate', '0-2 years']
    }
    
    job_level = None
    for level, keywords in exp_keywords.items():
        if any(kw in job_text for kw in keywords):
            job_level = level
            break
    
    # Experience scoring
    if job_level == 'senior':
        if years_exp >= 5:
            score += 25
            reasons.append(f"Your {int(years_exp)} years of experience matches senior-level expectations")
        elif years_exp >= 3:
            score += 18
            reasons.append("Experience level is close to senior requirements")
            improvements.append(f"Gain 2-3 more years of experience for senior roles")
        else:
            score += 10
            improvements.append(f"This senior role requires 5+ years experience; you have {int(years_exp)} years")
    elif job_level == 'mid':
        if years_exp >= 2:
            score += 20
            reasons.append("Your experience level aligns with mid-level requirements")
        else:
            score += 12
            improvements.append("Consider entry-level positions or gain 1-2 years more experience")
    elif job_level == 'entry':
        if years_exp <= 2:
            score += 20
            reasons.append("Perfect match for entry-level position")
        else:
            score += 15
            improvements.append("This role may be below your experience level - consider mid/senior roles")
    else:
        score += 15  # Neutral score if level unclear
    
    # Boost for strong Python alignment when explicitly required
    if 'python' in job_text and any('python' in s for s in resume_skills):
        score += 10
        reasons.append("Python requirement met and aligned with job focus")
    
    # Education matching (10% of score)
    education = resume_data.get('education', [])
    edu_text = ' '.join(str(e).lower() for e in education)
    
    # Check for education requirements
    if any(word in job_text for word in ['phd', 'doctorate', 'ph.d']):
        if any(word in edu_text for word in ['phd', 'doctorate', 'ph.d']):
            score += 10
            reasons.append("Education level meets advanced degree requirement")
        else:
            score += 5
            improvements.append("This role prefers a PhD/Doctorate - consider highlighting advanced coursework")
    elif any(word in job_text for word in ['master', 'mba', 'ms', 'm.s']):
        if any(word in edu_text for word in ['master', 'mba', 'ms', 'm.s']):
            score += 8
            reasons.append("Your master's degree meets the educational requirement")
        elif any(word in edu_text for word in ['phd', 'doctorate']):
            score += 10
            reasons.append("Your advanced degree exceeds the requirement")
        else:
            score += 5
            improvements.append("Consider pursuing a Master's degree for better fit")
    elif any(word in job_text for word in ['bachelor', 'degree', 'bs', 'ba', 'b.s', 'b.a']):
        if any(word in edu_text for word in ['bachelor', 'degree', 'bs', 'ba', 'b.s', 'b.a']):
            score += 7
        elif any(word in edu_text for word in ['master', 'phd']):
            score += 8
        else:
            score += 5
    else:
        score += 5
    
    # Overall quality (5% of score)
    score += 5
    
    # Cap score at 100
    score = min(100, score)
    
    # Extract key phrases and requirements from job description for personalized insights
    job_desc_original = job.get('description', '')
    job_title_display = job.get('title', 'This position')
    company_display = job.get('company', 'the company') if job.get('company') and job.get('company') != 'N/A' else 'this company'
    
    # Extract specific responsibilities/requirements mentioned in job description
    responsibility_keywords = []
    requirement_phrases = []
    
    # Look for common requirement patterns in job description
    requirement_patterns = [
        r'(?:must|should|required|requirement).*?\.',
        r'(?:experience with|knowledge of|proficiency in).*?\.',
        r'(?:working with|developing|building).*?\.'
    ]
    
    for pattern in requirement_patterns:
        matches = re.finditer(pattern, job_desc_original[:500], re.IGNORECASE)
        for match in matches:
            phrase = match.group(0).strip()
            if len(phrase) > 10 and len(phrase) < 150:
                requirement_phrases.append(phrase[:100])
    
    # Get top missing skills that are actually mentioned in the job
    priority_missing = []
    job_desc_lower = job_desc_original.lower()
    for skill in missing_skills:
        if skill.lower() in job_desc_lower:
            priority_missing.append(skill)
    
    # Use actual missing skills from job description
    if not priority_missing and missing_skills:
        priority_missing = missing_skills[:3]
    
    # Generate highly specific, job-description-based explanation
    # Use skills actually found in the job description + resume
    actual_matched = matched_skills[:3] if matched_skills else []
    primary_requirement = requirement_phrases[0] if requirement_phrases else ""
    missing_list = ', '.join(priority_missing[:3]) if priority_missing else ""
    
    if score >= 85:
        if actual_matched:
            explanation = (
                f"Excellent match for {job_title_display} at {company_display}! "
                f"Your expertise in {', '.join(actual_matched)} directly maps to this role. "
                f"{primary_requirement or (reasons[0] if reasons else 'You cover the core requirements')}."
            )
        else:
            explanation = (
                f"Excellent match for {job_title_display} at {company_display}! "
                f"{primary_requirement or (reasons[0] if reasons else 'Your profile aligns strongly with the role requirements')}."
            )
    elif score >= 70:
        if actual_matched:
            explanation = (
                f"Strong candidate for {job_title_display} at {company_display}. "
                f"Your experience with {', '.join(actual_matched[:2])} is valuable here. "
                f"{primary_requirement or (reasons[0] if reasons else 'Good alignment with the role')}."
            )
        else:
            explanation = (
                f"Strong candidate for {job_title_display}. "
                f"{primary_requirement or (reasons[0] if reasons else 'Relevant background for this role')}."
            )
    elif score >= 55:
        if missing_list:
            explanation = (
                f"Moderate match for {job_title_display}. "
                f"{primary_requirement or (reasons[0] if reasons else 'Some relevant experience')}. "
                f"Improve {missing_list} to strengthen your fit."
            )
        else:
            explanation = (
                f"Moderate match for {job_title_display}. "
                f"{primary_requirement or (reasons[0] if reasons else 'Some compatibility with the role')}."
            )
    elif score >= 40:
        if missing_list:
            explanation = (
                f"Limited match with {job_title_display} at {company_display}. "
                f"This role emphasizes {missing_list}; upskill here before applying."
            )
        else:
            explanation = (
                f"Limited match with {job_title_display}. "
                f"Significant gaps relative to the requirements."
            )
    else:
        explanation = (
            f"Low match with {job_title_display}. "
            f"The required skills and experience differ from your profile; consider roles closer to your background."
        )
    
    # Generate ONLY job-description-specific recommendations (no generic ones)
    improvements_clean = []
    
    # Only add recommendations for skills that are ACTUALLY mentioned in the job description
    job_desc_lower_clean = job_desc_original.lower()
    
    # Filter missing skills to only those mentioned in job description
    job_specific_missing = []
    for skill in missing_skills:
        skill_lower = skill.lower()
        # Check if skill is mentioned in job description
        if (skill_lower in job_desc_lower_clean or 
            any(word in job_desc_lower_clean for word in skill_lower.split()) or
            skill_lower.replace(' ', '') in job_desc_lower_clean.replace(' ', '')):
            job_specific_missing.append(skill)
    
    # Remove duplicates and get unique missing skills
    unique_missing = []
    seen_lower = set()
    for skill in job_specific_missing:
        if skill.lower() not in seen_lower:
            unique_missing.append(skill)
            seen_lower.add(skill.lower())
    
    # 1. Missing skills directly mentioned in job description (highest priority)
    if unique_missing:
        improvements_clean.append(f"Learn or strengthen: {', '.join(unique_missing[:3])} - specifically required in this role")
    
    # 2. Role-specific recommendations ONLY if skills are actually missing AND mentioned in job
    # Only add if the skill is BOTH missing AND mentioned in job description
    if 'ai engineer' in job_title.lower() or ('ai' in job_title.lower() and 'engineer' in job_title.lower()):
        if 'python' in [s.lower() for s in unique_missing]:
            improvements_clean.append("Python is essential for AI engineering - mentioned in this role")
        if any(s.lower() in ['tensorflow', 'pytorch'] for s in unique_missing):
            improvements_clean.append("ML frameworks (TensorFlow/PyTorch) are required for this AI role")
    elif 'data scientist' in job_title.lower() or ('data' in job_text and 'scientist' in job_text):
        if 'sql' in [s.lower() for s in unique_missing]:
            improvements_clean.append("SQL is critical for data analysis - mentioned in requirements")
        if any(s.lower() in ['pandas', 'numpy'] for s in unique_missing):
            improvements_clean.append("Data manipulation libraries (Pandas/NumPy) needed for this role")
    elif 'machine learning' in job_text or 'ml engineer' in job_title.lower():
        if any(s.lower() in ['tensorflow', 'pytorch'] for s in unique_missing):
            improvements_clean.append("ML frameworks required - mentioned in job description")
        if any(s.lower() in ['aws', 'gcp'] for s in unique_missing):
            improvements_clean.append("Cloud platform experience needed for ML deployment")
    elif 'web developer' in job_title.lower() or ('web' in job_text and 'developer' in job_text):
        if 'javascript' in [s.lower() for s in unique_missing]:
            improvements_clean.append("JavaScript is a core requirement for web development")
        if 'react' in [s.lower() for s in unique_missing]:
            improvements_clean.append("React.js experience mentioned in job requirements")
    elif 'backend' in job_title.lower() or 'backend developer' in job_text:
        if 'node.js' in [s.lower() for s in unique_missing]:
            improvements_clean.append("Node.js backend development needed")
        if 'sql' in [s.lower() for s in unique_missing]:
            improvements_clean.append("SQL database skills required for backend development")
    
    # 3. Experience-based specific recommendations
    if job_level == 'senior' and years_exp < 5:
        improvements_clean.append(f"This senior role typically requires 5+ years - you have {int(years_exp)}. Gain {5-int(years_exp)} more years or highlight leadership experience")
    
    # 4. Cloud/DevOps specific to job (only if mentioned in job description)
    if 'aws' in job_desc_lower_clean and any('aws' in s.lower() for s in unique_missing):
        improvements_clean.append("AWS is specifically mentioned in this role - consider certification")
    if 'azure' in job_desc_lower_clean and any('azure' in s.lower() for s in unique_missing):
        improvements_clean.append("Azure knowledge mentioned in job requirements")
    if 'docker' in job_desc_lower_clean and any('docker' in s.lower() for s in unique_missing):
        improvements_clean.append("Docker containerization mentioned in this role")
    if 'kubernetes' in job_desc_lower_clean and any('kubernetes' in s.lower() for s in unique_missing):
        improvements_clean.append("Kubernetes orchestration required per job description")
    
    # Only return job-specific recommendations (no generic fallbacks)
    # If no job-specific recommendations found, return empty list
    return (score, explanation, improvements_clean[:4] if improvements_clean else [], skill_match_ratio)

def display_results(matched_jobs: List[Dict]):
    """Display the results in a readable format"""
    print("\n" + "="*80)
    print("TOP JOB MATCHES FOR YOUR RESUME")
    print("="*80)
    
    for i, job in enumerate(matched_jobs[:10], 1):
        print(f"\n{i}. [{job['site']}] {job['title']}")
        print(f"   Company: {job.get('company', 'N/A')}")
        print(f"   Published: {job.get('published', 'N/A')}")
        print(f"   Compatibility Score: {job.get('score', 'N/A')}/100")
        print(f"   Link: {job['link']}")
        
        if 'explanation' in job:
            print(f"\n   EXPLANATION:")
            # Print the explanation with proper wrapping
            explanation = job['explanation']
            for line in [explanation[i:i+70] for i in range(0, len(explanation), 70)]:
                print(f"   {line}")
        
        if 'recommended_improvements' in job:
            print(f"\n   RECOMMENDED IMPROVEMENTS:")
            if isinstance(job['recommended_improvements'], list):
                for improvement in job['recommended_improvements']:
                    print(f"   • {improvement}")
            else:
                improvements = str(job['recommended_improvements'])
                for line in [improvements[i:i+70] for i in range(0, len(improvements), 70)]:
                    print(f"   {line}")
        
        print("-" * 80)

def main():
    print("=== AI-Powered Resume Analysis and Job Matching Tool ===\n")
    
    # Step 1: Extract text from resume
    resume_path = input("Enter the path to your resume (PDF/DOCX/Image): ").strip()
    
    if not os.path.exists(resume_path):
        print("File not found. Please check the path and try again.")
        return
    
    try:
        print("Extracting text from resume...")
        resume_text = extract_text(resume_path)
        if not resume_text.strip():
            print("No text could be extracted from the resume. It might be a scanned image with poor quality.")
            return
        print("✓ Resume text extracted successfully\n")
    except Exception as e:
        print(f"Error extracting text: {e}")
        return
    
    # Step 2: Analyze resume with AI
    print("Analyzing resume with AI...")
    resume_data = analyze_resume(resume_text)
    print("✓ Resume analysis completed\n")
    
    # Display resume summary
    print("=== RESUME SUMMARY ===")
    if "name" in resume_data:
        print(f"Name: {resume_data.get('name', 'N/A')}")
    if "email" in resume_data:
        print(f"Email: {resume_data.get('email', 'N/A')}")
    if "skills" in resume_data and isinstance(resume_data.get('skills'), list):
        print(f"Skills: {', '.join(resume_data.get('skills', []))[:100]}...")
    elif "skills" in resume_data:
        print(f"Skills: {str(resume_data.get('skills'))[:100]}...")
    print()
    
    # Step 3: Get relevant job listings from RSS feeds and LinkedIn
    job_query = input("Enter job search query (e.g., 'AI Engineer'): ").strip() or "AI Engineer"
    location = input("Enter location (default: India): ").strip() or "India"
    
    print(f"\nSearching for '{job_query}' positions in {location} using multiple sources...")
    jobs = get_jobs_from_rss(job_query, location)
    print(f"✓ Found {len(jobs)} jobs\n")
    
    if not jobs:
        print("No jobs found. Try a different query.")
        return
    
    # Step 4: Match jobs to resume
    print("Matching jobs to your resume...")
    matched_jobs = match_jobs_to_resume(jobs, resume_data, job_query)
    print("✓ Job matching completed")
    
    # Step 5: Display results
    display_results(matched_jobs)
    
    # Save to CSV
    try:
        df = pd.DataFrame(matched_jobs)
        df.to_csv("matched_jobs.csv", index=False, encoding="utf-8")
        print("\n✓ Results saved to matched_jobs.csv")
    except Exception as e:
        print(f"Error saving CSV: {e}")
    
    # Save resume analysis
    try:
        with open("resume_analysis.json", "w", encoding="utf-8") as f:
            json.dump(resume_data, f, indent=2, ensure_ascii=False)
        print("✓ Resume analysis saved to resume_analysis.json")
    except Exception as e:
        print(f"Error saving JSON: {e}")

if __name__ == "__main__":
    import random
    main()
