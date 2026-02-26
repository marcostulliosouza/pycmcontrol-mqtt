from __future__ import annotations

from _common import cfg_from_env_or_defaults
from pycmcontrol_mqtt import CmControlClient, Evidence
from pycmcontrol_mqtt.errors import CmcApontamentoError

SERIAL = "00000203030300"

cfg = cfg_from_env_or_defaults()

evi = Evidence.from_text(
    nome="log_teste",
    extensao="txt",
    texto="Teste de evidência do pycmcontrol-mqtt",
    descricao="Log de teste",
)

with CmControlClient(cfg, debug=True) as cmc:
    try:
        cmc.ensure_login()
        resp = cmc.apontar_serial(SERIAL, evidencias=[evi])
        print("OK:", resp)
    except CmcApontamentoError as e:
        print("Falhou:", e.status, e.log)
        print("Exchange:", cmc.last_exchange())
    finally:
        cmc.logout_oauth2()