# Creando nuestro resolver!!!

Este repositorio dedicado a la actividad solo se compone de `resolver.py`. No hay estructuras mas complejas de las pedidas en el laboratorio: Crear un emisor de mensajes, crear un parse y crear un resolver.

## Como correr mi resolver?
Para correrlo deben considerar que se realizo con un entorno virtual por lo que deben seguir los siguientes pasos.

1. Creamos nuestro entrono virutal
`python3 -m venv venv `

2. Lo activamos 
`source venv/bin/activate`

3. Instalamos dependencias
`pip install -r requirements.txt`


## Sobre los experimentos
Antes que nada mencionar lo siguiente. La parte del cache no fue realizado por tiempo (:c). Lass pruebas de funcionalidad retornan correctamente los elementos solicitados.

Se utilizaron udp sockets debido a que el protocolo de DNS ocupa sockets orientados a conexion.

Ahora volviendo a los experimentos.
Al acceder a la pagina de `www.webofscience.com` queda en bucle al resaltar la naturaleza de nuestro resolver que intentar obtener la IP de los NS intermedios repetidamente. Para el siguiente experimento en realidad al no alcanzar ningun server, no existe el dominio en la raiz. (ultimo exp no lo realice)