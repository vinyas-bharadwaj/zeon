import textwrap
from typing import Dict, Any


class DatabaseTemplates:
    """Database configuration templates for different database options"""
    
    @staticmethod
    def get_sqlite_config() -> Dict[str, Any]:
        return {
            "database_py": textwrap.dedent("""\
                from sqlalchemy import create_engine
                from sqlalchemy.ext.declarative import declarative_base
                from sqlalchemy.orm import sessionmaker
                import os
                from dotenv import load_dotenv

                load_dotenv()

                SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

                engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

                SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

                Base = declarative_base()

                def init_db():
                    Base.metadata.create_all(bind=engine)

                def get_db():
                    db = SessionLocal()
                    try:
                        yield db
                    finally:
                        db.close()
            """),
            "env_vars": {
                "DATABASE_URL": "sqlite:///./sql_app.db"
            },
            "requirements": [
                "SQLAlchemy==2.0.41"
            ]
        }
    
    @staticmethod
    def get_postgresql_config() -> Dict[str, Any]:
        return {
            "database_py": textwrap.dedent("""\
                from sqlalchemy import create_engine
                from sqlalchemy.ext.declarative import declarative_base
                from sqlalchemy.orm import sessionmaker
                import os
                from dotenv import load_dotenv

                load_dotenv()

                SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

                engine = create_engine(SQLALCHEMY_DATABASE_URL)

                SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

                Base = declarative_base()

                def init_db():
                    Base.metadata.create_all(bind=engine)

                def get_db():
                    db = SessionLocal()
                    try:
                        yield db
                    finally:
                        db.close()
            """),
            "env_vars": {
                "DATABASE_URL": "postgresql://user:password@localhost/dbname",
                "DB_HOST": "localhost",
                "DB_PORT": "5432",
                "DB_NAME": "your_database",
                "DB_USER": "your_username",
                "DB_PASSWORD": "your_password"
            },
            "requirements": [
                "SQLAlchemy==2.0.41",
                "psycopg2-binary==2.9.7"
            ]
        }
    
    @staticmethod
    def get_mongodb_config() -> Dict[str, Any]:
        return {
            "database_py": textwrap.dedent("""\
                from motor.motor_asyncio import AsyncIOMotorClient
                from pymongo import MongoClient
                import os
                from dotenv import load_dotenv

                load_dotenv()

                MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
                DATABASE_NAME = os.getenv("DATABASE_NAME", "fastapi_db")

                # Async client for FastAPI
                client = AsyncIOMotorClient(MONGODB_URL)
                database = client[DATABASE_NAME]

                # Sync client for non-async operations
                sync_client = MongoClient(MONGODB_URL)
                sync_database = sync_client[DATABASE_NAME]

                async def get_database():
                    return database

                def get_sync_database():
                    return sync_database

                async def close_database_connection():
                    client.close()
            """),
            "models_py": textwrap.dedent("""\
                from pydantic import BaseModel, Field
                from typing import Optional
                from datetime import datetime
                from bson import ObjectId

                class PyObjectId(ObjectId):
                    @classmethod
                    def __get_validators__(cls):
                        yield cls.validate

                    @classmethod
                    def validate(cls, v):
                        if not ObjectId.is_valid(v):
                            raise ValueError("Invalid objectid")
                        return ObjectId(v)

                    @classmethod
                    def __modify_schema__(cls, field_schema):
                        field_schema.update(type="string")

                class User(BaseModel):
                    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
                    username: str = Field(...)
                    email: str = Field(...)
                    password: str = Field(...)
                    created_at: datetime = Field(default_factory=datetime.utcnow)

                    class Config:
                        allow_population_by_field_name = True
                        arbitrary_types_allowed = True
                        json_encoders = {ObjectId: str}
            """),
            "env_vars": {
                "MONGODB_URL": "mongodb://localhost:27017",
                "DATABASE_NAME": "fastapi_db"
            },
            "requirements": [
                "motor==3.3.2",
                "pymongo==4.6.1"
            ]
        }
    
    @staticmethod
    def get_supabase_config() -> Dict[str, Any]:
        return {
            "database_py": textwrap.dedent("""\
                from supabase import create_client, Client
                from sqlalchemy import create_engine
                from sqlalchemy.ext.declarative import declarative_base
                from sqlalchemy.orm import sessionmaker
                import os
                from dotenv import load_dotenv

                load_dotenv()

                # Supabase client setup
                SUPABASE_URL = os.getenv("SUPABASE_URL")
                SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
                supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

                # SQLAlchemy setup for Supabase PostgreSQL
                SQLALCHEMY_DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL")

                engine = create_engine(SQLALCHEMY_DATABASE_URL)

                SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

                Base = declarative_base()

                def init_db():
                    Base.metadata.create_all(bind=engine)

                def get_db():
                    db = SessionLocal()
                    try:
                        yield db
                    finally:
                        db.close()

                def get_supabase_client():
                    return supabase
            """),
            "env_vars": {
                "SUPABASE_URL": "https://your-project.supabase.co",
                "SUPABASE_ANON_KEY": "your-anon-key",
                "SUPABASE_SERVICE_ROLE_KEY": "your-service-role-key",
                "SUPABASE_DATABASE_URL": "postgresql://postgres:password@db.your-project.supabase.co:5432/postgres"
            },
            "requirements": [
                "SQLAlchemy==2.0.41",
                "psycopg2-binary==2.9.7",
                "supabase==2.3.4"
            ]
        }
    
    @staticmethod
    def get_firebase_config() -> Dict[str, Any]:
        return {
            "database_py": textwrap.dedent("""\
                import firebase_admin
                from firebase_admin import credentials, firestore
                import os
                from dotenv import load_dotenv

                load_dotenv()

                # Initialize Firebase Admin SDK
                SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")

                if not firebase_admin._apps:
                    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
                        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
                        firebase_admin.initialize_app(cred)
                    else:
                        # Use default credentials (for production with service account)
                        firebase_admin.initialize_app()

                # Get Firestore client
                db = firestore.client()

                def get_firestore_client():
                    return db

                class FirestoreRepository:
                    def __init__(self, collection_name: str):
                        self.collection = db.collection(collection_name)
                    
                    async def create(self, data: dict):
                        doc_ref = self.collection.document()
                        doc_ref.set(data)
                        return doc_ref.id
                    
                    async def get(self, doc_id: str):
                        doc = self.collection.document(doc_id).get()
                        return doc.to_dict() if doc.exists else None
                    
                    async def update(self, doc_id: str, data: dict):
                        self.collection.document(doc_id).update(data)
                    
                    async def delete(self, doc_id: str):
                        self.collection.document(doc_id).delete()
                    
                    async def get_all(self):
                        docs = self.collection.stream()
                        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
            """),
            "models_py": textwrap.dedent("""\
                from pydantic import BaseModel, Field
                from typing import Optional
                from datetime import datetime

                class User(BaseModel):
                    id: Optional[str] = None
                    username: str = Field(...)
                    email: str = Field(...)
                    password: str = Field(...)
                    created_at: datetime = Field(default_factory=datetime.utcnow)

                    class Config:
                        json_encoders = {
                            datetime: lambda dt: dt.isoformat()
                        }
            """),
            "env_vars": {
                "FIREBASE_SERVICE_ACCOUNT_PATH": "./firebase-service-account.json",
                "FIREBASE_PROJECT_ID": "your-firebase-project-id"
            },
            "requirements": [
                "firebase-admin==6.4.0"
            ]
        }


class AuthTemplates:
    """Authentication configuration templates"""
    
    @staticmethod
    def get_jwt_auth() -> Dict[str, Any]:
        return {
            "oauth2_py": textwrap.dedent("""\
                from fastapi import Depends, status, HTTPException
                from fastapi.security import OAuth2PasswordBearer
                import jwt
                from jwt import PyJWTError
                from datetime import datetime, timedelta, timezone
                from sqlalchemy.orm import Session
                from dotenv import load_dotenv
                import os
                from .schemas import TokenData
                from .database import get_db
                from .models import User

                load_dotenv()

                oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')

                SECRET_KEY = os.getenv('SECRET_KEY')
                ALGORITHM = os.getenv('ALGORITHM')
                ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

                def create_access_token(data: dict):
                    to_encode = data.copy()
                    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                    to_encode.update({"exp": expire})
                    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
                    return encoded_jwt

                def verify_access_token(token: str, credentials_exception):
                    try:
                        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                        id: str = payload.get("user_id")
                        username: str = payload.get("username")
                        token_data = TokenData(id=id)
                    except PyJWTError:
                        raise credentials_exception
                    return token_data

                def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
                    credentials_exception = HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, 
                        detail="could not validate credentials",
                        headers={"WWW-Authenticate": "Bearer"}
                    )
                    token = verify_access_token(token, credentials_exception)
                    user = db.query(User).filter(User.id == token.id).first()
                    return user
            """),
            "requirements": ["PyJWT==2.10.1"]
        }
    
    @staticmethod
    def get_supabase_auth() -> Dict[str, Any]:
        return {
            "oauth2_py": textwrap.dedent("""\
                from fastapi import Depends, status, HTTPException
                from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
                from .database import get_supabase_client
                from gotrue.errors import AuthError

                security = HTTPBearer()

                def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
                    try:
                        supabase = get_supabase_client()
                        user = supabase.auth.get_user(credentials.credentials)
                        if user.user is None:
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid authentication credentials"
                            )
                        return user.user
                    except AuthError as e:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=str(e)
                        )
            """),
            "requirements": []
        }
