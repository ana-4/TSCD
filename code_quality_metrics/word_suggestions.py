import boto3
import os
import json
import re
import logging

s3_client = boto3.client('s3')

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = 'WordSuggestions'
table = dynamodb.Table(table_name)

s3_bucket = os.environ['S3_BUCKET']

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def extract_context(code):
    variables = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', code)
    function_names = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', code)
    comments = re.findall(r'#\s*(.*)', code)

    context = {
        'variables': set(variables),
        'functions': set(function_names),
        'comments': comments
    }
    return context

def suggest_improvements(context):
    suggestions = []

    for var in context['variables']:
        if len(var) < 3 or re.match(r'^[a-zA-Z]$', var):
            suggestions.append(f"Consider using a more descriptive variable name instead of '{var}'.")

    for comment in context['comments']:
        if 'fixme' in comment.lower():
            suggestions.append(f"Address the issue mentioned in the comment: '{comment}'")
        if 'todo' in comment.lower():
            suggestions.append(f"Complete the task mentioned in the comment: '{comment}'")

    for func in context['functions']:
        if not re.match(r'[a-z][a-zA-Z0-9]*', func):
            suggestions.append(f"Function name '{func}' should be in snake_case.")

    return suggestions

def analyze_code(code):
    context = extract_context(code)
    suggestions = suggest_improvements(context)
    return suggestions

def save_suggestions_to_dynamodb(context_text, suggestions):
    try:
        logger.info(f"Inserting suggestions into DynamoDB for context: {context_text}")
        table.put_item(
            Item={
                'context': context_text,
                'suggestions': json.dumps(suggestions)
            }
        )
    except Exception as e:
        logger.error(f"Error saving suggestions to DynamoDB: {e}")
        raise

def lambda_handler(event, context):
    context_text = event.get('context_text', '')

    if not context_text:
        return {
            'statusCode': 400,
            'body': json.dumps('context_text must be provided')
        }

    try:
        logger.info(f"Analyzing code for context: {context_text}")
        suggestions = analyze_code(context_text)

        save_suggestions_to_dynamodb(context_text, suggestions)

        return {
            'statusCode': 200,
            'body': json.dumps({'suggestions': suggestions})
        }

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error occurred: {str(e)}")
        }
