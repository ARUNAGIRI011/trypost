from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_prefix='', extra='ignore')

    agent_api_key: str
    nvidia_api_key: str
    nvidia_base_url: str = 'https://integrate.api.nvidia.com/v1'
    nvidia_model: str = 'nvidia/nemotron-3.5-super-vl-120b-a12b'
    database_url: str
    trypost_api_base_url: str
    trypost_api_key: str
    request_timeout_seconds: float = 30


settings = Settings()
