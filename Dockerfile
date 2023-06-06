FROM python:3.10-buster
WORKDIR /backend
COPY requirements.txt /backend
RUN pip install -r requirements.txt
COPY . /backend/
EXPOSE 8000
CMD ["python3", "manage.py", "runserver"] 