import sys
import os
import logging

# Pour charger les variables d'environnement depuis .env
from dotenv import load_dotenv
load_dotenv()

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# Activez le logging si vous voulez voir en détail ce que fait Spotipy
logging.basicConfig(level=logging.INFO)

# Récupération des identifiants et variables d'environnement
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SCOPE = "user-read-currently-playing user-read-playback-state"

class SpotifyOverlay(QWidget):
    def __init__(self, spotify):
        super().__init__()
        self.spotify = spotify

        # Paramètres de fenêtre : overlay au-dessus, sans bordure
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Label pour afficher le titre / artiste
        self.label = QLabel("Chargement du titre...", self)
        self.label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 128); padding: 5px;")
        self.label.setFont(QFont("Arial", 12, QFont.Bold))
        self.label.adjustSize()

        # Timer pour rafraîchir toutes les 5 secondes
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_track_info)
        self.timer.start(5000)

        # Première mise à jour
        self.update_track_info()

    def update_track_info(self):
        track_info = self.get_current_track()
        self.label.setText(track_info)
        self.label.adjustSize()

    def get_current_track(self):
        """
        Utilise l’API Spotify pour récupérer le morceau en cours de lecture.
        """
        try:
            current = self.spotify.current_user_playing_track()
            if current and current.get('item'):
                item = current['item']
                track_name = item['name']
                artists = [artist['name'] for artist in item['artists']]
                return f"{track_name} - {', '.join(artists)}"
            else:
                return "Pas de lecture en cours"
        except Exception as e:
            print("Erreur Spotify:", e)
            return "Erreur de connexion"

def run_gui(spotify):
    """
    Lance l’interface PyQt avec l’overlay.
    """
    app = QApplication(sys.argv)
    overlay = SpotifyOverlay(spotify)
    overlay.show()
    # Position de l'overlay (50, 50) -> coin en haut à gauche
    overlay.move(50, 50)
    sys.exit(app.exec_())

def main():
    # 1) On crée l'auth manager Spotipy en mode manuel (open_browser=False)
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        open_browser=False
    )

    # 2) Contrôle : si on a déjà un token valide en cache, Spotipy le récupérera.
    token_info = auth_manager.get_cached_token()
    if token_info:
        # On a un token -> on instancie Spotipy et on lance l'UI
        print("[INFO] Token déjà présent en cache, pas besoin de réauthentifier.")
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        run_gui(spotify)
    else:
        # Pas de token en cache -> on lance l'URL d'autorisation manuellement
        auth_url = auth_manager.get_authorize_url()
        print("1) Copiez ce lien dans votre navigateur pour autoriser l’application :")
        print(auth_url)
        print("2) Après avoir accepté, copiez l’URL de redirection (http://localhost:8888/callback?code=...) et collez-la ci-dessous :")
        response = input("URL de redirection : ")

        # 3) Spotipy va extraire le 'code' de l'URL fournie
        code = auth_manager.parse_response_code(response)
        if code:
            print("[INFO] Code récupéré:", code)
            # On récupère le token (et on le stocke en cache)
            token_info = auth_manager.get_access_token(code, as_dict=True)
            if token_info:
                print("[INFO] Token récupéré avec succès.")
                # Maintenant, on peut instancier Spotipy
                spotify = spotipy.Spotify(auth_manager=auth_manager)
                run_gui(spotify)
            else:
                print("[ERREUR] Impossible d’obtenir le token. Vérifiez votre URL.")
        else:
            print("[ERREUR] Pas de code dans l’URL de redirection.")

if __name__ == "__main__":
    main()
