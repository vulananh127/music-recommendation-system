import httpx
import os

def get_client():
    return httpx.AsyncClient(base_url=os.environ.get("ES_HOST", "http://elasticsearch:9200"), timeout=5.0)