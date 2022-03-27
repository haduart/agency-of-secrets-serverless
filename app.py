from botocore.exceptions import ClientError
from chalice import Chalice, CORSConfig, NotFoundError, BadRequestError, ForbiddenError,  Response, AuthResponse, AuthRoute, \
    CognitoUserPoolAuthorizer
from basicauth import decode
import logging
import boto3
from hashlib import blake2b
import json
import os
from boto3.dynamodb.conditions import Key
import random


_S3_CLIENT = None
_DYNAMODB_CLIENT = None
_DYNAMODB_TABLE = None

PROFILES_BUCKET_NAME = os.getenv('PROFILES_BUCKET_NAME', 'medgaims')

app = Chalice(app_name='agency-of-secrets-serverless')
app.log.setLevel(logging.DEBUG)

cors_config = CORSConfig(allow_origin="*")


def get_s3_client():
    global _S3_CLIENT
    if _S3_CLIENT is None:
        _S3_CLIENT = boto3.client('s3')
    return _S3_CLIENT


def check_if_file_exists(file_name):
    try:
        get_s3_client().head_object(Bucket=PROFILES_BUCKET_NAME, Key="profiles/" + file_name)
    except ClientError as e:
        print("The file does not exist")
        return False
    else:
        print("The file exist")
        return True


@app.route('/')
def index():
    return {'hello': 'world'}


@app.route('/get/{file_name}')
def get(file_name):
    if check_if_file_exists(file_name + ".json"):
        return {'file': file_name, 'found': 'true'}
    return {'file': file_name, 'found': 'false'}


#curl -X PUT https://as9hfctzei.execute-api.eu-west-1.amazonaws.com/api/upload/edu --upload-file edu.json --header "Content-Type:application/octet-stream"
#curl https://medgaims.s3.eu-west-1.amazonaws.com/profiles/edu.json
@app.route('/upload/{file_name}', methods=['PUT'], content_types=['application/octet-stream'])
def upload_to_s3(file_name):
    # get raw body of PUT request
    body = app.current_request.raw_body

    # write body to tmp file
    tmp_file_name = '/tmp/' + file_name
    with open(tmp_file_name, 'wb') as tmp_file:
        tmp_file.write(body)

    # upload tmp file to s3 bucket
    get_s3_client().upload_file(tmp_file_name, PROFILES_BUCKET_NAME, "profiles/" + file_name + ".json",
                                ExtraArgs={'ACL': 'public-read'})

    return Response(body='upload successful: {}'.format(file_name),
                    status_code=200,
                    headers={'Content-Type': 'text/plain'})


