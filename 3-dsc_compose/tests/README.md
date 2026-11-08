# Request handling tests

From the repository root, in a Python 3.11 virtual environment:

```bash
python -m pip install -r 3-dsc_compose/tests/requirements.txt
python -m unittest discover -s 3-dsc_compose/tests -v
```

These tests exercise the FastAPI upload endpoint and the frontend's handling of
successful responses, HTTP errors, connection failures, timeouts, and invalid
image responses. Model inference and Streamlit rendering are mocked; no model
downloads, Docker daemon, or running backend are needed.
