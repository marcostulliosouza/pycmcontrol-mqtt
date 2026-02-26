from __future__ import annotations

import time

from _common import cfg_from_env_or_defaults
from pycmcontrol_mqtt import CmControlClient

cfg = cfg_from_env_or_defaults()

with CmControlClient(cfg, debug=True) as cmc:
    for i in range(5):
        cmc.ensure_login()
        print("Iter", i, "token ok?", cmc.is_token_valid())
        time.sleep(1)
    cmc.logout_oauth2()