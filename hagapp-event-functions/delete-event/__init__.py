import logging

import azure.functions as func
from azure.cosmos import exceptions, CosmosClient, PartitionKey
from azure.core import MatchConditions
from datetime import datetime
import jwt
import json

endpoint = "https://hagapp-db.documents.azure.com:443/"
key = "VXM6X3ZZb8Xq8V7Cl1oP8jS71XpJmmxuM7ofQjENtVFqpCnk1yi6PH0hm1r8iXrOJmLGdtVqBWX7YfZzOq9fOA=="
client = CosmosClient(endpoint, key)
db = client.get_database_client("hagapp-db")
event_container = db.get_container_client("Events")
user_container = db.get_container_client("Users")
jwt_key = "secret"


def main(req: func.HttpRequest) -> func.HttpResponse:
    token = req.headers.get('Authorization')[7:]

    uid = req.params.get('uid')

    try:
        decoded_token = jwt.decode(token, jwt_key, algorithms=['HS256'])
        assert(decoded_token['uid'] == uid)
    except:
        return func.HttpResponse(json.dumps({'message': "Request Failed"}))

    eid = req.params.get('id')

    try:
        event_item = event_container.read_item(eid, eid)
        user_item = user_container.read_item(uid, uid)
        assert(eid in user_item['my-events'])
        event_container.delete_item(eid, eid)
    except:
        return func.HttpResponse(json.dumps({'message': "Request Failed"}))

    success = False
    while not success:
        try:
            user_item = user_container.read_item(uid, uid)
            user_item['my-events'].remove(eid)
            user_container.replace_item(uid, user_item,
                                        etag=user_item['_etag'],
                                        match_condition=MatchConditions(2))
            success = True
        except:
            pass

    return func.HttpResponse(json.dumps({'message': "Request Successful",
                                         'my-events': user_item['my-events']}))
