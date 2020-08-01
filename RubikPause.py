# Created by Wayne Porter and modify by Rubikshow

from ..Script import Script


class RubikPause(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Rubik Pause",
            "key": "RubikPause",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "LAYER1":
                {
                    "label": "LAYER 1",
                    "description": "Layer on on lance le script",
                    "type": "int"
                },
                "park_print_head":
                {
                    "label": "Park",
                    "description": "Bouger le chariot à une position précise pour changer el filament",
                    "type": "bool",
                    "default_value": true
                },
                "head_park_y":
                {
                    "label": "Position y park",
                    "description": "position de park y",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 235,
                    "enabled": "park_print_head"
                },
                "head_park_x":
                {
                    "label": "Position x park",
                    "description": "position de park x",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 235,
                    "enabled": "park_print_head"
                },
                "pause_length":
                {
                    "label": "Pause timing",
                    "description": "Combien de temps faut t-il attendre sans bouger à la position 1",
                    "type": "int",
                    "default_value": 60,
                    "minimum_value": 0,
                    "unit": "s",
                    "enabled": "park_print_head"
                },
                "park_feed_rate":
                {
                    "label": "Vitesse de mouvement",
                    "description": "A quel vitesse le chariot va se déplacer",
                    "unit": "mm/s",
                    "type": "float",
                    "default_value": 2000,
                    "enabled": "park_print_head"
                },
                "extrude":
                {
                    "label": "Extruder",
                    "description": "Souhaitez-vous extruder le filament",
                    "type": "bool",
                    "default_value": false
                },
                "extrud":
                {
                    "label": "Longueur de l'extrusion",
                    "description": "De combien de mm voulez-vous extruder le filament ?",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 100,
                    "enabled": "extrude"
                },
                "extrud_rapidity":
                {
                    "label": "Vitesse de l'extrusion",
                    "description": "A quel vitesse vous souhaitez extruder le filament ?",
                    "unit": "mm/s",
                    "type": "float",
                    "default_value": 15000,
                    "enabled": "extrude"
                },
                "modifyz":
                {
                    "label": "Modifier Z",
                    "description": "Lever le charriot (en Z) afin que la buse ne touche pas la paroi en premier.",
                    "type": "bool",
                    "default_value": false
                },
                "zadd":
                {
                    "label": "Valeur Z ajouter",
                    "description": "A combien faut il lever le charriot(en mm)",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 3,
                    "enabled": "modifyz"
                }
            }
        }"""

    def execute(self, data):
        modifyz = self.getSettingValueByKey("modifyz")
        zadd = self.getSettingValueByKey("zadd")
        feed_rate = self.getSettingValueByKey("park_feed_rate")
        extrude = self.getSettingValueByKey("extrude")
        extrud = self.getSettingValueByKey("extrud")
        extrud_rapidity = self.getSettingValueByKey("extrud_rapidity")
        park_print_head = self.getSettingValueByKey("park_print_head")
        x_park = self.getSettingValueByKey("head_park_x")
        y_park = self.getSettingValueByKey("head_park_y")
        pause_length = self.getSettingValueByKey("pause_length")
        LAYER1 = self.getSettingValueByKey("LAYER1")
        gcode_to_append = ""
        last_x = 0
        last_y = 0
        last_z = 0
        last_e = 0

        if park_print_head:
            gcode_to_append += self.putValue(G=1, F=feed_rate, X=x_park, Y=y_park) + " ;Park print head\n"
            gcode_to_append += self.putValue(M=400) + " ;Wait for moves to finish\n"

        for idx, layer in enumerate(data):
            for line in layer.split("\n"):
                if self.getValue(line, "G") in {0, 1}:  # Track X,Y,Z,E location.
                    last_x_recup = self.getValue(line, "X", last_x)
                    last_y_recup = self.getValue(line, "Y", last_y)
                    last_z_recup = self.getValue(line, "Z", last_z)
                    last_e_recup = self.getValue(line, "E", last_e)
                    if last_x_recup != 0:
                        last_x = last_x_recup
                    if last_y_recup != 0:
                        last_y = last_y_recup
                    if last_z_recup != 0:
                        last_z = last_z_recup
                    if last_e_recup != 0:
                        last_e = last_e_recup
            # Check that a layer is being printed
            lines = layer.split("\n")
            for line in lines:
                if (";LAYER:%s"%(LAYER1)) in line :

                    extrusion = last_e-extrud
                    z = last_z+zadd

                    layer += ";RubikPause Begin\n"

                    layer += gcode_to_append

                    if extrude:
                        layer += "G1 E%s F%s ;retract\n" % (extrusion, extrud_rapidity)
                        layer += "M400 ;attendre la fin du mouvement\n"
                        layer += "G4 S%s ; Pause\n" % (pause_length)
                        layer += "G1 E%s F%s ;extrusion\n" % (last_e, extrud_rapidity)
                        layer += "M400 ;attendre la fin du mouvement\n"
                        layer += "G4 S%s ; Pause\n" % (pause_length)

                    if modifyz:
                        layer += "G0 X%s Y%s Z%s;retour pos d'origine + z\n" % (last_x, last_y, z)
                        layer += "M400 ;attendre la fin du mouvement\n"
                        layer += "G1 X%s Y%s Z%s E%s ;retour pos d'origine\n" % (last_x, last_y, last_z, last_e)
                    else:
                        layer += "G1 X%s Y%s E%s ;retour pos d'origine\n" % (last_x, last_y, last_e)

                    layer += "M400 ;attendre la fin du mouvement\n"

                    layer += ";RubikPause End\n"

                    data[idx] = layer
                    break
        return data
