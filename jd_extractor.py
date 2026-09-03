import re

# Reuse the same skills vocabulary as resume extraction, for consistent matching
SKILLS_LIST = [
    "Python", "Java", "SQL", "Machine Learning", "TensorFlow",
    "Project Management", "Docker", "Kubernetes", "Git", "REST APIs",
    "Spring Boot", "Streamlit"
]

EXPERIENCE_PATTERN = re.compile(r'(\d+)\+?\s*(?:to\s*\d+\s*)?years?', re.I)

EDUCATION_PATTERNS = [
    re.compile(r'\bb\.?\s?tech\b', re.I),
    re.compile(r'\bb\.e\.?\b', re.I),
    re.compile(r'\bm\.?\s?tech\b', re.I),
    re.compile(r'\bbachelor', re.I),
    re.compile(r'\bmaster', re.I),
    re.compile(r'\bdegree\b', re.I),
]

def extract_required_skills(jd_text):
    return [skill for skill in SKILLS_LIST if skill.lower() in jd_text.lower()]

def extract_required_experience(jd_text):
    match = EXPERIENCE_PATTERN.search(jd_text)
    if match:
        return int(match.group(1))
    return 0

def extract_required_education(jd_text):
    lines = jd_text.split("\n")
    matches = []
    for line in lines:
        if any(p.search(line) for p in EDUCATION_PATTERNS):
            matches.append(line.strip())
    return matches

def extract_job_title(jd_text):
    lines = [l.strip() for l in jd_text.split("\n") if l.strip()]
    if lines:
        return lines[0]
    return "Untitled Position"

def analyze_job_description(jd_text):
    return {
        "title": extract_job_title(jd_text),
        "required_skills": extract_required_skills(jd_text),
        "required_experience_years": extract_required_experience(jd_text),
        "required_education": extract_required_education(jd_text),
        "raw_text": jd_text
    }