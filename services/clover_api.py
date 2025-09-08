import httpx
import os

BASE_URL = os.getenv("CLOVER_BASE_URL", "https://apisandbox.dev.clover.com/v3/merchants")


class CloverAPI:
    def __init__(self, merchant_id: str, access_token: str):
        self.merchant_id = merchant_id
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {access_token}"}

    async def get_items(self, limit: int = 100, offset: int = 0, expand: str | None = None):
        url = f"{BASE_URL}/{self.merchant_id}/items"
        params = {"limit": limit, "offset": offset}
        if expand:
            params["expand"] = expand
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=self.headers, params=params)
            return r.json()

    async def get_categories(self, limit: int = 100, offset: int = 0):
        url = f"{BASE_URL}/{self.merchant_id}/categories"
        params = {"limit": limit, "offset": offset}
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=self.headers, params=params)
            return r.json()

    async def get_modifier_groups(self, limit: int = 100, offset: int = 0):
        url = f"{BASE_URL}/{self.merchant_id}/modifier_groups"
        params = {"limit": limit, "offset": offset}
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=self.headers, params=params)
            return r.json()
