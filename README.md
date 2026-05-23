# Adaptive Document Preparation System

A backend-driven adaptive preparation system for generating MCQs from a multi-section PDF document, scoring simulated user answers, storing preparation history in a Knowledge Base, and adapting future question generation based on historical weak areas.

This project was built for the AI/ML Intern Take-Home Assessment.

---

## 1. Project Overview

The system ingests the provided `SLATEFALL_DOSSIER.pdf`, parses it into 10 document sections, allows selected sections to be used for preparation, generates MCQs from those sections, simulates user answers, scores the session, stores the result in a Knowledge Base, and adapts later sessions using previously missed topics.

The key adaptive behavior is:

- First-time run over a section = `cold_start`
- Returning run over a previously attempted section = `adaptive`
- Adaptive runs use historical wrong topics to influence question generation
- Previously mastered questions are tracked to reduce excessive repetition

---

## 2. Core Features

- PDF ingestion using PyMuPDF
- Section mapping for the 10-section SLATEFALL dossier
- CLI-based prep session execution
- FastAPI backend with Swagger documentation
- MCQ generation with a deterministic fallback generator
- Simulated user answers for evaluation
- Scoring with correct/wrong marking
- Clarification for wrong answers
- JSON-based Knowledge Base
- Historical weak topic detection
- Adaptive question generation
- Scenario A and Scenario B output exports
- Human-readable KB snapshots

---

## 3. Tech Stack

| Component | Choice |
|---|---|
| Language | Python |
| PDF Parsing | PyMuPDF |
| API Layer | FastAPI |
| Server | Uvicorn |
| Knowledge Base | JSON file |
| CLI Output | Rich |
| Validation | Pydantic |
| MCQ Generation | Rule-based fallback generator, designed for LLM extension |

---

## 4. Why This Stack

The assessment requires the system to run locally or against free-tier services. To make the project easy for reviewers to run, this implementation uses a deterministic fallback MCQ generator instead of requiring a paid API key.

The code is structured so that a real free/local LLM provider such as Gemini, Groq, Ollama, or HuggingFace can be plugged into `src/llm_client.py` later.

The JSON Knowledge Base was chosen because it is simple, transparent, and easy to inspect during evaluation.

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
│   ├── config.py
│   ├── pdf_parser.py
│   ├── section_mapper.py
│   ├── mcq_generator.py
│   ├── scoring.py
│   ├── kb_manager.py
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
├── requirements.txt
├── README.md
└── .gitignore

```
## 6. Prerequisites

- Python 3.11+ recommended
- Git
- The provided `SLATEFALL_DOSSIER.pdf` file placed in the `data/` folder

This project was developed and tested with Python 3.14.

---

## 7. Setup Instructions

Clone the repository:

```bash
git clone <repository-url>
cd adaptive-document-prep-system
```

Replace `<repository-url>` with the public GitHub/GitLab repository link after uploading the project.

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

## 8. CLI Commands

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

## 9. Evaluation Scenarios

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

---

## 10. API Usage

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

## 11. Knowledge Base Design

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

The KB supports:

- retrieving prior sessions for selected sections
- retrieving question-level results
- identifying repeated weak topics
- tracking mastered questions
- exporting top-5 recent session snapshots

---

## 12. Adaptive Logic

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

Example adaptive reason:

```text
Focused on previously missed topic: Known Bases, Safehouses, and Operational Territory
```

---

## 13. MCQ Generation

This implementation includes a deterministic fallback MCQ generator so the project can run without paid APIs.

Each MCQ includes:

- question ID
- section ID
- topic
- question text
- 4 answer options
- correct answer
- explanation
- adaptive reason
- generator metadata
- simulated user answer
- correctness result
- clarification

The design allows later integration with a free/local LLM by replacing or extending `src/llm_client.py`.

---

## 14. Known Limitations

- The current MCQ generator is a deterministic fallback, not a fully connected external LLM.
- Some generated distractors are generic.
- The system prioritizes reliable local execution over advanced natural language quality.
- The UI is not implemented; interaction is available through CLI and FastAPI Swagger docs.
- JSON storage is used instead of a production database for transparency and simplicity.
- Running Scenario A or Scenario B resets the KB before generating fresh scenario outputs.

---

## 15. Development Notes

The project focuses on the assessment’s core differentiator:

> The system must distinguish between first-time preparation and returning adaptive runs, using historical mistakes and question drift to shape later question generation.

Scenario B demonstrates this behavior through three consecutive runs where section 8 is repeated and the system adapts based on prior wrong topics.

---

## 16. Quick Review Commands

```bash
python -m src.cli parse
python -m src.cli scenario-a
python -m src.cli scenario-b
uvicorn src.api:app --reload
```