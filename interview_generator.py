import random

# Generic technical question templates — {skill} gets filled in from the job's required_skills
TECHNICAL_TEMPLATES = [
    "Describe a project where you used {skill}. What challenges did you run into?",
    "How would you explain {skill} to someone with no technical background?",
    "Walk me through how you'd debug a {skill} issue in production.",
    "What's a mistake you've made while working with {skill}, and what did you learn?",
    "How do you decide when {skill} is the right tool for a problem versus an alternative?",
]

# Generic behavioral templates — not tied to any specific skill
BEHAVIORAL_TEMPLATES = [
    "Tell me about a time you had to explain a complex technical concept to a non-technical stakeholder.",
    "Describe a situation where you disagreed with a teammate's technical approach. How did you handle it?",
    "Tell me about a project that didn't go as planned. What did you do?",
    "How do you prioritize tasks when working on multiple things at once?",
    "Describe a time you had to learn a new skill quickly for a project.",
]

def generate_questions(job, question_type="technical", num_questions=3):
    """
    job: a dict with at least 'title' and 'required_skills' (list)
    question_type: 'technical' or 'behavioral'
    """
    if question_type == "behavioral":
        return random.sample(BEHAVIORAL_TEMPLATES, min(num_questions, len(BEHAVIORAL_TEMPLATES)))

    skills = job.get("required_skills", [])
    if not skills:
        return ["No required skills found for this job — add skills to the job posting first."]

    questions = []
    templates_used = random.sample(TECHNICAL_TEMPLATES, min(num_questions, len(TECHNICAL_TEMPLATES)))
    for i, template in enumerate(templates_used):
        skill = skills[i % len(skills)]
        questions.append(template.format(skill=skill))

    return questions