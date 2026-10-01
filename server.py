from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusDeviceContext, ModbusServerContext

# Initialisation des données (coils, holding registers, etc.)
# Discrete Inputs et Coils sont des bits uniques : seules les valeurs 0 et 1
# sont possibles, on alterne donc pour que la position reste identifiable.
# Holding et Input Registers sont des 16 bits non signés (0-65535) : la valeur
# encode l'index du registre, ce qui rend chaque registre distinct et vérifiable.
#
# Le 0 en tête de chaque liste est réservé : pymodbus décale l'adresse de +1
# en interne, l'adresse Modbus 0 correspond donc au 2e élément de la liste.
# Sans ce préfixe, l'adresse 0 renverrait la valeur du registre suivant.
store = ModbusDeviceContext(
    di=ModbusSequentialDataBlock(0, [0] + [i % 2 for i in range(100)]),      # Discrete Inputs
    co=ModbusSequentialDataBlock(0, [0] + [i % 2 for i in range(100)]),      # Coils
    hr=ModbusSequentialDataBlock(0, [0] + [i + 1 for i in range(100)]),      # Holding Registers
    ir=ModbusSequentialDataBlock(0, [0] + [1000 + i for i in range(100)])    # Input Registers
)

# Contexte du serveur (1 slave par défaut, unit_id=1)
context = ModbusServerContext(devices = store, single=True)

# Démarrer le serveur sur le port 5020
StartTcpServer(context=context, address=("0.0.0.0", 5020))
