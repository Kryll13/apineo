# Projet APINEO

## Description

Démonstration d'un serveur et d'un client Modbus TCP avec [pymodbus](https://pymodbus.readthedocs.io/).

Le serveur expose des coils, des discrete inputs, des holding registers et des input registers pré-remplis. Le client s'y connecte, lit un registre, puis écrit une valeur.

## Versions

| Composant | Version   |
| --------- | --------- |
| pymodbus  | 3.15.0    |
| Python    | 3.13.5    |

## Installation

```bash
uv sync
```

## Utilisation

Lancer le serveur dans un terminal, puis le client dans un autre :

```bash
uv run python server.py   # dans un terminal
uv run python client.py   # dans un autre terminal
```

Le serveur écoute sur le port 5020, le client s'y connecte sur `127.0.0.1`.

## Données exposées

Toutes les plages commencent à l'adresse Modbus 0, sans registre décalé.

| Type              | Plage   | Contenu                              |
| ----------------- | ------- | ------------------------------------ |
| Coils             | 0..99   | bits alternés 0/1                    |
| Discrete inputs   | 0..99   | bits alternés 0/1                    |
| Holding registers | 0..99   | valeur = index + 1, donc 1, 2, 3... |
| Input registers   | 0..99   | valeur = 1000 + index                |

Le contenu est voulu lisible: chaque registre porte une valeur distincte, ce qui permet de vérifier d'un coup d'œil que l'adressage est correct.

## Détail d'adressage des bits

Les coils et discrete inputs sont déclarés en `DataType.BITS`. Une lecture `read_coils(address=0, count=4)` renvoie alors 8 bits, le registre complet, et non 4. Pour un adressage au bit, `SimDevice` accepte `use_bit_addressing`.

## Exemple de pymodbus antérieur

Une copie de la version des scripts fonctionnant avec pymodbus 3.11.4 est conservée dans [`legacy/pymodbus-3.11.4/`](legacy/pymodbus-3.11.4/README.md). Ces fichiers ne tournent pas avec 3.15, le README du dossier détaille les incompatibilités.
