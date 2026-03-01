"""
Advanced Resume Analytics Module
Provides detailed analysis and insights about resumes
"""
import re
from typing import Dict, List
import json

def calculate_resume_strength_score(resume_data: Dict) -> Dict:
    """
    Calculate overall resume strength score and provide detailed breakdown
    Returns a dictionary with scores and insights
    """
    # Canonical skill synonyms
    skill_synonyms = {
        'py': 'python', 'python3': 'python', 'js': 'javascript', 'ts': 'typescript',
        'node': 'node.js', 'nodejs': 'node.js', 'reactjs': 'react', 'react.js': 'react',
        'vuejs': 'vue', 'vue.js': 'vue', 'html5': 'html', 'css3': 'css',
        'gcloud': 'gcp', 'google cloud platform': 'gcp', 'postgres': 'postgresql',
        'mysql server': 'mysql', 'aws cloud': 'aws', 'azure cloud': 'azure'
    }
    
    scores = {
        'overall': 0,
        'skills': 0,
        'experience': 0,
        'education': 0,
        'summary': 0,
        'contact_info': 0
    }
    
    insights = {
        'strengths': [],
        'weaknesses': [],
        'recommendations': []
    }
    
    # Contact Information Score (0-100)
    has_name = bool(resume_data.get('name'))
    has_email = bool(resume_data.get('email'))
    has_phone = bool(resume_data.get('phone'))
    contact_score = ((has_name * 40) + (has_email * 40) + (has_phone * 20))
    scores['contact_info'] = contact_score
    
    if contact_score < 100:
        insights['weaknesses'].append("Missing contact information - ensure name, email, and phone are included")
    else:
        insights['strengths'].append("Complete contact information provided")
    
    # Skills Score (0-100)
    skills = resume_data.get('skills', [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(',')]
    
    # Canonicalize and deduplicate skills
    canonical_skills = []
    seen = set()
    for s in skills if isinstance(skills, list) else []:
        key = str(s).strip().lower()
        key = skill_synonyms.get(key, key)
        canonical = key.title()
        if canonical.lower() not in seen and canonical:
            canonical_skills.append(canonical)
            seen.add(canonical.lower())
    
    num_skills = len(canonical_skills)
    
    if num_skills >= 18:
        skills_score = 100
        insights['strengths'].append("Strong skillset with comprehensive technical skills")
    elif num_skills >= 12:
        skills_score = 90
        insights['strengths'].append("Good breadth of technical skills")
    elif num_skills >= 8:
        skills_score = 75
        insights['recommendations'].append("Add a few more role-relevant skills to strengthen coverage")
    elif num_skills >= 5:
        skills_score = 60
        insights['weaknesses'].append("Limited skills listed - expand your technical stack")
    elif num_skills > 0:
        skills_score = 45
        insights['weaknesses'].append("Very few skills listed - add core tools/languages for your target role")
    else:
        skills_score = 20
        insights['weaknesses'].append("No skills found - include a clear skills section")
    
    scores['skills'] = skills_score
    
    # Experience Score (0-100) - improved calculation with better data handling
    experience = resume_data.get('experience', [])
    if isinstance(experience, str):
        experience = []
    elif not isinstance(experience, list):
        experience = []
    
    # Ensure experience is a list of dicts
    normalized_experience = []
    for exp in experience:
        if isinstance(exp, dict):
            normalized_experience.append(exp)
        elif isinstance(exp, str) and exp.strip():
            normalized_experience.append({
                "role": "Professional Role",
                "company": exp.strip(),
                "duration": ""
            })
    
    num_roles = len(normalized_experience)
    
    # Calculate years of experience more accurately
    years_exp = _estimate_years_experience(normalized_experience)
    
    # Score based on both number of roles and years (prioritize years for accuracy)
    if years_exp >= 8 and num_roles >= 3:
        exp_score = 100
        insights['strengths'].append(f"Extensive work experience ({years_exp}+ years, {num_roles} roles)")
    elif years_exp >= 5:
        exp_score = 90
        insights['strengths'].append(f"Strong work experience ({years_exp} years)")
    elif years_exp >= 3:
        exp_score = 80
        insights['recommendations'].append("Highlight impact and outcomes for your recent roles")
    elif years_exp >= 1.5:
        exp_score = 65
        insights['recommendations'].append("Add measurable achievements to bolster experience section")
    elif years_exp > 0 or num_roles > 0:
        exp_score = 50
        insights['weaknesses'].append("Experience is light - include internships, projects, or freelance work")
    else:
        exp_score = 25
        insights['weaknesses'].append("Limited work experience - highlight projects, internships, or volunteer work")
    
    scores['experience'] = exp_score
    
    # Education Score (0-100) - improved detection
    education = resume_data.get('education', [])
    if isinstance(education, str):
        education = [education] if education else []
    
    num_degrees = len(education) if isinstance(education, list) else 0
    
    # Check education level quality
    edu_text = ' '.join(str(e).lower() for e in education)
    has_phd = any(word in edu_text for word in ['phd', 'doctorate', 'doctoral'])
    has_masters = any(word in edu_text for word in ['master', 'mba', 'ms', 'm.sc', 'mtech', 'm.tech', 'm.e', 'mca'])
    has_bachelors = any(word in edu_text for word in ['bachelor', 'bs', 'b.sc', 'btech', 'b.tech', 'b.e', 'be', 'bca', 'bba', 'b.s', 'b.a'])
    
    if has_phd:
        edu_score = 100
        insights['strengths'].append("Advanced degree (PhD/Doctorate) present")
    elif has_masters and num_degrees >= 1:
        edu_score = 95
        insights['strengths'].append("Master's degree present")
    elif has_bachelors and num_degrees >= 1:
        edu_score = 85
        insights['strengths'].append("Bachelor's degree present")
    elif num_degrees >= 2:
        edu_score = 80
    elif num_degrees == 1:
        edu_score = 70
        if not has_bachelors and not has_masters and not has_phd:
            insights['recommendations'].append("Consider specifying degree type (Bachelor's/Master's) in education section")
    else:
        edu_score = 40
        insights['weaknesses'].append("Education section missing or incomplete - include degree, institution, and year")
    
    scores['education'] = edu_score
    
    # Summary Score (0-100)
    summary = resume_data.get('summary', '')
    summary_length = len(summary) if summary else 0
    
    if summary_length >= 200:
        summary_score = 95
        insights['strengths'].append("Comprehensive professional summary")
    elif summary_length >= 120:
        summary_score = 85
    elif summary_length >= 60:
        summary_score = 70
        insights['recommendations'].append("Expand your professional summary for better impact")
    elif summary_length > 0:
        summary_score = 45
        insights['weaknesses'].append("Summary too brief - add more details about your professional background")
    else:
        summary_score = 20
        insights['weaknesses'].append("Missing professional summary - add a compelling summary")
    
    scores['summary'] = summary_score
    
    # Calculate overall score (weighted average)
    scores['overall'] = round(
        (scores['contact_info'] * 0.05 +
         scores['skills'] * 0.35 +
         scores['experience'] * 0.35 +
         scores['education'] * 0.15 +
         scores['summary'] * 0.1)
    )
    
    # Generate additional recommendations
    if scores['overall'] < 60:
        insights['recommendations'].append("Resume needs significant improvement - focus on all sections")
    elif scores['overall'] < 75:
        insights['recommendations'].append("Resume is decent but can be improved - address weak areas")
    else:
        insights['recommendations'].append("Resume is strong - consider minor refinements for optimal impact")
    
    return {
        'scores': scores,
        'insights': insights,
        'metrics': {
            'total_skills': num_skills,
            'total_experience_roles': num_roles,
            'total_degrees': num_degrees,
            'summary_length': summary_length
        }
    }


def analyze_skills_gap(resume_data: Dict, job_description: str) -> Dict:
    """
    Analyze the gap between resume skills and job requirements
    """
    resume_skills = resume_data.get('skills', [])
    if isinstance(resume_skills, str):
        resume_skills = [s.strip().lower() for s in resume_skills.split(',')]
    else:
        resume_skills = [str(s).strip().lower() for s in resume_skills]
    
    # Common tech skills to look for in job descriptions
    tech_keywords = {
        'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'ruby', 'php', 'swift', 'kotlin'],
        'web': ['html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring'],
        'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite'],
        'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins'],
        'data': ['pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn', 'apache spark', 'hadoop'],
        'tools': ['git', 'jira', 'agile', 'scrum', 'ci/cd', 'linux', 'bash']
    }
    
    job_lower = job_description.lower()
    
    # Find required skills in job description
    required_skills = []
    for category, keywords in tech_keywords.items():
        for keyword in keywords:
            if keyword in job_lower:
                required_skills.append(keyword)
    
    # Find matching skills
    matching_skills = []
    missing_skills = []
    
    for skill in required_skills:
        found = False
        for resume_skill in resume_skills:
            if skill in resume_skill or resume_skill in skill:
                matching_skills.append(skill)
                found = True
                break
        if not found:
            missing_skills.append(skill)
    
    # Calculate match percentage
    match_percentage = (len(matching_skills) / len(required_skills) * 100) if required_skills else 0
    
    return {
        'required_skills': list(set(required_skills)),
        'matching_skills': list(set(matching_skills)),
        'missing_skills': list(set(missing_skills)),
        'match_percentage': round(match_percentage, 1),
        'recommendations': _generate_skill_recommendations(missing_skills)
    }


def _generate_skill_recommendations(missing_skills: List[str]) -> List[str]:
    """Generate recommendations based on missing skills"""
    recommendations = []
    
    if not missing_skills:
        return ["Great! Your skills align well with the job requirements"]
    
    if len(missing_skills) <= 2:
        recommendations.append(f"Consider learning: {', '.join(missing_skills[:2])}")
    else:
        recommendations.append(f"Focus on learning: {', '.join(missing_skills[:3])}")
        recommendations.append(f"Additional skills to consider: {', '.join(missing_skills[3:5])}")
    
    return recommendations


def extract_key_metrics(resume_data: Dict) -> Dict:
    """Extract key metrics from resume data with improved data handling"""
    skills = resume_data.get('skills', [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(',') if s.strip()]
    elif not isinstance(skills, list):
        skills = []
    
    experience = resume_data.get('experience', [])
    if isinstance(experience, str):
        experience = []
    elif not isinstance(experience, list):
        experience = []
    
    # Normalize experience to list of dicts
    normalized_experience = []
    for exp in experience:
        if isinstance(exp, dict):
            normalized_experience.append(exp)
        elif isinstance(exp, str) and exp.strip():
            normalized_experience.append({
                "role": "Professional Role",
                "company": exp.strip(),
                "duration": ""
            })
    
    education = resume_data.get('education', [])
    if isinstance(education, str):
        education = [education] if education.strip() else []
    elif not isinstance(education, list):
        education = []
    
    # Categorize skills
    programming_skills = []
    framework_skills = []
    tool_skills = []
    soft_skills = []
    
    skill_keywords = {
        'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'ruby', 'php'],
        'framework': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'tensorflow', 'pytorch'],
        'tool': ['git', 'docker', 'kubernetes', 'jenkins', 'jira', 'linux', 'aws', 'azure', 'gcp']
    }
    
    for skill in skills:
        skill_lower = str(skill).lower()
        categorized = False
        
        for cat, keywords in skill_keywords.items():
            if any(kw in skill_lower for kw in keywords):
                if cat == 'programming':
                    programming_skills.append(skill)
                elif cat == 'framework':
                    framework_skills.append(skill)
                elif cat == 'tool':
                    tool_skills.append(skill)
                categorized = True
                break
        
        if not categorized:
            soft_skills.append(skill)
    
    return {
        'total_skills': len(skills),
        'programming_languages': len(programming_skills),
        'frameworks': len(framework_skills),
        'tools': len(tool_skills),
        'soft_skills': len(soft_skills),
        'years_experience': _estimate_years_experience(normalized_experience),
        'education_level': _get_highest_education(education),
        'skill_categories': {
            'programming': programming_skills[:10],
            'frameworks': framework_skills[:10],
            'tools': tool_skills[:10],
            'soft_skills': soft_skills[:5]
        }
    }


def _estimate_years_experience(experience: List) -> float:
    """Calculate years of experience from experience list - uses extracted 'years' field directly, no assumptions"""
    if not experience or not isinstance(experience, list):
        return 0.0
    
    total_years = 0.0
    
    for exp in experience:
        if isinstance(exp, dict):
            # Use the 'years' field if it exists (calculated from extracted dates)
            if 'years' in exp:
                years = exp.get('years', 0.0)
                if isinstance(years, (int, float)):
                    total_years += float(years)
            # Fallback: try to calculate from duration string
            elif 'duration' in exp:
                duration = str(exp.get('duration', '')).strip()
                if duration:
                    # Extract years from duration like "2020 - 2022" or "2020 - Present"
                    years = _parse_duration_to_years(duration)
                    total_years += years
    
    # Round to 1 decimal place for display
    return round(total_years, 1)


def _parse_duration_to_years(duration: str) -> float:
    """Parse duration string to years - handles multiple formats"""
    from datetime import datetime
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    def _norm_year(val: str):
        if not val:
            return None
        val = str(val)
        if len(val) == 2 and val.isdigit():
            num = int(val)
            return 2000 + num if num < 50 else 1900 + num
        if len(val) == 4 and val.isdigit():
            return int(val)
        return None
    
    month_names = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
        'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }
    
    # Pattern: "YYYY - YYYY" or "YYYY - Present"
    pattern1 = r'(\d{4})\s*[-–—]\s*(\d{4}|Present|Current|Now)'
    match1 = re.search(pattern1, duration, re.IGNORECASE)
    if match1:
        start_year = int(match1.group(1))
        end_str = match1.group(2)
        
        if end_str.lower() in ['present', 'current', 'now']:
            end_year = current_year
            end_month = current_month
            start_month = 1
        else:
            end_year = int(end_str)
            end_month = 12
            start_month = 1
        
        if 1950 <= start_year <= current_year and start_year <= end_year:
            months = (end_year - start_year) * 12 + (end_month - start_month)
            return months / 12.0
    
    # Pattern: "MM/YYYY - MM/YYYY" or "MM/YYYY - Present"
    pattern2 = r'(\d{1,2})[/-](\d{2,4})\s*[-–—]\s*(\d{1,2})?[/-]?(\d{2,4}|Present|Current|Now)?'
    match2 = re.search(pattern2, duration, re.IGNORECASE)
    if match2:
        start_month = int(match2.group(1))
        start_year = _norm_year(match2.group(2))
        
        if match2.group(4):
            if match2.group(4).lower() in ['present', 'current', 'now']:
                end_year = current_year
                end_month = current_month
            else:
                end_year = _norm_year(match2.group(4))
                end_month = int(match2.group(3)) if match2.group(3) else 12
        else:
            end_year = current_year
            end_month = current_month
        
        if start_year and end_year and 1950 <= start_year <= current_year and start_year <= end_year:
            months = (end_year - start_year) * 12 + (end_month - start_month)
            return months / 12.0
    
    return 0.0


def _get_highest_education(education: List) -> str:
    """
    Return the first extracted education entry (raw), avoiding preference/heuristics.
    This reflects exactly what was parsed from the CV.
    """
    if not education or not isinstance(education, list):
        return "Not specified"
    
    first = education[0]
    if isinstance(first, dict):
        degree = str(first.get("degree", "")).strip()
        inst = str(first.get("institution", "")).strip()
        year = str(first.get("year", "")).strip()
        parts = [p for p in [degree, inst, year] if p]
        return ' • '.join(parts)[:120] if parts else "Not specified"
    
    return str(first).strip()[:120] if str(first).strip() else "Not specified"

