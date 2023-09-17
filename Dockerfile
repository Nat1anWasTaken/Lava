FROM python:3.11.5-slim

COPY requirements.txt .
RUN apt-get update
RUN apt-get install -y git curl jq
RUN pip install --user -r /requirements.txt

COPY . .

CMD ["bash", "/script/run.sh"]
