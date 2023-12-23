import aiofiles
from fastapi import FastAPI, HTTPException, Response, Form, UploadFile, Depends, security
from fastapi.responses import FileResponse
from PIL import Image
import os
from io import BytesIO
from pathlib import Path
import httpx
from urllib.parse import urlparse, unquote
import redis
import asyncio
from dotenv import load_dotenv
from config import *
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

load_dotenv()

# Configure CORS settings
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Create an instance of HTTPBearer
http_bearer = security.HTTPBearer()
security_basic = HTTPBasic()
SECRET_KEY = os.getenv('bearer_secret_key')


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security_basic)):
    correct_username = os.getenv('swagger_ui_username')
    correct_password = os.getenv('swagger_ui_password')
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return credentials


def get_secret_key(security_payload: security.HTTPAuthorizationCredentials = Depends(http_bearer)):
    authorization = security_payload.credentials
    if not authorization or SECRET_KEY not in authorization:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return authorization


# Create default folder
os.makedirs(CACHE_DIR, exist_ok=True)

# Initialize Redis client
REDIS_CONNECTED = False
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    # Test the connection
    redis_client.ping()
    REDIS_CONNECTED = True
    print("Successfully connected to Redis.")
except redis.exceptions.ConnectionError:
    print("Failed to connect to Redis. memory operations will be skipped.")


def store_image_in_redis(file_path, image_content):
    """ Store image content in Redis """
    if REDIS_CONNECTED and EXPIRATION_SECONDS > 0:
        redis_key = get_redis_key(file_path)
        redis_client.setex(redis_key, EXPIRATION_SECONDS, image_content)


def get_redis_key(file_path):
    """ Generate a Redis key with a namespace prefix """
    return f"{REDIS_KEY_PREFIX}{file_path}"


def update_file_access(file_path):
    """ Update the last access time of a file in Redis """
    if REDIS_CONNECTED and EXPIRATION_SECONDS > 0:
        redis_key = get_redis_key(file_path)
        redis_client.setex(redis_key, EXPIRATION_SECONDS, 'accessed')


async def delete_expired_files():
    """ Periodically check and delete files not present in Redis and remove empty folders """
    while True:
        await asyncio.sleep(60 * 60 * 24)  # Checking files to remove once a day.
        if REDIS_CONNECTED and EXPIRATION_SECONDS > 0:
            # Scan all files in the cache_data directory
            for root, dirs, files in os.walk(CACHE_DIR):
                for file in files:
                    file_path = Path(root) / file
                    redis_key = get_redis_key(str(file_path))

                    # If the Redis key does not exist, delete the file
                    if not redis_client.exists(redis_key):
                        try:
                            os.remove(file_path)
                            print(f"Deleted file, not exist inside Redis: {file_path}")
                        except OSError as e:
                            print(f"Error deleting file {file_path}: {e}")
                    else:
                        print("Skipped deletion of", {file_path})

                # Remove empty directories
                for dir in dirs:  # noqa
                    dir_path = Path(root) / dir
                    if not os.listdir(dir_path):
                        try:
                            os.rmdir(dir_path)
                            print(f"Deleted empty directory: {dir_path}")
                        except OSError as e:
                            print(f"Error deleting directory {dir_path}: {e}")


@app.on_event("startup")
async def startup_event():
    if not STORE_CACHE_IN_MEMORY and REDIS_CONNECTED and EXPIRATION_SECONDS > 0:
        asyncio.create_task(delete_expired_files())
    else:
        print(
            "Skipping cache removal due to Redis connection issues or EXPIRATION_SECONDS = 0")


@app.post("/upload_image", dependencies=[Depends(get_secret_key)])
async def upload_image_file(file: UploadFile, overwrite: bool = False):
    # Check if the folder exists
    if not os.path.exists(FILES_DIR):
        # If not, create it
        os.makedirs(FILES_DIR, exist_ok=True)

    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File extension '{file_extension}' is not allowed")

    file_location = Path(FILES_DIR) / file.filename if not STORE_CACHE_IN_MEMORY else file.filename

    # Check if file exists and overwrite is False
    if not overwrite and os.path.exists(file_location):
        return {"message": "File exists and overwrite is False", "file_path": str(file_location)}

    file_content = await file.read()  # Read file content

    if STORE_CACHE_IN_MEMORY:
        store_image_in_redis(str(file_location), file_content)
        return {"message": "File uploaded and stored in memory", "file_path": str(file_location)}
    else:
        async with aiofiles.open(file_location, 'wb') as out_file:
            await out_file.write(file_content)  # Write to file
        update_file_access(str(file_location))
        return {"message": "File uploaded successfully", "file_path": str(file_location)}


@app.post("/cache_url", dependencies=[Depends(get_secret_key)])
async def cache_image_from_url(url: str = Form(...), overwrite: bool = False):
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL parameter")

    try:
        parsed_url = urlparse(url)
        original_path = unquote(parsed_url.path.lstrip('/'))
        # file_extension = os.path.splitext(original_path)[1]

        async with httpx.AsyncClient() as client:
            response = await client.get(url)

        if response.status_code == 200:
            for size_name, width in IMAGE_SIZES.items():
                image_filename = f"{size_name}_{original_path}"
                image_path = Path(CACHE_DIR) / image_filename if not STORE_CACHE_IN_MEMORY else image_filename
                # print(image_path)

                if STORE_CACHE_IN_MEMORY:
                    redis_key = get_redis_key(str(image_path))
                    if redis_client.exists(redis_key) and not overwrite:
                        continue
                    image = Image.open(BytesIO(response.content))
                    image.thumbnail((width, width))
                    image_bytes = BytesIO()
                    image.save(image_bytes, format=image.format)
                    store_image_in_redis(str(image_path), image_bytes.getvalue())
                else:
                    if image_path.exists() and not overwrite:
                        print(image_path)
                        update_file_access(str(image_path))
                        return {"message": "File exists and overwrite is False",
                                "cachedUrls": [str(Path(CACHE_DIR) / f"{size_name}_{original_path}") for size_name in
                                               IMAGE_SIZES] if not STORE_CACHE_IN_MEMORY else [
                                    f"{size_name}_{original_path}" for
                                    size_name in IMAGE_SIZES]}

                    image = Image.open(BytesIO(response.content))
                    image.thumbnail((width, width))
                    image_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(image_path, 'wb') as out_file:
                        image.save(out_file, format=image.format)
                    update_file_access(str(image_path))

            return {"message": "Image cached and resized successfully",
                    "cachedUrls": [str(Path(CACHE_DIR) / f"{size_name}_{original_path}") for size_name in
                                   IMAGE_SIZES] if not STORE_CACHE_IN_MEMORY else [f"{size_name}_{original_path}" for
                                                                                   size_name in IMAGE_SIZES]}
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch image from URL")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.get("/cache_data/{file_path:path}")
async def serve_cached_image(file_path: str):
    if STORE_CACHE_IN_MEMORY:
        redis_key = get_redis_key(file_path)
        image_content = redis_client.get(redis_key)
        if image_content:
            update_file_access(redis_key)
            return Response(content=image_content, media_type="image/*")
        else:
            raise HTTPException(status_code=404, detail="File not found")
    else:
        file_location = Path(CACHE_DIR) / file_path
        if file_location.is_file():
            update_file_access(str(file_location))
            return FileResponse(str(file_location))
        else:
            raise HTTPException(status_code=404, detail="File not found")


@app.delete("/clear_redis_cache", dependencies=[Depends(get_secret_key)])
async def clear_redis_cache():
    """
    Clear all keys in the Redis cache for the application namespace.
    """
    try:
        # Scan and delete all keys with the application's namespace prefix
        for key in redis_client.scan_iter(f"{REDIS_KEY_PREFIX}*"):
            await redis_client.delete(key)
        return {"message": "Redis cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing Redis cache: {str(e)}")


@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint(credentials: HTTPBasicCredentials = Depends(verify_credentials)):  # noqa
    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title="FastAPI CDN Server",
        version="v1.00",
        contact={
            "name": "George Khananaev",
            "url": "https://george.khananaev.com",
        },
        description="""FastAPI-based image caching and resizing server with Redis integration for efficient file management. 
              Automatically resizes images into multiple sizes, manages expiration, and supports conditional overwriting. 
              Ideal for dynamic web applications and content management systems.""",
        routes=app.routes,
    )

    return openapi_schema


@app.get("/docs", include_in_schema=False)
async def custom_docs_url(credentials: HTTPBasicCredentials = Depends(verify_credentials)):  # noqa
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(openapi_url="/openapi.json", title=app.title)  # noqa


@app.get("/redoc", include_in_schema=False)  # noqa
async def custom_redoc_url(credentials: HTTPBasicCredentials = Depends(verify_credentials)):  # noqa
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(openapi_url="/openapi.json", title=app.title)  # noqa


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
