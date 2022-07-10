import logging

import azure.functions as func
from azure.cosmos import exceptions, CosmosClient, PartitionKey
from azure.core import MatchConditions
import jwt
import json

endpoint = "https://hagapp-db.documents.azure.com:443/"
key = "VXM6X3ZZb8Xq8V7Cl1oP8jS71XpJmmxuM7ofQjENtVFqpCnk1yi6PH0hm1r8iXrOJmLGdtVqBWX7YfZzOq9fOA=="
client = CosmosClient(endpoint, key)
db = client.get_database_client("hagapp-db")
user_container = db.get_container_client("Users")
jwt_key = "secret"


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("request recieved")
    token = req.headers.get('Authorization')[7:]

    logging.info("token: " + str(token))

    uid = req.params.get('uid')

    try:
        decoded_token = jwt.decode(token, jwt_key, algorithms=['HS256'])
        assert(decoded_token['uid'] == uid)
    except:
        return func.HttpResponse(json.dumps({'message': "Invalid Token"}))

    logging.info("token valid")

    try:
        user_object = user_container.read_item(uid, uid)
    except:
        return func.HttpResponse(json.dumps({'message': "Request Failed"}))

    logging.info("user info read")

    return func.HttpResponse(json.dumps({'message': "Request Successful",
                                         'friends':
                                         user_object['friends'],
                                         'outgoing-friend-requests':
                                         user_object['outgoing-friend-requests'],
                                         'incoming-friend-requests':
                                         user_object['incoming-friend-requests']}))
