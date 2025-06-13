from pathlib import Path    
import files
import typer
import textwrap
import subprocess
import sys

app = typer.Typer()


def create_structure(project_name: str):
    base_path = Path(project_name)
    venv_path = base_path / 'venv'
    app_path = base_path / "app"
    routers_path = app_path / "routers"
    app_path.mkdir(parents=True, exist_ok=True)
    routers_path.mkdir(parents=True, exist_ok=True)

    (base_path / ".gitignore").write_text(files.gitignore_content)
    (base_path / ".env").write_text(files.env_content)

    (app_path / "__init__.py").touch()
    (app_path / "main.py").write_text(files.main_py_content)
    (app_path / "database.py").write_text(files.database_py_content)
    (app_path / "models.py").write_text(files.models_py_content)
    (app_path / "schemas.py").write_text(files.schemas_py_content)
    (app_path / "utils.py").write_text(files.utils_py_content)
    (app_path / "oauth2.py").write_text(files.oauth2_py_content)

    (routers_path / "__init__.py").touch()
    (routers_path / "auth.py").write_text(files.routers_auth_py_content)


    (base_path / "requirements.txt").write_text(files.requirements_content)

    # step 1: Creating virtual environment
    typer.echo("Creating virtual environment...")
    subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)

    # step 2: install all the dependencies from requirements.txt
    typer.echo("Installing dependencies in virtual environment...")
    
    if sys.platform == 'win32':
        pip_path = venv_path / 'Scripts' / 'pip'
    else:
        pip_path = venv_path / 'bin' / 'pip'

    subprocess.run([str(pip_path), "install", "-r", str(base_path / 'requirements.txt')], check=True)

    typer.echo(f"Project {project_name} initialized successfully!")


@app.command()
def init(project_name: str):
    """Initializes the FastAPI project"""
    create_structure(project_name)

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



if __name__ == "__main__":
    app()