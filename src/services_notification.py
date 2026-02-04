# src/services_notification.py
"""
Service de gestion des notifications
Envoie des alertes automatiques aux utilisateurs (étudiants, enseignants, admins)
lors d'événements importants : rattrapages, annulations, modifications.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime


class NotificationService:
    """
    Service centralisé pour la gestion des notifications.
    Gère l'envoi de messages aux différents acteurs du système.
    """
    
    # Types de notifications
    TYPE_RATTRAPAGE = "rattrapage"
    TYPE_ABSENCE = "absence"
    TYPE_ANNULATION = "annulation"
    TYPE_INFO = "info"
    TYPE_ALERTE = "alerte"
    TYPE_RESERVATION = "reservation"  # New type for reservation status updates
    
    def __init__(self, db):
        """
        Initialise le service de notification
        
        Args:
            db: Instance de Database
        """
        self.db = db
    
    # ═══════════════════════════════════════════════════════════
    # NOTIFICATIONS INDIVIDUELLES
    # ═══════════════════════════════════════════════════════════
    
    def envoyer_notification(self, destinataire_id: int, type_notification: str,
                            titre: str, message: str, seance_id: int = None) -> Tuple[bool, str]:
        """
        Envoie une notification à un utilisateur spécifique
        
        Args:
            destinataire_id: ID de l'utilisateur destinataire
            type_notification: Type de notification (rattrapage, absence, etc.)
            titre: Titre de la notification
            message: Contenu du message
            seance_id: ID de la séance concernée (optionnel)
        
        Returns:
            Tuple (success, message)
        """
        try:
            notif_id = self.db.ajouter_notification(
                destinataire_id, type_notification, titre, message, seance_id
            )
            
            if notif_id:
                return True, f"Notification envoyée (ID: {notif_id})"
            else:
                return False, "Erreur lors de l'envoi de la notification"
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def get_notifications_utilisateur(self, user_id: int, non_lues_seulement: bool = False) -> List[Dict]:
        """
        Récupère les notifications d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            non_lues_seulement: Si True, retourne uniquement les non lues
        
        Returns:
            Liste de notifications formatées
        """
        notifications_raw = self.db.get_notifications_utilisateur(user_id, non_lues_seulement)
        
        notifications = []
        for notif in notifications_raw:
            notifications.append({
                'id': notif[0],
                'destinataire_id': notif[1],
                'type': notif[2],
                'titre': notif[3],
                'message': notif[4],
                'lue': bool(notif[5]),
                'date_creation': notif[6],
                'seance_id': notif[7]
            })
        
        return notifications
    
    def marquer_comme_lue(self, notif_id: int) -> bool:
        """Marque une notification comme lue"""
        return self.db.marquer_notification_lue(notif_id)
    
    def get_nb_non_lues(self, user_id: int) -> int:
        """Retourne le nombre de notifications non lues"""
        return self.db.get_nb_notifications_non_lues(user_id)
    
    # ═══════════════════════════════════════════════════════════
    # NOTIFICATIONS GROUPÉES
    # ═══════════════════════════════════════════════════════════
    
    def notifier_groupe(self, groupe_id: int, type_notification: str,
                       titre: str, message: str, seance_id: int = None) -> Tuple[int, str]:
        """
        Envoie une notification à tous les étudiants d'un groupe
        
        Args:
            groupe_id: ID du groupe
            type_notification: Type de notification
            titre: Titre
            message: Message
            seance_id: ID de la séance concernée
        
        Returns:
            Tuple (nombre d'envois, message de confirmation)
        """
        nb_envois = self.db.envoyer_notification_groupe(
            groupe_id, type_notification, titre, message, seance_id
        )
        
        return nb_envois, f"Notification envoyée à {nb_envois} étudiants du groupe"
    
    def notifier_admins(self, type_notification: str, titre: str, 
                       message: str, seance_id: int = None) -> Tuple[int, str]:
        """
        Envoie une notification à tous les administrateurs
        
        Args:
            type_notification: Type de notification
            titre: Titre
            message: Message
            seance_id: ID de la séance concernée
        
        Returns:
            Tuple (nombre d'envois, message de confirmation)
        """
        nb_envois = self.db.envoyer_notification_admins(
            type_notification, titre, message, seance_id
        )
        
        return nb_envois, f"Notification envoyée à {nb_envois} administrateurs"
    
    # ═══════════════════════════════════════════════════════════
    # NOTIFICATIONS SPÉCIALISÉES
    # ═══════════════════════════════════════════════════════════
    
    def notifier_rattrapage(self, groupe_id: int, enseignant_nom: str,
                           matiere: str, date: str, heure_debut: str,
                           heure_fin: str, salle_nom: str) -> Tuple[int, str]:
        """
        Notifie les étudiants d'un groupe d'une séance de rattrapage
        
        Args:
            groupe_id: ID du groupe
            enseignant_nom: Nom de l'enseignant
            matiere: Nom de la matière
            date: Date du rattrapage
            heure_debut: Heure de début
            heure_fin: Heure de fin
            salle_nom: Nom de la salle
        
        Returns:
            Tuple (nombre d'envois, message)
        """
        titre = f"📚 Séance de rattrapage - {matiere}"
        message = (
            f"Une séance de rattrapage a été programmée :\n\n"
            f"📖 Matière : {matiere}\n"
            f"👨‍🏫 Enseignant : {enseignant_nom}\n"
            f"📅 Date : {date}\n"
            f"⏰ Horaire : {heure_debut} - {heure_fin}\n"
            f"📍 Salle : {salle_nom}\n\n"
            f"Votre présence est obligatoire."
        )
        
        return self.notifier_groupe(groupe_id, self.TYPE_RATTRAPAGE, titre, message)
    
    def notifier_annulation_cours(self, groupe_id: int, enseignant_nom: str,
                                  matiere: str, date: str, heure_debut: str,
                                  motif: str = None) -> Tuple[int, str]:
        """
        Notifie les étudiants d'un groupe de l'annulation d'un cours
        
        Args:
            groupe_id: ID du groupe
            enseignant_nom: Nom de l'enseignant
            matiere: Nom de la matière
            date: Date du cours annulé
            heure_debut: Heure de début du cours
            motif: Motif de l'annulation (optionnel)
        
        Returns:
            Tuple (nombre d'envois, message)
        """
        titre = f"⚠️ Cours annulé - {matiere}"
        message = (
            f"Le cours suivant a été annulé :\n\n"
            f"📖 Matière : {matiere}\n"
            f"👨‍🏫 Enseignant : {enseignant_nom}\n"
            f"📅 Date : {date}\n"
            f"⏰ Heure prévue : {heure_debut}\n"
        )
        
        if motif:
            message += f"\n📝 Motif : {motif}"
        
        return self.notifier_groupe(groupe_id, self.TYPE_ANNULATION, titre, message)
    
    def notifier_absence_enseignant(self, enseignant_id: int, enseignant_nom: str,
                                    date_debut: str, date_fin: str, 
                                    seances_annulees: List[Dict]) -> Dict:
        """
        Gère la notification complète lors d'une absence d'enseignant :
        - Notifie tous les étudiants concernés
        - Notifie les administrateurs
        
        Args:
            enseignant_id: ID de l'enseignant
            enseignant_nom: Nom de l'enseignant
            date_debut: Date de début d'absence
            date_fin: Date de fin d'absence
            seances_annulees: Liste des séances annulées
        
        Returns:
            Dict avec statistiques des notifications
        """
        result = {
            'etudiants_notifies': 0,
            'admins_notifies': 0,
            'groupes_concernes': set(),
            'seances_annulees': len(seances_annulees)
        }
        
        # Notifier chaque groupe concerné par les séances annulées
        for seance in seances_annulees:
            groupe_id = seance[8] if isinstance(seance, tuple) else seance.get('groupe_id')
            titre_seance = seance[1] if isinstance(seance, tuple) else seance.get('titre')
            date_seance = seance[3] if isinstance(seance, tuple) else seance.get('date')
            heure_debut = seance[4] if isinstance(seance, tuple) else seance.get('heure_debut')
            
            if groupe_id and groupe_id not in result['groupes_concernes']:
                nb, _ = self.notifier_annulation_cours(
                    groupe_id, enseignant_nom, titre_seance, date_seance, heure_debut,
                    f"Absence de l'enseignant du {date_debut} au {date_fin}"
                )
                result['etudiants_notifies'] += nb
                result['groupes_concernes'].add(groupe_id)
        
        # Notifier les administrateurs
        titre_admin = f"🔔 Absence déclarée - {enseignant_nom}"
        message_admin = (
            f"L'enseignant {enseignant_nom} a déclaré une absence :\n\n"
            f"📅 Période : du {date_debut} au {date_fin}\n"
            f"🗑️ Séances annulées : {len(seances_annulees)}\n"
            f"👥 Groupes concernés : {len(result['groupes_concernes'])}\n\n"
            f"Les salles ont été automatiquement libérées."
        )
        
        nb_admins, _ = self.notifier_admins(self.TYPE_ABSENCE, titre_admin, message_admin)
        result['admins_notifies'] = nb_admins
        
        result['groupes_concernes'] = len(result['groupes_concernes'])
        return result
    
    def notifier_reservation_approuvee(self, enseignant_id: int, salle_nom: str,
                                        date: str, heure_debut: str, heure_fin: str,
                                        motif: str = None, groupe_id: int = None) -> Tuple[bool, str]:
        """
        Notifie un enseignant que sa réservation a été approuvée.
        Si groupe_id est fourni, notifie aussi les étudiants du groupe.
        
        Args:
            enseignant_id: ID de l'enseignant
            salle_nom: Nom de la salle réservée
            date: Date de la réservation
            heure_debut: Heure de début
            heure_fin: Heure de fin
            motif: Motif de la réservation (optionnel)
            groupe_id: ID du groupe concerné (optionnel, pour notifier les étudiants)
        
        Returns:
            Tuple (success, message)
        """
        titre = f"✅ Réservation approuvée - {salle_nom}"
        message = (
            f"Votre demande de réservation a été approuvée !\n\n"
            f"📍 Salle : {salle_nom}\n"
            f"📅 Date : {date}\n"
            f"⏰ Horaire : {heure_debut} - {heure_fin}\n"
        )
        
        if motif:
            message += f"📝 Motif : {motif}\n"
        
        message += "\nLa salle est maintenant réservée à votre nom."
        
        # Notify the teacher
        success, msg = self.envoyer_notification(
            enseignant_id, self.TYPE_RESERVATION, titre, message
        )
        
        # Also notify students if a groupe_id is provided
        if groupe_id:
            # Get teacher name for student notification
            enseignant = self.db.get_utilisateur_by_id(enseignant_id)
            enseignant_nom = f"{enseignant[2]} {enseignant[1]}" if enseignant else "Enseignant"
            
            titre_etudiant = f"📚 Séance programmée - {motif or 'Séance'}"
            message_etudiant = (
                f"Une séance a été programmée par votre enseignant !\n\n"
                f"👨‍🏫 Enseignant : {enseignant_nom}\n"
                f"📍 Salle : {salle_nom}\n"
                f"📅 Date : {date}\n"
                f"⏰ Horaire : {heure_debut} - {heure_fin}\n"
            )
            if motif:
                message_etudiant += f"📝 Type : {motif}\n"
            
            message_etudiant += "\nVotre présence est requise."
            
            nb_etudiants, _ = self.notifier_groupe(groupe_id, self.TYPE_INFO, titre_etudiant, message_etudiant)
            return success, f"{msg} + {nb_etudiants} étudiants notifiés"
        
        return success, msg
    
    def notifier_reservation_rejetee(self, enseignant_id: int, salle_nom: str,
                                      date: str, heure_debut: str, heure_fin: str,
                                      raison_rejet: str = None) -> Tuple[bool, str]:
        """
        Notifie un enseignant que sa réservation a été rejetée.
        Note: Les étudiants ne sont PAS notifiés des rejets (seul l'enseignant sait).
        
        Args:
            enseignant_id: ID de l'enseignant
            salle_nom: Nom de la salle demandée
            date: Date de la réservation
            heure_debut: Heure de début
            heure_fin: Heure de fin
            raison_rejet: Raison du rejet (optionnel)
        
        Returns:
            Tuple (success, message)
        """
        titre = f"❌ Réservation rejetée - {salle_nom}"
        message = (
            f"Votre demande de réservation a été rejetée.\n\n"
            f"📍 Salle : {salle_nom}\n"
            f"📅 Date : {date}\n"
            f"⏰ Horaire : {heure_debut} - {heure_fin}\n"
        )
        
        if raison_rejet:
            message += f"\n📝 Raison : {raison_rejet}"
        else:
            message += "\nVeuillez contacter l'administration pour plus d'informations."
        
        return self.envoyer_notification(
            enseignant_id, self.TYPE_RESERVATION, titre, message
        )
    
    # ═══════════════════════════════════════════════════════════
    # FORMATAGE DE L'EMPLOI DU TEMPS EN TEXTE
    # ═══════════════════════════════════════════════════════════
    
    def formater_emploi_du_temps_texte(self, seances: List, date: str = None) -> str:
        """
        Formate l'emploi du temps en texte lisible
        
        Args:
            seances: Liste des séances (tuples ou dicts)
            date: Date spécifique (optionnel, sinon groupe par date)
        
        Returns:
            Texte formaté de l'emploi du temps
        """
        if not seances:
            return "Aucune séance programmée."
        
        # Convertir en dicts si nécessaire
        seances_list = []
        for s in seances:
            if isinstance(s, tuple):
                seances_list.append({
                    'id': s[0],
                    'titre': s[1],
                    'type_seance': s[2],
                    'date': s[3],
                    'heure_debut': s[4],
                    'heure_fin': s[5],
                    'salle_id': s[6],
                    'enseignant_id': s[7],
                    'groupe_id': s[8]
                })
            else:
                seances_list.append(s)
        
        # Trier par date et heure
        seances_list.sort(key=lambda x: (x['date'], x['heure_debut']))
        
        # Grouper par date
        dates_dict = {}
        for s in seances_list:
            d = s['date']
            if d not in dates_dict:
                dates_dict[d] = []
            dates_dict[d].append(s)
        
        # Construire le texte
        texte_parts = []
        for date_key in sorted(dates_dict.keys()):
            seances_jour = dates_dict[date_key]
            
            # Convertir la date en format lisible
            try:
                date_obj = datetime.strptime(date_key, "%Y-%m-%d")
                jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
                jour_nom = jours[date_obj.weekday()]
                date_lisible = date_obj.strftime(f"{jour_nom} %d/%m/%Y")
            except ValueError:
                date_lisible = date_key
            
            texte_parts.append(f"\n📅 {date_lisible}")
            texte_parts.append("-" * 40)
            
            for seance in seances_jour:
                texte_parts.append(
                    f"  ⏰ {seance['heure_debut']} - {seance['heure_fin']}"
                )
                texte_parts.append(
                    f"     📖 {seance['titre']} ({seance['type_seance']})"
                )
        
        return "\n".join(texte_parts)
