# TryPost Nemotron Marketing Agents

A separate CrewAI service adding campaign planning, Tamil/English copy generation, quality review, human approval and TryPost queue scheduling. It does not replace TryPost's composer, social connectors, scheduler, MCP server or analytics.

## Architecture

- TryPost remains the publishing system and owns connected social accounts, platform rules, media and scheduled posts.
- CrewAI runs three sequential roles: campaign strategist, multichannel copywriter and claims/compliance reviewer.
- NVIDIA Nemotron NIM is accessed through its OpenAI-compatible Chat Completions endpoint.
- Supabase Free PostgreSQL is the only application database. TryPost Laravel migrations and the agent campaign table share the same Supabase Postgres database.
- Redis remains TryPost's queue/cache service; it is not a relational database.

## Configure

1. Configure TryPost's .env for Supabase PostgreSQL. Use the direct connection if the host supports IPv6; otherwise use Supabase shared pooler SESSION mode on port 5432. Do not use transaction mode for this long-lived SQLAlchemy service.
2. Run TryPost migrations after reviewing the migration: php artisan migrate --force.
3. Copy agent_service/.env.example to agent_service/.env.
4. Set AGENT_API_KEY to a long random secret, NVIDIA_API_KEY, DATABASE_URL, TRYPOST_API_BASE_URL (include /api) and TRYPOST_API_KEY (TryPost Settings -> API Keys).
5. Start from repository root: docker compose -f compose.yaml -f agent_service/compose.agent.yaml up -d --build nemotron-marketing-agent.

The root Compose file still starts its local PostgreSQL service for default TryPost development. For Supabase deployment, configure the app container DB environment and use a Compose override that removes the pgsql service and its depends_on entry. Do not leave DB_HOST=pgsql hardcoded in Compose; Compose environment values override .env.

## API

All endpoints except /health require Authorization: Bearer AGENT_API_KEY.

Create a campaign (generates a plan only; does not publish):

~~~http
POST /campaigns
Authorization: Bearer AGENT_API_KEY
Content-Type: application/json
~~~

~~~json
{
  "title": "Shivaratri: the meaning of the night",
  "source_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "transcript": "Paste an authorized transcript here; at least 30 characters.",
  "language": "Tamil",
  "audience": "Tamil-speaking spirituality audience",
  "destinations": [
    {"social_account_id": "TRYPOST_ACCOUNT_UUID", "platform": "youtube"},
    {"social_account_id": "ANOTHER_ACCOUNT_UUID", "platform": "instagram"}
  ]
}
~~~

Review the returned campaign plan. Then explicitly approve it:

~~~http
POST /campaigns/{campaign_id}/approve
Authorization: Bearer AGENT_API_KEY
~~~

Approval sends POST /api/posts/batch to TryPost with status=scheduled and queue=next. Each channel must already have a posting schedule. TryPost validates platform-specific constraints. The agent transitions pending_approval -> scheduling before the external call. On error or timeout it sets scheduling_failed_manual_check and does not retry automatically, because TryPost may have accepted the batch before a timeout.

Check status using GET /campaigns/{campaign_id}.

## Current implementation scope

Implemented: text-only campaign plan generation, three-agent review, Supabase/PostgreSQL persistence, API-key protected endpoints, explicit approval, TryPost batch queue adapter.

Not yet implemented: automatic YouTube transcript retrieval, video/media upload, external keyword research, public-community discovery, direct group posting, paid advertising campaign management, automated analytics optimization or frontend dashboard. These require separate provider permissions and integrations.

No arbitrary Facebook/Reddit/WhatsApp group posting is attempted. Community sharing must respect official APIs, group rules and human permission.

Keep AGENT_API_KEY, NVIDIA_API_KEY, Supabase database password and TryPost API key server-side. Never commit .env files. TryPost is AGPL-3.0: preserve notices and comply with corresponding-source requirements if distributing or operating a modified network service.
