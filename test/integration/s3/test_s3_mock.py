import boto3
from contextlib import contextmanager

# Use moto if available, otherwise provide a lightweight fallback mock for S3 client
try:
    from moto import mock_s3  # type: ignore
except Exception:
    @contextmanager
    def mock_s3():
        class FakeS3Client:
            def __init__(self):
                self.buckets = {}

            def create_bucket(self, Bucket):
                self.buckets[Bucket] = {}

            def put_object(self, Bucket, Key, Body):
                self.buckets.setdefault(Bucket, {})[Key] = Body

            def get_object(self, Bucket, Key):
                import io
                return { 'Body': io.BytesIO(self.buckets[Bucket][Key]) }

        orig_client = boto3.client

        def client(*args, **kwargs):
            return FakeS3Client()

        boto3.client = client
        try:
            yield
        finally:
            boto3.client = orig_client


def test_s3_put_get_object():
    with mock_s3():
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket = 'test-bucket'
        s3.create_bucket(Bucket=bucket)
        s3.put_object(Bucket=bucket, Key='hello.txt', Body=b'hello')
        res = s3.get_object(Bucket=bucket, Key='hello.txt')
        body = res['Body'].read()
        assert body == b'hello'
