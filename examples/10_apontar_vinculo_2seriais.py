from __future__ import annotations

from _common import cfg_from_env_or_defaults
from pycmcontrol_mqtt import CmControlClient, SetupApontamento, Apontamento, Serial
from pycmcontrol_mqtt.errors import CmcApontamentoError

# ⚠️ Vinculação: faz sentido para 2 seriais (ou N seriais dependendo da operação),
# mas NÃO é lote "normal". Aqui é exemplo fiel à doc.
S1 = "00000203030300"
S2 = "506080999"

cfg = cfg_from_env_or_defaults()

with CmControlClient(cfg, debug=True) as cmc:
    cmc.ensure_login()

    setup = SetupApontamento(
        enderecoDispositivo=cfg.device_addr,
        apontamentos=[
            Apontamento(ok=True, seriais_vinculados=[Serial(S1), Serial(S2)]),
        ],
    )

    try:
        resp = cmc.setup_apontamento(setup)
        print("OK:", resp)
    except CmcApontamentoError as e:
        print("Falhou:", e.status, e.log)
        print("Exchange:", cmc.last_exchange())
    finally:
        cmc.logout_oauth2()