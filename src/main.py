import json
import boto3
import os

from src.models.profile_creation_agent import create_profiles_with_ai
from src.models.search_agent import interpret_query, filter_profiles


def list_files_in_s3(bucket_name, prefix="data/"):
    """
    List files in the S3 bucket while excluding unnecessary files.
    """
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    return [
        item['Key']
        for item in response.get('Contents', [])
        if not item['Key'].endswith('.zip')  # Ignore zip files
    ]


def download_data_from_s3(bucket_name, keys):
    """
    Downloads required data files from S3 to /tmp.

    Args:
    - bucket_name: The name of the S3 bucket.
    - keys: List of S3 keys to download.
    """
    s3 = boto3.client('s3')

    for key in keys: # keys are just s3 files
        local_path = f"/tmp/{os.path.basename(key)}"  # Extract file name from the key

        if not os.path.exists(local_path):  # Avoid redundant downloads
            try:
                s3.download_file(bucket_name, key, local_path)
                print(f"Downloaded {key} from {bucket_name} to {local_path}")
            except Exception as e:
                print(f"Failed to download {key}: {e}")


def process_query(query, bucket_name="faangai-data", local=False):
    """
    Core logic for processing a query.
    """
    if local:
        # Use local data directory
        data_directory = "data"
    else:
        # Dynamically list files in S3
        data_files = list_files_in_s3(bucket_name)
        download_data_from_s3(bucket_name, data_files)
        data_directory = "/tmp"

    # Read data and process
    profiles = create_profiles_with_ai(data_directory)
    criteria = interpret_query(query, profiles)

    if "error" in criteria:
        return {"error": "Failed to interpret query", "details": criteria["raw_content"]}

    matching_profiles = filter_profiles(profiles, criteria)
    return {"profiles": matching_profiles}


def lambda_handler(event, context):
    """
    AWS Lambda entry point.
    """
    query = event.get("query", "")
    if not query:
        return {"statusCode": 400, "body": json.dumps({"error": "Query not provided"})}

    try:
        result = process_query(query)
        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def main():
    """
    Local test entry point.
    """
    # Define test query
    query = "Find candidates with Python and TensorFlow skills OR a BSc degree in Software Engineering"

    # Run the query and display results
    result = process_query(query, local=True)  # Use local=True for testing
    print("\nQuery Results:")
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
