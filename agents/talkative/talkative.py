from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from utils.logging_config import setup_logger
from utils.file_loader import load_instructions_file


# === Logging Setup ===
logger = setup_logger(__name__)

# === Agent Configuration ===
MODEL = "gemini-2.0-flash"
NAME = "talkative"
DESCRIPTION = load_instructions_file(filename="talkative/description.txt")
INSTRUCTIONS = load_instructions_file(filename="talkative/instructions.txt")

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