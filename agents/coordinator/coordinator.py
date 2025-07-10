from utils.logging_config import setup_logger

from google.adk import Agent
from utils.file_loader import load_instructions_file
from agents.talkative import root_agent as talkative
from agents.scheduler import root_agent as scheduler

# === Agent Configuration ===
MODEL = "gemini-2.0-flash"
NAME = "manager"
INSTRUCTIONS = load_instructions_file(filename="agents/coordinator/instructions.txt")
DESCRIPTION = load_instructions_file(filename="agents/coordinator/description.txt")

# === Logging Configuration ===
logger = setup_logger(__name__)
logger.info(f"Entered {NAME} agent.")
logger.info(f"Using Description: {DESCRIPTION[:50]}...")  # Log first 50 characters for brevity
logger.info(f"Using Instructions: {INSTRUCTIONS[:50]}...")  # Log first 50 characters for brevity

# Create the root coordinator agent with the talkative and scheduler sub-agent
coordinator = Agent(
    name=NAME,
    model=MODEL,
    description=DESCRIPTION,
    instruction=INSTRUCTIONS,
    sub_agents=[talkative, scheduler],
)

root_agent = coordinator

# Log the successful initialization of the agent
logger.info(f"Initialized {NAME} agent.")