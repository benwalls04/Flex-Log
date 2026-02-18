from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
)

from constructs import Construct
import os

class RecServiceStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # Reference existing S3 bucket for models
        models_bucket = s3.Bucket.from_bucket_name(
            self, "ModelsBucket",
            "flexlog-models"
        )
        
        # Create Lambda function from Docker image
        function = lambda_.DockerImageFunction(
            self, "RecommendationFunction",
            code=lambda_.DockerImageCode.from_image_asset(
                os.path.join(os.path.dirname(__file__), "..", "image")
            ),
            memory_size=3008, 
            timeout=Duration.minutes(15), 
            environment={
                "DB_SECRET_NAME": "dev/supabase"

            }
        )
        
        # Grant Secrets Manager access to Lambda
        # Grant Secrets Manager access to Lambda
        db_secret = secretsmanager.Secret.from_secret_complete_arn(
            self, "SupabaseSecret",
            "arn:aws:secretsmanager:us-east-1:471112794843:secret:dev/supabase-S2mbfc"
        )
        db_secret.grant_read(function)

        redis_secret = secretsmanager.Secret.from_secret_complete_arn(
            self, "RedisSecret",
            "arn:aws:secretsmanager:us-east-1:471112794843:secret:dev/Redis-cvlyE8"
        )
        redis_secret.grant_read(function)

        models_bucket.grant_read_write(function)