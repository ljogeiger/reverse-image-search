# Reverse Image Search 
Author: lukasgeiger@google.com

TLDR: Search for similar images using an image file. This tutorial uses GCP's Multimodal Embedding API 
and Vector Search to perform Approximate Nearest Neighbors (ANN) search. 

Built off of sample code provided here: https://github.com/GoogleCloudPlatform/matching-engine-tutorial-for-image-search

## Use Case: 

## Architecture Diagram 

<insert-image-here>

## Steps: 
1. Build GCS buckets for images and embeddings 
2. Configure variables of createAndUpsertEmbeddings 
3. Generate Authentication token
4. Build createAndUpsertEmbeddings Cloud Function 
5. Create Vector Search Index and Endpoints
6. Build searchVectorDB Cloud Run 
7. Test system 



## Comparisons of Vector DBs (why Vector Search)

## Cloud Functions vs. Cloud Run

