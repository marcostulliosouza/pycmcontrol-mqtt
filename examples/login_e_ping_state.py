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
    token = cmc.login_oauth2()
    print("token ok?", bool(token))
    # agora fique rodando, o CmControl pode enviar /get/ping e /get/state
    input("Conectado. Pressione Enter para sair...\n")