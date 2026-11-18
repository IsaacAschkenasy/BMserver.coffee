FROM python:3.14
WORKDIR /usr/local/app

# Install the application dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy in the source code
COPY src ./src
EXPOSE 5000

# Setup an app user so the container doesn't run as the root user
RUN useradd --create-home app
USER app

CMD ["gunicorn", "-c", "src/gunicorn.conf.py", "--chdir", "src", "app:app"]