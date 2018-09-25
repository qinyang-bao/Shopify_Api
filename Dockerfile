FROM python:3.6-alpine

RUN adduser -D shopify

WORKDIR /home/shopify

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

COPY App App
COPY migrations migrations
COPY Shopify.py config.py app.db init_db.py .env boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP Shopify.py

RUN chown -R shopify:shopify ./
USER shopify

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
