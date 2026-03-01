"""
Gemini-Powered Resume Generator
Uses Google's Gemini API to generate intelligent, tailored resume content
"""

import google.generativeai as genai
import os
import json
import re
from typing import Dict, List, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv('GOOGLE_AI_API_KEY')
if api_key:
    genai.configure(api_key=api_key)
    # Use the correct model name for v1 API
    model = genai.GenerativeModel('gemini-2.0-flash-001')
else:
    print("Warning: GOOGLE_AI_API_KEY not set. Resume generator will use fallback mode.")
    model = None


class GeminiResumeGenerator:
    """Generate tailored resumes using Gemini AI"""
    
    # Available resume styles/templates
    STYLES = {
        'professional': {
            'name': 'Professional',
            'description': 'Clean, traditional format suitable for corporate positions',
            'font': 'Arial, sans-serif',
            'accent_color': '#2C3E50',
            'layout': 'single-column'
        },
        'modern': {
            'name': 'Modern',
            'description': 'Contemporary design with accent colors',
            'font': 'Calibri, sans-serif',
            'accent_color': '#007AFF',
            'layout': 'two-column'
        },
        'creative': {
            'name': 'Creative',
            'description': 'Bold design for creative industries',
            'font': 'Helvetica, sans-serif',
            'accent_color': '#E74C3C',
            'layout': 'two-column'
        },
        'minimal': {
            'name': 'Minimal',
            'description': 'Simple, text-focused layout',
            'font': 'Georgia, serif',
            'accent_color': '#34495E',
            'layout': 'single-column'
        },
        'tech': {
            'name': 'Tech',
            'description': 'Optimized for technical roles',
            'font': 'Consolas, monospace',
            'accent_color': '#27AE60',
            'layout': 'single-column'
        }
    }
    
    def __init__(self):
        self.model = model
    
    def generate_tailored_resume(
        self, 
        resume_data: Dict, 
        job_description: str,
        job_title: str,
        style: str = 'professional'
    ) -> Dict:
        """
        Generate a tailored resume using Gemini AI
        """
        # Get style configuration
        style_config = self.STYLES.get(style, self.STYLES['professional'])
        
        # Generate resume content using Gemini
        if self.model:
            tailored_content = self._generate_with_gemini(
                resume_data,
                job_description,
                job_title
            )
        else:
            # Fallback to rule-based generation
            tailored_content = self._generate_fallback(
                resume_data,
                job_description,
                job_title
            )
        
        # Generate HTML
        html = self._generate_html(
            resume_data,
            tailored_content,
            style_config,
            job_title
        )
        
        return {
            'html': html,
            'style': style,
            'style_config': style_config,
            'tailored_content': tailored_content,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'job_title': job_title,
                'style_used': style,
                'ai_generated': bool(self.model)
            }
        }
    
    def _generate_with_gemini(
        self,
        resume_data: Dict,
        job_description: str,
        job_title: str
    ) -> Dict:
        """
        Use Gemini API to generate tailored resume content
        """
        try:
            # Prepare resume context
            resume_context = self._prepare_resume_context(resume_data)
            
            # Create comprehensive prompt
            prompt = self._create_gemini_prompt(
                resume_context,
                job_description,
                job_title
            )
            
            # Generate content
            response = self.model.generate_content(prompt)
            
            # Parse response
            tailored_content = self._parse_gemini_response(response.text)
            
            return tailored_content
            
        except Exception as e:
            print(f"Error using Gemini API: {e}")
            print("Falling back to rule-based generation...")
            return self._generate_fallback(resume_data, job_description, job_title)
    
    def _prepare_resume_context(self, resume_data: Dict) -> str:
        """
        Prepare resume data as context for Gemini
        """
        context_parts = []
        
        # Personal info
        name = resume_data.get('name', 'Candidate')
        email = resume_data.get('email', '')
        phone = resume_data.get('phone', '')
        
        context_parts.append(f"CANDIDATE: {name}")
        if email:
            context_parts.append(f"Email: {email}")
        if phone:
            context_parts.append(f"Phone: {phone}")
        
        # Skills
        skills = resume_data.get('skills', [])
        if skills:
            if isinstance(skills, list):
                skills_str = ', '.join([str(s) for s in skills])
            else:
                skills_str = str(skills)
            context_parts.append(f"\nSKILLS: {skills_str}")
        
        # Experience
        experience = resume_data.get('experience', [])
        if experience and isinstance(experience, list):
            context_parts.append("\nWORK EXPERIENCE:")
            for exp in experience:
                if isinstance(exp, dict):
                    role = exp.get('role', '')
                    company = exp.get('company', '')
                    duration = exp.get('duration', '')
                    description = exp.get('description', '')
                    
                    if role or company:
                        context_parts.append(f"- {role} at {company}")
                        if duration:
                            context_parts.append(f"  Duration: {duration}")
                        if description:
                            context_parts.append(f"  {description}")
        
        # Projects
        projects = resume_data.get('projects', [])
        if projects:
            context_parts.append("\nPROJECTS:")
            if isinstance(projects, list):
                for proj in projects:
                    if isinstance(proj, dict):
                        title = proj.get('title', proj.get('name', ''))
                        description = proj.get('description', '')
                        technologies = proj.get('technologies', [])
                        
                        if title:
                            context_parts.append(f"- {title}")
                            if description:
                                context_parts.append(f"  {description}")
                            if technologies:
                                tech_str = ', '.join([str(t) for t in technologies]) if isinstance(technologies, list) else str(technologies)
                                context_parts.append(f"  Technologies: {tech_str}")
                    elif isinstance(proj, str):
                        context_parts.append(f"- {proj}")
        
        # Education
        education = resume_data.get('education', [])
        if education:
            context_parts.append("\nEDUCATION:")
            for edu in education:
                if isinstance(edu, dict):
                    degree = edu.get('degree', '')
                    institution = edu.get('institution', '')
                    year = edu.get('year', '')
                    gpa = edu.get('gpa', '')
                    context_parts.append(f"- {degree} from {institution} ({year}) {f'GPA: {gpa}' if gpa else ''}")
                elif isinstance(edu, str):
                    context_parts.append(f"- {edu}")
        
        # Certifications
        certifications = resume_data.get('certifications', [])
        if certifications:
            context_parts.append("\nCERTIFICATIONS & ACHIEVEMENTS:")
            if isinstance(certifications, list):
                for cert in certifications:
                    context_parts.append(f"- {cert}")
            else:
                context_parts.append(f"- {certifications}")
        
        # Co-curricular & Extra-curricular
        activities = resume_data.get('activities', resume_data.get('extracurricular', []))
        if activities:
            context_parts.append("\nCO-CURRICULAR & EXTRACURRICULAR:")
            if isinstance(activities, list):
                for activity in activities:
                    context_parts.append(f"- {activity}")
            else:
                context_parts.append(f"- {activities}")
        
        # Summary
        summary = resume_data.get('summary', '')
        if summary:
            context_parts.append(f"\nCURRENT SUMMARY: {summary}")
        
        return '\n'.join(context_parts)
    
    def _create_gemini_prompt(
        self,
        resume_context: str,
        job_description: str,
        job_title: str
    ) -> str:
        """
        Create a comprehensive prompt for Gemini
        """
        prompt = f"""You are an expert resume writer and career coach. Your task is to create a tailored, ATS-optimized resume for a specific job application.

ORIGINAL RESUME DATA:
{resume_context}

TARGET JOB:
Title: {job_title}
Description: {job_description}

YOUR TASK:
Analyze the candidate's background and the job requirements, then generate tailored resume content in JSON format.

INSTRUCTIONS:
1. Create a compelling professional summary (4-5 sentences) that:
   - Highlights the candidate's most relevant skills and experience for THIS specific job
   - Uses keywords from the job description naturally
   - Emphasizes both technical skills and practical experience
   - Shows clear value proposition for the employer
   - Sounds professional, confident, and achievement-oriented
   - If candidate is a student/recent graduate, emphasize learning ability and hands-on projects

2. Prioritize and organize skills:
   - HIGH PRIORITY: Skills that directly match job requirements (list 6-10)
   - MEDIUM PRIORITY: Related/transferable skills (list 4-8)
   - LOW PRIORITY: Other skills that are less relevant (list up to 5)

3. For EACH work experience entry, create 3-4 achievement-focused bullet points that:
   - Start with strong action verbs (Developed, Implemented, Designed, Led, Built, Achieved, etc.)
   - Include specific technologies, tools, and methodologies used
   - Quantify results whenever possible (percentages, numbers, metrics)
   - Show impact and value delivered
   - Are detailed and substantial (20-40 words each)
   - Follow the STAR format (Situation, Task, Action, Result)
   - Use technical terminology from the job description
   - For internships, emphasize learning, contribution, and growth

4. Optimize job titles:
   - If the original title is vague (e.g., "Intern"), enhance it to be more specific (e.g., "AI/ML Engineering Intern")
   - Keep the essence of the original role
   - Make it more professional and descriptive

CRITICAL REQUIREMENTS:
- Only use information from the original resume - DO NOT invent experience, achievements, or skills
- If experience descriptions are minimal, create detailed professional bullets based on typical responsibilities for that role and company
- For students/interns, focus on projects completed, technologies learned, and contributions made
- Keep the tone professional but confident
- Use industry-standard terminology from the job description
- Each bullet point should be substantial and detailed (aim for 20-40 words)
- Ensure all content is ATS-friendly

EXAMPLE OF GOOD BULLET POINTS:
❌ BAD: "Worked on machine learning projects"
✅ GOOD: "Developed and deployed machine learning models using Python and TensorFlow, achieving 91% anomaly detection accuracy through implementation of autoencoder-based architecture trained on 10,000+ image samples"

❌ BAD: "Built a chatbot"
✅ GOOD: "Created a retrieval-based chatbot leveraging LangChain and Gemini API with FAISS indexing and PostgreSQL integration, enabling semantic search across thousands of document chunks with real-time context-sensitive responses"

OUTPUT FORMAT (JSON):
{{
  "professional_summary": "Your tailored 4-5 sentence summary here that emphasizes both skills and experience...",
  "skills": {{
    "high_priority": ["skill1", "skill2", "skill3", ...],
    "medium_priority": ["skill4", "skill5", ...],
    "low_priority": ["skill6", "skill7", ...]
  }},
  "experience": [
    {{
      "original_role": "Intern",
      "optimized_role": "AI/ML Engineering Intern",
      "company": "Company Name",
      "duration": "April 2025 - June 2025",
      "achievements": [
        "Detailed 20-40 word achievement bullet point with specific technologies, metrics, and impact...",
        "Another substantial achievement describing technical work, tools used, and results achieved...",
        "Third achievement highlighting collaboration, learning, or specific project contributions..."
      ],
      "relevance": "high"
    }}
  ],
  "projects": [
    {{
      "title": "Project Name",
      "description": "Brief 1-2 sentence overview of the project",
      "achievements": [
        "Detailed bullet about implementation and technologies used...",
        "Another bullet about results, metrics, or impact..."
      ],
      "technologies": ["Tech1", "Tech2", "Tech3"]
    }}
  ],
  "certifications": [
    "Full certification name and date if available"
  ],
  "activities": [
    "Co-curricular or extracurricular activity with role/position"
  ]
}}

IMPORTANT: 
- Include ALL projects from the original resume
- Include ALL certifications and achievements
- Include ALL co-curricular/extracurricular activities
- Keep ALL education entries exactly as provided
- Make each achievement bullet DETAILED and SUBSTANTIAL

Generate the JSON now:"""
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict:
        """
        Parse Gemini's JSON response
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without code blocks
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")
            
            # Parse JSON
            content = json.loads(json_str)
            
            # Validate and set defaults for all sections
            if 'professional_summary' not in content:
                content['professional_summary'] = "Motivated professional seeking opportunities to contribute skills and grow."
            
            if 'skills' not in content:
                content['skills'] = {'high_priority': [], 'medium_priority': [], 'low_priority': []}
            
            if 'experience' not in content:
                content['experience'] = []
            
            if 'projects' not in content:
                content['projects'] = []
            
            if 'certifications' not in content:
                content['certifications'] = []
            
            if 'activities' not in content:
                content['activities'] = []
            
            return content
            
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            print(f"Response text: {response_text[:500]}...")
            # Return empty structure
            return {
                'professional_summary': "Motivated professional with diverse skills and experience.",
                'skills': {'high_priority': [], 'medium_priority': [], 'low_priority': []},
                'experience': [],
                'projects': [],
                'certifications': [],
                'activities': []
            }
    
    def _generate_fallback(
        self,
        resume_data: Dict,
        job_description: str,
        job_title: str
    ) -> Dict:
        """
        Enhanced fallback content generation with detailed, professional content
        """
        skills = resume_data.get('skills', [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(',')]
        
        # Extract job keywords for better matching
        job_lower = job_description.lower() if job_description else ''
        
        # Categorize skills based on job description
        high_priority = []
        medium_priority = []
        low_priority = []
        
        # Technical keywords mapping
        tech_categories = {
            'ml_ai': ['machine learning', 'deep learning', 'ai', 'neural network', 'model', 'tensorflow', 'pytorch'],
            'data': ['data', 'analysis', 'analytics', 'sql', 'database', 'postgresql', 'mongodb'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 'docker', 'kubernetes'],
            'web': ['react', 'angular', 'vue', 'javascript', 'frontend', 'backend', 'api', 'rest'],
            'python': ['python', 'django', 'flask', 'fastapi']
        }
        
        for skill in skills:
            skill_lower = str(skill).lower()
            matched = False
            
            # Check if skill matches job description
            if job_lower and skill_lower in job_lower:
                high_priority.append(skill)
                matched = True
            else:
                # Check category relevance
                for category, keywords in tech_categories.items():
                    if any(kw in job_lower for kw in keywords) and any(kw in skill_lower for kw in keywords):
                        if not matched:
                            medium_priority.append(skill)
                            matched = True
                        break
            
            if not matched:
                low_priority.append(skill)
        
        # If no job description, simple prioritization
        if not high_priority and not medium_priority:
            high_priority = skills[:8] if len(skills) >= 8 else skills
            medium_priority = skills[8:15] if len(skills) > 8 else []
            low_priority = skills[15:] if len(skills) > 15 else []
        
        # Generate professional summary
        summary = self._generate_detailed_summary(resume_data, job_title, high_priority)
        
        # Process and enhance experience
        experience_list = []
        experiences = resume_data.get('experience', [])
        
        for idx, exp in enumerate(experiences):
            if isinstance(exp, dict):
                role = exp.get('role', 'Professional')
                company = exp.get('company', 'Company')
                duration = exp.get('duration', '')
                description = exp.get('description', '')
                
                # Generate detailed achievements
                achievements = self._generate_achievement_bullets(
                    role, company, description, high_priority, job_title
                )
                
                # Determine relevance
                role_lower = role.lower()
                relevance = 'medium'
                if any(skill.lower() in role_lower for skill in high_priority[:5]):
                    relevance = 'high'
                elif 'intern' in role_lower and idx > 0:
                    relevance = 'medium'
                
                experience_list.append({
                    'original_role': role,
                    'optimized_role': self._optimize_role_title(role, job_title),
                    'company': company,
                    'duration': duration,
                    'achievements': achievements,
                    'relevance': relevance
                })
        
        return {
            'professional_summary': summary,
            'skills': {
                'high_priority': high_priority,
                'medium_priority': medium_priority,
                'low_priority': low_priority
            },
            'experience': experience_list,
            'projects': self._extract_projects(resume_data),
            'certifications': resume_data.get('certifications', []),
            'activities': resume_data.get('activities', resume_data.get('extracurricular', [])),
        }
    
    def _extract_projects(self, resume_data: Dict) -> List[Dict]:
        """Extract and format projects from resume data"""
        projects = resume_data.get('projects', [])
        if not projects:
            return []
        
        formatted_projects = []
        for proj in projects:
            if isinstance(proj, dict):
                formatted_projects.append({
                    'title': proj.get('title', proj.get('name', 'Project')),
                    'description': proj.get('description', ''),
                    'achievements': proj.get('achievements', [proj.get('description', '')]) if proj.get('description') else [],
                    'technologies': proj.get('technologies', [])
                })
            elif isinstance(proj, str):
                formatted_projects.append({
                    'title': proj,
                    'description': '',
                    'achievements': [],
                    'technologies': []
                })
        
        return formatted_projects
    
    def _generate_detailed_summary(self, resume_data: Dict, job_title: str, top_skills: List) -> str:
        """Generate a detailed, professional summary"""
        education = resume_data.get('education', [])
        experience = resume_data.get('experience', [])
        
        # Determine career stage
        is_student = any('b.tech' in str(edu).lower() or 'bachelor' in str(edu).lower() for edu in education)
        has_experience = len(experience) > 0
        
        # Build summary based on profile
        if is_student and has_experience:
            skills_str = ', '.join([str(s) for s in top_skills[:4]])
            return (
                f"Results-oriented AI/ML undergraduate with hands-on experience in {skills_str}. "
                f"Demonstrated ability to develop and deploy production-ready solutions through multiple internships. "
                f"Strong foundation in both theoretical concepts and practical implementation, with proven track record "
                f"in building scalable systems and delivering measurable results. Seeking opportunities to leverage "
                f"technical expertise and contribute to innovative {job_title} projects."
            )
        elif is_student:
            skills_str = ', '.join([str(s) for s in top_skills[:4]])
            return (
                f"Motivated {job_title} with strong academic foundation in {skills_str}. "
                f"Passionate about applying cutting-edge technologies to solve real-world problems. "
                f"Quick learner with excellent problem-solving abilities and eagerness to contribute "
                f"to innovative projects while continuing to grow professionally."
            )
        elif has_experience:
            skills_str = ', '.join([str(s) for s in top_skills[:4]])
            return (
                f"Experienced {job_title} specializing in {skills_str}. "
                f"Proven track record of delivering high-quality solutions and driving technical excellence. "
                f"Strong analytical and problem-solving skills with ability to translate complex requirements "
                f"into scalable, production-ready systems."
            )
        else:
            return (
                f"Dedicated professional seeking opportunities in {job_title}. "
                f"Strong technical foundation with commitment to continuous learning and excellence."
            )
    
    def _generate_achievement_bullets(
        self, 
        role: str, 
        company: str, 
        description: str,
        skills: List,
        job_title: str
    ) -> List[str]:
        """Generate detailed achievement-focused bullet points"""
        bullets = []
        
        # Use existing description if available and detailed
        if description and len(description) > 50:
            # Split description into bullets if not already
            if '•' in description or '-' in description:
                desc_bullets = [b.strip() for b in description.replace('•', '-').split('-') if b.strip()]
                return desc_bullets[:4]
            else:
                # Use as single achievement
                bullets.append(description)
        
        # Generate based on role type
        role_lower = role.lower()
        
        # ML/AI roles
        if any(kw in role_lower for kw in ['ml', 'ai', 'machine learning', 'data scien', 'research']):
            bullets.extend([
                f"Developed and implemented machine learning models using {skills[0] if skills else 'Python'} and industry-standard frameworks, achieving significant improvements in prediction accuracy and system performance",
                f"Conducted comprehensive data analysis and feature engineering on large-scale datasets, extracting actionable insights that directly informed product development and business decisions",
                f"Collaborated with cross-functional teams to integrate ML solutions into production environments, ensuring scalability, reliability, and optimal performance"
            ])
        
        # Software Engineering roles
        elif any(kw in role_lower for kw in ['software', 'developer', 'engineer', 'full stack', 'backend', 'frontend']):
            bullets.extend([
                f"Designed and developed scalable software solutions using modern technologies including {', '.join([str(s) for s in skills[:2]]) if skills else 'various frameworks'}, following industry best practices and design patterns",
                f"Implemented robust RESTful APIs and database architectures, optimizing query performance and ensuring data integrity across distributed systems",
                f"Participated in code reviews, testing, and deployment processes, contributing to continuous integration/continuous deployment (CI/CD) pipelines"
            ])
        
        # Data roles
        elif any(kw in role_lower for kw in ['data', 'analyst', 'analytics']):
            bullets.extend([
                f"Performed in-depth data analysis using SQL, Python, and statistical methods to identify trends, patterns, and opportunities for process improvement",
                f"Created comprehensive data visualizations and dashboards to communicate insights to stakeholders and support data-driven decision making",
                f"Developed automated data pipelines and ETL processes, improving data quality and reducing manual processing time by significant margins"
            ])
        
        # Internship roles
        elif 'intern' in role_lower:
            bullets.extend([
                f"Contributed to {company}'s core projects by developing features and solving technical challenges using {skills[0] if skills else 'modern technologies'}",
                f"Collaborated with senior engineers on design and implementation of scalable solutions, gaining hands-on experience with production systems",
                f"Participated in agile development processes including daily standups, sprint planning, and code reviews, demonstrating strong teamwork and communication skills"
            ])
        
        # Generic professional role
        else:
            bullets.extend([
                f"Led technical initiatives and collaborated with team members to deliver high-quality solutions aligned with business objectives",
                f"Implemented best practices in software development, testing, and deployment, ensuring code quality and system reliability",
                f"Contributed to process improvements and knowledge sharing, mentoring junior team members and documenting technical procedures"
            ])
        
        # Limit to 3-4 bullets
        return bullets[:4] if bullets else [
            f"Contributed to team success and project delivery at {company}, applying technical skills and problem-solving abilities",
            f"Collaborated with cross-functional teams to achieve project goals and meet deadlines",
            f"Gained valuable hands-on experience with industry-standard tools and methodologies"
        ]
    
    def _optimize_role_title(self, original_role: str, job_title: str) -> str:
        """Optimize role title for better presentation"""
        role_lower = original_role.lower()
        
        # If already detailed, keep it
        if len(original_role.split()) >= 3:
            return original_role
        
        # Add context based on keywords
        if 'intern' in role_lower:
            if any(kw in role_lower for kw in ['ml', 'ai', 'machine learning']):
                return original_role.replace('Intern', 'AI/ML Engineering Intern')
            elif any(kw in role_lower for kw in ['data', 'analyst']):
                return original_role.replace('Intern', 'Data Engineering Intern')
            elif any(kw in role_lower for kw in ['software', 'developer', 'full stack']):
                return original_role.replace('Intern', 'Software Engineering Intern')
        
        return original_role
    
    def _generate_html(
        self,
        resume_data: Dict,
        tailored_content: Dict,
        style_config: Dict,
        job_title: str
    ) -> str:
        """
        Generate HTML resume from tailored content with ALL sections
        """
        # Extract data
        name = str(resume_data.get('name', 'Your Name')).strip()
        email = str(resume_data.get('email', 'email@example.com')).strip()
        phone = str(resume_data.get('phone', 'Phone')).strip()
        
        summary = tailored_content.get('professional_summary', '')
        skills = tailored_content.get('skills', {})
        experience = tailored_content.get('experience', [])
        projects = tailored_content.get('projects', [])
        certifications = tailored_content.get('certifications', [])
        activities = tailored_content.get('activities', [])
        
        # Generate sections HTML
        skills_html = self._generate_skills_html(skills, style_config['accent_color'])
        experience_html = self._generate_experience_html(experience, style_config['accent_color'])
        projects_html = self._generate_projects_html(projects, style_config['accent_color'])
        education_html = self._generate_education_html(resume_data.get('education', []), style_config['accent_color'])
        certifications_html = self._generate_certifications_html(certifications, style_config['accent_color'])
        activities_html = self._generate_activities_html(activities, style_config['accent_color'])
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - {job_title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: {style_config['font']};
            line-height: 1.6;
            color: #333;
            max-width: 8.5in;
            margin: 0 auto;
            padding: 0.5in;
            background: white;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 3px solid {style_config['accent_color']};
        }}
        
        .name {{
            font-size: 2.5rem;
            font-weight: bold;
            color: {style_config['accent_color']};
            margin-bottom: 0.5rem;
        }}
        
        .contact {{
            font-size: 0.95rem;
            color: #666;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }}
        
        .contact-divider {{
            color: #ccc;
        }}
        
        .section {{
            margin-bottom: 1.5rem;
            page-break-inside: avoid;
        }}
        
        .section-title {{
            font-size: 1.2rem;
            font-weight: bold;
            color: {style_config['accent_color']};
            margin-bottom: 0.7rem;
            padding-bottom: 0.25rem;
            border-bottom: 2px solid {style_config['accent_color']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .summary {{
            font-size: 0.95rem;
            line-height: 1.7;
            color: #444;
            text-align: justify;
        }}
        
        .skills {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        
        .skill {{
            padding: 0.4rem 0.9rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 500;
        }}
        
        .skill-high {{
            background: {style_config['accent_color']};
            color: white;
            border: 2px solid {style_config['accent_color']};
            font-weight: 600;
        }}
        
        .skill-medium {{
            background: white;
            color: {style_config['accent_color']};
            border: 2px solid {style_config['accent_color']};
        }}
        
        .skill-low {{
            background: #f5f5f5;
            color: #999;
            border: 1px solid #ddd;
        }}
        
        .experience-item, .project-item {{
            margin-bottom: 1.2rem;
            padding: 0.9rem;
            border-radius: 8px;
            page-break-inside: avoid;
        }}
        
        .exp-high {{
            background: #f0f8ff;
            border-left: 4px solid {style_config['accent_color']};
        }}
        
        .exp-medium {{
            background: #fafafa;
            border-left: 4px solid #ccc;
        }}
        
        .exp-low {{
            background: white;
            border-left: 4px solid #eee;
        }}
        
        .project-item {{
            background: #f9fafb;
            border-left: 4px solid {style_config['accent_color']};
        }}
        
        .item-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.6rem;
        }}
        
        .item-title {{
            font-weight: bold;
            font-size: 1.05rem;
            color: #222;
        }}
        
        .item-subtitle {{
            color: #666;
            font-style: italic;
            font-size: 0.9rem;
            margin-top: 0.2rem;
        }}
        
        .item-duration {{
            color: #888;
            font-size: 0.85rem;
            white-space: nowrap;
        }}
        
        .achievements {{
            list-style: none;
            padding-left: 0;
        }}
        
        .achievements li {{
            position: relative;
            padding-left: 1.3rem;
            margin-bottom: 0.4rem;
            color: #555;
            line-height: 1.5;
            font-size: 0.9rem;
        }}
        
        .achievements li:before {{
            content: "▸";
            position: absolute;
            left: 0;
            color: {style_config['accent_color']};
            font-weight: bold;
        }}
        
        .technologies {{
            margin-top: 0.5rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
        }}
        
        .tech-badge {{
            background: {style_config['accent_color']}20;
            color: {style_config['accent_color']};
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .education-item {{
            margin-bottom: 0.9rem;
            padding: 0.7rem;
            background: #fafafa;
            border-radius: 6px;
            border-left: 3px solid {style_config['accent_color']};
        }}
        
        .edu-title {{
            font-weight: 600;
            color: #333;
            font-size: 1rem;
        }}
        
        .edu-institution {{
            color: #666;
            font-size: 0.9rem;
            margin-top: 0.2rem;
        }}
        
        .edu-details {{
            color: #888;
            font-size: 0.85rem;
            margin-top: 0.2rem;
        }}
        
        .cert-item, .activity-item {{
            position: relative;
            padding-left: 1.3rem;
            margin-bottom: 0.5rem;
            color: #555;
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        
        .cert-item:before, .activity-item:before {{
            content: "▸";
            position: absolute;
            left: 0;
            color: {style_config['accent_color']};
            font-weight: bold;
        }}
        
        @media print {{
            body {{ padding: 0.3in; }}
            .section {{ page-break-inside: avoid; }}
            .experience-item, .project-item {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="name">{self._escape_html(name)}</div>
        <div class="contact">
            <span>{self._escape_html(email)}</span>
            <span class="contact-divider">|</span>
            <span>{self._escape_html(phone)}</span>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">Professional Summary</div>
        <div class="summary">{self._escape_html(summary)}</div>
    </div>
    
    {f'''<div class="section">
        <div class="section-title">Technical Skills</div>
        <div class="skills">{skills_html}</div>
    </div>''' if skills_html else ''}
    
    {f'''<div class="section">
        <div class="section-title">Work Experience</div>
        {experience_html}
    </div>''' if experience_html else ''}
    
    {f'''<div class="section">
        <div class="section-title">Projects</div>
        {projects_html}
    </div>''' if projects_html else ''}
    
    {f'''<div class="section">
        <div class="section-title">Education</div>
        {education_html}
    </div>''' if education_html else ''}
    
    {f'''<div class="section">
        <div class="section-title">Certifications & Achievements</div>
        {certifications_html}
    </div>''' if certifications_html else ''}
    
    {f'''<div class="section">
        <div class="section-title">Co-Curricular & Extracurricular</div>
        {activities_html}
    </div>''' if activities_html else ''}
</body>
</html>
"""
        return html
    
    def _generate_skills_html(self, skills: Dict, accent_color: str) -> str:
        """Generate HTML for skills section"""
        html_parts = []
        
        # High priority skills
        for skill in skills.get('high_priority', []):
            html_parts.append(f'<span class="skill skill-high">{self._escape_html(str(skill))}</span>')
        
        # Medium priority skills
        for skill in skills.get('medium_priority', []):
            html_parts.append(f'<span class="skill skill-medium">{self._escape_html(str(skill))}</span>')
        
        # Low priority skills
        for skill in skills.get('low_priority', [])[:10]:
            html_parts.append(f'<span class="skill skill-low">{self._escape_html(str(skill))}</span>')
        
        return '\n            '.join(html_parts)
    
    def _generate_experience_html(self, experience: List[Dict], accent_color: str) -> str:
        """Generate HTML for experience section"""
        html_parts = []
        
        for exp in experience:
            role = exp.get('optimized_role', exp.get('original_role', 'Role'))
            company = exp.get('company', 'Company')
            duration = exp.get('duration', '')
            achievements = exp.get('achievements', [])
            relevance = exp.get('relevance', 'medium')
            
            achievements_html = '\n                '.join([
                f'<li>{self._escape_html(str(ach))}</li>'
                for ach in achievements
            ])
            
            html_parts.append(f'''
        <div class="experience-item exp-{relevance}">
            <div class="exp-header">
                <div>
                    <div class="exp-title">{self._escape_html(role)}</div>
                    <div class="exp-company">{self._escape_html(company)}</div>
                </div>
                {f'<div class="exp-duration">{self._escape_html(duration)}</div>' if duration else ''}
            </div>
            <ul class="achievements">
                {achievements_html}
            </ul>
        </div>
            ''')
        
        return '\n'.join(html_parts)
    
    def _generate_education_html(self, education: List, accent_color: str) -> str:
        """Generate HTML for education section - preserves ALL original content"""
        html_parts = []
        
        for edu in education:
            if isinstance(edu, dict):
                degree = str(edu.get('degree', '')).strip()
                field = str(edu.get('field', '')).strip()
                institution = str(edu.get('institution', '')).strip()
                year = str(edu.get('year', '')).strip()
                gpa = str(edu.get('gpa', '')).strip()
                percentage = str(edu.get('percentage', '')).strip()
                
                # Build title
                title_parts = []
                if degree:
                    title_parts.append(degree.upper() if len(degree) <= 6 else degree.title())
                if field:
                    title_parts.append(f"in {field}")
                
                edu_title = ' '.join(title_parts) if title_parts else 'Degree'
                
                # Build details
                details_parts = []
                if year:
                    details_parts.append(year)
                if gpa:
                    details_parts.append(f"GPA: {gpa}")
                if percentage:
                    details_parts.append(f"Percentage: {percentage}")
                
                html_parts.append(f'''
        <div class="education-item">
            <div class="edu-title">{self._escape_html(edu_title)}</div>
            {f'<div class="edu-institution">{self._escape_html(institution)}</div>' if institution else ''}
            {f'<div class="edu-details">{self._escape_html(" | ".join(details_parts))}</div>' if details_parts else ''}
        </div>
                ''')
            elif isinstance(edu, str):
                html_parts.append(f'''
        <div class="education-item">
            <div class="edu-title">{self._escape_html(str(edu))}</div>
        </div>
                ''')
        
        return '\n'.join(html_parts)
    
    def _generate_projects_html(self, projects: List, accent_color: str) -> str:
        """Generate HTML for projects section"""
        if not projects:
            return ''
        
        html_parts = []
        
        for proj in projects:
            if isinstance(proj, dict):
                title = proj.get('title', proj.get('name', 'Project'))
                description = proj.get('description', '')
                achievements = proj.get('achievements', [])
                technologies = proj.get('technologies', [])
                
                # If no achievements but has description, use description as achievement
                if not achievements and description:
                    achievements = [description]
                
                achievements_html = ''
                if achievements:
                    achievements_html = '<ul class="achievements">\n'
                    for ach in achievements:
                        achievements_html += f'                <li>{self._escape_html(str(ach))}</li>\n'
                    achievements_html += '            </ul>'
                
                tech_html = ''
                if technologies:
                    tech_list = technologies if isinstance(technologies, list) else [technologies]
                    tech_html = '<div class="technologies">\n'
                    for tech in tech_list:
                        tech_html += f'                <span class="tech-badge">{self._escape_html(str(tech))}</span>\n'
                    tech_html += '            </div>'
                
                html_parts.append(f'''
        <div class="project-item">
            <div class="item-header">
                <div>
                    <div class="item-title">{self._escape_html(title)}</div>
                </div>
            </div>
            {achievements_html}
            {tech_html}
        </div>
                ''')
            elif isinstance(proj, str):
                html_parts.append(f'''
        <div class="project-item">
            <div class="item-title">{self._escape_html(str(proj))}</div>
        </div>
                ''')
        
        return '\n'.join(html_parts)
    
    def _generate_certifications_html(self, certifications: List, accent_color: str) -> str:
        """Generate HTML for certifications section"""
        if not certifications:
            return ''
        
        html_parts = []
        cert_list = certifications if isinstance(certifications, list) else [certifications]
        
        for cert in cert_list:
            html_parts.append(f'        <div class="cert-item">{self._escape_html(str(cert))}</div>')
        
        return '\n'.join(html_parts)
    
    def _generate_activities_html(self, activities: List, accent_color: str) -> str:
        """Generate HTML for co-curricular and extracurricular activities"""
        if not activities:
            return ''
        
        html_parts = []
        activity_list = activities if isinstance(activities, list) else [activities]
        
        for activity in activity_list:
            html_parts.append(f'        <div class="activity-item">{self._escape_html(str(activity))}</div>')
        
        return '\n'.join(html_parts)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if not text:
            return ''
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#39;')
        return text


# Helper function for Flask route
def generate_resume_for_job(
    resume_data: Dict,
    job_description: str,
    job_title: str,
    style: str = 'professional'
) -> Dict:
    """
    Main function to generate tailored resume using Gemini
    """
    generator = GeminiResumeGenerator()
    return generator.generate_tailored_resume(
        resume_data,
        job_description,
        job_title,
        style
    )


def get_available_styles() -> Dict:
    """Get all available resume styles"""
    return GeminiResumeGenerator.STYLES