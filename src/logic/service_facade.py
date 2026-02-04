# src/logic/service_facade.py
"""
Service Facade - Unified entry point for business logic.

This module implements the Facade design pattern to provide a simplified
interface to the scheduling system's complex subsystem of services.

Usage:
    facade = ServiceFacade(db)
    result = facade.create_seance(seance_data)
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
from src.database import Database

# Import des services et validateurs
from src.logic.constraint_validator import ConstraintValidator
from src.logic.reservation_validator import ReservationValidator
from src.logic.room_availability_service import RoomAvailabilityService
from src.logic.unavailability_service import UnavailabilityService
from src.logic.schedule_generator import ScheduleGenerator
from src.logic.conflict_detector import ConflictDetector
from src.logic.time_utils import TimeUtils
from src.services_notification import NotificationService


class ServiceFacade:
    """
    Unified entry point for business logic (Facade Design Pattern).
    
    The UI should ideally only interact with this class to avoid
    tight coupling with the underlying services.
    
    Services managed:
    - Session management (create, update, delete)
    - Reservation management (request, approve, reject)
    - Room availability
    - Teacher unavailability
    - Schedule generation
    - Conflict detection
    """
    
    def __init__(self, db: Database):
        """
        Initialize the facade with a database connection.
        
        Args:
            db: Database instance
        """
        self.db = db
        # Initialize sub-services
        self.unavailability_service = UnavailabilityService(db)
        self.room_service = RoomAvailabilityService(db)
        self.notification_service = NotificationService(db)
        self._generator = None  # Lazy initialization
    
    @property
    def generator(self) -> ScheduleGenerator:
        """Lazy initialization of schedule generator with current data."""
        if self._generator is None:
            self._refresh_generator()
        return self._generator
    
    def _refresh_generator(self) -> None:
        """Refresh the schedule generator with current database data."""
        existing_seances = self._get_seances_as_dicts()
        existing_reservations = self._get_reservations_as_dicts()
        self._generator = ScheduleGenerator(self.db, existing_seances, existing_reservations)
    
    def _get_seances_as_dicts(self) -> List[Dict]:
        """Get all sessions as dictionaries."""
        seances = self.db.get_toutes_seances() or []
        return [self._seance_to_dict(s) for s in seances]
    
    def _get_reservations_as_dicts(self) -> List[Dict]:
        """Get all reservations as dictionaries."""
        reservations = self.db.get_toutes_reservations() or []
        return [self._reservation_to_dict(r) for r in reservations]
    
    def _seance_to_dict(self, seance) -> Dict:
        """Convert a seance tuple/row to a dictionary."""
        if isinstance(seance, dict):
            return seance
        if isinstance(seance, tuple):
            return {
                'id': seance[0], 'titre': seance[1], 'type_seance': seance[2],
                'date': seance[3], 'heure_debut': seance[4], 'heure_fin': seance[5],
                'salle_id': seance[6], 'enseignant_id': seance[7], 'groupe_id': seance[8]
            }
        try:
            return dict(seance)
        except (TypeError, ValueError):
            return {}
    
    def _reservation_to_dict(self, reservation) -> Dict:
        """Convert a reservation tuple/row to a dictionary."""
        if isinstance(reservation, dict):
            return reservation
        if isinstance(reservation, tuple):
            return {
                'id': reservation[0], 'enseignant_id': reservation[1],
                'salle_id': reservation[2], 'date': reservation[3],
                'heure_debut': reservation[4], 'heure_fin': reservation[5],
                'statut': reservation[6], 'motif': reservation[7] if len(reservation) > 7 else ''
            }
        try:
            return dict(reservation)
        except (TypeError, ValueError):
            return {}
    
    def _salle_to_dict(self, salle) -> Dict:
        """Convert a salle tuple/row to a dictionary."""
        if isinstance(salle, dict):
            return salle
        if isinstance(salle, tuple):
            return {
                'id': salle[0], 'nom': salle[1], 'capacite': salle[2],
                'type_salle': salle[3], 'equipements': salle[4] or ''
            }
        try:
            return dict(salle)
        except (TypeError, ValueError):
            return {}
    
    def _groupe_to_dict(self, groupe) -> Dict:
        """Convert a groupe tuple/row to a dictionary."""
        if isinstance(groupe, dict):
            return groupe
        if isinstance(groupe, tuple):
            return {
                'id': groupe[0], 'nom': groupe[1], 'effectif': groupe[2],
                'filiere_id': groupe[3] if len(groupe) > 3 else None
            }
        try:
            return dict(groupe)
        except (TypeError, ValueError):
            return {}
    
    # ═══════════════════════════════════════════════════════════════════
    # SESSION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    def create_seance(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Create a new session with full constraint validation.
        
        Args:
            data: Session data dictionary with keys:
                - titre: Session title
                - type_seance: Type (Cours, TD, TP, Examen)
                - date: Date (YYYY-MM-DD)
                - heure_debut: Start time (HH:MM)
                - heure_fin: End time (HH:MM)
                - salle_id: Room ID
                - enseignant_id: Teacher ID
                - groupe_id: Group ID
                
        Returns:
            Tuple of (success, list of messages)
        """
        # 1. Get necessary data
        all_seances = self._get_seances_as_dicts()
        salles_raw = self.db.get_toutes_salles() or []
        groupes_raw = self.db.get_tous_groupes() or []
        
        salles = [self._salle_to_dict(s) for s in salles_raw]
        groupes = [self._groupe_to_dict(g) for g in groupes_raw]
        
        # 2. Validate (conflicts, capacity, time...)
        validator = ConstraintValidator(all_seances, salles=salles, groupes=groupes)
        is_valid, errors = validator.validate_seance(
            date=data.get('date', ''),
            heure_debut=data.get('heure_debut', ''),
            heure_fin=data.get('heure_fin', ''),
            salle_id=data.get('salle_id'),
            enseignant_id=data.get('enseignant_id'),
            groupe_id=data.get('groupe_id')
        )
        
        if not is_valid:
            return False, errors
            
        # 3. Save if validation passes
        try:
            self.db.ajouter_seance(**data)
            self._refresh_generator()  # Refresh generator after adding session
            return True, ["✅ Séance créée avec succès"]
        except Exception as e:
            return False, [f"❌ Erreur: {str(e)}"]
    
    def update_seance(self, seance_id: int, data: Dict) -> Tuple[bool, List[str]]:
        """
        Update an existing session with validation.
        
        Args:
            seance_id: ID of the session to update
            data: Updated session data
            
        Returns:
            Tuple of (success, list of messages)
        """
        # Get current data
        all_seances = self._get_seances_as_dicts()
        salles_raw = self.db.get_toutes_salles() or []
        groupes_raw = self.db.get_tous_groupes() or []
        
        salles = [self._salle_to_dict(s) for s in salles_raw]
        groupes = [self._groupe_to_dict(g) for g in groupes_raw]
        
        # Validate, excluding the session being updated
        validator = ConstraintValidator(all_seances, salles=salles, groupes=groupes)
        is_valid, errors = validator.validate_seance(
            date=data.get('date', ''),
            heure_debut=data.get('heure_debut', ''),
            heure_fin=data.get('heure_fin', ''),
            salle_id=data.get('salle_id'),
            enseignant_id=data.get('enseignant_id'),
            groupe_id=data.get('groupe_id'),
            exclude_seance_id=seance_id
        )
        
        if not is_valid:
            return False, errors
        
        try:
            self.db.modifier_seance(seance_id, **data)
            self._refresh_generator()
            return True, ["✅ Séance modifiée avec succès"]
        except Exception as e:
            return False, [f"❌ Erreur: {str(e)}"]
    
    def delete_seance(self, seance_id: int) -> Tuple[bool, str]:
        """
        Delete a session.
        
        Args:
            seance_id: ID of the session to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            self.db.supprimer_seance(seance_id)
            self._refresh_generator()
            return True, "✅ Séance supprimée avec succès"
        except Exception as e:
            return False, f"❌ Erreur: {str(e)}"
    
    # ═══════════════════════════════════════════════════════════════════
    # RESERVATION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    def request_reservation(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Submit a room reservation request.
        
        Args:
            data: Reservation data dictionary with keys:
                - enseignant_id: Teacher ID
                - salle_id: Room ID
                - date: Date (YYYY-MM-DD)
                - heure_debut: Start time (HH:MM)
                - heure_fin: End time (HH:MM)
                - motif: Reason for reservation (optional)
                
        Returns:
            Tuple of (success, list of messages)
        """
        all_seances = self._get_seances_as_dicts()
        existing_res = self._get_reservations_as_dicts()
        
        validator = ReservationValidator(all_seances, existing_res)
        is_valid, errors = validator.validate_reservation_request(
            enseignant_id=data.get('enseignant_id'),
            salle_id=data.get('salle_id'),
            date=data.get('date', ''),
            heure_debut=data.get('heure_debut', ''),
            heure_fin=data.get('heure_fin', '')
        )
        
        if is_valid:
            try:
                self.db.ajouter_reservation(**data)
                return True, ["✅ Demande envoyée à l'administration"]
            except Exception as e:
                return False, [f"❌ Erreur: {str(e)}"]
        return False, errors
    
    def approve_reservation(self, reservation_id: int) -> Tuple[bool, str]:
        """
        Approve a pending reservation request and notify the teacher.
        
        Args:
            reservation_id: ID of the reservation to approve
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get reservation details before approving (with salle_nom from join)
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.id, r.enseignant_id, r.salle_id, r.date, r.heure_debut, 
                       r.heure_fin, r.statut, r.motif, s.nom as salle_nom 
                FROM reservations r
                JOIN salles s ON r.salle_id = s.id
                WHERE r.id = ?
            ''', (reservation_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return False, "❌ Réservation introuvable"
            
            # Convert to dictionary for clarity
            reservation = {
                'id': row[0],
                'enseignant_id': row[1],
                'salle_id': row[2],
                'date': row[3],
                'heure_debut': row[4],
                'heure_fin': row[5],
                'statut': row[6],
                'motif': row[7] or '',
                'salle_nom': row[8]
            }
            
            # Approve the reservation
            self.db.valider_reservation(reservation_id)
            self._refresh_generator()
            
            # Send notification to the teacher
            self.notification_service.notifier_reservation_approuvee(
                reservation['enseignant_id'],
                reservation['salle_nom'],
                reservation['date'],
                reservation['heure_debut'],
                reservation['heure_fin'],
                reservation['motif']
            )
            
            return True, "✅ Réservation validée et notification envoyée"
        except Exception as e:
            return False, f"❌ Erreur: {str(e)}"
    
    def reject_reservation(self, reservation_id: int, reason: str = "") -> Tuple[bool, str]:
        """
        Reject a pending reservation request and notify the teacher.
        
        Args:
            reservation_id: ID of the reservation to reject
            reason: Reason for rejection (optional)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get reservation details before rejecting (with salle_nom from join)
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.id, r.enseignant_id, r.salle_id, r.date, r.heure_debut, 
                       r.heure_fin, r.statut, r.motif, s.nom as salle_nom 
                FROM reservations r
                JOIN salles s ON r.salle_id = s.id
                WHERE r.id = ?
            ''', (reservation_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return False, "❌ Réservation introuvable"
            
            # Convert to dictionary for clarity
            reservation = {
                'id': row[0],
                'enseignant_id': row[1],
                'salle_id': row[2],
                'date': row[3],
                'heure_debut': row[4],
                'heure_fin': row[5],
                'statut': row[6],
                'motif': row[7] or '',
                'salle_nom': row[8]
            }
            
            # Reject the reservation
            self.db.refuser_reservation(reservation_id, reason)
            
            # Send notification to the teacher
            self.notification_service.notifier_reservation_rejetee(
                reservation['enseignant_id'],
                reservation['salle_nom'],
                reservation['date'],
                reservation['heure_debut'],
                reservation['heure_fin'],
                reason
            )
            
            return True, "✅ Réservation refusée et notification envoyée"
        except Exception as e:
            return False, f"❌ Erreur: {str(e)}"
    
    # ═══════════════════════════════════════════════════════════════════
    # ROOM & AVAILABILITY MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    def add_prof_unavailability(self, prof_id: int, date: str, 
                                start: str, end: str, motif: str = "") -> Tuple[bool, str]:
        """
        Add an unavailability period for a teacher.
        
        Args:
            prof_id: Teacher ID
            date: Date (YYYY-MM-DD)
            start: Start time (HH:MM)
            end: End time (HH:MM)
            motif: Reason (optional)
            
        Returns:
            Tuple of (success, message)
        """
        return self.unavailability_service.add_unavailability(prof_id, date, start, end, motif)

    def find_free_rooms(self, date: str, start: str, end: str, 
                       capacity: int = 0, type_salle: Optional[str] = None) -> List[Dict]:
        """
        Find available rooms for a given time slot.
        
        Args:
            date: Date (YYYY-MM-DD)
            start: Start time (HH:MM)
            end: End time (HH:MM)
            capacity: Minimum capacity required
            type_salle: Room type filter (optional)
            
        Returns:
            List of available room dictionaries
        """
        return self.room_service.find_available_rooms(date, start, end, capacity, type_salle)
    
    def get_room_schedule(self, salle_id: int, date: str) -> List[Tuple[str, str]]:
        """
        Get occupied time slots for a room on a specific date.
        
        Args:
            salle_id: Room ID
            date: Date (YYYY-MM-DD)
            
        Returns:
            List of (start_time, end_time) tuples
        """
        all_seances = self._get_seances_as_dicts()
        detector = ConflictDetector(all_seances)
        return detector.get_room_availability(salle_id, date)
    
    def get_teacher_schedule(self, enseignant_id: int, date: str) -> List[Tuple[str, str]]:
        """
        Get occupied time slots for a teacher on a specific date.
        
        Args:
            enseignant_id: Teacher ID
            date: Date (YYYY-MM-DD)
            
        Returns:
            List of (start_time, end_time) tuples
        """
        all_seances = self._get_seances_as_dicts()
        detector = ConflictDetector(all_seances)
        return detector.get_teacher_availability(enseignant_id, date)
    
    def get_group_schedule(self, groupe_id: int, date: str) -> List[Tuple[str, str]]:
        """
        Get occupied time slots for a group on a specific date.
        
        Args:
            groupe_id: Group ID
            date: Date (YYYY-MM-DD)
            
        Returns:
            List of (start_time, end_time) tuples
        """
        all_seances = self._get_seances_as_dicts()
        detector = ConflictDetector(all_seances)
        return detector.get_group_availability(groupe_id, date)
    
    # ═══════════════════════════════════════════════════════════════════
    # SCHEDULE GENERATION
    # ═══════════════════════════════════════════════════════════════════
    
    def generate_timetable(self, courses: List[Dict], start_date: str = None) -> Dict:
        """
        Generate a timetable for a list of courses.
        
        Args:
            courses: List of course dictionaries, each with:
                - groupe_id: Group ID
                - matiere: Subject name
                - type_seance: Session type
                - duree_heures: Duration in hours
                - enseignant_id: Teacher ID
                - nb_seances_semaine: Sessions per week
                - module_departement: Department (optional)
            start_date: Week start date (YYYY-MM-DD), defaults to next Monday
                
        Returns:
            Dictionary with 'success', 'generated_sessions', 'errors'
        """
        if start_date is None:
            start_date = TimeUtils.get_next_monday()
        
        # Refresh generator with latest data
        self._refresh_generator()
        
        result = {
            'success': True,
            'generated_sessions': [],
            'errors': [],
            'warnings': []
        }
        
        teacher_weekly_hours = {}
        teacher_daily_hours = {}
        
        for course in courses:
            try:
                sessions = self.generator.generate_schedule_for_group(
                    groupe_id=course.get('groupe_id'),
                    matiere=course.get('matiere', 'Cours'),
                    type_seance=course.get('type_seance', 'Cours'),
                    duree_heures=course.get('duree_heures', 1.5),
                    enseignant_id=course.get('enseignant_id'),
                    nb_seances_semaine=course.get('nb_seances_semaine', 1),
                    semaine_debut=start_date,
                    teacher_weekly_hours=teacher_weekly_hours,
                    teacher_daily_hours=teacher_daily_hours,
                    module_departement=course.get('module_departement')
                )
                
                if sessions:
                    result['generated_sessions'].extend(sessions)
                else:
                    result['warnings'].append(
                        f"Aucune session générée pour {course.get('matiere', 'cours inconnu')}"
                    )
            except Exception as e:
                result['errors'].append(f"Erreur pour {course.get('matiere', 'cours')}: {str(e)}")
        
        result['success'] = len(result['errors']) == 0
        return result
    
    def save_generated_sessions(self, sessions: List[Dict]) -> Tuple[bool, str]:
        """
        Save generated sessions to the database.
        
        Args:
            sessions: List of session dictionaries to save
            
        Returns:
            Tuple of (success, message)
        """
        saved_count = 0
        errors = []
        
        for session in sessions:
            try:
                self.db.ajouter_seance(**session)
                saved_count += 1
            except Exception as e:
                errors.append(str(e))
        
        self._refresh_generator()
        
        if errors:
            return False, f"Sauvegardé {saved_count}/{len(sessions)}. Erreurs: {', '.join(errors)}"
        return True, f"✅ {saved_count} séances sauvegardées avec succès"
    
    # ═══════════════════════════════════════════════════════════════════
    # CONFLICT DETECTION
    # ═══════════════════════════════════════════════════════════════════
    
    def check_conflicts(self, date: str, heure_debut: str, heure_fin: str,
                       salle_id: Optional[int] = None,
                       enseignant_id: Optional[int] = None,
                       groupe_id: Optional[int] = None,
                       exclude_seance_id: Optional[int] = None) -> List[str]:
        """
        Check for scheduling conflicts.
        
        Args:
            date: Date (YYYY-MM-DD)
            heure_debut: Start time (HH:MM)
            heure_fin: End time (HH:MM)
            salle_id: Room ID (optional)
            enseignant_id: Teacher ID (optional)
            groupe_id: Group ID (optional)
            exclude_seance_id: Session ID to exclude (optional)
            
        Returns:
            List of conflict messages (empty if no conflicts)
        """
        all_seances = self._get_seances_as_dicts()
        detector = ConflictDetector(all_seances)
        return detector.detect_all_conflicts(
            date, heure_debut, heure_fin,
            salle_id=salle_id,
            enseignant_id=enseignant_id,
            groupe_id=groupe_id,
            exclude_seance_id=exclude_seance_id
        )
    
    # ═══════════════════════════════════════════════════════════════════
    # TEACHER-GROUP FILTERING
    # ═══════════════════════════════════════════════════════════════════
    
    def get_teachers_for_group(self, groupe_id: int) -> List[Dict]:
        """
        Get teachers who can teach a specific group.
        Filters by matching specialty/department.
        
        Args:
            groupe_id: Group ID
            
        Returns:
            List of teacher dictionaries
        """
        teachers_raw = self.db.get_enseignants_by_groupe(groupe_id)
        teachers = []
        for t in teachers_raw:
            if isinstance(t, tuple):
                teachers.append({
                    'id': t[0],
                    'nom': t[1],
                    'prenom': t[2],
                    'email': t[3],
                    'specialite': t[6] if len(t) > 6 else ''
                })
            else:
                teachers.append(t)
        return teachers
    
    def get_teachers_for_filiere(self, filiere_id: int) -> List[Dict]:
        """
        Get teachers who can teach in a specific filière.
        
        Args:
            filiere_id: Filière ID
            
        Returns:
            List of teacher dictionaries
        """
        teachers_raw = self.db.get_enseignants_by_filiere(filiere_id)
        teachers = []
        for t in teachers_raw:
            if isinstance(t, tuple):
                teachers.append({
                    'id': t[0],
                    'nom': t[1],
                    'prenom': t[2],
                    'email': t[3],
                    'specialite': t[6] if len(t) > 6 else ''
                })
            else:
                teachers.append(t)
        return teachers
    
    def get_groups_for_teacher(self, enseignant_id: int) -> List[Dict]:
        """
        Get groups taught by a specific teacher.
        Useful for filtering groups in reservation UI.
        
        Args:
            enseignant_id: Teacher ID
            
        Returns:
            List of group dictionaries
        """
        groups_raw = self.db.get_groupes_by_enseignant(enseignant_id)
        groups = []
        for g in groups_raw:
            if isinstance(g, tuple):
                groups.append({
                    'id': g[0],
                    'nom': g[1],
                    'effectif': g[2],
                    'filiere_id': g[3] if len(g) > 3 else None
                })
            else:
                groups.append(g)
        return groups
    
    # ═══════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════
    
    def get_statistics(self) -> Dict:
        """
        Get system statistics.
        
        Returns:
            Dictionary with counts of various entities
        """
        return {
            'nb_seances': len(self.db.get_toutes_seances() or []),
            'nb_salles': len(self.db.get_toutes_salles() or []),
            'nb_groupes': len(self.db.get_tous_groupes() or []),
            'nb_enseignants': len(self.db.get_tous_utilisateurs('enseignant') or []),
            'nb_etudiants': len(self.db.get_tous_utilisateurs('etudiant') or []),
            'nb_reservations_en_attente': len(self.db.get_reservations_by_statut('en_attente') or [])
        }