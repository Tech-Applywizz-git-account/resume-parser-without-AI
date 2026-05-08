# patterns.py

import re

# Contact Information
EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
# Handles + 1(217) 790 - 5953 and other spaced formats
PHONE_PATTERN = r'(?:\+?\s?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
LINKEDIN_PATTERN = r'https?://(?:www\.)?linkedin\.com/in/[\w-]+/?'
GITHUB_PATTERN = r'https?://(?:www\.)?github\.com/[\w-]+/?'
PORTFOLIO_PATTERN = r'https?://(?:www\.)?[\w-]+\.(?:com|io|me|net|org)(?:/[\w-]+)*/?'

# Date Patterns (Handles 08/2023, Aug 2023, 2023)
MONTHS = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
YEARS = r'(?:20[0-2]\d|19[7-9]\d)'
DATE_PART = rf'(?:{MONTHS}\s*{YEARS}|{MONTHS}|{YEARS}|\d{{1,2}}/\d{{2,4}})'
DATE_RANGE_PATTERN = rf'({DATE_PART}|Present|Current)\s*[-–—to\s]+\s*({DATE_PART}|Present|Current)'

# Section Headers
HEADERS = {
    "summary": ["summary", "profile", "about", "professional summary", "objective", "career objective"],
    "skills": ["skills", "technical skills", "core competencies", "expertise", "technologies", "proficiencies", "technical expertise", "tools", "technology stack"],
    "experience": ["experience", "work experience", "employment", "professional background", "career history", "professional experience", "work history", "employment history", "professional timeline"],
    "projects": ["projects", "personal projects", "academic projects", "key projects", "notable projects", "technical projects"],
    "education": ["education", "academic background", "scholastic achievements", "qualification", "academic profile", "educational background", "academic record"],
    "certifications": ["certifications", "licenses", "courses", "certificates", "training", "professional certifications", "awards"],
    "achievements": ["achievements", "accomplishments", "recognitions", "honors"]
}

DEGREES = [
    'master of science', 'master of technology', 'master of business administration', 'master of arts',
    'bachelor of technology', 'bachelor of science', 'bachelor of engineering', 'bachelor of arts',
    'b.tech', 'm.tech', 'b.sc', 'm.sc', 'b.e', 'm.e', 'mba', 'phd', 'bca', 'mca', 'diploma', 'master of', 'bachelor of'
]

UNIVERSITY_KEYWORDS = ["university", "college", "institute", "school", "snist", "suny", "jntu", "iit", "nit", "polytechnic"]

def find_pattern(text, pattern):
    matches = re.findall(pattern, text, re.IGNORECASE)
    return matches[0] if matches else None














# """
# patterns.py — The single source of truth for all regex, keyword lists, and
# matching helpers.  Every pattern here was written after seeing 500+ resumes
# break a simpler version.

# Veteran notes
# ─────────────
# • Never hard-code a single regex for phone.  Phones come in 50+ formats.
# • Dates: month-first, year-first, slashed, dotted, short, long — all exist.
# • Degrees: people abbreviate them 8 different ways on the same resume.
# • Section headers: sometimes ALL-CAPS, sometimes emoji-prefixed, sometimes
#   in a sidebar column, sometimes buried in a table cell.
# • URLs: many PDFs store the visible text separately from the href; grab both.
# """

# import re

# # ──────────────────────────────────────────────────────────────────────────────
# # CONTACT PATTERNS
# # ──────────────────────────────────────────────────────────────────────────────

# EMAIL_PATTERN = (
#     r'[a-zA-Z0-9]'                    # must start with alnum
#     r'[a-zA-Z0-9._%+\-]{0,63}'        # local part
#     r'@'
#     r'[a-zA-Z0-9.\-]{1,255}'          # domain
#     r'\.[a-zA-Z]{2,10}'               # TLD
# )

# # Covers: +91-9876543210, (123) 456-7890, 123.456.7890, +1 800 555 5555,
# #         9876543210, 091-1234567890, etc.
# PHONE_PATTERN = (
#     r'(?:'
#         r'(?:\+|00)\s?'               # optional country code prefix
#         r'(?:\d[\s.\-]?){1,3}\s?'     # country digits
#     r')?'
#     r'(?:'
#         r'\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}'   # (xxx) xxx-xxxx
#         r'|\d{10}'                                    # 10 plain digits
#         r'|\d{3}[\s.\-]\d{4}[\s.\-]\d{3}'            # xxx-xxxx-xxx (some countries)
#         r'|\+?\d{1,3}[\s.\-]?\d{10}'                 # +CC 10-digit
#         r'|\+?\d{12,15}'                              # raw international
#     r')'
#     r'(?:\s?(?:ext|x|ext\.)\s?\d{1,6})?'            # optional extension
# )

# # ──────────────────────────────────────────────────────────────────────────────
# # URL / LINK PATTERNS
# # ──────────────────────────────────────────────────────────────────────────────

# URL_PATTERN = r'https?://[^\s<>"\'\\)]{4,}'

# # Domain-only patterns (no http) that still appear in resumes
# NAKED_LINKEDIN = r'(?:www\.)?linkedin\.com/in/[\w\-\./%]+'
# NAKED_GITHUB   = r'(?:www\.)?github\.com/[\w\-\./%]+'

# # ──────────────────────────────────────────────────────────────────────────────
# # DATE PATTERNS — the most pain-inducing part of any resume parser
# # ──────────────────────────────────────────────────────────────────────────────

# MONTH_FULL  = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
# MONTH_SHORT = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
# MONTH_NAMES = rf'(?:{MONTH_FULL}|{MONTH_SHORT})\.?'
# YEAR_4      = r'(?:20[0-2]\d|19[6-9]\d)'           # 1960–2029
# YEAR_2      = r"(?:'?\d{2})"                         # '22 or 22
# CURRENT     = r'(?:Present|Current|Till\s*Now|Ongoing|Now|Till\s*Date|To\s*Date|Today|—)'

# # A single point in time
# DATE_PART = (
#     rf'(?:'
#         rf'{MONTH_NAMES}\s*{YEAR_4}'        # Aug 2023
#         rf'|{MONTH_NAMES}\s*{YEAR_2}'       # Aug '23
#         rf'|{MONTH_NAMES}'                  # Aug (standalone, rare)
#         rf'|\d{{1,2}}/\d{{4}}'              # 08/2023
#         rf'|\d{{1,2}}/\d{{2}}'              # 08/23
#         rf'|{YEAR_4}'                        # 2023
#         rf'|{CURRENT}'
#     rf')'
# )

# # A range: "Aug 2021 – Present", "Jan 2020 to Dec 2022", "2019-2023"
# DATE_RANGE_PATTERN = (
#     rf'({DATE_PART})'
#     rf'\s*(?:[-–—]+|[Tt]o|[Tt]ill|[Tt]hrough|[Uu]ntil|[Uu]pto)\s*'
#     rf'({DATE_PART}|{CURRENT})'
# )

# # ──────────────────────────────────────────────────────────────────────────────
# # EDUCATION — degree spellings found in the wild
# # ──────────────────────────────────────────────────────────────────────────────

# DEGREES = [
#     # ── Doctorates ──
#     'doctor of philosophy', 'ph.d', 'phd', 'ph d', 'd.phil',
#     'doctor of medicine', 'md', 'm.d', 'doctor of business administration', 'dba',
#     # ── Masters ──
#     'master of science', 'master of technology', 'master of engineering',
#     'master of business administration', 'master of arts', 'master of commerce',
#     'master of computer applications', 'master of computer science',
#     'master of public administration', 'master of public health',
#     'master of information technology', 'master of data science',
#     'm.tech', 'm tech', 'mtech', 'm.sc', 'msc', 'm.e', 'me',
#     'mba', 'mca', 'm.ca', 'm.com', 'ma', 'ms', 'm.s', 'meng', 'm.eng',
#     'pgdm', 'pgd', 'post graduate diploma', 'post-graduate diploma',
#     # ── Bachelors ──
#     'bachelor of technology', 'bachelor of science', 'bachelor of engineering',
#     'bachelor of arts', 'bachelor of commerce', 'bachelor of computer applications',
#     'bachelor of business administration', 'bachelor of computer science',
#     'bachelor of information technology',
#     'b.tech', 'b tech', 'btech', 'b.sc', 'bsc', 'b.e', 'be',
#     'bca', 'b.ca', 'bba', 'bcom', 'b.com', 'ba', 'bs', 'b.s', 'beng', 'b.eng',
#     # ── Associates / Diplomas ──
#     'associate of science', 'associate of arts', 'associate degree',
#     'diploma', 'advanced diploma', 'higher national diploma', 'hnd', 'hnc',
#     # ── Generic prefix matches (used in fallback) ──
#     'master of', 'bachelor of', 'doctor of', 'associate of',
# ]

# # Sorted by length descending so longest match wins
# DEGREES_SORTED = sorted(DEGREES, key=len, reverse=True)

# UNIVERSITY_KEYWORDS = [
#     # Generic
#     'university', 'college', 'institute', 'school', 'academy', 'faculty',
#     'polytechnic', 'campus', 'institution',
#     # India
#     'iit', 'nit', 'iiit', 'bits', 'vnit', 'snist', 'jntu', 'anna', 'amu',
#     'du', 'bhu', 'vit', 'srm', 'manipal', 'lpu', 'amity',
#     # US / Global
#     'suny', 'mit', 'caltech', 'stanford', 'harvard', 'oxford', 'cambridge',
#     'carnegie', 'columbia', 'cornell', 'purdue', 'Georgia', 'michigan',
#     # Catchall
#     'deemed', 'autonomous', 'affiliated',
# ]

# # ──────────────────────────────────────────────────────────────────────────────
# # SECTION HEADERS — the keywords the segmenter uses for fuzzy matching
# # ──────────────────────────────────────────────────────────────────────────────

# HEADERS = {
#     "summary": [
#         "summary", "profile", "about me", "about", "professional summary",
#         "objective", "career objective", "professional objective",
#         "personal statement", "career summary", "overview", "introduction",
#         "professional profile", "executive summary", "bio", "highlights",
#         "career highlights", "professional statement", "mission",
#     ],
#     "skills": [
#         "skills", "technical skills", "core competencies", "expertise",
#         "technologies", "proficiencies", "technical expertise", "tools",
#         "technology stack", "competencies", "key skills", "soft skills",
#         "hard skills", "programming languages", "languages and technologies",
#         "tools and technologies", "tech stack", "it skills", "areas of expertise",
#         "technical proficiencies", "skill set", "skillset", "capabilities",
#         "technologies used", "technical knowledge", "developer skills",
#         "domain skills", "frameworks", "platforms", "databases",
#     ],
#     "experience": [
#         "experience", "work experience", "employment", "professional background",
#         "career history", "professional experience", "work history",
#         "employment history", "professional timeline", "career experience",
#         "relevant experience", "industry experience", "internship",
#         "internships", "work", "positions held", "professional roles",
#         "professional work experience", "job history", "job experience",
#         "work and experience", "career", "roles",
#     ],
#     "projects": [
#         "projects", "personal projects", "academic projects", "key projects",
#         "notable projects", "technical projects", "project work",
#         "project experience", "project highlights", "selected projects",
#         "independent projects", "open source", "open source projects",
#         "side projects", "portfolio", "project details",
#     ],
#     "education": [
#         "education", "academic background", "scholastic achievements",
#         "qualification", "academic profile", "educational background",
#         "academic record", "educational qualifications", "academics",
#         "educational history", "degrees", "qualifications", "academic history",
#         "academic details", "educational details", "academic credentials",
#         "schooling", "training and education",
#     ],
#     "certifications": [
#         "certifications", "licenses", "courses", "certificates",
#         "training", "professional certifications", "awards and certifications",
#         "professional development", "continuing education",
#         "professional training", "workshops", "seminars", "accreditations",
#         "credentials", "badges", "online courses", "moocs", "coursework",
#         "professional courses", "certifications and courses",
#     ],
#     "achievements": [
#         "achievements", "accomplishments", "recognitions", "honors",
#         "awards", "accolades", "honors and awards", "distinctions",
#         "scholarships", "fellowships", "prizes", "competitions", "hackathons",
#         "awards and recognitions", "key achievements",
#     ],
#     "languages": [
#         "languages", "language proficiency", "spoken languages",
#         "foreign languages", "linguistic skills", "language skills",
#         "languages known",
#     ],
#     "volunteer": [
#         "volunteer", "volunteering", "volunteer experience",
#         "community service", "social work", "extracurricular",
#         "extracurricular activities", "activities", "leadership",
#         "clubs", "organizations", "memberships", "affiliations",
#         "co curricular", "co-curricular",
#     ],
#     "publications": [
#         "publications", "research", "papers", "articles", "journals",
#         "conference papers", "research papers", "patents", "thesis",
#         "research work", "published work",
#     ],
# }

# # ──────────────────────────────────────────────────────────────────────────────
# # JOB-TITLE KEYWORDS — used to identify experience header lines
# # ──────────────────────────────────────────────────────────────────────────────

# JOB_TITLE_KEYWORDS = [
#     "engineer", "developer", "programmer", "coder", "architect",
#     "designer", "analyst", "scientist", "researcher",
#     "manager", "director", "lead", "head", "vp", "president",
#     "officer", "cto", "ceo", "coo", "ciso", "cfo",
#     "consultant", "advisor", "specialist", "expert",
#     "associate", "assistant", "coordinator", "administrator",
#     "intern", "trainee", "apprentice",
#     "instructor", "professor", "lecturer", "teacher",
#     "technician", "operator", "representative",
# ]

# # ──────────────────────────────────────────────────────────────────────────────
# # SKILL NORMALIZATION MAP — map common aliases to canonical name
# # ──────────────────────────────────────────────────────────────────────────────

# SKILL_ALIASES = {
#     "js": "JavaScript", "javascript": "JavaScript",
#     "ts": "TypeScript", "typescript": "TypeScript",
#     "py": "Python", "python": "Python",
#     "cpp": "C++", "c++": "C++", "c plus plus": "C++",
#     "golang": "Go", "go lang": "Go",
#     "nodejs": "Node.js", "node.js": "Node.js", "node js": "Node.js",
#     "reactjs": "React", "react.js": "React",
#     "vuejs": "Vue.js", "vue.js": "Vue.js",
#     "angularjs": "Angular", "angular.js": "Angular",
#     "k8s": "Kubernetes",
#     "aws": "AWS", "amazon web services": "AWS",
#     "gcp": "GCP", "google cloud": "GCP",
#     "azure": "Azure", "microsoft azure": "Azure",
#     "ml": "Machine Learning", "dl": "Deep Learning",
#     "nlp": "NLP", "cv": "Computer Vision",
#     "sql": "SQL", "mysql": "MySQL", "postgresql": "PostgreSQL",
#     "mongo": "MongoDB", "mongodb": "MongoDB",
#     "tf": "TensorFlow", "tensorflow": "TensorFlow",
#     "pytorch": "PyTorch",
#     "rest": "REST API", "restapi": "REST API",
#     "graphql": "GraphQL",
#     "html5": "HTML", "css3": "CSS",
#     "git": "Git", "github": "GitHub", "gitlab": "GitLab",
#     "linux": "Linux", "unix": "Unix",
#     "docker": "Docker", "kubernetes": "Kubernetes",
#     "ci/cd": "CI/CD", "cicd": "CI/CD",
#     "agile": "Agile", "scrum": "Scrum", "kanban": "Kanban",
#     "oop": "OOP", "dsa": "DSA",
# }

# # ──────────────────────────────────────────────────────────────────────────────
# # GPA PATTERNS
# # ──────────────────────────────────────────────────────────────────────────────

# GPA_PATTERN = (
#     r'(?:GPA|CGPA|CPI|SPI|Score|Percentage|%|Grade)\s*[:\-]?\s*'
#     r'(\d{1,2}(?:\.\d{1,2})?)'
#     r'(?:\s*(?:/|out\s*of)\s*(\d{1,2}(?:\.\d{1,2})?))?'
# )

# # ──────────────────────────────────────────────────────────────────────────────
# # HELPER FUNCTIONS
# # ──────────────────────────────────────────────────────────────────────────────

# def find_pattern(text: str, pattern: str, flags: int = re.IGNORECASE) -> str | None:
#     """Return first match or None."""
#     m = re.search(pattern, text, flags)
#     return m.group(0) if m else None

# def find_all_patterns(text: str, pattern: str, flags: int = re.IGNORECASE) -> list[str]:
#     """Return all non-overlapping matches."""
#     return re.findall(pattern, text, flags)

# def normalize_whitespace(s: str) -> str:
#     """Collapse internal whitespace to single space."""
#     return re.sub(r'\s+', ' ', s).strip()