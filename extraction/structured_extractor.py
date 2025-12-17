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
        cleaned = text.replace('\r', '\n')
        cleaned = re.sub(r'[\u2022\u2023\u25E6\u2043\u2219•]', ', ', cleaned)  # bullets -> comma to preserve delimiters
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
        """Extract work experience with dates - handles multiple formats, no assumptions"""
        experience_list = []
        
        # Find experience section - allow headings with/without colon
        exp_section_patterns = [
            r'(?:experience|work experience|employment|professional experience|career|work history|positions? held)\s*:?\s*(.+?)(?:\n\n|$)',
        ]
        
        search_text = text
        for pattern in exp_section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                search_text = match.group(1)
                break
        
        # Split into potential job entries by double newlines or clear separators
        # This handles various resume formats
        entry_separators = [
            r'\n\n+',  # Double newline
            r'\n(?=[A-Z][a-z]+\s+(?:at|@|,))',  # Newline before role/company
            r'\n(?=\d{4}\s*[-–—])',  # Newline before date
        ]
        
        # Try to split entries
        entries_text = [search_text]  # Start with full text
        def _normalize_year(year_str: str):
            if not year_str:
                return None
            year_str = str(year_str)
            if len(year_str) == 2 and year_str.isdigit():
                year = int(year_str)
                return 2000 + year if year < 50 else 1900 + year
            if year_str.isdigit():
                return int(year_str)
            return None
        
        for sep in entry_separators:
            new_entries = []
            for entry in entries_text:
                split_entries = re.split(sep, entry)
                new_entries.extend([e.strip() for e in split_entries if len(e.strip()) > 20])
            if len(new_entries) > len(entries_text):
                entries_text = new_entries
                break
        
        # Process each potential entry
        found_positions = set()
        month_names = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
            'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        
        for entry_text in entries_text[:15]:  # Limit to 15 entries
            if len(entry_text) < 15:
                continue
            
            exp = ExperienceEntry()
            
            # Extract dates FIRST (most reliable part)
            date_range_patterns = [
                # "YYYY - YYYY" or "YYYY - Present"
                r'(\d{4})\s*[-–—]\s*(\d{4}|Present|Current|Now|Till Date|Till now)',
                # "YYYY to YYYY/Present"
                r'(\d{4})\s*(?:to|until|till)\s*(\d{4}|Present|Current|Now)',
                # "MM/YYYY - MM/YYYY" or "MM/YYYY - Present"
                r'(\d{1,2})[/-](\d{4})\s*[-–—]\s*(\d{1,2})?[/-]?(\d{4}|Present|Current|Now)?',
                # "Month YYYY - Month YYYY" or "Month YYYY - Present"
                r'([A-Za-z]+)\s+(\d{4})\s*[-–—]\s*([A-Za-z]+)?\s*(\d{4}|Present|Current|Now)?',
                # "Mon'YY - Mon'YY/Present"
                r'([A-Za-z]{3,9})\'?(\d{2,4})\s*[-–—]\s*([A-Za-z]{3,9})?\'?(\d{2,4}|Present|Current|Now)?',
                # "YYYY-YYYY" (no spaces)
                r'(\d{4})[-–—](\d{4})',
            ]
            
            date_found = False
            for pattern in date_range_patterns:
                date_match = re.search(pattern, entry_text, re.IGNORECASE)
                if date_match:
                    groups = date_match.groups()
                    
                    # Pattern 5: "Mon'YY - Mon'YY/Present" (handles 2-digit years)
                    if len(groups) == 4 and groups[0] and groups[1] and re.match(r'[A-Za-z]{3,9}', groups[0]):
                        start_year = _normalize_year(groups[1])
                        if start_year and groups[0].lower() in month_names:
                            exp.start_date = f"{month_names[groups[0].lower()]:02d}/{start_year}"
                            if groups[3]:
                                if str(groups[3]).lower() in ['present', 'current', 'now', 'till date', 'till now']:
                                    end_year = datetime.now().year
                                    end_month = datetime.now().month
                                    exp.end_date = f"{end_month:02d}/{end_year}"
                                else:
                                    end_year = _normalize_year(groups[3])
                                    if end_year and groups[2] and groups[2].lower() in month_names:
                                        exp.end_date = f"{month_names[groups[2].lower()]:02d}/{end_year}"
                                    elif end_year:
                                        exp.end_date = str(end_year)
                            elif groups[2] and groups[2].lower() in month_names:
                                exp.end_date = f"{month_names[groups[2].lower()]:02d}/{start_year}"
                            else:
                                exp.end_date = "Present"
                            date_found = True
                    
                    # Pattern 1: "YYYY - YYYY/Present"
                    if not date_found and len(groups) == 2 and groups[0].isdigit():
                        exp.start_date = groups[0]
                        exp.end_date = groups[1] if groups[1] else "Present"
                        date_found = True
                    
                    # Pattern 2: "MM/YYYY - MM/YYYY/Present"
                    elif not date_found and len(groups) >= 2 and groups[1].isdigit() and len(groups[1]) == 4:
                        if len(groups[0]) <= 2:  # Month
                            exp.start_date = f"{groups[0]}/{groups[1]}"
                            if groups[2] and groups[3]:
                                exp.end_date = f"{groups[2]}/{groups[3]}"
                            elif groups[3]:
                                exp.end_date = groups[3]
                            else:
                                exp.end_date = "Present"
                        else:  # Year first
                            exp.start_date = groups[0]
                            exp.end_date = groups[1] if groups[1] else "Present"
                        date_found = True
                    
                    # Pattern 3: "Month YYYY - Month YYYY/Present"
                    elif not date_found and len(groups) >= 2 and groups[1].isdigit():
                        month = groups[0].lower()
                        if month in month_names:
                            exp.start_date = f"{month_names[month]:02d}/{groups[1]}"
                            if groups[2] and groups[3] and groups[3].isdigit():
                                end_month = groups[2].lower()
                                if end_month in month_names:
                                    exp.end_date = f"{month_names[end_month]:02d}/{groups[3]}"
                                else:
                                    exp.end_date = groups[3]
                            elif groups[3]:
                                exp.end_date = groups[3]
                            else:
                                exp.end_date = "Present"
                            date_found = True
                    
                    # Pattern 4: "YYYY-YYYY" (compact)
                    elif not date_found and len(groups) == 2 and all(g.isdigit() for g in groups):
                        exp.start_date = groups[0]
                        exp.end_date = groups[1]
                        date_found = True
                    
                    if date_found:
                        break
            
            # If no date range found, try to find single dates
            if not date_found:
                # Look for single year mentions
                years = re.findall(r'\b(19|20)\d{2}\b', entry_text)
                if len(years) >= 1:
                    exp.start_date = years[0]
                    if len(years) >= 2:
                        exp.end_date = years[1]
                    else:
                        exp.end_date = "Present"
                    date_found = True
            
            # Extract role/title - multiple patterns
            role_patterns = [
                # Role at Company
                r'([A-Z][A-Za-z\s&/]+(?:Engineer|Developer|Analyst|Manager|Lead|Senior|Junior|Specialist|Consultant|Intern|Associate|Architect|Designer|Scientist|Executive|Director|Coordinator|Officer|Administrator|Engineer|Developer|Programmer|Developer))\s+(?:at|@|,)\s*',
                # Standalone role on its own line
                r'^([A-Z][A-Za-z\s&/]+(?:Engineer|Developer|Analyst|Manager|Lead|Senior|Junior|Specialist|Consultant|Intern|Associate|Architect|Designer|Scientist|Executive|Director|Coordinator|Officer|Administrator))$',
                # Role - Company format
                r'([A-Z][A-Za-z\s&/]+(?:Engineer|Developer|Analyst|Manager|Lead|Senior|Junior|Specialist|Consultant|Intern|Associate|Architect|Designer|Scientist|Executive|Director))',
            ]
            
            for pattern in role_patterns:
                role_match = re.search(pattern, entry_text, re.IGNORECASE | re.MULTILINE)
                if role_match:
                    exp.role = role_match.group(1).strip()
                    break
            
            # Extract company - multiple patterns
            company_patterns = [
                # After "at" or "@"
                r'(?:at|@|,)\s*([A-Z][A-Za-z\s&,\.]+(?:Inc|LLC|Ltd|Corp|Corporation|Company|Solutions|Technologies|Systems|Limited)?)',
                # Standalone company name (capitalized words)
                r'^([A-Z][A-Z][A-Za-z\s&,\.]+(?:Inc|LLC|Ltd|Corp|Corporation|Company))',
                # Company - Role format (before role)
                r'^([A-Z][A-Za-z\s&,\.]+(?:Inc|LLC|Ltd|Corp|Company|Solutions|Technologies))\s*[-–—]',
            ]
            
            for pattern in company_patterns:
                company_match = re.search(pattern, entry_text, re.IGNORECASE | re.MULTILINE)
                if company_match:
                    company = company_match.group(1).strip()
                    # Clean up company name
                    company = re.sub(r'\s+', ' ', company).strip()
                    if len(company) > 2:
                        exp.company = company
                        break
            
            # Only add if we have at least role or company AND dates
            if (exp.role or exp.company) and exp.start_date:
                pos_id = (exp.role.lower() if exp.role else "", exp.company.lower() if exp.company else "")
                if pos_id not in found_positions or pos_id == ("", ""):
                    found_positions.add(pos_id)
                    
                    # Calculate duration based on extracted dates (no assumptions)
                    exp.duration_years = self._calculate_duration(exp.start_date, exp.end_date)
                    experience_list.append(exp)
        
        # Fallback: if nothing parsed, try global scan for date ranges
        if not experience_list:
            global_patterns = [
                r'(\d{4})\s*[-–—]\s*(\d{4}|Present|Current|Now)',
                r'(\d{1,2})[/-](\d{2,4})\s*[-–—]\s*(\d{1,2})?[/-]?(\d{2,4}|Present|Current|Now)?',
                r'([A-Za-z]{3,9})\s+(\d{2,4})\s*[-–—]\s*([A-Za-z]{3,9})?\s*(\d{2,4}|Present|Current|Now)?'
            ]
            for gpat in global_patterns:
                for m in re.finditer(gpat, text, re.IGNORECASE):
                    g = m.groups()
                    exp = ExperienceEntry()
                    start_year = end_year = None
                    start = g[0]
                    if len(g) >= 2:
                        end = g[1]
                    else:
                        end = ""
                    exp.start_date = start
                    exp.end_date = end or "Present"
                    exp.duration_years = self._calculate_duration(exp.start_date, exp.end_date)
                    if exp.duration_years > 0:
                        experience_list.append(exp)
                        if len(experience_list) >= 5:
                            break
                if experience_list:
                    break
        
        return experience_list[:10]  # Limit to 10 entries
    
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
        
        if not start_year:
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

