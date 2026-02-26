from __future__ import annotations

from pathlib import Path

from _common import cfg_from_env_or_defaults
from pycmcontrol_mqtt import CmControlClient, Evidence
from pycmcontrol_mqtt.errors import CmcApontamentoError

SERIAL = "00000203030300"
ARQ = Path(__file__).resolve().parent / "sample_log.txt"

# cria arquivo local para teste
ARQ.write_text("log de teste\nlinha2\n", encoding="utf-8")

cfg = cfg_from_env_or_defaults()

evi = Evidence.from_file(ARQ, descricao="Log de teste funcional")

with CmControlClient(cfg, debug=True) as cmc:
    cmc.ensure_login()
    try:
        resp = cmc.apontar_serial(SERIAL, evidencias=[evi])
        print("OK:", resp)
    except CmcApontamentoError as e:
        print("Falhou:", e.status, e.log)
        print("Exchange:", cmc.last_exchange())
    finally:
        cmc.logout_oauth2()