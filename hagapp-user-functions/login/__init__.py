import logging

import azure.functions as func
from azure.cosmos import exceptions, CosmosClient, PartitionKey
import jwt
from datetime import datetime, timedelta
import json

endpoint = "https://hagapp-db.documents.azure.com:443/"
key = "VXM6X3ZZb8Xq8V7Cl1oP8jS71XpJmmxuM7ofQjENtVFqpCnk1yi6PH0hm1r8iXrOJmLGdtVqBWX7YfZzOq9fOA=="
client = CosmosClient(endpoint, key)
db = client.get_database_client("hagapp-db")
user_container = db.get_container_client("Users")
jwt_key = "secret"


def main(req: func.HttpRequest) -> func.HttpResponse:
    uid = req.params.get('uid')
    password = req.params.get('password')

    # try logging in
    try:
        item = user_container.read_item(uid, partition_key=uid)
        assert(item['password'] == password)
    except:
        return func.HttpResponse(json.dumps({'message': "Login Failed"}))

    return func.HttpResponse(json.dumps({'uid': uid, 'accessToken': jwt.encode({'uid': uid, 'exp': datetime.utcnow() + timedelta(minutes=30)},
                                                                               jwt_key, algorithm="HS256")}))
