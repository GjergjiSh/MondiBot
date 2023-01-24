FROM python:3.10-slim-buster
RUN apt-get update && apt-get install ffmpeg -y
WORKDIR /bot
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN mkdir "/bot/logs/"
COPY . .
EXPOSE 5000
EXPOSE 6969
CMD ["python", "src/main.py"]