import time
import logging
import struct
import paho.mqtt.client as mqtt
from paho.mqtt.subscribeoptions import SubscribeOptions

BOUTISME_STRUCT = "<"

class ObjetSujet:
	def __init__(self, nom_sujet, retenu=False, qds=0):
		self.nom_sujet = nom_sujet
		self.retenu = retenu
		self.qds = qds
		self.utilisateur = None

	def attacher(self, utilisateur):
		self.utilisateur = utilisateur

	def maj(self):
		if self.utilisateur is not None:
			self.utilisateur.maj_objet(self)

	def serialiser(self):
		raise NotImplementedError("Serialiser n'est pas implémenté dans un objet de sujet")

	def deserialiser(self, donnee, client):
		raise NotImplementedError("Déserialiser n'est pas implémenté dans un objet de sujet")

class InfoRobot(ObjetSujet):
	def __init__(self, nom, retenu=False, qds=0):
		super().__init__(f"info_robot_{nom}", retenu, qds)
		self.x = 0
		self.y = 0
		self.theta = 0

	def serialiser(self):
		return struct.pack(BOUTISME_STRUCT+"fff", self.x, self.y, self.theta)

	def deserialiser(self, donnee, client):
		self.x, self.y, self.theta = struct.unpack(BOUTISME_STRUCT+"fff", donnee)

class InfoDebut(ObjetSujet):
	def __init__(self, retenu=False, qds=0):
		super().__init__("info_debut", retenu, qds)
		self.demarre = False
		self.temps = 0

	def demarrer(self):
		self.demarre = True
		self.temps = time.time()
		self.maj()

	def attends(self):
		while not self.demarre:
			time.sleep(0.01)

	def serialiser(self):
		return struct.pack(BOUTISME_STRUCT+"?f", self.demarre, self.temps)

	def deserialiser(self, donnee, client):
		self.demarre, self.temps = struct.unpack(BOUTISME_STRUCT+"?f", donnee)
		

class Utilisateur:
	def __init__(self, identifiant="", motdepasse="", ip_serveur_mqtt="127.0.0.1", objets_sujets=[], f_rappel=None):
		self.nom = f"anon_{time.time():0.0f}" if not identifiant else identifiant
		self.journaliseur = logging.getLogger(f"MQTT:{self.nom}")

		self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
		self.mqttc.on_message = self.on_message
		self.mqttc.on_connect = self.on_connect
		self.mqttc.username = identifiant
		self.mqttc.password = motdepasse
		self.mqttc.connect(ip_serveur_mqtt, 1883, 60)

		self.rappel = f_rappel
		self.objets_sujets = objets_sujets
		self.sujets = {}
		for objet in self.objets_sujets:
			if not isinstance(objet, ObjetSujet):
				self.journaliseur.warn(f"Objet de sujet {objet} n'en est pas un, on l'ignore.")
				self.objets_sujets.remove(objet)
				continue

			self.sujets[objet.nom_sujet] = objet
			objet.attacher(self)

	def on_message(self, client, userdata, msg):
		sujet = msg.topic
		donnee = msg.payload
		self.journaliseur.debug(f"Reçu {sujet}': {donnee}")
		if sujet not in self.sujets:
			self.journaliseur.warn(f"Pas d'objets associés au sujet reçu: {sujet}")
			return

		# On met à jour l'objet
		objet = self.sujets[sujet]
		objet.deserialiser(donnee, client)

		# Rappel au cas ou
		if self.rappel is not None:
			self.rappel(objet, client)

	def on_connect(self, client, userdata, flags, reason_code, properties):
		self.journaliseur.info(f"Connecté au serveur MQTT avec le code de retour {reason_code}")
		# On s'abonne dans le on_connect pour pouvoir gérer les pertes de connections.
		for objet in self.objets_sujets:
			client.subscribe(objet.nom_sujet, options=SubscribeOptions(noLocal=True))

	def maj_objet(self, objet):
		sujet = objet.nom_sujet
		donnee = objet.serialiser()
		self.journaliseur.debug(f"Envoie {sujet}: {donnee}")
		self.mqttc.publish(sujet, donnee, qos=objet.qds, retain=objet.retenu)

	def demarre_fil(self):
		self.mqttc.loop_start()

	def coupe_fil(self):
		self.mqttc.loop_stop()

class Poulet(Utilisateur):
	def __init__(self, ip_serveur_mqtt="127.0.0.1", objets_sujets=[], f_rappel=None):
		super().__init__("POULET", "4444719", ip_serveur_mqtt, objets_sujets, f_rappel)

class Nuke(Utilisateur):
	def __init__(self, ip_serveur_mqtt="127.0.0.1", objets_sujets=[], f_rappel=None):
		super().__init__("NUKE", "mespronomssontla/elle", ip_serveur_mqtt, objets_sujets, f_rappel)

class Pamiserable(Utilisateur):
	def __init__(self, ip_serveur_mqtt="127.0.0.1", objets_sujets=[], f_rappel=None):
		super().__init__("PAMISERABLE", "parpaingaroulette", ip_serveur_mqtt, objets_sujets, f_rappel)

class Paminable(Utilisateur):
	def __init__(self, ip_serveur_mqtt="127.0.0.1", objets_sujets=[], f_rappel=None):
		super().__init__("PAMINABLE", "pouussinng", ip_serveur_mqtt, objets_sujets, f_rappel)

if __name__ == "__main__":
	import argparse
	
	annuaire = {"NUKE":Nuke, "POULET":Poulet, "PAMISERABLE":Pamiserable, "PAMINABLE":Paminable}
	
	argumentateur = argparse.ArgumentParser(prog='publieur_commun',
											description='communication mqtt entre robot et station sol',
											epilog='8==============================================>')
	argumentateur.add_argument('-q', choices=annuaire.keys(), default="NUKE", help="qui fait tourner le script ?")
	
	arguments = argumentateur.parse_args()
	rob = InfoRobot("bob")
	util = annuaire[arguments.q](objets_sujets=[rob], f_rappel=lambda x,y:print(x.x,x.y,x.theta))
	logging.basicConfig(format="%(asctime)s: %(message)s",
						level=logging.DEBUG,
						datefmt="%H:%M:%S")

	util.demarre_fil()
	while True:
		time.sleep(1)
		if arguments.q == "POULET":
			rob.x += 1
			rob.y -= 1
			rob.theta += 5
			rob.maj()
			print("Maj")
