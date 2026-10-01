# Exemplaire pymodbus 3.11.4

Copie à l'identique des scripts `client.py` et `server.py` de la racine du projet,
dans l'état où ils fonctionnent.

## Versions de référence

| Composant | Version   |
| --------- | --------- |
| pymodbus  | 3.11.4    |
| Python    | 3.13.5    |

Ces versions correspondaient à la contrainte `pymodbus>=3.11.2,<3.12` et
`requires-python = ">=3.13,<3.14"` du `pyproject.toml`. Le projet a depuis été
basculé sur pymodbus 3.15.0 (voir `../../server.py` pour la version courante).

Pour exécuter ces fichiers, il faut pymodbus 3.11.x : ils ne fonctionnent pas
avec 3.15, dont les breaking changes sont décrits ci-dessous.

## Utilisation

Depuis ce dossier, avec l'environnement virtuel du projet :

```bash
../.venv/bin/python server.py   # dans un terminal
../.venv/bin/python client.py   # dans un autre terminal
```

Le serveur écoute sur le port 5020, le client s'y connecte sur `127.0.0.1`.

## Vérification effectuée

Le couple a été testé dans cet état le 1er octobre 2026 : le client lit le
registre de maintien 0 et renvoie `Valeurs des registres: [1]`, puis écrit le
coil 0 sans erreur.

## Pourquoi ce code ne tourne pas avec pymodbus 3.15

Deux incompatibilités, rencontrées lors de la migration vers 3.15.0 :

- `ModbusSequentialDataBlock` construit désormais un `SimData(address - 1, ...)`,
  donc `ModbusSequentialDataBlock(0, ...)` lève
  `TypeError: 0 <= address < 65535`. Le préfixe `[0]` en tête de liste ne
  compense plus : il faudrait passer `address=1` et le retirer.
- `ModbusDeviceContext`, `ModbusSequentialDataBlock` et `ModbusServerContext`
  sont dépréciés et seront supprimés en v4. Le projet utilise maintenant
  `SimData`/`SimDevice`.

## Avertissement

`server.py` se lie à `0.0.0.0`, ce qui expose le port 5020 à toutes les
interfaces réseau de la machine pendant l'exécution. Pour un usage local
uniquement, préférer `127.0.0.1`.
