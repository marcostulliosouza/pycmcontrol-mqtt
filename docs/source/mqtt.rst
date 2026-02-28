Comunicação MQTT
================

Eventos obrigatórios do driver
------------------------------

Quando conectado, o cliente responde automaticamente:

+-------------------+------------------------------+
| Evento recebido   | Resposta enviada             |
+===================+==============================+
| /get/ping         | /set/pong com timestamp      |
+-------------------+------------------------------+
| /get/state        | /set/state {"state":"1"}     |
+-------------------+------------------------------+

Também envia state=1 ao conectar.

Métodos principais
------------------

- publish_set(endpoint, payload)
- request(endpoint, payload)
- ping()