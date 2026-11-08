import time
from starlette.responses import StreamingResponse

import cv2
import uvicorn
import io
from fastapi import File, HTTPException
from fastapi import FastAPI
from fastapi import UploadFile
import numpy as np
from PIL import Image, UnidentifiedImageError

import config
import inference


app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Welcome from the API!"}


async def combine_images(output, resized, name):
    final_image = np.hstack((output, resized))
    cv2.imwrite(name, final_image)


@app.post("/{style}")
async def get_image(style: str, file: UploadFile = File(...)):
    if style not in config.STYLES:
        raise HTTPException(status_code=404, detail="Unknown style")

    try:
        with Image.open(file.file) as uploaded_image:
            image = np.array(uploaded_image.convert("RGB"))
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="Upload a valid image")

    model = config.STYLES[style]
    start = time.time()
    output, resized = inference.inference(model, image)
    res, img = cv2.imencode(".png", output)
    return StreamingResponse(io.BytesIO(img.tobytes()), media_type="image/png")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=80)
