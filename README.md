# Projet APINEO — Modbus TCP avec pymodbus

Un **automate simplifié** et un **client Modbus TCP**, écrits en Python, pour
apprendre le protocole Modbus en manipulant du vrai code.

L'automate se limite au **strict stockage de valeurs dans ses registres** : il ne
fait ni acquisition, ni traitement, ni commande. Toute la difficulté est donc
dans le dialogue réseau, l'adressage et les formats.

> **Public visé** : étudiant débutant en Python, à l'aise avec la syntaxe de
> base (variables, fonctions, listes). Aucune expérience en automatique n'est
> nécessaire : toutes les notions Modbus utilisées ici sont expliquées.

## Sommaire

1. [Ce que fait le projet](#1-ce-que-fait-le-projet)
2. [Installation](#2-installation)
3. [Lancer la démonstration](#3-lancer-la-démonstration)
4. [Comprendre Modbus](#4-comprendre-modbus)
5. [Les données de notre automate](#5-les-données-de-notre-automate)
6. [Lecture de `server.py`](#6-lecture-de-serverpy)
7. [Lecture de `client.py`](#7-lecture-de-clientpy)
8. [Les pièges à connaître](#8-les-pièges-à-connaître)
9. [À vous de jouer](#9-à-vous-de-jouer)
10. [Limites et pistes](#10-limites-et-pistes)
11. [La version pymodbus 3.11.4](#11-la-version-pymodbus-3114)
12. [Documentation](#12-documentation)

## 1. Ce que fait le projet

Deux programmes, à lancer dans deux terminaux :

| Programme  | Rôle Modbus                | Ce qu'il fait                                   |
| ---------- | -------------------------- | ----------------------------------------------- |
| `server.py` | l'**esclave** (l'automate) | mémoire de 4 tables de 100 valeurs, servie sur le réseau |
| `client.py` | le **maître**               | lit une valeur, en écrit deux, relit pour vérifier |

```
   client.py  ──── requêtes Modbus TCP ────▶  server.py
   (maître)        "lis le registre 0"          (esclave / automate)
               ◀─── réponse "1" ────────────────
               ──── "écris 17 dans le registre 0" ───▶
               ──── "mets la coil 0 à True"     ───▶
```

Un vrai automate répète en boucle *acquisition des entrées → exécution du
programme → écriture des sorties*. Ici on ne garde que la partie **mémoire**,
parce que c'est elle qui se manipule en Python, avec des entiers et des
booléens.

## 2. Installation

Python 3.13.x et pymodbus 3.15.x, épinglés dans `pyproject.toml`. La précision
n'est pas décorative : pymodbus change d'API entre les versions majeures, et ce
code ne fonctionne **que** avec la série 3.15.

```bash
uv sync                                              # avec uv
python -m venv .venv && .venv/Scripts/python.exe -m pip install -e .   # sinon (Windows)
```

## 3. Lancer la démonstration

Terminal 1 : `uv run python server.py` — terminal 2 : `uv run python client.py`

```text
Holding register 0 = 1
Reponse complete   : ReadHoldingRegistersResponse(dev_id=1, transaction_id=1, address=0, count=0, bits=[], registers=[1], status=1, retries=0)
Relu apres ecriture  : 17
```

- `1` : le registre 0 contient `adresse + 1`, donc 1. La mémoire est intacte et
  le client lit la bonne adresse.
- la réponse complète montre le `device_id=1` qui a répondu et le
  `transaction_id=1`, numéro de séquence qui permet d'apparier requêtes et
  réponses quand plusieurs clients parlent en même temps.
- `17` : la valeur écrite un peu plus tôt est bien relue. **Une écriture Modbus
  n'a pas d'autre preuve de succès que sa relecture.**

Pendant ce temps le terminal 1 reste muet : un serveur ne parle que lorsqu'on
l'interroge. Trois points à savoir :

- **Un seul serveur à la fois.** Celui de `legacy/pymodbus-3.11.4/` écoute sur le
  même port 5020 ; s'il tourne déjà, le second démarre **sans message d'erreur**
  et c'est le premier qui continue de répondre.
- **Le port 5020 et non 502** : 502 est le port Modbus officiel, mais réservé
  (privilèges administrateur).
- **Si ça ne va pas** — `Connexion impossible a 127.0.0.1:5020, le serveur
  est-il lance ?` signifie que le client n'a rien trouvé, dans 95 % des cas
  parce que le serveur n'est pas démarré ou pas dans le bon terminal. La ligne
  en anglais que pymodbus écrit aussi est son journal, pas une seconde erreur.

## 4. Comprendre Modbus

Modbus est un protocole né en 1979 pour les automates industriels. Resté
volontairement simple, il est immense répandu : automates, variateurs, capteurs,
compteurs d'énergie et systèmes SCADA le parlent tous.

**Deux rôles.** Le **maître** (`client.py`, l'opérateur) **initie toujours**
l'échange ; l'**esclave** (`server.py`, la machine) ne parle jamais de lui-même.
Connaître une valeur suppose donc de savoir la demander, en boucle : c'est le
*polling*, et c'est pourquoi le temps de cycle d'une acquisition Modbus est un
point critique en industrie.

**Une trame** contient l'**identifiant de l'esclave** (`device_id`, 1..247 : à qui
je parle), le **code de fonction** (ce que je veux faire) et l'**adresse de
départ** plus le **nombre d'éléments**. L'esclave répond avec la même structure.

**Les 4 tables, et seulement 4.** Un esclave Modbus n'a pas « des variables » :
toute la conception d'un automate consiste à décider ce qu'on met dans chaque
table, et à le documenter. Une « coil » et une « entrée discrète » sont toutes
deux des booléens, mais une sortie se commande et une entrée se constate : c'est
toute la différence.

| Table                | Type    | Écriture            | Codes      |
| -------------------- | ------- | ------------------- | ---------- |
| Coils                | 1 bit   | client et programme | 0x01, 0x05 |
| Entrées discrètes    | 1 bit   | programme seul      | 0x02       |
| Registres de maintien | 16 bits | client et programme | 0x03, 0x06 |
| Registres d'entrée    | 16 bits | programme seul      | 0x04       |

Les tables 2 et 4 n'ont **aucun code d'écriture** : elles sont en lecture seule
par construction du protocole.

**Deux formats.** 1 bit (`True` / `False`) et 16 bits non signé (0 à 65535). Les
« 32 bits » et les « flottants » sont des conventions de l'industrie, pas du
protocole : pymodbus les manipule (`DataType.INT32`, `DataType.FLOAT32`…) mais
ils occupent alors 2 ou 4 registres.

**Le piège des adresses.** Elles commencent à **0**, alors que la plupart des
manuels numérotent leurs registres à partir de 1 : un registre annoncé « 40001 »
correspond à l'adresse Modbus **0**. C'est la première cause d'erreur sur un
projet réel. Notre automate a été écrit sans ce décalage, pour que la
démonstration soit vérifiable à l'œil.

## 5. Les données de notre automate

Chaque table contient 100 valeurs, adressées de 0 à 99. Le contenu a été choisi
pour être **vérifiable d'un coup d'œil** : chaque valeur encode son adresse.

| Table                | Adresses | Contenu                        | Lecture | Écriture |
| -------------------- | -------- | ------------------------------ | :-----: | :------: |
| Coils                | 0..99    | `False, True, False, True...` |  oui    |   oui    |
| Entrées discrètes    | 0..99    | `False, True, False, True...` |  oui    |   non    |
| Registres de maintien | 0..99    | `adresse + 1`, soit 1..100     |  oui    |   oui    |
| Registres d'entrée   | 0..99    | `1000 + adresse`, soit 1000..1099 |  oui    |   non   |

Conséquence : si une lecture du registre 5 renvoie autre chose que 6, le
problème est dans l'adressage ou le décodage, jamais dans la donnée.

## 6. Lecture de `server.py`

Le fichier tient en deux idées : `SimDevice` décrit un esclave et ses 4 blocs de
valeurs, `StartTcpServer` ouvre le port et boucle jusqu'à l'arrêt du processus.

```python
device = SimDevice(id=1, simdata=(
    [SimData(0, values=[...], datatype=DataType.BITS)],       # coils
    [SimData(0, values=[...], datatype=DataType.BITS)],       # entrées discrètes
    [SimData(0, values=[...], datatype=DataType.REGISTERS)],  # registres de maintien
    [SimData(0, values=[...], datatype=DataType.REGISTERS)],  # registres d'entrée
))

StartTcpServer(context=[device], address=("0.0.0.0", 5020))
```

Trois détails à comprendre :

1. **L'ordre des 4 listes est imposé** (coils, entrées discrètes, registres de
   maintien, registres d'entrée). Inverser deux listes ne provoque pas d'erreur
   visible mais fait lire les mauvaises données — le bug d'adressage le plus
   discret qui soit.
2. **Les deux premières listes doivent être en `DataType.BITS`**, sinon pymodbus
   lève un `TypeError` : les tables 1 et 2 ne contiennent que des booléens.
3. **L'adresse 0 du `SimData` est l'adresse Modbus 0**, sans registre décalé ni
   valeur réservée en tête de liste. (L'ancienne API faisait autrement, voir
   [section 11](#11-la-version-pymodbus-3114).)

Pour écrire des données lisibles, on utilise une compréhension de liste, ici
`values=[i + 1 for i in range(NB_VALEURS)]` — pour chaque adresse `i`, la valeur
`i + 1`.

> **Sécurité réseau** — `"0.0.0.0"` rend le port 5020 joignable depuis le réseau
> local ; pour un usage strictement local, mettez `"127.0.0.1"`. Modbus ne
> prévoit **ni authentification, ni chiffrement, ni contrôle d'accès** : c'est un
> protocole pour un réseau d'atelier isolé, jamais pour Internet.

## 7. Lecture de `client.py`

Le client suit trois temps : **connecter, vérifier, agir**.

```python
client = ModbusTcpClient(HOTE, port=PORT)
if not client.connect():
    raise SystemExit("Connexion impossible ...")

resultat = client.read_holding_registers(address=0, count=1)
if resultat.isError():
    print(f"Erreur de lecture : {resultat}")

resultat = client.write_register(address=0, value=17)
resultat = client.write_coil(address=0, value=True)
client.close()
```

Quatre points :

- **Créer l'objet n'ouvre rien** : c'est `connect()` qui ouvre la socket, et elle
  renvoie `True` ou `False`. Si le serveur n'est pas démarré elle renvoie
  `False` **sans lever d'exception** ; sans ce test, le script planterait plus
  loin sur une erreur de socket difficile à rattacher à sa vraie cause.
- **`address` est le premier registre demandé, `count` le nombre** : une lecture
  est toujours un bloc contigu.
- **`isError()` est indispensable** : en cas d'erreur l'objet n'est pas une
  réponse de lecture mais une `ExceptionResponse`, sans attribut `.registers`.
  Y accéder lèverait une `AttributeError` qui masquerait la vraie cause.
- **`.registers` est une liste**, même pour `count=1` : d'où les crochets autour
  de la valeur dans les sorties du terminal, et le `[0]` qui en extrait le
  contenu.

Écrire un registre de maintien (0x06) et une coil (0x05) : ce sont les deux
seules écritures possibles depuis un client. Avec `SimData(..., readonly=True)`,
pymodbus répond par une erreur d'adresse illégale.

## 8. Les pièges à connaître

Des faits vérifiés sur ce projet, pas des généralités.

### 8.1 Une lecture de coils renvoie plus de bits que demandé

```python
client.read_coils(0, count=4).bits
# [False, True, False, True, False, False, False, False]  → 8 bits, pas 4
```

Modbus transporte les bits **groupés par octets** : demander 4 coils produit 1
octet, que la bibliothèque décode en 8 bits. Les 4 derniers ne sont pas lus dans
la mémoire de l'automate, ils sont mis à zéro — dans notre serveur la coil 5
vaut bien `True`, et pourtant le 6e bit renvoyé est `False`. Seuls les `count`
**premiers** bits sont donc significatifs ; le comportement vient du protocole,
pas de pymodbus.

```text
count demandé   1..8  9..16  17..24
bits renvoyés     8     16     24
```

### 8.2 Lire hors des adresses déclarées ne renvoie pas 0

```python
client.read_holding_registers(100, count=1)
# ExceptionResponse(function_code=131, exception_code=2)
```

Le code 2 est « adresse illégale ». C'est un bon réflexe de l'automate : il
refuse une adresse non déclarée plutôt que de renvoyer une valeur inventée. D'où
l'obligation de toujours tester `isError()`.

### 8.3 Les écritures ne se voient pas toutes dans `.registers`

La réponse à `write_register(0, 17)` contient bien `registers=[17]`, mais celle
à `write_registers(0, [7, 8, 9])` a un champ `registers` **vide** : pymodbus y
mettrait les valeurs écrites, pas celles de l'esclave.

### 8.4 La console Windows et les accents

La source est en UTF-8, mais la console Windows utilise souvent `cp1252`, d'où
les accents affichés derrière un caractère bizarre. Les messages de ce projet sont
volontairement sans accent ; pour les retrouver : `python -X utf8 client.py`.

## 9. À vous de jouer

Toutes ces vérifications se font dans `client.py`, sans toucher au serveur. Par
ordre de difficulté :

1. **Lire plusieurs registres** — `read_holding_registers(address=0, count=5)`
   doit renvoyer `[1, 2, 3, 4, 5]`. Si vous obtenez `[2, 3, 4, 5, 6]`, vous avez
   appliqué le décalage décrit en [section 4](#4-comprendre-modbus).
2. **Lire les registres d'entrée** — `read_input_registers(address=0, count=3)`
   doit renvoyer `[1000, 1001, 1002]`.
3. **Lire les entrées discrètes** — `read_discrete_inputs(address=0, count=8)`,
   et observer les bits de remplissage.
4. **Écrire plusieurs registres d'un coup** — `write_registers(0, [7, 8, 9])`,
   puis relire et vérifier `[7, 8, 9]`.
5. **Écrire plusieurs coils** — `write_coils(0, [True, False, True])`.
6. **Provoquer une erreur** — `read_holding_registers(200, count=1)` doit
   renvoyer une exception de code 2, jamais une valeur.
7. **Parler au mauvais esclave** — `read_holding_registers(0, count=1,
   device_id=2)` doit renvoyer une erreur : sur le bus, l'esclave 2 n'existe
   pas. Seul `device_id=1` répond, le `id=1` déclaré dans `server.py`.
8. **Changer l'adresse d'écoute** — se connecter depuis une autre machine du
   réseau avec `HOTE = "0.0.0.0"` côté serveur (c'est déjà le cas), puis remettre
   `"127.0.0.1"` et constater que la connexion distante échoue.

## 10. Limites et pistes

Savoir ce qu'un programme **ne fait pas** fait partie de l'apprentissage. Cet
automate n'a pas de cycle — la mémoire ne change que lorsqu'un client écrit ; pas
de persistance — tout est perdu à l'arrêt ; pas d'entrées/sorties réelles ; pas
de temps réel ni de sécurité ; et un seul esclave (`device_id=1`).

La bibliothèque permet d'aller plus loin sans changer d'architecture :

| Sujet | Comment |
| ----- | ------- |
| Registres en lecture seule | `SimData(..., readonly=True)` |
| Types 32/64 bits, flottants, textes | `datatype=DataType.FLOAT32`, `INT32`, `STRING` |
| Logique de programme | le paramètre `action=` de `SimDevice` |
| Plusieurs automates | une liste de `SimDevice`, avec des `id` différents |
| Adressage au bit | `use_bit_addressing` : avec nos 4 blocs séparés l'adresse désigne déjà le bit ; avec un bloc unique partagé, l'adresse effective du bit vaut `registre * 16 + position` |
| Diagnostic | `trace_packet=` / `trace_pdu=` pour voir les trames |
| Modbus série / UDP | `StartSerialServer` (RS-485, le plus courant en usine) |

## 11. La version pymodbus 3.11.4

Le dossier [`legacy/pymodbus-3.11.4/`](legacy/pymodbus-3.11.4/) contient la même
démonstration écrite pour **pymodbus 3.11.4**, avec l'ancienne API
`ModbusSequentialDataBlock` / `ModbusDeviceContext` / `ModbusServerContext`. Ce
dossier est important pour deux raisons : c'est l'API que vous rencontrerez dans
la plupart des projets industriels existants et sur Internet ; et elle est
**incompatible** avec la 3.15 actuelle.

**Installation — environnement dédié obligatoire**, les deux versions de la
bibliothèque ne pouvant pas cohabiter. Les commandes complètes (`uv venv`, puis
`uv pip install -r requirements.txt`) sont en tête du `server.py` de ce dossier,
avec les chemins pour Linux/macOS et la commande de lancement.

**Le `0` en tête des listes**, point le plus important de cette version :
`ModbusSequentialDataBlock(0, [...])` reçoit l'adresse **0**, mais pymodbus indexe
la liste à partir de 1, donc l'adresse N renvoie la valeur de la case N+1.

```text
liste     :  [0]  [1]  [2]  [3]  ...
              |    |    |    |
adresse   :   --   0    1    2  ...
```

Le premier élément est une place **réservée**, jamais adressée — d'où le `[0] +`
en tête de chaque bloc de ce dossier. Sans lui, l'adresse 0 renverrait 2, puis
3, puis 4…, et le client ne signalerait **aucune erreur**. Ce piège n'existe plus
en 3.15, où `SimData(0, ...)` adresse directement la bonne case.

Lancé avec la 3.15, ce `server.py` s'arrête sur une `TypeError`, car
`ModbusSequentialDataBlock` n'est plus qu'un mince habillage autour de `SimData`
et calcule l'adresse interne `address - 1`, soit `-1` :

```text
ModbusSequentialDataBlock(0, [0] + ...)
  -> SimData(address - 1, values=values, datatype=DataType.REGISTERS)
  -> TypeError: 0 <= address < 65535
```

Le dépannage consiste à passer `address=1` et à retirer le `[0]` réservé : on
retrouve les mêmes valeurs, mais la 3.15 écrit alors des avertissements de
dépréciation (`ModbusSequentialDataBlock ... are deprecated and will be removed
in v4`). La seule écriture durable reste le serveur en `SimData` / `SimDevice`.

### Résumé des différences entre les deux versions

| Sujet                          | pymodbus 3.11.4                  | pymodbus 3.15                    |
| ------------------------------ | -------------------------------- | -------------------------------- |
| Mémoire du serveur             | `ModbusSequentialDataBlock`      | `SimData`                        |
| Esclave                        | `ModbusDeviceContext`            | `SimDevice`                      |
| Contexte du serveur            | `ModbusServerContext`            | `SimDevice`, passé à `context=`  |
| Adresse du premier bloc        | `[0] + valeurs` (0 réservé)      | `SimData(0, ...)` sans décalage  |
| Type de données                | implicite                        | `datatype=DataType.BITS/REGISTERS` |
| `StartTcpServer(context=...)`  | `ModbusServerContext`            | `list[SimDevice]`                |
| `device_id=2` (esclave absente) | **répond quand même** (`single=True`) | **renvoie une erreur** |

Côté client, rien n'a changé : `write_register(...)` et `isError()` sont
identiques, et le paramètre qui identifie l'esclave s'appelle `device_id` dans
les deux versions (il s'appelait `slave` avant 3.10). Seul `single=True` n'existe
plus en tant que tel : l'argument est accepté mais ignoré en 3.15. Avec lui, les
erreurs d'adressage d'esclave étaient invisibles — `device_id` 0, 2, 7 et 247
obtenaient tous une réponse, alors qu'un vrai automate n'accepterait que les
adresses déclarées sur le bus.

## 12. Documentation

- [Documentation pymodbus](https://pymodbus.readthedocs.io/) — API de référence
- [Simulator de pymodbus](https://pymodbus.readthedocs.io/en/dev/source/simulator.html) — les `SimData` et `SimDevice`
- [Guide de migration vers la 4.0](https://pymodbus.readthedocs.io/en/dev/source/upgrade_40.html#convert-to-simdata-simdevice) — ce que pymodbus prépare
- [Spécifications Modbus](https://www.modbus.org/specifications) — la page officielle, puis [la spécification du protocole (PDF)](https://www.modbus.org/file/secure/modbusprotocolspecification.pdf), à lire au moins une fois