import time

import requests
import streamlit as st
from PIL import Image, UnidentifiedImageError
import io
import os

STYLES = {
    "candy": "candy",
    "composition 6": "composition_vii",
    "feathers": "feathers",
    "la_muse": "la_muse",
    "mosaic": "mosaic",
    "starry night": "starry_night",
    "the scream": "the_scream",
    "the wave": "the_wave",
    "udnie": "udnie",
}

env_backend_url = os.environ.get('APP_BACKEND_URL')

st.title("Style transfer web app")

if not env_backend_url:
    st.error("Set APP_BACKEND_URL to the backend URL before starting the frontend.")
    st.stop()

image = st.file_uploader("Choose an image")

style = st.selectbox("Choose the style", [i for i in STYLES.keys()])

if st.button("Style Transfer"):
    if image is not None and style is not None:
        files = {"file": image.getvalue()}
        try:
            response = requests.post(
                f"{env_backend_url.rstrip('/')}/{style}",
                files=files,
                timeout=(5, 120),
            )
            response.raise_for_status()
        except requests.Timeout:
            st.error("The backend timed out. Please try again.")
        except requests.RequestException:
            st.error("The backend could not process the image. Check that it is running and its models are available.")
        else:
            try:
                img = Image.open(io.BytesIO(response.content))
                img.load()
            except (UnidentifiedImageError, OSError):
                st.error("The backend returned an invalid image.")
            else:
                st.image(img)
