import random

FOLLOWUP_ACKS = [
    "Thanks for sharing that.",
    "Got it, that's helpful context.",
    "Interesting approach — noted.",
    "Thanks, that gives me a good sense of your experience.",
]

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

def check_relevance(answer_text, skill):
    """Very simple relevance check: does the answer mention the skill the question was about?"""
    if not skill:
        return None
    return skill.lower() in answer_text.lower()

def submit_answer(session, answer_text):
    if session["completed"]:
        return session

    current_q = session["questions"][session["current_index"]]
    relevant = check_relevance(answer_text, current_q.get("skill"))

    session["transcript"].append({
        "question": current_q["question"],
        "skill": current_q.get("skill"),
        "answer": answer_text,
        "mentions_skill": relevant,
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