# Use the official Python 3.8 slim image as the base image
# https://hub.docker.com/_/python
#
# The slim variant of the Python image doesn't have the common packages
# installed in the regular Python image, like git, bash, and others.
# This makes the slim image smaller in size.
# The slim image is recommended for production use.
# see https://pythonspeed.com/articles/base-image-python-docker-images/
FROM python:3.8-slim

# Set the working directory in the container to /app
# This means all the subsequent commands will be run in the /app directory
# It also sets the working directory for the application
WORKDIR /app

# Update the package list
RUN apt-get update

# Install ffmpeg, libsm6, and libxext6 packages
# They are required to use OpenCV
RUN apt-get install 'ffmpeg'\
    'libsm6'\
    'libxext6'  -y

# Copy the requirements.txt file into the container at /app
COPY requirements.txt .

# Install the Python dependencies specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Set the default port; docker run -e or Compose can override it at runtime.
ENV STREAMLIT_SERVER_PORT=8501
# Document the default port. EXPOSE does not configure or publish the server.
EXPOSE 8501

# Run the Streamlit application
CMD ["streamlit", "run", "main.py"]
