import cmd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import smbus2
import struct

bus=smbus2.SMBus(1)
i2c_addresse=0 #normalement 0x69
class Pami(cmd.Cmd):
    def __init__(self):
        self.allume = 1 # Pami inactif
        self.obstacle = 0
        super(Pami, self).__init__()
        self.pos_x= 0.
        self.pos_y=0.
        self.orientation = 0
        self.kp_teta=0.
        self.ki_teta=0.
        self.kd_teta=0.
        self.kp_rho=0.
        self.ki_rho=0.
        self.kd_rho=0.

    def do_reveil(self,i=0):
        self.allume = 1 #Pami allumé
        print("le pami est en marche")
        bus.write_i2c_block_data(i2c_addresse,0,struct.pack('i', 1))#vérifier qu'on reçoit bien les ytes dans le bon ordre

    def do_eteint(self,h=0):
        """éteint le pami, le stoppe et remet ses roues droites"""
        self.allume = 0
        self.orientation = 0
        bus.write_i2c_block_data(i2c_addresse,0,struct.pack('i', 0))
        print("pami eteint")

    def do_detecte(self,h=0):
        """rencontre un obstacle (plante?) et éteint le pami"""
        print("le pami est devant la plante")
        self.obstacle = 1
        self.do_eteint()

    def do_deplace(self,distance:float,angle:float):
        """fait avancer le pami"""
        if self.allume == 1:
            bus.write_i2c_block_data(i2c_addresse,1,struct.pack('!f',distance)+struct.pack('!f',angle))
            self.orientation += angle
            print("le Pami tourne de "+str(angle) +"degrés/angle et avance de"+ str(distance))
        else:
            print("ne peut pas avancer/tourner, pami est éteint")

    def do_exit(self,i=0):
        """stoppe le moteur, eteint le pami et ferme le terminal"""
        print("Ciao")
        self.do_eteint()
        bus.write_i2c_block_data(i2c_addresse,0,list(struct.pack('i', 0.0)))
        return True

    def do_demande_position(self,i=0):
        """demande la position et l'angle teta d'orientation du robot"""
        bus.write_i2c_block_data(i2c_addresse,3,struct.pack('i',0))
        res=bus.read_i2c_block_data(i2c_addresse,3,8)
        x=struct.unpack('!f',res[4:])
        y=struct.unpack('!f',res[:4])
        return (x,y)


    def do_demande_erreur(self,i=0):
        """demande l'erreur suite à un mouvement"""
        bus.write_i2c_block_data(i2c_addresse,4,struct.pack('i',0))
        res = bus.read_i2c_block_data(i2c_addresse,1,8)
        erreur_teta = struct.unpack('!f',res[0:4])
        print("erreur sur teta : " + str(erreur_teta))
        erreur_r = struct.unpack('!f',res[4:])
        print("erreur sur r : " + str(erreur_r))




    def do_info(self, func):
        """pour l'instant c'était juste un test pour utiliser FuncAnimation"""
        fig, ax = plt.figure(),plt.axes(xlim=[0. , 5*np.pi ],ylim=[ 0. , 100.])
        (line,) = ax.plot([],[])


        def animate(i):
            x = np.linspace(0, 5 * np.pi, 1000)
            y = np.sin(2 * (x - 0.1 * i ))
            line.set_data(x,y)
            return (line,)

        ani=FuncAnimation(fig, animate, frames=50 , interval=500,blit=True)

        plt.show()
    def demande_k(self, h=0):
        """envoie une demande et s'attend à recevoir les 3 valeurs: kp,ki et kd"""
        res=bus.read_i2c_block_data(i2c_addresse,2, 24)#attention les octets sont dans le mauvais ordre, il faut faire '!f' et pas 'f'

        kteta_p= struct.unpack('!f',res[:4])#4 premiers octets
        print("kp_teta = " + str(kteta_p))
        kteta_i=struct.unpack('!f',res[4:8])
        print("ki_teta = " + str(kteta_i))
        kteta_d= struct.unpack('!f',res[8:12])
        print("kd_teta = " + str(kteta_d))

        krho_d=struct.unpack('!f',res[12:16])
        print("kd_rho = " + str(krho_d))
        krho_i= struct.unpack('!f',res[16:20])
        print("ki_rho = " + str(krho_i))
        krho_p= struct.unpack('!f',res[20:])
        print("kd_rho = " + str(krho_p))


#a<<b => on ajoute b zéros à droite de a, donc multiplie par 2^b le nombre
#a>>b => supprime les b derniers bits de a, donc c'est a//(2^b)


test=Pami()

if __name__=="__main__":
    test.cmdloop()

