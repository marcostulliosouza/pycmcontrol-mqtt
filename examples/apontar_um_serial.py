from pycmcontrol_mqtt import CmControlClient, CmControlConfig

cfg = CmControlConfig(
    device_addr="device001",
    broker_host="10.0.0.5",
    broker_port=1883,
    mqtt_user="user",
    mqtt_pass="pass",
    api_user="login",
    api_pass="senha",
)

with CmControlClient(cfg) as cmc:
    cmc.ensure_login()
    resp = cmc.apontar_serial("00000203030300")
    print(resp)