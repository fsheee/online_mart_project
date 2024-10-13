import asyncio
import json
import logging
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta
from typing import Annotated, List
from app.models import User, Token, UserAll, UserResponse, UserUpdate,RegisterUser
from app.auth import authenticate_user, create_access_token, create_refresh_token, get_current_user,validate_refresh_token, get_user_from_db, hash_password

from app.db import get_session, create_tables
from app.deps import get_kafka_producer
from app.settings import KAFKA_USER_TOPIC,BOOTSTRAP_SERVER
from app.consumer.user_consumer import consume_messages
# from app.crud.user_crud import update_user_profile

logging.basicConfig(level=logging.INFO)

# Define the lifespan event handler
async def lifespan(app: FastAPI):
    logging.info("Lifespan event started...")
    
    # Create database tables
    create_tables()
    
    logging.info("Lifespan event completed...")
# Start Kafka consumer task
    # task = asyncio.create_task(consume_messages('order', 'broker:19092'))
    task = asyncio.create_task(consume_messages(KAFKA_USER_TOPIC, 
                                         BOOTSTRAP_SERVER))

    try:
        yield 
    finally:
        logging.info("Lifespan event ended...")
        # Cancel the consumer task on shutdown
        task.cancel()
        await task  
app = FastAPI(
    lifespan=lifespan,
    title="Kafka With FastAPI User Micro Service",
    version="0.0.1",
    servers=[
        {
            "url": "http://127.0.0.1:8006",
            "description": "Development Server"
        }
    ]
)

# JWT configuration
SECRET_KEY = 'ur secret key'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
    producer: AIOKafkaProducer = Depends(get_kafka_producer)):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    user_data = {
        "action": "login",
        "user": {
            "id": user.user_id,
            "username": user.username,
            "email": user.email
        }
    }
    
    await producer.send_and_wait("KAFKA_USER_TOPIC", json.dumps(user_data).encode('utf-8'))
    return {"access_token": access_token, "token_type": "bearer"}

# CRUD Endpoints for User
#

@app.post("/signup", response_model=dict)
async def create_user(user: RegisterUser, session: Annotated[Session,
                      Depends(get_session)], producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):
    # Check if user already exists
    existing_user = get_user_from_db(session, email=user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = hash_password(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # Create access token
    access_token = create_access_token(data={"sub": new_user.username})
    
    #  sent to Kafka
    user_data = {
        "action": "create",
        "user": {
            "user_id": new_user.user_id,
            "username": new_user.username,
            "email": new_user.email
        }
    }
    
    # Send data to Kafka
    await producer.send_and_wait("KAFKA_USER_TOPIC", json.dumps(user_data).encode('utf-8'))
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": new_user.username,
        "detail": "User created successfully"
    }


@app.get("/profile", response_model=UserResponse)
def get_user(current_user: Annotated[UserResponse, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)]):
    user = session.query(User).filter(User.user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
    

# by id
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user_by_id(  user_id: int, current_user: Annotated[UserResponse,
                    Depends(get_current_user)] ,session:Annotated [Session,Depends(get_session)]):
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
# ## all user

@app.get("/users", response_model=List[UserAll])
def get_all_users( session: Session = Depends(get_session),current_user = Depends(get_current_user)
):
    # Retrieve all users from the database
    users = session.exec(select(User)).all()

    # Log the number of users found
    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    return users  # Return the list of users
#update 
@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user_by_id(user_id:int,user_update:UserUpdate,
                      session: Annotated[Session, Depends(get_session)],
                     producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):

    # Fetch the user from the database
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user 
    if user_update.email:
        # Check if the new email is already registered by another user
        db_user_with_email = session.query(User).filter(User.email == user_update.email).first()
        if db_user_with_email and db_user_with_email.user_id != user_id:
            raise HTTPException(status_code=400, detail="Email already registered")
        db_user.email = user_update.email

    if user_update.password:
        hashed_password = hash_password(user_update.password)
        db_user.hashed_password = hashed_password


    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    
    user_data = {
        "action": "update",
        "user": {
            "id": db_user.user_id,  # The user's ID
            "username": db_user.username,
            "email": db_user.email
        }
    }

    # Send to kafka
    await producer.send_and_wait(KAFKA_USER_TOPIC, json.dumps(user_data).encode('utf-8'))

    
    return db_user

    
# del
@app.delete("/users/{user_id}")
async def delete_user_by_id( user_id: int,  session: Annotated[Session, Depends(get_session)],
                       producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):
    # Fetch the user from the database
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    session.delete(user)
    session.commit()

    # Prepare Kafka message data
    user_data = {
        "action": "delete",
        "user": {
            "id": user.user_id,
            "username": user.username,
            "email": user.email
        }
    }

    # Send a message to Kafka
    await producer.send_and_wait(KAFKA_USER_TOPIC, json.dumps(user_data).encode('utf-8'))

    # Return success message
    return {"message": "User deleted successfully"}

# Token Refresh Endpoint
@app.post("/refresh")
def refresh_access_token(old_token: str, session: Session = Depends(get_session)):
    
    user = validate_refresh_token(old_token, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expiry_time=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
