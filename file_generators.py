import textwrap
from typing import Dict, Any
from config_manager import ProjectConfiguration, DatabaseChoice, AuthChoice, FeatureChoice


class AdditionalTemplates:
    """Templates for additional features and configurations"""
    
    @staticmethod
    def get_docker_files() -> Dict[str, str]:
        return {
            "Dockerfile": textwrap.dedent("""\
                FROM python:3.11-slim

                WORKDIR /app

                COPY requirements.txt .
                RUN pip install --no-cache-dir -r requirements.txt

                COPY ./app ./app

                CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
            """),
            "docker-compose.yml": textwrap.dedent("""\
                version: '3.8'

                services:
                  web:
                    build: .
                    ports:
                      - "8000:8000"
                    volumes:
                      - ./app:/app/app
                    environment:
                      - DATABASE_URL=${DATABASE_URL}
                    depends_on:
                      - db

                  db:
                    image: postgres:15
                    environment:
                      POSTGRES_DB: fastapi_db
                      POSTGRES_USER: user
                      POSTGRES_PASSWORD: password
                    ports:
                      - "5432:5432"
                    volumes:
                      - postgres_data:/var/lib/postgresql/data

                volumes:
                  postgres_data:
            """),
            ".dockerignore": textwrap.dedent("""\
                __pycache__
                *.pyc
                *.pyo
                *.pyd
                .Python
                env/
                venv/
                .env
                .git
                .gitignore
                README.md
                Dockerfile
                .dockerignore
            """)
        }
    
    @staticmethod
    def get_testing_files() -> Dict[str, str]:
        return {
            "tests/__init__.py": "",
            "tests/conftest.py": textwrap.dedent("""\
                import pytest
                from fastapi.testclient import TestClient
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from app.main import app
                from app.database import get_db, Base

                SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

                engine = create_engine(
                    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
                )
                TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

                @pytest.fixture
                def session():
                    Base.metadata.drop_all(bind=engine)
                    Base.metadata.create_all(bind=engine)
                    db = TestingSessionLocal()
                    try:
                        yield db
                    finally:
                        db.close()

                @pytest.fixture
                def client(session):
                    def override_get_db():
                        try:
                            yield session
                        finally:
                            session.close()

                    app.dependency_overrides[get_db] = override_get_db
                    yield TestClient(app)
                    del app.dependency_overrides[get_db]
            """),
            "tests/test_main.py": textwrap.dedent("""\
                import pytest
                from fastapi.testclient import TestClient

                def test_read_main(client):
                    response = client.get("/")
                    assert response.status_code == 200
                    assert response.json() == {"message": "Hello world"}
            """),
            "tests/test_auth.py": textwrap.dedent("""\
                import pytest
                from fastapi.testclient import TestClient

                def test_create_user(client):
                    response = client.post(
                        "/auth/register",
                        json={
                            "username": "testuser",
                            "email": "test@example.com",
                            "password": "testpassword"
                        }
                    )
                    assert response.status_code == 201
                    data = response.json()
                    assert data["username"] == "testuser"
                    assert data["email"] == "test@example.com"
                    assert "id" in data

                def test_login_user(client):
                    # First create a user
                    client.post(
                        "/auth/register",
                        json={
                            "username": "testuser",
                            "email": "test@example.com",
                            "password": "testpassword"
                        }
                    )
                    
                    # Then login
                    response = client.post(
                        "/auth/login",
                        data={
                            "username": "testuser",
                            "password": "testpassword"
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert "access_token" in data
                    assert data["token_type"] == "bearer"
            """)
        }
    
    @staticmethod
    def get_cors_middleware() -> str:
        return textwrap.dedent("""\
            from fastapi.middleware.cors import CORSMiddleware

            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],  # Allows all origins
                allow_credentials=True,
                allow_methods=["*"],  # Allows all methods
                allow_headers=["*"],  # Allows all headers
            )
        """)
    
    @staticmethod
    def get_rate_limiting_middleware() -> str:
        return textwrap.dedent("""\
            from slowapi import Limiter, _rate_limit_exceeded_handler
            from slowapi.util import get_remote_address
            from slowapi.errors import RateLimitExceeded

            limiter = Limiter(key_func=get_remote_address)
            app.state.limiter = limiter
            app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        """)


class CustomizedFileGenerator:
    """Generate customized files based on project configuration"""
    
    def __init__(self, config: ProjectConfiguration):
        self.config = config
    
    def generate_main_py(self) -> str:
        """Generate main.py based on configuration"""
        imports = ["from fastapi import FastAPI"]
        
        # Database imports
        if self.config.database in [DatabaseChoice.SQLITE, DatabaseChoice.POSTGRESQL, DatabaseChoice.SUPABASE]:
            imports.append("from .database import Base, engine")
        elif self.config.database == DatabaseChoice.MONGODB:
            imports.append("from .database import close_database_connection")
        elif self.config.database == DatabaseChoice.FIREBASE:
            imports.append("from .database import get_firestore_client")
        
        # Auth router import (only if auth is enabled)
        if self.config.auth != AuthChoice.NONE:
            imports.append("from .routers.auth import router as auth_router")
        
        # Feature imports
        if FeatureChoice.CORS in self.config.features:
            imports.append("from fastapi.middleware.cors import CORSMiddleware")
        
        if FeatureChoice.RATE_LIMITING in self.config.features:
            imports.extend([
                "from slowapi import Limiter, _rate_limit_exceeded_handler",
                "from slowapi.util import get_remote_address",
                "from slowapi.errors import RateLimitExceeded"
            ])
        
        # App creation
        app_creation = ["app = FastAPI()"]
        
        # Database initialization
        if self.config.database in [DatabaseChoice.SQLITE, DatabaseChoice.POSTGRESQL, DatabaseChoice.SUPABASE]:
            app_creation.append("Base.metadata.create_all(bind=engine)")
        
        # Middleware setup
        middleware_setup = []
        
        if FeatureChoice.CORS in self.config.features:
            middleware_setup.extend([
                "",
                "app.add_middleware(",
                "    CORSMiddleware,",
                "    allow_origins=[\"*\"],",
                "    allow_credentials=True,",
                "    allow_methods=[\"*\"],",
                "    allow_headers=[\"*\"],",
                ")"
            ])
        
        if FeatureChoice.RATE_LIMITING in self.config.features:
            middleware_setup.extend([
                "",
                "limiter = Limiter(key_func=get_remote_address)",
                "app.state.limiter = limiter",
                "app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)"
            ])
        
        # Router inclusion
        router_inclusion = []
        if self.config.auth != AuthChoice.NONE:
            router_inclusion.append("app.include_router(auth_router)")
        
        # Shutdown event for MongoDB
        shutdown_event = []
        if self.config.database == DatabaseChoice.MONGODB:
            shutdown_event.extend([
                "",
                "@app.on_event(\"shutdown\")",
                "async def shutdown_db_client():",
                "    await close_database_connection()"
            ])
        
        # Home route
        home_route = [
            "",
            "@app.get(\"/\")",
            "def home():",
            "    return {\"message\": \"Hello world\"}"
        ]
        
        # Combine all parts
        all_parts = (
            imports +
            [""] +
            app_creation +
            middleware_setup +
            ([""] if router_inclusion else []) +
            router_inclusion +
            shutdown_event +
            home_route
        )
        
        return "\n".join(all_parts) + "\n"
    
    def generate_auth_router(self) -> str:
        """Generate auth router based on database and auth configuration"""
        if self.config.auth == AuthChoice.NONE:
            return ""
        
        if self.config.database == DatabaseChoice.MONGODB:
            return self._generate_mongodb_auth_router()
        elif self.config.database == DatabaseChoice.FIREBASE:
            return self._generate_firebase_auth_router()
        elif self.config.auth == AuthChoice.SUPABASE:
            return self._generate_supabase_auth_router()
        else:
            return self._generate_sql_auth_router()
    
    def _generate_sql_auth_router(self) -> str:
        """Generate SQL-based auth router"""
        return textwrap.dedent("""\
            from fastapi import APIRouter, Depends, HTTPException, status
            from fastapi.security.oauth2 import OAuth2PasswordRequestForm
            from sqlalchemy.orm import Session
            from ..database import get_db
            from ..schemas import Token
            from ..models import User
            from ..oauth2 import create_access_token
            from ..utils import hash, verify
            from ..schemas import CreateUser, ResponseUser

            router = APIRouter(
                prefix='/auth',
                tags=['auth']
            )

            @router.post('/register', response_model=ResponseUser, status_code=status.HTTP_201_CREATED)
            def create_user(user: CreateUser, db: Session = Depends(get_db)):
                hashed_password = hash(user.password)
                user.password = hashed_password

                new_user = User(**user.model_dump()) 
                db.add(new_user)
                db.commit() 
                db.refresh(new_user)

                return new_user

            @router.get('/user/{id}', response_model=ResponseUser)
            def get_user(id: int, db: Session = Depends(get_db)):
                user = db.query(User).filter(User.id == id).first()

                if user is None:
                    raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"user with id: {id} does not exist")

                return user

            @router.post('/login', response_model=Token)
            def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

                user = db.query(User).filter(User.username == user_credentials.username).first()

                if user is None:
                    raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"user with username: {user_credentials.username} does not exist")

                if not verify(user_credentials.password, user.password):
                    raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"invalid credentials")

                access_token = create_access_token(data={"user_id": user.id, "username": user.username })

                return {"access_token": access_token, "token_type": "bearer"}
        """)
    
    def _generate_mongodb_auth_router(self) -> str:
        """Generate MongoDB-based auth router"""
        return textwrap.dedent("""\
            from fastapi import APIRouter, Depends, HTTPException, status
            from fastapi.security.oauth2 import OAuth2PasswordRequestForm
            from ..database import get_database
            from ..schemas import Token, CreateUser, ResponseUser
            from ..oauth2 import create_access_token
            from ..utils import hash, verify
            from bson import ObjectId

            router = APIRouter(
                prefix='/auth',
                tags=['auth']
            )

            @router.post('/register', response_model=ResponseUser, status_code=status.HTTP_201_CREATED)
            async def create_user(user: CreateUser):
                db = await get_database()
                
                # Check if user already exists
                existing_user = await db.users.find_one({"$or": [{"username": user.username}, {"email": user.email}]})
                if existing_user:
                    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")
                
                hashed_password = hash(user.password)
                user_dict = user.model_dump()
                user_dict["password"] = hashed_password
                
                result = await db.users.insert_one(user_dict)
                new_user = await db.users.find_one({"_id": result.inserted_id})
                
                return ResponseUser(**new_user)

            @router.get('/user/{user_id}', response_model=ResponseUser)
            async def get_user(user_id: str):
                db = await get_database()
                user = await db.users.find_one({"_id": ObjectId(user_id)})
                
                if user is None:
                    raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"user with id: {user_id} does not exist")
                
                return ResponseUser(**user)

            @router.post('/login', response_model=Token)
            async def login(user_credentials: OAuth2PasswordRequestForm = Depends()):
                db = await get_database()
                user = await db.users.find_one({"username": user_credentials.username})
                
                if user is None:
                    raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"user with username: {user_credentials.username} does not exist")
                
                if not verify(user_credentials.password, user["password"]):
                    raise HTTPException(status.HTTP_403_FORBIDDEN, detail="invalid credentials")
                
                access_token = create_access_token(data={"user_id": str(user["_id"]), "username": user["username"]})
                
                return {"access_token": access_token, "token_type": "bearer"}
        """)
    
    def _generate_firebase_auth_router(self) -> str:
        """Generate Firebase-based auth router"""
        return textwrap.dedent("""\
            from fastapi import APIRouter, Depends, HTTPException, status
            from fastapi.security.oauth2 import OAuth2PasswordRequestForm
            from ..database import FirestoreRepository
            from ..schemas import CreateUser, ResponseUser, Token
            from ..oauth2 import create_access_token
            from ..utils import hash, verify

            router = APIRouter(
                prefix='/auth',
                tags=['auth']
            )

            users_repo = FirestoreRepository("users")

            @router.post('/register', response_model=ResponseUser, status_code=status.HTTP_201_CREATED)
            async def create_user(user: CreateUser):
                user_dict = user.model_dump()
                user_dict["password"] = hash(user.password)
                
                user_id = await users_repo.create(user_dict)
                new_user = await users_repo.get(user_id)
                new_user["id"] = user_id
                
                return ResponseUser(**new_user)

            @router.get('/user/{user_id}', response_model=ResponseUser)
            async def get_user(user_id: str):
                user = await users_repo.get(user_id)
                
                if user is None:
                    raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"user with id: {user_id} does not exist")
                
                user["id"] = user_id
                return ResponseUser(**user)

            @router.post('/login', response_model=Token)
            async def login(user_credentials: OAuth2PasswordRequestForm = Depends()):
                all_users = await users_repo.get_all()
                user = next((u for u in all_users if u["username"] == user_credentials.username), None)
                
                if user is None:
                    raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"user with username: {user_credentials.username} does not exist")
                
                if not verify(user_credentials.password, user["password"]):
                    raise HTTPException(status.HTTP_403_FORBIDDEN, detail="invalid credentials")
                
                access_token = create_access_token(data={"user_id": user["id"], "username": user["username"]})
                
                return {"access_token": access_token, "token_type": "bearer"}
        """)
    
    def _generate_supabase_auth_router(self) -> str:
        """Generate Supabase-based auth router"""
        return textwrap.dedent("""\
            from fastapi import APIRouter, Depends, HTTPException, status
            from ..database import get_supabase_client
            from ..schemas import CreateUser, ResponseUser, Token
            from gotrue.errors import AuthError

            router = APIRouter(
                prefix='/auth',
                tags=['auth']
            )

            @router.post('/register', response_model=ResponseUser, status_code=status.HTTP_201_CREATED)
            def create_user(user: CreateUser):
                try:
                    supabase = get_supabase_client()
                    auth_user = supabase.auth.sign_up({
                        "email": user.email,
                        "password": user.password,
                        "options": {
                            "data": {"username": user.username}
                        }
                    })
                    
                    if auth_user.user:
                        return ResponseUser(
                            id=auth_user.user.id,
                            username=user.username,
                            email=user.email,
                            created_at=auth_user.user.created_at
                        )
                    else:
                        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Failed to create user")
                        
                except AuthError as e:
                    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

            @router.post('/login', response_model=Token)
            def login(user: CreateUser):
                try:
                    supabase = get_supabase_client()
                    auth_response = supabase.auth.sign_in_with_password({
                        "email": user.email,
                        "password": user.password
                    })
                    
                    if auth_response.session:
                        return Token(
                            access_token=auth_response.session.access_token,
                            token_type="bearer"
                        )
                    else:
                        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
                        
                except AuthError as e:
                    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e))
        """)
