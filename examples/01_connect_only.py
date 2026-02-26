from __future__ import annotations

from _common import cfg_from_env_or_defaults
from pycmcontrol_mqtt import CmControlClient
from pycmcontrol_mqtt.errors import CmcConnectionError, CmcConnectionTimeout, CmcMqttAuthError

cfg = cfg_from_env_or_defaults()

try:
    with CmControlClient(cfg, debug=True) as cmc:
        print("Conectado ao broker. Device online publicado.")
except CmcMqttAuthError as e:
    print("Auth MQTT falhou:", e)
except CmcConnectionTimeout as e:
    print("Timeout conexão:", e)
except CmcConnectionError as e:
    print("Falha conexão:", e)