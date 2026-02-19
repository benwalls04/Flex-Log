FROM public.ecr.aws/lambda/python:3.12

COPY src/shared/core.py ${LAMBDA_TASK_ROOT}
COPY src/worker/main.py ${LAMBDA_TASK_ROOT}
COPY src/worker/requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD [ "main.handler" ]
