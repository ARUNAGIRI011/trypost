from pydantic import BaseModel, Field, HttpUrl


class Destination(BaseModel):
    social_account_id: str
    platform: str = Field(description='Platform name, e.g. youtube, instagram, facebook, linkedin, telegram.')
    account_label: str | None = None


class CampaignRequest(BaseModel):
    title: str = Field(min_length=2, max_length=240)
    source_url: HttpUrl | None = None
    transcript: str = Field(min_length=30, max_length=50000)
    language: str = 'Tamil'
    audience: str = 'Tamil-speaking spirituality audience'
    brand_voice: str = 'Respectful, informative, culturally sensitive; do not invent historical or spiritual claims.'
    call_to_action: str = 'Watch the full video and share your reflections.'
    destinations: list[Destination] = Field(min_length=1, max_length=12)


class GeneratedPost(BaseModel):
    social_account_id: str
    platform: str
    content: str = Field(min_length=1, max_length=25000)
    rationale: str


class CampaignPlan(BaseModel):
    campaign_angle: str
    audience_summary: str
    posts: list[GeneratedPost]
    compliance_notes: list[str] = []


class CampaignCreated(BaseModel):
    campaign_id: str
    status: str
    plan: CampaignPlan


class CampaignStatus(BaseModel):
    campaign_id: str
    status: str
    trypost_response: dict | None = None
