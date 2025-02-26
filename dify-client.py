import requests
import time
import logging
import base64
import json
from typing import Any, Dict, Optional, List


class DifyApiClient:
    def __init__(self, base_url: str, debug: bool = False) -> None:
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: float = 0
        self.debug = debug

        self.logger = logging.getLogger("DifyApiClient")
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)

    def _log(self, message: str) -> None:
        if self.debug:
            self.logger.debug(message)

    def _decode_base64_url(self, base64_url_str: str) -> str:
        padding = "=" * (4 - (len(base64_url_str) % 4))
        return base64.urlsafe_b64decode(base64_url_str + padding).decode("utf-8")

    def _decode_token(self, token: str) -> Dict[str, Any]:
        parts = token.split(".")
        if len(parts) != 3:
            self._log("Invalid JWT token format")
            raise ValueError("Invalid JWT token format")

        payload_str = self._decode_base64_url(parts[1])
        return json.loads(payload_str)

    def _update_tokens(self, access_token: str, refresh_token: str) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token

        decoded_access_token = self._decode_token(access_token)
        expires_in = decoded_access_token.get("exp", time.time()) - time.time()
        self.token_expiry = time.time() + expires_in

        self._log(f"Tokens updated. Access token expires in {expires_in} seconds.")

    def _is_token_expired(self) -> bool:
        expired = time.time() >= self.token_expiry
        self._log(f"Token expired: {expired}")
        return expired

    def login(self, email: str, password: str) -> None:
        self._log(f"Logging in with email: {email}")
        url = f"{self.base_url}/console/api/login"
        payload = {
            "email": email,
            "password": password,
            "language": "en-US",
            "remember_me": True
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        if data["result"] == "success":
            tokens = data["data"]
            self._update_tokens(tokens["access_token"], tokens["refresh_token"])
        else:
            self._log(f"Login failed with response: {data}")
            raise Exception("Login failed")

    def _refresh_tokens(self) -> None:
        self._log("Refreshing tokens using refresh token.")
        url = f"{self.base_url}/auth/refresh"
        payload = {
            "refresh_token": self.refresh_token
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        if data['result'] == 'success':
            tokens = data['data']
            self._update_tokens(tokens['access_token'], tokens['refresh_token'])
        else:
            self._log(f"Token refresh failed with response: {data}")
            raise Exception("Token refresh failed")

    def _ensure_valid_token(self) -> None:
        if self._is_token_expired():
            self._refresh_tokens()

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        self._ensure_valid_token()
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        url = f"{self.base_url}{endpoint}"
        self._log(f"GET request to {url} with params: {params}")
        response = requests.get(url, headers=headers, params=params)
        self._log(f"Response: {response.status_code} - {response.text}")
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        self._ensure_valid_token()
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        url = f"{self.base_url}{endpoint}"
        self._log(f"POST request to {url} with data: {data}")
        response = requests.post(url, headers=headers, json=data)
        self._log(f"Response: {response.status_code} - {response.text}")
        response.raise_for_status()
        return response.json()

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        self._ensure_valid_token()
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        url = f"{self.base_url}{endpoint}"
        self._log(f"PUT request to {url} with data: {data}")
        response = requests.put(url, headers=headers, json=data)
        self._log(f"Response: {response.status_code} - {response.text}")
        response.raise_for_status()
        return response.json()

    def delete(self, endpoint: str) -> Any:
        self._ensure_valid_token()
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        url = f"{self.base_url}{endpoint}"
        self._log(f"DELETE request to {url}")
        response = requests.delete(url, headers=headers)
        self._log(f"Response: {response.status_code} - {response.text}")
        response.raise_for_status()
        return response.json()

def main(workflow_run_id: str, application_id: str) -> Dict:
    client = DifyApiClient(base_url="http://dify.dify-system.svc", debug=False)

    client.login(email="*******", password="******")

    # response = client.get("/console/api/apps?page=1&limit=30&name=")
    # app_id = response['data'][1]['id']

    # response = client.get(f"/console/api/apps/{app_id}/chat-conversations?page=1&limit=100")

    # response = client.get(f"/console/api/apps/{app_id}/chat-messages?conversation_id={response['data'][0]['id']}")
    # workflow_id = response['data'][0]['workflow_run_id']

    response = client.get(f"/console/api/apps/{application_id}/workflow-runs/{workflow_run_id}/node-executions")

    return response