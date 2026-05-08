<!-- # Production-Level Resume Parser (No-AI / Hybrid)

This is a robust resume parser built using Python, SpaCy, and rule-based heuristics. It follows a multi-stage pipeline to achieve high accuracy without relying purely on LLMs.

## 🚀 Features
- **Multi-Engine Extraction**: Uses `pdfplumber` with a fallback to `PyMuPDF` for complex layouts.
- **Section Segmentation**: Intelligent section detection (Education, Experience, Skills, etc.) using fuzzy matching.
- **Hybrid Parsing**: Combines Regex, SpaCy NER, and keyword heuristics.
- **Experience Timeline Builder**: Automatically reconstructs employment history and calculates total years.
- **Confidence Scoring**: Each field is assigned a confidence score.
- **Production Ready**: Built with FastAPI for high performance.

## 🛠️ Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

2. Run the API:
   ```bash
   python app.py
   ```

## 📡 API Usage

### Parse Resume
- **Endpoint**: `POST /parse`
- **Payload**: `file` (Multipart/form-data)

**Example Response:**
```json
{
  "first_name": "John",
  "middle_name": "Quincy",
  "last_name": "Doe",
  "personal_email": "john.doe@example.com",
  "primary_phone": "+15551234567",
  "whatsapp_number": "+15551234567",
  "date_of_birth": "1990-01-01",
  "full_address": "New York, USA",
  "linkedin_url": "https://www.linkedin.com/in/johndoe",
  "github_url": "https://github.com/johndoe",
  "portfolio_url": "https://johndoe.com",
  "highest_education": "Bachelor",
  "university_name": "Harvard University",
  "main_subject": "Computer Science",
  "graduation_year": "2012",
  "cgpa": "3.8",
  "experience": "11.5",
  "employment_history": [
    {
      "job_title": "Senior Software Engineer",
      "company_name": "Tech Corp",
      "start_date": "2018-06-01",
      "end_date": "2023-12-31",
      "is_current": false
    }
  ],
  "addons_notes": "Confidence Score: 0.85. Summary of experience..."
}
```

## 🧩 Architecture
1. **Extraction**: `pdfplumber` / `fitz`.
2. **Segmentation**: `rapidfuzz` matches headers.
3. **NLP**: `SpaCy` for entity recognition.
4. **Logic**: `extractor.py` processes segments into the final schema. -->










# ApplyWizz — Universal Resume Parser v2.0

A production-grade resume parser built to handle the *messiest* real-world CVs:
two-column PDFs, ALL-CAPS headers, emoji-prefixed sections, international phone
numbers, ligature characters, partial dates, mid-sentence degree mentions, and more.

---

## Architecture

```
parser/
├── __init__.py        Public API: ResumeParser, extract_text_from_file
├── patterns.py        All regex, keyword lists, and match helpers
├── segmenter.py       Multi-strategy section header detection
├── text_utils.py      PDF/DOCX/TXT extraction with column detection
└── extractor.py       ResumeParser — multi-fallback field extractors
app.py                 FastAPI server  (GET /, POST /parse, POST /parse/batch)
index.html             Dashboard UI
requirements.txt
```

---

## What's in v2.0

### text_utils.py — Multi-column PDF support
- Uses pdfplumber word bounding-boxes to detect 2-column layouts
- Reconstructs reading order by (y, x) position grouping
- Falls back to PyMuPDF when pdfplumber fails
- Normalises ligatures (ﬁ→fi), curly quotes, zero-width chars
- Extracts text from DOCX tables (used for skills/education grids)

### segmenter.py — Robust header detection
- Handles ALL-CAPS, Title Case, trailing colon ("Skills:")
- Strips emoji, decorative rules (───, ===), leading bullets
- Confidence-scored fuzzy matching with per-signal boosts
- Relaxed threshold for short ALL-CAPS lines

### patterns.py — Comprehensive patterns
- Phone: 15+ real-world formats; validated with `phonenumbers`
- Date: month+year, year-only, slashed, short-year ('23), current terms
- Degrees: 60+ spellings including regional variants (BCA, MCA, PGDM…)
- Section headers: 200+ synonyms across 11 section types
- Skill alias map: JS→JavaScript, k8s→Kubernetes, etc.

### extractor.py — Multi-strategy field parsing
| Field       | Strategy 1              | Strategy 2              | Fallback           |
|-------------|-------------------------|-------------------------|--------------------|
| Name        | SpaCy PERSON entity     | 2-5 alpha-only words    | First non-contact line |
| Email       | Regex; pick name-match  | —                       | First found        |
| Phone       | phonenumbers validation | —                       | Strip non-digits   |
| Location    | City, State regex       | SpaCy GPE entity        | Full-text GPE scan |
| Education   | State-machine (degree→uni→date→GPA) | — | — |
| Experience  | Date-range anchor       | Job-keyword + short line | — |
| Skills      | Comma/pipe/bullet split | Alias normalisation     | — |
| Certs       | Line + issuer split     | —                       | Raw lines          |
| Languages   | Comma/bullet split      | Proficiency extraction  | — |

---

## Setup

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python app.py
# Open http://localhost:8000
```

---

## API

```
POST /parse          multipart/form-data  file=<resume>
POST /parse/batch    multipart/form-data  files=<up to 10 resumes>
GET  /health         → { status: "ok", version: "2.0.0" }
GET  /sections       → all section header keywords
```

### Response fields
```json
{
  "first_name", "middle_name", "last_name",
  "predicted_job_title", "summary",
  "personal_email", "all_emails",
  "primary_phone", "all_phones",
  "full_address",
  "linkedin_url", "github_url", "portfolio_url", "other_links",
  "employment_history": [{ job_title, company_name, location, dates, description }],
  "projects_list":      [{ title, organization, duration, description }],
  "education_history":  [{ degree, university, subject, dates, gpa, details }],
  "skills",
  "certifications": [{ name, issuer, date }],
  "languages":      [{ language, proficiency }],
  "achievements",
  "sections_detected",
  "confidence_score",
  "_parse_time_ms"
}
```