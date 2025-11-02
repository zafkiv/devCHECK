# services/neynar.py
import aiohttp
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class NeynarService:
    """Сервис для работы с Neynar API"""
    
    BASE_URL = "https://api.neynar.com/v2/farcaster"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "accept": "application/json",
            "api_key": api_key
        }
        logger.info(f"✅ Using Client ID: {api_key[:12]}...")
    
    async def get_user_by_fid(self, fid: int) -> Optional[Dict]:
        """Получить информацию о пользователе по FID"""
        url = f"{self.BASE_URL}/user/bulk"
        params = {"fids": str(fid)}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status != 200:
                        logger.error(f"❌ API error: {response.status}")
                        return None
                    
                    data = await response.json()
                    
                    if not data.get("users"):
                        logger.warning(f"⚠️ User {fid} not found")
                        return None
                    
                    user = data["users"][0]
                    logger.info(f"✅ User {fid} found: @{user['username']}")
                    
                    return {
                        'fid': user['fid'],
                        'username': user['username'],
                        'display_name': user.get('display_name', ''),
                        'pfp_url': user.get('pfp_url', ''),
                        'profile': user.get('profile', {}),
                        'follower_count': user.get('follower_count', 0),
                        'following_count': user.get('following_count', 0)
                    }
        except Exception as e:
            logger.error(f"❌ Error fetching user {fid}: {e}")
            return None
    
    async def get_user_casts(self, fid: int, limit: int = 25) -> List[Dict]:
        """Получить касты пользователя"""
        url = f"{self.BASE_URL}/feed/user/casts"
        params = {
            "fid": fid,
            "limit": limit
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status != 200:
                        logger.error(f"❌ API error: {response.status}")
                        return []
                    
                    data = await response.json()
                    casts = data.get("casts", [])
                    
                    logger.info(f"✅ Retrieved {len(casts)} casts for FID {fid}")
                    
                    result = []
                    for cast in casts:
                        result.append({
                            'hash': cast['hash'],
                            'text': cast['text'],
                            'timestamp': cast['timestamp'],
                            'author_fid': cast['author']['fid'],
                            'reactions': cast.get('reactions', {}),
                            'replies': cast.get('replies', {})
                        })
                    
                    return result
        except Exception as e:
            logger.error(f"❌ Error fetching casts for {fid}: {e}")
            return []
    
    async def get_cast_by_hash(self, cast_hash: str) -> Optional[Dict]:
        """Получить информацию о касте по hash"""
        url = f"{self.BASE_URL}/cast"
        params = {"identifier": cast_hash, "type": "hash"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status != 200:
                        logger.error(f"❌ API error: {response.status}")
                        return None
                    
                    data = await response.json()
                    cast = data.get("cast")
                    
                    if not cast:
                        logger.warning(f"⚠️ Cast {cast_hash} not found")
                        return None
                    
                    return {
                        'hash': cast['hash'],
                        'text': cast['text'],
                        'timestamp': cast['timestamp'],
                        'author': cast['author'],
                        'reactions': cast.get('reactions', {}),
                        'replies': cast.get('replies', {})
                    }
        except Exception as e:
            logger.error(f"❌ Error fetching cast {cast_hash}: {e}")
            return None