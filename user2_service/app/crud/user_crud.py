
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from app.models import RegisterUser, UserUpdate,User

from passlib.context import CryptContext
# Create an instance of CryptContext for bcrypt hashing
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration
SECRET_KEY = 'ur secret key'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_MINUTES = 60


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# create user
async def create_user(session:Session, user:RegisterUser):
    db_user = User(
    username = user.username,
    email = user.email,
    hashed_password = bcrypt_context.hash(user.password),)
    session.add(db_user)
    session.commit()
    return db_user

    
#  Authenticate a user and return the authenticated user 
async def authenticate(session: Session, username: str, password: str):
    db_user = session.query(User).filter(User.username == username).first()
    if not db_user:
        return None
    if not bcrypt_context.verify(password, db_user.hashed_password):
        return None
    return db_user
    

async def update_user(session:Session,db_user:User, user_update:UserUpdate):
    db_user.email = user_update.email or db_user.email
    # save
    session.commit()
    session.refresh(db_user)


def delete_user(user_id: int, session: Session):
    # Fetch the user based on ID
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete the user from the database
    session.delete(user)
    session.commit()
    return {"message": "User deleted successfully"}

# def update_user_profile(user_id: int, updated_data: RegisterUser, session: Session):
#     user = session.get(User, user_id)
#     if not user:
#         return None  # or raise an exception
#     user.username = updated_data.username
#     user.email = updated_data.email
#     user.password=updated_data.password
#     session.add(user)
#     session.commit()
#     session.refresh(user)
#     return user

# from sqlmodel import Session, select
# from app.models import User

# def create_user(session: Session, username: str, email: str, password: str) -> User:
#     user = User(username=username, email=email, password=password)
#     session.add(user)
#     session.commit()
#     session.refresh(user)
#     return user

# def get_user_by_username(session: Session, username: str) -> User:
#     statement = select(User).where(User.username == username)
#     return session.exec(statement).first()

# def get_user_by_email(session: Session, email: str) -> User:
#     statement = select(User).where(User.email == email)
#     return session.exec(statement).first()
