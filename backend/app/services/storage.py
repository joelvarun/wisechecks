import boto3
from app.core.config import settings


def s3_client():
    return boto3.client(
        's3',
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
    )


def ensure_bucket():
    client = s3_client()
    buckets = [b['Name'] for b in client.list_buckets().get('Buckets', [])]
    if settings.minio_bucket not in buckets:
        client.create_bucket(Bucket=settings.minio_bucket)


def upload_bytes(key: str, content: bytes) -> str:
    client = s3_client()
    client.put_object(Bucket=settings.minio_bucket, Key=key, Body=content)
    return f's3://{settings.minio_bucket}/{key}'
