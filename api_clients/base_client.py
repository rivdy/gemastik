"""
BaseAPIClient
=============
Kelas dasar abstrak untuk seluruh klien API eksternal (AlphaFold, RCSB PDB,
PubChem, ChEMBL, DisGeNET, Open Targets, dst). Sesuai dengan desain UML
'BaseAPIClient' pada Workflow UML kalian: menyimpan BASE_URL, api_key,
timeout, dan session requests, ditambah retry + rate limiting generik.

Setiap API konkret cukup mewarisi kelas ini dan mengoverride:
  - _auth_headers() / _auth_params()  -> cara autentikasi berbeda-beda
  - method-method khusus per API (get_prediction, search, dst)
"""

from __future__ import annotations

import time
import logging
from abc import ABC
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("otomasi_gemastik.api_clients")


class APIClientError(Exception):
    """Dilempar ketika request ke API eksternal gagal setelah retry."""


class BaseAPIClient(ABC):
    #: harus dioverride oleh subclass, contoh: "https://alphafold.ebi.ac.uk/api"
    BASE_URL: str = ""

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        min_request_interval: float = 0.0,
    ):
        if not self.BASE_URL:
            raise ValueError(f"{self.__class__.__name__} harus mendefinisikan BASE_URL")

        self.api_key = api_key
        self.timeout = timeout
        self.min_request_interval = min_request_interval
        self._last_request_ts: float = 0.0

        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    # ------------------------------------------------------------------ #
    # Hook-hook yang boleh dioverride subclass
    # ------------------------------------------------------------------ #
    def _auth_headers(self) -> dict:
        """Default: tidak ada auth. Override jika API butuh header (mis. DisGeNET)."""
        return {}

    def _auth_params(self) -> dict:
        """Default: tidak ada auth. Override jika API butuh query param key."""
        return {}

    def _default_headers(self) -> dict:
        return {"Accept": "application/json"}

    # ------------------------------------------------------------------ #
    # Rate limiting sederhana (token-bucket 1 slot, cukup untuk kompetisi)
    # ------------------------------------------------------------------ #
    def _respect_rate_limit(self) -> None:
        if self.min_request_interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request_ts
        wait = self.min_request_interval - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request_ts = time.monotonic()

    # ------------------------------------------------------------------ #
    # Core request method
    # ------------------------------------------------------------------ #
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json_body: Optional[dict] = None,
        headers: Optional[dict] = None,
        expect_json: bool = True,
    ) -> Any:
        self._respect_rate_limit()

        url = path if path.startswith("http") else f"{self.BASE_URL}{path}"
        merged_headers = {**self._default_headers(), **self._auth_headers(), **(headers or {})}
        merged_params = {**self._auth_params(), **(params or {})}

        try:
            resp = self.session.request(
                method=method,
                url=url,
                params=merged_params,
                json=json_body,
                headers=merged_headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("Request ke %s gagal: %s", url, exc)
            raise APIClientError(f"Gagal memanggil {url}: {exc}") from exc

        if not expect_json:
            return resp.content

        if not resp.content:
            return None

        try:
            return resp.json()
        except ValueError as exc:
            raise APIClientError(f"Respons dari {url} bukan JSON valid") from exc

    def get(self, path: str, params: Optional[dict] = None, **kwargs) -> Any:
        return self._request("GET", path, params=params, **kwargs)

    def post(self, path: str, json_body: Optional[dict] = None, **kwargs) -> Any:
        return self._request("POST", path, json_body=json_body, **kwargs)

    def close(self) -> None:
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
