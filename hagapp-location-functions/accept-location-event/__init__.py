import logging

import azure.functions as func
from azure.cosmos import exceptions, CosmosClient, PartitionKey
from azure.core import MatchConditions
from datetime import datetime, date
import jwt
import json

endpoint = "https://hagapp-db.documents.azure.com:443/"
key = "VXM6X3ZZb8Xq8V7Cl1oP8jS71XpJmmxuM7ofQjENtVFqpCnk1yi6PH0hm1r8iXrOJmLGdtVqBWX7YfZzOq9fOA=="
client = CosmosClient(endpoint, key)
db = client.get_database_client("hagapp-db")
location_event_container = db.get_container_client("LocationEvents")
user_container = db.get_container_client("Users")
jwt_key = "secret"


def main(req: func.HttpRequest) -> func.HttpResponse:
    token = req.headers.get('Authorization')[7:]

    try:
        body = req.get_json()
    except:
        return func.HttpResponse(json.dumps({'message': "Request Failed - No JSON in request"}))

    uid = body.get('uid')

    try:
        decoded_token = jwt.decode(token, jwt_key, algorithms=['HS256'])
        assert(decoded_token['uid'] == uid)
    except:
        return func.HttpResponse(json.dumps({'message': "Request Failed"}))

    eid = body.get('id')

    # loc should have the form
    # {
    #     "type":"Point",
    #     "coordinates":[ 31.9, -4.8 ] # lat, long
    # }
    # take in loc in form of lat,long
    try:
        loc = body.get('loc').split(',')
        loc = {
            "type": "Point",
            "coordinates": [float(loc[0]), float(loc[1])]
        }
    except:
        return func.HttpResponse(json.dumps({'message': "Request Failed, invalid location"}))

    success = False

    try:
        user_item = user_container.read_item(uid, uid)
        while not success:
            # TODO extract item within given distance of location with KQL
            # event_item = location_event_container.read_item(eid, eid)
            event_item = list(location_event_container.query_items(
                query="SELECT * FROM e WHERE ST_DISTANCE(e.loc, @loc) <= e.dist and e.id = @id",
                parameters=[
                    {"name": "@loc", "value": loc}, {"name": "@id", "value": eid}
                ]
            ))[0]
            assert(
                # date.fromisoformat(
                # event_item['event-time']) > datetime.now() and
                event_item['num-participants'] > len(
                    event_item['accepted-uids'])
                and uid not in event_item['accepted-uids'])
            event_item['accepted-uids'].append(uid)
            try:
                location_event_container.replace_item(eid, event_item,
                                                      etag=event_item['_etag'],
                                                      match_condition=MatchConditions(2))
                success = True
            except:
                pass
    except:
        return func.HttpResponse(json.dumps({'message': "Accept Event Failed"}))

    success = False

    while not success:
        user_item = user_container.read_item(uid, uid)
        user_item['accepted-events'].append(eid)
        try:
            user_container.replace_item(uid, user_item,
                                        etag=user_item['_etag'],
                                        match_condition=MatchConditions(2))
            success = True
        except:
            pass

    return func.HttpResponse(json.dumps({'message': "Accept Event Successful"}))
