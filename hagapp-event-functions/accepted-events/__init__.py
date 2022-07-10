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
location_event_container = db.get_container_client("LocationEvents")
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

    events = []
    try:
        user_item = user_container.read_item(uid, uid)
        for eid in user_item['accepted-events']:
            try:
                try:
                    event_item = event_container.read_item(eid, eid)
                except:
                    event_item = location_event_container.read_item(eid, eid)
                events.append(event_item)
            except:
                success = False
                while not success:
                    user_item = user_container.read_item(uid, uid)
                    user_item['accepted-events'].remove(eid)
                    try:
                        user_container.replace_item(uid, user_item,
                                                    etag=user_item['_etag'],
                                                    match_condition=MatchConditions(2))
                        success = True
                    except:
                        pass
        for eid in user_item['my-events']:
            try:
                event_item = event_container.read_item(eid, eid)
                events.append(event_item)
            except:
                try:
                    event_item = location_event_container.read_item(eid, eid)
                    events.append(event_item)
                except:
                    pass

        # still need to get events offered to all users

        return func.HttpResponse(json.dumps({'message': "Request Successful",
                                             'accepted-events': events}))

    except:
        return func.HttpResponse(json.dumps({'message': "Request Failed"}))
