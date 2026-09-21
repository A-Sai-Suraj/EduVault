"""SQLite persistence and CRUD helpers for Academic Resource Hub."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .data_loader import is_theory_subject

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "academic_hub.db"
DEFAULT_JSON_PATH = BASE_DIR / "Resources.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS semesters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semester_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semester_id INTEGER NOT NULL REFERENCES semesters(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    is_theory INTEGER NOT NULL DEFAULT 1 CHECK (is_theory IN (0, 1)),
    UNIQUE (semester_id, code)
);
CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    unit TEXT NOT NULL DEFAULT '',
    type TEXT NOT NULL DEFAULT '',
    file_name TEXT NOT NULL,
    url TEXT NOT NULL,
    source_regulation TEXT NOT NULL DEFAULT 'R25',
    UNIQUE (subject_id, file_name, url)
);
"""


def _connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: str | Path = DEFAULT_DB_PATH, json_path: str | Path = DEFAULT_JSON_PATH) -> None:
    """Create the schema and import JSON only when the database is first created."""
    db_file = Path(db_path)
    first_run = not db_file.exists()
    with _connect(db_file) as connection:
        connection.executescript(SCHEMA)
        if first_run:
            migrate_json_to_db(connection, json_path)


def migrate_json_to_db(
    connection: sqlite3.Connection | None = None,
    json_path: str | Path = DEFAULT_JSON_PATH,
) -> None:
    """Import the legacy JSON into an existing connection without duplicates."""
    owns_connection = connection is None
    if owns_connection:
        connection = _connect(DEFAULT_DB_PATH)
    assert connection is not None
    try:
        with open(json_path, "r", encoding="utf-8") as source:
            payload = json.load(source)
        for semester_key, semester in payload.get("semesters", {}).items():
            connection.execute(
                "INSERT OR IGNORE INTO semesters (semester_key, name) VALUES (?, ?)",
                (semester_key, semester.get("name", semester_key)),
            )
            semester_row = connection.execute(
                "SELECT id FROM semesters WHERE semester_key = ?", (semester_key,)
            ).fetchone()
            for subject in semester.get("subjects", []):
                connection.execute(
                    """INSERT OR IGNORE INTO subjects
                       (semester_id, code, name, is_theory) VALUES (?, ?, ?, ?)""",
                    (
                        semester_row["id"],
                        subject.get("code", ""),
                        subject.get("name", ""),
                        int(is_theory_subject(subject)),
                    ),
                )
                subject_row = connection.execute(
                    "SELECT id FROM subjects WHERE semester_id = ? AND code = ?",
                    (semester_row["id"], subject.get("code", "")),
                ).fetchone()
                for resource in subject.get("resources", []):
                    connection.execute(
                        """INSERT OR IGNORE INTO resources
                           (subject_id, unit, type, file_name, url, source_regulation)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            subject_row["id"],
                            resource.get("unit", ""),
                            resource.get("type", ""),
                            resource.get("file", ""),
                            resource.get("url", ""),
                            resource.get("source_regulation", "R25"),
                        ),
                    )
        if owns_connection:
            connection.commit()
    finally:
        if owns_connection:
            connection.close()


def _rows(connection: sqlite3.Connection, query: str, params: tuple = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(query, params).fetchall()]


def get_semesters(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        return _rows(connection, "SELECT * FROM semesters ORDER BY id")


def get_subjects(semester_id: int | None = None, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    query = "SELECT subjects.*, semesters.name AS semester_name, semesters.semester_key FROM subjects JOIN semesters ON semesters.id = subjects.semester_id"
    params: tuple = ()
    if semester_id is not None:
        query += " WHERE semester_id = ?"
        params = (semester_id,)
    query += " ORDER BY subjects.id"
    with _connect(db_path) as connection:
        return _rows(connection, query, params)


def get_theory_subjects(semester_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        return _rows(connection, "SELECT subjects.*, semesters.name AS semester_name, semesters.semester_key FROM subjects JOIN semesters ON semesters.id = subjects.semester_id WHERE semester_id = ? AND is_theory = 1 ORDER BY subjects.id", (semester_id,))


def get_resources(subject_id: int | None = None, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    query = "SELECT resources.*, subjects.code AS subject_code, subjects.name AS subject_name, subjects.is_theory, semesters.name AS semester_name, semesters.semester_key FROM resources JOIN subjects ON subjects.id = resources.subject_id JOIN semesters ON semesters.id = subjects.semester_id"
    params: tuple = ()
    if subject_id is not None:
        query += " WHERE subject_id = ?"
        params = (subject_id,)
    query += " ORDER BY resources.id"
    with _connect(db_path) as connection:
        return _rows(connection, query, params)


def get_app_data(db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, Any]:
    """Return the legacy-shaped model so the existing student UI stays stable."""
    data = {"semesters": {}}
    with _connect(db_path) as connection:
        semesters = _rows(connection, "SELECT * FROM semesters ORDER BY id")
        for semester in semesters:
            subjects = _rows(connection, "SELECT * FROM subjects WHERE semester_id = ? ORDER BY id", (semester["id"],))
            for subject in subjects:
                subject["resources"] = [
                    {"id": resource["id"], "unit": resource["unit"], "type": resource["type"], "file": resource["file_name"], "url": resource["url"], "source_regulation": resource["source_regulation"]}
                    for resource in _rows(connection, "SELECT * FROM resources WHERE subject_id = ? ORDER BY id", (subject["id"],))
                ]
            data["semesters"][semester["semester_key"]] = {"name": semester["name"], "subjects": subjects}
    return data


def add_semester(semester_key: str, name: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as connection:
        connection.execute("INSERT INTO semesters (semester_key, name) VALUES (?, ?)", (semester_key.strip(), name.strip()))


def update_semester(semester_id: int, name: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as connection:
        connection.execute("UPDATE semesters SET name = ? WHERE id = ?", (name.strip(), semester_id))


def delete_semester(semester_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as connection:
        if connection.execute("SELECT 1 FROM subjects WHERE semester_id = ? LIMIT 1", (semester_id,)).fetchone():
            raise ValueError("Delete the semester's subjects and resources first.")
        connection.execute("DELETE FROM semesters WHERE id = ?", (semester_id,))


def add_subject(semester_id: int, code: str, name: str, is_theory: bool, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as connection:
        connection.execute("INSERT INTO subjects (semester_id, code, name, is_theory) VALUES (?, ?, ?, ?)", (semester_id, code.strip(), name.strip(), int(is_theory)))


def update_subject(subject_id: int, semester_id: int, code: str, name: str, is_theory: bool, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as connection:
        connection.execute("UPDATE subjects SET semester_id = ?, code = ?, name = ?, is_theory = ? WHERE id = ?", (semester_id, code.strip(), name.strip(), int(is_theory), subject_id))


def delete_subject(subject_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as connection:
        connection.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))


def add_resource(subject_id: int, unit: str, resource_type: str, file_name: str, url: str, source_regulation: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as connection:
        connection.execute("INSERT INTO resources (subject_id, unit, type, file_name, url, source_regulation) VALUES (?, ?, ?, ?, ?, ?)", (subject_id, unit.strip(), resource_type.strip(), file_name.strip(), url.strip(), source_regulation.strip() or "R25"))


def update_resource(resource_id: int, unit: str, resource_type: str, file_name: str, url: str, source_regulation: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as connection:
        connection.execute("UPDATE resources SET unit = ?, type = ?, file_name = ?, url = ?, source_regulation = ? WHERE id = ?", (unit.strip(), resource_type.strip(), file_name.strip(), url.strip(), source_regulation.strip() or "R25", resource_id))


def delete_resource(resource_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as connection:
        connection.execute("DELETE FROM resources WHERE id = ?", (resource_id,))


def search_resources(query: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    pattern = f"%{query.strip().lower()}%"
    with _connect(db_path) as connection:
        return _rows(connection, "SELECT resources.*, subjects.code AS subject_code, subjects.name AS subject_name, subjects.is_theory, semesters.name AS semester_name, semesters.semester_key FROM resources JOIN subjects ON subjects.id = resources.subject_id JOIN semesters ON semesters.id = subjects.semester_id WHERE subjects.is_theory = 1 AND (LOWER(subjects.name) LIKE ? OR LOWER(subjects.code) LIKE ? OR LOWER(resources.file_name) LIKE ?) ORDER BY resources.id", (pattern, pattern, pattern))


def database_stats(db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, int]:
    with _connect(db_path) as connection:
        return {
            "semesters": connection.execute("SELECT COUNT(*) FROM semesters").fetchone()[0],
            "theory_subjects": connection.execute("SELECT COUNT(*) FROM subjects WHERE is_theory = 1").fetchone()[0],
            "resources": connection.execute("SELECT COUNT(*) FROM resources JOIN subjects ON subjects.id = resources.subject_id WHERE subjects.is_theory = 1").fetchone()[0],
        }
