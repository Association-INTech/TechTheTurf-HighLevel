# TODO

## Communication par l'I2C

### Configurer la RaspBerry pi:

 - Si la commande  `i2cdetect` existe, elle est sûrement déjà configuré
 - Activer I2C
```
sudo raspi-config
// Interface settings -> I2C -> Yes
```
 - outils i2c sytème/python
```
sudo apt-get install i2c_tools
sudo apt-get install python3-pip
python3 -m pip install smbus2
```

### i2c avec smbus et python
[documentation](https://pypi.org/project/smbus2/)

#### Objectifs
 - savoir communiquer avec des pico en esclave
 - interface python


## Descriptif des échanges de données
A déterminer

 - taille des trames: fixe, variable
 - contenu des trames
 - fonctionnalités principales:
   - ordonner une trajectoire
   - interruption/reprise de trajectoire
   - lire/écrire des variables
   - lire valeur de codeuses

##  Invite de commandes interactif avec cmd

Usage basique de cmd:

```py 
# nom de fichier example.py
import cmd

class Shell(cmd.Cmd): 
    def do_command(self, line):
        """nom générique "do_<nom de commande>" """
        print(f"You entered \"{line}\" as arguments")


Shell().cmdloop()
```
Dans un terminal en lançant `py example.py` (Windows) ou `python3 example.py` (Linux) on obtient :
```
(Cmd) > command
You enterded "" as arguments
(Cmd) > command Python > C
You enterded "Python > C" as arguments
```

 ### Objectifs

 - intégrer la communication avec la pico