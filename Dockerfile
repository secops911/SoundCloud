# Use an official Python image as the base
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the project files to the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port (optional, depending on the script)
EXPOSE 8080

# Command to run the script
CMD ["python3", "SoundCloud.py"]

