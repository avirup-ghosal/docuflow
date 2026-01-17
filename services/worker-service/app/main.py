import os
import json
import asyncio
import boto3
import aio_pika
from motor.motor_asyncio import AsyncIOMotorClient
from pypdf import PdfReader
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@doc_mongo:27017")
RABBITMQ_URI = os.getenv("RABBITMQ_URI", "amqp://guest:guest@doc_rabbitmq:5672/")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "documents")

# --- CLIENTS ---
# MongoDB (Async)
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client.docuflow_db

# S3/MinIO (Synchronous - will run in thread pool)
s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL", "http://minio:9000"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
    region_name=os.getenv("AWS_REGION", "us-east-1"),
)

# Thread Pool for CPU-heavy tasks (PDF parsing)
executor = ThreadPoolExecutor(max_workers=3)

def process_pdf_sync(file_id, s3_key):
    """
    This function runs in a separate thread to avoid blocking the async loop.
    1. Downloads PDF from MinIO
    2. Extracts text using pypdf
    """
    print(f"[{file_id}] Downloading from MinIO: {s3_key}", flush=True)
    
    try:
        # A. Download file into memory (RAM)
        file_obj = BytesIO()
        s3_client.download_fileobj(S3_BUCKET_NAME, s3_key, file_obj)
        file_obj.seek(0) # Reset pointer to start of file

        # B. Extract Text
        print(f"[{file_id}] Extracting text...", flush=True)
        reader = PdfReader(file_obj)
        extracted_text = ""
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
        
        # Simple fallback if PDF is empty or image-only
        if not extracted_text.strip():
            extracted_text = "[No text found or scanned PDF]"

        return extracted_text

    except Exception as e:
        print(f"[{file_id}] Error processing PDF: {e}", flush=True)
        raise e

async def on_message(message: aio_pika.IncomingMessage):
    """
    Triggered when a message arrives from RabbitMQ.
    """
    async with message.process(): # Automatically sends ACK if this block finishes
        body = json.loads(message.body)
        file_id = body.get("file_id")
        s3_key = body.get("s3_path")
        
        print(f"Received Job: {file_id}", flush=True)

        try:
            # 1. Update Status to PROCESSING
            await db.documents.update_one(
                {"_id": file_id},
                {"$set": {"status": "PROCESSING"}}
            )

            # 2. Run Heavy Logic in Thread Pool (Non-blocking)
            loop = asyncio.get_running_loop()
            text_content = await loop.run_in_executor(
                executor, 
                process_pdf_sync, 
                file_id, 
                s3_key
            )

            # 3. Update DB with Results
            await db.documents.update_one(
                {"_id": file_id},
                {
                    "$set": {
                        "status": "COMPLETED",
                        "extracted_text": text_content
                    }
                }
            )
            print(f"[{file_id}] Job Finished Successfully.", flush=True)

        except Exception as e:
            print(f"[{file_id}] Job Failed: {e}", flush=True)
            # Mark as FAILED for UI
            await db.documents.update_one(
                {"_id": file_id},
                {"$set": {"status": "FAILED", "error": str(e)}}
            )

async def main():
    """
    Main entry point: Connects to RabbitMQ and starts listening.
    """
    print("Worker Service Starting...", flush=True)
    
    # Retry logic for RabbitMQ connection (waits for RabbitMQ to start)
    while True:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URI)
            break
        except Exception as e:
            print(f"Waiting for RabbitMQ... ({e})", flush=True)
            await asyncio.sleep(5)

    channel = await connection.channel()
    
    # Declare queue (idempotent - safe to run multiple times)
    queue = await channel.declare_queue("task_queue", durable=True)

    print(" [*] Waiting for messages. To exit press CTRL+C", flush=True)

    # Start consuming
    await queue.consume(on_message)

    # Keep running script
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
