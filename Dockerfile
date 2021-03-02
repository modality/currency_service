FROM python:3.8.6

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app
RUN pip install -v -r requirements.txt
COPY . /usr/src/app

# This is required for the Flask cli
ENV FLASK_APP app.py

CMD flask run --host=0.0.0.0
