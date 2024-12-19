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


def download_data_from_s3(bucket_name, files):
    """
    Downloads required data files from S3 to /tmp.
    """
    s3 = boto3.client('s3')
    for file in files:
        local_path = f"/tmp/{file}"
        if not os.path.exists(local_path):  # Avoid redundant downloads
            s3.download_file(bucket_name, file, local_path)


def process_query(query, bucket_name="faangai-data"):
    """
    Core logic for processing a query. Reusable by both main() and lambda_handler.
    """
    # Dynamically list files in S3
    data_files = list_files_in_s3(bucket_name)

    # Download files to /tmp
    download_data_from_s3(bucket_name, data_files)

    # Read data from /tmp
    data_directory = "/tmp"
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
    result = process_query(query)
    print("\nQuery Results:")
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
