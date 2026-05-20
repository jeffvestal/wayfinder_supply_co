from elasticsearch import Elasticsearch
import os

_es_client = None


def get_elastic_client():
    """
    Get or create Elasticsearch client singleton.
    """
    global _es_client
    
    if _es_client is None:
        es_url = os.getenv("STANDALONE_ELASTICSEARCH_URL", os.getenv("ELASTICSEARCH_URL", "http://kubernetes-vm:30920"))
        api_key = os.getenv("STANDALONE_ELASTICSEARCH_APIKEY", os.getenv("ELASTICSEARCH_APIKEY", ""))
        
        if not api_key:
            raise ValueError("STANDALONE_ELASTICSEARCH_APIKEY (or ELASTICSEARCH_APIKEY) environment variable is required")
        
        _es_client = Elasticsearch(
            [es_url],
            api_key=api_key,
            request_timeout=30
        )
    
    return _es_client


