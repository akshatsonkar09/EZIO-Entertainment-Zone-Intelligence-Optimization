"""
Script to extract and format the full conversation transcript (all user queries and model responses)
into a clean, publication-quality Markdown file.
"""

import json
import re
from pathlib import Path


TRANSCRIPT_PATH = Path(
    r"C:\Users\Akshat\.gemini\antigravity-ide\brain\b30e5e23-a616-4da8-9578-f18aa594295f\.system_generated\logs\transcript_full.jsonl"
)
WORKSPACE_OUTPUT = Path(r"C:\Coding\Project Black Knight\Project_Black_Knight_Conversation_Transcript.md")
ARTIFACT_OUTPUT = Path(
    r"C:\Users\Akshat\.gemini\antigravity-ide\brain\b30e5e23-a616-4da8-9578-f18aa594295f\Project_Black_Knight_Conversation_Transcript.md"
)


def clean_user_text(text: str) -> str:
    m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    text = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", text, flags=re.DOTALL)
    return text.strip()


def export_transcript():
    if not TRANSCRIPT_PATH.exists():
        raise FileNotFoundError(f"Transcript not found at {TRANSCRIPT_PATH}")

    turns = []
    current_turn = {"user": "", "responses": []}

    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            stype = row.get("type")
            source = row.get("source")
            content = row.get("content") or ""

            if stype == "USER_INPUT" and source == "USER_EXPLICIT":
                if current_turn["user"] or current_turn["responses"]:
                    turns.append(current_turn)
                current_turn = {"user": clean_user_text(content), "responses": []}
            elif stype == "PLANNER_RESPONSE" and source == "MODEL":
                if content.strip():
                    current_turn["responses"].append(content.strip())

    if current_turn["user"] or current_turn["responses"]:
        turns.append(current_turn)

    md = []
    md.append("# Project Black Knight — Complete Conversation Transcript\n")
    md.append("**Conversation ID:** `b30e5e23-a616-4da8-9578-f18aa594295f`  ")
    md.append("**Repository:** `c:/Coding/Project Black Knight`  ")
    md.append("**Topics Covered:** Phases 1–5 (Audit, Query Parser, Metadata Filtering, Hybrid Retrieval, Final Regression)  ")
    md.append("**Total Interaction Turns:** " + str(len(turns)) + "\n")
    md.append("---\n")

    phase_titles = [
        "Phase 1: Repository Audit & Evaluation Setup",
        "Phase 2: Query Parser Evaluation",
        "Phase 3: Metadata Filtering & Data Correctness",
        "Phase 4: Hybrid Retrieval & Recommendation Evaluation",
        "Phase 5: Final Regression & System Evaluation",
        "Export Conversation Transcript Request",
    ]

    for idx, turn in enumerate(turns, start=1):
        phase_label = phase_titles[idx - 1] if idx - 1 < len(phase_titles) else f"Turn {idx}"
        md.append(f"## Turn {idx}: {phase_label}\n")

        # User section
        md.append("### 👤 User Request\n")
        md.append(turn["user"])
        md.append("\n\n---\n")

        # Model section
        md.append("### 🤖 Assistant Responses\n")
        responses = turn["responses"]
        if not responses:
            md.append("*(In progress / pending)*\n")
        elif len(responses) == 1:
            md.append(responses[0])
            md.append("\n")
        else:
            # When there are intermediate execution notifications and a final comprehensive report
            main_report = responses[-1]
            status_updates = responses[:-1]

            if status_updates:
                md.append("<details>\n<summary><b>Click to expand intermediate execution updates (" + str(len(status_updates)) + " status updates)</b></summary>\n\n")
                for s_idx, update in enumerate(status_updates, 1):
                    md.append(f"**Update {s_idx}:** {update}\n\n")
                md.append("</details>\n\n")

            md.append("#### Main Response & Report\n")
            md.append(main_report)
            md.append("\n")

        md.append("\n---\n\n")

    content = "\n".join(md)

    WORKSPACE_OUTPUT.write_text(content, encoding="utf-8")
    print(f"Saved transcript to workspace at: {WORKSPACE_OUTPUT} ({len(content)} characters)")

    ARTIFACT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_OUTPUT.write_text(content, encoding="utf-8")
    print(f"Saved transcript to artifacts at: {ARTIFACT_OUTPUT}")


if __name__ == "__main__":
    export_transcript()
