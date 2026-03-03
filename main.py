#!/usr/bin/env python3
# main.py
"""
Point d'entrée principal du système de gestion d'emploi du temps FSTT

Lancement de l'application:
    python main.py
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import de la fenêtre de login
from src.ui.login_window import LoginWindow

# Import de la base de données
try:
    from src.database import Database
except ImportError:
    print("⚠️ Module database non trouvé - L'application fonctionnera en mode démo")
    Database = None


class FSSTApplication:
    """
    Application principale du système FSTT
    Gère le flux de navigation entre les différentes fenêtres
    """
    
    def __init__(self):
        """Initialise l'application"""
        self.app = QApplication(sys.argv)
        self.setup_application()
        
        # Fenêtres
        self.login_window = None
        self.admin_window = None
        self.enseignant_window = None
        self.etudiant_window = None
        
        # Utilisateur connecté
        self.current_user = None
        self.current_user_type = None
        
        # Base de données
        self.db = Database() if Database else None
        
    def setup_application(self):
        """Configure les paramètres globaux de l'application"""
        
        # Nom et organisation
        self.app.setApplicationName("FSTT - Gestion Emploi du Temps")
        self.app.setOrganizationName("Faculté des Sciences et Techniques de Tanger")
        
        # Police par défaut
        font = QFont("Segoe UI", 10)
        self.app.setFont(font)
        
        # Style général
        self.app.setStyle("Fusion")
        
        # Icône (si disponible)
        icon_path = os.path.join('assets', 'images', 'fst_logo.png')
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))
    
    def run(self):
        """Lance l'application"""
        print("=" * 60)
        print("🎓 FSTT - Système de Gestion d'Emploi du Temps")
        print("=" * 60)
        
        # Vérifier la base de données
        if self.db:
            print("✅ Base de données connectée")
            # Auto-clean expired reservations
            try:
                deleted = self.db.supprimer_reservations_expirees()
                if deleted > 0:
                    print(f"🧹 {deleted} réservation(s) expirée(s) supprimée(s)")
            except Exception as e:
                print(f"⚠️ Nettoyage réservations: {e}")
        else:
            print("⚠️  Mode démo (sans base de données)")
        
        print("\n🚀 Lancement de l'interface...")
        
        # Afficher la fenêtre de login
        self.show_login()
        
        # Lancer la boucle d'événements Qt
        return self.app.exec()
    
    def show_login(self):
        """Affiche la fenêtre de connexion"""
        self.login_window = LoginWindow(self.db)
        
        # Connecter le signal de succès
        self.login_window.login_success.connect(self.on_login_success)
        
        # Afficher la fenêtre
        self.login_window.show()
    
    def on_login_success(self, user, user_type):
        """
        Callback appelé lors d'une connexion réussie
        
        Args:
            user: Objet utilisateur (Admin/Enseignant/Etudiant)
            user_type: Type d'utilisateur ('admin', 'enseignant', 'etudiant')
        """
        self.current_user = user
        self.current_user_type = user_type
        
        print(f"\n✅ Connexion réussie!")
        print(f"   Type: {user_type}")
        
        # Rediriger vers l'interface appropriée
        if user_type == 'admin':
            self.show_admin_window()
        elif user_type == 'enseignant':
            self.show_enseignant_window()
        elif user_type == 'etudiant':
            self.show_etudiant_window()
        else:
            QMessageBox.critical(
                None,
                "Erreur",
                f"Type d'utilisateur inconnu: {user_type}"
            )
    
    def show_admin_window(self):
        """Affiche l'interface administrateur"""
        print("\n📊 Chargement de l'interface administrateur...")
        
        try:
            from src.ui.admin_window import AdminWindow
            self.admin_window = AdminWindow(self.current_user, self.db)
            # Connecter le signal de déconnexion
            if hasattr(self.admin_window, 'logout_signal'):
                self.admin_window.logout_signal.connect(self.logout)
                
            self.admin_window.showMaximized()
            # Fermer la fenêtre de login uniquement après le succès de l'ouverture admin
            if self.login_window:
                self.login_window.close()
                
        except Exception as e:
            print(f"❌ Erreur lors du chargement de l'admin: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(None, "Erreur Critique", f"Impossible de charger l'interface administrateur:\n{str(e)}")
    
    def show_enseignant_window(self):
        """Affiche l'interface enseignant"""
        print("\n👨‍🏫 Chargement de l'interface enseignant...")
        
        try:
            from src.ui.enseignant_window import EnseignantWindow
            self.enseignant_window = EnseignantWindow(self.current_user, self.db)
            if hasattr(self.enseignant_window, 'logout_signal'):
                self.enseignant_window.logout_signal.connect(self.logout)
                
            self.enseignant_window.show()
            if self.login_window:
                self.login_window.close()
        except Exception as e:
            print(f"❌ Erreur Enseignant: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(None, "Erreur", f"Impossible de charger l'interface enseignant:\n{str(e)}")
    
    def show_etudiant_window(self):
        """Affiche l'interface étudiant"""
        print("\n👨‍🎓 Chargement de l'interface étudiant...")
        
        try:
            from src.ui.etudiant_window import EtudiantWindow
            self.etudiant_window = EtudiantWindow(self.current_user, self.db)
            if hasattr(self.etudiant_window, 'logout_signal'):
                self.etudiant_window.logout_signal.connect(self.logout)
                
            self.etudiant_window.show()
            if self.login_window:
                self.login_window.close()
        except Exception as e:
            print(f"❌ Erreur Étudiant: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(None, "Erreur", f"Impossible de charger l'interface étudiant:\n{str(e)}")


    
    def logout(self):
        """Déconnecte l'utilisateur actuel et revient au login"""
        print(f"\n👋 Déconnexion de {self.current_user_type}")
        self.current_user = None
        self.current_user_type = None
        
        # Fermer les fenêtres actives
        if self.admin_window: self.admin_window.close()
        if self.enseignant_window: self.enseignant_window.close()
        if self.etudiant_window: self.etudiant_window.close()
        
        self.admin_window = None
        self.enseignant_window = None
        self.etudiant_window = None
        
        # Réafficher le login
        self.show_login()


# ═══════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════

def main():
    """Fonction principale"""
    
    # Créer et lancer l'application
    app = FSSTApplication()
    sys.exit(app.run())


if __name__ == '__main__':
    main()