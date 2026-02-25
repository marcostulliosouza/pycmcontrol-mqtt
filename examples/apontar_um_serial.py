from pycmcontrol_mqtt import CmControlClient, CmControlConfig
from pycmcontrol_mqtt.errors import CmcConnectionError, CmcLoginError, CmcApontamentoError, CmcTimeout

cfg = CmControlConfig(
    device_addr="device001",
    broker_host="10.0.0.5",
    broker_port=1883,
    mqtt_user="user",
    mqtt_pass="pass",
    api_user="login",
    api_pass="senha",
)

try:
    with CmControlClient(cfg) as cmc:
        cmc.ensure_login()
        cmc.apontar_serial("00000203030300")
except CmcConnectionError as e:
    print("Falha broker:", e)
except CmcLoginError as e:
    print("Falha login:", e)
except CmcApontamentoError as e:
    print("Falha apontamento:", e.status, e.log)
except CmcTimeout as e:
    print("Timeout:", e)