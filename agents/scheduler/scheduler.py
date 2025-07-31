import os
import sys
import json
from pathlib import Path

# Add the project root (2 levels up from this file) to Python's module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Import necessary modules from the project
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.cloud import bigquery
from utils import load_instructions_file, setup_logger

# === Logging Setup ===
bq_client = bigquery.Client()
logger = setup_logger(__name__)

# Loading different database files and caching them 
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

def get_enrollable_courses(tool_context: ToolContext) -> dict:
    """
    Retrieves the list of courses that a student still needs and that are offered in the upcoming term.

    This function performs two BigQuery operations:
    1. It fetches the list of courses the student has yet to complete.
    2. It fetches the list of courses being offered in the next academic term.
    It then computes the intersection to determine which needed courses are available for enrollment.

    Returns:
        dict: A dictionary containing:
            - 'status' (str): 'success' or 'error'.
            - 'message' (str): A descriptive message.
            - 'courses' (list): A sorted list of eligible course IDs the student can enroll in.

    Example:
        {
            "status": "success",
            "message": "4 courses are available for enrollment next term.",
            "courses": ["CS101", "MATH205", "ENG150", "BIO220"]
        }

    Notes:
        - The student ID is currently hardcoded and should be dynamically injected in production.
        - Relies on two BigQuery tables:
            1. `schedule_recommend.student_courses_needed`
            2. `schedule_recommend.next_term_course_offerings`
    """
    try:
        # === Get list of courses student still needs ===
        student_id = "AAAr+31XvoSD4GO4PvUzMvA3tZzHzQezVLUhUdPuwiQ="
        tool_context.state["student_id"] = student_id  # Store in context for later use

        query_needed = """
            SELECT Still_Needed
            FROM `schedule_recommend.student_courses_needed`
            WHERE TO_BASE64(Student_ID) = @student_id
        """
        job_config_needed = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("student_id", "STRING", student_id)
            ]
        )
        result_needed = list(bq_client.query(query_needed, job_config=job_config_needed).result())

        if not result_needed or not result_needed[0]["Still_Needed"]:
            return {
                "status": "error",
                "message": "No 'Still_Needed' courses found for the student.",
                "courses": []
            }

        still_needed = set(
            c.strip() for c in result_needed[0]["Still_Needed"].split(",") if c.strip()
        )

        # === Get list of courses offered next term ===
        query_offerings = """
            SELECT COURSE_ID
            FROM `schedule_recommend.next_term_course_offerings`
        """
        result_offerings = list(bq_client.query(query_offerings).result())
        offered_courses = set(row["COURSE_ID"] for row in result_offerings if row["COURSE_ID"])

        # === Intersect ===
        eligible_courses = sorted(list(still_needed & offered_courses))

        return {
            "status": "success",
            "message": f"{len(eligible_courses)} courses are available for enrollment next term.",
            "courses": eligible_courses
        }

    except Exception as e:
        print(f"Error fetching enrollable courses: {e}")
        return {
            "status": "error",
            "message": f"Failed to load enrollable courses: {e}",
            "courses": []
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