# 📚 Système de Gestion d'Emploi du Temps - FST Tanger

**Projet académique - Année 2025/2026**

---

## 🚀 GUIDE DE DÉMARRAGE RAPIDE

### Prérequis
- **Python 3.10+** installé
- **pip** (gestionnaire de packages Python)

### Installation en 3 étapes

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Initialiser la base de données avec les données de test
python init_data.py

# 3. Lancer l'application
python main.py
```

---

## 🔐 IDENTIFIANTS DE CONNEXION

### Administrateur
| Email | Mot de passe |
|-------|--------------|
| `admin@fstt.ac.ma` | `admin123` |

### Enseignants (60 professeurs)
| Email | Mot de passe |
|-------|--------------|
| `mohammed.alami1@uae.ac.ma` | `prof123` |
| `fatima.bennani1@uae.ac.ma` | `prof123` |
| `ahmed.tazi1@uae.ac.ma` | `prof123` |
| *(tous les autres profs)* | `prof123` |

### Étudiants (1300 étudiants)
| Email | Mot de passe |
|-------|--------------|
| `mohammed.bennani1@etu.uae.ac.ma` | `etudiant123` |
| `fatima.alami2@etu.uae.ac.ma` | `etudiant123` |
| *(tous les autres étudiants)* | `etudiant123` |

---

## 📖 UTILISATION DE L'APPLICATION

### 1️⃣ En tant qu'ADMINISTRATEUR

1. **Se connecter** avec `admin@fstt.ac.ma` / `admin123`
2. **Importer les données** (si pas déjà fait):
   - Aller dans "Générer Emploi" 
   - Cliquer sur "Importer les Salles" → sélectionner `templates_csv/salles.csv`
   - Cliquer sur "Importer Groupes" → sélectionner `templates_csv/groupes.csv`
   - Cliquer sur "Importer Enseignants" → sélectionner `templates_csv/enseignants.csv`
   - Cliquer sur "Importer Étudiants" → sélectionner `templates_csv/etudiants.csv`
3. **Générer l'emploi du temps**:
   - Cliquer sur "Lancer la Génération de l'Emploi du Temps"
   - Attendre la fin de la génération
4. **Gérer les réservations** dans l'onglet "Réservations"
   - Voir les demandes en attente
   - Accepter ou rejeter les demandes
   - Les étudiants sont automatiquement notifiés
5. **Voir les notifications** dans l'onglet "Notifications"

### 2️⃣ En tant qu'ENSEIGNANT

1. **Se connecter** avec un email prof (ex: `mohammed.alami1@uae.ac.ma` / `prof123`)
2. **Consulter son emploi du temps** dans "Emploi du Temps"
   - Affiche: Module, Salle (📍), Groupe (👥), Type de séance
3. **Télécharger** en PDF, Excel ou PNG avec les boutons
4. **Réserver une salle** dans "Réserver une séance"
5. **Voir ses réservations** dans "Mes Réservations"
   - Badge rouge indique les nouvelles réponses de l'admin
   - Statut: En attente / Acceptée / Rejetée
6. **Signaler une indisponibilité** dans "Indisponibilités"

### 3️⃣ En tant qu'ÉTUDIANT

1. **Se connecter** avec un email étudiant (ex: `mohammed.bennani1@etu.uae.ac.ma` / `etudiant123`)
2. **Consulter l'emploi du temps** de son groupe
   - Affiche: Module, Salle, Enseignant, Type de séance
3. **Télécharger** en PDF, Excel ou PNG
4. **Chercher des salles libres** dans "Salles Libres"
5. **Voir les mises à jour** dans "Mises à jour"
   - Notifications de séances approuvées
   - Rattrapages confirmés
   - Badge rouge indique les nouvelles notifications

---

## ✨ FONCTIONNALITÉS PRINCIPALES

### Génération d'Emploi du Temps

| Contrainte | Valeur | Description |
|------------|--------|-------------|
| Heures/semaine (Enseignant) | 12h max | Maximum d'heures d'enseignement par semaine |
| Heures/jour (Enseignant) | 6h max | Maximum par jour |
| Heures/semaine (Étudiant) | 18h max | 6 Cours + 6 TD × 1.5h |
| Heures/jour (Étudiant) | 4.5h max | Charge quotidienne maximale |

### Contraintes Respectées

- ✅ **Spécialité enseignant**: Les professeurs enseignent uniquement les matières de leur spécialité
- ✅ **Filière étudiant**: Les étudiants étudient uniquement les matières de leur filière
- ✅ **Pas de conflits**: Pas de chevauchement de salles, professeurs ou groupes
- ✅ **Diversité**: Sélection aléatoire des enseignants pour la variété
- ✅ **Appariement Cours/TD**: Le même enseignant pour un Cours et son TD

### Système de Notifications

- **Enseignants**: Notification quand l'admin répond à leur demande de réservation
- **Étudiants**: Notification quand une séance est confirmée pour leur groupe
- **Badge rouge**: Indique les notifications non lues
- **Marquage automatique**: Les notifications sont marquées comme lues quand la page est consultée

---

## 📂 STRUCTURE DU PROJET

```
PROJET_EMPLOI_DU_TEMPS/
├── main.py                    # Point d'entrée de l'application
├── config.py                  # Configuration globale (filières, matières)
├── configUI.py                # Configuration interface (couleurs, fenêtres)
├── requirements.txt           # Dépendances Python
├── README.md                  # Ce fichier
│
├── src/
│   ├── database.py            # Gestion base de données SQLite
│   ├── import_manager.py      # Import CSV
│   ├── models.py              # Classes POO (Utilisateur, Salle, Groupe...)
│   ├── gestionnaire.py        # Logique métier (Rattrapage, Absences)
│   ├── services_notification.py # Service de notifications
│   ├── services_audio.py      # Service Text-to-Speech
│   │
│   ├── ui/                    # Interfaces utilisateur
│   │   ├── styles.py          # Styles CSS professionnels
│   │   ├── login_window.py    # Fenêtre de connexion
│   │   ├── admin_window.py    # Interface administrateur + Charts
│   │   ├── enseignant_window.py # Interface enseignant
│   │   └── etudiant_window.py # Interface étudiant
│   │
│   └── logic/                 # Logique de génération
│       ├── schedule_generator.py    # Générateur d'emploi du temps
│       ├── conflict_detector.py     # Détection de conflits
│       ├── constraint_validator.py  # Validation des contraintes
│       ├── room_availability_service.py # Disponibilité des salles
│       ├── csv_import_service.py    # Import CSV
│       ├── time_utils.py            # Utilitaires temporels
│       ├── unavailability_service.py # Gestion indisponibilités
│       └── timetable_export_service.py  # Export PDF/Excel/PNG
│
├── data/
│   └── emploi_du_temps.db     # Base de données SQLite
│
├── templates_csv/             # Fichiers CSV de données
│   ├── salles.csv             # 77 salles FSTT
│   ├── groupes.csv            # 39 groupes
│   ├── enseignants.csv        # 60 enseignants
│   └── etudiants.csv          # 1300 étudiants
│
├── assets/                    # Ressources (images, icônes)
│   └── images/
│
└── exports/                   # Fichiers exportés (PDF, Excel, PNG)
    ├── audio/
    ├── csv/
    ├── excel/
    └── pdf/
```

---

## 📊 DONNÉES DE TEST

| Entité | Nombre | Description |
|--------|--------|-------------|
| Filières | 13 | Génie Civil, Informatique, Mathématiques, etc. |
| Groupes | 39 | GP_GCI, Gr_GCI_1, GP_INFO, etc. |
| Salles | 77 | Amphithéâtres, Salles de cours, Laboratoires |
| Enseignants | 60 | Professeurs avec spécialités variées |
| Étudiants | 1300 | Répartis dans les groupes |

### Filières Disponibles

| Niveau | Filières |
|--------|----------|
| **Licence** | Génie Civil, Informatique, Mathématiques, Physique, Chimie |
| **Master** | Génie Mécanique, Électronique, Management, Sciences de l'Environnement |
| **Ingénieur** | Génie Informatique, Génie Industriel, Génie Électrique, Génie des Procédés |

---

## 🔧 DÉPANNAGE

### L'application ne démarre pas
```bash
# Vérifier que PyQt6 est installé
pip install PyQt6

# Réinstaller toutes les dépendances
pip install -r requirements.txt --force-reinstall
```

### Base de données vide
```bash
# Supprimer et réinitialiser la base de données
rm -f data/emploi_du_temps.db
python init_data.py
```

### Pas d'emploi du temps visible
1. Connectez-vous en tant qu'admin
2. Allez dans "Générer Emploi"
3. Cliquez sur "Lancer la Génération"

### Erreur "Module not found"
```bash
# S'assurer d'être dans le bon répertoire
cd /chemin/vers/le/projet
python main.py
```

### Pas assez de sessions générées
Si vous voyez des avertissements lors de la génération:
- Vérifiez que les enseignants ont des spécialités correspondant aux matières
- Augmentez le nombre d'enseignants par spécialité si nécessaire

---

## ✅ FONCTIONNALITÉS IMPLÉMENTÉES

### Core
- [x] Interface de connexion moderne (Admin, Prof, Étudiant)
- [x] Import CSV massif (salles, groupes, enseignants, étudiants)
- [x] Base de données SQLite avec schéma complet
- [x] Gestion des utilisateurs avec rôles

### Emploi du Temps
- [x] Génération automatique d'emploi du temps
- [x] Contraintes de spécialité enseignant (professeurs = matières de leur domaine)
- [x] Contraintes de filière étudiant (étudiants = matières de leur filière)
- [x] Limite d'heures hebdomadaires (18h étudiants, 12h enseignants)
- [x] Limite d'heures quotidiennes (4.5h étudiants, 6h enseignants)
- [x] Détection des conflits (salles, profs, groupes)
- [x] Appariement Cours/TD (même prof pour les deux)

### Affichage
- [x] Emploi du temps personnalisé par groupe (étudiant)
- [x] Emploi du temps personnalisé par prof (enseignant)
- [x] Affichage détaillé: Module, Salle, Groupe, Type de séance
- [x] Code couleur par type de séance (Cours=bleu, TD=vert, TP=jaune)

### Réservations
- [x] Demande de réservation de salle par les enseignants
- [x] Approbation/Rejet par l'admin avec motif
- [x] Notification des étudiants quand admin accepte
- [x] Page "Mes Réservations" pour les enseignants

### Notifications
- [x] Système de notifications complet
- [x] Badge rouge pour notifications non lues
- [x] Marquage automatique comme lues
- [x] Page "Mises à jour" pour les étudiants

### Exports
- [x] Export PDF de l'emploi du temps
- [x] Export Excel (.xlsx)
- [x] Export PNG (image)
- [x] Service audio (Text-to-Speech)

### Interface
- [x] Design moderne avec glassmorphism
- [x] Sidebar avec navigation
- [x] Charts modernes (DonutChart, StatCards)
- [x] Styles CSS professionnels
- [x] Couleurs FSTT (Bleu #0066CC, Jaune #FFC107)

---

## 🎨 COMPOSANTS UI

### Charts (admin_window.py)
- **ModernDonutChart**: Graphique circulaire avec dégradés
- **ModernStatCard**: Cartes statistiques avec icônes
- **SimpleBarChart**: Graphique à barres

### Styles (styles.py)
- Styles Login (formulaire, boutons, messages)
- Styles Sidebar (navigation, boutons, header)
- Styles Tables (tableaux de données)
- Styles Boutons (primary, secondary, success, danger)
- Styles Cards (dashboard)
- Styles Charts (container, title)
- Styles Emploi du temps (cellules par type)

---

## 👥 Équipe de Développement

Projet académique - FST Tanger - 2025/2026

---

**Pour toute question, consultez le fichier `Mini projet (1).pdf` qui contient le cahier des charges complet.**
