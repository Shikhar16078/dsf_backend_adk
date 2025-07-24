import os
import sys
import difflib
import yaml

# Add the project root (2 levels up from this file) to Python's module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from google.adk.agents import Agent
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

# Load FAQs from the YAML file
def load_faqs() -> dict:
    faq_path = os.path.join(os.path.dirname(__file__), "faqs.yaml")
    with open(faq_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {item["question"].strip().lower(): item["answer"] for item in data}

faq_responses = load_faqs()

# === FAQ Tool ===
def get_faq_answer(question: str) -> dict:
    q = question.strip().lower()

    questions = list(faq_responses.keys())
    best_match = difflib.get_close_matches(q, questions, n=1, cutoff=0.6)

    if best_match:
        matched_question = best_match[0]
        return {"status": "success", "answer": faq_responses[matched_question]}
    else:
        return {
            "status": "error",
            "error_message": (
                "I'm sorry, I don't have an answer to that question yet. "
                "Please try rephrasing or contact your academic advisor."
            ),
        }

# Create the agent
talkative = Agent(
    name=NAME,
    model=MODEL,
    description=DESCRIPTION,
    instruction=INSTRUCTIONS,
    tools=[get_faq_answer],
)

root_agent = talkative
logger.info(f"Initialized {NAME} agent.")