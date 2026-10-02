"""Client Modbus TCP minimal (maître) - pymodbus 3.11.4, API historique.

Même code que `../../client.py`, exécuté avec pymodbus 3.11.4.

Bonne nouvelle pour la comparaison : l'API client n'a pas changé entre 3.11.4 et
3.15 — c'est donc du côté du serveur que tout a changé. Installation et
lancement sont décrits en tête du server.py de ce dossier.
"""

from pymodbus.client import ModbusTcpClient

# --- 1. Connexion -----------------------------------------------------------
#
# connect() renvoie True ou False : sans test, le script planterait plus loin sur
# une erreur de socket peu lisible.
client = ModbusTcpClient("127.0.0.1", port=5020)

if not client.connect():
    raise SystemExit("Connexion impossible a 127.0.0.1:5020, le serveur est-il lance ?")

# --- 2. Lecture -------------------------------------------------------------
#
# « Donne-moi 1 registre de maintien à l'adresse 0 ». La réponse est un objet
# dont le champ .registers contient la liste des valeurs lues ; en cas d'erreur
# c'est une ExceptionResponse, qui n'a pas ce champ.
resultat = client.read_holding_registers(address=0, count=1)

if resultat.isError():
    print(f"Erreur de lecture : {resultat}")
else:
    print(f"Holding register 0 = {resultat.registers[0]}")

# --- 3. Ecritures -----------------------------------------------------------
#
# Registre 0 = 17 (par exemple 17.0 °C), puis coil 0 allumée (par exemple un
# chauffage). Ce sont les deux seules tables modifiables.
resultat = client.write_register(address=0, value=17)
if resultat.isError():
    print(f"Erreur d'ecriture du registre : {resultat}")

resultat = client.write_coil(address=0, value=True)
if resultat.isError():
    print(f"Erreur d'ecriture de la coil : {resultat}")

# --- 4. Relecture de controle -----------------------------------------------
#
# La seule preuve qu'une écriture a réussi est de relire la valeur.
resultat = client.read_holding_registers(address=0, count=1)
if not resultat.isError():
    print(f"Relu apres ecriture  : {resultat.registers[0]}")

# --- 5. Fermeture ----------------------------------------------------------
client.close()

# Note : pas d'accents dans les messages, pour ne pas dépendre de l'encodage de
# la console Windows. Voir la note de ../../client.py