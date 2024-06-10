import boto3
import json
import os

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['DYNAMODB_TABLE']
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    try:
        # Extract context from the event
        context_text = event.get('context_text', '')
        if not context_text:
            return {
                'statusCode': 400,
                'body': json.dumps('context_text must be provided')
            }

        # Query DynamoDB for suggestions based on the context
        response = table.scan()
        suggestions = []

        for item in response['Items']:
            if context_text in item['context']:
                suggestions.append(item['suggestion'])

        return {
            'statusCode': 200,
            'body': json.dumps(suggestions)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error occurred: {str(e)}")
        }
