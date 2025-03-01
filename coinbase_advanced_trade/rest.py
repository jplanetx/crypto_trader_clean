"""
A minimal stub for Coinbase Advanced Trade REST client.
"""

class RESTClient:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def get_product_ticker(self, product_id):
        # Dummy implementation for testing purposes.
        # In a real scenario, this method would make an HTTP request to the Coinbase Advanced Trade API.
        return {"price": "123.45"}
