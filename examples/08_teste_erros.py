from __future__ import annotations

from pycmcontrol_mqtt import CmControlClient, CmControlConfig
from pycmcontrol_mqtt.errors import (
    CmcDnsError,
    CmcConnectionTimeout,
    CmcConnectionError,
    CmcLoginError,
)

# 1) DNS inválido => CmcDnsError
cfg_dns = CmControlConfig(
    device_addr="device001",
    broker_host="nao-existe.localdomain",
    broker_port=1883,
    mqtt_user="x",
    mqtt_pass="y",
    api_user="u",
    api_pass="p",
)

try:
    with CmControlClient(cfg_dns) as cmc:
        pass
except CmcDnsError as e:
    print("[OK] DNS erro capturado:", e)

# 2) Porta errada => timeout/conexão
cfg_port = CmControlConfig(
    device_addr="device001",
    broker_host="127.0.0.1",
    broker_port=19999,
    mqtt_user="x",
    mqtt_pass="y",
    api_user="u",
    api_pass="p",
)

try:
    with CmControlClient(cfg_port) as cmc:
        pass
except (CmcConnectionTimeout, CmcConnectionError) as e:
    print("[OK] Conexão/timeout capturado:", e)

# 3) Login inválido (precisa broker real)
# Rode somente se tiver broker válido:
# with CmControlClient(cfg_real, debug=True) as cmc:
#     try:
#         cmc.login_oauth2()
#     except CmcLoginError as e:
#         print("[OK] Login erro:", e.status, e.log)