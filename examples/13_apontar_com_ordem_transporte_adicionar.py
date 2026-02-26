from __future__ import annotations

from _common import cfg_from_env_or_defaults
from pycmcontrol_mqtt import CmControlClient, Apontamento, Serial
from pycmcontrol_mqtt.errors import CmcApontamentoError

ORT = "ORT000000001"
cfg = cfg_from_env_or_defaults()

ap = Apontamento(
    ok=True,
    serial = Serial(codigo='1231213123')
)

with CmControlClient(cfg, debug=True) as cmc:
    try:
        cmc.ensure_login()
        resp = cmc.ordem_transporte(ORT, acao="ADICIONAR_TRANSPORTE", apontamentos=[ap])
        print("OK:", resp)
    except CmcApontamentoError as e:
        print("Falhou:", e.status, e.log)
        print("Exchange:", cmc.last_exchange())
    finally:
        cmc.logout_oauth2()