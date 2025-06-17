from pathlib import Path    
import files
import typer
import textwrap
import subprocess
import sys
from config_manager import (
    get_project_configuration, 
    get_database_config, 
    get_auth_config,
    generate_env_content,
    generate_requirements,
    DatabaseChoice,
    AuthChoice,
    FeatureChoice
)
from file_generators import CustomizedFileGenerator, AdditionalTemplates

app = typer.Typer()


def create_structure(project_name: str, interactive: bool = True):
    """Create project structure with customizable options"""
    
    # Get project configuration
    config = get_project_configuration(project_name, interactive)
    
    base_path = Path(project_name)
    venv_path = base_path / 'venv'
    app_path = base_path / "app"
    routers_path = app_path / "routers"
    
    # Create directories
    app_path.mkdir(parents=True, exist_ok=True)
    routers_path.mkdir(parents=True, exist_ok=True)
        
    if sys.platform == 'win32':
        pip_path = venv_path / 'Scripts' / 'pip'
    else:
        pip_path = venv_path / 'bin' / 'pip'

    # Get configuration-based content
    db_config = get_database_config(config.database)
    auth_config = get_auth_config(config.auth)
    file_generator = CustomizedFileGenerator(config)

    # Create base files
    (base_path / ".gitignore").write_text(files.gitignore_content)
    (base_path / ".env").write_text(generate_env_content(config))
    (base_path / "requirements.txt").write_text(generate_requirements(config))

    # Create app files
    (app_path / "__init__.py").touch()
    (app_path / "main.py").write_text(file_generator.generate_main_py())
    
    # Database configuration
    (app_path / "database.py").write_text(db_config["database_py"])
    
    # Models (use custom models for NoSQL databases)
    if config.database in [DatabaseChoice.MONGODB, DatabaseChoice.FIREBASE]:
        if "models_py" in db_config:
            (app_path / "models.py").write_text(db_config["models_py"])
        else:
            (app_path / "models.py").write_text(files.models_py_content)
    else:
        (app_path / "models.py").write_text(files.models_py_content)
    
    # Schemas
    (app_path / "schemas.py").write_text(files.schemas_py_content)
    
    # Utils (only for databases that need password hashing)
    if config.auth == AuthChoice.JWT and config.database not in [DatabaseChoice.MONGODB, DatabaseChoice.FIREBASE]:
        (app_path / "utils.py").write_text(files.utils_py_content)
    elif config.database in [DatabaseChoice.MONGODB, DatabaseChoice.FIREBASE]:
        (app_path / "utils.py").write_text(files.utils_py_content)
    else:
        (app_path / "utils.py").touch()
    
    # Auth configuration
    if config.auth != AuthChoice.NONE:
        (app_path / "oauth2.py").write_text(auth_config.get("oauth2_py", ""))
        (routers_path / "__init__.py").touch()
        (routers_path / "auth.py").write_text(file_generator.generate_auth_router())
    else:
        (routers_path / "__init__.py").touch()

    # Handle additional features
    handle_additional_features(config, base_path)

    # Create virtual environment
    typer.echo("🔧 Creating virtual environment...")
    subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)
    
    # Setup alembic if selected
    if FeatureChoice.ALEMBIC in config.features:
        subprocess.run([str(pip_path), "install", "alembic"], check=True)
        alembic_init(base_path, pip_path, config)

    # Install dependencies
    typer.echo("📦 Installing dependencies in virtual environment...")
    subprocess.run([str(pip_path), "install", "-r", str(base_path / 'requirements.txt')], check=True)

    # Show completion message with instructions
    show_completion_message(project_name, config)


def handle_additional_features(config, base_path):
    """Handle additional features setup"""
    
    # Docker setup
    if FeatureChoice.DOCKER in config.features:
        docker_files = AdditionalTemplates.get_docker_files()
        for filename, content in docker_files.items():
            file_path = base_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
    
    # Testing setup
    if FeatureChoice.TESTING in config.features:
        test_files = AdditionalTemplates.get_testing_files()
        for filename, content in test_files.items():
            file_path = base_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)


def show_completion_message(project_name: str, config):
    """Show completion message with next steps"""
    typer.echo(f"\n🎉 Project {project_name} initialized successfully!")
    typer.echo("=" * 50)
    typer.echo(f"📊 Configuration:")
    typer.echo(f"   Database: {config.database.value}")
    typer.echo(f"   Authentication: {config.auth.value}")
    if config.features:
        typer.echo(f"   Features: {', '.join([f.value for f in config.features])}")
    
    typer.echo(f"\n🚀 Next steps:")
    typer.echo(f"   1. cd {project_name}")
    typer.echo(f"   2. Update .env file with your database credentials")
    
    if config.database == DatabaseChoice.POSTGRESQL:
        typer.echo(f"   3. Make sure PostgreSQL is running")
    elif config.database == DatabaseChoice.MONGODB:
        typer.echo(f"   3. Make sure MongoDB is running")
    elif config.database == DatabaseChoice.SUPABASE:
        typer.echo(f"   3. Update .env with your Supabase credentials")
    elif config.database == DatabaseChoice.FIREBASE:
        typer.echo(f"   3. Add your Firebase service account JSON file")
    
    if FeatureChoice.ALEMBIC in config.features:
        typer.echo(f"   4. Run: zeon makemigrations \"Initial migration\"")
        typer.echo(f"   5. Run: zeon migrate")
        typer.echo(f"   6. Start development: uvicorn app.main:app --reload")
    else:
        typer.echo(f"   4. Start development: uvicorn app.main:app --reload")
    
    if FeatureChoice.DOCKER in config.features:
        typer.echo(f"\n🐳 Docker commands:")
        typer.echo(f"   Build: docker-compose build")
        typer.echo(f"   Run: docker-compose up")
    
    if FeatureChoice.TESTING in config.features:
        typer.echo(f"\n🧪 Testing:")
        typer.echo(f"   Run tests: pytest")


def alembic_init(base_path, pip_path, config):
    """Initialize Alembic with proper configuration"""
    alembic_dir = base_path / "alembic"
    alembic_ini = base_path / "alembic.ini"

    if not alembic_dir.exists():
        typer.echo("⚙️  Initializing Alembic...")
        subprocess.run([str(pip_path.parent / "alembic"), "init", "alembic"], cwd=base_path, check=True)

        # Modify alembic.ini based on database choice
        ini_text = alembic_ini.read_text()
        
        if config.database == DatabaseChoice.SQLITE:
            ini_text = ini_text.replace(
                "sqlalchemy.url = driver://user:pass@localhost/dbname",
                "sqlalchemy.url = sqlite:///./sql_app.db"
            )
        elif config.database == DatabaseChoice.POSTGRESQL:
            ini_text = ini_text.replace(
                "sqlalchemy.url = driver://user:pass@localhost/dbname",
                "sqlalchemy.url = postgresql://user:password@localhost/dbname"
            )
        elif config.database == DatabaseChoice.SUPABASE:
            ini_text = ini_text.replace(
                "sqlalchemy.url = driver://user:pass@localhost/dbname",
                "sqlalchemy.url = postgresql://postgres:password@db.your-project.supabase.co:5432/postgres"
            )
        
        alembic_ini.write_text(ini_text)

        # Modify env.py to import Base from your app
        env_path = alembic_dir / "env.py"
        env_text = env_path.read_text()

        insert_import = "from app.database import Base"
        insert_metadata = "target_metadata = Base.metadata"

        env_text = insert_import + "\n" + env_text
        env_text = env_text.replace("target_metadata = None", insert_metadata)
        env_path.write_text(env_text)

        typer.echo("✅ Alembic initialized and configured.")



@app.command()
def init(
    project_name: str,
    quick: bool = typer.Option(False, "--quick", "-q", help="Skip interactive configuration and use defaults")
):
    """Initializes the FastAPI project with customizable options"""
    create_structure(project_name, interactive=not quick)

@app.command()
def routers(router_name: str, project_name: str = "."):
    """
    Create a new router in app/routers/ and add it to app/main.py
    """
    base_path = Path(project_name)
    routers_path = base_path / "app" / "routers"
    main_path = base_path / "app" / "main.py"

    # Create routers dir if not exists
    routers_path.mkdir(parents=True, exist_ok=True)

    router_file = routers_path / f"{router_name}.py"
    if router_file.exists():
        typer.echo(f"Router '{router_name}' already exists!")
        raise typer.Exit()

    # Create router file using textwrap.dedent
    router_code = textwrap.dedent(f"""
        from fastapi import APIRouter

        router = APIRouter(prefix='/{router_name}', tags=['{router_name}'])

        @router.get("/")
        def read_root():
            return {{"message": "Hello from {router_name}!"}}
    """)
    router_file.write_text(router_code)

    # Add import and include_router to main.py
    if not main_path.exists():
        typer.echo("main.py not found. Make sure to initialize the project first.")
        raise typer.Exit()

    import_line = f"from .routers.{router_name} import router as {router_name}_router"
    include_line = f"\napp.include_router({router_name}_router)"

    main_lines = main_path.read_text().splitlines()

    # Check if import already exists
    if import_line in main_lines:
        typer.echo("Router already imported in app/main.py")
        return
    
    # Insert import after the last import statement
    insert_index = 0
    for i, line in enumerate(main_lines):
        if line.startswith("import") or line.startswith("from"):
            insert_index = i + 1

    # Insert the import line
    main_lines.insert(insert_index, import_line)
    
    # Put the app.include_router() statement in the bottom
    main_lines.append(include_line)

    # Write updated content
    main_path.write_text("\n".join(main_lines))

    typer.echo(f"Router '{router_name}' created and added to app/main.py")

@app.command()
def add(package_name: str, project_name: str = "."):
    """
    Install a Python package into the venv and add it to requirements.txt
    """
    base_path = Path(project_name)
    venv_path = base_path / "venv"
    requirements_path = base_path / "requirements.txt"

    if not venv_path.exists():
        typer.echo("❌ No virtual environment found. Please initialize the project first.")
        raise typer.Exit()

    # Determine pip path based on OS
    pip_path = venv_path / ("Scripts" if sys.platform == "win32" else "bin") / "pip"

    # Install the package
    typer.echo(f"📦 Installing {package_name}...")
    subprocess.run([str(pip_path), "install", package_name], check=True)

    # Freeze current state of installed packages into requirements.txt
    freeze_result = subprocess.run([str(pip_path), "freeze"], capture_output=True, text=True, check=True)
    requirements_path.write_text(freeze_result.stdout)

    typer.echo(f"✅ Package '{package_name}' installed and added to requirements.txt")


@app.command()
def makemigrations(message: str = "auto", project_name: str = "."):
    """
    Create Alembic migration script based on models
    """
    base_path = Path(project_name)
    venv_path = base_path / 'venv'
    alembic_path = venv_path / ("Scripts" if sys.platform == "win32" else "bin") / "alembic"
    alembic_ini = base_path / "alembic.ini"

    if not alembic_ini.exists():
        typer.echo("❌ Alembic not initialized. Run 'alembic init alembic' first.")
        raise typer.Exit()

    subprocess.run([str(alembic_path), "-c", str(alembic_ini), "revision", "--autogenerate", "-m", message], cwd=base_path, check=True)
    typer.echo("✅ Migration script created.")

@app.command()
def migrate(project_name: str = "."):
    """
    Apply migrations to the database
    """
    base_path = Path(project_name)
    venv_path = base_path / 'venv'
    alembic_path = venv_path / ("Scripts" if sys.platform == "win32" else "bin") / "alembic"
    alembic_ini = base_path / "alembic.ini"

    if not alembic_ini.exists():
        typer.echo("❌ Alembic not initialized. Run 'alembic init alembic' first.")
        raise typer.Exit()
    
    subprocess.run([str(alembic_path), "-c", str(alembic_ini), "upgrade", "head"], check=True)
    typer.echo("✅ Migrations applied to database.")

@app.command()
def create(
    project_name: str,
    database: DatabaseChoice = typer.Option(DatabaseChoice.SQLITE, "--db", help="Database to use"),
    auth: AuthChoice = typer.Option(AuthChoice.JWT, "--auth", help="Authentication method"),
    features: str = typer.Option("", "--features", help="Comma-separated list of features (alembic,docker,testing,cors,rate_limiting)"),
):
    """Create a FastAPI project with specified configuration (non-interactive)"""
    from config_manager import ProjectConfiguration, FeatureChoice
    
    # Parse features
    feature_list = []
    if features.strip():
        feature_names = [f.strip() for f in features.split(",")]
        feature_map = {
            "alembic": FeatureChoice.ALEMBIC,
            "docker": FeatureChoice.DOCKER,
            "testing": FeatureChoice.TESTING,
            "cors": FeatureChoice.CORS,
            "rate_limiting": FeatureChoice.RATE_LIMITING,
        }
        feature_list = [feature_map[name] for name in feature_names if name in feature_map]
    
    # Create configuration
    config = ProjectConfiguration()
    config.project_name = project_name
    config.database = database
    config.auth = auth
    config.features = feature_list
    
    # Show configuration
    typer.echo(f"🚀 Creating FastAPI project: {project_name}")
    typer.echo(f"   Database: {database.value}")
    typer.echo(f"   Authentication: {auth.value}")
    if feature_list:
        typer.echo(f"   Features: {', '.join([f.value for f in feature_list])}")
    
    # Create project with the configuration
    create_structure_with_config(project_name, config)


def create_structure_with_config(project_name: str, config):
    """Create project structure with provided configuration"""
    
    base_path = Path(project_name)
    venv_path = base_path / 'venv'
    app_path = base_path / "app"
    routers_path = app_path / "routers"
    
    # Create directories
    app_path.mkdir(parents=True, exist_ok=True)
    routers_path.mkdir(parents=True, exist_ok=True)
        
    if sys.platform == 'win32':
        pip_path = venv_path / 'Scripts' / 'pip'
    else:
        pip_path = venv_path / 'bin' / 'pip'

    # Get configuration-based content
    db_config = get_database_config(config.database)
    auth_config = get_auth_config(config.auth)
    file_generator = CustomizedFileGenerator(config)

    # Create base files
    (base_path / ".gitignore").write_text(files.gitignore_content)
    (base_path / ".env").write_text(generate_env_content(config))
    (base_path / "requirements.txt").write_text(generate_requirements(config))

    # Create app files
    (app_path / "__init__.py").touch()
    (app_path / "main.py").write_text(file_generator.generate_main_py())
    
    # Database configuration
    (app_path / "database.py").write_text(db_config["database_py"])
    
    # Models (use custom models for NoSQL databases)
    if config.database in [DatabaseChoice.MONGODB, DatabaseChoice.FIREBASE]:
        if "models_py" in db_config:
            (app_path / "models.py").write_text(db_config["models_py"])
        else:
            (app_path / "models.py").write_text(files.models_py_content)
    else:
        (app_path / "models.py").write_text(files.models_py_content)
    
    # Schemas
    (app_path / "schemas.py").write_text(files.schemas_py_content)
    
    # Utils (only for databases that need password hashing)
    if config.auth == AuthChoice.JWT and config.database not in [DatabaseChoice.MONGODB, DatabaseChoice.FIREBASE]:
        (app_path / "utils.py").write_text(files.utils_py_content)
    elif config.database in [DatabaseChoice.MONGODB, DatabaseChoice.FIREBASE]:
        (app_path / "utils.py").write_text(files.utils_py_content)
    else:
        (app_path / "utils.py").touch()
    
    # Auth configuration
    if config.auth != AuthChoice.NONE:
        (app_path / "oauth2.py").write_text(auth_config.get("oauth2_py", ""))
        (routers_path / "__init__.py").touch()
        (routers_path / "auth.py").write_text(file_generator.generate_auth_router())
    else:
        (routers_path / "__init__.py").touch()

    # Handle additional features
    handle_additional_features(config, base_path)

    # Create virtual environment
    typer.echo("🔧 Creating virtual environment...")
    subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)
    
    # Setup alembic if selected
    if FeatureChoice.ALEMBIC in config.features:
        subprocess.run([str(pip_path), "install", "alembic"], check=True)
        alembic_init(base_path, pip_path, config)

    # Install dependencies
    typer.echo("📦 Installing dependencies in virtual environment...")
    subprocess.run([str(pip_path), "install", "-r", str(base_path / 'requirements.txt')], check=True)

    # Show completion message with instructions
    show_completion_message(project_name, config)


@app.command()
def presets():
    """Show available preset configurations"""
    typer.echo("🎯 Available Preset Configurations:")
    typer.echo("=" * 50)
    
    presets = [
        {
            "name": "Basic SQLite",
            "command": "zeon create myproject --db sqlite --auth jwt",
            "description": "Simple SQLite setup with JWT authentication"
        },
        {
            "name": "PostgreSQL + Docker",
            "command": "zeon create myproject --db postgresql --auth jwt --features alembic,docker,testing",
            "description": "Production-ready setup with PostgreSQL, Docker, and testing"
        },
        {
            "name": "MongoDB API",
            "command": "zeon create myproject --db mongodb --auth jwt --features testing,cors",
            "description": "NoSQL API with MongoDB and CORS enabled"
        },
        {
            "name": "Supabase Backend",
            "command": "zeon create myproject --db supabase --auth supabase --features cors,rate_limiting",
            "description": "Full-stack ready with Supabase backend"
        },
        {
            "name": "Firebase API",
            "command": "zeon create myproject --db firebase --auth firebase --features testing,cors",
            "description": "Serverless API with Firebase backend"
        },
        {
            "name": "Microservice Ready",
            "command": "zeon create myproject --db postgresql --auth jwt --features alembic,docker,testing,cors,rate_limiting",
            "description": "Complete microservice setup with all features"
        }
    ]
    
    for preset in presets:
        typer.echo(f"\n📦 {preset['name']}")
        typer.echo(f"   {preset['description']}")
        typer.echo(f"   Command: {preset['command']}")
    
    typer.echo(f"\n💡 Usage Examples:")
    typer.echo(f"   Interactive setup: zeon init myproject")
    typer.echo(f"   Quick setup: zeon init myproject --quick")
    typer.echo(f"   Custom setup: zeon create myproject --db postgresql --auth jwt --features alembic,docker")


if __name__ == "__main__":
    app()