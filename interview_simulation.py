import random

CLOSING_MESSAGE = "That's all the questions I have for now. Thanks for your time — your responses have been recorded for review."

FOLLOWUP_ACKS = [
    "Thanks for sharing that.",
    "Got it, that's helpful context.",
    "Interesting approach — noted.",
    "Thanks, that gives me a good sense of your experience.",
]

def start_interview(candidate_name, job, num_technical=2, num_behavioral=1):
    """Builds the initial interview session state: a list of questions to ask in order."""
    from interview_generator import generate_questions

    questions = (
        generate_questions(job, "technical", num_technical) +
        generate_questions(job, "behavioral", num_behavioral)
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

def submit_answer(session, answer_text):
    """Records the candidate's answer, appends it to the transcript, and advances to the next question."""
    if session["completed"]:
        return session

    current_q = session["questions"][session["current_index"]]
    session["transcript"].append({"question": current_q, "answer": answer_text})
    session["current_index"] += 1

    if session["current_index"] >= len(session["questions"]):
        session["completed"] = True

    return session

def get_current_question(session):
    if session["completed"] or session["current_index"] >= len(session["questions"]):
        return None
    return session["questions"][session["current_index"]]

def get_random_ack():
    return random.choice(FOLLOWUP_ACKS)