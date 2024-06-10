import boto3
import os
import json
import radon.complexity as radon_complexity
import radon.metrics as radon_metrics
import radon.raw as radon_raw
from radon.complexity import cc_rank, cc_visit
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData

# Initialize the S3 client
s3_client = boto3.client('s3')
s3_bucket = os.environ['S3_BUCKET']
db_endpoint = os.environ['RDS_ENDPOINT']

def analyze_code(code):
    metrics = {
        'cyclomatic_complexity': [],
        'lines_of_code': 0,
        'code_duplication': 0
    }

    # Analyze Cyclomatic Complexity
    complexity_results = cc_visit(code)
    for result in complexity_results:
        metrics['cyclomatic_complexity'].append({
            'name': result.name,
            'complexity': result.complexity,
            'rank': cc_rank(result.complexity)
        })

    # Analyze Lines of Code
    loc = radon_raw.analyze(code)
    metrics['lines_of_code'] = loc.loc

    # Dummy code duplication count (implement actual duplication detection if needed)
    metrics['code_duplication'] = 0

    return metrics

def save_metrics_to_db(repo_name, metrics):
    engine = create_engine(f'mysql+pymysql://masteruser:masterpassword@{db_endpoint}/MetricsDB')
    metadata = MetaData()

    metrics_table = Table('code_metrics', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('repo_name', String(255)),
        Column('metric_type', String(255)),
        Column('metric_value', String(255)),
    )

    conn = engine.connect()

    for metric_type, values in metrics.items():
        if isinstance(values, list):
            for value in values:
                conn.execute(metrics_table.insert().values(
                    repo_name=repo_name,
                    metric_type=metric_type,
                    metric_value=json.dumps(value)
                ))
        else:
            conn.execute(metrics_table.insert().values(
                repo_name=repo_name,
                metric_type=metric_type,
                metric_value=str(values)
            ))

    conn.close()

def lambda_handler(event, context):
    repo_name = event.get('repo_name')
    s3_key = event.get('s3_key')

    if not repo_name or not s3_key:
        return {
            'statusCode': 400,
            'body': json.dumps('Repository name and S3 key must be provided')
        }

    try:
        # Fetch code from S3
        response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        code = response['Body'].read().decode('utf-8')

        # Analyze code
        metrics = analyze_code(code)

        # Save metrics to S3
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=f"analysis-results/{repo_name}-metrics.json",
            Body=json.dumps(metrics)
        )

        # Save metrics to RDS
        save_metrics_to_db(repo_name, metrics)

        return {
            'statusCode': 200,
            'body': json.dumps('Code analysis completed successfully')
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error occurred: {str(e)}")
        }
