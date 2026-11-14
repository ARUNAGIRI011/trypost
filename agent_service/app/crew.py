from crewai import Agent, Crew, LLM, Process, Task

from .schemas import CampaignPlan
from .settings import settings


def build_plan(inputs: dict) -> CampaignPlan:
    llm = LLM(
        model=settings.nvidia_model,
        custom_openai=True,
        base_url=settings.nvidia_base_url,
        api_key=settings.nvidia_api_key,
        temperature=0.35,
    )
    strategist = Agent(
        role='Digital Marketing Strategist',
        goal='Create a factual, audience-aware campaign strategy for the supplied video.',
        backstory='You plan ethical campaigns for educational and Tamil-language creator channels.',
        llm=llm, allow_delegation=False, verbose=False,
    )
    copywriter = Agent(
        role='Multichannel Tamil Content Copywriter',
        goal='Write distinct, native-feeling promotional copy for each requested social account.',
        backstory='You write clear Tamil and English social copy, adapting length and style by platform.',
        llm=llm, allow_delegation=False, verbose=False,
    )
    reviewer = Agent(
        role='Marketing Quality and Claims Reviewer',
        goal='Remove unsupported claims, misleading hooks, spam language and platform-inappropriate copy.',
        backstory='You protect creator trust and keep educational and spiritual content respectful and accurate.',
        llm=llm, allow_delegation=False, verbose=False,
    )
    strategy = Task(
        description='Analyze the supplied campaign JSON. Identify the topic, audience, truthful angle, CTA and factual boundaries. Use only transcript-supported claims. Input: {campaign_json}',
        expected_output='A concise campaign strategy with topic, audience, angle and factual boundaries.',
        agent=strategist,
    )
    write = Task(
        description='Create exactly one promotional post for every destination in the campaign JSON. Preserve each social_account_id. Adapt copy by platform and requested language. Use restrained relevant hashtags. Never invent miracles, healing outcomes, historical facts or guaranteed reach. Return structured CampaignPlan output. Input: {campaign_json}',
        expected_output='Structured CampaignPlan with one post per requested destination.',
        agent=copywriter, context=[strategy], output_pydantic=CampaignPlan,
    )
    review = Task(
        description='Review each post for factual support, readability, cultural respect, spam and platform fit. Preserve exactly one post per requested destination and all account IDs. Return the corrected complete CampaignPlan and any cautions.',
        expected_output='Reviewed structured CampaignPlan.',
        agent=reviewer, context=[strategy, write], output_pydantic=CampaignPlan,
    )
    result = Crew(agents=[strategist, copywriter, reviewer], tasks=[strategy, write, review], process=Process.sequential, verbose=False).kickoff(inputs={'campaign_json': inputs})
    if result.pydantic is None:
        raise ValueError('Nemotron did not return structured CampaignPlan output.')
    plan = result.pydantic
    expected = {d['social_account_id'] for d in inputs['destinations']}
    actual = [p.social_account_id for p in plan.posts]
    if set(actual) != expected or len(actual) != len(expected):
        raise ValueError('Generated destinations do not match requested TryPost social accounts.')
    return plan
