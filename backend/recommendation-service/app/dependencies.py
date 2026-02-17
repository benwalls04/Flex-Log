from contextlib import asynccontextmanager
from fastapi import FastAPI
import boto3
import redis
from psycopg2.pool import SimpleConnectionPool
import os
import json

class AppState:
    def __init__(self):
        self.s3_client = None
        self.redis_client = None
        self.db_pool = None
        self.db_config = None
        self.supabase_secret = None
        self.redis_secret = None

app_state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    region_name = os.environ.get('AWS_REGION', 'us-east-1')
    db_secret_name = os.environ.get('DB_SECRET_NAME', 'dev/supabase')
    redis_secret_name = os.environ.get('REDIS_SECRET_NAME', 'dev/Redis')
    
    secrets_client = boto3.client('secretsmanager', region_name=region_name)
    db_secret_response = secrets_client.get_secret_value(SecretId=db_secret_name)
    app_state.supabase_secret = json.loads(db_secret_response['SecretString'])
    redis_secret_response = secrets_client.get_secret_value(SecretId=redis_secret_name)
    app_state.redis_secret = json.loads(redis_secret_response['SecretString'])

    app_state.s3_client = boto3.client('s3', region_name=region_name)
    
    app_state.db_config = {
        "host": app_state.supabase_secret["DB_HOST"],
        "port": int(app_state.supabase_secret.get("DB_PORT", 6543)),
        "database": app_state.supabase_secret.get("DB_NAME", "postgres"),
        "user": app_state.supabase_secret["DB_USER"],
        "password": app_state.supabase_secret["DB_PASSWORD"],
        "sslmode": "require",
        "connect_timeout": 15
    }
    
    try:
        app_state.db_pool = SimpleConnectionPool(
            minconn=2,     
            maxconn=10,   
            **app_state.db_config
        )
    except Exception as e:
        print(f"Failed to create database pool: {e}")
        raise
    
    try:
        app_state.redis_client = redis.Redis(
            host=app_state.redis_secret.get("REDIS_HOST"),
            port=int(app_state.redis_secret.get("REDIS_PORT", 6379)),
            password=app_state.redis_secret.get("REDIS_PASSWORD"),
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30
        )
        app_state.redis_client.ping()
    except Exception as e:
        print(f"Failed to initialize Redis: {e}")
        raise
        
    yield  # Application runs here
        
    if app_state.db_pool:
        try:
            app_state.db_pool.closeall()
        except Exception as e:
            print(f"Error closing database pool: {e}")
    
    if app_state.redis_client:
        try:
            app_state.redis_client.close()
        except Exception as e:
            print(f"Error closing Redis client: {e}")
    

def get_db_connection():
    if not app_state.db_pool:
        raise RuntimeError("Database pool not initialized")
    return app_state.db_pool.getconn()


def release_db_connection(conn):
    if app_state.db_pool and conn:
        app_state.db_pool.putconn(conn)


def get_s3_client():
    if not app_state.s3_client:
        raise RuntimeError("S3 client not initialized")
    return app_state.s3_client


def get_redis_client():
    if not app_state.redis_client:
        raise RuntimeError("Redis client not initialized")
    return app_state.redis_client


def get_db_config():
    if not app_state.db_config:
        raise RuntimeError("Database config not initialized")
    return app_state.db_config
