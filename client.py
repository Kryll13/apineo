"""Client Modbus TCP minimal (maître) - pymodbus 3.15.

Le client est le « maître » : c'est lui qui décide quand lire ou écrire. Même en
trois opérations, il contient les trois gestes de base d'un vrai client
industriel : vérifier la connexion, vérifier que la réponse n'est pas une erreur
Modbus (isError()), et fermer la connexion à la fin.

Lancement :  python client.py    (le serveur doit tourner dans l'autre terminal)
"""

from pymodbus.client import ModbusTcpClient

HOTE = "127.0.0.1"  # machine locale ; un vrai automate aurait son adresse IP
PORT = 5020  # doit correspondre au port du serveur

# --- 1. Connexion -----------------------------------------------------------
#
# Créer le client n'ouvre rien : c'est connect() qui ouvre la socket TCP.
# connect() renvoie True ou False sans lever d'exception si le serveur est
# absent : sans ce test, le script planterait plus loin sur une erreur de socket
# incompréhensible.
client = ModbusTcpClient(HOTE, port=PORT)

if not client.connect():
    raise SystemExit(f"Connexion impossible a {HOTE}:{PORT}, le serveur est-il lance ?")

# --- 2. Lecture -------------------------------------------------------------
#
# « Donne-moi count registres de maintien, à partir de l'adresse address ». La
# réponse est un objet ; le champ utile ici est .registers, une liste d'entiers
# (d'où les crochets autour du résultat).
resultat = client.read_holding_registers(address=0, count=1)

if resultat.isError():
    # En cas d'erreur, resultat n'est pas une ReadHoldingRegistersResponse mais
    # une ExceptionResponse : il ne contient pas .registers.
    print(f"Erreur de lecture : {resultat}")
else:
    print(f"Holding register 0 = {resultat.registers[0]}")
    print(f"Reponse complete   : {resultat}")

# --- 3. Ecritures -----------------------------------------------------------
#
# Registre de maintien : un entier 16 bits (0 à 65535), ici 17, qui pourrait
# représenter 17.0 °C. Coil : un seul bit, True ou False — ici on l'allume, ce
# qui dans un vrai automate pourrait commander un chauffage, un moteur, un
# voyant.
resultat = client.write_register(address=0, value=17)
if resultat.isError():
    print(f"Erreur d'ecriture du registre : {resultat}")

resultat = client.write_coil(address=0, value=True)
if resultat.isError():
    print(f"Erreur d'ecriture de la coil : {resultat}")

# La seule preuve qu'une écriture a réussi est de relire : c'est aussi ce que
# fait un vrai programme de supervision après chaque commande.
resultat = client.read_holding_registers(address=0, count=1)
if not resultat.isError():
    print(f"Relu apres ecriture  : {resultat.registers[0]}")

# --- 4. Fermeture ----------------------------------------------------------
client.close()

# Note : aucun accent dans les messages affichés, car la console Windows utilise
# souvent l'encodage cp1252. Pour les retrouver :  python -X utf8 client.py