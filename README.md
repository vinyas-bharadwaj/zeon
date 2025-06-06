# Zeon 🧬

**Zeon** is a Python-based CLI tool that instantly scaffolds a complete FastAPI project with built-in authentication, user management, JWT handling, and environment-based configuration — all with a single command.

---

## ✨ Features

- 🚀 FastAPI project scaffolding
- 🧠 SQLite + SQLAlchemy ORM setup
- 🔐 JWT-based authentication
- 🧰 Utility functions for password hashing
- 📁 Organized folder structure (routers, models, schemas)
- ✅ Includes `.env`, `.gitignore`, and `requirements.txt`

---

## 📦 Installation

To install Zeon from [PyPI](https://pypi.org/project/zeon/):

```bash
pip install zeon
```

## ⚡Usage

To create a new FastAPI project, run:

```bash
zeon myproject
```

This will generate the following structure inside `myproject/`:

```pgsql
myproject/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── utils.py
│   ├── oauth2.py
│   └── routers/
│       └── auth.py
├── .env
├── .gitignore
├── requirements.txt
```