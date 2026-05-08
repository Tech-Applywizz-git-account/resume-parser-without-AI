# segmenter.py

from rapidfuzz import process, fuzz
import re
from .patterns import HEADERS as SECTION_HEADERS

def segment_resume(text):
    """Segment the resume text into sections based on headers."""
    lines = text.split('\n')
    sections = {
        "personal": "",
        "summary": "",
        "skills": "",
        "experience": "",
        "projects": "",
        "education": "",
        "certifications": "",
        "achievements": ""
    }
    
    current_section = "personal"
    
    for line in lines:
        clean_line = line.strip().lower()
        if not clean_line:
            continue
            
        # Check if line is a header
        found_header = False
        for section, keywords in SECTION_HEADERS.items():
            # Use fuzzy matching for headers
            # Scorers: token_sort_ratio is good for headers like "Work Experience" vs "Experience"
            best_match = process.extractOne(clean_line, keywords, scorer=fuzz.token_sort_ratio)
            
            # Heuristic: Headers are usually short and have high match score
            if best_match and best_match[1] > 85 and len(clean_line.split()) < 5:
                current_section = section
                found_header = True
                break
        
        if not found_header:
            sections[current_section] += line + "\n"
            
    return sections








# """
# segmenter.py — Splits a resume into named sections.

# Veteran notes
# ─────────────
# • A header can be ALL CAPS, Title Case, or even sentence case.
# • A header can be prefixed with emoji (📌 Experience) or Unicode symbols.
# • A header can be separated from content by a decorative rule (═══, ───).
# • Two-column resumes sometimes have headers in the left gutter; pdfplumber's
#   word-position sorting (done in text_utils) normalises these before we see them.
# • Fuzzy matching alone isn't enough — we also check:
#     – line length (headers are short, ≤ 7 words)
#     – trailing colon  ("Skills:")
#     – ALL-CAPS boost
#     – exact-match shortcut
# • We keep a "personal" bucket for everything before the first detected header
#   (name, contact details, title line).
# """

# import re
# from rapidfuzz import process, fuzz
# from .patterns import HEADERS as SECTION_HEADERS

# # ──────────────────────────────────────────────────────────────────────────────
# # Constants
# # ──────────────────────────────────────────────────────────────────────────────

# _DECO_CHARS = frozenset('─━═—–_=*#~•◆■□▪▫●○◉►▶→←↑↓|+')

# _BULLET_RE     = re.compile(r'^[\s\u2022\u25cf\u25aa\u25ab\u25e6\u2023\u25b8\u2013\u2014\-\*]+')
# _NUMBER_RE     = re.compile(r'^\s*\d+[\.\)]\s*')
# _EMOJI_RE      = re.compile(r'[\U00010000-\U0010ffff\u2600-\u26FF\u2700-\u27BF]')
# _DECO_STRIP_RE = re.compile(r'[─━═—–_=*#~•◆■□▪▫●○◉►▶→←|]+')
# _COLON_STRIP   = re.compile(r'[:]+$')

# # Fuzzy score thresholds
# _EXACT_SCORE    = 100
# _HIGH_SCORE     = 88   # confident
# _MEDIUM_SCORE   = 78   # acceptable with extra signals (all-caps / short line)

# # ──────────────────────────────────────────────────────────────────────────────
# # Helpers
# # ──────────────────────────────────────────────────────────────────────────────

# def _is_decorative(line: str) -> bool:
#     """Return True for pure separator lines like ─────── or ============."""
#     s = line.strip()
#     if len(s) < 3:
#         return False
#     unique = set(s.replace(' ', ''))
#     return len(unique) <= 2 and unique.issubset(_DECO_CHARS)


# def _normalize_for_match(raw: str) -> str:
#     """
#     Strip all the noise so we can fuzzy-match against clean keyword lists.
#     """
#     s = raw.strip()
#     s = _EMOJI_RE.sub(' ', s)          # remove emoji
#     s = _DECO_STRIP_RE.sub(' ', s)     # remove deco chars
#     s = _BULLET_RE.sub('', s)          # leading bullets
#     s = _NUMBER_RE.sub('', s)          # leading "1." or "1)"
#     s = _COLON_STRIP.sub('', s)        # trailing colon  "Skills:"
#     s = re.sub(r'\s+', ' ', s).strip().lower()
#     return s


# def _is_all_caps(raw: str) -> bool:
#     alpha_only = re.sub(r'[^a-zA-Z]', '', raw)
#     return len(alpha_only) >= 3 and alpha_only.isupper()


# def detect_section_header(line: str) -> tuple[str | None, int]:
#     """
#     Return (section_name, confidence_score) or (None, 0).

#     Confidence is 0-100.  Callers should accept ≥ 78 as a header.
#     """
#     raw = line.strip()
#     if not raw or len(raw) > 90:
#         return None, 0

#     normalized = _normalize_for_match(raw)
#     if not normalized:
#         return None, 0

#     word_count = len(normalized.split())
#     if word_count > 7:   # real headers are short
#         return None, 0

#     all_caps   = _is_all_caps(raw)
#     title_case = raw.istitle()

#     best_section, best_score = None, 0

#     for section, keywords in SECTION_HEADERS.items():
#         # 1. Exact match shortcut
#         if normalized in keywords or normalized in [k.lower() for k in keywords]:
#             return section, _EXACT_SCORE

#         # 2. Fuzzy match
#         result = process.extractOne(
#             normalized, keywords,
#             scorer=fuzz.token_sort_ratio,
#             score_cutoff=60,
#         )
#         if result is None:
#             continue
#         score = result[1]

#         # Boost signals
#         if all_caps:
#             score = min(100, score + 12)
#         if title_case and word_count <= 3:
#             score = min(100, score + 6)
#         if word_count == 1:
#             score = min(100, score + 5)   # single-word headers are usually real
#         if raw.endswith(':'):
#             score = min(100, score + 8)

#         if score > best_score:
#             best_score = score
#             best_section = section

#     threshold = _HIGH_SCORE
#     # Relax threshold for all-caps short lines — they're almost always headers
#     if all_caps and word_count <= 4:
#         threshold = _MEDIUM_SCORE

#     return (best_section, best_score) if best_score >= threshold else (None, 0)


# # ──────────────────────────────────────────────────────────────────────────────
# # Main segmenter
# # ──────────────────────────────────────────────────────────────────────────────

# def segment_resume(text: str) -> dict[str, str]:
#     """
#     Segment resume text into labelled sections.

#     Returns a dict whose keys are section names and values are the raw text
#     (with newlines preserved) belonging to that section.
#     """
#     sections: dict[str, str] = {
#         "personal":       "",
#         "summary":        "",
#         "skills":         "",
#         "experience":     "",
#         "projects":       "",
#         "education":      "",
#         "certifications": "",
#         "achievements":   "",
#         "languages":      "",
#         "volunteer":      "",
#         "publications":   "",
#     }

#     current = "personal"
#     lines   = text.split('\n')

#     # ── Pass 1: line-by-line classification ──────────────────────────────────
#     for line in lines:
#         # Pure decorative separators → skip
#         if _is_decorative(line):
#             continue

#         stripped = line.strip()

#         # Blank lines are structural; preserve them in the current section
#         if not stripped:
#             sections[current] += '\n'
#             continue

#         section, score = detect_section_header(stripped)
#         if section:
#             current = section
#         else:
#             sections[current] += line + '\n'

#     # ── Pass 2: trim each section ─────────────────────────────────────────────
#     for key in sections:
#         sections[key] = sections[key].strip()

#     return sections