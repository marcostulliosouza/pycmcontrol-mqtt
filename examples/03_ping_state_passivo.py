from __future__ import annotations

from _common import cfg_from_env_or_defaults
from pycmcontrol_mqtt import CmControlClient
from pycmcontrol_mqtt.errors import CmcTimeout

cfg = cfg_from_env_or_defaults()

with CmControlClient(cfg, debug=True) as cmc:
    try:
        resp = cmc.ping(timeout_s=5)
        print("PONG recebido:", resp)
    except CmcTimeout as e:
        print("Não veio PONG:", e)