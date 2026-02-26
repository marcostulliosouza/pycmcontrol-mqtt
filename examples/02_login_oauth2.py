from __future__ import annotations

from _common import cfg_from_env_or_defaults
from pycmcontrol_mqtt import CmControlClient
from pycmcontrol_mqtt.errors import CmcLoginError

cfg = cfg_from_env_or_defaults()

with CmControlClient(cfg, debug=True) as cmc:
    try:
        tok = cmc.login_oauth2()
        print("Token obtido:", tok[:12] + "...")
        print("Token válido?", cmc.is_token_valid())
    except CmcLoginError as e:
        print("Falha login:", e.status, e.log)
        print("Exchange:", cmc.last_exchange())
    finally:
        cmc.logout_oauth2()