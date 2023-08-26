FROM python:3.11.5-slim as base

FROM base as builder

COPY requirements.txt .
RUN apt-get update
RUN apt-get install -y git
RUN pip install --user -r /requirements.txt

FROM base

RUN apt-get update
RUN apt-get install -y curl jq
COPY --from=builder /root/.local /root/.local
COPY . .

CMD ["bash", "/script/run.sh"]
