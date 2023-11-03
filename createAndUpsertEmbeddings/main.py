from cloudevents.http import CloudEvent
from google.cloud import storage
from google.cloud import aiplatform
from google.protobuf import struct_pb2

import os
import tempfile
import base64
import functions_framework
import subprocess
import requests
import json
import google.auth.transport.requests

storage_client = storage.Client()

def getToken(): 
    creds, project = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    return creds.token

def upsertDataPoint(datapoint_id, datapoint_content):
    index_id = "7836549224647884800"

    type_datapointcontent = type(datapoint_content)
    type_datapointid = type(datapoint_id)

    print(f"datapoint id: {datapoint_id}, type: {type_datapointid}")
    print(f"datapoint content: {datapoint_content[0]}, type: {type_datapointcontent}")

    token = getToken()

    response = requests.post(f"https://us-central1-aiplatform.googleapis.com/v1/projects/prove-identityai/locations/us-central1/indexes/7836549224647884800:upsertDatapoints",
        headers = {
            "Authorization": f"Bearer {token}"
        },
        json = {
            "datapoints": [
                {
                    "datapointId": datapoint_id, 
                    "featureVector": datapoint_content
                }
            ]
        })

    print(response.json())
    
    if response.status_code == 200: 
        return "success"
    else: 
        return "error"

# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def hello_gcs(cloud_event: CloudEvent) -> tuple:
    """This function is triggered by a change in a storage bucket.

    Args:
        cloud_event: The CloudEvent that triggered this function.
    Returns:
        
    """
    image_file = cloud_event.data

    bucket_name = image_file["bucket"]
    image_name = image_file["name"]

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.get_blob(image_name)
    blob_bytes = blob.download_as_bytes()

    print(f"Bucket: {bucket_name}")
    print(f"File: {image_name}")

    encoded_content = base64.b64encode(blob_bytes).decode("utf-8")

    token = getToken()

    response = requests.post(f"https://us-central1-aiplatform.googleapis.com/v1/projects/prove-identityai/locations/us-central1/publishers/google/models/multimodalembedding@001:predict",
        headers = {
            "Authorization": f"Bearer {token}"
        },
        json = {
            "instances": [
                {"image": {"bytesBase64Encoded": encoded_content}}
            ]
        })
    print(response.json())
    embedding = response.json()["predictions"][0]['imageEmbedding']

    json_object = {
        "id": f"{image_name}",
        "embedding": embedding
    }

    # NOTE: doesn't not check for repeated uploads of same image. Would need to include some logic in order to avoid overwriting already uploaded images 
    # Vector Search does check for duplicates before upserting so it wouldn't affect the index performance wise. Would likely get charged for the bytes transfered. 

    output_bucket = storage_client.bucket("prove-identityai-flower-embeddings")
    out_image_name = image_name.split(".")[0]

    new_blob = output_bucket.blob(f"embedding_{out_image_name}.json")
    new_blob.upload_from_string(
        data=json.dumps(json_object),
        content_type='application/json'
    )    

    upsert_result = upsertDataPoint(image_name, embedding)    
    print(f"Upsert Result: {upsert_result}")
    
    if upsert_result == "success":
        return f"embedding_{out_image_name}.json complete"
    else: 
        return f"embedding_{out_image_name}.json unsuccessful"
