import typer
from typing import Dict, List, Any
from enum import Enum
from config_templates import DatabaseTemplates, AuthTemplates
import secrets


class DatabaseChoice(str, Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    SUPABASE = "supabase"
    FIREBASE = "firebase"


class AuthChoice(str, Enum):
    JWT = "jwt"
    SUPABASE = "supabase"
    FIREBASE = "firebase"
    NONE = "none"


class FeatureChoice(str, Enum):
    ALEMBIC = "alembic"
    DOCKER = "docker"
    TESTING = "testing"
    CORS = "cors"
    RATE_LIMITING = "rate_limiting"


class ProjectConfiguration:
    def __init__(self):
        self.database: DatabaseChoice = DatabaseChoice.SQLITE
        self.auth: AuthChoice = AuthChoice.JWT
        self.features: List[FeatureChoice] = []
        self.project_name: str = ""
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "database": self.database.value,
            "auth": self.auth.value,
            "features": [f.value for f in self.features],
            "project_name": self.project_name
        }


def prompt_database_choice() -> DatabaseChoice:
    """Prompt user to select database option"""
    typer.echo("\n🗄️  Select your database:")
    typer.echo("1. SQLite (Default - File-based, great for development)")
    typer.echo("2. PostgreSQL (Robust relational database)")
    typer.echo("3. MongoDB (NoSQL document database)")
    typer.echo("4. Supabase (Backend-as-a-Service with PostgreSQL)")
    typer.echo("5. Firebase Firestore (Google's NoSQL cloud database)")
    
    choice = typer.prompt("Enter your choice (1-5)", type=int, default=1)
    
    choices = {
        1: DatabaseChoice.SQLITE,
        2: DatabaseChoice.POSTGRESQL,
        3: DatabaseChoice.MONGODB,
        4: DatabaseChoice.SUPABASE,
        5: DatabaseChoice.FIREBASE
    }
    
    return choices.get(choice, DatabaseChoice.SQLITE)


def prompt_auth_choice(database: DatabaseChoice) -> AuthChoice:
    """Prompt user to select authentication method"""
    typer.echo("\n🔐 Select your authentication method:")
    
    if database == DatabaseChoice.SUPABASE:
        typer.echo("1. Supabase Auth (Recommended for Supabase)")
        typer.echo("2. JWT Authentication")
        typer.echo("3. No authentication")
        choice = typer.prompt("Enter your choice (1-3)", type=int, default=1)
        choices = {1: AuthChoice.SUPABASE, 2: AuthChoice.JWT, 3: AuthChoice.NONE}
    elif database == DatabaseChoice.FIREBASE:
        typer.echo("1. Firebase Auth (Recommended for Firebase)")
        typer.echo("2. JWT Authentication")
        typer.echo("3. No authentication")
        choice = typer.prompt("Enter your choice (1-3)", type=int, default=1)
        choices = {1: AuthChoice.FIREBASE, 2: AuthChoice.JWT, 3: AuthChoice.NONE}
    else:
        typer.echo("1. JWT Authentication (Default)")
        typer.echo("2. No authentication")
        choice = typer.prompt("Enter your choice (1-2)", type=int, default=1)
        choices = {1: AuthChoice.JWT, 2: AuthChoice.NONE}
    
    return choices.get(choice, AuthChoice.JWT)


def prompt_additional_features() -> List[FeatureChoice]:
    """Prompt user to select additional features"""
    typer.echo("\n✨ Select additional features (space-separated numbers, or press Enter for none):")
    typer.echo("1. Alembic (Database migrations)")
    typer.echo("2. Docker (Containerization)")
    typer.echo("3. Testing setup (pytest + test files)")
    typer.echo("4. CORS middleware")
    typer.echo("5. Rate limiting")
    
    choice_input = typer.prompt("Enter your choices", default="", show_default=False)
    
    if not choice_input.strip():
        return []
    
    try:
        choices = [int(x.strip()) for x in choice_input.split()]
    except ValueError:
        typer.echo("Invalid input. Skipping additional features.")
        return []
    
    feature_map = {
        1: FeatureChoice.ALEMBIC,
        2: FeatureChoice.DOCKER,
        3: FeatureChoice.TESTING,
        4: FeatureChoice.CORS,
        5: FeatureChoice.RATE_LIMITING
    }
    
    return [feature_map[choice] for choice in choices if choice in feature_map]


def get_project_configuration(project_name: str, interactive: bool = True) -> ProjectConfiguration:
    """Get project configuration from user or use defaults"""
    config = ProjectConfiguration()
    config.project_name = project_name
    
    if not interactive:
        return config
    
    typer.echo(f"\n🚀 Configuring your FastAPI project: {project_name}")
    typer.echo("=" * 50)
    
    config.database = prompt_database_choice()
    config.auth = prompt_auth_choice(config.database)
    config.features = prompt_additional_features()
    
    # Show configuration summary
    typer.echo("\n📋 Configuration Summary:")
    typer.echo(f"  Database: {config.database.value}")
    typer.echo(f"  Authentication: {config.auth.value}")
    typer.echo(f"  Additional features: {', '.join([f.value for f in config.features]) if config.features else 'None'}")
    
    if typer.confirm("\nProceed with this configuration?", default=True):
        return config
    else:
        typer.echo("Configuration cancelled.")
        raise typer.Exit(1)


def get_database_config(choice: DatabaseChoice) -> Dict[str, Any]:
    """Get database configuration based on choice"""
    templates = {
        DatabaseChoice.SQLITE: DatabaseTemplates.get_sqlite_config,
        DatabaseChoice.POSTGRESQL: DatabaseTemplates.get_postgresql_config,
        DatabaseChoice.MONGODB: DatabaseTemplates.get_mongodb_config,
        DatabaseChoice.SUPABASE: DatabaseTemplates.get_supabase_config,
        DatabaseChoice.FIREBASE: DatabaseTemplates.get_firebase_config,
    }
    
    return templates[choice]()


def get_auth_config(choice: AuthChoice) -> Dict[str, Any]:
    """Get authentication configuration based on choice"""
    if choice == AuthChoice.JWT:
        return AuthTemplates.get_jwt_auth()
    elif choice == AuthChoice.SUPABASE:
        return AuthTemplates.get_supabase_auth()
    elif choice == AuthChoice.FIREBASE:
        return AuthTemplates.get_supabase_auth()  # Similar pattern for Firebase
    else:
        return {"oauth2_py": "", "requirements": []}


def generate_env_content(config: ProjectConfiguration) -> str:
    """Generate .env file content based on configuration"""
    db_config = get_database_config(config.database)
    
    # Base environment variables
    secret_key = secrets.token_urlsafe(32)
    env_vars = {
        "SECRET_KEY": secret_key,
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30"
    }
    
    # Add database-specific environment variables
    if "env_vars" in db_config:
        env_vars.update(db_config["env_vars"])
    
    # Generate .env content
    env_content = ""
    for key, value in env_vars.items():
        env_content += f"{key}={value}\n"
    
    return env_content


def generate_requirements(config: ProjectConfiguration) -> str:
    """Generate requirements.txt content based on configuration"""
    base_requirements = [
        "annotated-types==0.7.0",
        "anyio==4.9.0",
        "certifi==2025.4.26",
        "click==8.2.1",
        "colorama==0.4.6",
        "dnspython==2.7.0",
        "email_validator==2.2.0",
        "fastapi==0.115.12",
        "fastapi-cli==0.0.7",
        "h11==0.16.0",
        "httpcore==1.0.9",
        "httptools==0.6.4",
        "httpx==0.28.1",
        "idna==3.10",
        "Jinja2==3.1.6",
        "markdown-it-py==3.0.0",
        "MarkupSafe==3.0.2",
        "mdurl==0.1.2",
        "pydantic==2.11.5",
        "pydantic_core==2.33.2",
        "Pygments==2.19.1",
        "python-dotenv==1.1.0",
        "python-multipart==0.0.20",
        "PyYAML==6.0.2",
        "rich==14.0.0",
        "rich-toolkit==0.14.7",
        "shellingham==1.5.4",
        "sniffio==1.3.1",
        "starlette==0.46.2",
        "typer==0.16.0",
        "typing-inspection==0.4.1",
        "typing_extensions==4.14.0",
        "uvicorn==0.34.3",
        "watchfiles==1.0.5",
        "websockets==15.0.1"
    ]
    
    # Add database-specific requirements
    db_config = get_database_config(config.database)
    if "requirements" in db_config:
        base_requirements.extend(db_config["requirements"])
    
    # Add auth-specific requirements
    auth_config = get_auth_config(config.auth)
    if "requirements" in auth_config:
        base_requirements.extend(auth_config["requirements"])
    
    # Add feature-specific requirements
    feature_requirements = {
        FeatureChoice.TESTING: ["pytest==7.4.3", "pytest-asyncio==0.21.1", "httpx==0.28.1"],
        FeatureChoice.CORS: [],  # CORS is built into FastAPI
        FeatureChoice.RATE_LIMITING: ["slowapi==0.1.9"],
        FeatureChoice.ALEMBIC: ["alembic==1.13.1"]
    }
    
    for feature in config.features:
        if feature in feature_requirements:
            base_requirements.extend(feature_requirements[feature])
    
    # Add password hashing for non-NoSQL databases with auth
    if config.auth in [AuthChoice.JWT] and config.database not in [DatabaseChoice.MONGODB, DatabaseChoice.FIREBASE]:
        base_requirements.append("passlib==1.7.4")
        base_requirements.append("bcrypt==4.0.1")
    
    # Remove duplicates and sort
    unique_requirements = sorted(list(set(base_requirements)))
    
    return "\n".join(unique_requirements) + "\n"
