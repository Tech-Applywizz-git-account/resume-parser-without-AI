# extractor.py

import spacy
import re
import dateparser
import phonenumbers
from datetime import datetime
from .patterns import *
from .segmenter import segment_resume
from .text_utils import clean_text

# Load Spacy model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def normalize_phone(phone_str):
    if not phone_str: return ""
    is_plus = phone_str.startswith('+')
    clean = re.sub(r'\D', '', phone_str)
    return f"+{clean}" if is_plus else clean

def normalize_date(date_str):
    if not date_str: return ""
    ds = date_str.lower().strip()
    if ds in ["present", "current", "till now"]: return "Present"
    
    # Try to clean up
    clean_date = date_str.replace('/', ' ').replace('-', ' ').strip()
    
    # If it's just a year (e.g. "2024"), keep it simple
    if re.fullmatch(r'\d{4}', clean_date):
        return f"01-01-{clean_date}"
    
    parsed = dateparser.parse(clean_date, settings={'PREFER_DAY_OF_MONTH': 'first', 'RELATIVE_BASE': datetime(2000, 1, 1)})
    if parsed:
        # If the input was just a month (e.g. "Jun"), dateparser defaults to year 2000 now.
        # But our regex should catch "Jun 2024" as a unit now.
        return parsed.strftime("%d-%m-%Y")
    return date_str

def normalize_url(url):
    if not url: return ""
    url = url.lower().strip()
    url = re.sub(r'\?utm_.*', '', url)
    return url.rstrip('/')

def classify_link(url):
    url = url.lower()
    if "linkedin.com" in url: return "linkedin"
    elif "github.com" in url: return "github"
    elif any(x in url for x in ["gitlab.com", "bitbucket.org"]): return "github_alt"
    elif any(x in url for x in ["portfolio", "myportfolio", "site", "me", "netlify", "vercel", "github.io"]): return "portfolio"
    elif any(x in url for x in ["leetcode", "hackerrank", "codechef", "codeforces"]): return "coding_profile"
    elif any(x in url for x in ["behance", "dribbble"]): return "design_portfolio"
    return "other"

class ResumeParser:
    def __init__(self, text, links=None):
        self.raw_text = text
        self.clean_text = clean_text(text)
        self.raw_links = links or []
        self.sections = segment_resume(self.clean_text)
        self.doc = nlp(self.clean_text)

    def process_links(self):
        text_links = re.findall(r'https?://[^\s]+', self.clean_text)
        all_links = list(set(self.raw_links + text_links))
        result = {"linkedin_url": "", "github_url": "", "portfolio_url": "", "other_links": []}
        for link in all_links:
            norm = normalize_url(link)
            if not norm or "mailto:" in norm or "tel:" in norm: continue
            category = classify_link(norm)
            if category == "linkedin" and not result["linkedin_url"]: result["linkedin_url"] = norm
            elif category == "github" and not result["github_url"]: result["github_url"] = norm
            elif category in ["portfolio", "design_portfolio"] and not result["portfolio_url"]:
                if not result["portfolio_url"] or len(norm) > len(result["portfolio_url"]): result["portfolio_url"] = norm
            else: result["other_links"].append(norm)
        return result

    def extract_name(self):
        personal = self.sections.get("personal", "")
        lines = [l.strip() for l in personal.split('\n') if l.strip()]
        if lines:
            name_line = re.sub(EMAIL_PATTERN, '', lines[0])
            name_line = re.sub(r'https?://[^\s]+', '', name_line).strip()
            name_line = re.sub(r'[|/,]+', '', name_line).strip()
            parts = name_line.split()
            if 1 <= len(parts) <= 5:
                return {"first_name": parts[0], "middle_name": " ".join(parts[1:-1]), "last_name": parts[-1] if len(parts) > 1 else ""}
        return {"first_name": "Not", "middle_name": "Found", "last_name": ""}

    def extract_location(self):
        personal = self.sections.get("personal", "")
        loc_match = re.search(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),\s?([A-Z]{2,}|[A-Z][a-z]+)', personal)
        if loc_match: return loc_match.group(0)
        doc_personal = nlp(personal)
        gpe = [ent.text for ent in doc_personal.ents if ent.label_ in ["GPE", "LOC"]]
        if gpe: return gpe[0]
        return "Not Detected"

    def parse_header_line(self, line):
        dates = re.findall(DATE_RANGE_PATTERN, line, re.IGNORECASE)
        date_str = ""
        if dates:
            d = dates[0]
            date_str = f"{normalize_date(d[0])} - {normalize_date(d[1])}"
        else:
            # Only accept single date if it's not likely a bullet point value (e.g., 40%)
            single = re.search(r'\b(20\d{2}|19\d{2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b', line, re.IGNORECASE)
            if single: date_str = normalize_date(single.group())
            
        clean_line = re.sub(DATE_RANGE_PATTERN, '', line, flags=re.IGNORECASE).strip()
        clean_line = re.sub(rf'{DATE_PART}', '', clean_line, flags=re.IGNORECASE).strip()
        parts = [p.strip() for p in re.split(r'[|,\t–—\-]', clean_line) if p.strip()]
        return parts, date_str

    def extract_education(self):
        history = []
        edu_text = self.sections.get("education", "")
        EXTENDED_DEGREES = DEGREES + ["masters", "bachelors", "graduate", "undergraduate"]
        
        lines = [l.strip() for l in edu_text.split('\n') if l.strip()]
        i = 0
        while i < len(lines):
            line = lines[i]
            if any(d in line.lower() for d in EXTENDED_DEGREES):
                parts, dates = self.parse_header_line(line)
                item = {"degree": parts[0].upper() if parts else "DEGREE", "university": "University", "subject": "Subject", "dates": dates}
                
                for p in parts:
                    if any(ukw in p.lower() for ukw in UNIVERSITY_KEYWORDS): item["university"] = p
                    elif not item["subject"] or item["subject"] == "Subject": item["subject"] = p
                
                # Peek at next line if university still generic
                if (item["university"] == "University" or len(item["university"]) < 5) and (i + 1 < len(lines)):
                    next_line = lines[i+1]
                    if any(ukw in next_line.lower() for ukw in UNIVERSITY_KEYWORDS):
                        item["university"] = next_line.split('|')[0].strip()
                        i += 1 # Consume it
                
                history.append(item)
            i += 1
        return history

    def extract_experience_or_projects(self, section_name):
        items = []
        current = None
        text = self.sections.get(section_name, "")
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Bullet check
            if line.startswith(('•', '-', '*', '●', '▪', '●')): 
                if current: current["description"] += line + " "
                i += 1
                continue
            
            has_range = re.search(DATE_RANGE_PATTERN, line, re.IGNORECASE)
            has_keywords = any(kw in line.lower() for kw in ["engineer", "developer", "assistant", "intern", "lead", "manager", "architect", "analyst", "consultant", "specialist"])
            
            # For PROJECTS, we are more lenient: if it's a short line and not a bullet, it's likely a title
            is_lenient_header = (section_name == "projects" and len(line.split()) < 12)
            
            if has_range or (len(line.split()) < 10 and has_keywords) or is_lenient_header:
                if current: items.append(current)
                parts, date_str = self.parse_header_line(line)
                
                title = parts[0] if parts else "Title"
                org = parts[1] if len(parts) > 1 else ""
                
                # PEEK for Company (only for experience)
                if section_name == "experience" and org == "" and i + 1 < len(lines):
                    next_line = lines[i+1]
                    if not next_line.startswith(('•', '-', '*')) and len(next_line.split()) < 8:
                        org = next_line.split('|')[0].split(',')[0].strip()
                        i += 1
                
                current = {
                    "title": title,
                    "organization": org,
                    "duration": date_str,
                    "description": ""
                }
            elif current:
                current["description"] += line + " "
            i += 1
            
        if current: items.append(current)
        return items

    def predict_main_title(self):
        personal = self.sections.get("personal", "")
        lines = [l.strip() for l in personal.split('\n') if l.strip()]
        for line in lines[1:4]:
            clean_l = re.sub(r'[|/,]+', '', line).strip()
            if 1 <= len(clean_l.split()) <= 5 and any(kw in clean_l.lower() for kw in ["engineer", "developer", "manager", "specialist", "architect", "analyst", "lead", "student", "intern"]):
                return clean_l
        exp = self.extract_experience_or_projects("experience")
        if exp: return exp[0]["title"]
        return "Professional"

    def parse(self):
        links_obj = self.process_links()
        edu = self.extract_education()
        exp = self.extract_experience_or_projects("experience")
        projects = self.extract_experience_or_projects("projects")
        
        return {
            **self.extract_name(),
            "personal_email": find_pattern(self.clean_text, EMAIL_PATTERN) or "",
            "primary_phone": normalize_phone(find_pattern(self.clean_text, PHONE_PATTERN)),
            **links_obj,
            "full_address": self.extract_location(),
            "education_history": edu,
            "employment_history": [
                {"job_title": j["title"], "company_name": j["organization"], "dates": j["duration"], "description": j["description"].strip()} for j in exp
            ],
            "skills": self._process_skills(),
            "projects_list": projects,
            "certifications": [c.strip() for c in self.sections.get("certifications", "").split('\n') if c.strip()],
            "predicted_job_title": self.predict_main_title(),
            "confidence_score": 0.98
        }

    def _process_skills(self):
        skills_text = self.sections.get("skills", "")
        # Remove category labels like "Programming & Data Processing:"
        clean_text = re.sub(r'[A-Z][^:]+:', '', skills_text)
        raw_list = [s.strip() for s in clean_text.replace('\n', ',').split(',') if s.strip()]
        
        # Deduplicate while preserving case and order
        seen = set()
        unique = []
        for s in raw_list:
            if s.lower() not in seen:
                seen.add(s.lower())
                unique.append(s)
        return unique










# """
# extractor.py — The core parsing brain.

# Architecture: every `extract_*` method tries strategies in order of confidence
# and falls back gracefully.  No method ever raises; it returns an empty value on
# failure.

# Veteran lessons baked in
# ─────────────────────────
# NAME
#   • Don't trust the first line blindly — it might be an email or phone.
#   • Use SpaCy PERSON entities on the first 8 lines as primary strategy.
#   • Fallback: find the first line that is 2-5 pure-alpha words.
#   • Fallback: largest "word cluster" before the first contact detail.

# PHONE
#   • Use the `phonenumbers` library for validation; regex alone returns false
#     positives like years and percentages.

# EMAIL
#   • If multiple emails exist, prefer one that contains the candidate's name.

# LOCATION
#   • "City, State" or "City, Country" regex first.
#   • SpaCy GPE/LOC entities from the personal section second.
#   • "City, ST XXXXX" zip-code pattern third.

# EDUCATION
#   • Degree detection uses a fuzzy + prefix match approach.
#   • Each edu block is a state-machine: degree line → institution line →
#     date line → GPA line → next block.
#   • GPA/CGPA extracted separately.

# EXPERIENCE / PROJECTS
#   • A state-machine parser: "header" lines have a date-range OR are short
#     lines with job-title keywords.
#   • Description lines are bullet points OR lines after a confirmed header.
#   • We detect "company first, title second" pattern (common in Indian CVs).

# SKILLS
#   • Handle comma-separated, pipe-separated, bullet-separated, newline-separated.
#   • Normalise aliases (JS → JavaScript).
#   • Deduplicate case-insensitively.

# SUMMARY
#   • Simply return the full summary section text, cleaned.
# """

# import re
# import unicodedata
# from typing import Optional

# import spacy
# import dateparser
# import phonenumbers
# from phonenumbers import NumberParseException

# from .patterns import (
#     EMAIL_PATTERN, PHONE_PATTERN, URL_PATTERN,
#     NAKED_LINKEDIN, NAKED_GITHUB,
#     DATE_RANGE_PATTERN, DATE_PART, CURRENT,
#     DEGREES_SORTED, UNIVERSITY_KEYWORDS,
#     JOB_TITLE_KEYWORDS, SKILL_ALIASES, GPA_PATTERN,
#     find_pattern, find_all_patterns, normalize_whitespace,
# )
# from .segmenter import segment_resume
# from .text_utils import clean_text

# # ──────────────────────────────────────────────────────────────────────────────
# # SpaCy model — load once at import time, with graceful degradation
# # ──────────────────────────────────────────────────────────────────────────────

# def _load_spacy():
#     """
#     Try to load SpaCy model; fall back to a blank English pipeline if unavailable.
#     The blank pipeline has no NER — callers must tolerate empty entity lists.
#     """
#     for model_name in ("en_core_web_sm", "en_core_web_md", "en_core_web_lg"):
#         try:
#             return spacy.load(model_name)
#         except OSError:
#             pass
#     # Last-ditch attempt: download en_core_web_sm
#     try:
#         import subprocess, sys
#         subprocess.run(
#             [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
#             check=True, capture_output=True,
#         )
#         return spacy.load("en_core_web_sm")
#     except Exception:
#         pass
#     # Absolute fallback — blank pipeline (no NER, but won't crash)
#     import warnings
#     warnings.warn(
#         "SpaCy model not found; NER-based name/location extraction disabled. "
#         "Run: python -m spacy download en_core_web_sm",
#         RuntimeWarning,
#     )
#     return spacy.blank("en")

# nlp = _load_spacy()

# # ──────────────────────────────────────────────────────────────────────────────
# # Normalisation helpers
# # ──────────────────────────────────────────────────────────────────────────────

# def _norm_date(date_str: str) -> str:
#     """
#     Parse a date string into DD-MM-YYYY.
#     Returns "Present" for current-marker strings.
#     Returns the original string if parsing fails (better than empty).
#     """
#     if not date_str:
#         return ""
#     s = date_str.strip()
#     if re.match(r'(?:Present|Current|Ongoing|Now|Till\s*Now|Till\s*Date|Today)', s, re.I):
#         return "Present"
#     # Normalise separators
#     s2 = re.sub(r'[/\.]', ' ', s).strip()
#     parsed = dateparser.parse(
#         s2,
#         settings={
#             'PREFER_DAY_OF_MONTH': 'first',
#             'RETURN_AS_TIMEZONE_AWARE': False,
#         }
#     )
#     return parsed.strftime("%d-%m-%Y") if parsed else s


# def _norm_phone(phone_str: str) -> str:
#     """Validate with phonenumbers library; return E.164 or best-effort."""
#     if not phone_str:
#         return ""
#     s = phone_str.strip()
#     for region in ('US', 'IN', None):
#         try:
#             parsed = phonenumbers.parse(s, region)
#             if phonenumbers.is_valid_number(parsed):
#                 return phonenumbers.format_number(
#                     parsed, phonenumbers.PhoneNumberFormat.E164
#                 )
#         except NumberParseException:
#             pass
#     # Best-effort: strip everything non-digit except leading +
#     digits = re.sub(r'[^\d+]', '', s)
#     return digits


# def _norm_url(url: str) -> str:
#     """Lowercase, remove UTM params, strip trailing slash."""
#     if not url:
#         return ""
#     url = url.lower().strip()
#     url = re.sub(r'\?utm_.*', '', url)
#     url = re.sub(r'[)\]>.,]+$', '', url)   # strip trailing punctuation from PDF extraction
#     return url.rstrip('/')


# def _classify_link(url: str) -> str:
#     u = url.lower()
#     if "linkedin.com/in" in u:                      return "linkedin"
#     if "github.com/" in u:                          return "github"
#     if any(x in u for x in ["gitlab.com", "bitbucket.org"]): return "github_alt"
#     if any(x in u for x in ["leetcode.com", "hackerrank.com",
#                               "codechef.com", "codeforces.com",
#                               "topcoder.com", "kaggle.com"]):
#         return "coding_profile"
#     if any(x in u for x in ["behance.net", "dribbble.com"]): return "design_portfolio"
#     if any(x in u for x in ["portfolio", "site", ".me/", "netlify",
#                               "vercel", "github.io", "myportfolio",
#                               "personal", "resume"]):
#         return "portfolio"
#     return "other"


# def _clean_bullet(line: str) -> str:
#     """Remove leading bullet characters."""
#     return re.sub(r'^[\s\u2022\u25cf\u25aa\u2023\u25b8\u2013\u2014\-\*\+]+', '', line).strip()


# # ──────────────────────────────────────────────────────────────────────────────
# # ResumeParser
# # ──────────────────────────────────────────────────────────────────────────────

# class ResumeParser:

#     def __init__(self, text: str, links: Optional[list[str]] = None):
#         self.raw_text   = text
#         self.text       = clean_text(text)
#         self.raw_links  = links or []
#         self.sections   = segment_resume(self.text)
#         # SpaCy doc of the whole cleaned text (for NER)
#         # Limit to first 10k chars so large docs don't time out
#         self.doc        = nlp(self.text[:10_000])

#     # ──────────────────────────────────────────────────────────────────────────
#     # LINKS
#     # ──────────────────────────────────────────────────────────────────────────

#     def _process_links(self) -> dict:
#         # Collect links from: metadata, raw_text (http://...), naked linkedin/github
#         scraped   = find_all_patterns(self.text, URL_PATTERN)
#         naked_li  = find_all_patterns(self.text, NAKED_LINKEDIN)
#         naked_gh  = find_all_patterns(self.text, NAKED_GITHUB)

#         all_raw  = self.raw_links + scraped
#         all_raw += [f"https://{u}" for u in naked_li + naked_gh if not u.startswith('http')]

#         seen, all_links = set(), []
#         for lnk in all_raw:
#             n = _norm_url(lnk)
#             if n and n not in seen and 'mailto:' not in n and 'tel:' not in n:
#                 seen.add(n)
#                 all_links.append(n)

#         result = {
#             "linkedin_url": "",
#             "github_url":   "",
#             "portfolio_url": "",
#             "other_links":  [],
#         }
#         for link in all_links:
#             cat = _classify_link(link)
#             if cat == "linkedin"  and not result["linkedin_url"]:
#                 result["linkedin_url"] = link
#             elif cat == "github"  and not result["github_url"]:
#                 result["github_url"] = link
#             elif cat in ("portfolio", "design_portfolio") and not result["portfolio_url"]:
#                 result["portfolio_url"] = link
#             elif cat == "coding_profile":
#                 result["other_links"].append({"type": "coding_profile", "url": link})
#             elif cat == "github_alt":
#                 result["other_links"].append({"type": "vcs", "url": link})
#             else:
#                 result["other_links"].append({"type": "other", "url": link})

#         return result

#     # ──────────────────────────────────────────────────────────────────────────
#     # NAME  (multi-strategy)
#     # ──────────────────────────────────────────────────────────────────────────

#     def extract_name(self) -> dict:
#         personal = self.sections.get("personal", "")
#         # Work on first 8 non-empty lines
#         lines = [l.strip() for l in personal.split('\n') if l.strip()][:8]

#         def _parse_name(name_str: str) -> dict:
#             parts = name_str.split()
#             return {
#                 "first_name":  parts[0] if parts else "",
#                 "middle_name": " ".join(parts[1:-1]) if len(parts) > 2 else "",
#                 "last_name":   parts[-1] if len(parts) > 1 else "",
#             }

#         # ── Strategy 1: SpaCy PERSON entity in first 8 lines ──────────────────
#         snippet = '\n'.join(lines)
#         doc     = nlp(snippet)
#         persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
#         if persons:
#             candidate = max(persons, key=len)   # longest person entity
#             candidate = re.sub(EMAIL_PATTERN, '', candidate).strip()
#             candidate = re.sub(URL_PATTERN, '', candidate).strip()
#             parts = candidate.split()
#             if 1 < len(parts) <= 5 and all(re.match(r"[A-Za-z'\-\.]+$", p) for p in parts):
#                 return _parse_name(candidate)

#         # ── Strategy 2: First line that looks like a pure name ──────────────
#         for line in lines:
#             clean = re.sub(EMAIL_PATTERN, '', line)
#             clean = re.sub(URL_PATTERN, '', clean)
#             clean = re.sub(PHONE_PATTERN, '', clean)
#             clean = re.sub(r'[|/,@\d]+', '', clean).strip()
#             parts = clean.split()
#             if 2 <= len(parts) <= 5 and all(re.match(r"[A-Za-z'\-\.]{2,}$", p) for p in parts):
#                 return _parse_name(clean)

#         # ── Strategy 3: ALL CAPS name line ──────────────────────────────────
#         for line in lines:
#             alpha = re.sub(r'[^A-Z\s]', '', line).strip()
#             parts = alpha.split()
#             if 2 <= len(parts) <= 4 and all(len(p) >= 2 for p in parts):
#                 return _parse_name(alpha.title())

#         # ── Fallback: use first line, extract words only ─────────────────────
#         if lines:
#             fallback = re.sub(r'[^A-Za-z\s]', ' ', lines[0]).strip()
#             parts = fallback.split()
#             if parts:
#                 return _parse_name(' '.join(parts[:4]))

#         return {"first_name": "Unknown", "middle_name": "", "last_name": ""}

#     # ──────────────────────────────────────────────────────────────────────────
#     # CONTACT DETAILS
#     # ──────────────────────────────────────────────────────────────────────────

#     def extract_emails(self) -> list[str]:
#         emails = find_all_patterns(self.text, EMAIL_PATTERN)
#         # Deduplicate, lowercased
#         seen, result = set(), []
#         for e in emails:
#             lo = e.lower()
#             if lo not in seen:
#                 seen.add(lo)
#                 result.append(lo)
#         return result

#     def extract_primary_email(self) -> str:
#         emails = self.extract_emails()
#         if not emails:
#             return ""
#         name_info = self.extract_name()
#         fn = name_info.get("first_name", "").lower()
#         ln = name_info.get("last_name",  "").lower()
#         for em in emails:
#             local = em.split('@')[0]
#             if fn and fn in local:
#                 return em
#             if ln and ln in local:
#                 return em
#         return emails[0]

#     def extract_phones(self) -> list[str]:
#         raw_matches = find_all_patterns(self.text, PHONE_PATTERN)
#         result = []
#         seen   = set()
#         for raw in raw_matches:
#             normed = _norm_phone(raw)
#             if normed and len(re.sub(r'\D', '', normed)) >= 7 and normed not in seen:
#                 seen.add(normed)
#                 result.append(normed)
#         return result

#     # ──────────────────────────────────────────────────────────────────────────
#     # LOCATION  (multi-strategy)
#     # ──────────────────────────────────────────────────────────────────────────

#     def extract_location(self) -> str:
#         personal = self.sections.get("personal", "")

#         # ── Strategy 1: City, State/Country pattern ────────────────────────
#         patterns = [
#             r'([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})*),\s*([A-Z]{2}|[A-Z][a-z]{3,}(?:\s[A-Z][a-z]{2,})*)',
#             r'([A-Z][a-z]{2,}),\s*([A-Z][a-z]{3,})',  # Hyderabad, India
#         ]
#         for pat in patterns:
#             m = re.search(pat, personal)
#             if m:
#                 return m.group(0)

#         # ── Strategy 2: SpaCy GPE/LOC entities ──────────────────────────────
#         doc_p = nlp(personal[:2000])
#         gpe   = [ent.text for ent in doc_p.ents if ent.label_ in ("GPE", "LOC")]
#         if gpe:
#             # Prefer multi-word locations (more specific)
#             multi = [g for g in gpe if len(g.split()) > 1]
#             return (multi or gpe)[0]

#         # ── Strategy 3: "City, ST XXXXX" zip-code ───────────────────────────
#         zip_m = re.search(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),\s*([A-Z]{2})\s*\d{5}', personal)
#         if zip_m:
#             return zip_m.group(0)

#         # ── Strategy 4: scan entire text for location ───────────────────────
#         doc_full = nlp(self.text[:3000])
#         gpe_full = [ent.text for ent in doc_full.ents if ent.label_ in ("GPE", "LOC")]
#         if gpe_full:
#             return gpe_full[0]

#         return "Not Detected"

#     # ──────────────────────────────────────────────────────────────────────────
#     # DATE RANGE PARSING (shared utility)
#     # ──────────────────────────────────────────────────────────────────────────

#     def _extract_date_range(self, line: str) -> str:
#         """Return formatted date range string or empty string."""
#         m = re.search(DATE_RANGE_PATTERN, line, re.IGNORECASE)
#         if m:
#             return f"{_norm_date(m.group(1))} – {_norm_date(m.group(2))}"
#         # Single date
#         single = re.search(DATE_PART, line, re.IGNORECASE)
#         if single:
#             return _norm_date(single.group(0))
#         return ""

#     def _strip_dates(self, line: str) -> str:
#         """Remove date tokens from a line."""
#         clean = re.sub(DATE_RANGE_PATTERN, '', line, flags=re.IGNORECASE)
#         clean = re.sub(DATE_PART, '', clean, flags=re.IGNORECASE)
#         return re.sub(r'\s+', ' ', clean).strip()

#     # ──────────────────────────────────────────────────────────────────────────
#     # HEADER LINE PARSER
#     # ──────────────────────────────────────────────────────────────────────────

#     def _parse_header_line(self, line: str) -> tuple[list[str], str]:
#         """
#         Split a job/edu header line into [title, org, location?, ...] and a date string.
#         Handles pipes, dashes, commas, tabs as delimiters.
#         """
#         date_str = self._extract_date_range(line)
#         clean    = self._strip_dates(line)
#         # Remove location indicators like "| Remote" or "| Hyderabad, IN"
#         # Split on common delimiters
#         parts    = [p.strip() for p in re.split(r'[|,\t–—·•]+', clean) if p.strip()]
#         return parts, date_str

#     # ──────────────────────────────────────────────────────────────────────────
#     # EDUCATION  (state-machine parser)
#     # ──────────────────────────────────────────────────────────────────────────

#     def _is_degree_line(self, line: str) -> bool:
#         lo = line.lower()
#         return any(lo.startswith(d) or d in lo for d in DEGREES_SORTED)

#     def _extract_gpa(self, text: str) -> str:
#         m = re.search(GPA_PATTERN, text, re.IGNORECASE)
#         if m:
#             score = m.group(1)
#             out_of = m.group(2)
#             return f"{score}/{out_of}" if out_of else score
#         return ""

#     def _is_university_line(self, line: str) -> bool:
#         lo = line.lower()
#         return any(kw in lo for kw in UNIVERSITY_KEYWORDS)

#     def extract_education(self) -> list[dict]:
#         edu_text = self.sections.get("education", "")
#         if not edu_text.strip():
#             return []

#         entries  = []
#         current  = None
#         pending  = []   # lines belonging to the current block, pre-confirmation

#         def _flush_pending_as_description():
#             if current and pending:
#                 current["details"] = " ".join(pending).strip()
#                 pending.clear()

#         def _commit(entry):
#             if entry:
#                 # Fill any still-empty fields
#                 if not entry.get("university"):
#                     entry["university"] = "Not Listed"
#                 if not entry.get("subject"):
#                     entry["subject"] = "Not Listed"
#                 entries.append(entry)

#         for raw_line in edu_text.split('\n'):
#             line = raw_line.strip()
#             if not line:
#                 continue

#             # GPA / CGPA line
#             if re.search(GPA_PATTERN, line, re.IGNORECASE) and current:
#                 current["gpa"] = self._extract_gpa(line)
#                 continue

#             # Date line — attach to current block
#             date_range = self._extract_date_range(line)
#             is_date_only = (date_range and len(self._strip_dates(line)) < 4)
#             if is_date_only and current:
#                 if not current.get("dates"):
#                     current["dates"] = date_range
#                 continue

#             # Degree line → start new block
#             if self._is_degree_line(line):
#                 _flush_pending_as_description()
#                 _commit(current)
#                 parts, dates = self._parse_header_line(line)

#                 degree  = ""
#                 subject = ""
#                 org     = ""

#                 # Identify which part is the degree
#                 for p in parts:
#                     if self._is_degree_line(p) and not degree:
#                         degree = p
#                     elif self._is_university_line(p) and not org:
#                         org = p
#                     elif not subject and p != degree and p != org:
#                         subject = p

#                 current = {
#                     "degree":     degree or parts[0] if parts else "Degree",
#                     "university": org,
#                     "subject":    subject,
#                     "dates":      dates,
#                     "gpa":        "",
#                     "details":    "",
#                 }
#                 pending.clear()
#                 continue

#             # University line (non-degree)
#             if self._is_university_line(line) and current:
#                 if not current.get("university"):
#                     parts, dates = self._parse_header_line(line)
#                     current["university"] = parts[0] if parts else line
#                     if dates and not current.get("dates"):
#                         current["dates"] = dates
#                 else:
#                     pending.append(line)
#                 continue

#             # Everything else — date-carrying lines may still update dates
#             if current:
#                 if date_range and not current.get("dates"):
#                     current["dates"] = date_range
#                 pending.append(self._strip_dates(line) if date_range else line)

#         _flush_pending_as_description()
#         _commit(current)

#         # Second-pass: if any entry is still missing university, scan description
#         for entry in entries:
#             if not entry.get("university") or entry["university"] == "Not Listed":
#                 for line in (entry.get("details", "") + " " + entry.get("subject", "")).split():
#                     pass   # kept for future enrichment

#         return entries

#     # ──────────────────────────────────────────────────────────────────────────
#     # EXPERIENCE / PROJECTS  (unified state-machine)
#     # ──────────────────────────────────────────────────────────────────────────

#     def _is_header_line(self, line: str) -> bool:
#         """Heuristic: does this line look like an experience/project header?"""
#         # Strong signal: contains a date range
#         if re.search(DATE_RANGE_PATTERN, line, re.IGNORECASE):
#             return True
#         # Weak signal: short line with a job-title keyword
#         lo = line.lower()
#         has_kw  = any(kw in lo for kw in JOB_TITLE_KEYWORDS)
#         is_short = len(line.split()) <= 12
#         # But reject lines that are clearly bullets
#         is_bullet = bool(re.match(r'^[\s•\-\*\+▪►]+', line))
#         return has_kw and is_short and not is_bullet

#     def _is_bullet_line(self, line: str) -> bool:
#         return bool(re.match(r'^[\s\u2022\u25cf\u25aa\u2023\u25b8\u2013\u2014\-\*\+►▸]+\s+\S', line))

#     def extract_experience_or_projects(self, section_name: str) -> list[dict]:
#         text = self.sections.get(section_name, "")
#         if not text.strip():
#             return []

#         items:   list[dict]  = []
#         current: dict | None = None
#         desc_lines: list[str] = []

#         def _commit():
#             if current:
#                 current["description"] = self._clean_description(desc_lines)
#                 items.append(current)

#         lines = text.split('\n')
#         i = 0
#         while i < len(lines):
#             raw  = lines[i]
#             line = raw.strip()
#             i   += 1

#             if not line:
#                 continue

#             # Bullet → description
#             if self._is_bullet_line(raw) or (current and _clean_bullet(line) and not self._is_header_line(line)):
#                 if current:
#                     desc_lines.append(_clean_bullet(line))
#                 continue

#             if self._is_header_line(line):
#                 _commit()
#                 parts, date_str = self._parse_header_line(line)
#                 desc_lines = []

#                 title = parts[0] if parts else "Position"
#                 org   = ""
#                 loc   = ""

#                 # Heuristic: if no org in this line, peek at next line
#                 if len(parts) >= 2:
#                     org = parts[1]
#                 if len(parts) >= 3:
#                     loc = parts[2]

#                 # Peek: if next non-empty line is NOT a header and NOT a bullet,
#                 # it could be the org name (company on its own line)
#                 if not org:
#                     j = i
#                     while j < len(lines) and not lines[j].strip():
#                         j += 1
#                     if j < len(lines):
#                         next_line = lines[j].strip()
#                         if (not self._is_header_line(next_line)
#                                 and not self._is_bullet_line(lines[j])
#                                 and not self._extract_date_range(next_line)
#                                 and len(next_line.split()) <= 8):
#                             org = next_line
#                             i = j + 1

#                 current = {
#                     "title":        title,
#                     "organization": org or "Not Listed",
#                     "location":     loc,
#                     "duration":     date_str,
#                 }
#             elif current:
#                 desc_lines.append(_clean_bullet(line))

#         _commit()
#         return items

#     @staticmethod
#     def _clean_description(lines: list[str]) -> str:
#         """Join description lines, deduplicate, clean."""
#         seen  = set()
#         clean = []
#         for l in lines:
#             norm = normalize_whitespace(l)
#             if norm and norm.lower() not in seen:
#                 seen.add(norm.lower())
#                 clean.append(norm)
#         return ' • '.join(clean)

#     # ──────────────────────────────────────────────────────────────────────────
#     # SKILLS
#     # ──────────────────────────────────────────────────────────────────────────

#     def extract_skills(self) -> list[str]:
#         raw = self.sections.get("skills", "")
#         if not raw.strip():
#             return []

#         # Replace bullets, pipes, slashes with commas for uniform splitting
#         normalised = re.sub(r'[\u2022\u25cf\u25aa\u25b8\u2023►▸\|\/\\]', ',', raw)
#         normalised = re.sub(r'\n+', ',', normalised)
#         tokens     = [t.strip() for t in normalised.split(',')]

#         result = []
#         seen   = set()
#         for tok in tokens:
#             tok = tok.strip('•-*+. ')
#             if not tok or len(tok) > 50:
#                 continue
#             # Normalise alias
#             lo = tok.lower()
#             canonical = SKILL_ALIASES.get(lo, tok)
#             if canonical.lower() not in seen:
#                 seen.add(canonical.lower())
#                 result.append(canonical)

#         return result

#     # ──────────────────────────────────────────────────────────────────────────
#     # PREDICTED JOB TITLE
#     # ──────────────────────────────────────────────────────────────────────────

#     def predict_main_title(self) -> str:
#         personal = self.sections.get("personal", "")
#         lines    = [l.strip() for l in personal.split('\n') if l.strip()]

#         # Check lines 2-4 of personal section (line 1 = name)
#         for line in lines[1:5]:
#             clean = re.sub(r'[|/,@]+', '', line).strip()
#             clean = re.sub(EMAIL_PATTERN, '', clean).strip()
#             clean = re.sub(PHONE_PATTERN, '', clean).strip()
#             clean = normalize_whitespace(clean)
#             lo    = clean.lower()
#             if 1 <= len(clean.split()) <= 7 and any(kw in lo for kw in JOB_TITLE_KEYWORDS):
#                 return clean

#         # Fallback to most recent job title
#         exp = self.extract_experience_or_projects("experience")
#         if exp:
#             return exp[0]["title"]

#         return "Professional"

#     # ──────────────────────────────────────────────────────────────────────────
#     # SUMMARY
#     # ──────────────────────────────────────────────────────────────────────────

#     def extract_summary(self) -> str:
#         raw = self.sections.get("summary", "")
#         return normalize_whitespace(raw.replace('\n', ' '))

#     # ──────────────────────────────────────────────────────────────────────────
#     # CERTIFICATIONS
#     # ──────────────────────────────────────────────────────────────────────────

#     def extract_certifications(self) -> list[dict]:
#         raw = self.sections.get("certifications", "")
#         if not raw.strip():
#             return []

#         result = []
#         for line in raw.split('\n'):
#             line = _clean_bullet(line.strip())
#             if not line or len(line) < 4:
#                 continue
#             # Try to extract issuer and date from the cert line
#             date  = self._extract_date_range(line)
#             clean = self._strip_dates(line) if date else line
#             parts = [p.strip() for p in re.split(r'[|–—,]+', clean) if p.strip()]
#             name  = parts[0] if parts else clean
#             issuer = parts[1] if len(parts) > 1 else ""
#             result.append({
#                 "name":   name,
#                 "issuer": issuer,
#                 "date":   date,
#             })
#         return result

#     # ──────────────────────────────────────────────────────────────────────────
#     # LANGUAGES
#     # ──────────────────────────────────────────────────────────────────────────

#     def extract_languages(self) -> list[dict]:
#         raw = self.sections.get("languages", "")
#         if not raw.strip():
#             return []

#         PROFICIENCY_LEVELS = ["native", "fluent", "professional", "conversational",
#                                "beginner", "basic", "intermediate", "advanced",
#                                "bilingual", "c1", "c2", "b1", "b2", "a1", "a2"]
#         result = []
#         seen   = set()
#         normalised = re.sub(r'[\u2022\u25cf|\n\t]', ',', raw)
#         for tok in normalised.split(','):
#             tok = _clean_bullet(tok.strip())
#             if not tok or len(tok) > 60:
#                 continue
#             lo    = tok.lower()
#             level = next((l for l in PROFICIENCY_LEVELS if l in lo), "")
#             lang  = re.sub('|'.join(PROFICIENCY_LEVELS), '', lo, flags=re.I).strip('- ()/').strip().title()
#             if lang and lang.lower() not in seen:
#                 seen.add(lang.lower())
#                 result.append({"language": lang, "proficiency": level.title()})
#         return result

#     # ──────────────────────────────────────────────────────────────────────────
#     # ACHIEVEMENTS
#     # ──────────────────────────────────────────────────────────────────────────

#     def extract_achievements(self) -> list[str]:
#         raw = self.sections.get("achievements", "") + "\n" + self.sections.get("volunteer", "")
#         if not raw.strip():
#             return []
#         result = []
#         for line in raw.split('\n'):
#             clean = _clean_bullet(line.strip())
#             if clean and len(clean) > 5:
#                 result.append(clean)
#         return result

#     # ──────────────────────────────────────────────────────────────────────────
#     # MAIN PARSE  — assembles everything into the final payload
#     # ──────────────────────────────────────────────────────────────────────────

#     def parse(self) -> dict:
#         links_data  = self._process_links()
#         name_data   = self.extract_name()
#         emails      = self.extract_emails()
#         phones      = self.extract_phones()
#         education   = self.extract_education()
#         experience  = self.extract_experience_or_projects("experience")
#         projects    = self.extract_experience_or_projects("projects")
#         skills      = self.extract_skills()
#         certs       = self.extract_certifications()
#         languages   = self.extract_languages()
#         achievements = self.extract_achievements()

#         employment_history = [
#             {
#                 "job_title":    j["title"],
#                 "company_name": j["organization"],
#                 "location":     j.get("location", ""),
#                 "dates":        j["duration"],
#                 "description":  j["description"],
#             }
#             for j in experience
#         ]

#         return {
#             # ── Identity ───────────────────────────────────────────────────
#             **name_data,
#             "predicted_job_title": self.predict_main_title(),
#             "summary":             self.extract_summary(),

#             # ── Contact ────────────────────────────────────────────────────
#             "personal_email":   self.extract_primary_email(),
#             "all_emails":       emails,
#             "primary_phone":    phones[0] if phones else "",
#             "all_phones":       phones,
#             "full_address":     self.extract_location(),

#             # ── Links ──────────────────────────────────────────────────────
#             **links_data,

#             # ── Career ─────────────────────────────────────────────────────
#             "employment_history": employment_history,
#             "projects_list":      projects,

#             # ── Education ──────────────────────────────────────────────────
#             "education_history": education,

#             # ── Skills & More ──────────────────────────────────────────────
#             "skills":        skills,
#             "certifications": certs,
#             "languages":     languages,
#             "achievements":  achievements,

#             # ── Meta ───────────────────────────────────────────────────────
#             "sections_detected": [k for k, v in self.sections.items() if v.strip()],
#             "confidence_score":  self._confidence(),
#         }

#     # ──────────────────────────────────────────────────────────────────────────
#     # CONFIDENCE SCORE  — simple heuristic based on field coverage
#     # ──────────────────────────────────────────────────────────────────────────

#     def _confidence(self) -> float:
#         payload = {
#             "name":      self.extract_name().get("first_name", "") not in ("", "Unknown"),
#             "email":     bool(self.extract_emails()),
#             "phone":     bool(self.extract_phones()),
#             "location":  self.extract_location() != "Not Detected",
#             "education": bool(self.sections.get("education", "").strip()),
#             "experience":bool(self.sections.get("experience", "").strip()),
#             "skills":    bool(self.sections.get("skills", "").strip()),
#         }
#         filled = sum(1 for v in payload.values() if v)
#         return round(filled / len(payload), 2)