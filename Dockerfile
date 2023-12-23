# Use the official Python image with slim version
FROM python:3.12.1-slim

# Set the working directory
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt /app/

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies
RUN pip install -r requirements.txt

# Copy the application code into the container
COPY . /app/

# Replace 'localhost' with 'redis' in config.py
RUN sed -i "s/REDIS_HOST = 'localhost'/REDIS_HOST = 'redis'/g" config.py


# Expose the port that your application will run on
EXPOSE 8080

# Start uvicorn with specified parameters
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]