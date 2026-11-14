import hmac
import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .crew import build_plan
from .db import SessionLocal
from .models import MarketingCampaign
from .schemas import CampaignCreated, CampaignRequest, CampaignStatus
from .settings import settings
from .trypost import TryPostClient

app = FastAPI(title='TryPost Nemotron Marketing Agents', version='0.1.0')
bearer = HTTPBearer(auto_error=False)


def require_agent_key(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> None:
    if credentials is None or not hmac.compare_digest(credentials.credentials, settings.agent_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid agent API key')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/health')
def health(db: Session = Depends(get_db)):
    db.execute(text('select 1'))
    return {'status': 'ok', 'database': 'connected'}


@app.post('/campaigns', response_model=CampaignCreated, dependencies=[Depends(require_agent_key)])
def create_campaign(request: CampaignRequest, db: Session = Depends(get_db)):
    data = request.model_dump(mode='json')
    try:
        plan = build_plan(data)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'Nemotron campaign generation failed: {exc}') from exc
    campaign = MarketingCampaign(
        title=request.title,
        source_url=str(request.source_url) if request.source_url else None,
        language=request.language,
        status='pending_approval',
        input_data=data,
        plan=plan.model_dump(mode='json'),
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return CampaignCreated(campaign_id=str(campaign.id), status=campaign.status, plan=plan)


@app.get('/campaigns/{campaign_id}', response_model=CampaignStatus, dependencies=[Depends(require_agent_key)])
def get_campaign(campaign_id: uuid.UUID, db: Session = Depends(get_db)):
    campaign = db.get(MarketingCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail='Campaign not found')
    return CampaignStatus(campaign_id=str(campaign.id), status=campaign.status, trypost_response=campaign.trypost_response)


@app.post('/campaigns/{campaign_id}/approve', response_model=CampaignStatus, dependencies=[Depends(require_agent_key)])
async def approve_campaign(campaign_id: uuid.UUID, db: Session = Depends(get_db)):
    campaign = db.execute(select(MarketingCampaign).where(MarketingCampaign.id == campaign_id).with_for_update()).scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=404, detail='Campaign not found')
    if campaign.status != 'pending_approval':
        raise HTTPException(status_code=409, detail=f'Campaign is {campaign.status}; only pending_approval can be approved.')

    # Persist a one-way transition before the external API call. Never blindly
    # retry after a timeout: TryPost may have accepted the batch already.
    campaign.status = 'scheduling'
    campaign.approved_at = datetime.now(timezone.utc)
    db.commit()
    try:
        response = await TryPostClient().schedule_approved_campaign(campaign.plan)
    except Exception as exc:
        campaign = db.get(MarketingCampaign, campaign_id)
        campaign.status = 'scheduling_failed_manual_check'
        campaign.error_message = str(exc)[:4000]
        db.commit()
        raise HTTPException(status_code=502, detail='TryPost scheduling failed or timed out. Inspect TryPost before retrying to prevent duplicate posts.') from exc

    campaign = db.get(MarketingCampaign, campaign_id)
    campaign.status = 'scheduled'
    campaign.trypost_response = response
    db.commit()
    return CampaignStatus(campaign_id=str(campaign.id), status=campaign.status, trypost_response=response)
