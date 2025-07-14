# from google.adk.agents import Agent
# from google.adk.tools import FunctionTool
# from utils.logging_config import setup_logger
# from utils.file_loader import load_instructions_file

# # === Logging Setup ===
# logger = setup_logger(__name__)

# # === Mocked Course Data ===
# COURSES_OFFERED_THIS_QUARTER = {
#     "CS218", "CS224", "CS230", "CS235", "CS240",
#     "CS245", "CS250", "CS260", "CS261", "CS262",
#     "MATH131", "STAT155", "EE120", "CS272"
# }

# def get_quarter_details() -> set:
#     """Returns the set of courses offered this quarter."""
#     return COURSES_OFFERED_THIS_QUARTER

# # === Tools ===
# def get_enrollable_courses(state: dict) -> str:
#     """Returns courses the student is eligible to enroll in this quarter."""
#     student = state.get("student_details", {})
#     taken = set(student.get("courses_taken", []))
#     available = get_quarter_details()
#     enrollable = sorted(available - taken)

#     if not enrollable:
#         return "✅ Based on your history, there are no new courses currently available for you to take."

#     return "📝 Based on your academic history, here are some courses you're eligible to enroll in:\n" + ", ".join(enrollable)

# def respond_to_course_options_request(state: dict) -> str:
#     """Responds to general queries about what a student can take."""
#     return get_enrollable_courses(state)

# def render_schedule(state: dict) -> str:
#     """Returns a static confirmation for now."""
#     return "🗓️ Your schedule has been updated with the selected courses."

# # === Agent Configuration ===
# MODEL = "gemini-2.0-flash"
# NAME = "scheduler"
# DESCRIPTION = load_instructions_file("agents/scheduler/description.txt")
# INSTRUCTIONS = load_instructions_file("agents/scheduler/instructions.txt")

# # === Logging ===
# logger.info(f"Entered {NAME} agent.")
# logger.info(f"Using Description: {DESCRIPTION[:50]}...")
# logger.info(f"Using Instructions: {INSTRUCTIONS[:50]}...")

# # === Define Tools as FunctionTool ===
# TOOLS = [
#     FunctionTool(func=get_enrollable_courses),
#     FunctionTool(func=respond_to_course_options_request),
#     FunctionTool(func=render_schedule),
# ]

# # === Instantiate Agent ===
# scheduler = Agent(
#     name=NAME,
#     model=MODEL,
#     description=DESCRIPTION,
#     instruction=INSTRUCTIONS,
#     tools=TOOLS,
# )

# root_agent = scheduler
# logger.info(f"Initialized {NAME} agent.")

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from utils.logging_config import setup_logger
from utils.file_loader import load_instructions_file
from scheduler.sched_algo import get_eligible_courses



# === Logging Setup ===
logger = setup_logger(__name__)

# === Agent Identity ===
MODEL = "gemini-2.0-flash"
NAME = "scheduler"
DESCRIPTION = load_instructions_file("agents/scheduler/description.txt")
INSTRUCTIONS = load_instructions_file("agents/scheduler/instructions.txt")

logger.info(f"Entered {NAME} agent.")
logger.info(f"Using Description: {DESCRIPTION[:50]}...")
logger.info(f"Using Instructions: {INSTRUCTIONS[:50]}...")

import json

with open("scheduler/mock_data.json") as f:
    mock_data = json.load(f)

DEGREE_PLAN_2024_CS = mock_data["degree_plan"]
COURSES_OFFERED_THIS_QUARTER = mock_data["quarter_offerings"]
PREREQUISITES = mock_data["prerequisites"]
STUDENT_DEGREE = mock_data["student_info"]
COURSE_ENROLLMENTS = mock_data["course_enrollments"]



# === Core Algorithm ===
def get_algorithmic_eligible_courses(state: dict) -> dict:
    student = state.get("student_details", {})
    taken = set(student.get("courses_taken", []))
    satisfied = taken.copy()

    normalized_year = student.get("year", "year_1")  # Already in 'year_1' format
    quarter_str = student.get("current_quarter", "Fall")

    eligible = []

    if normalized_year in DEGREE_PLAN_2024_CS:
        year_plan = DEGREE_PLAN_2024_CS[normalized_year]
        for quarter, courses in year_plan.items():
            for course in courses:
                if course in taken or course not in COURSES_OFFERED_THIS_QUARTER:
                    continue
                prereqs = PREREQUISITES.get(course, [])
                if all(pr in satisfied for pr in prereqs):
                    eligible.append({
                        "course": course,
                        "quarter": quarter,
                        "year": normalized_year,
                        "prerequisites": prereqs
                    })

    return {
        "eligible_courses": eligible,
        "student_history": list(taken),
        "current_year": normalized_year,
        "current_quarter": quarter_str
    }


# === Tool 1: Basic eligibility response ===
def get_enrollable_courses(state: dict) -> str:
    eligible = get_algorithmic_eligible_courses(state)
    if not eligible:
        return "There are no eligible classes for you to take this quarter."
    return "Based on your history and what's offered this quarter, you may enroll in:\n- " + "\n- ".join(eligible)

# === Tool 2: General-purpose response to “what can I take?” ===
def respond_to_course_options_request(state: dict) -> str:
    return get_enrollable_courses(state)

# === Tool 3: LLM-style refinement with user preferences ===
def refine_with_preferences(state: dict) -> str:
    result = get_algorithmic_eligible_courses(state)
    eligible_courses = result["eligible_courses"]
    pref = state.get("preferences", {}).get("topic_focus", "any area")

    if not eligible_courses:
        return f"Based on your interest in '{pref}', there are no eligible courses this quarter."

    top_courses = ", ".join(course["course"] for course in eligible_courses[:3])
    return f"✨ Based on your interest in '{pref}', consider:\n- {top_courses}"


def generate_schedule_with_llm(state: dict) -> str:
    student = state.get("student_details", {
        "courses_taken": [e["Student_course_Course"] for e in COURSE_ENROLLMENTS],
        "year": STUDENT_DEGREE.get("year", "year_1"),
        "current_quarter": STUDENT_DEGREE.get("Term", "2025 Winter").split()[-1]
    })
    preferences = state.get("preferences", {"topic_focus": "general"})

    filtered = get_eligible_courses(
        student,
        COURSES_OFFERED_THIS_QUARTER,
        PREREQUISITES,
        DEGREE_PLAN_2024_CS
    )

    prompt = (
        f"You are a scheduling assistant.\n\n"
        f"Student is in year {filtered['current_year']}, quarter {filtered['current_quarter']}.\n"
        f"Completed courses: {', '.join(filtered['student_history'])}\n\n"
        f"Eligible courses this quarter (algorithmically filtered):\n" +
        "\n".join(f"- {c['course']} (from {c['year']} {c['quarter']})" for c in filtered['eligible_courses']) +
        "\n\nStudent preferences:\n" +
        f"{preferences}\n\n"
        f"Here is the full degree plan:\n{DEGREE_PLAN_2024_CS}\n\n"
        "Recommend 3–5 courses to take this quarter."
    )

    return prompt 


# === Tool 4: Render schedule confirmation (stub) ===
def render_schedule(state: dict) -> str:
    return "Your schedule has been drafted and saved."

# === Tools ===
TOOLS = [
    FunctionTool(func=get_enrollable_courses),
    FunctionTool(func=respond_to_course_options_request),
    FunctionTool(func=refine_with_preferences),
    FunctionTool(func=render_schedule),
    FunctionTool(func=generate_schedule_with_llm),
]

# === Agent Declaration ===
scheduler = Agent(
    name=NAME,
    model=MODEL,  # Only used if direct input is passed
    instruction=INSTRUCTIONS,
    description=DESCRIPTION,
    tools=TOOLS,
)

# === Expose root_agent for coordinator ===
root_agent = scheduler
logger.info(f"Initialized {NAME} agent.")