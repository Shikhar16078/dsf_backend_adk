# 🧠 UCR Schedule Recommender - Backend (Google ADK)

This repository implements a multi-agent system using **Google's Agent Development Kit (ADK)** to assist UCR students with academic course scheduling. It forms the backend layer of the DSF project under the UCR Fellowship 2025.

---

## 🚀 Features

- 🤖 Modular agent architecture using Google ADK
- 🧭 Root agent routes requests to sub-agents based on user intent
- 📚 Scheduler agent recommends courses based on academic history
- 💬 Talkative agent handles casual, ethical, and off-topic conversation
- 📦 Easy to extend with new tools or agents
- 📜 Clean logging and instruction-based agent behavior

---

## 📁 Project Structure

```
dsf_backend_adk/
├── agents/
│   ├── scheduler/                    # Sub-agent for scheduling logic
│   │   ├── agent.py
│   │   ├── description.txt
│   │   └── instructions.txt
│   ├── talkative/                    # Sub-agent for casual interactions
│   │   ├── agent.py
│   │   ├── description.txt
│   │   └── instructions.txt
│   └── user_level_coordinator/       # Root agent (router)
│       ├── agent.py
│       ├── description.txt
│       └── instructions.txt
├── utils/
│   ├── file_loader.py                # Load instructions from .txt
│   └── logging_config.py             # Logger setup
├── tools/                           # Tool functions (if any)
├── logs/                            # Runtime logs
├── .env                             # API keys / config (not committed)
└── README.md
```

---

## 🧠 Agents Overview

### 🔸 coordinator (Root Agent)

- Routes user queries to appropriate sub-agents
- Parses intent but does **not** respond directly
- Sub-agents:
  - `scheduler`
  - `talkative`

### 🔹 scheduler

- Recommends courses based on previously taken ones
- Accepts `student_details` from state
- Returns list of enrollable courses

### 🔹 talkative

- Handles greetings, goodbyes, off-topic, unethical, or casual chatter
- Uses scripted logic and never invokes tools or accesses backend
- Robust instruction set ensures controlled replies

---

## 🛠️ Setup Instructions

This project uses [`uv`](https://github.com/astral-sh/uv) — a fast Python package manager and environment manager.

Follow these steps to get started:

---

### 1. **Install `uv`**

```bash
pip install uv
```

---

### 2. **Clone the repo**

```bash
git clone https://github.com/Shikhar16078/dsf_backend_adk.git
cd dsf_backend_adk
```

---

### 3. **Install all dependencies from `pyproject.toml`**

```bash
uv venv                          # Create a virtual environment 
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
uv pip install -r pyproject.toml  # ✅ Install dependencies from pyproject.toml
```

✅ The above `uv` commands will:
- Automatically create a `.venv/` if not already present
- Activate it
- Install all dependencies lightning-fast using `pyproject.toml`

---
### 4. **Set up `.env` file**

Create a `.env` file in the project root:

```bash
touch .env
```

Then paste the following starter content into it:

```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_gemini_key
OPENAI_API_KEY=your_open_ai_key
```

Make sure to replace the placeholder keys with your actual API credentials.

### 5. **Run the local agent**

```bash
adk web agents
```

---

📦 That's it! You're now running the backend agent environment with `uv` and ADK.

📝 **Optional: To add or update dependencies**, use:

```bash
uv add <package-name>
```

This will also update the `pyproject.toml` if applicable.

## 🧪 Development Notes

- Use `.env` to configure API keys (e.g., for Gemini or ADK)
- Logging outputs to `logs/agent-<timestamp>.log`
- Add sub-agents under `agents/<agent_name>/`
- Add tools under `tools/` and register in `agent.py`

## 🚀 Next Steps

- ✅ **Integrate Real Data Sources**  
  Replace mocked student info and course offerings by fetching real data from your university's database or APIs.

- 🧠 **Implement Core Scheduling Logic**  
  Enhance the `scheduler` agent to support logic for workload balancing, time conflict resolution, and prerequisite checking.

- 🎨 **Design Schedule Renderer**  
  Consider adding a separate sub-agent to handle schedule visualization and output formatting for the frontend.

- 🌐 **Build and Connect Frontend UI**  
  Develop a frontend interface (React, Next.js, etc.) that communicates with this backend via the ADK API. Handle session creation, message routing, and display of agent responses.
