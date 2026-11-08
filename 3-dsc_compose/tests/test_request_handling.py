import importlib.util
import io
import os
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
import numpy as np
from PIL import Image
import requests


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lab_backend", ROOT / "backend/main.py")
backend = importlib.util.module_from_spec(spec)
with patch.object(sys, "path", [str(ROOT / "backend"), *sys.path]):
    spec.loader.exec_module(backend)


def png_bytes(mode="RGB"):
    buffer = io.BytesIO()
    Image.new(mode, (8, 8)).save(buffer, format="PNG")
    return buffer.getvalue()


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(backend.app)
        self.addCleanup(self.client.close)

    def test_unknown_style_returns_404_without_running_inference(self):
        with patch.object(backend.inference, "inference") as infer:
            response = self.client.post(
                "/unknown", files={"file": ("input.png", png_bytes(), "image/png")}
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Unknown style")
        infer.assert_not_called()

    def test_invalid_upload_returns_400_without_running_inference(self):
        with patch.object(backend.inference, "inference") as infer:
            response = self.client.post(
                "/candy", files={"file": ("input.png", b"not an image", "image/png")}
            )
        self.assertEqual(response.status_code, 400)
        infer.assert_not_called()

    def test_missing_upload_returns_422(self):
        self.assertEqual(self.client.post("/candy").status_code, 422)

    def test_rgb_grayscale_and_rgba_uploads_return_png(self):
        output = np.zeros((8, 8, 3), dtype=np.uint8)
        for mode in ("RGB", "L", "RGBA"):
            with self.subTest(mode=mode), patch.object(
                backend.inference, "inference", return_value=(output, output)
            ) as infer:
                response = self.client.post(
                    "/candy", files={"file": ("input.png", png_bytes(mode), "image/png")}
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["content-type"], "image/png")
                self.assertEqual(Image.open(io.BytesIO(response.content)).size, (8, 8))
                self.assertEqual(infer.call_args[0][1].shape, (8, 8, 3))


class FrontendTests(unittest.TestCase):
    def setUp(self):
        self.streamlit = Mock()
        self.streamlit.file_uploader.return_value = io.BytesIO(png_bytes())
        self.streamlit.selectbox.return_value = "candy"
        self.streamlit.button.return_value = True

    def run_frontend(self, response=None, error=None):
        with patch.dict(sys.modules, {"streamlit": self.streamlit}), patch.dict(
            os.environ, {"APP_BACKEND_URL": "http://backend/"}
        ), patch("requests.post", return_value=response, side_effect=error) as post:
            runpy.run_path(str(ROOT / "frontend/main.py"))
        return post

    def test_success_displays_image_and_sets_timeout(self):
        response = Mock(content=png_bytes())
        post = self.run_frontend(response=response)
        self.assertEqual(post.call_args[0][0], "http://backend/candy")
        self.assertEqual(post.call_args[1]["timeout"], (5, 120))
        response.raise_for_status.assert_called_once_with()
        self.streamlit.image.assert_called_once()
        self.streamlit.error.assert_not_called()

    def test_http_error_is_not_decoded_as_an_image(self):
        response = Mock(content=b"Internal Server Error")
        response.raise_for_status.side_effect = requests.HTTPError("500")
        self.run_frontend(response=response)
        self.streamlit.error.assert_called_once()
        self.streamlit.image.assert_not_called()

    def test_timeouts_and_connection_failures_show_errors(self):
        for error in (requests.Timeout(), requests.ConnectionError()):
            with self.subTest(error=type(error).__name__):
                self.streamlit.reset_mock()
                self.run_frontend(error=error)
                self.streamlit.error.assert_called_once()
                self.streamlit.image.assert_not_called()

    def test_invalid_image_response_shows_error(self):
        self.run_frontend(response=Mock(content=b"not an image"))
        self.streamlit.error.assert_called_once()
        self.streamlit.image.assert_not_called()

    def test_missing_backend_url_shows_configuration_error(self):
        class StopFrontend(Exception):
            pass

        self.streamlit.stop.side_effect = StopFrontend
        with patch.dict(sys.modules, {"streamlit": self.streamlit}), patch.dict(
            os.environ, {}, clear=True
        ), patch("requests.post") as post, self.assertRaises(StopFrontend):
            runpy.run_path(str(ROOT / "frontend/main.py"))
        self.streamlit.error.assert_called_once()
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
