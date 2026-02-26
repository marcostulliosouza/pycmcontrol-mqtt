from __future__ import annotations

from _common import cfg_from_env_or_defaults
from pycmcontrol_mqtt import CmControlClient, SetupApontamento, OrdemTransporte
from pycmcontrol_mqtt.errors import CmcApontamentoError

ORT = "ORT000000001"

cfg = cfg_from_env_or_defaults()

with CmControlClient(cfg, debug=True) as cmc:
    cmc.ensure_login()

    setup = SetupApontamento(
        enderecoDispositivo=cfg.device_addr,
        ordemTransporte=OrdemTransporte(codigo=ORT, acao="APONTAR_TRANSPORTE"),
        apontamentos=[],  # doc mostra que pode existir só ordemTransporte
    )

    try:
        resp = cmc.setup_apontamento(setup)
        print("OK:", resp)
    except CmcApontamentoError as e:
        print("Falhou:", e.status, e.log)
        print("Exchange:", cmc.last_exchange())
    finally:
        cmc.logout_oauth2()