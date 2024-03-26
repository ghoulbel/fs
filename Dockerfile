FROM python:3.9

WORKDIR /app

COPY . /data

COPY fs.py .

#CMD ["python", "fs.py", "data/IN/", "data/OUT/", "500", "200"]
