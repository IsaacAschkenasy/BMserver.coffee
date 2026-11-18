FROM python:3.14
WORKDIR /usr/local/app
ENV DB_PATH=/usr/data/coffee/data.db

# Install the application dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy in the source code
COPY src ./src
EXPOSE 5000

# Setup an app user so the container doesn't run as the root user
RUN useradd --create-home app \
    && mkdir -p /usr/data/coffee \
    && chown app:app /usr/data/coffee
USER app

CMD ["gunicorn", "-c", "src/gunicorn.conf.py", "--chdir", "src", "app:app"]