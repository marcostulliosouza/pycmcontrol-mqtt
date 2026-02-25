import time
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

seriais = ["S1", "S2", "S3"]

with CmControlClient(cfg) as cmc:
    cmc.ensure_login()

    for s in seriais:
        resp = cmc.apontar_serial(s)
        print(s, resp.get("status"), resp.get("log"))
        time.sleep(0.2)