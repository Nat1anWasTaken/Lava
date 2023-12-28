FROM python:3.12.1-slim

COPY requirements.txt .
RUN apt-get update
RUN apt-get install -y git curl jq gcc
RUN pip install --user -r /requirements.txt

COPY . .

CMD ["bash", "/script/run.sh"]
