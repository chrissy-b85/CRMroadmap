"""Comprehensive test suite for the /providers API endpoints."""
import pytest
from httpx import AsyncClient

from app.utils.abn import validate_abn

pytestmark = pytest.mark.asyncio

# ---------------------------------------------------------------------------
# Known valid ABNs for unit-testing the validation algorithm
# ---------------------------------------------------------------------------

# ATO ABN: 51 824 753 556
VALID_ABN = "51824753556"
# Another well-known valid ABN (Australian Taxation Office variant)
VALID_ABN_2 = "53004085616"
# Invalid ABNs
INVALID_ABN = "12345678901"
INVALID_ABN_SHORT = "1234567890"


def make_provider_payload(abn: str = VALID_ABN, **kwargs) -> dict:
    """Return a minimal valid provider payload."""
    return {
        "business_name": kwargs.pop("business_name", "Acme Support Services"),
        "abn": abn,
        "registration_group": kwargs.pop("registration_group", "Daily Activities"),
        "email": kwargs.pop("email", "acme@example.com"),
        "phone": kwargs.pop("phone", "0298765432"),
        "address": kwargs.pop("address", "1 Provider St, Sydney NSW 2000"),
        "bank_bsb": kwargs.pop("bank_bsb", "062000"),
        "bank_account": kwargs.pop("bank_account", "12345678"),
        "bank_account_name": kwargs.pop("bank_account_name", "Acme Support Services"),
        **kwargs,
    }


# ---------------------------------------------------------------------------
# ABN utility unit tests
# ---------------------------------------------------------------------------


def test_validate_abn_known_valid():
    """Known valid ABN (ATO: 51 824 753 556) should pass."""
    assert validate_abn("51824753556") is True
    assert validate_abn("51 824 753 556") is True  # spaces stripped


def test_validate_abn_invalid():
    """Known invalid ABN should fail."""
    assert validate_abn(INVALID_ABN) is False
    assert validate_abn("00000000000") is False


def test_validate_abn_wrong_length():
    """ABN with wrong length should fail."""
    assert validate_abn(INVALID_ABN_SHORT) is False
    assert validate_abn("123456789012") is False


# ---------------------------------------------------------------------------
# Provider creation
# ---------------------------------------------------------------------------


async def test_create_provider_success(test_client: AsyncClient):
    """POST /providers/ returns 201 with correct response body."""
    payload = make_provider_payload()
    resp = await test_client.post("/api/v1/providers/", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["business_name"] == payload["business_name"]
    assert body["abn"] == VALID_ABN
    assert body["is_active"] is True
    assert "id" in body


async def test_create_provider_invalid_abn(test_client: AsyncClient):
    """POST /providers/ with invalid ABN returns 422."""
    payload = make_provider_payload(abn=INVALID_ABN)
    resp = await test_client.post("/api/v1/providers/", json=payload)
    assert resp.status_code == 422


async def test_create_provider_duplicate_abn(test_client: AsyncClient):
    """POST /providers/ with duplicate ABN returns 409."""
    payload = make_provider_payload(abn=VALID_ABN_2)
    first = await test_client.post("/api/v1/providers/", json=payload)
    assert first.status_code == 201

    second = await test_client.post("/api/v1/providers/", json=payload)
    assert second.status_code == 409


async def test_bank_account_masked_in_response(test_client: AsyncClient):
    """Bank account in responses shows only last 3 digits masked."""
    abn = "83914571673"  # another valid ABN
    payload = make_provider_payload(abn=abn, bank_account="987654321")
    resp = await test_client.post("/api/v1/providers/", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["bank_account_masked"] == "***321"
    assert "bank_account" not in body


# ---------------------------------------------------------------------------
# Listing providers
# ---------------------------------------------------------------------------


async def test_list_providers(test_client: AsyncClient):
    """GET /providers/ returns paginated list."""
    resp = await test_client.get("/api/v1/providers/")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert "page" in body
    assert "page_size" in body
    assert isinstance(body["items"], list)


async def test_search_providers_by_name(test_client: AsyncClient):
    """search param filters by business name."""
    unique_name = "ZephyrineSupport"
    abn = "26008672179"  # valid ABN
    payload = make_provider_payload(abn=abn, business_name=unique_name)
    create_resp = await test_client.post("/api/v1/providers/", json=payload)
    assert create_resp.status_code == 201

    resp = await test_client.get(f"/api/v1/providers/?search={unique_name}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert any(p["business_name"] == unique_name for p in body["items"])


async def test_search_providers_by_abn(test_client: AsyncClient):
    """search param filters by ABN."""
    abn = "49638346578"  # valid ABN
    payload = make_provider_payload(abn=abn)
    create_resp = await test_client.post("/api/v1/providers/", json=payload)
    assert create_resp.status_code == 201

    resp = await test_client.get(f"/api/v1/providers/?search={abn}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert any(p["abn"] == abn for p in body["items"])


# ---------------------------------------------------------------------------
# Getting a single provider
# ---------------------------------------------------------------------------


async def test_get_provider_by_id(test_client: AsyncClient):
    """GET /providers/{id} returns 200 with correct provider."""
    abn = "60103105183"  # valid ABN
    payload = make_provider_payload(abn=abn)
    create_resp = await test_client.post("/api/v1/providers/", json=payload)
    assert create_resp.status_code == 201
    pid = create_resp.json()["id"]

    resp = await test_client.get(f"/api/v1/providers/{pid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == pid


async def test_get_provider_not_found(test_client: AsyncClient):
    """GET /providers/{non-existent-id} returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await test_client.get(f"/api/v1/providers/{fake_id}")
    assert resp.status_code == 404


async def test_get_provider_by_abn(test_client: AsyncClient):
    """GET /providers/abn/{abn} returns 200 with correct provider."""
    abn = "33051775556"  # valid ABN
    payload = make_provider_payload(abn=abn)
    create_resp = await test_client.post("/api/v1/providers/", json=payload)
    assert create_resp.status_code == 201

    resp = await test_client.get(f"/api/v1/providers/abn/{abn}")
    assert resp.status_code == 200
    assert resp.json()["abn"] == abn


# ---------------------------------------------------------------------------
# Updating a provider
# ---------------------------------------------------------------------------


async def test_update_provider(test_client: AsyncClient):
    """PATCH /providers/{id} updates specified fields and returns 200."""
    abn = "45433036541"  # valid ABN
    payload = make_provider_payload(abn=abn)
    create_resp = await test_client.post("/api/v1/providers/", json=payload)
    assert create_resp.status_code == 201
    pid = create_resp.json()["id"]

    resp = await test_client.patch(
        f"/api/v1/providers/{pid}", json={"business_name": "Updated Name"}
    )
    assert resp.status_code == 200
    assert resp.json()["business_name"] == "Updated Name"


# ---------------------------------------------------------------------------
# Deactivating a provider
# ---------------------------------------------------------------------------


async def test_deactivate_provider(test_client: AsyncClient):
    """DELETE /providers/{id} returns 204 and provider is deactivated."""
    abn = "59901627204"  # valid ABN
    payload = make_provider_payload(abn=abn)
    create_resp = await test_client.post("/api/v1/providers/", json=payload)
    assert create_resp.status_code == 201
    pid = create_resp.json()["id"]

    resp = await test_client.delete(f"/api/v1/providers/{pid}")
    assert resp.status_code == 204

    get_resp = await test_client.get(f"/api/v1/providers/{pid}")
    assert get_resp.status_code == 200
    assert get_resp.json()["is_active"] is False
