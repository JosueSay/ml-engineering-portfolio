"""Configuración de referencia que viaja dentro del paquete.

Existe para que quien instale la distribución pueda ejecutarla desde cualquier
carpeta sin haber clonado el repositorio. Sin esto, el paquete instalado busca
la configuración junto al código y no la encuentra.

No sustituye a `config/config.yaml` en el repositorio: ese sigue siendo el que
se edita durante el desarrollo, y tiene preferencia cuando está presente. Este
es el respaldo, y su contenido debe mantenerse igual al otro.
"""
