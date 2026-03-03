# src/database.py
import sqlite3
import hashlib
import os
import shutil
from datetime import datetime
from config import DATABASE_PATH

class Database:
    """Classe pour gérer la base de données SQLite - FSTT"""
    
    # Mapping from filière names to departments for teacher-group filtering
    FILIERE_TO_DEPT = {
        # Informatique
        'gi': 'informatique', 'génie informatique': 'informatique',
        'idai': 'informatique', 'lssd': 'informatique',
        'ad': 'informatique', 'analytique des données': 'informatique',
        'iasd': 'informatique', 'mbd': 'informatique',
        'sitbd': 'informatique', 'sim': 'informatique',
        'tc-gi': 'informatique',
        
        # Mathématiques
        'ma': 'mathématiques', 'mathématiques et applications': 'mathématiques',
        'is': 'mathématiques', 'ingénierie statistique': 'mathématiques',
        'lmid': 'mathématiques', 'tc-msd': 'mathématiques',
        'mmsd': 'mathématiques', 'aais': 'mathématiques',
        
        # Physique
        'tc-gp': 'physique', 'enr': 'physique',
        'énergies renouvelables': 'physique', 'ge': 'physique',
        
        # Chimie
        'tc-gc': 'chimie', 'gp': 'chimie', 'génie des procédés': 'chimie',
        'tac': 'chimie', 'gmpm': 'chimie',
        
        # Biologie
        'tc-gb': 'biologie', 'biot': 'biologie', 'biotechnologies': 'biologie',
        'bcmb': 'biologie', 'sa': 'biologie', 'eadd': 'biologie',
        
        # Géologie/Géosciences
        'tc-geg': 'géologie', 'ga': 'géologie', 'géosciences appliquées': 'géologie',
        'ger': 'géologie', 'slap': 'géologie', 'rrn': 'géologie',
        'se': 'géologie', 'iecdd': 'géologie',
        
        # Génie Électrique
        'tc-gese': 'génie électrique', 'gesi': 'génie électrique',
        'gemi': 'génie électrique',
        
        # Génie Mécanique/Industriel
        'tc-gmsi': 'génie mécanique', 'gi-ing': 'génie industriel',
        'dip': 'génie mécanique', 'design industriel': 'génie mécanique',
        
        # Génie Civil
        'gc': 'génie civil', 'gc-m': 'génie civil',
    }
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def get_connection(self):
        """Retourne une connexion à la base de données"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        return conn
    
    def hash_password(self, password):
        """Hash un mot de passe avec SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    # ═══════════════════════════════════════════════════════════
    # CRÉATION DES TABLES
    # ═══════════════════════════════════════════════════════════
    
    def init_database(self):
        """Crée toutes les tables de la base de données"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table 1 : Utilisateurs (avec duree_max_jour)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                mot_de_passe TEXT NOT NULL,
                type_user TEXT NOT NULL CHECK(type_user IN ('admin', 'enseignant', 'etudiant')),
                specialite TEXT,
                groupe_id INTEGER,
                duree_max_jour INTEGER DEFAULT 480,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (groupe_id) REFERENCES groupes(id) ON DELETE SET NULL
            )
        ''')
        
        # Table 2 : Filières
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS filieres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                niveau TEXT NOT NULL CHECK(niveau IN ('L1', 'L2', 'L3', 'M1', 'M2'))
            )
        ''')
        
        # Table 3 : Groupes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groupes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                effectif INTEGER NOT NULL CHECK(effectif > 0),
                filiere_id INTEGER NOT NULL,
                FOREIGN KEY (filiere_id) REFERENCES filieres(id) ON DELETE CASCADE
            )
        ''')
        
        # Table 4 : Salles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS salles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT UNIQUE NOT NULL,
                capacite INTEGER NOT NULL CHECK(capacite > 0),
                type_salle TEXT NOT NULL CHECK(type_salle IN ('Salle', 'Amphithéâtre', 'Laboratoire')),
                equipements TEXT
            )
        ''')
        
        # Table 5 : Séances
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titre TEXT NOT NULL,
                type_seance TEXT NOT NULL CHECK(type_seance IN ('Cours', 'TD', 'TP', 'Examen')),
                date TEXT NOT NULL,
                heure_debut TEXT NOT NULL,
                heure_fin TEXT NOT NULL,
                salle_id INTEGER,
                enseignant_id INTEGER,
                groupe_id INTEGER,
                FOREIGN KEY (salle_id) REFERENCES salles(id) ON DELETE SET NULL,
                FOREIGN KEY (enseignant_id) REFERENCES utilisateurs(id) ON DELETE SET NULL,
                FOREIGN KEY (groupe_id) REFERENCES groupes(id) ON DELETE CASCADE
            )
        ''')
        
        # Table 6 : Réservations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enseignant_id INTEGER NOT NULL,
                salle_id INTEGER NOT NULL,
                groupe_id INTEGER,
                date TEXT NOT NULL,
                heure_debut TEXT NOT NULL,
                heure_fin TEXT NOT NULL,
                statut TEXT DEFAULT 'en_attente' CHECK(statut IN ('en_attente', 'validee', 'rejetee')),
                motif TEXT,
                date_demande TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (enseignant_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
                FOREIGN KEY (salle_id) REFERENCES salles(id) ON DELETE CASCADE,
                FOREIGN KEY (groupe_id) REFERENCES groupes(id) ON DELETE SET NULL
            )
        ''')
        
        # Table 7 : Disponibilités
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS disponibilites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enseignant_id INTEGER NOT NULL,
                date_debut TEXT NOT NULL,
                date_fin TEXT NOT NULL,
                motif TEXT,
                FOREIGN KEY (enseignant_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
            )
        ''')
        
        # Table 8 : Historique des imports
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historique_imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_import TEXT NOT NULL,
                nb_lignes INTEGER NOT NULL,
                date_import TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fichier_nom TEXT,
                admin_id INTEGER,
                FOREIGN KEY (admin_id) REFERENCES utilisateurs(id)
            )
        ''')
        
        # Table 9 : Notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                destinataire_id INTEGER NOT NULL,
                type_notification TEXT NOT NULL CHECK(type_notification IN ('rattrapage', 'absence', 'annulation', 'info', 'alerte', 'reservation', 'modification')),
                titre TEXT NOT NULL,
                message TEXT NOT NULL,
                lue INTEGER DEFAULT 0,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                seance_id INTEGER,
                FOREIGN KEY (destinataire_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
                FOREIGN KEY (seance_id) REFERENCES seances(id) ON DELETE SET NULL
            )
        ''')
        
        # Table 10 : Rattrapages (Makeup sessions)
        # Note: UNIQUE constraint on (salle_id, date, heure_debut) prevents race conditions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rattrapages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enseignant_id INTEGER NOT NULL,
                groupe_id INTEGER NOT NULL,
                salle_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                heure_debut TEXT NOT NULL,
                heure_fin TEXT NOT NULL,
                motif TEXT,
                statut TEXT DEFAULT 'en_attente' CHECK(statut IN ('en_attente', 'confirmé', 'annulé', 'rejete')),
                motif_rejet TEXT,
                seance_originale_id INTEGER,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (enseignant_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
                FOREIGN KEY (groupe_id) REFERENCES groupes(id) ON DELETE CASCADE,
                FOREIGN KEY (salle_id) REFERENCES salles(id) ON DELETE CASCADE,
                FOREIGN KEY (seance_originale_id) REFERENCES seances(id) ON DELETE SET NULL,
                UNIQUE (salle_id, date, heure_debut, statut) 
            )
        ''')
        
        # Table 11 : Modules (pour contrainte spécialité enseignant)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                nom TEXT NOT NULL,
                departement TEXT NOT NULL,
                filiere_id INTEGER,
                volume_cours INTEGER DEFAULT 0,
                volume_td INTEGER DEFAULT 0,
                volume_tp INTEGER DEFAULT 0,
                FOREIGN KEY (filiere_id) REFERENCES filieres(id) ON DELETE SET NULL
            )
        ''')
        
        conn.commit()
        
        # ── Migration: update notifications CHECK constraint to include 'modification' ──
        self._migrate_notifications_table(conn if not conn.in_transaction else None)
        
        conn.close()
        print("✅ Base de données initialisée avec succès!")
        print(f"📁 Fichier : {self.db_path}")
        print(f"📊 Tables créées : 10 tables")
    
    def _migrate_notifications_table(self, conn_param=None):
        """Migrate notifications table to add 'modification' to CHECK constraint if needed"""
        conn = conn_param or self.get_connection()
        cursor = conn.cursor()
        try:
            # Check current schema
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='notifications'")
            row = cursor.fetchone()
            if row and "'modification'" not in (row[0] or ''):
                # Need to recreate table with new CHECK constraint
                cursor.execute("ALTER TABLE notifications RENAME TO notifications_old")
                cursor.execute('''
                    CREATE TABLE notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        destinataire_id INTEGER NOT NULL,
                        type_notification TEXT NOT NULL CHECK(type_notification IN ('rattrapage', 'absence', 'annulation', 'info', 'alerte', 'reservation', 'modification')),
                        titre TEXT NOT NULL,
                        message TEXT NOT NULL,
                        lue INTEGER DEFAULT 0,
                        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        seance_id INTEGER,
                        FOREIGN KEY (destinataire_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
                        FOREIGN KEY (seance_id) REFERENCES seances(id) ON DELETE SET NULL
                    )
                ''')
                cursor.execute("INSERT INTO notifications SELECT * FROM notifications_old")
                cursor.execute("DROP TABLE notifications_old")
                conn.commit()
                print("✅ Migration: notifications table updated with 'modification' type")
        except Exception as e:
            print(f"⚠️ Migration notifications: {e}")
        finally:
            if not conn_param:
                conn.close()
    
    # ═══════════════════════════════════════════════════════════
    # SÉCURITÉ ET BACKUP
    # ═══════════════════════════════════════════════════════════

    def sauvegarder_bdd(self):
        """Crée une sauvegarde de sécurité de la base de données"""
        if os.path.exists(self.db_path):
            backup_dir = os.path.join(os.path.dirname(self.db_path), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_fstt_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_name)
            
            shutil.copy2(self.db_path, backup_path)
            print(f"🛡️ Sauvegarde créée : {backup_path}")
            return backup_path
        return None
    
    # ═══════════════════════════════════════════════════════════
    # MÉTHODES CRUD - UTILISATEURS
    # ═══════════════════════════════════════════════════════════
    
    def ajouter_utilisateur(self, nom, prenom, email, mot_de_passe, type_user, 
                           specialite=None, groupe_id=None, duree_max_jour=480):
        """Ajoute un utilisateur (avec durée max pour enseignants)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        mot_de_passe_hash = self.hash_password(mot_de_passe)
        
        try:
            cursor.execute('''
                INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, type_user, 
                                        specialite, groupe_id, duree_max_jour)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nom, prenom, email, mot_de_passe_hash, type_user, specialite, 
                  groupe_id, duree_max_jour))
            
            conn.commit()
            user_id = cursor.lastrowid
            return user_id
        except sqlite3.IntegrityError:
            print(f"❌ Email {email} déjà utilisé")
            return None
        finally:
            conn.close()
    
    def verifier_connexion(self, email, mot_de_passe):
        """Vérifie les identifiants de connexion"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        mot_de_passe_hash = self.hash_password(mot_de_passe)
        
        cursor.execute('''
            SELECT * FROM utilisateurs 
            WHERE email = ? AND mot_de_passe = ?
        ''', (email, mot_de_passe_hash))
        
        user = cursor.fetchone()
        conn.close()
        
        return user
    
    def supprimer_tous_utilisateurs_type(self, type_user):
        """Supprime tous les utilisateurs d'un type (pour import)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM utilisateurs WHERE type_user = ?', (type_user,))
        nb_supprime = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return nb_supprime
    
    def get_tous_utilisateurs(self, type_user=None):
        """Récupère tous les utilisateurs (optionnel : filtré par type)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if type_user:
            cursor.execute('SELECT * FROM utilisateurs WHERE type_user = ?', (type_user,))
        else:
            cursor.execute('SELECT * FROM utilisateurs')
        
        utilisateurs = cursor.fetchall()
        conn.close()
        
        return utilisateurs

    def get_utilisateur_by_id(self, user_id):
        """Récupère un utilisateur par son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM utilisateurs WHERE id = ?', (user_id,))
        utilisateur = cursor.fetchone()
        
        conn.close()
        return utilisateur

    def get_utilisateur_by_email(self, email):
        """Récupère un utilisateur par son email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM utilisateurs WHERE email = ?', (email,))
        utilisateur = cursor.fetchone()
        
        conn.close()
        return utilisateur

    def modifier_utilisateur(self, user_id, nom=None, prenom=None, email=None, 
                            mot_de_passe=None, specialite=None, groupe_id=None,
                            duree_max_jour=None):
        """Modifie les informations d'un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Construction dynamique de la requête
        champs = []
        valeurs = []
        
        if nom:
            champs.append("nom = ?")
            valeurs.append(nom)
        if prenom:
            champs.append("prenom = ?")
            valeurs.append(prenom)
        if email:
            champs.append("email = ?")
            valeurs.append(email)
        if mot_de_passe:
            champs.append("mot_de_passe = ?")
            valeurs.append(self.hash_password(mot_de_passe))
        if specialite is not None:
            champs.append("specialite = ?")
            valeurs.append(specialite)
        if groupe_id is not None:
            champs.append("groupe_id = ?")
            valeurs.append(groupe_id)
        if duree_max_jour is not None:
            champs.append("duree_max_jour = ?")
            valeurs.append(duree_max_jour)
        
        if not champs:
            return False
        
        valeurs.append(user_id)
        requete = f"UPDATE utilisateurs SET {', '.join(champs)} WHERE id = ?"
        
        try:
            cursor.execute(requete, valeurs)
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(f"❌ Erreur lors de la modification : {e}")
            return False
        finally:
            conn.close()

    def supprimer_utilisateur(self, user_id):
        """Supprime un utilisateur par son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM utilisateurs WHERE id = ?', (user_id,))
        nb_supprime = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return nb_supprime > 0

    # ═══════════════════════════════════════════════════════════
    # MÉTHODES - CONTRAINTES ENSEIGNANTS
    # ═══════════════════════════════════════════════════════════

    def get_duree_max_enseignant(self, enseignant_id):
        """Récupère la durée max journalière d'un enseignant (en minutes)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT duree_max_jour FROM utilisateurs 
            WHERE id = ? AND type_user = 'enseignant'
        ''', (enseignant_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 480  # 480 min = 8h par défaut

    def modifier_duree_max_enseignant(self, enseignant_id, duree_minutes):
        """Modifie la durée max journalière d'un enseignant"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE utilisateurs 
            SET duree_max_jour = ?
            WHERE id = ? AND type_user = 'enseignant'
        ''', (duree_minutes, enseignant_id))
        
        conn.commit()
        nb_modif = cursor.rowcount
        conn.close()
        
        return nb_modif > 0

    def calculer_duree_journee_enseignant(self, enseignant_id, date):
        """Calcule le total d'heures d'un enseignant pour une date donnée"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT heure_debut, heure_fin 
            FROM seances 
            WHERE enseignant_id = ? AND date = ?
        ''', (enseignant_id, date))
        
        seances = cursor.fetchall()
        conn.close()
        
        total_minutes = 0
        for seance in seances:
            heure_debut = seance[0]
            heure_fin = seance[1]
            duree = self.calculer_duree_minutes(heure_debut, heure_fin)
            total_minutes += duree
        
        return total_minutes

    def calculer_duree_minutes(self, heure_debut, heure_fin):
        """Calcule la durée en minutes entre deux heures (format HH:MM)"""
        from datetime import datetime
        
        fmt = "%H:%M"
        debut = datetime.strptime(heure_debut, fmt)
        fin = datetime.strptime(heure_fin, fmt)
        
        duree = (fin - debut).total_seconds() / 60
        return int(duree)

    def peut_ajouter_seance_enseignant(self, enseignant_id, date, duree_seance):
        """Vérifie si on peut ajouter une séance sans dépasser la durée max"""
        duree_actuelle = self.calculer_duree_journee_enseignant(enseignant_id, date)
        duree_max = self.get_duree_max_enseignant(enseignant_id)
        
        return (duree_actuelle + duree_seance) <= duree_max
    
    # ═══════════════════════════════════════════════════════════
    # MÉTHODES CRUD - FILIÈRES
    # ═══════════════════════════════════════════════════════════
    
    def ajouter_filiere(self, nom, niveau):
        """Ajoute une filière"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO filieres (nom, niveau)
            VALUES (?, ?)
        ''', (nom, niveau))
        
        conn.commit()
        filiere_id = cursor.lastrowid
        conn.close()
        
        return filiere_id
    
    def get_toutes_filieres(self):
        """Récupère toutes les filières"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM filieres ORDER BY niveau, nom')
        filieres = cursor.fetchall()
        
        conn.close()
        return filieres
    
    def get_filiere_by_nom(self, nom):
        """Récupère une filière par son nom"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM filieres WHERE nom = ?', (nom,))
        filiere = cursor.fetchone()
        
        conn.close()
        return filiere
    
    # ═══════════════════════════════════════════════════════════
    # MÉTHODES CRUD - GROUPES
    # ═══════════════════════════════════════════════════════════
    
    def ajouter_groupe(self, nom, effectif, filiere_id):
        """Ajoute un groupe"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO groupes (nom, effectif, filiere_id)
            VALUES (?, ?, ?)
        ''', (nom, effectif, filiere_id))
        
        conn.commit()
        groupe_id = cursor.lastrowid
        conn.close()
        
        return groupe_id
    
    def get_tous_groupes(self):
        """Récupère tous les groupes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM groupes')
        groupes = cursor.fetchall()
        
        conn.close()
        return groupes
    
    def get_groupe_by_nom_filiere(self, nom_groupe, filiere_id):
        """Récupère un groupe par nom et filière"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM groupes 
            WHERE nom = ? AND filiere_id = ?
        ''', (nom_groupe, filiere_id))
        
        groupe = cursor.fetchone()
        conn.close()
        
        return groupe
    
    def get_groupe_by_nom(self, nom_groupe):
        """Récupère un groupe par son nom (sans filière)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM groupes WHERE nom = ?', (nom_groupe,))
        groupe = cursor.fetchone()
        
        conn.close()
        return groupe
    
    def supprimer_tous_groupes(self):
        """Supprime tous les groupes (pour import)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM groupes')
        nb_supprime = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return nb_supprime
    
    # ═══════════════════════════════════════════════════════════
    # MÉTHODES CRUD - SALLES
    # ═══════════════════════════════════════════════════════════
    
    def ajouter_salle(self, nom, capacite, type_salle, equipements=""):
        """Ajoute une salle"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO salles (nom, capacite, type_salle, equipements)
                VALUES (?, ?, ?, ?)
            ''', (nom, capacite, type_salle, equipements))
            
            conn.commit()
            salle_id = cursor.lastrowid
            return salle_id
        except sqlite3.IntegrityError:
            print(f"❌ Salle {nom} existe déjà")
            return None
        finally:
            conn.close()
    
    def get_toutes_salles(self):
        """Récupère toutes les salles"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM salles ORDER BY nom')
        salles = cursor.fetchall()
        
        conn.close()
        return salles

    def get_salles_by_type(self, type_salle):
        """Récupère les salles filtrées par type (Salle, Amphithéâtre, Laboratoire)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM salles WHERE type_salle = ? ORDER BY nom', (type_salle,))
        salles = cursor.fetchall()
        conn.close()
        return salles

    def get_salles_for_session_type(self, type_seance, enseignant_specialite=None):
        """
        Returns rooms appropriate for a given session type.
        - Cours/Examen → Salle + Amphithéâtre (all)
        - TD → Salle (all regular rooms)  
        - TP → Laboratoire only, filtered by specialty if provided
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if type_seance == 'TP':
            # For TP, only labs
            cursor.execute("SELECT * FROM salles WHERE type_salle = 'Laboratoire' ORDER BY nom")
            all_labs = cursor.fetchall()
            conn.close()
            
            if not enseignant_specialite:
                return all_labs
            
            # Filter labs by specialty mapping
            spec_lower = enseignant_specialite.lower().strip()
            
            # Map specialties to lab keyword prefixes
            SPECIALITE_TO_LAB = {
                'informatique': ['info'],
                'mathématiques': ['math', 'info'],
                'physique': ['physique'],
                'chimie': ['chimie'],
                'biologie': ['bio'],
                'géologie': ['bio', 'chimie'],  # geology may use bio/chem labs
                'génie mécanique': ['gm'],
                'génie industriel': ['gm'],
                'génie électrique': ['physique', 'info'],
                'génie civil': ['gm'],
            }
            
            allowed_prefixes = SPECIALITE_TO_LAB.get(spec_lower, None)
            if allowed_prefixes is None:
                # Unknown specialty → show all labs
                return all_labs
            
            filtered = []
            for lab in all_labs:
                lab_name = lab[1].lower()
                if any(prefix in lab_name for prefix in allowed_prefixes):
                    filtered.append(lab)
            
            return filtered if filtered else all_labs
            
        elif type_seance == 'TD':
            cursor.execute("SELECT * FROM salles WHERE type_salle = 'Salle' ORDER BY nom")
            salles = cursor.fetchall()
            conn.close()
            return salles
        else:
            # Cours, Examen → all Salle + Amphithéâtre
            cursor.execute("SELECT * FROM salles WHERE type_salle IN ('Salle', 'Amphithéâtre') ORDER BY nom")
            salles = cursor.fetchall()
            conn.close()
            return salles
    
    def supprimer_toutes_salles(self):
        """Supprime toutes les salles (pour import)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM salles')
        nb_supprime = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return nb_supprime
    
    # ═══════════════════════════════════════════════════════════
    # MÉTHODES CRUD - SÉANCES
    # ═══════════════════════════════════════════════════════════

    def ajouter_seance(self, titre, type_seance, date, heure_debut, heure_fin,
                      salle_id, enseignant_id, groupe_id):
        """Ajoute une séance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO seances (titre, type_seance, date, heure_debut, heure_fin,
                                   salle_id, enseignant_id, groupe_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (titre, type_seance, date, heure_debut, heure_fin,
                  salle_id, enseignant_id, groupe_id))
            
            conn.commit()
            seance_id = cursor.lastrowid
            return seance_id
        except Exception as e:
            print(f"❌ Erreur ajout séance : {e}")
            return None
        finally:
            conn.close()

    def modifier_seance(self, seance_id, date=None, heure_debut=None, heure_fin=None,
                        salle_id=None, groupe_id=None, titre=None, type_seance=None):
        """Modifie une séance existante (champs fournis uniquement)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            updates = []
            params = []
            if date is not None:
                updates.append("date = ?"); params.append(date)
            if heure_debut is not None:
                updates.append("heure_debut = ?"); params.append(heure_debut)
            if heure_fin is not None:
                updates.append("heure_fin = ?"); params.append(heure_fin)
            if salle_id is not None:
                updates.append("salle_id = ?"); params.append(salle_id)
            if groupe_id is not None:
                updates.append("groupe_id = ?"); params.append(groupe_id)
            if titre is not None:
                updates.append("titre = ?"); params.append(titre)
            if type_seance is not None:
                updates.append("type_seance = ?"); params.append(type_seance)
            if not updates:
                return False
            params.append(seance_id)
            cursor.execute(f"UPDATE seances SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Erreur modification séance : {e}")
            return False
        finally:
            conn.close()

    def get_seance_by_id(self, seance_id):
        """Récupère une séance par son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM seances WHERE id = ?", (seance_id,))
        seance = cursor.fetchone()
        conn.close()
        return seance

    def get_seances_by_groupe(self, groupe_id, date_debut=None, date_fin=None):
        """Récupère les séances d'un groupe"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if date_debut and date_fin:
            cursor.execute('''
                SELECT * FROM seances 
                WHERE groupe_id = ? AND date BETWEEN ? AND ?
                ORDER BY date, heure_debut
            ''', (groupe_id, date_debut, date_fin))
        else:
            cursor.execute('''
                SELECT * FROM seances 
                WHERE groupe_id = ?
                ORDER BY date, heure_debut
            ''', (groupe_id,))
        
        seances = cursor.fetchall()
        conn.close()
        
        return seances

    def get_seances_by_enseignant(self, enseignant_id, date_debut=None, date_fin=None):
        """Récupère les séances d'un enseignant"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if date_debut and date_fin:
            cursor.execute('''
                SELECT * FROM seances 
                WHERE enseignant_id = ? AND date BETWEEN ? AND ?
                ORDER BY date, heure_debut
            ''', (enseignant_id, date_debut, date_fin))
        else:
            cursor.execute('''
                SELECT * FROM seances 
                WHERE enseignant_id = ?
                ORDER BY date, heure_debut
            ''', (enseignant_id,))
        
        seances = cursor.fetchall()
        conn.close()
        
        return seances

    def get_seances_by_salle(self, salle_id, date):
        """Récupère les séances d'une salle pour une date"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM seances 
            WHERE salle_id = ? AND date = ?
            ORDER BY heure_debut
        ''', (salle_id, date))
        
        seances = cursor.fetchall()
        conn.close()
        
        return seances

    def verifier_conflit_seance(self, date, heure_debut, heure_fin, 
                               salle_id=None, enseignant_id=None, groupe_id=None,
                               exclude_seance_id=None):
        """Vérifie s'il y a un conflit pour une séance — matches by day-of-week"""
        from datetime import datetime as dt
        conn = self.get_connection()
        cursor = conn.cursor()
        
        conflits = []
        
        # Find all seance dates that share the same day-of-week as `date`
        try:
            target_weekday = dt.strptime(date, "%Y-%m-%d").weekday()
        except (ValueError, TypeError):
            conn.close()
            return conflits
        
        cursor.execute("SELECT DISTINCT date FROM seances")
        all_dates = [row[0] for row in cursor.fetchall()]
        matching_dates = []
        for d in all_dates:
            try:
                if dt.strptime(d, "%Y-%m-%d").weekday() == target_weekday:
                    matching_dates.append(d)
            except (ValueError, TypeError):
                continue
        
        if not matching_dates:
            conn.close()
            return conflits
        
        placeholders = ",".join(["?"] * len(matching_dates))
        exclude_clause = "AND id != ?" if exclude_seance_id else ""
        exclude_params = [exclude_seance_id] if exclude_seance_id else []
        
        # Conflit salle
        if salle_id:
            cursor.execute(f'''
                SELECT * FROM seances 
                WHERE salle_id = ? AND date IN ({placeholders})
                {exclude_clause}
                AND ((heure_debut < ? AND heure_fin > ?) OR 
                     (heure_debut < ? AND heure_fin > ?) OR
                     (heure_debut >= ? AND heure_fin <= ?))
            ''', [salle_id] + matching_dates + exclude_params + [heure_fin, heure_debut, 
                  heure_fin, heure_debut, heure_debut, heure_fin])
            
            if cursor.fetchone():
                conflits.append("Salle déjà occupée par une séance régulière")
        
        # Conflit enseignant
        if enseignant_id:
            cursor.execute(f'''
                SELECT * FROM seances 
                WHERE enseignant_id = ? AND date IN ({placeholders})
                {exclude_clause}
                AND ((heure_debut < ? AND heure_fin > ?) OR 
                     (heure_debut < ? AND heure_fin > ?) OR
                     (heure_debut >= ? AND heure_fin <= ?))
            ''', [enseignant_id] + matching_dates + exclude_params + [heure_fin, heure_debut, 
                  heure_fin, heure_debut, heure_debut, heure_fin])
            
            if cursor.fetchone():
                conflits.append("Enseignant déjà occupé par une séance régulière")
        
        # Conflit groupe
        if groupe_id:
            cursor.execute(f'''
                SELECT * FROM seances 
                WHERE groupe_id = ? AND date IN ({placeholders})
                {exclude_clause}
                AND ((heure_debut < ? AND heure_fin > ?) OR 
                     (heure_debut < ? AND heure_fin > ?) OR
                     (heure_debut >= ? AND heure_fin <= ?))
            ''', [groupe_id] + matching_dates + exclude_params + [heure_fin, heure_debut, 
                  heure_fin, heure_debut, heure_debut, heure_fin])
            
            if cursor.fetchone():
                conflits.append("Groupe déjà occupé par une séance régulière")
        
        conn.close()
        
        return conflits
    
    def verifier_conflit_reservation(self, date, heure_debut, heure_fin, salle_id):
        """Vérifie s'il y a un conflit avec des réservations validées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, u.prenom, u.nom FROM reservations r
            LEFT JOIN utilisateurs u ON r.enseignant_id = u.id
            WHERE r.salle_id = ? AND r.date = ? AND r.statut = 'validee'
            AND ((r.heure_debut < ? AND r.heure_fin > ?) OR 
                 (r.heure_debut < ? AND r.heure_fin > ?) OR
                 (r.heure_debut >= ? AND r.heure_fin <= ?))
        ''', (salle_id, date, heure_fin, heure_debut, 
              heure_fin, heure_debut, heure_debut, heure_fin))
        
        conflits = cursor.fetchall()
        conn.close()
        return conflits
    
    def get_groupes_by_enseignant(self, enseignant_id):
        """Récupère les groupes qu'un enseignant enseigne (depuis les séances)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT g.* FROM groupes g
            JOIN seances s ON g.id = s.groupe_id
            WHERE s.enseignant_id = ?
            ORDER BY g.nom
        ''', (enseignant_id,))
        
        groupes = cursor.fetchall()
        conn.close()
        return groupes
    
    def get_modules_by_enseignant(self, enseignant_id):
        """Récupère les modules qu'un enseignant enseigne (depuis les séances)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT titre FROM seances
            WHERE enseignant_id = ?
            ORDER BY titre
        ''', (enseignant_id,))
        
        modules = [row[0] for row in cursor.fetchall()]
        conn.close()
        return modules
    
    # ═══════════════════════════════════════════════════════════
    # MÉTHODES CRUD - RÉSERVATIONS
    # ═══════════════════════════════════════════════════════════

    def supprimer_reservations_expirees(self):
        """Remove approved reservations whose date has passed (auto-cleanup)"""
        from datetime import datetime as dt
        today = dt.now().strftime("%Y-%m-%d")
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reservations WHERE date < ? AND statut = 'validee'", (today,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def ajouter_reservation(self, enseignant_id, salle_id, date, heure_debut, 
                           heure_fin, motif="", groupe_id=None):
        """Crée une demande de réservation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reservations (enseignant_id, salle_id, groupe_id, date, heure_debut,
                                     heure_fin, motif)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (enseignant_id, salle_id, groupe_id, date, heure_debut, heure_fin, motif))
        
        conn.commit()
        reservation_id = cursor.lastrowid
        conn.close()
        
        return reservation_id

    def get_reservations_by_statut(self, statut="en_attente"):
        """Récupère les réservations par statut avec groupe_id"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, g.nom as groupe_nom 
            FROM reservations r
            LEFT JOIN groupes g ON r.groupe_id = g.id
            WHERE r.statut = ?
            ORDER BY r.date_demande DESC
        ''', (statut,))
        
        reservations = cursor.fetchall()
        conn.close()
        
        return reservations

    def get_reservations_by_enseignant(self, enseignant_id):
        """Récupère les réservations d'un enseignant"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.id, r.enseignant_id, s.nom as salle_nom, r.date, r.heure_debut, 
                   r.heure_fin, r.motif, r.statut, g.nom as groupe_nom, r.groupe_id
            FROM reservations r
            LEFT JOIN salles s ON r.salle_id = s.id
            LEFT JOIN groupes g ON r.groupe_id = g.id
            WHERE r.enseignant_id = ?
            ORDER BY r.date_demande DESC
        ''', (enseignant_id,))
        
        reservations = cursor.fetchall()
        conn.close()
        
        return reservations

    def modifier_statut_reservation(self, reservation_id, statut):
        """Modifie le statut d'une réservation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE reservations 
            SET statut = ?
            WHERE id = ?
        ''', (statut, reservation_id))
        
        conn.commit()
        conn.close()
        
        return True
    
    def valider_reservation(self, reservation_id):
        """
        Valide (accepte) une réservation.
        Utilisé par ServiceFacade pour approuver les demandes.
        """
        return self.modifier_statut_reservation(reservation_id, 'validee')
    
    def refuser_reservation(self, reservation_id, motif_rejet=None):
        """
        Refuse (rejette) une réservation avec un motif optionnel.
        Utilisé par ServiceFacade pour rejeter les demandes.
        """
        if motif_rejet:
            return self.modifier_reservation_avec_motif(reservation_id, 'rejetee', motif_rejet)
        else:
            return self.modifier_statut_reservation(reservation_id, 'rejetee')
    
    # ═══════════════════════════════════════════════════════════
    # HISTORIQUE IMPORTS
    # ═══════════════════════════════════════════════════════════
    
    def ajouter_historique_import(self, type_import, nb_lignes, fichier_nom, admin_id):
        """Enregistre un import dans l'historique"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO historique_imports (type_import, nb_lignes, fichier_nom, admin_id)
            VALUES (?, ?, ?, ?)
        ''', (type_import, nb_lignes, fichier_nom, admin_id))
        
        conn.commit()
        conn.close()
        
        return True
    
    # ═══════════════════════════════════════════════════════════
    # MÉTHODES CRUD - DISPONIBILITÉS (INDISPONIBILITÉS ENSEIGNANTS)
    # ═══════════════════════════════════════════════════════════
    
    def ajouter_disponibilite(self, enseignant_id, date_debut, date_fin, motif=""):
        """
        Ajoute une indisponibilité pour un enseignant
        
        Args:
            enseignant_id: ID de l'enseignant
            date_debut: Date de début au format YYYY-MM-DD
            date_fin: Date de fin au format YYYY-MM-DD
            motif: Raison de l'indisponibilité
        
        Returns:
            int: ID de la disponibilité créée
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO disponibilites (enseignant_id, date_debut, date_fin, motif)
            VALUES (?, ?, ?, ?)
        ''', (enseignant_id, date_debut, date_fin, motif))
        
        conn.commit()
        dispo_id = cursor.lastrowid
        conn.close()
        
        return dispo_id
    
    def get_disponibilites_by_enseignant(self, enseignant_id):
        """
        Récupère les indisponibilités d'un enseignant
        
        Args:
            enseignant_id: ID de l'enseignant
        
        Returns:
            list: Liste des indisponibilités
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM disponibilites 
            WHERE enseignant_id = ?
            ORDER BY date_debut DESC
        ''', (enseignant_id,))
        
        disponibilites = cursor.fetchall()
        conn.close()
        
        return disponibilites
    
    def supprimer_disponibilite(self, dispo_id):
        """
        Supprime une indisponibilité
        
        Args:
            dispo_id: ID de la disponibilité
        
        Returns:
            bool: True si succès
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM disponibilites WHERE id = ?', (dispo_id,))
        nb_supprime = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return nb_supprime > 0
    
    def verifier_indisponibilite_enseignant(self, enseignant_id, date):
        """
        Vérifie si un enseignant est indisponible à une date donnée
        
        Args:
            enseignant_id: ID de l'enseignant
            date: Date au format YYYY-MM-DD
        
        Returns:
            bool: True si indisponible
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM disponibilites 
            WHERE enseignant_id = ? AND date_debut <= ? AND date_fin >= ?
        ''', (enseignant_id, date, date))
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    # ═══════════════════════════════════════════════════════════
    # MÉTHODES UTILITAIRES - SÉANCES
    # ═══════════════════════════════════════════════════════════
    
    def get_toutes_seances(self):
        """Récupère toutes les séances"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM seances ORDER BY date, heure_debut')
        seances = cursor.fetchall()
        
        conn.close()
        return seances
    
    def get_seances_by_date(self, date):
        """Récupère les séances pour une date donnée"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM seances 
            WHERE date = ?
            ORDER BY heure_debut
        ''', (date,))
        
        seances = cursor.fetchall()
        conn.close()
        
        return seances
    
    def supprimer_seance(self, seance_id):
        """Supprime une séance par son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM seances WHERE id = ?', (seance_id,))
        nb_supprime = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return nb_supprime > 0
    
    def get_toutes_reservations(self):
        """Récupère toutes les réservations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM reservations ORDER BY date_demande DESC')
        reservations = cursor.fetchall()
        
        conn.close()
        return reservations
    
    def get_salle_by_id(self, salle_id):
        """Récupère une salle par son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM salles WHERE id = ?', (salle_id,))
        salle = cursor.fetchone()
        
        conn.close()
        return salle
    
    def get_groupe_by_id(self, groupe_id):
        """Récupère un groupe par son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM groupes WHERE id = ?', (groupe_id,))
        groupe = cursor.fetchone()
        
        conn.close()
        return groupe
    
    def get_filiere_by_id(self, filiere_id):
        """Récupère une filière par son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM filieres WHERE id = ?', (filiere_id,))
        filiere = cursor.fetchone()
        
        conn.close()
        return filiere
    
    # ═══════════════════════════════════════════════════════════
    # MÉTHODES CRUD - NOTIFICATIONS
    # ═══════════════════════════════════════════════════════════
    
    def ajouter_notification(self, destinataire_id, type_notification, titre, message, seance_id=None):
        """Ajoute une notification pour un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Valider que le destinataire existe
            cursor.execute('SELECT id FROM utilisateurs WHERE id = ?', (destinataire_id,))
            if not cursor.fetchone():
                print(f"⚠️ Destinataire {destinataire_id} inexistant - notification ignorée")
                return None
            
            cursor.execute('''
                INSERT INTO notifications (destinataire_id, type_notification, titre, message, seance_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (destinataire_id, type_notification, titre, message, seance_id))
            
            conn.commit()
            notif_id = cursor.lastrowid
            return notif_id
        except Exception as e:
            print(f"❌ Erreur notification: {e}")
            return None
        finally:
            conn.close()
    
    def get_notifications_utilisateur(self, user_id, non_lues_seulement=False):
        """Récupère les notifications d'un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if non_lues_seulement:
            cursor.execute('''
                SELECT * FROM notifications 
                WHERE destinataire_id = ? AND lue = 0
                ORDER BY date_creation DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT * FROM notifications 
                WHERE destinataire_id = ?
                ORDER BY date_creation DESC
            ''', (user_id,))
        
        notifications = cursor.fetchall()
        conn.close()
        return notifications
    
    def marquer_notification_lue(self, notif_id):
        """Marque une notification comme lue"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE notifications SET lue = 1 WHERE id = ?', (notif_id,))
        conn.commit()
        nb_modif = cursor.rowcount
        conn.close()
        
        return nb_modif > 0
    
    def marquer_toutes_notifications_lues(self, user_id):
        """Marque toutes les notifications d'un utilisateur comme lues"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE notifications SET lue = 1 WHERE destinataire_id = ? AND lue = 0', (user_id,))
        conn.commit()
        nb_modif = cursor.rowcount
        conn.close()
        
        return nb_modif
    
    def get_nb_notifications_non_lues(self, user_id):
        """Compte le nombre de notifications non lues"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM notifications 
            WHERE destinataire_id = ? AND lue = 0
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    
    def envoyer_notification_groupe(self, groupe_id, type_notification, titre, message, seance_id=None):
        """Envoie une notification à tous les étudiants d'un groupe"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Récupérer tous les étudiants du groupe
        cursor.execute('''
            SELECT id FROM utilisateurs 
            WHERE groupe_id = ? AND type_user = 'etudiant'
        ''', (groupe_id,))
        
        etudiants = cursor.fetchall()
        nb_envois = 0
        nb_erreurs = 0
        
        for etudiant in etudiants:
            try:
                cursor.execute('''
                    INSERT INTO notifications (destinataire_id, type_notification, titre, message, seance_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (etudiant[0], type_notification, titre, message, seance_id))
                nb_envois += 1
            except Exception as e:
                nb_erreurs += 1
                # Log error but continue sending to other students
                print(f"⚠️ Erreur notification étudiant {etudiant[0]}: {e}")
        
        if nb_erreurs > 0:
            print(f"ℹ️ Notifications groupe: {nb_envois} envoyées, {nb_erreurs} erreurs")
        
        conn.commit()
        conn.close()
        return nb_envois
    
    def envoyer_notification_admins(self, type_notification, titre, message, seance_id=None):
        """Envoie une notification à tous les administrateurs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Récupérer tous les admins
        cursor.execute("SELECT id FROM utilisateurs WHERE type_user = 'admin'")
        admins = cursor.fetchall()
        nb_envois = 0
        nb_erreurs = 0
        
        for admin in admins:
            try:
                cursor.execute('''
                    INSERT INTO notifications (destinataire_id, type_notification, titre, message, seance_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (admin[0], type_notification, titre, message, seance_id))
                nb_envois += 1
            except Exception as e:
                nb_erreurs += 1
                print(f"⚠️ Erreur notification admin {admin[0]}: {e}")
        
        if nb_erreurs > 0:
            print(f"ℹ️ Notifications admins: {nb_envois} envoyées, {nb_erreurs} erreurs")
        
        conn.commit()
        conn.close()
        return nb_envois
    
    # ═══════════════════════════════════════════════════════════
    # MÉTHODES CRUD - RATTRAPAGES
    # ═══════════════════════════════════════════════════════════
    
    def ajouter_rattrapage(self, enseignant_id, groupe_id, salle_id, date, heure_debut, 
                           heure_fin, motif=None, seance_originale_id=None):
        """Ajoute une séance de rattrapage et verrouille la salle"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO rattrapages (enseignant_id, groupe_id, salle_id, date, 
                                        heure_debut, heure_fin, motif, seance_originale_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (enseignant_id, groupe_id, salle_id, date, heure_debut, heure_fin, 
                  motif, seance_originale_id))
            
            conn.commit()
            rattrapage_id = cursor.lastrowid
            return rattrapage_id
        except Exception as e:
            print(f"❌ Erreur rattrapage: {e}")
            return None
        finally:
            conn.close()
    
    def get_rattrapages_groupe(self, groupe_id):
        """Récupère tous les rattrapages d'un groupe"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM rattrapages 
            WHERE groupe_id = ? AND statut = 'confirmé'
            ORDER BY date, heure_debut
        ''', (groupe_id,))
        
        rattrapages = cursor.fetchall()
        conn.close()
        return rattrapages
    
    def get_rattrapages_enseignant(self, enseignant_id):
        """Récupère tous les rattrapages d'un enseignant"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM rattrapages 
            WHERE enseignant_id = ? AND statut = 'confirmé'
            ORDER BY date, heure_debut
        ''', (enseignant_id,))
        
        rattrapages = cursor.fetchall()
        conn.close()
        return rattrapages
    
    def annuler_rattrapage(self, rattrapage_id):
        """Annule un rattrapage (libère la salle)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE rattrapages SET statut = 'annulé' WHERE id = ?
        ''', (rattrapage_id,))
        
        conn.commit()
        nb_modif = cursor.rowcount
        conn.close()
        return nb_modif > 0
    
    def verifier_salle_occupee_rattrapage(self, salle_id, date, heure_debut, heure_fin):
        """Vérifie si une salle est occupée par un rattrapage"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM rattrapages 
            WHERE salle_id = ? AND date = ? AND statut = 'confirmé'
            AND NOT (heure_fin <= ? OR heure_debut >= ?)
        ''', (salle_id, date, heure_debut, heure_fin))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] > 0
    
    def get_seances_enseignant_periode(self, enseignant_id, date_debut, date_fin):
        """Récupère toutes les séances d'un enseignant sur une période"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM seances 
            WHERE enseignant_id = ? AND date >= ? AND date <= ?
            ORDER BY date, heure_debut
        ''', (enseignant_id, date_debut, date_fin))
        
        seances = cursor.fetchall()
        conn.close()
        return seances
    
    def liberer_seances_enseignant(self, enseignant_id, date_debut, date_fin):
        """
        Libère (supprime) toutes les séances d'un enseignant sur une période.
        Retourne la liste des séances supprimées pour notification.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # D'abord récupérer les séances pour les notifier
        cursor.execute('''
            SELECT * FROM seances 
            WHERE enseignant_id = ? AND date >= ? AND date <= ?
        ''', (enseignant_id, date_debut, date_fin))
        
        seances_a_supprimer = cursor.fetchall()
        
        # Supprimer les séances
        cursor.execute('''
            DELETE FROM seances 
            WHERE enseignant_id = ? AND date >= ? AND date <= ?
        ''', (enseignant_id, date_debut, date_fin))
        
        conn.commit()
        nb_supprime = cursor.rowcount
        conn.close()
        
        return seances_a_supprimer, nb_supprime
    
    def get_etudiants_groupe(self, groupe_id):
        """Récupère tous les étudiants d'un groupe"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM utilisateurs 
            WHERE groupe_id = ? AND type_user = 'etudiant'
        ''', (groupe_id,))
        
        etudiants = cursor.fetchall()
        conn.close()
        return etudiants
    
    # ═══════════════════════════════════════════════════════════
    # MÉTHODES MODULES (Contrainte spécialité/département)
    # ═══════════════════════════════════════════════════════════
    
    def ajouter_module(self, code, nom, departement, filiere_id=None, 
                       volume_cours=0, volume_td=0, volume_tp=0):
        """Ajoute un module avec son département"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO modules (code, nom, departement, filiere_id, 
                                    volume_cours, volume_td, volume_tp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (code, nom, departement, filiere_id, volume_cours, volume_td, volume_tp))
            
            conn.commit()
            module_id = cursor.lastrowid
            return module_id
        except sqlite3.IntegrityError:
            print(f"❌ Module {code} existe déjà")
            return None
        finally:
            conn.close()
    
    def get_modules_by_departement(self, departement):
        """Récupère les modules d'un département"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM modules 
            WHERE departement = ?
            ORDER BY nom
        ''', (departement,))
        
        modules = cursor.fetchall()
        conn.close()
        return modules
    
    def get_enseignants_by_specialite(self, specialite):
        """
        Récupère les enseignants d'une spécialité/département.
        Utilise une correspondance insensible à la casse et flexible.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Try exact match first (case-insensitive)
        cursor.execute('''
            SELECT * FROM utilisateurs 
            WHERE type_user = 'enseignant' AND LOWER(specialite) = LOWER(?)
        ''', (specialite,))
        
        enseignants = cursor.fetchall()
        
        # If no exact match, try LIKE match
        if not enseignants:
            cursor.execute('''
                SELECT * FROM utilisateurs 
                WHERE type_user = 'enseignant' AND LOWER(specialite) LIKE LOWER(?)
            ''', (f'%{specialite}%',))
            enseignants = cursor.fetchall()
        
        conn.close()
        return enseignants
    
    def valider_enseignant_module(self, enseignant_id, module_departement):
        """
        Vérifie si un enseignant peut enseigner un module basé sur sa spécialité.
        Retourne (is_valid, enseignant_specialite)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT specialite FROM utilisateurs 
            WHERE id = ? AND type_user = 'enseignant'
        ''', (enseignant_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False, None
        
        enseignant_specialite = result[0]
        
        # Si pas de spécialité définie, autoriser (fallback)
        if not enseignant_specialite or not module_departement:
            return True, enseignant_specialite
        
        # Vérification stricte: spécialité doit correspondre au département
        # On utilise une correspondance flexible (contient)
        specialite_lower = enseignant_specialite.lower()
        departement_lower = module_departement.lower()
        
        # Correspondances connues
        CORRESPONDANCES = {
            'informatique': ['informatique', 'génie informatique', 'gi', 'smi', 'info'],
            'mathématiques': ['mathématiques', 'math', 'statistiques', 'sma'],
            'physique': ['physique', 'génie physique', 'smp'],
            'chimie': ['chimie', 'génie des procédés', 'smc'],
            'biologie': ['biologie', 'biotechnologies', 'svt'],
            'géologie': ['géologie', 'géosciences', 'stu'],
            'génie électrique': ['électrique', 'électronique', 'génie électrique'],
            'génie mécanique': ['mécanique', 'génie mécanique', 'industriel'],
            'génie civil': ['civil', 'génie civil', 'btp'],
        }
        
        for dept_key, aliases in CORRESPONDANCES.items():
            if any(alias in departement_lower for alias in aliases):
                if any(alias in specialite_lower for alias in aliases):
                    return True, enseignant_specialite
        
        # Si pas de correspondance trouvée mais contient le même mot
        if departement_lower in specialite_lower or specialite_lower in departement_lower:
            return True, enseignant_specialite
        
        return False, enseignant_specialite
    
    def get_enseignants_by_groupe(self, groupe_id):
        """
        Récupère les enseignants qui peuvent enseigner à un groupe donné.
        Filtre par la spécialité correspondant à la filière du groupe.
        
        Args:
            groupe_id: ID du groupe
        
        Returns:
            Liste des enseignants avec spécialité correspondante
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Récupérer la filière du groupe
        cursor.execute('''
            SELECT f.nom, f.niveau 
            FROM groupes g
            JOIN filieres f ON g.filiere_id = f.id
            WHERE g.id = ?
        ''', (groupe_id,))
        
        filiere = cursor.fetchone()
        if not filiere:
            conn.close()
            return []
        
        filiere_nom = filiere[0]
        
        # 2. Extraire le département/domaine de la filière using class constant
        filiere_lower = filiere_nom.lower()
        departement = None
        
        for key, dept in self.FILIERE_TO_DEPT.items():
            if key in filiere_lower:
                departement = dept
                break
        
        # 3. Récupérer les enseignants qui enseignent déjà ce groupe
        cursor.execute('''
            SELECT DISTINCT u.* 
            FROM utilisateurs u
            JOIN seances s ON u.id = s.enseignant_id
            WHERE u.type_user = 'enseignant' AND s.groupe_id = ?
        ''', (groupe_id,))
        
        enseignants_groupe = cursor.fetchall()
        
        # 4. Si on a un département, récupérer aussi les enseignants de cette spécialité
        if departement:
            cursor.execute('''
                SELECT * FROM utilisateurs 
                WHERE type_user = 'enseignant' 
                AND (LOWER(specialite) LIKE ? OR LOWER(specialite) LIKE ?)
            ''', (f'%{departement}%', f'%{filiere_lower}%'))
            
            enseignants_dept = cursor.fetchall()
            
            # Combiner les deux listes sans doublons
            seen_ids = {e[0] for e in enseignants_groupe}
            for e in enseignants_dept:
                if e[0] not in seen_ids:
                    enseignants_groupe.append(e)
                    seen_ids.add(e[0])
        
        conn.close()
        return enseignants_groupe
    
    def get_enseignants_by_filiere(self, filiere_id):
        """
        Récupère les enseignants qui peuvent enseigner dans une filière donnée.
        
        Args:
            filiere_id: ID de la filière
        
        Returns:
            Liste des enseignants avec spécialité correspondante
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Récupérer la filière
        cursor.execute('SELECT nom FROM filieres WHERE id = ?', (filiere_id,))
        filiere = cursor.fetchone()
        if not filiere:
            conn.close()
            return []
        
        filiere_nom = filiere[0].lower()
        
        # Récupérer les enseignants qui enseignent déjà dans cette filière
        cursor.execute('''
            SELECT DISTINCT u.* 
            FROM utilisateurs u
            JOIN seances s ON u.id = s.enseignant_id
            JOIN groupes g ON s.groupe_id = g.id
            WHERE u.type_user = 'enseignant' AND g.filiere_id = ?
        ''', (filiere_id,))
        
        enseignants = cursor.fetchall()
        
        # Aussi chercher par spécialité
        cursor.execute('''
            SELECT * FROM utilisateurs 
            WHERE type_user = 'enseignant' 
            AND LOWER(specialite) LIKE ?
        ''', (f'%{filiere_nom}%',))
        
        enseignants_spec = cursor.fetchall()
        
        # Combiner sans doublons
        seen_ids = {e[0] for e in enseignants}
        for e in enseignants_spec:
            if e[0] not in seen_ids:
                enseignants.append(e)
                seen_ids.add(e[0])
        
        conn.close()
        return enseignants
    
    def get_groupes_by_enseignant(self, enseignant_id):
        """
        Récupère les groupes qu'un enseignant enseigne.
        Utile pour filtrer les groupes lors d'une réservation.
        
        Args:
            enseignant_id: ID de l'enseignant
        
        Returns:
            Liste des groupes enseignés par le professeur
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Récupérer les groupes via les séances existantes
        cursor.execute('''
            SELECT DISTINCT g.* 
            FROM groupes g
            JOIN seances s ON g.id = s.groupe_id
            WHERE s.enseignant_id = ?
            ORDER BY g.nom
        ''', (enseignant_id,))
        
        groupes = cursor.fetchall()
        conn.close()
        return groupes
    
    # ═══════════════════════════════════════════════════════════
    # MÉTHODES RÉSERVATIONS AVANCÉES (Workflow Admin Approval)
    # ═══════════════════════════════════════════════════════════
    
    def creer_demande_reservation(self, enseignant_id, salle_id, groupe_id, date, 
                                  heure_debut, heure_fin, type_demande, motif=""):
        """
        Crée une demande de réservation avec statut 'en_attente'
        Type: 'rattrapage' ou 'reprogrammation'
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO rattrapages (enseignant_id, groupe_id, salle_id, date, 
                                        heure_debut, heure_fin, motif, statut)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'en_attente')
            ''', (enseignant_id, groupe_id, salle_id, date, heure_debut, heure_fin, motif))
            
            conn.commit()
            demande_id = cursor.lastrowid
            return demande_id
        except Exception as e:
            print(f"❌ Erreur création demande: {e}")
            return None
        finally:
            conn.close()
    
    def get_demandes_en_attente(self):
        """Récupère toutes les demandes en attente d'approbation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, u.nom, u.prenom, s.nom as salle_nom, g.nom as groupe_nom
            FROM rattrapages r
            JOIN utilisateurs u ON r.enseignant_id = u.id
            JOIN salles s ON r.salle_id = s.id
            JOIN groupes g ON r.groupe_id = g.id
            WHERE r.statut = 'en_attente'
            ORDER BY r.date_creation DESC
        ''')
        
        demandes = cursor.fetchall()
        conn.close()
        return demandes
    
    def approuver_demande(self, demande_id):
        """
        Approuve une demande de réservation.
        Change le statut en 'confirmé' (la salle est maintenant verrouillée)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE rattrapages 
            SET statut = 'confirmé'
            WHERE id = ?
        ''', (demande_id,))
        
        # Récupérer les infos pour notification
        cursor.execute('SELECT * FROM rattrapages WHERE id = ?', (demande_id,))
        demande = cursor.fetchone()
        
        conn.commit()
        conn.close()
        return demande
    
    def rejeter_demande(self, demande_id, motif_rejet):
        """
        Rejette une demande de réservation avec un motif obligatoire.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE rattrapages 
            SET statut = 'rejete', motif_rejet = ?
            WHERE id = ?
        ''', (motif_rejet, demande_id))
        
        # Récupérer les infos pour notification
        cursor.execute('SELECT * FROM rattrapages WHERE id = ?', (demande_id,))
        demande = cursor.fetchone()
        
        conn.commit()
        conn.close()
        return demande
    
    def get_demande_by_id(self, demande_id):
        """Récupère une demande par son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, u.nom, u.prenom, s.nom as salle_nom, g.nom as groupe_nom
            FROM rattrapages r
            JOIN utilisateurs u ON r.enseignant_id = u.id
            JOIN salles s ON r.salle_id = s.id
            JOIN groupes g ON r.groupe_id = g.id
            WHERE r.id = ?
        ''', (demande_id,))
        
        demande = cursor.fetchone()
        conn.close()
        return demande
    
    def get_reservation_by_id(self, reservation_id):
        """Récupère une réservation par son ID avec infos jointes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, u.nom, u.prenom, s.nom as salle_nom
            FROM reservations r
            JOIN utilisateurs u ON r.enseignant_id = u.id
            JOIN salles s ON r.salle_id = s.id
            WHERE r.id = ?
        ''', (reservation_id,))
        
        reservation = cursor.fetchone()
        conn.close()
        return reservation
    
    def modifier_reservation_avec_motif(self, reservation_id, statut, motif_rejet=None):
        """Modifie le statut d'une réservation avec motif de rejet optionnel"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Ajouter colonne motif_rejet si elle n'existe pas
        try:
            cursor.execute('ALTER TABLE reservations ADD COLUMN motif_rejet TEXT')
        except:
            pass  # Colonne existe déjà
        
        if motif_rejet:
            cursor.execute('''
                UPDATE reservations 
                SET statut = ?, motif_rejet = ?
                WHERE id = ?
            ''', (statut, motif_rejet, reservation_id))
        else:
            cursor.execute('''
                UPDATE reservations 
                SET statut = ?
                WHERE id = ?
            ''', (statut, reservation_id))
        
        conn.commit()
        conn.close()
        return True