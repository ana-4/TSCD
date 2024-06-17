import boto3
import os
import json
import logging
import radon.complexity as radon_complexity
import radon.raw as radon_raw
from radon.complexity import cc_rank, cc_visit
import ast

s3_client = boto3.client('s3')

dynamodb = boto3.resource('dynamodb')
table_name = 'CodeQualityMetrics'
table = dynamodb.Table(table_name)

s3_bucket = os.environ['S3_BUCKET']

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def analyze_code(code):
    metrics = {
        'cyclomatic_complexity': [],
        'lines_of_code': 0,
        'number_of_classes': 0,
        'number_of_functions': 0,
    }

    # Analyze Cyclomatic Complexity
    try:
        blocks = radon_complexity.cc_visit(code)
        metrics['cyclomatic_complexity'] = [block.complexity for block in blocks]
    except Exception as e:
        logger.error(f"Error analyzing cyclomatic complexity: {e}")

    # Analyze Lines of Code
    try:
        loc = radon_raw.analyze(code)
        metrics['lines_of_code'] = loc.loc
    except Exception as e:
        logger.error(f"Error analyzing lines of code: {e}")

    # Analyze Number of Classes and Functions
    try:
        tree = ast.parse(code)
        metrics['number_of_classes'] = sum(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
        metrics['number_of_functions'] = sum(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
    except Exception as e:
        logger.error(f"Error analyzing classes and functions: {e}")

    return metrics


def save_metrics_to_dynamodb(repo_name, metrics):
    try:
        logger.info(f"Inserting metrics into DynamoDB for repo: {repo_name}")
        table.put_item(
            Item={
                'repo_name': repo_name,
                'metrics': metrics
            }
        )
    except Exception as e:
        logger.error(f"Error saving metrics to DynamoDB: {e}")
        raise


def lambda_handler(event, context):
    repo_name = event.get('repo_name')
    s3_key = event.get('s3_key')

    if not repo_name or not s3_key:
        return {
            'statusCode': 400,
            'body': json.dumps('Repository name and S3 key must be provided')
        }

    try:
        logger.info(f"Fetching file {s3_key} from bucket {s3_bucket}")
        response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        code = response['Body'].read().decode('utf-8')

        logger.info(f"Analyzing code from {s3_key}")
        metrics = analyze_code(code)

        s3_client.put_object(
            Bucket=s3_bucket,
            Key=f"analysis-results/{repo_name}-metrics.json",
            Body=json.dumps(metrics)
        )

        save_metrics_to_dynamodb(repo_name, metrics)

        return {
            'statusCode': 200,
            'body': json.dumps('Code analysis completed successfully')
        }

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error occurred: {str(e)}")
        }
