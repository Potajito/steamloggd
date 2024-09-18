# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any necessary dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install-deps
RUN playwright install

# Run app.py when the container launches
CMD ["python", "app.py"]