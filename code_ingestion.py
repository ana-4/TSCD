import boto3
import json
import os
import requests
from zipfile import ZipFile
import io

# Initialize the S3 client
s3_client = boto3.client('s3')


def lambda_handler(event, context):
    # The GitHub repository details should be passed in the event
    repo_owner = event.get('repo_owner')
    repo_name = event.get('repo_name')
    branch = event.get('branch', 'main')

    if not repo_owner or not repo_name:
        return {
            'statusCode': 400,
            'body': json.dumps('Repository owner and name must be provided')
        }

    # Construct the GitHub API URL to get the repository archive (zip file)
    github_url = f"https://github.com/{repo_owner}/{repo_name}/archive/{branch}.zip"

    try:
        # Fetch the repository archive from GitHub
        response = requests.get(github_url)

        if response.status_code == 200:
            # Read the zip file content
            zip_content = io.BytesIO(response.content)

            # Extract and upload each file in the zip to the S3 bucket
            with ZipFile(zip_content, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith('/'):
                        continue  # Skip directories

                    file_name = file_info.filename.split('/')[-1]
                    file_data = zip_ref.read(file_info)

                    # Upload to S3
                    s3_client.put_object(
                        Bucket=os.environ['S3_BUCKET'],
                        Key=f"{repo_name}/{file_name}",
                        Body=file_data
                    )

            return {
                'statusCode': 200,
                'body': json.dumps('Repository code successfully ingested')
            }
        else:
            return {
                'statusCode': response.status_code,
                'body': json.dumps('Failed to fetch repository archive from GitHub')
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error occurred: {str(e)}")
        }
