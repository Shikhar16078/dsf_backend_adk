import os
import sys
import json

# Add the project root (2 levels up from this file) to Python's module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Import Utility functions
from utils import setup_logger
from utils import load_instructions_file

# Import necessary modules from Google ADK
from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from typing import Optional
from google.genai import types

# Import diferent agents
from agents.talkative import root_agent as talkative
from agents.scheduler import root_agent as scheduler

# Setup logger for this module
logger = setup_logger(__name__)

# Mocking Student ID
STUDENT_ID = "862547410"

# === Agent Configuration ===
MODEL = "gemini-2.0-flash"
NAME = "manager"
INSTRUCTIONS = load_instructions_file(filename="agents/coordinator/instructions.txt")
DESCRIPTION = load_instructions_file(filename="agents/coordinator/description.txt")

# === Logging Configuration ===
logger.info(f"Entered {NAME} agent.")
logger.info(f"Using Description: {DESCRIPTION[:50]}...")  # Log first 50 characters for brevity
logger.info(f"Using Instructions: {INSTRUCTIONS[:50]}...")  # Log first 50 characters for brevity

# === Agent Callbacks ===
def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Callback that runs before the agent starts processing a request.

    Loads the student record matching STUDENT_ID from students.json
    and sets it into context state as 'student_details'.
    """
    state = callback_context.state

    try:
        with open("database/students.json", "r") as f:
            students = json.load(f)
        student = next((s for s in students if s["student_id"] == STUDENT_ID), None)

        if student:
            state["student_details"] = student
            logger.info(f"[BEFORE CALLBACK] Loaded student: {student['name']} ({STUDENT_ID})")
        else:
            logger.warning(f"[BEFORE CALLBACK] Student ID {STUDENT_ID} not found in students.json")
            state["student_details"] = {}

    except Exception as e:
        logger.error(f"[BEFORE CALLBACK] Failed to load students.json: {e}")
        state["student_details"] = {}

    logger.info("[BEFORE CALLBACK] Initialized state with student details and metadata.")
    return None


# Create the root coordinator agent with the talkative and scheduler sub-agent
coordinator = Agent(
    name=NAME,
    model=MODEL,
    description=DESCRIPTION,
    instruction=INSTRUCTIONS,
    sub_agents=[talkative, scheduler],
    before_agent_callback=before_agent_callback,
)

root_agent = coordinator

# Log the successful initialization of the agent
logger.info(f"Initialized {NAME} agent.")