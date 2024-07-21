FROM python:3.12

COPY ../requirements.txt .

RUN pip install -r requirements.txt

COPY src/pibot pibot

WORKDIR /pibot

ENTRYPOINT ["python", "run.py"]