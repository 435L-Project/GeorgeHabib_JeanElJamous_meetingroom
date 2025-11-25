FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc

COPY . /app

RUN pip install --no-cache-dir -r users_service/requirements.txt
RUN pip install --no-cache-dir -r reviews_service/requirements.txt
RUN pip install --no-cache-dir -r rooms_service/requirements.txt
RUN pip install --no-cache-dir -r bookings_service/requirements.txt

CMD ["python"]