import os
import sys

# Add the project root (2 levels up from this file) to Python's module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from utils import load_instructions_file, setup_logger

# === Logging Setup ===
logger = setup_logger(__name__)

# === Agent Configuration ===
MODEL = "gemini-2.0-flash"
NAME = "talkative"
DESCRIPTION = load_instructions_file(filename="agents/talkative/description.txt")
INSTRUCTIONS = load_instructions_file(filename="agents/talkative/instructions.txt")

# === Logging ===
logger.info(f"Entered {NAME} agent.")
logger.info(f"Using Description: {DESCRIPTION[:50]}...")
logger.info(f"Using Instructions: {INSTRUCTIONS[:50]}...")

# Create the agent
talkative = Agent(
    name=NAME,
    model=MODEL,
    description=DESCRIPTION,
    instruction=INSTRUCTIONS,
)

root_agent = talkative
logger.info(f"Initialized {NAME} agent.")