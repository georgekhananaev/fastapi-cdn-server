from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import FileResponse
from PIL import Image
import os
from io import BytesIO
from pathlib import Path
import httpx
from urllib.parse import urlparse, unquote

app = FastAPI()

# Settings
CACHE_DIR = 'images'
IMAGE_SIZES = {
    "small": 320,
    "medium": 640,
    "large": 1280
}
os.makedirs(CACHE_DIR, exist_ok=True)


@app.post("/cache_image")
async def cache_image(url: str = Form(...)):
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL parameter")

    try:
        parsed_url = urlparse(url)
        original_path = unquote(parsed_url.path.lstrip('/'))
        file_extension = os.path.splitext(original_path)[1]

        async with httpx.AsyncClient() as client:
            response = await client.get(url)

        if response.status_code == 200:
            for size_name, width in IMAGE_SIZES.items():
                image = Image.open(BytesIO(response.content))
                image.thumbnail((width, width))
                image_path = Path(CACHE_DIR) / f"{size_name}_{original_path}"
                image_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(image_path, format=image.format)

            return {"message": "Image cached and resized successfully",
                    "cachedUrls": [str(Path(CACHE_DIR) / f"{size_name}_{original_path}") for size_name in IMAGE_SIZES]}
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch image from URL")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


# Serve cached images
@app.get("/cache_data/{file_path:path}")
async def serve_cached_image(file_path: str):
    file_location = Path(CACHE_DIR) / file_path
    if file_location.is_file():
        return FileResponse(str(file_location))
    else:
        raise HTTPException(status_code=404, detail="File not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
