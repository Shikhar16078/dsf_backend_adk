# 🤖 Agents Architecture Overview

This folder contains the agents that drive the behavior of the system, built using the Google ADK (Agent Development Kit). These agents are designed to handle specific categories of user queries by coordinating between intelligent routing (`coordinator`) and task-specific handling (`scheduler` and `talkative`).

---

## 🧠 Agents Overview

### 🔸 `coordinator` (Root Agent)

- **Role**: Serves as the entry point and top-level router for all incoming user requests.
- **Functionality**:
  - Parses user intent and routes queries to appropriate sub-agents.
  - Does **not** respond directly to users.
  - Loads and injects mock student profile (`student_details`) into the agent's state via a `before_agent_callback`.
- **Sub-agents**:
  - `scheduler`
  - `talkative`
- **Student Mocking**:
  - Loads from `database/students.json`
  - Uses a hardcoded `STUDENT_ID` for testing: `"862547410"`

### 🔹 `scheduler` (Sub-agent)

- **Role**: Handles all scheduling and course-planning queries from users.
- **Functionality**:
  - Accesses and uses mock data from:
    - `courses.json`
    - `offerings.json`
    - `students.json` (via state injected by `coordinator`)
  - Implements the following tools:
    - `get_enrollable_courses(quarter, year, tool_context)`  
      Determines which courses a student can enroll in, based on past completions and prerequisites.
    - `get_course_details(course_id)`  
      Retrieves metadata for a specific course (e.g., title, prerequisites).
    - `get_course_offerings(quarter, year)`  
      Lists courses available in a specific term.
    - `build_schedule(avoid_days, avoid_times, tool_context)`  
      Generates a mock schedule respecting time/day constraints (currently placeholder logic).
    - `get_student_details(tool_context)`  
      Returns the student's mock profile from state.
- **Logging**:
  - Logs key steps like data loading, eligibility filtering, and error cases.
- **Model**: `gemini-2.0-flash`

### 🔹 `talkative` (Sub-agent)

- **Role**: Manages off-topic, casual, ethical, or social conversations.
- **Functionality**:
  - Handles greetings, farewells, and any non-technical or inappropriate queries.
  - Purely instruction-driven with **no tool usage or backend access**.
  - Acts as a catch-all for non-scheduling intents.
- **Model**: `gemini-2.0-flash`

---

## 📁 File Structure

```
agents/
├── coordinator/
│ ├── init.py
│ ├── instructions.txt
│ ├── description.txt
├── scheduler/
│ ├── init.py
│ ├── instructions.txt
│ ├── description.txt
├── talkative/
│ ├── init.py
│ ├── instructions.txt
│ ├── description.txt
```

---

## 🛠️ Extending This System

- To add a **new agent**, define it similarly to the existing ones, including:
  - Instructions file
  - Description file
  - Optional tools and callback logic
- Update the `coordinator`’s `sub_agents` list to include the new agent.
- Ensure appropriate intent-routing logic is added (manual or via LLM intent recognition).

---

## 📌 Notes

- All agents share the same language model (`gemini-2.0-flash`) but serve **distinct purposes**.
- The design ensures **clear separation of concerns**, enabling modularity and easier debugging.
- State management is handled consistently using ADK’s `ToolContext`.