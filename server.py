from pymodbus.server import StartTcpServer
from pymodbus.simulator import SimData, SimDevice, DataType

# Initialisation des données (coils, holding registers, etc.)
# Discrete Inputs et Coils sont des bits uniques : seules les valeurs 0 et 1
# sont possibles, on alterne donc pour que la position reste identifiable.
# Holding et Input Registers sont des 16 bits non signés (0-65535) : la valeur
# encode l'index du registre, ce qui rend chaque registre distinct et vérifiable.
#
# L'adresse du premier SimData correspond directement à l'adresse Modbus : pas
# de registre décalé ni de préfixe à réserver.
#
# Les 4 types de données sont déclarés comme un tuple dans l'ordre :
# (coils, discrete inputs, holding registers, input registers).
# Les deux premiers doivent être en DataType.BITS, et SimDevice les adresse
# alors par bit : la coil 0 est bien la coil 0.
device = SimDevice(
    id=1,
    simdata=(
        [SimData(0, values=[bool(i % 2) for i in range(100)], datatype=DataType.BITS)],      # Coils
        [SimData(0, values=[bool(i % 2) for i in range(100)], datatype=DataType.BITS)],      # Discrete Inputs
        [SimData(0, values=[i + 1 for i in range(100)], datatype=DataType.REGISTERS)],        # Holding Registers
        [SimData(0, values=[1000 + i for i in range(100)], datatype=DataType.REGISTERS)],     # Input Registers
    ),
)

# Démarrer le serveur sur le port 5020
StartTcpServer(context=[device], address=("0.0.0.0", 5020))
