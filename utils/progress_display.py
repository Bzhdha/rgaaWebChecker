import sys
import os

class ProgressDisplay:
    def __init__(self):
        self.last_message = ""
        self.is_first_message = True
        self.last_length = 0

    def update(self, message):
        # Calculer la longueur nécessaire pour effacer la ligne précédente
        padding = max(self.last_length - len(message), 0)
        
        if self.is_first_message:
            # Pour le premier message, on affiche simplement
            sys.stdout.write(message)
            self.is_first_message = False
        else:
            # Pour les messages suivants, on revient au début de la ligne
            sys.stdout.write(f"\r{message}{' ' * padding}")
        
        sys.stdout.flush()
        self.last_message = message
        self.last_length = len(message)

    def clear(self):
        # Effacer la ligne actuelle
        if self.last_length > 0:
            sys.stdout.write(f"\r{' ' * self.last_length}\r")
            sys.stdout.flush()
        self.last_message = ""
        self.last_length = 0
        self.is_first_message = True 