# Zeon 🧬

**Zeon** is a powerful Python-based CLI tool that instantly scaffolds complete FastAPI projects with customizable database backends, authentication methods, and additional features — all with a single command.

---

## ✨ Features

- 🚀 **FastAPI project scaffolding** with interactive configuration
- 🗄️ **Multiple database options**: SQLite, PostgreSQL, MongoDB, Supabase, Firebase
- 🔐 **Flexible authentication**: JWT, Supabase Auth, Firebase Auth, or none
- 🐳 **Docker support** with docker-compose configuration
- � **Testing setup** with pytest and test files
- ⚙️ **Database migrations** with Alembic
- 🌐 **CORS middleware** for cross-origin requests
- 🛡️ **Rate limiting** for API protection
- 📁 **Organized project structure** with best practices
- ✅ **Environment configuration** with `.env` files

---

## 📦 Installation

To install Zeon from [PyPI](https://pypi.org/project/zeon/):

```bash
pip install zeon
```

## ⚡ Usage

### Interactive Setup (Recommended)

Create a new FastAPI project with interactive configuration:

```bash
zeon init myproject
```

This will prompt you to choose:

- Database backend (SQLite, PostgreSQL, MongoDB, Supabase, Firebase)
- Authentication method (JWT, Supabase Auth, Firebase Auth, or none)
- Additional features (Alembic, Docker, Testing, CORS, Rate limiting)

### Quick Setup

Skip interactive prompts and use defaults:

```bash
zeon init myproject --quick
```

### Custom Setup

Create a project with specific configuration:

```bash
zeon create myproject --db postgresql --auth jwt --features alembic,docker,testing
```

### View Preset Configurations

See available preset configurations:

```bash
zeon presets
```

## 🎯 Available Configurations

### Database Options

| Option | Description | Use Case |
|--------|-------------|----------|
| `sqlite` | File-based database | Development, small apps |
| `postgresql` | Robust relational database | Production apps |
| `mongodb` | NoSQL document database | Flexible schemas |
| `supabase` | Backend-as-a-Service | Full-stack apps |
| `firebase` | Google's cloud database | Serverless apps |

### Authentication Methods

| Option | Description | Compatible With |
|--------|-------------|-----------------|
| `jwt` | JSON Web Tokens | All databases |
| `supabase` | Supabase authentication | Supabase database |
| `firebase` | Firebase authentication | Firebase database |
| `none` | No authentication | All databases |

### Additional Features

| Feature | Description |
|---------|-------------|
| `alembic` | Database migration tool |
| `docker` | Containerization with docker-compose |
| `testing` | pytest setup with test files |
| `cors` | Cross-Origin Resource Sharing |
| `rate_limiting` | API rate limiting |

## 📋 Project Structure

Depending on your configuration, Zeon generates:

```text
myproject/
├── app/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database configuration
│   ├── models.py            # Data models
│   ├── schemas.py           # Pydantic schemas
│   ├── utils.py             # Utility functions
│   ├── oauth2.py            # Authentication logic
│   └── routers/
│       └── auth.py          # Authentication routes
├── tests/                   # Test files (if testing enabled)
├── alembic/                 # Migration files (if Alembic enabled)
├── Dockerfile               # Docker config (if Docker enabled)
├── docker-compose.yml       # Docker compose (if Docker enabled)
├── .env                     # Environment variables
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
└── alembic.ini             # Alembic config (if enabled)
```

## 🚀 Preset Examples

### Basic SQLite Project

```bash
zeon create myproject --db sqlite --auth jwt
```

### Production PostgreSQL Setup

```bash
zeon create myproject --db postgresql --auth jwt --features alembic,docker,testing
```

### MongoDB API with CORS

```bash
zeon create myproject --db mongodb --auth jwt --features testing,cors
```

### Supabase Full-Stack Backend

```bash
zeon create myproject --db supabase --auth supabase --features cors,rate_limiting
```

### Complete Microservice

```bash
zeon create myproject --db postgresql --auth jwt --features alembic,docker,testing,cors,rate_limiting
```

## 📚 Additional Commands

### Manage Routers

Add new routers to your existing project:

```bash
zeon routers posts myproject
```

### Add Packages

Install and add packages to your project:

```bash
zeon add fastapi-limiter myproject
```

### Database Migrations (with Alembic)

Create migrations:

```bash
zeon makemigrations "Add user table" myproject
```

Apply migrations:

```bash
zeon migrate myproject
```

## 🔧 Configuration Examples

### Environment Variables

The generated `.env` file will contain different variables based on your database choice:

**SQLite:**

```bash
DATABASE_URL=sqlite:///./sql_app.db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**PostgreSQL:**

```bash
DATABASE_URL=postgresql://user:password@localhost/dbname
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Supabase:**

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🚀 Getting Started

1. **Install Zeon**

   ```bash
   pip install zeon
   ```

2. **Create your project**

   ```bash
   zeon init myproject
   ```

3. **Navigate to your project**

   ```bash
   cd myproject
   ```

4. **Update environment variables**
   Edit the `.env` file with your database credentials

5. **Start development**

   ```bash
   # Activate virtual environment
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   
   # Start the server
   uvicorn app.main:app --reload
   ```

6. **Visit your API**
   Open <http://localhost:8000> in your browser

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.