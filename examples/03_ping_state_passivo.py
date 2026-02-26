#/
#
#  Serve para validar que o CmControl está enviando /get/ping e /get/state, e você respondendo corretamente.
#
#/
from __future__ import annotations

import time

from _common import cfg_from_env_or_defaults
from pycmcontrol_mqtt import CmControlClient

cfg = cfg_from_env_or_defaults()

with CmControlClient(cfg, debug=True) as cmc:
    print("Aguardando ping/state do sistema por 60s...")
    t0 = time.time()
    while time.time() - t0 < 60:
        time.sleep(0.2)

print("Fim.")