from __future__ import annotations

from _common import cfg_from_env_or_defaults
from pycmcontrol_mqtt import CmControlClient
from pycmcontrol_mqtt.errors import CmcApontamentoError, CmcLoginError

SERIAL = "00000203030300"

cfg = cfg_from_env_or_defaults()

with CmControlClient(cfg, debug=True) as cmc:
    try:
        cmc.ensure_login()
        resp = cmc.validar_rota(SERIAL)
        print("VALIDAR_ROTA OK:", resp)
    except CmcLoginError as e:
        print("Login falhou:", e.status, e.log)
        print("Exchange:", cmc.last_exchange())
    except CmcApontamentoError as e:
        print("VALIDAR_ROTA falhou:", e.status, e.log)
        print("Exchange:", cmc.last_exchange())
    finally:
        cmc.logout_oauth2()