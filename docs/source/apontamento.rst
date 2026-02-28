Apontamento
===========

Apontamento simples
-------------------

.. code-block:: python

   with CmControlClient(cfg) as cmc:
       cmc.ensure_login()
       resp = cmc.apontar_serial("00000203030300")
       print(resp)

Payload equivalente:

.. code-block:: json

   {
     "enderecoDispositivo": "device001",
     "apontamentos": [
       {
         "ok": true,
         "seriais": [
           { "codigo": "00000203030300" }
         ]
       }
     ]
   }