from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_sqs as sqs,
    aws_lambda_event_sources as event_sources,
)

from constructs import Construct
import os

from dotenv import load_dotenv

# Env keys passed from .env to Lambdas (same keys as in .env)
_LAMBDA_ENV_KEYS = [
    "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
    "REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD",
]

def _get_lambda_env() -> dict:
    _rec_service_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(_rec_service_root, ".env"))
    return {k: os.environ.get(k, "") for k in _LAMBDA_ENV_KEYS}


class RecServiceStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        lambda_env = _get_lambda_env()

        # Reference existing S3 bucket for models
        models_bucket = s3.Bucket.from_bucket_name(
            self, "ModelsBucket",
            "flexlog-models"
        )

        # Create Lambda function from Docker image
        _rec_service_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        read_function = lambda_.DockerImageFunction(
            self, "Read",
            code=lambda_.DockerImageCode.from_image_asset(
                _rec_service_root,
                file=os.path.join("src", "read", "Dockerfile"),
            ),
            memory_size=3008,
            timeout=Duration.minutes(5),
            environment=lambda_env,
        )

        worker_function = lambda_.DockerImageFunction(
            self, "Worker",
            code=lambda_.DockerImageCode.from_image_asset(
                _rec_service_root,
                file=os.path.join("src", "worker", "Dockerfile"),
            ),
            memory_size=3008,
            timeout=Duration.minutes(15),
            environment=lambda_env,
        )

        recommendation_queue = sqs.Queue.from_queue_arn(
            self, "RecommendationQueue",
            "arn:aws:sqs:us-east-1:471112794843:flexlogRecQueue"
        )

        worker_function.add_event_source(
            event_sources.SqsEventSource(
                recommendation_queue,
                batch_size=1,
            )
        )

        models_bucket.grant_read_write(read_function)
        models_bucket.grant_read_write(worker_function)