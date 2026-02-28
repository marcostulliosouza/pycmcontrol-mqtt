Autenticação OAuth2
===================

O cliente executa automaticamente:

1. Login BASIC
2. Recebimento de token JWT
3. Uso de Bearer Token nas chamadas REST

.. code-block:: python

   with CmControlClient(cfg) as cmc:
       cmc.ensure_login()

Logout opcional:

.. code-block:: python

   cmc.logout_oauth2()