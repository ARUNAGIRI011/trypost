import httpx

from .settings import settings


class TryPostClient:
    async def schedule_approved_campaign(self, plan: dict) -> dict:
        payload = {
            'status': 'scheduled',
            'queue': 'next',
            'destinations': [
                {'social_account_id': post['social_account_id'], 'content': post['content']}
                for post in plan['posts']
            ],
        }
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(
                f"{settings.trypost_api_base_url.rstrip('/')}/posts/batch",
                headers={
                    'Authorization': f'Bearer {settings.trypost_api_key}',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                json=payload,
            )
            response.raise_for_status()
            return response.json()
