from src.main.api.foundation.endpoint import Endpoint
from typing import Dict, Callable


class HttpRequester:
    def __init__(self, request_spec: Dict[str, str], endpoint: Endpoint, response_spec: Callable):
        self.request_spec = request_spec
        self.endpoint = endpoint
        self.response_spec = response_spec
