"""Automate simplifié (esclave Modbus TCP) - pymodbus 3.15.

Ce serveur ne fait qu'une chose : servir une mémoire faite de 4 tables de
valeurs. Un vrai automate enchaînerait des entrées, un programme, puis des
sorties ; ici on ne garde que la partie mémoire, et toute la difficulté est
dans le dialogue réseau, l'adressage et les formats.

Deux rappels Modbus : le dialogue est question/réponse, sans envoi spontané de
données — c'est le client qui interroge l'esclave, c'est le polling ; et un
esclave n'expose exactement que 4 tables, qui constituent sa mémoire.

Lancement :  python server.py    (puis, dans un autre terminal, client.py)
"""

from pymodbus.server import StartTcpServer
from pymodbus.simulator import DataType, SimData, SimDevice

# --- Paramètres --------------------------------------------------------------
HOTE = "0.0.0.0"  # toutes les interfaces ; "127.0.0.1" pour un usage local
PORT = 5020  # le port Modbus officiel (502) est réservé : privilèges admin
NB_VALEURS = 100  # nombre de valeurs dans chaque table

# "0.0.0.0" rend le port 5020 accessible depuis le réseau local. Attention :
# Modbus ne prévoit ni authentification, ni chiffrement, ni contrôle d'accès.

# --- Mémoire de l'automate --------------------------------------------------
#
# Un seul esclave (device_id = 1) : l'identifiant est obligatoire dans Modbus,
# car plusieurs automates se partagent le câble et le client doit savoir à qui il
# parle. simdata est un tuple de 4 listes, toujours dans cet ordre : coils,
# entrées discrètes, registres de maintien, registres d'entrée.
device = SimDevice(
    id=1,
    simdata=(
        # 1. COILS (table 1) : sorties logiques, 1 bit, True/False. Un client
        # peut aussi les écrire directement (0x05). DataType.BITS est
        # obligatoire pour les 2 premières tables, sinon pymodbus lève une
        # TypeError.
        [SimData(0, values=[bool(i % 2) for i in range(NB_VALEURS)], datatype=DataType.BITS)],
        # 2. ENTRÉES DISCRÈTES (table 2) : états logiques en lecture seule
        # (capteurs, fins de course...), même type que les coils.
        [SimData(0, values=[bool(i % 2) for i in range(NB_VALEURS)], datatype=DataType.BITS)],
        # 3. REGISTRES DE MAINTIEN (table 3) : la mémoire de travail, en lecture
        # ET en écriture. Une valeur est un entier 16 bits non signé, de 0 à
        # 65535. On y met valeur = adresse + 1 : chaque registre contient ainsi
        # une valeur unique, ce qui vérifie d'un coup d'œil l'adressage du
        # client.
        [SimData(0, values=[i + 1 for i in range(NB_VALEURS)], datatype=DataType.REGISTERS)],
        # 4. REGISTRES D'ENTRÉE (table 4) : valeurs mesurées, en lecture seule.
        # Même format que la table 3, mais des valeurs 1000..1099 pour la
        # distinguer visuellement.
        [SimData(0, values=[1000 + i for i in range(NB_VALEURS)], datatype=DataType.REGISTERS)],
    ),
)

# L'adresse 0 de chaque SimData est l'adresse Modbus 0 : pas de registre
# décalé, pas de valeur réservée en tête de liste (l'ancienne API faisait
# autrement, voir ../../legacy/pymodbus-3.11.4/server.py). Les adresses valides
# vont de 0 à NB_VALEURS - 1 ; lire au-delà renvoie une réponse d'erreur
# (code 2, « adresse illégale ») et non une valeur.

# --- Démarrage ---------------------------------------------------------------
#
# StartTcpServer() ne rend pas la main : il boucle pour répondre aux clients
# jusqu'à l'arrêt du processus (Ctrl+C). C'est le comportement attendu ici.
StartTcpServer(context=[device], address=(HOTE, PORT))