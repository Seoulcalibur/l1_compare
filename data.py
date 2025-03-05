import boto3
import pandas as pd
import json
from botocore.exceptions import ClientError
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for AWS configuration
aws_access_key_id = None
aws_secret_access_key = None
aws_bucket_name = None
aws_validator_file_name = None
region_name = None
s3_client = None


def initialize_aws(access_key=None, secret_key=None, bucket=None, validator_file=None, region='us-east-1'):
    """
    Initialize AWS configuration from provided parameters or environment variables

    Args:
        access_key (str, optional): AWS access key ID
        secret_key (str, optional): AWS secret access key
        bucket (str, optional): S3 bucket name
        validator_file (str, optional): Validator file name in S3
        region (str, optional): AWS region name
    """
    global aws_access_key_id, aws_secret_access_key, aws_bucket_name, aws_validator_file_name, region_name, s3_client

    # First try to use provided parameters
    aws_access_key_id = access_key or os.environ.get('AWS_ACCESS_KEY')
    aws_secret_access_key = secret_key or os.environ.get('AWS_SECRET_KEY')
    aws_bucket_name = bucket or os.environ.get('AWS_BUCKET_NAME')
    aws_validator_file_name = validator_file or os.environ.get('AWS_VALIDATOR_FILE_NAME')
    region_name = region or os.environ.get('AWS_REGION_NAME', 'us-east-1')

    # Check if we have the required credentials
    if not aws_access_key_id or not aws_secret_access_key or not aws_bucket_name:
        logger.warning("Missing AWS credentials. Please provide them as parameters or set environment variables.")
        return False

    # Initialize S3 client
    try:
        s3_client = boto3.client('s3',
                                 aws_access_key_id=aws_access_key_id,
                                 aws_secret_access_key=aws_secret_access_key,
                                 region_name=region_name)

        # Test connection by listing buckets
        s3_client.list_buckets()
        logger.info("AWS configuration initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize AWS: {e}")
        return False


def fetch_s3_object(file_name):
    """
    Fetch an object from S3 bucket

    Args:
        file_name (str): The key of the file in the S3 bucket

    Returns:
        The response object from S3 or None if an error occurs
    """
    if s3_client is None:
        logger.error("AWS not initialized. Call initialize_aws() first.")
        return None

    try:
        response = s3_client.get_object(Bucket=aws_bucket_name, Key=file_name)
        return response
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            logger.error(f"The file {file_name} does not exist in bucket {aws_bucket_name}")
        elif error_code == 'AccessDenied':
            logger.error(f"Access denied to file {file_name} in bucket {aws_bucket_name}")
        else:
            logger.error(f"Error retrieving file from S3: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error retrieving file from S3: {e}")
        return None

def fetch_json_data(file_name=None):
    """
    Fetch and parse JSON data from S3

    Args:
        file_name (str, optional): The file to fetch. Defaults to aws_validator_file_name.

    Returns:
        dict or None: The parsed JSON data or None if an error occurs
    """
    if s3_client is None:
        logger.error("AWS not initialized. Call initialize_aws() first.")
        return None

    if file_name is None:
        if aws_validator_file_name is None:
            logger.error("No file name provided and no default validator file name set")
            return None
        file_name = aws_validator_file_name

    response = fetch_s3_object(file_name)
    if response:
        try:
            json_data = response['Body'].read().decode('utf-8')
            data = json.loads(json_data)
            return data
        except Exception as e:
            logger.error(f"Error parsing JSON data: {e}")
            return None
    return None

def fetch_csv_data(file_name):
    """
    Fetch and parse CSV data from S3

    Args:
        file_name (str): The file to fetch

    Returns:
        pandas.DataFrame or None: The parsed CSV data or None if an error occurs
    """
    if s3_client is None:
        logger.error("AWS not initialized. Call initialize_aws() first.")
        return None

    response = fetch_s3_object(file_name)
    if response:
        try:
            # Read CSV directly from the response body
            df = pd.read_csv(response['Body'])
            return df
        except Exception as e:
            logger.error(f"Error parsing CSV data: {e}")
            return None
    return None

def fetch_tx_fee():
    """
    Fetch transaction fee data

    Returns:
        pandas.DataFrame or None: DataFrame with month, category, and gas_fees columns
    """
    if s3_client is None:
        logger.error("AWS not initialized. Call initialize_aws() first.")
        return None

    if aws_validator_file_name is None:
        logger.error("No validator file name set")
        return None

    try:
        data = fetch_json_data(aws_validator_file_name)
        if data:
            df = pd.DataFrame(data)
            if all(col in df.columns for col in ['month', 'category', 'gas_fees']):
                return df[['month', 'category', 'gas_fees']]
            else:
                missing_cols = [col for col in ['month', 'category', 'gas_fees'] if col not in df.columns]
                logger.error(f"Missing columns in data: {missing_cols}")
                return None
        return None
    except Exception as e:
        logger.error(f"Error processing transaction fee data: {e}")
        return None

def list_bucket_files(prefix=''):
    """
    List all files in the S3 bucket with an optional prefix

    Args:
        prefix (str, optional): Prefix to filter files. Defaults to ''.

    Returns:
        list or None: List of file names or None if an error occurs
    """
    if s3_client is None:
        logger.error("AWS not initialized. Call initialize_aws() first.")
        return None

    try:
        response = s3_client.list_objects_v2(Bucket=aws_bucket_name, Prefix=prefix)
        if 'Contents' in response:
            return [item['Key'] for item in response['Contents']]
        return []
    except Exception as e:
        logger.error(f"Error listing bucket files: {e}")
        return None

# Test the functions if run directly
if __name__ == "__main__":
    # Example usage
    print("Testing S3 functions...")

    # Replace these with your actual AWS credentials
    success = initialize_aws(
        access_key=AWS_ACCESS_KEY,
        secret_key=AWS_SECRET_KEY,
        bucket='seoulcalibur',
        validator_file='dune_query_4667263.json'
    )

    if success:
        # List files in the bucket
        files = list_bucket_files()
        print(f"Files in bucket: {files}")

        # Test fetching JSON data
        if aws_validator_file_name:
            json_data = fetch_json_data()
            if json_data:
                print(f"Successfully fetched JSON data from {aws_validator_file_name}")
                print(f"Data keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'Not a dictionary'}")
            else:
                print(f"Failed to fetch JSON data from {aws_validator_file_name}")

        # Test fetching transaction fee data
        tx_fee_data = fetch_tx_fee()
        if tx_fee_data is not None:
            print(f"Successfully fetched transaction fee data with shape: {tx_fee_data.shape}")
            print(tx_fee_data.head())
        else:
            print("Failed to fetch transaction fee data")
