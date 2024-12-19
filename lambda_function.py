import json
from src.main import process_query  # Adjust this import if your structure changes


def lambda_handler(event, context):
    """
    AWS Lambda entry point.

    AWS Lambda always expects the handler function to accept two arguments:

    event: Contains the input data passed to the function (e.g., API Gateway request, S3 event, etc.).
    context: Contains runtime information about the execution environment, such as memory limits, function name, request ID, etc.
    Even if you don’t use context, AWS requires your function to accept it. Can be used for timeout, debug logs etc
    """
    query = event.get("query", "")
    if not query:
        return {"statusCode": 400, "body": json.dumps({"error": "Query not provided"})}

    try:
        result = process_query(query)
        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

if __name__ == "__main__":
    # Simulate an AWS Lambda event
    event = {
        "query": "Find candidates with Python and TensorFlow skills OR a BSc degree in Software Engineering"
    }
    context = {}  # Lambda context is not needed for basic testing

    # Call the handler function
    response = lambda_handler(event, context)
    print("Lambda Response:")
    print(json.dumps(response, indent=4))