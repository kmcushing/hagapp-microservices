import logging

import azure.functions as func
from azure.cosmos import exceptions, CosmosClient, PartitionKey
import json

endpoint = "https://hagapp-db.documents.azure.com:443/"
key = "VXM6X3ZZb8Xq8V7Cl1oP8jS71XpJmmxuM7ofQjENtVFqpCnk1yi6PH0hm1r8iXrOJmLGdtVqBWX7YfZzOq9fOA=="
client = CosmosClient(endpoint, key)
db = client.get_database_client("hagapp-db")
user_container = db.get_container_client("Users")


def main(req: func.HttpRequest) -> func.HttpResponse:

    uid = req.params.get('uid')
    password = req.params.get('password')
    email = req.params.get('email')

    try:
        user_container.create_item({
            "id": uid,
            "email": email,
            "password": password,
            "my-events": [],
            "accepted-events": [],
            "available-events": [],
            "past-events": [],
            "friends": [],
            "incoming-friend-requests": [],
            "outgoing-friend-requests": []
        })
    except:
        return func.HttpResponse(json.dumps({'message': "Create User Failed"}))

    return func.HttpResponse(json.dumps({'message': "Create User Successful"}))
