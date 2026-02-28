pycmcontrol-mqtt
================

Biblioteca Python para integração com o **Driver Dispositivo CmControl v1.00** via MQTT,
implementando o protocolo oficial do sistema.

Permite que aplicações Python atuem como um dispositivo CmControl totalmente compatível,
suportando:

- Comunicação MQTT nativa
- Proxy MQTT + REST
- Autenticação OAuth2
- Apontamento de seriais
- Envio de evidências
- TLS
- Tipagem estática (PEP 561)

.. toctree::
   :maxdepth: 2
   :caption: Conteúdo

   installation
   quickstart
   oauth2
   mqtt
   apontamento
   errors
   tls
   api
   structure