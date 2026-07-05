"""
Test dasar untuk BaseAPIClient. Semua request di-mock, jadi tests ini
bisa jalan tanpa koneksi internet (penting buat CI).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from api_clients.base_client import BaseAPIClient, APIClientError


class DummyClient(BaseAPIClient):
    BASE_URL = "https://example.test/api"


class AuthedDummyClient(BaseAPIClient):
    BASE_URL = "https://example.test/api"

    def _auth_headers(self):
        if not self.api_key:
            raise ValueError("butuh api_key")
        return {"Authorization": f"Bearer {self.api_key}"}


def test_base_url_required():
    class NoBaseUrlClient(BaseAPIClient):
        BASE_URL = ""

    with pytest.raises(ValueError):
        NoBaseUrlClient()


def test_get_success(requests_mock):
    requests_mock.get("https://example.test/api/ping", json={"ok": True})
    client = DummyClient()
    result = client.get("/ping")
    assert result == {"ok": True}


def test_get_failure_raises_api_client_error(requests_mock):
    requests_mock.get("https://example.test/api/broken", status_code=500)
    client = DummyClient(max_retries=1)
    with pytest.raises(APIClientError):
        client.get("/broken")


def test_auth_header_injected(requests_mock):
    requests_mock.get(
        "https://example.test/api/secure",
        json={"secure": True},
        request_headers={"Authorization": "Bearer secret123"},
    )
    client = AuthedDummyClient(api_key="secret123")
    result = client.get("/secure")
    assert result == {"secure": True}


def test_context_manager_closes_session():
    with DummyClient() as client:
        assert client.session is not None
    # session.close() dipanggil otomatis, tidak ada assertion langsung
    # tapi memastikan __exit__ tidak melempar error
