# HL INTech de la CDR 2024

ca bouge ????

## Que font les scripts ?

- `main.py` Script principale qui fait tout fonctionner ensemble
- `graph.py <ip>` Script pour avoir les graph des pids
- `ps4.py [p]` Script pour controller le robot avec une manette (avec p pour le pami)
- `commander.py [a]` Script pour debug en cmd (avec a pour les actionneurs) 

## Setup Raspi

```bash
# Turn on I2C
sudo raspi-config nonint do_i2c 0
# Install OpenOCD & GDB
sudo apt install -y openocd gdb-multiarch
# Install smbus2 globally
python -m pip install smbus2
```

## Flasher les picos

Le script `tools/flash.sh` permet de flasher les différents picos.

Par exemple pour flasher `paminable.elf` sur une pico d'un pami: `./tools/flash.sh paminable.elf pami`