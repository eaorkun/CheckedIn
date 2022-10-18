"""Module for all AWS Stuff """
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_KEY = os.environ["AWS_ACCESS_KEY"]
SECRET_KEY = os.environ["AWS_SECRET_KEY"]

# Resources/ Clients
dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="us-east-1",
)
dynamo_client = boto3.client(
    "dynamodb",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="us-east-1",
)
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY"],
    aws_secret_access_key=os.environ["AWS_SECRET_KEY"],
    region_name="us-east-1",
)
# Tables
user_table = dynamodb.Table("checkedinusers")
org_table = dynamodb.Table("checkedinorgs")
event_table = dynamodb.Table("checkedinevents")


# S3 Buckets
s3_dataset_bucket = "hack-tx-files"
s3_dataset_url = f"https://{s3_dataset_bucket}.s3.us-east-1.amazonaws.com/"