FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV STREAMLIT_SERVER_PORT=8501
EXPOSE 8501

CMD ["streamlit", "run", "main.py"]
