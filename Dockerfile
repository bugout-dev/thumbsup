FROM python:3.8.3-buster

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "gunicorn", "--bind", "0.0.0.0:5000", "thumbsup.server:app" ]
CMD []
