# HL INTech de la CDR 2024

Ca a bougé, on a finis 9ème. 

## Que font les scripts ?

- `graph.py <ip>` Script pour avoir les graph des pids
- `ps4.py [p/na]` Script pour controller le robot avec une manette (avec p pour le pami et na pour le gros sans les actionneurs)
- `commander.py [-a] [-d]` Script pour debug en cmd (avec a pour les actionneurs et d pour le debug sur l'écran)
- `tablevis.py` Visualiseur de la table qui n'a jamais été finit

## Ou sont les scénarios ?

- `main.py (b/y)` Le scénario originel qui sert d'exemple pour les autres.
- `main3.py` Variation plus aggressive, diagonale vers zone adverse.
- `arig_depart_panneaux.py (b/y)` Attente au début puis repasse sur les panneau du milieu.
- `main_tbu_edit.py (b/y)` Le scénario finale à 87 points (88 si bonne estimation de plante).

## Setup Raspi

```bash
# Turn on I2C
sudo raspi-config nonint do_i2c 0
# Install OpenOCD & GDB
sudo apt install -y openocd gdb-multiarch
# Install smbus2 globally
python -m pip install smbus2

# Create venv
python -m venv venv
# Load into the venv
source venv/bin/activate
# Install other requirements
python -m pip install -r requirements.txt
```

## Flasher les picos

Le script `tools/flash.sh` permet de flasher les différents picos.

Par exemple pour flasher `paminable.elf` sur une pico d'un pami: `./tools/flash.sh paminable.elf pami`