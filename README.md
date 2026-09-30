# 📚 EduVault

> A student-friendly academic resource hub for quickly finding semester-wise notes and study materials.

EduVault is a centralized academic resource platform designed to make study materials easier to find and access.

Instead of searching through scattered links and messages, students can browse resources semester-wise and subject-wise from a single platform.

---

## ✨ Features

- 📚 Semester-wise resource organization
- 📖 Subject-wise study materials
- 🔍 Search resources quickly
- 📂 Unit-wise resource organization
- 🔗 Easy access to study materials
- 🔐 Admin panel for resource management
- 📱 Student-friendly interface
- 💾 SQLite-based data management

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| 🐍 Python | Application logic |
| 🎈 Streamlit | Web application framework |
| 🗄️ SQLite | Data storage |
| 📁 Google Drive | Resource storage |
| 🔧 Git & GitHub | Version control |
| ☁️ Render | Deployment |
| 🐳 Docker | Optional containerized deployment |

---

## 🏗️ How It Works
                    ┌───────────────┐
                    │    STUDENT    │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    EDUVAULT   │
                    │   Streamlit   │
                    └───────┬───────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
             ┌────────┐           ┌────────┐
             │ Search │           │ Browse │
             └───┬────┘           └───┬────┘
                 │                    │
                 └─────────┬──────────┘
                           ▼
                     ┌───────────┐
                     │ Semester  │
                     └─────┬─────┘
                           ▼
                     ┌───────────┐
                     │  Subject  │
                     └─────┬─────┘
                           ▼
                     ┌───────────┐
                     │ Resources │
                     └─────┬─────┘
                           ▼
                     ┌───────────┐
                     │   Access  │
                     └───────────┘
