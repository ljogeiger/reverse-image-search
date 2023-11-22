from flask import Flask, request
from google.cloud import storage
from google.cloud import aiplatform

import urllib
import google.auth.transport.requests
import base64
import requests
import json
import os

app = Flask(__name__)

#change these
PROJECT_NAME="prove-identityai"
PROJECT_ID="267911685723"
REGION="us-central1"
ENDPOINT_DOMAIN="1814211594.us-central1-267911685723.vdb.vertexai.goog" # publicEndpointDomainName - https://cloud.google.com/vertex-ai/docs/vector-search/query-index-public-endpoint
ENDPOINT_ID="7579844045887766528"
DEPLOYED_ENDPOINT_DISPLAY_NAME="stream_search_deploy_1698156859082"

storage_client = storage.Client(project=PROJECT_NAME)

def getToken(): 
    creds, _ = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    return creds.token


def searchFromEmbedding(embedding, top_n): 
    endpoint = f"https://{ENDPOINT_DOMAIN}/v1/projects/{PROJECT_ID}/locations/{REGION}/indexEndpoints/{ENDPOINT_ID}:findNeighbors"

    token = getToken() 

    response = requests.post(endpoint,
        headers = {
            "Authorization": f"Bearer {token}"
        }, 
        json = {
            "deployedIndexId": DEPLOYED_ENDPOINT_DISPLAY_NAME,
            "queries": [
                {"datapoint": {"featureVector": embedding}}
            ]
        })

    print(response.json())

    result_top_n = []
    for i in range(top_n):
        neighbors = response.json()["nearestNeighbors"][0]["neighbors"]
        result_top_n.append(f'Name: {neighbors[i]["datapoint"]["datapointId"]} with Distance: {neighbors[i]["distance"]}')

    return result_top_n

@app.route("/main", methods=["POST"])
def start():
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)
    #request_args = request.args

    bucket_name = request_json["bucket"]
    image_name = request_json["object"]

    # default 3
    if "top_n" in request_json: 
        top_n = request_json["top_n"]
    else: 
        top_n = 3

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.get_blob(image_name)
    blob_bytes = blob.download_as_bytes()

    print(f"Bucket: {bucket_name}")
    print(f"File: {image_name}")

    encoded_content = base64.b64encode(blob_bytes).decode("utf-8")

    endpoint = f"https://{REGION}-aiplatform.googleapis.com/v1/projects/{PROJECT_NAME}/locations/{REGION}/publishers/google/models/multimodalembedding@001:predict"
    
    token = getToken()

    response = requests.post(endpoint,
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

    # now search across index projects/267911685723/locations/us-central1/indexEndpoints/7579844045887766528

    top_n_images = searchFromEmbedding(embedding, top_n)

    return top_n_images

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port = int(os.environ.get("PORT",8080)))