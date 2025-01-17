FROM public.ecr.aws/lambda/python:3.13

COPY cat5 ./cat5
COPY processor ./processor
COPY requirements.txt ./

RUN dnf -y install git

RUN pip install -r requirements.txt --no-cache-dir --root-user-action ignore -t .

CMD ["processor.handler.lambda_handler"]
