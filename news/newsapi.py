from typing import Optional

import aiohttp

__all__ = ['get_everything']

_API_KEY = open('api-key', 'r').read()
_ENDPOINT = 'https://newsapi.org/v2/everything'
_SESSION: Optional[aiohttp.ClientSession] = None


async def _get_session() -> aiohttp.ClientSession:
    global _SESSION

    if _SESSION is None:
        # Can only create a ClientSession in an async func
        _SESSION = aiohttp.ClientSession()

    return _SESSION


async def _request(url, params=None):
    session = await _get_session()
    async with session.get(url, params=params) as resp:
        return await resp.json()


async def get_everything(keyword: str):
    params = {'q': keyword, 'language': 'en', 'apiKey': _API_KEY}
    return await _request(_ENDPOINT, params=params)
