import random

FOLLOWUP_ACKS = [
    "Thanks for sharing that.",
    "Got it, that's helpful context.",
    "Interesting approach — noted.",
    "Thanks, that gives me a good sense of your experience.",
]

# Related terms per skill — so an answer counts as relevant even without
# using the exact skill name (e.g. "structured query language" for SQL).
SKILL_KEYWORDS = {
    "python": ["python", "py", "django", "flask", "pandas", "numpy", "script"],
    "java": ["java", "jvm", "oop", "object oriented", "class", "spring"],
    "sql": ["sql", "query", "queries", "database", "table", "select", "insert",
            "update", "delete", "join", "schema", "structured query language"],
    "machine learning": ["machine learning", "ml", "model", "training", "dataset",
                          "algorithm", "prediction", "accuracy", "supervised", "regression"],
    "tensorflow": ["tensorflow", "keras", "neural network", "layer", "tensor", "model"],
    "project management": ["project management", "timeline", "scope", "stakeholder",
                            "agile", "scrum", "planning", "deadline", "milestone"],
    "docker": ["docker", "container", "image", "dockerfile", "compose"],
    "kubernetes": ["kubernetes", "k8s", "pod", "cluster", "node", "deployment", "orchestration"],
    "git": ["git", "commit", "branch", "merge", "repository", "repo", "pull request", "version control"],
    "rest apis": ["rest", "api", "endpoint", "http", "get request", "post request", "json", "request", "response"],
    "spring boot": ["spring", "springboot", "bean", "controller", "annotation"],
    "streamlit": ["streamlit", "dashboard", "widget"],
}

def start_interview(candidate_name, job, num_technical=2, num_behavioral=1, difficulty="Intermediate"):
    from interview_generator import generate_questions

    questions = (
        generate_questions(job, "technical", num_technical, difficulty) +
        generate_questions(job, "behavioral", num_behavioral, difficulty)
    )

    return {
        "candidate_name": candidate_name,
        "job_title": job.get("title"),
        "questions": questions,
        "current_index": 0,
        "transcript": [],
        "completed": False,
    }

def get_opening_message(candidate_name, job_title):
    return f"Hello {candidate_name}, I'm your AI interviewer today. We'll go through a few questions about the {job_title} role — take your time with each answer."

def evaluate_answer(answer_text, skill):
    """
    Lightweight heuristic evaluation — not true language understanding,
    just keyword/synonym matching plus a basic depth check.
    Returns: (relevant: bool or None, feedback: str)
    """
    word_count = len(answer_text.split())

    if not skill:
        # Behavioral question — no skill to check, just judge on detail
        if word_count >= 20:
            return None, "Good — specific and detailed answer."
        elif word_count >= 8:
            return None, "Reasonable answer — a concrete example would make it stronger."
        else:
            return None, "Quite brief — try expanding with a specific situation and outcome."

    keywords = SKILL_KEYWORDS.get(skill.lower(), [skill.lower()])
    answer_lower = answer_text.lower()
    relevant = any(kw in answer_lower for kw in keywords)

    if relevant and word_count >= 15:
        return True, f"Strong answer — clearly relevant to {skill} and reasonably detailed."
    elif relevant:
        return True, f"Relevant to {skill}, but brief — consider adding a specific example."
    else:
        return False, f"This doesn't clearly connect back to {skill} — try referencing it more directly."

def submit_answer(session, answer_text):
    if session["completed"]:
        return session

    current_q = session["questions"][session["current_index"]]
    skill = current_q.get("skill")
    relevant, feedback = evaluate_answer(answer_text, skill)

    session["transcript"].append({
        "question": current_q["question"],
        "skill": skill,
        "answer": answer_text,
        "mentions_skill": relevant,
        "feedback": feedback,
    })
    session["current_index"] += 1

    if session["current_index"] >= len(session["questions"]):
        session["completed"] = True

    return session

def get_current_question(session):
    if session["completed"] or session["current_index"] >= len(session["questions"]):
        return None
    return session["questions"][session["current_index"]]["question"]

def get_random_ack():
    return random.choice(FOLLOWUP_ACKS)