"""Automate simplifié (esclave Modbus TCP) - pymodbus 3.11.4, API historique.

Même automate que `../../server.py`, écrit avec l'ancienne API pymodbus, celle
que l'on trouve encore dans la plupart des exemples et de beaucoup de projets
industriels. Le but est de voir les deux écritures côte à côte, et de comprendre
pourquoi on ne peut pas les mélanger.

Ce fichier ne fonctionne PAS avec pymodbus 3.15 : il lui faut 3.11.x, dans un
environnement dédié, les deux versions de la bibliothèque ne pouvant pas
cohabiter.

Installation puis lancement, deux terminaux :

    uv venv .venv
    uv pip install --python .venv/Scripts/python.exe -r requirements.txt
    .venv/Scripts/python.exe server.py
    .venv/Scripts/python.exe client.py

Sous Linux/macOS, remplacer le chemin par .venv/bin/python.
"""

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import StartTcpServer

# --- Mémoire de l'automate --------------------------------------------------
#
# 3.11.4 ne connaît ni SimData ni SimDevice. La mémoire se décrit avec trois
# classes emboîtées, à lire dans l'ordre :
#
#   ModbusSequentialDataBlock : un bloc de valeurs contiguës (la mémoire)
#   ModbusDeviceContext       : les 4 blocs d'UN esclave
#   ModbusServerContext       : le ou les esclaves du serveur
#
# Le point qui surprend le plus : ModbusSequentialDataBlock(0, [...]) reçoit
# l'adresse 0, mais pymodbus indexe la liste à partir de 1, donc l'adresse N
# renvoie la valeur de la case N+1 :
#
#   liste     :  [0]  [1]  [2]  [3]  ...
#                 |    |    |    |
#   adresse   :   --   0    1    2  ...
#
# Le premier élément est une place réservée, jamais adressée : d'où le [0] + en
# tête de chaque bloc. Sans lui, l'adresse Modbus 0 renverrait la valeur 2 et
# tout le reste serait décalé d'une unité — une erreur d'adressage silencieuse :
# le client reçoit bien une réponse, mais la mauvaise valeur.
#
# Ce piège n'existe plus depuis pymodbus 3.15 : voir ../../server.py.
store = ModbusDeviceContext(
    # Tables 1 et 2 : 1 bit par valeur, donc seulement 0 ou 1. On alterne
    # 0/1/0/1... pour que chaque position reste identifiable à la lecture.
    di=ModbusSequentialDataBlock(0, [0] + [i % 2 for i in range(100)]),  # Entrées discrètes
    co=ModbusSequentialDataBlock(0, [0] + [i % 2 for i in range(100)]),  # Coils
    # Table 3 : la mémoire de travail, en lecture et en écriture. Entier 16 bits
    # non signé (0 à 65535), valeur = adresse + 1.
    hr=ModbusSequentialDataBlock(0, [0] + [i + 1 for i in range(100)]),  # Registres de maintien
    # Table 4 : valeurs mesurées, en lecture seule. Valeurs 1000..1099.
    ir=ModbusSequentialDataBlock(0, [0] + [1000 + i for i in range(100)]),  # Registres d'entrée
)

# --- Contexte du serveur ----------------------------------------------------
#
# ModbusServerContext regroupe les esclaves du serveur. Avec single=True,
# l'unique contexte sert à toutes les requêtes, quel que soit le device_id.
#
# Attention, comportement vérifié sur cette version : device_id=1 répond, mais
# device_id=0, 2, 7 et 247 répondent aussi. Cette écriture masque donc les
# erreurs d'adressage d'esclave.
#
# En 3.15, single= est déprécié (l'argument est accepté mais ignoré) et le
# contexte se construit avec SimDevice. Dans cette version, seul l'esclave
# déclaré répond : interroger device_id=2 renvoie une erreur.
context = ModbusServerContext(devices=store, single=True)

# --- Démarrage du serveur ---------------------------------------------------
#
# On écoute sur le port 5020 pour éviter le port 502 (privilèges admin).
# 0.0.0.0 expose le port à toutes les interfaces réseau de la machine : pour un
# usage strictement local, préférer "127.0.0.1".
StartTcpServer(context=context, address=("0.0.0.0", 5020))