Uso Rápido
==========

Exemplo básico:

.. code-block:: python

   from pycmcontrol_mqtt import CmControlClient, CmControlConfig

   cfg = CmControlConfig(
       device_addr="device001",
       broker_host="cmcontrol.example.com",
       broker_port=1883,
       mqtt_user="usuario",
       mqtt_pass="senha",
       api_user="api_user",
       api_pass="api_pass",
   )

   with CmControlClient(cfg, debug=True) as cmc:
       cmc.ensure_login()