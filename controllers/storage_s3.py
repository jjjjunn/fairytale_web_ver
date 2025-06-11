# s3 용 함수
import boto3
import requests
from io import BytesIO

def save_image_s3(image_url: str, bucket_name: str, object_name: str) -> str:
    s3 = boto3.client("s3")
    response = requests.get(image_url)
    s3.upload_fileobj(BytesIO(response.content), bucket_name, object_name)
    return f"https://{bucket_name}.s3.amazonaws.com/{object_name}"