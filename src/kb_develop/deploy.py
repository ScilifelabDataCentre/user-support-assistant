"""Deploy the embedded chunks to the Qdrant vector database.

Deploy steps (each function below says which step it implements):

  Step 1. Recreate the collection: delete QDRANT_COLLECTION ("serve_guide") if it
          exists, then create it empty, with the vector size of the embeddings and
          cosine distance. Every ingestion rebuilds the whole knowledge base, so chunks
          of pages that were changed or removed do not stay behind.
  Step 2. Build points: one Qdrant point per chunk. The point id is the chunk id, the
          vector is the chunk's embedding, and all other chunk fields (text, content,
          headings, breadcrumb, URLs, ...) are stored as the point's payload (metadata).
  Step 3. Upload the points in batches of BATCH_SIZE; a failed batch is retried up to
          MAX_RETRIES times.
  Step 4. Check: count the points in the collection; it must equal the number of chunks.

The Qdrant client is created by the caller (clients.qdrant_client()) and passed in;
the collection name comes from config.py.
"""

import logging

from qdrant_client.models import Distance, PointStruct, VectorParams

import config

logger = logging.getLogger(__name__)

# Points per upload request (Step 3)
BATCH_SIZE = 64
# Retries for a failed upload batch (Step 3)
MAX_RETRIES = 3


# ------------------------- Step 1: recreate collection -----------------------

def recreate_collection(client, collection, vector_size):
    """Step 1: delete the collection if it exists, then create it empty."""
    if client.collection_exists(collection):
        logger.info("Deleting existing collection %s", collection)
        client.delete_collection(collection)

    logger.info("Creating collection %s (vector size %d, cosine distance)", collection, vector_size)
    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


# ---------------------------- Step 2: build points ---------------------------

def build_points(chunks):
    """Step 2: one point per chunk: id = chunk id, vector = its embedding,
    payload = all other chunk fields."""
    points = []
    for chunk in chunks:
        payload = dict(chunk)
        vector = payload.pop("vector")
        point = PointStruct(id=chunk["id"], vector=vector, payload=payload)
        points.append(point)
    return points


# ------------------------------- Step 3: upload ------------------------------

def upload(client, collection, points):
    """Step 3: upload the points in batches of BATCH_SIZE and wait until Qdrant has
    stored them (failed batches are retried up to MAX_RETRIES times)."""
    client.upload_points(
        collection_name=collection,
        points=points,
        batch_size=BATCH_SIZE,
        max_retries=MAX_RETRIES,
        wait=True,
    )


# ------------------------------- Step 4: check -------------------------------

def check_count(client, collection, expected):
    """Step 4: raise if the collection does not hold exactly `expected` points."""
    count = client.count(collection_name=collection, exact=True).count
    if count != expected:
        raise RuntimeError(f"collection {collection} has {count} points, expected {expected}")
    return count


# --------------------------------- pipeline ----------------------------------

def deploy_chunks(client, chunks):
    """Run Steps 1-4: put the embedded chunks into the Qdrant collection
    QDRANT_COLLECTION, replacing what was there."""
    if not chunks:
        raise ValueError("no chunks to deploy")
    collection = config.QDRANT_COLLECTION

    # Step 1. Recreate the collection
    vector_size = len(chunks[0]["vector"])
    recreate_collection(client, collection, vector_size)

    # Step 2. Build points
    points = build_points(chunks)

    # Step 3. Upload
    logger.info("Uploading %d points to %s", len(points), collection)
    upload(client, collection, points)

    # Step 4. Check
    count = check_count(client, collection, len(points))
    logger.info("Collection %s now holds %d points", collection, count)
