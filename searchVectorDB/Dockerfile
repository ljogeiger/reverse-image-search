FROM python:3.11
COPY . .
RUN pip install -r requirements.txt
RUN make ./app
CMD python ./app/main.py