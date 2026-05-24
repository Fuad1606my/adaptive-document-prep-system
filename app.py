import pandas as pd
import streamlit as st
from datetime import datetime

from src.config import PDF_PATH
from src.pdf_parser import extract_pdf_text, get_pdf_page_count
from src.section_mapper import split_sections, get_section_summary, SECTION_TITLES
from src.kb_manager import (
    get_sessions_for_sections,
    get_wrong_topics_for_sections,
    get_mastered_questions_for_sections,
    get_kb_snapshot,
    create_session_record,
    add_session,
    save_kb,
)
from src.mcq_generator import generate_mcqs_for_sections
from src.scoring import simulate_answers, score_questions
from src.exporter import export_questions, export_kb_snapshot, get_scenario_dir


st.set_page_config(
    page_title="Adaptive Document Preparation System",
    page_icon="📘",
    layout="wide",
)
st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(135deg, #0b1020 0%, #111827 45%, #06121f 100%);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #1f2937 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    .hero-card {
        padding: 28px 32px;
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(37,99,235,0.18), rgba(16,185,129,0.10));
        border: 1px solid rgba(255,255,255,0.10);
        box-shadow: 0 18px 45px rgba(0,0,0,0.25);
        margin-bottom: 22px;
    }

    .hero-title {
        font-size: 44px;
        font-weight: 800;
        line-height: 1.1;
        color: #f8fafc;
        margin-bottom: 10px;
    }

    .hero-subtitle {
        font-size: 17px;
        color: #cbd5e1;
        max-width: 980px;
    }

    .badge-row {
        margin-top: 18px;
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }

    .badge {
        padding: 7px 12px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 600;
        background: rgba(15,23,42,0.65);
        color: #e5e7eb;
        border: 1px solid rgba(255,255,255,0.12);
    }

    .metric-card {
        padding: 20px;
        border-radius: 18px;
        background: rgba(15,23,42,0.78);
        border: 1px solid rgba(255,255,255,0.10);
        box-shadow: 0 12px 28px rgba(0,0,0,0.22);
    }

    .metric-label {
        color: #94a3b8;
        font-size: 13px;
        margin-bottom: 4px;
    }

    .metric-value {
        color: #f8fafc;
        font-size: 34px;
        font-weight: 800;
    }

    .section-card {
        padding: 18px 20px;
        border-radius: 18px;
        background: rgba(15,23,42,0.65);
        border: 1px solid rgba(255,255,255,0.10);
        margin-bottom: 14px;
    }

    .question-card {
        padding: 22px;
        border-radius: 20px;
        background: rgba(15,23,42,0.72);
        border: 1px solid rgba(255,255,255,0.10);
        margin-bottom: 18px;
        box-shadow: 0 14px 30px rgba(0,0,0,0.22);
    }

    .correct-card {
        border-left: 5px solid #22c55e;
    }

    .wrong-card {
        border-left: 5px solid #ef4444;
    }

    .soft-divider {
        height: 1px;
        background: rgba(255,255,255,0.10);
        margin: 18px 0;
    }

    div.stButton > button {
        border-radius: 14px;
        font-weight: 700;
        min-height: 46px;
    }

    div[data-testid="stMetric"] {
        background: rgba(15,23,42,0.70);
        border: 1px solid rgba(255,255,255,0.10);
        padding: 18px;
        border-radius: 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_sections():
    full_text = extract_pdf_text(PDF_PATH)
    return split_sections(full_text)


def generate_questions_only(section_ids, n_per_section):
    sections = load_sections()
    previous_sessions = get_sessions_for_sections(section_ids)
    session_type = "adaptive" if previous_sessions else "cold_start"
    weak_topics = get_wrong_topics_for_sections(section_ids)
    mastered_questions = get_mastered_questions_for_sections(section_ids)

    questions = generate_mcqs_for_sections(
        sections=sections,
        selected_section_ids=section_ids,
        n_per_section=n_per_section,
        weak_topics=weak_topics,
        mastered_questions=mastered_questions,
    )

    return questions, weak_topics, session_type


def save_scored_session(section_ids, questions, answers, session_type):
    scored_questions = score_questions(questions, answers)

    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    session_record = create_session_record(
        session_id=session_id,
        sections=section_ids,
        questions=scored_questions,
        session_type=session_type,
    )

    add_session(session_record)
    return session_record


def run_simulated_session(section_ids, n_per_section, simulate_mode):
    questions, weak_topics, session_type = generate_questions_only(
        section_ids=section_ids,
        n_per_section=n_per_section,
    )
    answers = simulate_answers(questions, mode=simulate_mode)
    session_record = save_scored_session(section_ids, questions, answers, session_type)
    return session_record, weak_topics


def render_question_result_card(question, index):
    is_correct = question.get("is_correct")
    status_label = "✅ Correct" if is_correct else "❌ Wrong"
    card_class = "correct-card" if is_correct else "wrong-card"

    st.markdown(
        f"""
        <div class="question-card {card_class}">
            <h3>Q{index}. {question.get("question", "")}</h3>
            <p>
                <b>Section:</b> {question.get("section_id")} &nbsp; | &nbsp;
                <b>Topic:</b> {question.get("topic")} &nbsp; | &nbsp;
                <b>Status:</b> {status_label}
            </p>
            <p><b>Generator:</b> <code>{question.get("generator")}</code></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            options = question.get("options", {})
            for key in ["A", "B", "C", "D"]:
                option_text = options.get(key, "")
                if key == question.get("correct_answer"):
                    st.markdown(f"**{key}. {option_text}**")
                else:
                    st.markdown(f"{key}. {option_text}")

        with col2:
            st.markdown(f"**Your answer:** `{question.get('user_answer')}`")
            st.markdown(f"**Correct answer:** `{question.get('correct_answer')}`")

            adaptive_reason = question.get("adaptive_reason")
            if adaptive_reason:
                st.info(adaptive_reason)

            if is_correct:
                st.success(question.get("clarification", "Correct."))
            else:
                st.warning(question.get("clarification", ""))


def render_manual_question(question, index):
    st.markdown(
        f"""
        <div class="question-card">
            <h2>Q{index}. {question.get("question")}</h2>
            <p>
                <b>Section {question.get("section_id")}</b> •
                Topic: <b>{question.get("topic")}</b> •
                Generator: <code>{question.get("generator")}</code>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    options = question.get("options", {})
    formatted_options = [
        f"{key}. {options.get(key, '')}"
        for key in ["A", "B", "C", "D"]
    ]

    selected = st.radio(
        "Choose your answer",
        options=formatted_options,
        key=f"manual_answer_{question.get('question_id')}",
        index=None,
    )

    if selected:
        answer_key = selected.split(".")[0]
        st.session_state.manual_answers[question["question_id"]] = answer_key

def render_score_summary(session_record):
    score = session_record.get("score", {})

    st.success("Session completed and saved to KB.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Session Type</div>
                <div class="metric-value">{session_record.get("session_type")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Total Questions</div>
                <div class="metric-value">{score.get("total", 0)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Correct</div>
                <div class="metric-value">{score.get("correct", 0)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Accuracy</div>
                <div class="metric-value">{score.get("accuracy", 0)}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_weak_topics_table(weak_topics):
    st.markdown("### Historical Weak Topics Used")

    if weak_topics:
        weak_rows = []
        for item in weak_topics:
            weak_rows.append(
                {
                    "topic": item.get("topic"),
                    "wrong_count": item.get("wrong_count"),
                    "correct_count": item.get("correct_count"),
                    "sections": str(item.get("sections")),
                }
            )
        st.dataframe(pd.DataFrame(weak_rows), width="stretch")
    else:
        st.info("No previous weak topics found for this selection.")


def render_kb_snapshot():
    snapshot = get_kb_snapshot()

    st.subheader("Knowledge Base Snapshot")
    st.caption("Top recent preparation sessions stored in the KB.")

    st.metric("Total sessions", snapshot.get("total_sessions", 0))

    recent_sessions = snapshot.get("recent_sessions", [])

    if not recent_sessions:
        st.info("No sessions stored yet.")
        return

    rows = []
    for session in recent_sessions:
        score = session.get("score", {})
        rows.append(
            {
                "session_id": session.get("session_id"),
                "session_type": session.get("session_type"),
                "sections": str(session.get("sections")),
                "score": f"{score.get('correct', 0)}/{score.get('total', 0)}",
                "accuracy": score.get("accuracy", 0),
                "weak_topics": ", ".join(session.get("weak_topics", [])),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch")


def run_scenario_b_from_ui():
    save_kb({"sessions": []})

    scenario_steps = [
        {
            "name": "scenario_b_iter1",
            "sections": [5, 8],
            "questions_file": "questions_iter1.json",
            "snapshot_file": "kb_snapshot_iter1.json",
            "simulate": "mixed",
        },
        {
            "name": "scenario_b_iter2",
            "sections": [6, 8, 9],
            "questions_file": "questions_iter2.json",
            "snapshot_file": "kb_snapshot_iter2.json",
            "simulate": "mixed",
        },
        {
            "name": "scenario_b_iter3",
            "sections": [8],
            "questions_file": "questions_iter3.json",
            "snapshot_file": "kb_snapshot_iter3.json",
            "simulate": "mixed",
        },
    ]

    exported = []
    progress = st.progress(0)

    for index, step in enumerate(scenario_steps, start=1):
        session_record, _ = run_simulated_session(
            section_ids=step["sections"],
            n_per_section=5,
            simulate_mode=step["simulate"],
        )

        output_dir = get_scenario_dir(step["name"])

        questions_path = export_questions(
            output_dir,
            step["questions_file"],
            session_record,
        )

        snapshot_path = export_kb_snapshot(
            output_dir,
            step["snapshot_file"],
            get_kb_snapshot(),
        )

        exported.append(
            {
                "iteration": index,
                "sections": step["sections"],
                "session_type": session_record.get("session_type"),
                "score": session_record.get("score"),
                "questions_file": str(questions_path),
                "snapshot_file": str(snapshot_path),
            }
        )

        progress.progress(index / len(scenario_steps))

    return exported


if "manual_questions" not in st.session_state:
    st.session_state.manual_questions = None

if "manual_answers" not in st.session_state:
    st.session_state.manual_answers = {}

if "manual_context" not in st.session_state:
    st.session_state.manual_context = None

if "latest_session_record" not in st.session_state:
    st.session_state.latest_session_record = None

if "latest_weak_topics" not in st.session_state:
    st.session_state.latest_weak_topics = []


st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">📘 Adaptive Document Preparation System</div>
        <div class="hero-subtitle">
            A local AI-powered study platform that parses a multi-section PDF,
            generates adaptive MCQs, tracks weak topics, and improves future preparation
            using learning history.
        </div>
        <div class="badge-row">
            <span class="badge">Local Ollama LLM</span>
            <span class="badge">Adaptive Knowledge Base</span>
            <span class="badge">Manual + Simulated Mode</span>
            <span class="badge">PDF-Aware MCQ Engine</span>
            <span class="badge">Offline-Friendly</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Controls")
    st.markdown("### System Status")

    try:
        page_count = get_pdf_page_count(PDF_PATH)
        sections = load_sections()
        st.success("PDF loaded")
        st.caption(f"Pages: {page_count} | Sections: {len(sections)}")
    except Exception as exc:
        st.error(f"PDF load failed: {exc}")
        st.stop()

    st.markdown("---")

    section_options = {
        f"Section {sid}: {SECTION_TITLES.get(sid, f'Section {sid}')}": sid
        for sid in sorted(sections.keys())
    }

    selected_labels = st.multiselect(
        "Select sections",
        options=list(section_options.keys()),
        default=[
            "Section 5: Operational Tactics and Combat Doctrine",
            "Section 8: Known Bases, Safehouses, and Operational Territory",
        ],
    )

    selected_section_ids = [section_options[label] for label in selected_labels]

    n_per_section = st.slider(
        "Questions per section",
        min_value=1,
        max_value=5,
        value=2,
        step=1,
    )

    answer_mode = st.selectbox(
        "Answer mode",
        options=["Manual", "Simulated"],
        index=0,
    )

    simulate_mode = st.selectbox(
        "Simulation mode",
        options=["mixed", "all_correct", "all_wrong", "random"],
        index=0,
        disabled=(answer_mode == "Manual"),
    )

    st.markdown("---")

    if answer_mode == "Manual":
        generate_button = st.button(
            "Generate Manual Questions",
            type="primary",
            width="stretch",
        )
        submit_button = st.button(
            "Submit Manual Answers",
            width="stretch",
        )
    else:
        run_button = st.button(
            "Run Simulated Session",
            type="primary",
            width="stretch",
        )

    st.markdown("---")

    scenario_b_button = st.button(
        "Run Scenario B Export",
        width="stretch",
    )


tab1, tab2, tab3 = st.tabs(
    [
        "Prep Session",
        "Document Sections",
        "Knowledge Base",
    ]
)

with tab1:
    st.subheader("Prep Session")

    if not selected_section_ids:
        st.info("Select at least one section from the sidebar.")

    if answer_mode == "Manual":
        st.info("Manual mode: generate questions first, answer A/B/C/D, then submit.")

        if generate_button:
            if not selected_section_ids:
                st.error("Please select at least one section.")
            else:
                with st.spinner("Generating manual questions. Ollama may take time..."):
                    questions, weak_topics, session_type = generate_questions_only(
                        section_ids=selected_section_ids,
                        n_per_section=n_per_section,
                    )

                st.session_state.manual_questions = questions
                st.session_state.manual_answers = {}
                st.session_state.manual_context = {
                    "section_ids": selected_section_ids,
                    "weak_topics": weak_topics,
                    "session_type": session_type,
                }
                st.session_state.latest_session_record = None
                st.session_state.latest_weak_topics = weak_topics

                st.success("Questions generated. Select your answers below.")

        if st.session_state.manual_questions:
            context = st.session_state.manual_context or {}

            st.markdown("### Manual Questions")
            st.caption(f"Session type: {context.get('session_type')}")

            render_weak_topics_table(context.get("weak_topics", []))

            for idx, question in enumerate(st.session_state.manual_questions, start=1):
                render_manual_question(question, idx)

            answered_count = len(st.session_state.manual_answers)
            total_count = len(st.session_state.manual_questions)
            st.progress(answered_count / total_count if total_count else 0)
            st.caption(f"Answered {answered_count}/{total_count}")

            if submit_button:
                if answered_count < total_count:
                    st.error("Please answer all questions before submitting.")
                else:
                    session_record = save_scored_session(
                        section_ids=context.get("section_ids", selected_section_ids),
                        questions=st.session_state.manual_questions,
                        answers=st.session_state.manual_answers,
                        session_type=context.get("session_type", "cold_start"),
                    )

                    st.session_state.latest_session_record = session_record
                    st.success("Manual answers submitted and saved to KB.")

        if st.session_state.latest_session_record:
            st.markdown("### Manual Session Results")
            render_score_summary(st.session_state.latest_session_record)

            for idx, question in enumerate(
                st.session_state.latest_session_record.get("questions", []),
                start=1,
            ):
                render_question_result_card(question, idx)

    else:
        if run_button:
            if not selected_section_ids:
                st.error("Please select at least one section.")
            else:
                with st.spinner("Generating and scoring questions. Ollama may take time..."):
                    session_record, historical_weak_topics = run_simulated_session(
                        section_ids=selected_section_ids,
                        n_per_section=n_per_section,
                        simulate_mode=simulate_mode,
                    )

                st.session_state.latest_session_record = session_record
                st.session_state.latest_weak_topics = historical_weak_topics

                render_score_summary(session_record)
                render_weak_topics_table(historical_weak_topics)

                st.markdown("### Generated Questions and Results")
                for idx, question in enumerate(session_record.get("questions", []), start=1):
                    render_question_result_card(question, idx)

    if scenario_b_button:
        st.markdown("### Scenario B Export")

        with st.spinner("Running Scenario B. This may take time with Ollama..."):
            exported = run_scenario_b_from_ui()

        st.success("Scenario B completed and exported successfully.")
        st.dataframe(pd.DataFrame(exported), width="stretch")


with tab2:
    st.subheader("Parsed Document Sections")

    section_rows = []

    for section_id in sorted(sections.keys()):
        summary = get_section_summary(section_id, sections[section_id])
        section_rows.append(summary)

    st.dataframe(pd.DataFrame(section_rows), width="stretch")

    with st.expander("View section previews"):
        for section_id in sorted(sections.keys()):
            summary = get_section_summary(section_id, sections[section_id], max_chars=600)
            st.markdown(f"### Section {section_id}: {summary['title']}")
            st.write(summary["preview"])


with tab3:
    render_kb_snapshot()