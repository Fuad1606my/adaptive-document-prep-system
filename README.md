# Adaptive Document Preparation System

A local AI-powered adaptive study system for generating Multiple Choice Questions (MCQs) from a multi-section PDF document, collecting user answers, scoring sessions, storing preparation history in a Knowledge Base, and adapting future question generation based on historical weak areas.

This project was built for the AI/ML Intern Take-Home Assessment.

---

## 1. Project Overview

The system ingests the provided `SLATEFALL_DOSSIER.pdf`, parses it into 10 document sections, allows users to select one or more sections for preparation, generates MCQs from those sections, collects answers, scores the session, stores the result in a Knowledge Base, and adapts later sessions using previously missed topics.

The project supports three ways to use the system:

1. **CLI** for evaluation scenarios and reproducible outputs.
2. **FastAPI REST API** for backend integration and Swagger testing.
3. **Streamlit UI** for real users to study interactively.

The key adaptive behavior is:

- First-time run over selected sections = `cold_start`
- Returning run over previously attempted sections = `adaptive`
- Adaptive runs use historical wrong topics to influence question generation
- Previously mastered questions are tracked to reduce excessive repetition
- Wrong answers are stored and used to focus future practice

---

## 2. Core Features

- PDF ingestion using PyMuPDF
- Automatic section mapping for the 10-section SLATEFALL dossier
- CLI-based prep session execution
- FastAPI backend with Swagger documentation
- Streamlit user interface
- Manual answer mode for real users
- Simulated answer mode for evaluation runs
- Local Ollama LLM integration for MCQ generation
- Deterministic fallback MCQ generator for reliability
- Scoring with correct/wrong marking
- Correct answer and clarification for every wrong answer
- JSON-based Knowledge Base
- Historical weak topic detection
- Adaptive question generation
- Scenario A and Scenario B output exports
- Human-readable KB snapshots
- Offline-friendly local execution

---

## 3. Tech Stack

| Component | Choice |
|---|---|
| Language | Python |
| PDF Parsing | PyMuPDF |
| Local LLM | Ollama with `llama3.2:3b` |
| Backend API | FastAPI |
| Server | Uvicorn |
| User Interface | Streamlit |
| Knowledge Base | JSON file |
| CLI Output | Rich |
| Validation | Pydantic + custom LLM response validation |
| MCQ Generation | Ollama LLM with fallback rule-based generator |
| Data Display | Pandas / Streamlit dataframes |

---

## 4. Why This Stack

The assessment requires the system to run locally or against free-tier services. This implementation uses **Ollama** so that MCQ generation can run locally without paid APIs.

The project also includes a deterministic fallback generator. If Ollama is unavailable, slow, or returns malformed JSON, the fallback generator keeps the application usable and prevents scenario runs from failing.

FastAPI was chosen because it provides a clean Python backend and automatic Swagger documentation. Streamlit was added to make the system usable by real users, not just API testers.

The JSON Knowledge Base was chosen because it is simple, transparent, easy to inspect, and explicitly suitable for this assessment’s evaluation workflow.

---

## 5. Project Structure

```text
adaptive-document-prep-system/
│
├── data/
│   ├── SLATEFALL_DOSSIER.pdf
│   └── kb.json
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── pdf_parser.py
│   ├── section_mapper.py
│   ├── llm_client.py
│   ├── mcq_generator.py
│   ├── scoring.py
│   ├── kb_manager.py
│   ├── adaptive_engine.py
│   ├── exporter.py
│   ├── api.py
│   └── cli.py
│
├── outputs/
│   ├── scenario_a/
│   ├── scenario_b_iter1/
│   ├── scenario_b_iter2/
│   └── scenario_b_iter3/
│
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 6. Prerequisites

- Python 3.11+ recommended
- Git
- Ollama installed locally for LLM-based generation
- The provided `SLATEFALL_DOSSIER.pdf` file placed in the `data/` folder

This project was developed and tested with Python 3.14 on Windows.

---

## 7. Setup Instructions

Clone the repository:

```bash
git clone https://github.com/Fuad1606my/adaptive-document-prep-system.git
cd adaptive-document-prep-system
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```bash
venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```bash
venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 8. Ollama Local LLM Setup

This project supports local LLM-based MCQ generation through Ollama.

Install Ollama on Windows:

```powershell
irm https://ollama.com/install.ps1 | iex
```

Pull the model:

```bash
ollama pull llama3.2:3b
```

Test the model:

```bash
ollama run llama3.2:3b
```

Example test prompt:

```text
Say hello in one sentence.
```

Exit Ollama chat:

```text
/bye
```

The project calls Ollama through:

```text
http://localhost:11434/api/chat
```

If Ollama is unavailable or returns invalid JSON, the system automatically falls back to the local deterministic generator.

---

## 9. Streamlit User Interface

Run the interactive UI:

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

The UI supports:

- selecting one or more PDF sections
- choosing questions per section
- manual answer mode
- simulated answer mode
- viewing generated MCQs
- answering A/B/C/D questions
- scoring the session
- viewing correct answers and clarifications
- seeing whether each question came from `ollama_llm` or `fallback_rule_based`
- viewing historical weak topics
- viewing KB snapshots
- running Scenario B export

---

## 10. Answer Modes

The system supports two answer modes.

### Manual Mode

Manual mode is intended for real users.

Flow:

```text
Select sections
Generate questions
Choose A/B/C/D manually
Submit answers
View score and clarifications
Save session to KB
Use history for future adaptation
```

Manual mode makes the project useful as a real adaptive study tool.

### Simulated Mode

Simulated mode is used for evaluation and reproducible scenario outputs.

Supported simulation modes:

```text
mixed
all_correct
all_wrong
random
```

Simulated answers are acceptable for the required assessment scenarios.

---

## 11. CLI Commands

### Parse the PDF and show detected sections

```bash
python -m src.cli parse
```

Expected result:

- PDF loads successfully
- 50 pages detected
- 10 sections parsed

### Run a single prep session

```bash
python -m src.cli run-session --sections 5 8 --n 5 --simulate mixed
```

Available simulation modes:

```text
all_correct
all_wrong
mixed
random
```

### Test Knowledge Base behavior

```bash
python -m src.cli kb-test
```

This creates a dummy session and verifies KB save/load and snapshot behavior.

---

## 12. Evaluation Scenarios

### Scenario A

Cold-start prep over two sections:

```bash
python -m src.cli scenario-a
```

Exports:

```text
outputs/scenario_a/
  questions_scenario_a.json
  kb_snapshot_scenario_a.json
```

### Scenario B

Three consecutive adaptive iterations:

```bash
python -m src.cli scenario-b
```

Scenario B uses:

```text
Iteration 1: sections 5, 8
Iteration 2: sections 6, 8, 9
Iteration 3: section 8
```

Exports:

```text
outputs/scenario_b_iter1/
  questions_iter1.json
  kb_snapshot_iter1.json

outputs/scenario_b_iter2/
  questions_iter2.json
  kb_snapshot_iter2.json

outputs/scenario_b_iter3/
  questions_iter3.json
  kb_snapshot_iter3.json
```

Scenario B demonstrates the core adaptive behavior because section 8 appears in multiple iterations, allowing the system to use historical mistakes to influence later questions.

---

## 13. FastAPI Usage

Start the FastAPI server:

```bash
uvicorn src.api:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Available endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/sections` | List parsed PDF sections |
| POST | `/sessions/run` | Run a prep session |
| GET | `/kb/snapshot` | View KB snapshot |
| POST | `/kb/reset` | Reset KB |
| POST | `/scenarios/a/run` | Run Scenario A |
| POST | `/scenarios/b/run` | Run Scenario B |

Example request for `/sessions/run`:

```json
{
  "sections": [5, 8],
  "n": 5,
  "simulate": "mixed"
}
```

---

## 14. Knowledge Base Design

The KB is stored in:

```text
data/kb.json
```

Each session record contains:

```json
{
  "session_id": "session_...",
  "timestamp": "...",
  "session_type": "cold_start or adaptive",
  "sections": [5, 8],
  "questions": [],
  "score": {
    "total": 10,
    "correct": 6,
    "wrong": 4,
    "accuracy": 60
  },
  "weak_topics": []
}
```

Each question record stores:

```json
{
  "question_id": "q_...",
  "section_id": 5,
  "topic": "Three-Two-One Rule",
  "question": "...",
  "options": {
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "..."
  },
  "correct_answer": "A",
  "user_answer": "B",
  "is_correct": false,
  "explanation": "...",
  "clarification": "...",
  "adaptive_reason": "...",
  "generator": "ollama_llm"
}
```

The KB supports:

- retrieving prior sessions for selected sections
- retrieving question-level results
- identifying repeated weak topics
- tracking mastered questions
- exporting top-5 recent session snapshots

---

## 15. Adaptive Logic

The adaptive engine checks whether selected sections have previous session history.

If no prior history exists:

```text
session_type = cold_start
```

If history exists:

```text
session_type = adaptive
```

For adaptive sessions, the system:

1. Retrieves prior sessions involving selected sections
2. Finds topics that were answered incorrectly
3. Prioritizes those weak topics during MCQ generation
4. Adds `adaptive_reason` metadata to generated questions
5. Avoids excessive repetition of previously correct questions where possible
6. Saves the new results back into the KB for future runs

Example adaptive reason:

```text
Focused on previously missed topic: Known Bases, Safehouses, and Operational Territory
```

---

## 16. MCQ Generation

The MCQ generator uses a hybrid design:

```text
Primary: Ollama local LLM
Fallback: deterministic rule-based generator
```

The system first attempts to generate MCQs using Ollama. Local models may occasionally return malformed JSON or fewer valid questions than requested, so the project validates the LLM response before using it.

If the LLM output fails validation, the system uses the fallback generator.

Every generated question stores its generator source:

```json
"generator": "ollama_llm"
```

or:

```json
"generator": "fallback_rule_based"
```

This makes the output auditable for reviewers.

---

## 17. Output Files

Required scenario outputs are stored under:

```text
outputs/
```

Scenario A:

```text
outputs/scenario_a/questions_scenario_a.json
outputs/scenario_a/kb_snapshot_scenario_a.json
```

Scenario B:

```text
outputs/scenario_b_iter1/questions_iter1.json
outputs/scenario_b_iter1/kb_snapshot_iter1.json

outputs/scenario_b_iter2/questions_iter2.json
outputs/scenario_b_iter2/kb_snapshot_iter2.json

outputs/scenario_b_iter3/questions_iter3.json
outputs/scenario_b_iter3/kb_snapshot_iter3.json
```

These files include generated questions, simulated answers, scoring results, adaptive reasons, and KB snapshots.

---

## 18. Known Limitations

- Ollama must be installed locally to use real LLM generation.
- Local LLM generation can be slower than a cloud API.
- The fallback generator is deterministic and less natural than LLM-generated questions.
- JSON storage is used instead of a production database for simplicity and transparency.
- The adaptive logic is topic-based rather than vector-search-based.
- Scenario A and Scenario B reset the KB before generating fresh scenario outputs.
- The system is designed for local single-user evaluation, not multi-user production deployment.

---

## 19. Development Notes

The project focuses on the assessment’s core differentiator:

> The system must distinguish between first-time preparation and returning adaptive runs, using historical mistakes and question drift to shape later question generation.

Scenario B demonstrates this behavior through three consecutive runs where section 8 is repeated and the system adapts based on prior wrong topics.

The Streamlit UI demonstrates the same system as a real user-facing adaptive study application.

---

## 20. Quick Review Commands

CLI:

```bash
python -m src.cli parse
python -m src.cli scenario-a
python -m src.cli scenario-b
```

FastAPI:

```bash
uvicorn src.api:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Streamlit UI:

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

Ollama:

```bash
ollama pull llama3.2:3b
ollama run llama3.2:3b
```

---

## 21. Repository

Public GitHub repository:

```text
https://github.com/Fuad1606my/adaptive-document-prep-system
```