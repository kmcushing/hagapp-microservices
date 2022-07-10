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
    uid = req.params.get('uid')

    logging.info("got token")

    try:
        decoded_token = jwt.decode(token, jwt_key, algorithms=['HS256'])
        assert(decoded_token['uid'] == uid)
    except:
        return func.HttpResponse(json.dumps({'message': "Request Failed"}))

    logging.info("token valid")

    # loc shoould have the form
    # {
    #     "type":"Point",
    #     "coordinates":[ 31.9, -4.8 ] # lat, long
    # }
    # take in loc in form of lat,long
    try:
        # loc = req.params.get('loc').split(',')
        # loc = {
        #     "type": "Point",
        #     "coordinates": [float(loc[0]), float(loc[1])]
        # }
        loc = req.params.get('loc').split(',')
        loc = {
            "type": "Point",
            "coordinates": [float(loc[0]), float(loc[1])]
        }
        # loc = {
        #     "type": "Point",
        #     "coordinates": [float(req.params.get('lat')), float(req.params.get('lng'))]
        # }
    except:
        return func.HttpResponse(json.dumps({'message': "Request Failed, invalid location"}))

    logging.info("loc valid: " + str(loc))

    try:

        # logging.info(location_event_container.query_items(
        #     query="SELECT * FROM e WHERE ST_DISTANCE(e.loc, @loc) <= e.dist",
        #     parameters=[
        #         {"name": "@loc", "value": loc}
        #     ]
        # ))

        # for e in enumerate(location_event_container.query_items(
        #         query="SELECT * FROM e WHERE ST_DISTANCE(e.loc, @loc) <= e.dist",
        #         parameters=[
        #             {"name": "@loc", "value": loc}
        #         ])):
        #     logging.info(e)

        events = list(location_event_container.query_items(
            query="SELECT * FROM e WHERE ST_DISTANCE(e.loc, @loc) <= e.dist",
            parameters=[
                {"name": "@loc", "value": loc}
            ],
            enable_cross_partition_query=True
        ))
        logging.info("got events")
        logging.info(events)
        available_events = [
            e for e in events if int(e['num-participants']) > len(e['accepted-uids']) and uid not in e['accepted-uids']]
        logging.info("got available events")
        logging.info(available_events)
        return func.HttpResponse(json.dumps({'message': "Request Successful",
                                             'events': available_events}))

    except Exception as e:
        logging.info(e)
        return func.HttpResponse(json.dumps({'message': "Request Failed"}))
