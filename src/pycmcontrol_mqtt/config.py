from dataclasses import dataclass
from typing import Optional
import os


@dataclass(frozen=True)
class CmControlConfig:
    """
    Config de conexão com o broker e credenciais do CmControl (OAuth2 via MQTT+REST).

    A doc diz: credenciais do broker vêm no CmControl em:
      Menu Principal > Configurações > MQTT
    """
    device_addr: str
    broker_host: str
    broker_port: int = 1883
    mqtt_user: str = ""
    mqtt_pass: str = ""

    # OAuth2 (Basic -> access_token Bearer)
    api_user: str = ""
    api_pass: str = ""

    connect_timeout_s: int = 10
    token_renew_margin_s: int = 600  # renova antes do vencimento

    @property
    def has_api_credentials(self) -> bool:
        return bool(self.api_user and self.api_pass)

    @classmethod
    def from_env(cls, env_path: Optional[str] = None, prefix: str = "CMC_") -> "CmControlConfig":
        """
        Helper opcional (NÃO obrigatório).
        Para usar .env: pip install cmcontrol-mqtt[env]
        """
        if env_path:
            try:
                from dotenv import load_dotenv  # type: ignore
                load_dotenv(env_path)
            except Exception:
                pass

        def req(name: str) -> str:
            v = os.getenv(prefix + name, "").strip()
            if not v:
                raise ValueError(f"Missing env var: {prefix}{name}")
            return v

        def opt(name: str, default: str = "") -> str:
            return os.getenv(prefix + name, default).strip()

        def opt_int(name: str, default: int) -> int:
            v = os.getenv(prefix + name, "").strip()
            return int(v) if v else default

        return cls(
            device_addr=req("DEVICE_ADDR"),
            broker_host=req("BROKER_HOST"),
            broker_port=opt_int("BROKER_PORT", 1883),
            mqtt_user=req("MQTT_USER"),
            mqtt_pass=req("MQTT_PASS"),
            api_user=opt("API_USER", ""),
            api_pass=opt("API_PASS", ""),
            connect_timeout_s=opt_int("CONNECT_TIMEOUT_S", 10),
            token_renew_margin_s=opt_int("TOKEN_RENEW_MARGIN_S", 600),
        )