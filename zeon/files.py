import textwrap
import secrets

main_py_content = textwrap.dedent("""\
    from fastapi import FastAPI
    from .database import Base, engine
    from .routers.auth import router as auth_router

    app = FastAPI()

    Base.metadata.create_all(bind=engine)

    app.include_router(auth_router)

    @app.get("/")
    def home():
        return {"message": "Hello world"}
""")

database_py_content = textwrap.dedent("""\
    from sqlalchemy import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker


    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

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
""")

models_py_content = textwrap.dedent("""\
    from sqlalchemy import Column, Integer, String, Text
    from sqlalchemy.sql.sqltypes import TIMESTAMP 
    from sqlalchemy.sql import func
    from .database import Base
                                   
    class User(Base):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, nullable=False)
        username = Column(String, nullable=False, unique=True)
        email = Column(String, nullable=False, unique=True)
        password = Column(String, nullable=False)
        created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
""")

oauth2_py_content = textwrap.dedent("""\
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
        credentials_exception = HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                                                detail="could not validate credentials",
                                                headers={"WWW-Authenticate": "Bearer"})
        
        token = verify_access_token(token, credentials_exception)

        user = db.query(User).filter(User.id == token.id).first()
        
        return user
""")

schemas_py_content = textwrap.dedent("""\
    from pydantic import BaseModel, EmailStr
    from datetime import datetime
    from typing import Optional
    
    class CreateUser(BaseModel):
        username: str
        email: EmailStr
        password: str

    class ResponseUser(BaseModel):
        id: int
        username: str
        email: str
        created_at: datetime

        model_config = {
            "from_attributes": True
        }
    
    class Token(BaseModel):
        access_token: str
        token_type: str
                                     
        
    class TokenData(BaseModel):
        id: Optional[int] = None
        username: Optional[str] = None
""")


utils_py_content = textwrap.dedent("""\
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


    # Hashing and security
    def hash(password: str):
        return pwd_context.hash(password)

    def verify(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
""")

routers_auth_py_content = textwrap.dedent("""\
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

gitignore_content = textwrap.dedent("""\
    venv/
    __pycache__/
    .env
""")

secret_key = secrets.token_urlsafe(32)
env_content = textwrap.dedent(f"""\
    SECRET_KEY={secret_key}
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
""")

requirements_content = textwrap.dedent("""\
    annotated-types==0.7.0
    anyio==4.9.0
    bcrypt==4.0.1
    certifi==2025.4.26
    click==8.2.1
    colorama==0.4.6
    dnspython==2.7.0
    email_validator==2.2.0
    fastapi==0.115.12
    fastapi-cli==0.0.7
    greenlet==3.2.3
    h11==0.16.0
    httpcore==1.0.9
    httptools==0.6.4
    httpx==0.28.1
    idna==3.10
    Jinja2==3.1.6
    markdown-it-py==3.0.0
    MarkupSafe==3.0.2
    mdurl==0.1.2
    passlib==1.7.4
    pydantic==2.11.5
    pydantic_core==2.33.2
    Pygments==2.19.1
    PyJWT==2.10.1
    python-dotenv==1.1.0
    python-multipart==0.0.20
    PyYAML==6.0.2
    rich==14.0.0
    rich-toolkit==0.14.7
    shellingham==1.5.4
    sniffio==1.3.1
    SQLAlchemy==2.0.41
    starlette==0.46.2
    typer==0.16.0
    typing-inspection==0.4.1
    typing_extensions==4.14.0
    uvicorn==0.34.3
    watchfiles==1.0.5
    websockets==15.0.1
""")