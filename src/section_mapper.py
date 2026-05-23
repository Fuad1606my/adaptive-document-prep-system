import re
from typing import Dict


SECTION_TITLES = {
    1: "Identity, Background, and Public Status",
    2: "Powers, Abilities, and Documented Limits",
    3: "Origin and Key Historical Events",
    4: "Equipment, Gear, and Specialized Technology",
    5: "Operational Tactics and Combat Doctrine",
    6: "Allies, Networks, and Known Affiliations",
    7: "Adversaries and Documented Threats",
    8: "Known Bases, Safehouses, and Operational Territory",
    9: "Case Files: Documented Engagements and Incidents",
    10: "Glossary, Codenames, and Reference Tables",
}


def split_sections(full_text: str) -> Dict[int, str]:
    """
    Split SLATEFALL dossier text into Section 1-10.
    Uses the PDF's section headings.
    """
    pattern = r"Section\s+(\d+)\.\s+([^\n]+)"
    matches = list(re.finditer(pattern, full_text))

    if not matches:
        raise ValueError("No section headings found. Check PDF text format.")

    sections: Dict[int, str] = {}

    for index, match in enumerate(matches):
        section_id = int(match.group(1))

        if section_id < 1 or section_id > 10:
            continue

        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(full_text)

        section_text = full_text[start:end].strip()
        sections[section_id] = section_text

    missing = [section_id for section_id in range(1, 11) if section_id not in sections]
    if missing:
        raise ValueError(f"Missing sections after parsing: {missing}")

    return sections


def get_section_summary(section_id: int, section_text: str, max_chars: int = 250) -> dict:
    """
    Create a small summary object for CLI/API output.
    """
    title = SECTION_TITLES.get(section_id, f"Section {section_id}")
    cleaned = " ".join(section_text.split())
    preview = cleaned[:max_chars] + "..." if len(cleaned) > max_chars else cleaned

    return {
        "section_id": section_id,
        "title": title,
        "characters": len(section_text),
        "preview": preview,
    }