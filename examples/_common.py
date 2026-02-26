from __future__ import annotations

import os
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path
from pycmcontrol_mqtt import CmControlConfig


def cfg_from_env_or_defaults(
    *,
    device_addr: Optional[str] = None,
    broker_host: Optional[str] = None,
    broker_port: Optional[int] = None,
    mqtt_user: Optional[str] = None,
    mqtt_pass: Optional[str] = None,
    api_user: Optional[str] = None,
    api_pass: Optional[str] = None,
) -> CmControlConfig:
    """
    Permite rodar exemplos: define por ENV se existir.
    ENV sugeridas:
      CMC_DEVICE_ADDR, CMC_BROKER_HOST, CMC_BROKER_PORT, CMC_MQTT_USER, CMC_MQTT_PASS, CMC_API_USER, CMC_API_PASS
    """

    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        pass
    return CmControlConfig(
        device_addr=device_addr or os.getenv("CMC_DEVICE_ADDR", "device001"),
        broker_host=broker_host or os.getenv("CMC_BROKER_HOST", "localhost"),
        broker_port=int(broker_port or os.getenv("CMC_BROKER_PORT", "1883")),
        mqtt_user=mqtt_user or os.getenv("CMC_MQTT_USER", ""),
        mqtt_pass=mqtt_pass or os.getenv("CMC_MQTT_PASS", ""),
        api_user=api_user or os.getenv("CMC_API_USER", ""),
        api_pass=api_pass or os.getenv("CMC_API_PASS", ""),
    )