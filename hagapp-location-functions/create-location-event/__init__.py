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
location_event_container = db.get_container_client("LocationEvents")
event_container = db.get_container_client("Events")
closed_event_container = db.get_container_client("ClosedEvents")
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
    event_time = body.get('event-time')
    num_participants = body.get('num-participants')
    notes = body.get('notes')

    # max distance for location based events - in meters - convert to meters from miles
    dist = float(body.get('dist')) * 1609.344

    # loc shoould have the form
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

    # ensure idisuniquetoall current and past events
    try:
        closed_event_container.read_item(eid, eid)
        return func.HttpResponse(json.dumps({'message': "Create Event Failed - need a unique event id"}))
    except:
        pass

    try:
        event_container.read_item(eid, eid)
        return func.HttpResponse(json.dumps({'message': "Create Event Failed - need a unique event id"}))
    except:
        pass

    try:
        location_event_container.create_item({'id': eid, 'uid': uid,
                                              'event-time': event_time,
                                              #   'lng': lng,
                                              #   'lat': lat,
                                              'loc': loc,
                                              'dist': dist,
                                              'accepted-uids': [uid],
                                              'num-participants': num_participants,
                                              'notes': notes})
    except:
        return func.HttpResponse(json.dumps({'message': "Create Event Failed - not a unique id"}))

    success = False
    while not success:
        user_item = user_container.read_item(uid, uid)
        try:
            user_item['my-events'].append(eid)
            user_container.replace_item(uid, user_item, etag=user_item['_etag'],
                                        match_condition=MatchConditions(2))
        except:
            continue
        success = True

    return func.HttpResponse(json.dumps({'message': "Request Successful"}))
