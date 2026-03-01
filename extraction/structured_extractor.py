"""
Structured Resume Extraction Module
Production-ready extraction using rule-based patterns + NLP
More accurate and reliable than LLM-only approaches
"""
import re
from typing import Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class ContactInfo:
    name: str = ""
    email: str = ""
    phone: str = ""

@dataclass
class EducationEntry:
    degree: str = ""
    institution: str = ""
    field: str = ""
    year: str = ""
    gpa: str = ""

@dataclass
class ExperienceEntry:
    role: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    duration_years: float = 0.0

@dataclass
class SkillEntry:
    name: str = ""
    category: str = ""  # programming, framework, tool, soft_skill
    proficiency: str = ""  # beginner, intermediate, advanced, expert

class StructuredResumeExtractor:
    """Production-grade resume extractor using deterministic rules + patterns"""
    
    def __init__(self):
        # Comprehensive patterns compiled once
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            re.IGNORECASE
        )
        
        self.phone_patterns = [
            re.compile(r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            re.compile(r'\d{10}'),
            re.compile(r'\(\d{3}\)\s?\d{3}[-.]?\d{4}'),
            re.compile(r'\d{3}[-.]\d{3}[-.]\d{4}'),
        ]
        
        # Name detection patterns
        self.name_keywords = ['resume', 'cv', 'curriculum vitae', 'phone', 'email', 'mobile', 'address']
        
        # Skills database
        self.skills_database = {
            'programming': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'go', 'rust', 
                'ruby', 'php', 'swift', 'kotlin', 'r', 'scala', 'perl', 'matlab', 'dart'
            ],
            'framework': [
                'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'asp.net',
                'laravel', 'express', 'next.js', 'nuxt', 'svelte', 'ember', 'backbone'
            ],
            'database': [
                'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite', 'cassandra',
                'elasticsearch', 'dynamodb', 'neo4j', 'mariadb', 'couchdb'
            ],
            'cloud': [
                'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'jenkins',
                'terraform', 'ansible', 'ci/cd', 'devops', 'cloudformation'
            ],
            'ml_ai': [
                'machine learning', 'deep learning', 'ai', 'tensorflow', 'pytorch', 'keras',
                'scikit-learn', 'pandas', 'numpy', 'opencv', 'nlp', 'computer vision'
            ],
            'tools': [
                'git', 'github', 'gitlab', 'jira', 'confluence', 'agile', 'scrum', 'linux',
                'unix', 'bash', 'powershell', 'vim', 'vscode', 'intellij', 'eclipse'
            ]
        }
        # Canonical skill synonyms/variants
        self.skill_synonyms = {
            'py': 'python',
            'python3': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'node': 'node.js',
            'nodejs': 'node.js',
            'reactjs': 'react',
            'react.js': 'react',
            'vuejs': 'vue',
            'vue.js': 'vue',
            'html5': 'html',
            'css3': 'css',
            'gcloud': 'gcp',
            'google cloud platform': 'gcp',
            'postgres': 'postgresql',
            'postgresql': 'postgresql',
            'aws cloud': 'aws',
            'azure cloud': 'azure',
            'ms sql': 'sql',
            'mysql server': 'mysql'
        }
        
        # Education degree patterns
        self.degree_patterns = [
            re.compile(r'(?:Bachelor|B\.S\.|B\.A\.|B\.Sc\.|B\.Tech\.|B\.E\.|B\.Eng\.|BS|BA)\s+(?:of|in)?\s*(?:Science|Arts|Engineering|Technology|Business|Commerce|Computer Science|Information Technology|Electronics)?', re.IGNORECASE),
            re.compile(r'(?:Master|M\.S\.|M\.A\.|M\.Tech\.|M\.E\.|M\.Sc\.|MS|MA|MBA|M\.Sc)\s+(?:of|in)?\s*(?:Science|Arts|Engineering|Technology|Business|Computer Science)?', re.IGNORECASE),
            re.compile(r'(?:PhD|Ph\.D\.|Doctorate|Doctoral)\s+(?:in|of)?', re.IGNORECASE),
            re.compile(r'(?:Diploma|Certificate|Associate)\s+(?:in|of)?', re.IGNORECASE),
            re.compile(r'(?:BCA|MCA|BBA|MBA|B\.Com|M\.Com|BSc|MSc|B\.Pharm|M\.Pharm)', re.IGNORECASE),
            re.compile(r'\b(BE|ME|BTech|MTech|BSc|MSc|BEng|MEng|B\.E\.|M\.E\.)\b', re.IGNORECASE),
            re.compile(r'(?:Bachelor\s+of\s+Technology|Bachelor\s+of\s+Engineering|B\s*Tech|B\s*E)', re.IGNORECASE),
        ]
        
        # Institution patterns
        self.institution_patterns = [
            re.compile(r'([A-Z][A-Za-z\s&]+(?:University|College|Institute|School|Univ\.|Uni\.|IIT|NIT|IIM))', re.IGNORECASE),
        ]
        
        # Date patterns
        self.date_patterns = [
            re.compile(r'(\d{1,2})[/-](\d{1,2})?[/-]?(\d{4})'),  # MM/YYYY or DD/MM/YYYY
            re.compile(r'(\w+)\s+(\d{4})'),  # Month YYYY
            re.compile(r'(\d{4})'),  # Just year
        ]

    def _normalize_text(self, text: str) -> str:
        """Normalize bullets/whitespace while keeping structure."""
        if not text:
            return ""
        
        # Replace common PDF artifacts and mangled characters
        cleaned = text.replace('\r', '\n')
        # Handle 'û' (often a dash in PDFs)
        cleaned = cleaned.replace('\xfb', '-') 
        # Handle other artifacts
        cleaned = re.sub(r'[\u2022\u2023\u25E6\u2043\u2219•ûÆÖ§]', ', ', cleaned)
        
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()

    def _canonical_skill(self, skill: str) -> str:
        """Lowercase, map synonyms, and title-case for output."""
        if not skill:
            return ""
        s = skill.strip().lower()
        s = self.skill_synonyms.get(s, s)
        return s.title()
    
    def extract_contact_info(self, text: str) -> ContactInfo:
        """Extract contact information with high accuracy"""
        contact = ContactInfo()
        lines = text.split('\n')
        
        # Extract email
        emails = self.email_pattern.findall(text)
        if emails:
            contact.email = emails[0].lower()
        
        # Extract phone
        for pattern in self.phone_patterns:
            phones = pattern.findall(text)
            if phones:
                # Clean phone number
                phone = re.sub(r'[^\d+]', '', phones[0])
                if len(phone) >= 10:
                    contact.phone = phone[:15]  # Limit length
                    break
        
        # Extract name (usually first substantial line)
        for i, line in enumerate(lines[:15]):  # Check first 15 lines
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Skip common non-name patterns
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in self.name_keywords):
                continue
            
            # Skip if contains email/phone/URL
            if '@' in line or 'http' in line_lower or len(self.phone_patterns[0].findall(line)) > 0:
                continue
            
            # Name should be 2-4 words, mostly alphabetic
            words = line.split()
            if 2 <= len(words) <= 4:
                # Check if mostly alphabetic
                alpha_chars = sum(1 for c in line if c.isalpha())
                if alpha_chars / max(len(line), 1) > 0.7:  # 70% alphabetic
                    if 5 <= len(line) <= 60:
                        contact.name = line
                        break
        
        return contact
    
    def extract_skills(self, text: str) -> List[SkillEntry]:
        """Extract skills using pattern matching + database lookup"""
        skills = []
        text_lower = text.lower()
        
        # Find skills section with or without trailing colon
        skills_section_patterns = [
            r'(?:skills?|technical skills?|technologies?|competencies?|proficiencies?|expertise)\s*:?\s*(.+?)(?:\n\n|\n(?=[A-Z][A-Za-z ]{2,}:)|\n(?=[A-Z]{3,}\b)|$)',
            r'(?:core competencies?|key skills?)\s*:?\s*(.+?)(?:\n\n|\n(?=[A-Z][A-Za-z ]{2,}:)|\n(?=[A-Z]{3,}\b)|$)',
        ]
        
        skills_text = ""
        for pattern in skills_section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                skills_text = match.group(1)
                break
        
        # ALWAYS search entire text for skills (not just section)
        # This ensures we catch skills mentioned in experience/projects
        search_text = text  # Search entire resume
        
        # Extract skills from database - search entire text
        found_skill_names = set()
        for category, skill_list in self.skills_database.items():
            for skill in skill_list:
                # Use word boundaries for exact matches, but also allow partial matches in context
                # Try exact match first
                pattern_exact = r'\b' + re.escape(skill.lower()) + r'\b'
                # Also try case-insensitive partial match for common skills
                pattern_partial = re.escape(skill.lower())
                
                if re.search(pattern_exact, search_text.lower()):
                    canonical = self._canonical_skill(skill)
                    if canonical.lower() not in found_skill_names:
                        skills.append(SkillEntry(name=canonical, category=category))
                        found_skill_names.add(canonical.lower())
        
        # Extract additional skills from dedicated section OR entire text
        # First try the skills section if found
        if skills_text and len(skills_text) > 20:
            # Split by common delimiters
            skill_items = re.split(r'[,;|•\-\n\r\t/]+', skills_text)
            for item in skill_items:
                item = re.sub(r'[•\-\*\d\.\(\)]', '', item).strip()
                if item and len(item) > 1 and len(item) < 50:
                    # Avoid false positives
                    if not any(word in item.lower() for word in 
                              ['years', 'experience', 'proficient', 'skilled', 'expert', 'level', 
                               'working', 'worked', 'utilized', 'used', 'developed']):
                        canonical = self._canonical_skill(item)
                        if canonical.lower() not in found_skill_names:
                            skills.append(SkillEntry(name=canonical, category='other'))
                            found_skill_names.add(canonical.lower())
        
        # Also extract skills mentioned in experience/projects sections
        # Look for patterns like "used Python", "worked with React", "experience with Java"
        skill_context_patterns = [
            r'(?:used|utilized|worked with|experience with|knowledge of|proficient in|skilled in|expert in)\s+([A-Z][A-Za-z\s\+#]+)',
            r'([A-Z][A-Za-z]+(?:\s*\+\s*[A-Z][A-Za-z]+)?)\s+(?:development|programming|framework|technology)',
        ]
        
        for pattern in skill_context_patterns:
            matches = re.finditer(pattern, search_text, re.IGNORECASE)
            for match in matches:
                potential_skill = match.group(1).strip()
                if len(potential_skill) > 2 and len(potential_skill) < 30:
                    # Check if it's a known skill
                    potential_lower = potential_skill.lower()
                    if potential_lower not in found_skill_names:
                        # Check against database
                        found_in_db = False
                        for skill_list in self.skills_database.values():
                            if any(potential_lower == s.lower() for s in skill_list):
                                found_in_db = True
                                break
                        
                        if found_in_db or len(potential_skill.split()) <= 2:
                            canonical = self._canonical_skill(potential_skill)
                            skills.append(SkillEntry(name=canonical, category='other'))
                            found_skill_names.add(canonical.lower())
        
        # Deduplicate and keep stable order
        unique_skills = []
        seen = set()
        for skill in skills:
            key = (skill.name.lower(), skill.category)
            if key not in seen:
                unique_skills.append(skill)
                seen.add(key)
        
        return unique_skills[:30]  # Limit to top 30 skills
    
    def extract_education(self, text: str) -> List[EducationEntry]:
        """Extract education with high precision"""
        education_list = []
        
        # Find education section
        edu_section_pattern = r'(?:education|academic|qualification|degrees?)\s*:?\s*(.+?)(?:\n\n|\n(?=[A-Z][a-z]+\s*:)|\n(?=[A-Z]{3,}\b)|$)'
        edu_section_match = re.search(edu_section_pattern, text, re.IGNORECASE | re.DOTALL)
        
        search_text = edu_section_match.group(1) if edu_section_match else text
        
        # Split into potential entries (by line breaks or double newlines)
        potential_entries = re.split(r'\n\n+|\n(?=[A-Z])', search_text)
        
        for entry_text in potential_entries:
            entry_text = entry_text.strip()
            if len(entry_text) < 10:
                continue
            
            edu = EducationEntry()
            
            # Extract degree
            for pattern in self.degree_patterns:
                match = pattern.search(entry_text, re.IGNORECASE)
                if match:
                    edu.degree = match.group(0).strip()
                    break
            
            # Extract institution
            for pattern in self.institution_patterns:
                match = pattern.search(entry_text, re.IGNORECASE)
                if match:
                    edu.institution = match.group(1).strip()
                    break
            
            # Extract year
            year_match = re.search(r'\b(19|20)\d{2}\b', entry_text)
            if year_match:
                edu.year = year_match.group(0)
            else:
                grad_match = re.search(r'graduat(?:ed|ion)\s*(?:in|:)?\s*(19|20)\d{2}', entry_text, re.IGNORECASE)
                if grad_match:
                    edu.year = grad_match.group(0)[-4:]
            
            # Extract GPA if present
            gpa_match = re.search(r'GPA[:\s]*([0-9]\.[0-9]{1,2})|([0-9]\.[0-9]{1,2})\s*GPA', entry_text, re.IGNORECASE)
            if gpa_match:
                edu.gpa = gpa_match.group(1) or gpa_match.group(2)
            
            # Extract field of study
            field_patterns = [
                r'(?:in|of)\s+([A-Z][A-Za-z\s]+(?:Science|Engineering|Technology|Arts|Business|Commerce))',
                r'(?:major(?:ing)?\s+in|field\s+of\s+study)[:\s]*([A-Za-z\s]+)',
            ]
            for pattern in field_patterns:
                match = re.search(pattern, entry_text, re.IGNORECASE)
                if match:
                    edu.field = match.group(1).strip()
                    break
            
            # Only add if we found at least degree or institution
            if edu.degree or edu.institution:
                education_list.append(edu)
        
        # Deduplicate by degree + institution + year
        deduped = []
        seen = set()
        for edu in education_list:
            key = (edu.degree.lower(), edu.institution.lower(), edu.year)
            if key not in seen:
                deduped.append(edu)
                seen.add(key)
        
        # If nothing found in explicit sections, do a fallback scan across entire text
        if not deduped:
            lines = [ln.strip() for ln in text.split('\n') if len(ln.strip()) > 6]
            for ln in lines:
                for pattern in self.degree_patterns:
                    m = pattern.search(ln)
                    if m:
                        edu = EducationEntry()
                        edu.degree = m.group(0).strip()
                        # Try to capture institution heuristically (preceding or following capitalized tokens)
                        inst_match = re.search(r'([A-Z][A-Za-z&\s]{3,}(University|College|Institute|School|IIT|NIT|IIM))', ln)
                        if inst_match:
                            edu.institution = inst_match.group(1).strip()
                        year_match = re.search(r'\b(19|20)\d{2}\b', ln)
                        if year_match:
                            edu.year = year_match.group(0)
                        else:
                            # Sometimes year appears earlier in the line
                            early_year = re.search(r'(19|20)\d{2}', text)
                            if early_year:
                                edu.year = early_year.group(0)
                        key = (edu.degree.lower(), edu.institution.lower(), edu.year)
                        if key not in seen:
                            deduped.append(edu)
                            seen.add(key)
                        break
        
        return deduped[:5]  # Limit to 5 education entries
    
    def extract_experience(self, text: str) -> List[ExperienceEntry]:
        """Extract ALL work experience entries - handles multi-entry sections correctly."""
        experience_list = []

        # ── 1. Isolate the EXPERIENCE section (stop at next known section heading) ──
        exp_section_re = re.compile(
            r'(?:experience|work\s+experience|employment|professional\s+experience|career|internship[s]?)\s*:?\s*\n'
            r'(.*?)'
            r'(?=\n(?:education|projects?|certifications?|achievements?|technical\s+skills?|skills?|publications?|awards?|'
            r'volunteering|languages?|references?|hobbies|interests?|summary|profile)\s*\n|$)',
            re.IGNORECASE | re.DOTALL
        )
        section_match = exp_section_re.search(text)
        if section_match:
            section_text = section_match.group(1).strip()
        else:
            section_text = text  # fall back to full text

        # ── 2. Split section into individual job blocks ──
        # Strategy: a new job entry starts with a Role title line followed (on the same or next line)
        # by a month+year date range.
        # Pattern anchors: "Job Title    Month YYYY - Month YYYY" or "Job Title\nCompany\nDates"
        job_splitter = re.compile(
            r'(?=(?:[A-Z][A-Za-z/&\s]+)'          # capitalised job title
            r'(?:Intern|Engineer|Developer|Analyst|Manager|Lead|Senior|Junior|Specialist|'
            r'Scientist|Consultant|Officer|Coordinator|Executive|Director|Associate|Architect|'
            r'Programmer|Designer|Researcher|Trainer|Advisor|Head|VP|President|Founder|'
            r'Technician|Support|Representative|Assistant)\b)',
            re.MULTILINE
        )

        blocks = job_splitter.split(section_text)
        # Filter empty/short blocks
        blocks = [b.strip() for b in blocks if len(b.strip()) > 20]

        # If splitter found nothing useful, try splitting by month-year date patterns
        if len(blocks) <= 1:
            # Split on lines that start with a month name + year (new entry indicator)
            date_line_re = re.compile(
                r'(?=(?:January|February|March|April|May|June|July|August|September|October|November|December'
                r'|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
                re.IGNORECASE
            )
            blocks = date_line_re.split(section_text)
            blocks = [b.strip() for b in blocks if len(b.strip()) > 20]

        if not blocks:
            blocks = [section_text]

        # ── 3. Parse each block ──
        month_map = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2,
            'march': 3, 'mar': 3, 'april': 4, 'apr': 4, 'may': 5,
            'june': 6, 'jun': 6, 'july': 7, 'jul': 7, 'august': 8, 'aug': 8,
            'september': 9, 'sep': 9, 'sept': 9, 'october': 10, 'oct': 10,
            'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }

        # Various date-range patterns ordered from most specific to least
        date_range_patterns = [
            # "December 2025 - January 2026" or "Dec 2025 - Jan 2026"
            re.compile(
                r'([A-Za-z]{3,9})\s+(\d{4})\s*[-–—]\s*([A-Za-z]{3,9})\s+(\d{4})',
                re.IGNORECASE
            ),
            # "December 2025 - Present"
            re.compile(
                r'([A-Za-z]{3,9})\s+(\d{4})\s*[-–—]\s*(Present|Current|Now|Till\s+Date)',
                re.IGNORECASE
            ),
            # "2022 - Present" or "2022 – 2025"
            re.compile(
                r'(\d{4})\s*[-–—]\s*(\d{4}|Present|Current|Now)',
                re.IGNORECASE
            ),
        ]

        role_patterns = [
            re.compile(
                r'^([A-Z][A-Za-z/&\s]+'
                r'(?:Intern|Engineer|Developer|Analyst|Manager|Lead|Senior|Junior|Specialist|'
                r'Scientist|Consultant|Officer|Coordinator|Executive|Director|Associate|'
                r'Researcher|Trainer|Advisor|Head|Architect|Programmer|Designer|Representative|Assistant))',
                re.MULTILINE
            ),
            re.compile(
                r'([A-Z][A-Za-z/&\s]+'
                r'(?:Intern|Engineer|Developer|Analyst|Manager|Lead|Senior|Junior|Specialist|Scientist))',
                re.MULTILINE
            ),
        ]

        seen = set()
        for block in blocks[:20]:
            exp = ExperienceEntry()

            # Extract date range
            for dpat in date_range_patterns:
                dm = dpat.search(block)
                if dm:
                    g = dm.groups()
                    if len(g) == 4:  # Month YYYY - Month YYYY
                        exp.start_date = f"{g[0]} {g[1]}"
                        exp.end_date = f"{g[2]} {g[3]}"
                    elif len(g) == 3:  # Month YYYY - Present
                        exp.start_date = f"{g[0]} {g[1]}"
                        exp.end_date = g[2]
                    elif len(g) == 2:  # YYYY - YYYY/Present
                        exp.start_date = g[0]
                        exp.end_date = g[1]
                    break

            # Extract role
            for rpat in role_patterns:
                rm = rpat.search(block)
                if rm:
                    role_text = rm.group(1).strip()
                    # Clean up extra whitespace
                    role_text = re.sub(r'\s+', ' ', role_text)
                    if 3 < len(role_text) < 80:
                        exp.role = role_text
                        break

            # Extract company: look for a line that's a capitalised company name
            # (not a role line, not a date line)
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            for line in lines:
                # Skip the role line itself, skip short lines, skip date lines
                if line == exp.role:
                    continue
                if re.search(r'\d{4}', line):
                    continue
                if len(line) < 4 or len(line) > 80:
                    continue
                # Company-like: mostly capitalized proper nouns
                if re.match(r'^[A-Z][A-Za-z\s&.,\'/()-]{2,}$', line):
                    exp.company = line.strip()
                    break

            # Only keep entries with at least a role OR company, and a date
            if (exp.role or exp.company) and exp.start_date:
                key = (exp.role.lower(), exp.company.lower())
                if key not in seen:
                    seen.add(key)
                    exp.duration_years = self._calculate_duration(exp.start_date, exp.end_date)
                    experience_list.append(exp)

        # ── 4. Final fallback: global date-range scan ──
        if not experience_list:
            for m in re.finditer(
                r'([A-Za-z]{3,9})\s+(\d{4})\s*[-–—]\s*([A-Za-z]{3,9}|Present)\s*(\d{4})?',
                section_text, re.IGNORECASE
            ):
                exp = ExperienceEntry()
                g = m.groups()
                exp.start_date = f"{g[0]} {g[1]}"
                exp.end_date = f"{g[2]} {g[3]}" if g[3] else g[2]
                exp.duration_years = self._calculate_duration(exp.start_date, exp.end_date)
                experience_list.append(exp)
                if len(experience_list) >= 5:
                    break

        return experience_list[:10]


    def _calculate_duration(self, start: str, end: str) -> float:
        """Calculate years of experience from date strings - handles multiple formats exactly as written"""
        if not start:
            return 0.0
        
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        def _norm_year(val: str):
            if not val:
                return None
            val = str(val)
            if len(val) == 2 and val.isdigit():
                num = int(val)
                return 2000 + num if num < 50 else 1900 + num
            if val.isdigit() and len(val) == 4:
                return int(val)
            return None
        
        month_names = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
            'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        
        # Parse start date
        start_year = None
        start_month = 1
        
        # Format: "MM/YYYY" or "M/YYYY"
        mm_yyyy = re.search(r'(\d{1,2})[/-](\d{4})', start)
        if mm_yyyy:
            start_month = int(mm_yyyy.group(1))
            start_year = _norm_year(mm_yyyy.group(2))
        else:
            # Format: "Month YYYY" or "Mon YYYY"
            month_year = re.search(r'([A-Za-z]+)\s+(\d{4})', start, re.IGNORECASE)
            if month_year:
                month_name = month_year.group(1).lower()
                if month_name in month_names:
                    start_month = month_names[month_name]
                    start_year = _norm_year(month_year.group(2))
            else:
                # Format: Just "YYYY"
                year_only = re.search(r'\b(19|20)\d{2}\b', start)
                if year_only:
                    start_year = _norm_year(year_only.group(0))
                    start_month = 1  # Default to January if only year given
        
        if not start_year or start_year > current_year + 1:
            return 0.0
        
        # Parse end date
        end_year = current_year
        end_month = current_month
        
        if end:
            end_lower = end.lower()
            if end_lower in ['present', 'current', 'now', 'till date', 'till now']:
                end_year = current_year
                end_month = current_month
            else:
                # Format: "MM/YYYY" or "M/YYYY"
                mm_yyyy_end = re.search(r'(\d{1,2})[/-](\d{4})', end)
                if mm_yyyy_end:
                    end_month = int(mm_yyyy_end.group(1))
                    norm_end = _norm_year(mm_yyyy_end.group(2))
                    end_year = norm_end if norm_end else end_year
                else:
                    # Format: "Month YYYY" or "Mon YYYY"
                    month_year_end = re.search(r'([A-Za-z]+)\s+(\d{4})', end, re.IGNORECASE)
                    if month_year_end:
                        month_name_end = month_year_end.group(1).lower()
                        if month_name_end in month_names:
                            end_month = month_names[month_name_end]
                            norm_end = _norm_year(month_year_end.group(2))
                            end_year = norm_end if norm_end else end_year
                    else:
                        # Format: Just "YYYY"
                        year_only_end = re.search(r'\b(19|20)\d{2}\b', end)
                        if year_only_end:
                            norm_end = _norm_year(year_only_end.group(0))
                            if norm_end:
                                end_year = norm_end
                            end_month = 12  # Default to December if only year given
        
        # Cap end date to current if future
        if end_year > current_year or (end_year == current_year and end_month > current_month):
            end_year = current_year
            end_month = current_month
        
        # If start is after end (future start), discard
        if start_year > end_year or (start_year == end_year and start_month > end_month):
            return 0.0
        
        # Calculate exact duration (no assumptions beyond defaults for missing month)
        start_total_months = start_year * 12 + start_month
        end_total_months = end_year * 12 + end_month
        total_months = end_total_months - start_total_months
        
        # Return years as float (can be fractional)
        return max(0.0, total_months / 12.0)
    
    def extract_summary(self, text: str) -> str:
        """Extract professional summary/objective"""
        summary_patterns = [
            r'(?:summary|objective|profile|about|professional summary)[:]\s*(.+?)(?:\n\n|\n(?=[A-Z][a-z]+\s*:)|$)',
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                summary = match.group(1).strip()
                # Clean up
                summary = re.sub(r'\s+', ' ', summary)
                return summary[:500]  # Limit length
        
        # Fallback: use first substantial paragraph
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 80 and len(p.strip()) < 500]
        if paragraphs:
            return paragraphs[0]
        
        return ""
    
    def extract_all(self, text: str) -> Dict:
        """Main extraction method - returns structured data"""
        text = self._normalize_text(text)
        result = {
            'name': '',
            'email': '',
            'phone': '',
            'skills': [],
            'education': [],
            'experience': [],
            'summary': ''
        }
        
        # Extract contact info
        contact = self.extract_contact_info(text)
        result['name'] = contact.name
        result['email'] = contact.email
        result['phone'] = contact.phone
        
        # Extract skills
        skills = self.extract_skills(text)
        result['skills'] = [skill.name for skill in skills]
        
        # Extract education
        education = self.extract_education(text)
        result['education'] = [
            {
                'degree': e.degree,
                'institution': e.institution,
                'field': e.field,
                'year': e.year,
                'gpa': e.gpa
            }
            for e in education
        ]
        
        # Extract experience
        experience = self.extract_experience(text)
        result['experience'] = [
            {
                'role': e.role,
                'company': e.company,
                'location': e.location,
                'duration': f"{e.start_date} - {e.end_date}" if e.start_date else "",
                'years': round(e.duration_years, 1)
            }
            for e in experience
        ]
        
        # Extract summary - also look in experience descriptions
        summary = self.extract_summary(text)
        if not summary:
            # Fallback: use first paragraph from experience or projects
            exp_sections = re.findall(r'(?:experience|projects?)[:]\s*(.+?)(?:\n\n|\n(?=[A-Z][a-z]+\s*:)|$)', text, re.IGNORECASE | re.DOTALL)
            if exp_sections:
                first_exp = exp_sections[0]
                # Get first sentence or two
                sentences = re.split(r'[.!?]\s+', first_exp)
                summary = '. '.join(sentences[:2]).strip()
                if summary:
                    summary = summary + '.' if not summary.endswith('.') else summary
        
        result['summary'] = summary[:500] if summary else ""
        
        return result

