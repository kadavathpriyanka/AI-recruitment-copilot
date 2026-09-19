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

# Aptitude questions have a real, checkable answer — unlike technical/behavioral ones.
APTITUDE_QA = [
    {"question": "If a train travels 60 km in 45 minutes, what is its speed in km/h?",
     "answer": "80 km/h. Speed = distance / time = 60 km / (45/60 h) = 60 / 0.75 = 80 km/h."},
    {"question": "A shopkeeper sells an item at a 20% profit. If the cost price is ₹500, what is the selling price?",
     "answer": "₹600. Selling price = cost price + 20% of cost price = 500 + 100 = ₹600."},
    {"question": "Complete the series: 2, 6, 12, 20, 30, ?",
     "answer": "42. The differences between terms are 4, 6, 8, 10, 12 — each increasing by 2. 30 + 12 = 42."},
    {"question": "If all Bloops are Razzies and all Razzies are Lazzies, are all Bloops definitely Lazzies? Why or why not?",
     "answer": "Yes. This follows the transitive property of set membership: Bloops ⊆ Razzies ⊆ Lazzies, so Bloops ⊆ Lazzies."},
    {"question": "A clock shows 3:15. What is the angle between the hour and minute hands?",
     "answer": "7.5°. At 3:15, the minute hand is at 90°, and the hour hand is at 90 + (15/60 × 30) = 97.5°. Difference = 7.5°."},
    {"question": "Rearrange the letters in 'LISTEN' to form another meaningful word.",
     "answer": "SILENT (or ENLIST) — both are valid anagrams of LISTEN."},
    {"question": "If 5 machines take 5 minutes to make 5 widgets, how long would 100 machines take to make 100 widgets?",
     "answer": "5 minutes. Each machine makes 1 widget in 5 minutes, regardless of how many machines are running in parallel."},
    {"question": "A is twice as old as B. Five years ago, A was three times as old as B. Find their current ages.",
     "answer": "A is 20, B is 10. Let B = x, A = 2x. Five years ago: 2x-5 = 3(x-5) → 2x-5 = 3x-15 → x = 10. So B=10, A=20."},
    {"question": "Which number should come next: 1, 4, 9, 16, 25, ?",
     "answer": "36. These are perfect squares: 1², 2², 3², 4², 5², 6² = 36."},
    {"question": "Two pipes can fill a tank in 20 and 30 minutes respectively. How long will both take together?",
     "answer": "12 minutes. Combined rate = 1/20 + 1/30 = 3/60 + 2/60 = 5/60 = 1/12, so together they take 12 minutes."},
]

DIFFICULTY_TEMPLATES = {
    "Beginner": BEGINNER_TECHNICAL_TEMPLATES,
    "Intermediate": INTERMEDIATE_TECHNICAL_TEMPLATES,
    "Advanced": ADVANCED_TECHNICAL_TEMPLATES,
}

def _pick_items(items, num_questions):
    """Pick num_questions items. Uses no-repeat sampling when possible,
    otherwise cycles through with repeats (shuffled) once the pool runs out."""
    if num_questions <= len(items):
        return random.sample(items, num_questions)
    pool = items * (num_questions // len(items) + 1)
    random.shuffle(pool)
    return pool[:num_questions]

def generate_questions(job, question_type="technical", num_questions=3, difficulty="Intermediate"):
    """
    Returns a list of dicts: {"question": str, "skill": str or None, "type": question_type, "answer": str or None}
    "answer" is populated only for aptitude questions, which have a real correct answer.
    """
    if num_questions <= 0:
        return []

    if question_type == "behavioral":
        chosen = _pick_items(BEHAVIORAL_TEMPLATES, num_questions)
        return [{"question": q, "skill": None, "type": "behavioral", "answer": None} for q in chosen]

    if question_type == "aptitude":
        chosen = _pick_items(APTITUDE_QA, num_questions)
        return [{"question": qa["question"], "skill": None, "type": "aptitude", "answer": qa["answer"]} for qa in chosen]

    # technical
    skills = job.get("required_skills", [])
    if not skills:
        return [{"question": "No required skills found for this job — add skills to the job posting first.", "skill": None, "type": "technical", "answer": None}]

    templates = DIFFICULTY_TEMPLATES.get(difficulty, INTERMEDIATE_TECHNICAL_TEMPLATES)
    templates_used = _pick_items(templates, num_questions)

    questions = []
    for i, template in enumerate(templates_used):
        skill = skills[i % len(skills)]
        questions.append({"question": template.format(skill=skill), "skill": skill, "type": "technical", "answer": None})

    return questions