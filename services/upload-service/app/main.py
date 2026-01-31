import os
import boto3
import jwt
import uuid
import json
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
import aio_pika

# --- CONFIGURATION ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@doc_mongo:27017")
RABBITMQ_URI = os.getenv("RABBITMQ_URI", "amqp://guest:guest@doc_rabbitmq:5672/")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "documents")
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "super-secret-key")
JWT_ALGORITHM = "HS256"

# --- GLOBAL CLIENTS ---

mongodb_client = None
db = None
rabbitmq_connection = None
rabbitmq_channel = None

# --- S3 CLIENT ---

s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL", "http://minio:9000"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
    region_name=os.getenv("AWS_REGION", "us-east-1"),
)

# --- LIFESPAN MANAGER (Startup/Shutdown Logic) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongodb_client, db, rabbitmq_connection, rabbitmq_channel
    
    # 1. Connect to MongoDB
    print("Connecting to MongoDB...")
    mongodb_client = AsyncIOMotorClient(MONGO_URI)
    db = mongodb_client.docuflow_db
    print("Connected to MongoDB.")

    # 1.5. AUTOMATION: Create S3 Bucket if missing
    print(f"Checking for S3 Bucket '{S3_BUCKET_NAME}'...")
    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        print(f"Bucket '{S3_BUCKET_NAME}' exists.")
    except Exception:
        print(f"Bucket '{S3_BUCKET_NAME}' not found. Creating it...")
        try:
            s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
            print(f"Successfully created bucket '{S3_BUCKET_NAME}'")
        except Exception as e:
            print(f"CRITICAL: Failed to create bucket: {e}")

    # 2. Connect to RabbitMQ
    print("Connecting to RabbitMQ...")
    try:
        rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URI)
        rabbitmq_channel = await rabbitmq_connection.channel()
        # Declare the queue to ensure it exists
        await rabbitmq_channel.declare_queue("task_queue", durable=True)
        print("Connected to RabbitMQ.")
    except Exception as e:
        print(f"Warning: RabbitMQ connection failed (Worker features won't work): {e}")

    yield # The application runs here

    # 3. Cleanup on Shutdown
    print("Closing connections...")
    if mongodb_client:
        mongodb_client.close()
    if rabbitmq_connection:
        await rabbitmq_connection.close()

# --- APP INITIALIZATION ---
app = FastAPI(lifespan=lifespan)
security = HTTPBearer()

# --- AUTH HELPER ---
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # Decode the token using the Secret Key shared with Auth Service
        print("---------------------------------------------------")
        print(f"DEBUG CHECK: The loaded Secret Key is: '{JWT_SECRET}'")
        print("---------------------------------------------------")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return str(user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- ROUTES ---

@app.get("/health")
def health_check():
    return {"status": "running", "service": "upload-service"}

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    user_id: str = Depends(get_current_user)
):
    """
    1. Uploads file to MinIO (S3)
    2. Saves metadata to MongoDB
    3. Sends message to RabbitMQ for processing
    """
    
    # A. Validation
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    file_id = str(uuid.uuid4())
    s3_key = f"{user_id}/{file_id}.pdf"

    try:
        # B. Upload to MinIO
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": file.content_type}
        )

        # C. Save Metadata to MongoDB
        file_doc = {
            "_id": file_id,
            "user_id": user_id,
            "filename": file.filename,
            "s3_path": s3_key,
            "upload_timestamp": datetime.utcnow(),
            "status": "PENDING", 
            "content_type": file.content_type
        }
        await db.documents.insert_one(file_doc)

        # D. Send to RabbitMQ 
        if rabbitmq_channel:
            message_body = json.dumps({
                "task": "process_pdf",
                "file_id": file_id,
                "s3_path": s3_key,
                "user_id": user_id
            }).encode()

            await rabbitmq_channel.default_exchange.publish(
                aio_pika.Message(body=message_body),
                routing_key="task_queue"
            )

        return {
            "message": "Upload successful",
            "file_id": file_id,
            "status": "PENDING"
        }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/status/{file_id}")
async def get_file_status(file_id: str, user_id: str = Depends(get_current_user)):
    # 1. Query MongoDB for the file
    doc = await db.documents.find_one({"_id": file_id, "user_id": user_id})

    if not doc:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "file_id": doc["_id"],
        "filename": doc["filename"],
        "status": doc["status"], # "COMPLETED" when successful
        "extracted_text": doc.get("extracted_text", None), 
        "upload_timestamp": doc["upload_timestamp"]
    }

@app.get("/files")
async def list_user_files(user_id: str = Depends(get_current_user)):
    # Sort by newest first (-1)
    cursor = db.documents.find({"user_id": user_id}).sort("upload_timestamp", -1)
    return await cursor.to_list(length=50)
