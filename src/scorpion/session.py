import base64
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

from src.scorpion.utils import Url

PARENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(PARENT_DIR)
print(PARENT_DIR, ROOT_DIR)
load_dotenv(override=True)


class Session(BaseModel):
    """Creates a requests session to the Evertz Scorpion api"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    scheme: str = "http"
    host: str = "98.188.63.196"
    port: int = None
    version: str = "v.api/apis/"
    api_limit: float = 1.0 / 4
    max_records_per_request: int = 100
    session: Optional[requests.Session] = None
    url: Optional[str] = None
    timeout: float = 2
    token: str = os.environ.get("SCORPION_TOKEN")
    config: dict = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = self._get_config()
        self.session = requests.Session()
        self.url = Url(
            scheme=self.scheme,
            host=self.host,
            port=self.port,
            version=self.version,
        )
        self._token()
        self.session.headers.update({"jwt": self.token})

    def _get_config(self):
        with open(f"{PARENT_DIR}/config.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_config(self):
        with open(f"{PARENT_DIR}/config.json", "w", encoding="utf-8") as f:
            f.write(
                json.dumps(self.config, indent=4, sort_keys=True, ensure_ascii=False)
            )

    def _token(self):
        if not self.token:
            self.token = self._get_token()
        else:
            timestamp_str = os.environ["SCORPION_TOKEN_TIMEOUT"]
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            if not datetime.now() < timestamp:
                self.token = self._get_token()

    def _set_token_timeout(self, timeout: int):
        timestamp = datetime.now()
        timestamp += timedelta(seconds=timeout)
        self.config["SCORPION_TOKEN_TIMEOUT"] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        self._write_config()

    def _get_token(self):
        creds = json.dumps(
            {
                "username": os.environ["SCORPION_USER"],
                "password": os.environ["SCORPION_PASS"],
            }
        ).encode("ascii")
        creds = base64.b64encode(creds)
        creds = creds.decode("ascii")
        self.url.path = f"{self.version}BT/JWTCREATE/{creds}"
        response = requests.post(
            self.url.to_string(),
            verify=False,
            timeout=5,
        )
        token = response.json()["jwt"]
        self.config["SCORPION_TOKEN"] = token
        self._write_config()
        self._set_token_timeout(response.json()["brief"]["life"])
        return token

    def verify_token(self):

        self.url.path = f"{self.version}BT/JWTVERIFY/{self.token}"
        response = requests.post(
            self.url.to_string(),
            verify=False,
            timeout=2,
        )
        if response.json().get("status") == "valid":
            print(f"{response.json().get('life-remain')}")
            return True
        return False

    def _refresh_token(self):
        self.url.path = f"{self.version}BT/JWTREFRESH/{self.token}"
        response = requests.post(
            self.url.to_string(),
            verify=False,
            timeout=5,
        )
        token = response.json().get("jwt")
        self.config["SCORPION_TOKEN"] = token
        self._write_config()
        self._set_env("SCORPION_TOKEN", token)
        self._set_token_timeout(response.json()["brief"]["life"])
        return False

    def _process_response(self, response):
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            err_msg = str(exc)
            try:
                error_dict = response.json()
            except ValueError:
                pass
            else:
                if "error" in error_dict:
                    err_msg = f"{err_msg} [Error: {error_dict['error']}]"
            print(err_msg)
            raise exc
        # self._refresh_token()
        return response.json()

    def _request(self, http_method: str, params=None, json_data=None, files=None):

        response = self.session.request(
            http_method,
            self.url.to_string(),
            params=params,
            json=json_data,
            files=files,
            timeout=self.timeout,
        )

        return self._process_response(response)
