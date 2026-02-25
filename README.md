# pycmcontrol-mqtt

Biblioteca Python para integração com o **Driver Dispositivo CmControl v1.00** via MQTT, seguindo exatamente:

- REQUEST: `br/com/cmcontrol/dispositivo/{device}/set/{endpoint}`
- RESPONSE: `br/com/cmcontrol/dispositivo/{device}/get/{endpoint}`
- QoS = 0
- Retained = false
- Dispositivo deve ficar inscrito em: `br/com/cmcontrol/dispositivo/{device}/get/+`

Inclui suporte a:
- Eventos obrigatórios: `PING` e `STATE` (resposta automática quando o sistema solicitar)
- MQTT+REST proxy (`set/rest/...`) para autenticação OAuth2 e chamadas REST
- Endpoint de apontamento `rest/api/v1/setup.apontamento`

## Instalação

```bash
pip install pycmcontrol-mqtt