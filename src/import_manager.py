# src/import_manager.py
import csv
import os
from src.database import Database
from config import COLONNES_ETUDIANTS, COLONNES_ENSEIGNANTS, COLONNES_SALLES, COLONNES_GROUPES

# Default filière level for auto-created filières during CSV import
# L3 (Licence 3) is the most common level at FSTT for undergraduate programs
DEFAULT_FILIERE_NIVEAU = "L3"

class ImportManager:
    """Classe pour gérer les imports massifs CSV de la FSTT"""
    
    def __init__(self):
        self.db = Database()
    
    def parse_csv(self, fichier_path):
        """Lit un fichier CSV et retourne une liste de dictionnaires"""
        try:
            with open(fichier_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            print(f"❌ Erreur lors de la lecture du fichier : {e}")
            return None

    def valider_colonnes(self, donnees, colonnes_requises):
        """Vérifie si le CSV possède bien toutes les colonnes nécessaires"""
        if not donnees: 
            return False
        colonnes_fichier = donnees[0].keys()
        manquantes = [col for col in colonnes_requises if col not in colonnes_fichier]
        if manquantes:
            print(f"❌ Colonnes manquantes : {', '.join(manquantes)}")
            return False
        return True

    def import_salles(self, fichier_path):
        """Importe les salles — upsert by name to preserve IDs for existing seances"""
        donnees = self.parse_csv(fichier_path)
        
        if not donnees:
            return False
            
        if not self.valider_colonnes(donnees, COLONNES_SALLES):
            print("❌ Erreur : Colonnes manquantes dans le fichier Salles.")
            return False

        # 1. Sauvegarde de sécurité
        self.db.sauvegarder_bdd()
        
        # 2. Build set of names from CSV
        csv_names = set(ligne['nom'].strip() for ligne in donnees)
        
        # 3. Get existing salles mapped by name
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom FROM salles")
        existing = {row[1]: row[0] for row in cursor.fetchall()}
        
        # 4. Delete salles not present in new CSV
        for name, sid in existing.items():
            if name not in csv_names:
                cursor.execute("DELETE FROM salles WHERE id = ?", (sid,))
        
        # 5. Upsert: update existing by name, insert new
        succes = 0
        for ligne in donnees:
            nom = ligne['nom'].strip()
            capacite = int(ligne['capacite'])
            type_salle = ligne['type_salle']
            equipements = ligne.get('equipements', '')
            
            if nom in existing:
                cursor.execute(
                    "UPDATE salles SET capacite=?, type_salle=?, equipements=? WHERE id=?",
                    (capacite, type_salle, equipements, existing[nom])
                )
            else:
                cursor.execute(
                    "INSERT INTO salles (nom, capacite, type_salle, equipements) VALUES (?,?,?,?)",
                    (nom, capacite, type_salle, equipements)
                )
            succes += 1
        
        conn.commit()
        conn.close()
        
        # 6. Historique
        self.db.ajouter_historique_import("Salles", succes, os.path.basename(fichier_path), 1)
        print(f"✅ Import réussi : {succes} salles ajoutées.")
        return True

    def import_enseignants(self, fichier_path, mode='remplacer'):
        """
        Importe les enseignants — upsert by email to preserve IDs
        
        Args:
            fichier_path: Chemin du CSV
            mode: 'remplacer' (upsert + remove missing) ou 'fusionner' (upsert only)
        """
        donnees = self.parse_csv(fichier_path)
        
        if not donnees:
            return False
            
        if not self.valider_colonnes(donnees, COLONNES_ENSEIGNANTS):
            print("❌ Erreur : Colonnes manquantes dans le fichier Enseignants.")
            return False

        self.db.sauvegarder_bdd()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get existing enseignants mapped by email
        cursor.execute("SELECT id, email FROM utilisateurs WHERE type_user = 'enseignant'")
        existing = {row[1]: row[0] for row in cursor.fetchall()}
        
        csv_emails = set(ligne['email'] for ligne in donnees)
        
        if mode == 'remplacer':
            # Delete enseignants not in new CSV
            for email, eid in existing.items():
                if email not in csv_emails:
                    cursor.execute("DELETE FROM utilisateurs WHERE id = ?", (eid,))
            print("🗑️  Anciennes données supprimées")
        else:
            print("➕ Mode fusion : ajout sans suppression")
        
        import hashlib
        succes = 0
        for ligne in donnees:
            email = ligne['email'].strip()
            duree_max = int(ligne.get('duree_max_jour', 480))
            pwd_hash = hashlib.sha256("prof123".encode()).hexdigest()
            
            if email in existing:
                # Update existing — preserve ID
                cursor.execute("""
                    UPDATE utilisateurs 
                    SET nom=?, prenom=?, specialite=?, duree_max_jour=?
                    WHERE id=?
                """, (ligne['nom'], ligne['prenom'], ligne['specialite'],
                      duree_max, existing[email]))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO utilisateurs 
                    (nom, prenom, email, mot_de_passe, type_user, specialite, groupe_id, duree_max_jour)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (ligne['nom'], ligne['prenom'], email, pwd_hash,
                      'enseignant', ligne['specialite'], None, duree_max))
            succes += 1
        
        conn.commit()
        conn.close()
            
        self.db.ajouter_historique_import("Enseignants", succes, os.path.basename(fichier_path), 1)
        print(f"✅ Import réussi : {succes} enseignants ajoutés.")
        return True

    def import_groupes(self, fichier_path):
        """Importe les groupes — upsert by (nom, filiere) to preserve IDs for existing seances"""
        donnees = self.parse_csv(fichier_path)
        
        if not donnees:
            return False
            
        if not self.valider_colonnes(donnees, COLONNES_GROUPES):
            print("❌ Erreur : Colonnes manquantes dans le fichier Groupes.")
            return False

        self.db.sauvegarder_bdd()
        
        succes = 0
        erreurs = 0
        filieres_creees = 0
        
        # 1. Resolve filières first, build list of (nom, effectif, filiere_id) 
        csv_groups = []
        for ligne in donnees:
            filiere_nom = ligne['filiere'].strip()
            filiere = self.db.get_filiere_by_nom(filiere_nom)
            
            if not filiere:
                filiere_id = self.db.ajouter_filiere(filiere_nom, DEFAULT_FILIERE_NIVEAU)
                if filiere_id:
                    print(f"✅ Filière créée automatiquement : '{filiere_nom}' (Niveau: {DEFAULT_FILIERE_NIVEAU})")
                    filieres_creees += 1
                else:
                    print(f"⚠️ Impossible de créer la filière '{filiere_nom}' pour le groupe '{ligne['nom']}'")
                    erreurs += 1
                    continue
            else:
                filiere_id = filiere[0]
            
            csv_groups.append((ligne['nom'].strip(), int(ligne['effectif']), filiere_id))
        
        # 2. Build set of (nom, filiere_id) from CSV for deletion check
        csv_keys = set((nom, fid) for nom, _, fid in csv_groups)
        
        # 3. Get existing groups mapped by (nom, filiere_id)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, filiere_id FROM groupes")
        existing = {(row[1], row[2]): row[0] for row in cursor.fetchall()}
        
        # 4. Delete groups not present in new CSV
        for key, gid in existing.items():
            if key not in csv_keys:
                cursor.execute("DELETE FROM groupes WHERE id = ?", (gid,))
        
        # 5. Upsert: update existing, insert new
        for nom, effectif, filiere_id in csv_groups:
            key = (nom, filiere_id)
            if key in existing:
                cursor.execute(
                    "UPDATE groupes SET effectif=? WHERE id=?",
                    (effectif, existing[key])
                )
            else:
                cursor.execute(
                    "INSERT INTO groupes (nom, effectif, filiere_id) VALUES (?,?,?)",
                    (nom, effectif, filiere_id)
                )
            succes += 1
        
        conn.commit()
        conn.close()
        
        self.db.ajouter_historique_import("Groupes", succes, os.path.basename(fichier_path), 1)
        
        if filieres_creees > 0:
            print(f"📚 {filieres_creees} filières créées automatiquement.")
        
        if erreurs > 0:
            print(f"⚠️ Import partiel : {succes} groupes ajoutés, {erreurs} erreurs.")
        else:
            print(f"✅ Import réussi : {succes} groupes ajoutés.")
        
        return True

    def import_etudiants(self, fichier_path):
        """Importe les étudiants — upsert by email to preserve IDs"""
        donnees = self.parse_csv(fichier_path)
        
        if not donnees:
            return False
            
        if not self.valider_colonnes(donnees, COLONNES_ETUDIANTS):
            print("❌ Erreur : Colonnes manquantes dans le fichier Étudiants.")
            return False

        self.db.sauvegarder_bdd()
        
        succes = 0
        erreurs = 0
        
        # 1. Build set of emails from CSV
        csv_emails = set(ligne['email'].strip() for ligne in donnees)
        
        # 2. Get existing students mapped by email
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email FROM utilisateurs WHERE type_user = 'etudiant'")
        existing = {row[1]: row[0] for row in cursor.fetchall()}
        
        # 3. Delete students not present in new CSV
        for email, uid in existing.items():
            if email not in csv_emails:
                cursor.execute("DELETE FROM utilisateurs WHERE id = ?", (uid,))
        
        # 4. Upsert: update existing, insert new
        for ligne in donnees:
            email = ligne['email'].strip()
            nom = ligne['nom']
            prenom = ligne['prenom']
            
            # Resolve groupe
            groupe = self.db.get_groupe_by_nom(ligne['groupe'].strip())
            if not groupe:
                print(f"⚠️ Groupe '{ligne['groupe']}' introuvable pour {nom} {prenom}")
                erreurs += 1
                continue
            groupe_id = groupe[0]
            
            if email in existing:
                cursor.execute(
                    "UPDATE utilisateurs SET nom=?, prenom=?, groupe_id=? WHERE id=?",
                    (nom, prenom, groupe_id, existing[email])
                )
            else:
                hashed = self.db.hash_password("etudiant123")
                cursor.execute(
                    "INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, type_user, groupe_id) VALUES (?,?,?,?,?,?)",
                    (nom, prenom, email, hashed, "etudiant", groupe_id)
                )
            succes += 1
        
        conn.commit()
        conn.close()
        
        self.db.ajouter_historique_import("Étudiants", succes, os.path.basename(fichier_path), 1)
        
        if erreurs > 0:
            print(f"⚠️ Import partiel : {succes} étudiants ajoutés, {erreurs} erreurs.")
        else:
            print(f"✅ Import réussi : {succes} étudiants ajoutés.")
        
        return True

    def import_tous_fichiers(self, dossier_templates):
        """Importe automatiquement tous les CSV du dossier templates"""
        print("🚀 Lancement de l'import complet...")
        
        fichiers = {
            'salles.csv': self.import_salles,
            'enseignants.csv': self.import_enseignants,
            'groupes.csv': self.import_groupes,
            'etudiants.csv': self.import_etudiants
        }
        
        resultats = {}
        
        for nom_fichier, fonction_import in fichiers.items():
            chemin = os.path.join(dossier_templates, nom_fichier)
            
            if os.path.exists(chemin):
                print(f"\n📄 Import de {nom_fichier}...")
                resultats[nom_fichier] = fonction_import(chemin)
            else:
                print(f"⚠️ Fichier {nom_fichier} introuvable, ignoré.")
                resultats[nom_fichier] = False
        
        print("\n" + "="*50)
        print("📊 RÉSUMÉ DE L'IMPORT")
        print("="*50)
        for fichier, succes in resultats.items():
            statut = "✅ Réussi" if succes else "❌ Échoué"
            print(f"{fichier:20} : {statut}")
        
        return resultats