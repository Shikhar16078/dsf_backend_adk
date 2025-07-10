import os
import sys

# Add the project root (2 levels up from this file) to Python's module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from utils import load_instructions_file, setup_logger

# === Logging Setup ===
logger = setup_logger(__name__)

# === Mocked Course Data ===
COURSES_OFFERED_THIS_QUARTER = {
    "CS218", "CS224", "CS230", "CS235", "CS240",
    "CS245", "CS250", "CS260", "CS261", "CS262",
    "MATH131", "STAT155", "EE120", "CS272"
}

def get_quarter_details() -> set:
    """Returns the set of courses offered this quarter."""
    return COURSES_OFFERED_THIS_QUARTER

# === Tools ===
def get_enrollable_courses(state: dict) -> str:
    """Returns courses the student is eligible to enroll in this quarter."""
    student = state.get("student_details", {})
    taken = set(student.get("courses_taken", []))
    available = get_quarter_details()
    enrollable = sorted(available - taken)

    if not enrollable:
        return "✅ Based on your history, there are no new courses currently available for you to take."

    return "📝 Based on your academic history, here are some courses you're eligible to enroll in:\n" + ", ".join(enrollable)

def respond_to_course_options_request(state: dict) -> str:
    """Responds to general queries about what a student can take."""
    return get_enrollable_courses(state)

def render_schedule(state: dict) -> str:
    """Returns a static confirmation for now."""
    return "🗓️ Your schedule has been updated with the selected courses."

# === Agent Configuration ===
MODEL = "gemini-2.0-flash"
NAME = "scheduler"
DESCRIPTION = load_instructions_file("agents/scheduler/description.txt")
INSTRUCTIONS = load_instructions_file("agents/scheduler/instructions.txt")

# === Logging ===
logger.info(f"Entered {NAME} agent.")
logger.info(f"Using Description: {DESCRIPTION[:50]}...")
logger.info(f"Using Instructions: {INSTRUCTIONS[:50]}...")

# === Define Tools as FunctionTool ===
TOOLS = [
    FunctionTool(func=get_enrollable_courses),
    FunctionTool(func=respond_to_course_options_request),
    FunctionTool(func=render_schedule),
]

# === Instantiate Agent ===
scheduler = Agent(
    name=NAME,
    model=MODEL,
    description=DESCRIPTION,
    instruction=INSTRUCTIONS,
    tools=TOOLS,
)

root_agent = scheduler
logger.info(f"Initialized {NAME} agent.")