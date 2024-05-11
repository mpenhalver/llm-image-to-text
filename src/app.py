import boto3
import base64
import json
from botocore.exceptions import ClientError
import os


s3 = boto3.client('s3')

# Create a client for Amazon Bedrock
bedrock = boto3.client('bedrock-runtime')

def lambda_handler(event, context):

  input_bucket = os.environ['S3_BUCKET_INPUT'] 
  key = event['Records'][0]['s3']['object']['key']

  try:
    # Download JPEG image from S3
    image = s3.get_object(Bucket=input_bucket, Key=key)['Body'].read()

    # Convert to base64 encoding
    image_base64 = base64.b64encode(image).decode('utf-8')

    print(image_base64)

    # # Body for Claude v3 Sonnet
    body = json.dumps({
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 10000,
    "messages": [
        {
          "role": "user",
          "content": [
            {
              "type": "image",
              "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image_base64
              }
            },
            {
              "type": "text",
              "text": "Você é um assistente que realiza cadastro de pessoas desabrigadas de uma tragédia com base na imagem. Você deve identificar as informações disponíveis na imagem e organizá-las de forma estruturada separando em linhas e colunas."
            }
          ]
        }
      ]
    })
    # Parameters for Claude V3 sonnet
    model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
    accept = 'application/json'
    content_type = 'application/json'

    # Invoke Bedrock API
    response = bedrock.invoke_model(body=body, modelId=model_id, accept=accept, contentType=content_type)

    # Parse the response body
    response_body = json.loads(response.get('body').read())
    print(response_body)

    # Extract text
    text = response_body['content'][0]['text']
    
    # Save the text content to a local file
    temp_file_name = '/tmp/claude_output.txt'
    with open(temp_file_name, 'w') as file:
      file.write(text)

    # Upload to S3
    output_bucket = os.environ['S3_BUCKET_OUTPUT']
    s3_file_name = 'claude_output.txt'
    s3.upload_file(temp_file_name, output_bucket, s3_file_name)

   # Remove the temporary text file
    os.remove(temp_file_name)

  
  except ClientError as e:
    print(e)
    return {
      'statusCode': 500,
      'body': 'Error generating the blog'
    }

  return {
    'statusCode': 200,
    'body': json.dumps({
        'generated-text': response_body
    })
}