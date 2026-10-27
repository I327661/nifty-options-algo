from typing import Tuple, Type
from pydantic import BaseModel
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, YamlConfigSettingsSource


class RiskConfig(BaseModel):
    lot_size: int = 65
    max_capital_per_trade_pct: float = 0.02
    daily_loss_limit_pct: float = 0.01
    max_open_positions: int = 3
    default_sl_pct: float = 0.30
    default_target_pct: float = 0.60
    illiquid_premium_threshold: float = 5.0
    brokerage_per_order: float = 20.0
    account_capital: float = 100000.0


class BrokerConfig(BaseModel):
    name: str = "fyers"
    app_id: str = ""
    access_token: str = ""


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        yaml_file="config/settings.yaml",
        env_file="config/.env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    risk: RiskConfig = RiskConfig()
    broker: BrokerConfig = BrokerConfig()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        **kwargs: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            kwargs.get("init_settings"),
            kwargs.get("env_settings"),
            kwargs.get("dotenv_settings"),
            YamlConfigSettingsSource(settings_cls),
        )


def load_config() -> AppConfig:
    return AppConfig()
