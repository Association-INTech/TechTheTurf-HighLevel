from os import wait
import time
import sys
import logging
import argparse
import paho.mqtt.client as mqtt

class Utilisateur():
    def __init__(self, f_rappel):
        self.nom = f"anon_{time.time():0.0f}"
        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format,
                            level=logging.DEBUG,
                            datefmt="%H:%M:%S")
        self.journaliseur = logging.getLogger(self.nom)
        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttc.on_message = self.on_message
        self.mqttc.on_connect = self.on_connect
        self.mqttc.connect("127.0.0.1", 1883, 60)
        self.rappel = f_rappel
    def on_message(self, client, userdata, msg):
        self.rappel(client, msg)
        self.journaliseur.info(msg.topic+" "+str(msg.payload))
    def on_connect(self, client, userdata, flags, reason_code, properties):
        self.journaliseur.info(f"Connected with result code {reason_code}")
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe("toptoptopictropipal")
    def message(self, topic="toptoptopictropipal"):
        self.journaliseur.info(self.mqttc.publish(topic, f"{self.nom} : chalut chat va la pêche ?"))
    def fil(self):
        self.mqttc.loop_start()
    def coupe_fil(self):
        self.mqttc.loop_stop()
class Poulet(Utilisateur):
    def __init__(self):
        Utilisateur.__init__(self)
        self.nom = "POULET"

class Nuke(Utilisateur):
    def __init__(self):
        Utilisateur.__init__(self)
        self.nom = "NUKE"
def main(u):
    ut = Poulet() if u == "POULET" else Nuke()
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format,
                        level=logging.DEBUG,
                        datefmt="%H:%M:%S")
    ut.fil()
    #mqttc.on_log = logging.info
#    mqttc.enable_logger(journaliseur)
    # mqttc.connect("mqtt.eclipseprojects.io", 1883, 60)

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
        # ut.message()
if __name__ == "__main__":
    annuaire = ["NUKE", "POULET", "pamisérable"]
    argumentateur = argparse.ArgumentParser(
                    prog='publieur_commun',
                    description='communication mqtt entre robot et station sol',
                    epilog='8==============================================>')
    argumentateur.add_argument('-q',  choices=annuaire, help="qui fait tourner le script ?")
    argumentateur.add_argument('-d', choices = ["DEBUG", "INFO"], help = "niveau de déboguage")
    arguments = argumentateur.parse_args()
    main(u=arguments.q)
