from __future__ import annotations

from _common import cfg_from_env_or_defaults
from pycmcontrol_mqtt import CmControlClient
from pycmcontrol_mqtt.errors import CmcApontamentoError

SERIAIS = [
    "00000203030300",
    "00000203030301",
    "00000203030302",
]

cfg = cfg_from_env_or_defaults()

with CmControlClient(cfg, debug=False) as cmc:
    cmc.ensure_login()
    for s in SERIAIS:
        try:
            resp = cmc.apontar_serial(s, timeout_s=15)
            print("OK", s, resp.get("status"), resp.get("log"))
        except CmcApontamentoError as e:
            print("NOK", s, e.status, e.log)
            print("Exchange:", cmc.last_exchange())
            # continue para tentar os próximos
    cmc.logout_oauth2()