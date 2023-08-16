import logging
# import os
# import boto3
# import sqlalchemy

LOG_FMT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FMT)
logger = logging.getLogger(__name__)

# s3 = boto3.resource('s3',
#     endpoint_url=os.getenv('S3_ENDPOINT'),
#     aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
#     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
# )
# bucket = s3.Bucket(os.getenv('BUCKET_NAME'))

# PGUSER = os.getenv('POSTGRES_USER')
# PGPASSWORD = os.getenv('POSTGRES_PASSWORD')
# PGHOST = os.getenv('POSTGRES_HOST')
# PGDB = os.getenv('POSTGRES_DB')
# engine = sqlalchemy.create_engine(
#     f'postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}/{PGDB}', pool_pre_ping=True)

