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
        student_details = tool_context.state.get("student_details", {})
        student_id = student_details.get("Student_ID")
        logger.info(f"Fetching enrollable courses for student ID: {student_id}")
        
        # If student_id is not set, return an error
        if not student_id:
            return {
                "status": "error",
                "message": "Student ID not found in context state.",
                "courses": []
            }
        
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
    Retrieve detailed offering information for a specific course by its course ID.

    This function queries BigQuery's `next_term_course_offerings` table to find all sections
    of a given course (e.g., "ENGR001M") offered in the upcoming term.

    Parameters:
        course_id (str): The course ID to look up.

    Returns:
        dict: {
            "status": "success" | "error",
            "course_details": [list of offering dicts],
            "message": optional message
        }
    """
    try:
        query = """
            SELECT *
            FROM `schedule_recommend.next_term_course_offerings`
            WHERE COURSE_ID = @course_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("course_id", "STRING", course_id)
            ]
        )
        results = list(bq_client.query(query, job_config=job_config).result())

        if not results:
            return {
                "status": "error",
                "course_details": [],
                "message": f"No offerings found for course '{course_id}'."
            }

        offerings = [dict(row) for row in results]

        return {
            "status": "success",
            "course_details": offerings
        }

    except Exception as e:
        logger.error(f"Failed to fetch course details for {course_id}: {e}")
        return {
            "status": "error",
            "course_details": [],
            "message": f"Failed to fetch course details: {e}"
        }
    

# Not Being Used For Now
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
    tools=[get_enrollable_courses, get_course_details, get_student_details],
)

root_agent = scheduler
logger.info(f"Initialized {NAME} agent.")