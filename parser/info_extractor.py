import spacy
import re

nlp = spacy.load("en_core_web_sm")

EDUCATION_PATTERNS = [
    re.compile(r'\bb\.?\s?tech\b', re.I),
    re.compile(r'\bb\.e\.?\b', re.I),
    re.compile(r'\bm\.?\s?tech\b', re.I),
    re.compile(r'\bbachelor', re.I),
    re.compile(r'\bmaster', re.I),
    re.compile(r'\bdiploma\b', re.I),
    re.compile(r'\buniversity\b', re.I),
    re.compile(r'\binstitute\b', re.I),
    re.compile(r'\bcollege\b', re.I),
    re.compile(r'\bcgpa\b', re.I),
    re.compile(r'\bjntu\b', re.I),
    re.compile(r'\bintermediate\b', re.I),
    re.compile(r'\b(10th|12th|ssc|hsc)\b', re.I),
]

SECTION_HEADERS = [
    "education", "skills", "experience", "work experience", "projects",
    "certifications", "technical skills", "summary", "objective"
]

CERT_KEYWORDS = [
    "certified", "certificate", "certification", "aws", "azure", "google cloud",
    "cka", "pmp", "scrum"
]

EXPERIENCE_KEYWORDS = [
    "intern", "engineer", "developer", "years", "present", "manager", "analyst"
]

def get_lines(text):
    # Bullets are often on the same physical line separated by "•" —
    # split on that too, not just newlines, so unrelated bullets don't get merged.
    normalized = text.replace("•", "\n")
    return [l.strip() for l in normalized.split("\n") if l.strip()]

def extract_name(text, email, doc):
    lines = get_lines(text)

    LINK_WORDS = ["github", "linkedin", "portfolio", "http", "www", "behance", "leetcode"]

    def is_valid_name_line(line):
        line_lower = line.lower().strip(":")
        if line_lower in SECTION_HEADERS:
            return False
        if "@" in line or re.search(r'\d{4,}', line):
            return False
        if any(p.search(line) for p in EDUCATION_PATTERNS):
            return False
        if any(word in line_lower for word in LINK_WORDS):
            return False
        if len(line.split()) > 5:
            return False
        return True

    if email:
        for i, line in enumerate(lines):
            if email in line:
                if i > 0 and is_valid_name_line(lines[i - 1]):
                    return lines[i - 1]
                break

    for line in lines:
        if is_valid_name_line(line):
            return line

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None

def extract_education(text):
    lines = get_lines(text)
    matches = []
    for line in lines:
        if any(p.search(line) for p in EDUCATION_PATTERNS):
            matches.append(line)
    return matches

def extract_certifications(text):
    lines = get_lines(text)
    matches = []
    for line in lines:
        if line.lower().strip(":") in SECTION_HEADERS:
            continue
        if any(keyword in line.lower() for keyword in CERT_KEYWORDS):
            matches.append(line)
    return matches

def extract_experience(text):
    lines = get_lines(text)
    matches = []
    for line in lines:
        if line.lower().strip(":") in SECTION_HEADERS:
            continue
        if any(keyword in line.lower() for keyword in EXPERIENCE_KEYWORDS):
            matches.append(line)
    return matches

def extract_candidate_info(text):
    doc = nlp(text)
    candidate = {
        "name": None,
        "email": None,
        "phone": None,
        "education": [],
        "skills": [],
        "experience": [],
        "certifications": []
    }

    email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    if email_match:
        candidate["email"] = email_match.group(0)

    phone_match = re.search(r'\+?\d[\d -]{8,}\d', text)
    if phone_match:
        candidate["phone"] = phone_match.group(0)

    candidate["name"] = extract_name(text, candidate["email"], doc)
    candidate["education"] = extract_education(text)
    candidate["certifications"] = extract_certifications(text)
    candidate["experience"] = extract_experience(text)

    skills_list = [
        "Python", "Java", "SQL", "Machine Learning", "TensorFlow",
        "Project Management", "Docker", "Kubernetes", "Git", "REST APIs",
        "Spring Boot", "Streamlit"
    ]
    candidate["skills"] = [skill for skill in skills_list if skill.lower() in text.lower()]

    return candidate