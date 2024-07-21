FROM python:3.12

COPY ../requirements.txt .

RUN pip install -r requirements.txt

COPY src/ .

# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1

#WORKDIR pibot/
CMD ["python", "-m", "pibot"]
#ENTRYPOINT ["python", "pibot"]