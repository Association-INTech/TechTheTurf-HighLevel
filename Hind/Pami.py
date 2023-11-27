import cmd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import  smbus2 as s
import struct

class Pami(cmd.Cmd):

#Initialisation des variables#
    def __init__(self):
        rot_teta = 0
        rot_rho = 0
        kp_tete = 0
        ki_teta = 0
        kd_teta = 0
        kp_rho = 0
        ki_rho = 0
        kd_rho = 0
        pid = {'teta' : 0, 'rho' : 1, ' vitesse_roue_gauche' : 2, 'vitesse_roue_droite' : 3}

    bus = s.SMBus(1)
    i2c_adresse = 0x69 #adresse i2c du rasberry

### ECRITURE ###

    def do_allumer(self, ligne):
        bus.write_i2c_block_data(i2c_adresse, 0 << 4,struct.pack('i',1)) # vérifier avec pablo car renvoit 4 octet or i s'attend à ce que je le lise sur 1 octet
        print("Le pami s'allume", line)

    def do_eteindre(self, line):
        bus.write_i2c_block_data(i2c_adresse, 0 << 4,struct.pack('i',0))
        print("Le pami s'éteind", line)

    def do_avancer(self, distance):
        distance_float = float(distance)
        bus.write_i2c_block_data(i2c_adresse, 1 << 4,struct.pack(distance_float))
        print("le pami avance de "+distance)

    def do_rotation(self, angle):
        angle_float = float(angle)
        bus.write_i2c_block_data(i2c_adresse, 1 << 4,struct.pack(angle_float))
        print("le parmi tourne de "+angle)

    def do_changer(self, ligne_commande):
        pid, kp, ki, kd = ligne_commande.split()
        kp_float = float(kp)
        ki_float = float(ki)
        kd_float = float(kd)
        bus.write_i2c_block_data(i2c_adresse, 5 << 4 | self.pid[pid], struct.pack('f',kp_float) + struct.pack('f',ki_float) + struct.pack('f',kd_float))

## LECTURE ###

    def do_demande_asservissement(self,line):
        k_teta = bus.read_i2c_block_data(i2c_adresse,2 << 4  | 0,12)#avec la | : choix du PID et [0] car on veut que la première partie et pas la valeur approximé
        k_rho = bus.read_i2c_block_data(i2c_adresse,2 << 4 | 1,12)

        kp_teta = struct.unpack('f',k_teta[0:4])[0]
        ki_teta = struct.unpack('f',k_teta[4:8])[0]
        kd_teta = struct.unpack('f',k_teta[8:12])[0]
        kp_rho = struct.unpack('f',k_rho[0:4])[0]
        ki_rho = struct.unpack('f',k_rho[4:8])[0]
        kd_rho = struct.unpack('f',k_rho[8:12])[0]
        print("Demande d'asservissement au BL")

    def do_teta_rho(self, line):
        position = bus.read_i2c_block_data(i2c_adresse, 3 << 4, 12)
        teta = struct.unpack('f', position[0:4])[0]
        rho = struct.unpack('f', position[4:8])[0]

    def do_erreur(self,line):
        erreur_position = bus.read_i2c_block_data(i2c_adresse, 4 << 4, 12)
        erreur_teta = struct.unpack('f',erreur_position[0:4])[0]
        erreur_rho = struct.unpack('f', erreur_position[4:8])[0]

    def do_objet(self,line):
        detect=0
        if detect :
            self.do_eteindre(line)
            print("Le pami à touché une fleur")

    def do_graph(self,i=0):
        fig = plt.figure()
        axis = plt.axes(xlim =(0, 4),
                        ylim =(-2, 2))
        # initializing a line variable
        line, = axis.plot([], [], lw = 3)

        def init():
            line.set_data([], [])
            return line,

        def animate(i):
            x = np.linspace(0, 4, 1000)
            y = np.sin(2 * np.pi * (x - 0.01 * i))
            line.set_data(x, y)
            return line,

        anim = FuncAnimation(fig, animate,
                             init_func = init,
                             frames = 200,
                             interval = 20,
                             blit = True)
        plt.show()

Pami().cmdloop()
