"""Deploy the embedded chunks to the Qdrant vector database.

Deploy steps (each function below says which step it implements):

  Step 1. Recreate the collection: delete QDRANT_COLLECTION ("serve_guide") if it
          exists, then create it empty, with two named vectors per point, for hybrid
          search:
            - DENSE_VECTOR: the chunk's embedding (vector size of the embeddings,
              cosine distance), for semantic search;
            - SPARSE_VECTOR: BM25 keyword weights, for keyword search. The IDF
              modifier makes Qdrant apply the inverse document frequency of the
              collection at query time.
          Every ingestion rebuilds the whole knowledge base, so chunks of pages that
          were changed or removed do not stay behind.
  Step 2. Build points: one Qdrant point per chunk. The point id is the chunk id; the
          dense vector is the chunk's embedding; the sparse vector is the chunk's
          "text" as a BM25_MODEL document, which Qdrant turns into BM25 weights on the
          server (needs Qdrant >= 1.15.2 and clients.qdrant_client(), which sends
          documents to the server). All other chunk fields (text, content, headings,
          breadcrumb, URLs, ...) are stored as the point's payload (metadata).
  Step 3. Upload the points in batches of BATCH_SIZE; a failed batch is retried up to
          MAX_RETRIES times.
  Step 4. Check: count the points in the collection; it must equal the number of chunks.

The Qdrant client is created by the caller (clients.qdrant_client()) and passed in;
the collection name comes from config.py.
"""

import logging

from qdrant_client.models import (
    Distance,
    Document,
    Modifier,
    PointStruct,
    SparseVectorParams,
    VectorParams,
)

import config

logger = logging.getLogger(__name__)

# Names of the two vectors of every point (Steps 1, 2); the search uses the same names.
DENSE_VECTOR = "dense"
SPARSE_VECTOR = "sparse"
# Qdrant's built-in BM25 model, run on the Qdrant server (Step 2); the search must
# use the same model for the query.
BM25_MODEL = "Qdrant/bm25"
# Points per upload request (Step 3)
BATCH_SIZE = 64
# Retries for a failed upload batch (Step 3)
MAX_RETRIES = 3


# ------------------------- Step 1: recreate collection -----------------------

def recreate_collection(client, collection, vector_size):
    """Step 1: delete the collection if it exists, then create it empty, with a dense
    and a sparse (BM25) vector per point."""
    if client.collection_exists(collection):
        logger.info("Deleting existing collection %s", collection)
        client.delete_collection(collection)

    logger.info("Creating collection %s (dense vector size %d, cosine distance; sparse BM25 vector)",
                collection, vector_size)
    client.create_collection(
        collection_name=collection,
        vectors_config={DENSE_VECTOR: VectorParams(size=vector_size, distance=Distance.COSINE)},
        sparse_vectors_config={SPARSE_VECTOR: SparseVectorParams(modifier=Modifier.IDF)},
    )


# ---------------------------- Step 2: build points ---------------------------

def build_points(chunks):
    """Step 2: one point per chunk: id = chunk id, dense vector = its embedding,
    sparse vector = its text as a BM25 document, payload = all other chunk fields."""
    points = []
    for chunk in chunks:
        payload = dict(chunk)
        dense_vector = payload.pop("vector")
        sparse_vector = Document(text=chunk["text"], model=BM25_MODEL)
        vectors = {DENSE_VECTOR: dense_vector, SPARSE_VECTOR: sparse_vector}
        point = PointStruct(id=chunk["id"], vector=vectors, payload=payload)
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
