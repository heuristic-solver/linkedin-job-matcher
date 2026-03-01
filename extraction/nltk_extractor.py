"""
NLTK-Based Resume NER Extractor
Works across all resume formats:
  - Single-column, two-column, ATS plain-text, designed PDFs
  - Inline date format: "Role  Month YYYY – Month YYYY"
  - Stack format: "Role\nCompany\nDates"
  - Table format: "Company | Role | Dates"

Uses NLTK's trained POS tagger + NE chunker (Penn Treebank corpora)
for named entity recognition of PERSON, ORGANIZATION, GPE.
Compatible with Python 3.14+.
"""
import re
import nltk
from typing import List, Dict, Optional
from datetime import datetime

# ── NLTK data bootstrap ───────────────────────────────────────────────────────
_NLTK_PKGS = [
    ('tokenizers/punkt_tab', 'punkt_tab'),
    ('taggers/averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger_eng'),
    ('chunkers/maxent_ne_chunker_tab', 'maxent_ne_chunker_tab'),
    ('corpora/words', 'words'),
    ('corpora/stopwords', 'stopwords'),
]
for path, pkg in _NLTK_PKGS:
    try:
        nltk.data.find(path)
    except LookupError:
        nltk.download(pkg, quiet=True)

# ── Skills corpus (100+ terms, case-normalised) ───────────────────────────────
_SKILLS_CANONICAL = [
    # Programming languages
    'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'C', 'Go', 'Rust',
    'Ruby', 'PHP', 'Swift', 'Kotlin', 'R', 'Scala', 'MATLAB', 'Dart', 'Bash',
    'SQL', 'Perl', 'Haskell', 'Lua', 'Julia',
    # Web / Frameworks
    'React', 'Angular', 'Vue', 'Node.js', 'Express', 'Next.js', 'Django',
    'Flask', 'FastAPI', 'Spring', 'ASP.NET', 'Svelte', 'jQuery', 'Bootstrap',
    'Tailwind CSS', 'GraphQL', 'REST API', 'WebSocket',
    # Data / ML / AI
    'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision', 'AI',
    'Artificial Intelligence', 'TensorFlow', 'PyTorch', 'Keras',
    'Scikit-learn', 'Scikit-Learn', 'Scikit Learn',
    'Pandas', 'NumPy', 'Matplotlib', 'Seaborn', 'Plotly', 'OpenCV', 'Mediapipe',
    'NLTK', 'Hugging Face', 'LangChain', 'LlamaIndex', 'YOLO',
    'Random Forest', 'XGBoost', 'LightGBM', 'CatBoost',
    'LSTM', 'Transformer', 'BERT', 'GPT', 'CNN', 'RNN', 'GAN',
    'Reinforcement Learning', 'Agentic AI', 'RAG', 'Fine-tuning',
    'PSNR', 'SSIM', 'ESPCN', 'mmWave', 'STT', 'TTS',
    'FinBERT', 'Vosk', 'Gradio', 'Streamlit', 'BeautifulSoup', 'SERP API',
    'Data Science', 'Data Analysis', 'Data Engineering', 'Statistics',
    # Cloud & DevOps
    'AWS', 'Azure', 'GCP', 'Google Cloud', 'Google Cloud Platform',
    'Docker', 'Kubernetes', 'Jenkins', 'Terraform', 'Ansible',
    'CI/CD', 'DevOps', 'Heroku', 'Vercel', 'Netlify',
    # Databases
    'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Cassandra',
    'DynamoDB', 'Elasticsearch', 'Oracle', 'Firebase', 'Snowflake',
    # Tools & Platforms
    'Git', 'GitHub', 'GitLab', 'Jira', 'Confluence', 'Linux', 'Unix',
    'VS Code', 'Visual Studio Code', 'IntelliJ', 'Postman', 'Figma',
    'Google Colab', 'Jupyter', 'Tableau', 'Power BI',
    # Concepts / Methodologies
    'Agile', 'Scrum', 'Microservices', 'OOP', 'System Design',
    'Data Structures', 'Algorithms', 'Software Development',
]
_SKILLS_LOWER_MAP = {s.lower(): s for s in _SKILLS_CANONICAL}

# ── Role-level keywords (used for splitting experience blocks) ────────────────
_ROLE_KEYWORDS = (
    'Intern', 'Engineer', 'Developer', 'Analyst', 'Manager', 'Lead',
    'Senior', 'Junior', 'Specialist', 'Scientist', 'Consultant', 'Officer',
    'Director', 'Associate', 'Researcher', 'Trainer', 'Advisor', 'Head',
    'Architect', 'Designer', 'Executive', 'Coordinator', 'Representative',
    'Administrator', 'Technician', 'Programmer', 'VP', 'President',
)
_ROLE_RE = re.compile(
    r'(?:' + '|'.join(re.escape(k) for k in _ROLE_KEYWORDS) + r')\b',
    re.IGNORECASE,
)

# ── Degree patterns (ordered by specificity) ─────────────────────────────────
_DEGREE_PATTERNS = [
    r'(?:Bachelor|Master|Doctor|Ph\.?D\.?)(?:\'s)?\s+of\s+\w+(?:\s+in\s+[\w\s&]+)?',
    r'B\.?\s*Tech(?:nology)?(?:\s+in\s+[\w\s&]+)?',
    r'M\.?\s*Tech(?:nology)?(?:\s+in\s+[\w\s&]+)?',
    r'B\.?\s*[SE]\.?(?:\s+in\s+[\w\s&]+)?',
    r'M\.?\s*Sc\.?(?:\s+in\s+[\w\s&]+)?',
    r'MBA(?:\s+in\s+[\w\s&]+)?',
    r'Associate(?:\'s)?\s+(?:Degree\s+)?(?:in\s+)?[\w\s]+',
    r'Diploma(?:\s+in\s+[\w\s&]+)?',
    r'High\s+School\s+Diploma',
    r'GED',
]

# ── Major section headings ────────────────────────────────────────────────────
_SECTION_RE = re.compile(
    r'^(SUMMARY|OBJECTIVE|PROFILE|ABOUT|EDUCATION|QUALIFICATION'
    r'|EXPERIENCE|WORK\s+EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EMPLOYMENT'
    r'|INTERNSHIPS?|CAREER\s+HISTORY|WORK\s+HISTORY'
    r'|SKILLS?|TECHNICAL\s+SKILLS?|CORE\s+COMPETENCIES'
    r'|PROJECTS?|PORTFOLIO|CERTIFICATIONS?(?:\s+[&]\s+ACHIEVEMENTS?)?|CERTIFICATES?'
    r'|ACHIEVEMENTS?|AWARDS?|HONORS?|PUBLICATIONS?'
    r'|VOLUNTEERING?|LANGUAGES?|REFERENCES?|CONTACT|INTERESTS?|HOBBIES'
    r'|CO-CURRICULAR(?:\s+[&]\s+EXTRACURRICULAR)?|EXTRACURRICULAR)\s*:?\s*$',
    re.IGNORECASE | re.MULTILINE,
)

# ── Date regex helpers ────────────────────────────────────────────────────────
_MONTH_MAP = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
    'mar': 3, 'march': 3, 'apr': 4, 'april': 4, 'may': 5,
    'jun': 6, 'june': 6, 'jul': 7, 'july': 7, 'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9, 'oct': 10, 'october': 10,
    'nov': 11, 'november': 11, 'dec': 12, 'december': 12,
}
_MONTH_NAMES = '|'.join([
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
    'Jan', 'Feb', 'Mar', 'Apr', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
])
_END_TERMS = r'(?:Present|Current|Now|Till\s+Date|Today)'
_DATE_RANGE_RES = [
    # "December 2025 – January 2026" (with spaces, any dash variant)
    re.compile(
        rf'({_MONTH_NAMES})\s+(\d{{4}})\s*[-\u2013\u2014]\s*({_MONTH_NAMES})\s+(\d{{4}})',
        re.IGNORECASE,
    ),
    # "April 2025–June 2025" (NO spaces around dash — compact form)
    re.compile(
        rf'({_MONTH_NAMES})\s+(\d{{4}})[-\u2013\u2014]({_MONTH_NAMES})\s*(\d{{4}})',
        re.IGNORECASE,
    ),
    # "April2025-May2025" — NO space between month and year (space-stripped PDFs)
    re.compile(
        rf'({_MONTH_NAMES})(\d{{4}})[-\u2013\u2014]({_MONTH_NAMES})(\d{{4}})',
        re.IGNORECASE,
    ),
    # "December 2025 – Present"
    re.compile(
        rf'({_MONTH_NAMES})\s+(\d{{4}})\s*[-\u2013\u2014]\s*({_END_TERMS})',
        re.IGNORECASE,
    ),
    # "April2025-Present" — no space, present end
    re.compile(
        rf'({_MONTH_NAMES})(\d{{4}})[-\u2013\u2014]({_END_TERMS})',
        re.IGNORECASE,
    ),
    # "2022 – Present"  /  "2020 – 2023"
    re.compile(
        rf'(\d{{4}})\s*[-\u2013\u2014]\s*({_END_TERMS}|\d{{4}})',
        re.IGNORECASE,
    ),
    # "01/2022 – 06/2023"
    re.compile(r'(\d{1,2})[/-](\d{4})\s*[-\u2013\u2014]\s*(\d{1,2})?[/-]?(\d{4}|' + _END_TERMS + r')?', re.IGNORECASE),
]


def _parse_duration(text: str):
    """Extract (duration_str, years_float) from any text containing a date range."""
    for pat in _DATE_RANGE_RES:
        m = pat.search(text)
        if not m:
            continue
        g = m.groups()
        now = datetime.now()
        try:
            if len(g) == 4 and g[2]:  # Month YYYY – Month YYYY
                sm = _MONTH_MAP.get(g[0].lower()[:3], 1)
                sy = int(g[1])
                em_str = g[2]
                ey_str = g[3] if g[3] else str(now.year)
                if em_str.lower().replace(' ', '') not in ('present', 'current', 'now', 'tilldate', 'today'):
                    em = _MONTH_MAP.get(em_str.lower()[:3], now.month)
                    ey = int(ey_str) if ey_str.isdigit() else now.year
                else:
                    em = now.month
                    ey = now.year
                months = max((ey - sy) * 12 + (em - sm), 0)
                return m.group(0).strip(), round(months / 12, 2)
            elif len(g) == 2:  # YYYY – YYYY/Present
                sy = int(g[0])
                ey_str = str(g[1])
                ey = now.year if not ey_str.isdigit() else int(ey_str)
                return m.group(0).strip(), round(max(ey - sy, 0), 2)
        except Exception:
            pass
    return '', 0.0


def _ner_orgs(text: str) -> List[str]:
    """Run NLTK NER on text and return ORGANIZATION entities found."""
    orgs = []
    try:
        tokens = nltk.word_tokenize(text[:600])
        tagged = nltk.pos_tag(tokens)
        chunks = nltk.ne_chunk(tagged, binary=False)
        for chunk in chunks:
            if hasattr(chunk, 'label') and chunk.label() == 'ORGANIZATION':
                org = ' '.join(c[0] for c in chunk.leaves()).strip()
                if 3 < len(org) < 80:
                    orgs.append(org)
    except Exception:
        pass
    return orgs


def _ner_persons(text: str) -> List[str]:
    """Run NLTK NER on text and return PERSON entities found."""
    persons = []
    try:
        tokens = nltk.word_tokenize(text[:400])
        tagged = nltk.pos_tag(tokens)
        chunks = nltk.ne_chunk(tagged, binary=False)
        for chunk in chunks:
            if hasattr(chunk, 'label') and chunk.label() == 'PERSON':
                name = ' '.join(c[0] for c in chunk.leaves()).strip()
                if 4 < len(name) < 60 and 2 <= len(name.split()) <= 5:
                    persons.append(name)
    except Exception:
        pass
    return persons


class NLTKResumeExtractor:
    """
    General-purpose resume extractor.
    Handles all major resume layouts using NLTK NER + universal pattern matching.
    """

    def __init__(self):
        self._sections: Dict[str, str] = {}
        self._raw_text: str = ''

    # ── Public API ─────────────────────────────────────────────────────────────

    def extract_all(self, text: str) -> Dict:
        text = self._clean(text)
        self._raw_text = text
        self._sections = self._split_sections(text)

        return {
            'name':       self._get_name(text),
            'email':      self._get_email(text),
            'phone':      self._get_phone(text),
            'summary':    self._get_summary(),
            'skills':     self._get_skills(text),
            'education':  self._get_education(),
            'experience': self._get_experience(text),
        }

    # ── Text cleaning ──────────────────────────────────────────────────────────

    def _clean(self, text: str) -> str:
        """Normalise PDF encoding artifacts and fix common spacing issues."""
        _REPLACEMENTS = {
            '\xfb': '-', '\x96': '-', '\x97': '-', 'û': '-', 'Ö': '-', '§': '-',
            '\x91': "'", '\x92': "'", 'Æ': "'",
            '\x93': '"', '\x94': '"',
            '\u2013': '-', '\u2014': '-',
            '\u2022': '•', '\u2019': "'",
        }
        for ch, rep in _REPLACEMENTS.items():
            text = text.replace(ch, rep)
        # Collapse multiple spaces (but keep newlines)
        text = re.sub(r'[ \t]{2,}', '  ', text)
        # Fix space-stripped PDFs: insert space between month name and 4-digit year
        # e.g. "April2025" -> "April 2025"
        MONTHS_RE = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
        text = re.sub(rf'{MONTHS_RE}(\d{{4}})', r'\1 \2', text, flags=re.IGNORECASE)
        return text

    # ── Section splitting ──────────────────────────────────────────────────────

    def _split_sections(self, text: str) -> Dict[str, str]:
        """Split resume into named sections using ALL-CAPS heading detection."""
        lines = text.split('\n')
        sections: Dict[str, str] = {}
        current_key = 'HEADER'
        buf: List[str] = []

        for line in lines:
            stripped = line.strip()
            if _SECTION_RE.match(stripped):
                sections[current_key] = '\n'.join(buf).strip()
                current_key = re.sub(r'\s+', '_', stripped.upper().rstrip(':'))
                buf = []
            else:
                buf.append(line)
        sections[current_key] = '\n'.join(buf).strip()
        return sections

    def _section(self, *keys: str) -> str:
        """Return content of the first matching section."""
        for key in keys:
            for k, v in self._sections.items():
                if key.upper() in k:
                    return v
        return ''

    def _extract_between_headings(self, heading: str) -> str:
        """
        Universal section extractor — find content between `heading`
        and the next known section heading in raw text.
        """
        NEXT_SECTION = (
            r'(?:PROJECTS?|RESEARCH\s+PROJECTS?|UNDERGRADUATE\s+PROJECTS?|COURSE\s+PROJECTS?'
            r'|COMPETITIONS?|PRESENTATIONS?|CONFERENCES?'
            r'|CERTIFICATIONS?(?:\s+&\s+ACHIEVEMENTS?)?|CERTIFICATES?'
            r'|ACHIEVEMENTS?|TECHNICAL\s+SKILLS?|SKILLS?|PUBLICATIONS?'
            r'|LANGUAGES?|AWARDS?|HONORS?|VOLUNTEERING?|REFERENCES?'
            r'|INTERESTS?|CONTACT|EDUCATION|ABOUT|PROFILE|SUMMARY'
            r'|PROFESSIONAL\s+SUMMARY|CO-CURRICULAR|EXTRACURRICULAR)'
        )
        pat = re.compile(
            rf'(?:^|\n)({heading})[^\n]*\n(.*?)(?=\n\s*{NEXT_SECTION}[^\n]*\n|\Z)',
            re.IGNORECASE | re.DOTALL | re.MULTILINE,
        )
        m = pat.search(self._raw_text)
        if not m:
            return ''
        content = m.group(2) if m.lastindex >= 2 else m.group(1)
        return content.strip() if content else ''

    # ── Name ───────────────────────────────────────────────────────────────────

    def _get_name(self, text: str) -> str:
        header = self._sections.get('HEADER', text[:600])
        header_lines = [l.strip() for l in header.split('\n') if l.strip()]

        # ── Fast heuristic first: top line that looks like a name ──────────────
        # (Most resumes put the name as the very first line)
        skip_words = ['@', 'http', 'github', 'linkedin', 'mobile', 'phone', 'email']
        for line in header_lines[:5]:
            if any(s in line.lower() for s in skip_words):
                continue
            if '+' in line and any(c.isdigit() for c in line):
                continue  # phone number line
            if '|' in line:
                continue  # contact bar line
            words = line.split()
            if 2 <= len(words) <= 5 and all(w[0].isupper() for w in words if w.isalpha()) and len(line) < 50:
                return line

        # ── NLTK NER fallback: longest PERSON entity in header ─────────────────
        all_persons = []
        for line in header_lines[:8]:
            if any(c in line.lower() for c in ['@', 'http', '+91', '+1', 'github', 'linkedin', 'medium', '|']):
                continue
            all_persons.extend(_ner_persons(line))
        if all_persons:
            return max(all_persons, key=len)

        return ''

    # ── Contact ────────────────────────────────────────────────────────────────

    def _get_email(self, text: str) -> str:
        m = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text)
        return m.group(0) if m else ''

    def _get_phone(self, text: str) -> str:
        for pat in [
            r'\+?\d{1,3}[\s.-]?\(?\d{3,5}\)?[\s.-]?\d{3,5}[\s.-]?\d{3,5}',
            r'\d{10,12}',
        ]:
            m = re.search(pat, text)
            if m:
                phone = re.sub(r'[^\d+\-() ]', '', m.group(0)).strip()
                if len(re.sub(r'\D', '', phone)) >= 10:
                    return phone
        return ''

    # ── Summary ────────────────────────────────────────────────────────────────

    def _get_summary(self) -> str:
        text = self._section('SUMMARY', 'OBJECTIVE', 'PROFILE', 'ABOUT')
        if not text:
            # Try first paragraph of header
            header = self._sections.get('HEADER', '')
            paras = [p.strip() for p in header.split('\n\n') if len(p.strip()) > 50]
            text = paras[0] if paras else ''
        if not text:
            return ''
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return ' '.join(sentences[:3])[:500].strip()

    # ── Skills ─────────────────────────────────────────────────────────────────

    def _get_skills(self, full_text: str) -> List[str]:
        """Match against the skills corpus in both the skills section and full text."""
        skills_section = self._section('SKILL', 'TECHNICAL', 'COMPETENC')
        combined = (skills_section + '\n' + full_text).lower()
        found = set()
        # Longer skills first to avoid partial matches
        for skill_lower in sorted(_SKILLS_LOWER_MAP, key=len, reverse=True):
            pattern = r'(?<![A-Za-z0-9])' + re.escape(skill_lower) + r'(?![A-Za-z0-9])'
            if re.search(pattern, combined, re.IGNORECASE):
                found.add(_SKILLS_LOWER_MAP[skill_lower])
        return sorted(found)

    # ── Education ──────────────────────────────────────────────────────────────

    def _get_education(self) -> List[Dict]:
        text = self._section('EDUCATION', 'QUALIFICATION')
        if not text:
            text = self._extract_between_headings('EDUCATION')
        if not text:
            return []

        results = []
        # Split on blank lines; each block is one edu entry
        blocks = re.split(r'\n{2,}', text)
        if len(blocks) <= 1:
            blocks = re.split(
                r'(?=' + '|'.join(f'(?:{p})' for p in _DEGREE_PATTERNS) + r')',
                text, flags=re.IGNORECASE,
            )

        for block in blocks[:5]:
            block = block.strip()
            if not block:
                continue
            edu = {'degree': '', 'institution': '', 'field': '', 'year': '', 'gpa': ''}

            for dp in _DEGREE_PATTERNS:
                dm = re.search(dp, block, re.IGNORECASE)
                if dm:
                    edu['degree'] = dm.group(0).strip()
                    break

            # Year range
            ym = re.search(r'\b(20\d{2})\s*[-–]\s*(20\d{2}|Present|Current)', block, re.IGNORECASE)
            if ym:
                edu['year'] = f"{ym.group(1)} - {ym.group(2)}"
            else:
                ym2 = re.search(r'\b(19|20)\d{2}\b', block)
                if ym2:
                    edu['year'] = ym2.group(0)

            # GPA
            gm = re.search(r'GPA\s*:?\s*([\d.]+)', block, re.IGNORECASE)
            if gm:
                edu['gpa'] = gm.group(1)

            # Institution: try NLTK NER first
            orgs = _ner_orgs(block)
            for org in orgs:
                if org.lower() not in edu['degree'].lower() and len(org) > 4:
                    edu['institution'] = org
                    break

            # Fallback: first capitalised line that isn't the degree or a date line
            if not edu['institution']:
                for line in block.split('\n'):
                    line = line.strip()
                    if not line or re.search(r'\d{4}', line):
                        continue
                    if edu['degree'] and edu['degree'].lower()[:15] in line.lower():
                        continue
                    if re.match(r'^[A-Z][A-Za-z\s&,\'-]{5,80}$', line):
                        edu['institution'] = line
                        break

            # Field from degree text
            fm = re.search(r'(?:in|of)\s+([\w\s&]+?)(?:\s*[;,]|$)', edu['degree'], re.IGNORECASE)
            if fm:
                edu['field'] = fm.group(1).strip()

            if edu['degree'] or edu['institution']:
                results.append(edu)

        return results[:5]

    # ── Experience ─────────────────────────────────────────────────────────────

    def _get_experience(self, full_text: str) -> List[Dict]:
        """
        Handles all resume experience formats universally:
          (A) Inline: "Role Title   Month YYYY - Month YYYY"
          (B) Stacked: "Role\\nCompany\\nMonth YYYY - Present"
          (C) Year range only: "Company\\nRole\\n2020-2023"

        Uses a fast line-by-line scanner — no catastrophic backtracking.
        """
        text = self._section('EXPERIENCE', 'WORK', 'EMPLOYMENT', 'INTERNSHIP', 'CAREER')
        if not text:
            text = self._extract_between_headings(
                r'INTERNSHIPS?|EXPERIENCE|WORK\s+EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EMPLOYMENT'
            )
        if not text:
            return []

        results: List[Dict] = []
        seen: set = set()
        lines = text.split('\n')

        # ── Step 1: identify all lines that contain a date range ──────────────
        # These act as anchors; for each, we look at surrounding lines for role/company.
        dated_line_indices: List[int] = []
        for i, line in enumerate(lines):
            if _parse_duration(line)[0]:  # has a parseable date range
                dated_line_indices.append(i)

        # ── Step 2: for each dated line, find role and company ─────────────────
        for anchor_i in dated_line_indices:
            anchor_line = lines[anchor_i]
            duration, years = _parse_duration(anchor_line)
            role = ''
            company = ''

            # Check if role is ON THE SAME LINE as the date
            # e.g. "AI/ML Development Intern   December 2025 - January 2026"
            role_match = _ROLE_RE.search(anchor_line)
            if role_match:
                # Role is inline — extract the part before the date
                dur_match = re.search(
                    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}'
                    r'|(?:Present|Current|Now)',
                    anchor_line, re.IGNORECASE
                )
                pre_date = anchor_line[:dur_match.start()].strip() if dur_match else anchor_line[:role_match.end()].strip()

                # ── Format detection: how are role + company separated? ──────────
                # Priority: en-dash/pipe (Rutwik), comma (Atharv), plain (Joel)

                # 1. "Company – Intern | Date"  or  "Company - Intern | Date"
                pipe_dash_split = re.split(r'\s*[-–|]\s*', pre_date)
                if len(pipe_dash_split) >= 2:
                    for split_idx in range(len(pipe_dash_split) - 1, -1, -1):
                        if _ROLE_RE.search(pipe_dash_split[split_idx]):
                            role = pipe_dash_split[split_idx].strip()
                            company = ' '.join(pipe_dash_split[:split_idx]).strip()
                            company = re.sub(r'\s*\([^)]+\)', '', company).strip()
                            break
                    else:
                        role = pre_date

                # 2. "Role, Company" - comma separated (Atharv style)
                if not role and ',' in pre_date:
                    parts = pre_date.split(',', 1)
                    if _ROLE_RE.search(parts[0]):
                        role = parts[0].strip()
                        company = parts[1].strip() if len(parts) > 1 else ''
                    else:
                        role = pre_date

                # 3. Fallback: role is the whole pre-date text
                if not role:
                    role = pre_date

                # If company not found inline, look at lines after
                if not company:
                    for j in range(anchor_i + 1, min(anchor_i + 4, len(lines))):
                        candidate = lines[j].strip()
                        if not candidate or candidate.startswith(('-', '–', '•', '*', '·')):
                            break
                        if _ROLE_RE.search(candidate) and _parse_duration(candidate)[0]:
                            break
                        if re.match(r'^[A-Z][A-Za-z\s&.,\'/()-]{3,70}$', candidate):
                            company = candidate
                            break
            else:
                # Date is on its own line — role is in adjacent lines (stacked format)
                # Look BEFORE anchor for role (within 3 lines)
                for j in range(anchor_i - 1, max(anchor_i - 4, -1), -1):
                    candidate = lines[j].strip()
                    if not candidate:
                        continue
                    if _ROLE_RE.search(candidate) and not _parse_duration(candidate)[0]:
                        role = re.sub(r'\s+', ' ', candidate).strip()
                        break

                # Look in the window around anchor for company (capitalised non-role line)
                window = list(range(max(0, anchor_i - 3), min(len(lines), anchor_i + 4)))
                for j in window:
                    candidate = lines[j].strip()
                    if not candidate or j == anchor_i:
                        continue
                    if _parse_duration(candidate)[0]:
                        continue
                    if candidate == role:
                        continue
                    if candidate.startswith(('-', '–', '•', '*')):
                        continue
                    if re.match(r'^[A-Z][A-Za-z\s&.,\'/()-]{3,70}$', candidate):
                        company = candidate
                        break

            if not role and not company:
                continue

            # NLTK NER fallback for company
            if not company:
                block = '\n'.join(lines[max(0, anchor_i-2):min(len(lines), anchor_i+4)])
                orgs = _ner_orgs(block)
                for org in orgs:
                    if org.lower() not in role.lower():
                        company = org
                        break

            entry = {
                'role': re.sub(r'\s+', ' ', role).strip(),
                'company': company,
                'location': None,
                'duration': duration,
                'years': years,
            }
            key = (entry['role'].lower()[:30], entry['company'].lower()[:20])
            if key not in seen:
                seen.add(key)
                results.append(entry)

        return results[:10]

    def _parse_inline_block(self, role_text: str, date_text: str, full_block: str) -> Dict:
        """Parse an experience entry where role+date appear on the same line."""
        entry = {'role': '', 'company': '', 'location': None, 'duration': '', 'years': 0.0}
        entry['role'] = re.sub(r'\s+', ' ', role_text).strip()
        entry['duration'], entry['years'] = _parse_duration(date_text)
        if not entry['duration']:
            entry['duration'] = date_text.strip()

        # Company: first non-role, non-date, non-bullet line after the heading line
        for line in full_block.split('\n')[1:]:
            line = line.strip()
            if not line:
                continue
            if line.startswith(('-', '–', '•', '*', '·', '▪')):
                break  # reached bullet points
            if re.search(r'\d{4}', line):
                continue
            if re.search(r'(?:' + '|'.join(_ROLE_KEYWORDS) + r')\b', line, re.IGNORECASE):
                break  # next job
            if re.match(r'^[A-Z][A-Za-z\s&.,\'/()-]{3,70}$', line):
                entry['company'] = line
                break

        # Try NLTK NER for company if heuristic failed
        if not entry['company']:
            orgs = _ner_orgs(full_block[:400])
            for org in orgs:
                if org.lower() not in entry['role'].lower():
                    entry['company'] = org
                    break

        return entry

    def _parse_stacked_block(self, block: str) -> Optional[Dict]:
        """Parse an experience block in stacked format."""
        entry = {'role': '', 'company': '', 'location': None, 'duration': '', 'years': 0.0}

        # Date
        entry['duration'], entry['years'] = _parse_duration(block)
        if not entry['duration']:
            return None

        lines = [l.strip() for l in block.split('\n') if l.strip()]
        role_line_idx = None
        for i, line in enumerate(lines):
            if _ROLE_RE.search(line) and not re.search(r'\d{4}', line):
                entry['role'] = re.sub(r'\s+', ' ', line).strip()
                role_line_idx = i
                break

        if not entry['role']:
            return None

        # Company: adjacent line that's not the role and not a date
        for i, line in enumerate(lines):
            if i == role_line_idx:
                continue
            if re.search(r'\d{4}', line):
                continue
            if line.startswith(('-', '–', '•', '*')):
                continue
            if re.match(r'^[A-Z][A-Za-z\s&.,\'/()-]{3,70}$', line):
                entry['company'] = line
                break

        # Fallback: NLTK NER
        if not entry['company']:
            orgs = _ner_orgs(block[:400])
            for org in orgs:
                if org.lower() not in entry['role'].lower():
                    entry['company'] = org
                    break

        if entry['role']:
            return entry
        return None
