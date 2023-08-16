FROM python:3.9-slim
    WORKDIR /code
    COPY ./requirements.txt /code/requirements.txt
    RUN pip install -r /code/requirements.txt

    COPY ./app /code/app
    ENTRYPOINT ["python", "app/index.py"]
    EXPOSE 80

