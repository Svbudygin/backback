import requests

from app.core.redis import rediss
from app.core.config import settings
from app.schemas.AnalyticsSchema import PowerBIResponseSchema


REDIS_KEY = "POWERBI_TOKEN"
REDIS_EXP_TIME = 3600


def _generate_token():
    auth_url = f"https://login.microsoftonline.com/{settings.ANALIZATOR_TENANT_ID}/oauth2/v2.0/token"

    auth_payload = {
        "grant_type": "client_credentials",
        "client_id": settings.ANALIZATOR_CLIENT_ID,
        "client_secret": settings.ANALIZATOR_CLIENT_SECRET,
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }

    auth_resp = requests.post(auth_url, data=auth_payload)
    auth_resp.raise_for_status()
    access_token = auth_resp.json()["access_token"]

    report_id = settings.ANALIZATOR_REPORT_ID
    group_id = settings.ANALIZATOR_GROUP_ID

    embed_url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/reports/{report_id}/GenerateToken"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    embed_payload = {
        "accessLevel": "View"
    }

    embed_resp = requests.post(embed_url, json=embed_payload, headers=headers)
    embed_resp.raise_for_status()
    embed_token = embed_resp.json()["token"]

    return embed_token


async def _generate_token_and_save_to_redis():
    token = _generate_token()

    await rediss.setex(REDIS_KEY, REDIS_EXP_TIME, token)

    return token


async def _get_token():
    try:
        token = await rediss.get(REDIS_KEY)

        if token:
            return token

        return await _generate_token_and_save_to_redis()
    except Exception as e:
        return await _generate_token_and_save_to_redis()


async def get_powerbi_report_data(hard_refresh: bool):
    return PowerBIResponseSchema(
        reportId=settings.ANALIZATOR_REPORT_ID,
        embedUrl=f"https://app.powerbi.com/reportEmbed?reportId=${settings.ANALIZATOR_REPORT_ID}&groupId={settings.ANALIZATOR_GROUP_ID}",
        embedToken= await _generate_token_and_save_to_redis() if hard_refresh else await _get_token()
    )
