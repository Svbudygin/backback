FROM python:3.12

WORKDIR /app

COPY requirements.txt ./

#RUN apk add libpq-dev python3-dev postgresql postgresql-dev && pip install --upgrade pip && pip install setuptools wheel && pip install --no-cache-dir -r requirements.txt

# RUN apt install libpq-dev python3-dev postgresql postgresql-dev && pip install --upgrade pip && pip install setuptools wheel && pip install --no-cache-dir -r requirements.txt


RUN pip install --upgrade pip && pip install setuptools wheel && pip install --no-cache-dir -r requirements.txt


COPY . .


# CMD ["sleep","1000000"]

CMD ["fastapi", "run", "app/main.py", "--port", "8000", "--workers", "2"]

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--loop", "uvloop","--log-level","debug"]

# CMD [ "flask", "run" , "-h", "0.0.0.0", "-p", "8080"]
