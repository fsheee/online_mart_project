
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from app.config import MailBody  
from app.email import send_email  
from app.consumer.notice_consumer import consume_order_events
 

# Lifespan handler to start and stop Kafka consumer as a background task
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start consuming messages from Kafka
    task = asyncio.create_task(consume_order_events())
    yield
    # Stop the Kafka consumer 
    await task


app = FastAPI(
    lifespan=lifespan,
    title="Notification Service API",
    version="0.0.1",
    # description="Notification Service API delivers timely, personalized notifications to keep users informed and engaged with order and account updates."
    servers=[
        {
            "url": "http://127.0.0.1:8009/",
            "description": "Local Development Server"
        }
    ]
)


@app.get("/")
def index():
    return {"status": "FastAPI notification service"}

# Endpoint to schedule an email notification using FastAPI BackgroundTasks
@app.post("/send_email")
def schedule_mail(req: MailBody, tasks: BackgroundTasks):
    data = req.dict()
    tasks.add_task(send_email, data)  # Add the email task to background execution
    return {"status": 200, "message": "Email has been sent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8009)
