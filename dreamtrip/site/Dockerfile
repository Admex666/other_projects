FROM python:3.11-slim

# Chrome telepítése (modern módszer)
RUN apt-get update && apt-get install -y wget gnupg unzip curl
RUN wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y /tmp/google-chrome.deb
RUN rm /tmp/google-chrome.deb
RUN rm -rf /var/lib/apt/lists/*

# ChromeDriver telepítése
RUN wget -O /tmp/chromedriver-linux64.zip https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.204/linux64/chromedriver-linux64.zip
RUN unzip /tmp/chromedriver-linux64.zip -d /tmp/
RUN mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/
RUN chmod +x /usr/local/bin/chromedriver
RUN rm -rf /tmp/chromedriver*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]