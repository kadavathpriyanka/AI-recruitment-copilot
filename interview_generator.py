import random

BEGINNER_TECHNICAL_TEMPLATES = [
    "What is {skill} and where have you used it?",
    "Explain the basic purpose of {skill} in your own words.",
    "Have you used {skill} in a class project? What did you build?",
]

INTERMEDIATE_TECHNICAL_TEMPLATES = [
    "Describe a project where you used {skill}. What challenges did you run into?",
    "How would you explain {skill} to someone with no technical background?",
    "Walk me through how you'd debug a {skill} issue in production.",
    "What's a mistake you've made while working with {skill}, and what did you learn?",
    "How do you decide when {skill} is the right tool for a problem versus an alternative?",
]

ADVANCED_TECHNICAL_TEMPLATES = [
    "How would you scale a {skill}-based system to handle 10x the current traffic?",
    "Design a fault-tolerant approach using {skill}. What failure modes would you plan for?",
    "How would you optimize {skill} performance under tight latency constraints?",
    "Walk me through a trade-off you'd make when {skill} isn't the ideal fit, but the team insists on using it.",
]

BEHAVIORAL_TEMPLATES = [
    "Tell me about a time you had to explain a complex technical concept to a non-technical stakeholder.",
    "Describe a situation where you disagreed with a teammate's technical approach. How did you handle it?",
    "Tell me about a project that didn't go as planned. What did you do?",
    "How do you prioritize tasks when working on multiple things at once?",
    "Describe a time you had to learn a new skill quickly for a project.",
]

DIFFICULTY_TEMPLATES = {
    "Beginner": BEGINNER_TECHNICAL_TEMPLATES,
    "Intermediate": INTERMEDIATE_TECHNICAL_TEMPLATES,
    "Advanced": ADVANCED_TECHNICAL_TEMPLATES,
}

def generate_questions(job, question_type="technical", num_questions=3, difficulty="Intermediate"):
    """
    Returns a list of dicts: {"question": str, "skill": str or None}
    The "skill" field lets the interview simulation check whether an answer
    actually mentions the topic the question was about.
    """
    if question_type == "behavioral":
        chosen = random.sample(BEHAVIORAL_TEMPLATES, min(num_questions, len(BEHAVIORAL_TEMPLATES)))
        return [{"question": q, "skill": None} for q in chosen]

    skills = job.get("required_skills", [])
    if not skills:
        return [{"question": "No required skills found for this job — add skills to the job posting first.", "skill": None}]

    templates = DIFFICULTY_TEMPLATES.get(difficulty, INTERMEDIATE_TECHNICAL_TEMPLATES)
    templates_used = random.sample(templates, min(num_questions, len(templates)))

    questions = []
    for i, template in enumerate(templates_used):
        skill = skills[i % len(skills)]
        questions.append({"question": template.format(skill=skill), "skill": skill})

    return questions