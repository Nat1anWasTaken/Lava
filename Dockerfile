FROM python:3.10.9-alpine3.17
COPY . .
RUN apk add git
RUN pip install -r /requirements.txt
CMD [ "python", "main.py" ]