# HL INTech de la CDR 2024

ca bouge ????

## Que font les scripts ?

- `main.py` Script principale qui fait tout fonctionner ensemble
- `graph.py <ip>` Script pour avoir les graph des pids
- `ps4.py [p]` Script pour controller le robot avec une manette (avec p pour le pami)
- `commander.py [a]` Script pour debug en cmd (avec a pour les actionneurs) 

## Setup Raspi

- Activer l'I2C à travers `raspi-config`
	```bash
	sudo raspi-config
	```

- Installer OpenOCD & GDB
	```bash
	sudo apt install openocd gdb-multiarch
	```

- Installer smbus2 en global
	```bash
	python -m pip install smbus2
	```

- Script pour flash les picos
	```bash
	#!/bin/bash
	# Utilisation : ./flash pami.elf
	openocd -f /usr/share/openocd/scripts/interface/raspberrypi2-native.cfg -c "bcm2835gpio swd_nums 26 19; adapter_khz 1000" -f /usr/share/openocd/scripts/target/rp2040.cfg -c "program $1 verify ; init ; reset halt ; rp2040.core1 arp_reset assert 0 ; rp2040.core0 arp_reset assert 0; exit"
	```