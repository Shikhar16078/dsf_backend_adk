import os
import sys
import json
from pathlib import Path

# Add the project root (2 levels up from this file) to Python's module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from google.adk.agents import Agent
from google.adk.tools import ToolContext
from utils import load_instructions_file, setup_logger

# === Logging Setup ===
logger = setup_logger(__name__)

# Loading differnet Datbase files and caching them 
_COURSE_CACHE = None
_OFFERINGS_CACHE = None

def _load_courses(path: str | Path = "database/courses.json") -> list[dict]:
    global _COURSE_CACHE
    if _COURSE_CACHE is None:
        with open(path, "r", encoding="utf-8") as f:
            _COURSE_CACHE = json.load(f)
    return _COURSE_CACHE

def _load_offerings(path: str | Path = "database/offerings.json") -> list[dict]:
    global _OFFERINGS_CACHE
    if _OFFERINGS_CACHE is None:
        with open(path, "r", encoding="utf-8") as f:
            _OFFERINGS_CACHE = json.load(f)
    return _OFFERINGS_CACHE


# === Tools ===

def get_enrollable_courses(quarter: str, year: str, tool_context: ToolContext) -> dict:
    """
    Returns a list of courses the student is eligible to enroll in for the specified quarter and year.

    A course is considered enrollable if:
      - The course is offered in the specified term (quarter + year).
      - The student has not already taken it.
      - All prerequisites have been completed.

    Parameters:
        quarter (str): The academic term (e.g., "Fall", "Winter", "Summer", "Spring").
        year (str): The academic year as a string (e.g., "2024").
        tool_context (ToolContext): Contains `state["student_details"]` with `courses_taken`.

    Returns:
        dict: {
            "status": "success" | "error",
            "message": "...",
            "courses": [list of eligible course detail dicts]
        }
    """
    try:
        student = tool_context.state["student_details"]
        taken = set(student.get("courses_taken", []))
        year_int = int(year)

        catalog = _load_courses()
        offerings = _load_offerings()

    except (KeyError, FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to load data: {e}")
        return {
            "status": "error",
            "message": f"Failed to compute enrollable courses: {e}",
            "courses": []
        }

    # Find offered course IDs for this quarter/year
    offering_this_term = next(
        (entry for entry in offerings if entry["term"].lower() == quarter.lower() and entry["year"] == year_int),
        None
    )

    if not offering_this_term:
        msg = f"No offerings found for {quarter} {year}"
        logger.warning(msg)
        return {
            "status": "error",
            "message": msg,
            "courses": []
        }

    offered_courses = set(offering_this_term["courses"])
    logger.info(f"Courses offered in {quarter} {year}: {offered_courses}")

    enrollable = []
    for course in catalog:
        course_id = course.get("course_id")
        prereqs = set(course.get("prerequisites", []))

        if (
            course_id in offered_courses and
            course_id not in taken and
            prereqs.issubset(taken)
        ):
            enrollable.append(course)

    enrollable = sorted(enrollable, key=lambda c: c["course_id"])

    logger.info(f"Student's courses taken: {taken}")
    logger.info(f"Eligible courses for enrollment: {[c['course_id'] for c in enrollable]}")

    return {
        "status": "success",
        "message": f"Here are the courses you can enroll in for {quarter} {year}.",
        "courses": enrollable
    }

def get_course_details(course_id: str) -> dict:
    """
    Retrieve detailed information for a specific course by its course ID.

    This function searches the course catalog for a course matching the provided
    `course_id` (e.g., "CS101") and returns its full details if found. It is designed 
    to be used as a tool function in agent workflows that require academic course data.

    Parameters:
        course_id (str): The unique identifier of the course to retrieve.

    Returns:
        dict: A dictionary containing the operation result. The response includes:
            - status (str): "success" if the course is found, otherwise "error".
            - course_details (dict): The full course object if found, or an empty dict.
            - message (str, optional): Error description if the operation failed.

    Example successful response:
        {
            "status": "success",
            "course_details": {
                "course_id": "CS218",
                "title": "Foundations of CS 218",
                ...
            }
        }

    Example error response (course not found):
        {
            "status": "error",
            "course_details": {},
            "message": "Course 'CS999' not found"
        }
    """

    try:
        courses = _load_courses()
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return {
            "status": "error",
            "course_details": {},
            "message": f"Unable to load course catalog: {exc}"
        }

    # Find the first course whose course_id matches (case-sensitive)
    for course in courses:
        if course.get("course_id") == course_id:
            return {
                "status": "success",
                "course_details": course
            }

    # If nothing matched
    return {
        "status": "error",
        "course_details": {},
        "message": f"Course '{course_id}' not found"
    }

def get_course_offerings(quarter: str, year: str) -> dict:
    """
    Retrieve the list of course IDs offered in a specific academic term.

    Parameters
    ----------
    quarter : str
        Academic term (e.g., "Fall", "Winter", "Spring", "Summer").
        Matching is case-insensitive.
    year : str
        Four-digit calendar year, passed as string (e.g., "2024").

    Returns
    -------
    dict
        {
            "status": "success" | "error",
            "message": <human-readable status>,
            "offerings": [<course_id>, ...]   # empty list if none / on error
        }
    """
    try:
        year_int = int(year)
        offerings_data = _load_offerings()
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        logger.error(f"Unable to load offerings data: {exc}")
        return {
            "status": "error",
            "message": f"Failed to retrieve offerings: {exc}",
            "offerings": []
        }

    # Locate the term entry
    term_entry = next(
        (
            entry for entry in offerings_data
            if entry["term"].lower() == quarter.lower() and entry["year"] == year_int
        ),
        None
    )

    if term_entry is None:
        msg = f"No offerings found for {quarter} {year}."
        logger.warning(msg)
        return {
            "status": "error",
            "message": msg,
            "offerings": []
        }

    courses = sorted(term_entry.get("courses", []))
    logger.info(f"Offerings for {quarter} {year}: {courses}")

    return {
        "status": "success",
        "message": f"Courses offered in {quarter} {year} have been retrieved.",
        "offerings": courses
    }

def build_schedule(avoid_days: list[str], avoid_times: list[str], tool_context: ToolContext) -> str:
    """
    Builds a mock student schedule based on the provided constraints.

    This function generates a placeholder schedule while avoiding the specified days and time ranges.
    It does not perform real scheduling logic or course conflict resolution — that will be implemented later.

    Parameters:
        avoid_days (list): List of weekdays to avoid classes on (e.g., ["Monday", "Friday"]).
        avoid_times (list): List of time ranges to avoid in 24-hour format (e.g., ["09:00-12:00", "14:00-16:00"]).

    Returns:
        str: A confirmation message indicating that the schedule was built using the given constraints.
    """
    all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    avoid_set = set(day.capitalize() for day in avoid_days)

    allowed_days = [day for day in all_days if day not in avoid_set]

    tool_context.state["constraints"] = {
        "allowed_days": allowed_days,
        "avoid_times": avoid_times
    }

    return {
        "status": "success", 
        "message": f"✅ Your schedule has been built with the following constraints: Avoiding {', '.join(avoid_days)} on days and {', '.join(avoid_times)} on times."
    }

def get_student_details(tool_context: ToolContext) -> dict:
    """
    Retrieve the student's details from the tool context state.

    This function accesses the `state["student_details"]` dictionary to return the student's information.
    It is designed to be used as a tool function in agent workflows that require access to student data.

    Returns:
        dict: A dictionary containing the student's details, or an error message if not found.
    """
    try:
        student_details = tool_context.state["student_details"]
        return {
            "status": "success",
            "student_details": student_details
        }
    except KeyError:
        return {
            "status": "error",
            "message": "Student details not found in state."
        }

# === Agent Configuration ===
MODEL = "gemini-2.0-flash"
NAME = "scheduler"
DESCRIPTION = load_instructions_file("agents/scheduler/description.txt")
INSTRUCTIONS = load_instructions_file("agents/scheduler/instructions.txt")

# === Logging ===
logger.info(f"Entered {NAME} agent.")
logger.info(f"Using Description: {DESCRIPTION[:50]}...")
logger.info(f"Using Instructions: {INSTRUCTIONS[:50]}...")

# === Instantiate Agent ===
scheduler = Agent(
    name=NAME,
    model=MODEL,
    description=DESCRIPTION,
    instruction=INSTRUCTIONS,
    tools=[get_enrollable_courses, build_schedule, get_course_details, get_course_offerings, get_student_details],
)

root_agent = scheduler
logger.info(f"Initialized {NAME} agent.")