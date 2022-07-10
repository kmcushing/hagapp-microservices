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
    token = req.headers.get('Authorization')[7:]

    try:
        body = req.get_json()
    except:
        return func.HttpResponse(json.dumps({'message': "Request Failed - No JSON in request"}))

    print('got body')

    uid = body['uid']

    try:
        decoded_token = jwt.decode(token, jwt_key, algorithms=['HS256'])
        assert(decoded_token['uid'] == uid)
    except:
        return func.HttpResponse(json.dumps({'message': "Invalid Token", 'token': token}))

    print("uids match")
    target_uid = body['target-uid']

    try:
        target_object = user_container.read_item(target_uid, target_uid)
        user_object = user_container.read_item(uid, uid)
    except:
        return func.HttpResponse(json.dumps({'message': "Request Failed"}))

    success = False

    while not success:
        user_object = user_container.read_item(uid, uid)
        user_object['outgoing-friend-requests'].append(target_uid)
        try:
            user_container.replace_item(uid, user_object,
                                        etag=user_object['_etag'],
                                        match_condition=MatchConditions(2))
            success = True
        except:
            pass

    success = False

    while not success:
        target_object = user_container.read_item(target_uid, target_uid)
        target_object['incoming-friend-requests'].append(uid)
        try:
            user_container.replace_item(target_uid, target_object,
                                        etag=target_object['_etag'],
                                        match_condition=MatchConditions(2))
            success = True
        except:
            pass

    return func.HttpResponse(json.dumps({'message': "Request Successful",
                                         'outgoing-friend-requests':
                                         user_object['outgoing-friend-requests']}))
