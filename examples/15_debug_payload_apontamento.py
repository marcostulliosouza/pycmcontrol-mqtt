from __future__ import annotations

import json

from _common import cfg_from_env_or_defaults
from pycmcontrol_mqtt import SetupApontamento, Apontamento, Serial

cfg = cfg_from_env_or_defaults()

setup = SetupApontamento(
    enderecoDispositivo=cfg.device_addr,
    apontamentos=[Apontamento(ok=True, serial=Serial("00000203030300"))],
)

print(json.dumps(setup.to_dict(), indent=2, ensure_ascii=False))