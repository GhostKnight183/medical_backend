FROM python:3.12.10

WORKDIR /medicalplaza

RUN pip install --upgrade pip wheel

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY python_app ./python_app
COPY .env .env

# Запускаем приложение
CMD ["python", "python_app/Backend/main.py"]
