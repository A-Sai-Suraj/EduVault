"""
utils/data_loader.py
--------------------
Pure data-processing helpers for the Academic Resource Hub.
No Streamlit imports — keeps concerns separated.
"""

import json
import re
import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Excluded keywords for lab / practical / workshop subjects
# Add more keywords here to automatically exclude future practical courses.
# ---------------------------------------------------------------------------
LAB_KEYWORDS = [
    "lab",
    "laboratory",
    "workshop",
    "practical",
]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_resources(path: str = "Resources.json") -> dict:
    """
    Load and return the parsed JSON data.
    Returns None (instead of raising) so the caller can show a friendly error.
    """
    try:
        p = Path(path)
        if not p.exists():
            return None, f"File not found: {path}"
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {path}: {e}"
    except Exception as e:
        return None, f"Could not load resources: {e}"


# ---------------------------------------------------------------------------
# Semester helpers
# ---------------------------------------------------------------------------

def get_semesters(data: dict) -> list[dict]:
    """
    Return an ordered list of dicts: [{"key": "semester_1", "name": "Semester 1"}, ...]
    Order follows the natural key sort (semester_1 < semester_2 < ...).
    """
    semesters = data.get("semesters", {})
    result = []
    for key in sorted(semesters.keys()):
        sem = semesters[key]
        result.append({"key": key, "name": sem.get("name", key)})
    return result


# ---------------------------------------------------------------------------
# Subject filtering
# ---------------------------------------------------------------------------

def is_theory_subject(subject: dict) -> bool:
    """
    Return True when the subject is a theory course.
    Excludes subjects whose name contains any of LAB_KEYWORDS (case-insensitive).
    Matching is done on whole-word boundaries where possible to avoid
    false positives (e.g. 'Elaboration' would not be excluded).
    """
    if "is_theory" in subject:
        return bool(subject["is_theory"])

    name = subject.get("name", "").lower()
    for kw in LAB_KEYWORDS:
        # Use word-boundary matching for short keywords like "lab" to avoid
        # accidentally matching "elaboration", "collaborate", etc.
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, name):
            return False
    return True


def get_theory_subjects(semester_data: dict) -> list[dict]:
    """
    Return only theory subjects from the given semester data dict.
    """
    subjects = semester_data.get("subjects", [])
    return [s for s in subjects if is_theory_subject(s)]


# ---------------------------------------------------------------------------
# Resource filtering
# ---------------------------------------------------------------------------

def is_r25_resource(resource: dict) -> bool:
    """
    Return True if the resource is a valid R25 resource.
    A resource is R25 unless it explicitly declares source_regulation == "R22".
    Default assumption: R25.
    """
    return resource.get("source_regulation", "R25") != "R22"


def get_subject_resources(subject: dict) -> list[dict]:
    """
    Return all resources for a subject, including R22 source material.
    """
    return subject.get("resources", [])


# ---------------------------------------------------------------------------
# Google Drive URL helpers
# ---------------------------------------------------------------------------

# Patterns that cover the most common Drive URL shapes:
#   /file/d/<ID>/view
#   /open?id=<ID>
#   /uc?id=<ID>&export=download
_DRIVE_ID_PATTERNS = [
    re.compile(r"/file/d/([A-Za-z0-9_-]+)"),
    re.compile(r"[?&]id=([A-Za-z0-9_-]+)"),
]


def extract_drive_id(url: str) -> str | None:
    """
    Extract the Google Drive file ID from a Drive URL.
    Returns None if no ID can be found.
    """
    if not url:
        return None
    for pattern in _DRIVE_ID_PATTERNS:
        m = pattern.search(url)
        if m:
            return m.group(1)
    return None


def make_download_url(url: str) -> str | None:
    """
    Convert a Google Drive view URL into a direct-download URL.
    Returns None if the URL is not a recognised Drive URL.
    """
    file_id = extract_drive_id(url)
    if file_id:
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return None


def is_drive_url(url: str) -> bool:
    """Return True if the URL looks like a Google Drive link."""
    return bool(url and "drive.google.com" in url)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search_subjects(data: dict, query: str, semester_key: str | None = None) -> list[dict]:
    """
    Search theory subjects by name (case-insensitive).
    Returns a list of dicts:
        {"semester_name": ..., "subject": ..., "matching_resources": [...]}

    If semester_key is given, search is limited to that semester.
    Resources within each subject include both R25 and R22 source material.
    """
    query = query.strip().lower()
    if not query:
        return []

    semesters = data.get("semesters", {})
    keys_to_search = (
        [semester_key] if semester_key and semester_key in semesters
        else sorted(semesters.keys())
    )

    results = []
    for key in keys_to_search:
        sem = semesters[key]
        sem_name = sem.get("name", key)
        for subject in get_theory_subjects(sem):
            subject_name = subject.get("name", "").lower()
            resources = get_subject_resources(subject)

            subject_matches = query in subject_name

            # Also search within resource file names
            matching_resources = [
                r for r in resources
                if query in r.get("file", "").lower()
            ]

            if subject_matches or matching_resources:
                results.append({
                    "semester_key": key,
                    "semester_name": sem_name,
                    "subject": subject,
                    "subject_matches": subject_matches,
                    "matching_resources": matching_resources if not subject_matches else resources,
                })

    return results


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def compute_stats(data: dict) -> dict:
    """
    Compute summary statistics from the JSON.
    Counts only theory subjects and all resources stored for them.
    """
    semesters = data.get("semesters", {})
    num_semesters = len(semesters)
    num_theory_subjects = 0
    num_resources = 0

    for sem in semesters.values():
        theory_subs = get_theory_subjects(sem)
        num_theory_subjects += len(theory_subs)
        for sub in theory_subs:
            num_resources += len(get_subject_resources(sub))

    return {
        "semesters": num_semesters,
        "theory_subjects": num_theory_subjects,
        "resources": num_resources,
    }
