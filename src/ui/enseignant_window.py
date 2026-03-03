# src/ui/enseignant_window.py
"""
Fenêtre principale de l'enseignant - Modern SaaS Design
MERGED: Visuals from enseignant_window 10 + Full Logic + Notification Fix
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QStackedWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QComboBox, QDateEdit,
    QTextEdit, QMessageBox, QGridLayout,
    QGraphicsDropShadowEffect, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QColor

from configUI import WINDOW_CONFIG, COLORS, FST_LOGO_IMAGE
from src.services_notification import NotificationService
from src.ui.styles import (
    GLOBAL_STYLE, SIDEBAR_STYLE, SIDEBAR_BUTTON_STYLE, 
    SIDEBAR_USER_INFO_STYLE, CARD_STYLE, CARD_TITLE_STYLE,
    PRIMARY_BUTTON_STYLE, SECONDARY_BUTTON_STYLE,
    TABLE_STYLE, INPUT_STYLE, DANGER_BUTTON_STYLE
)


class UserWrapper:
    def __init__(self, user_tuple):
        self.id = user_tuple[0]
        self.nom = user_tuple[1]
        self.prenom = user_tuple[2]
        self.email = user_tuple[3]

class EnseignantWindow(QWidget):
    logout_signal = pyqtSignal()

    def __init__(self, user, db):
        super().__init__()
        if isinstance(user, tuple):
            self.user = UserWrapper(user)
        else:
            self.user = user
            
        self.db = db
        self.notification_service = NotificationService(db)
        
        self.setWindowTitle("UniSchedule-Gestion d'emploi du Temps FSTT")
        self.setMinimumSize(1024, 768)
        self.showMaximized()
        self.setStyleSheet(GLOBAL_STYLE)
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.create_sidebar()
        self.create_content_area()
        self.switch_page("Schedule")
        self.update_reservation_badge()

    # ═══════════════════════════════════════════════════════════
    # BUSINESS LOGIC
    # ═══════════════════════════════════════════════════════════

    def load_schedule(self):
        """Load teacher's schedule"""
        self.schedule_table.clearContents()
        
        def get_row(time_str):
            if "08" in time_str or "09" in time_str: return 0
            if "10" in time_str or "11" in time_str: return 1
            if "12" in time_str or "13" in time_str: return 2
            if "14" in time_str or "15" in time_str: return 3
            if "16" in time_str or "17" in time_str: return 4
            return -1

        try:
            seances = self.db.get_seances_by_enseignant(self.user.id)
            for s in seances:
                date_str = s[3]
                qdate = QDate.fromString(date_str, "yyyy-MM-dd")
                day_idx = qdate.dayOfWeek() - 1
                
                if 0 <= day_idx <= 5:
                    row = get_row(s[4])
                    if row != -1:
                        module_name, session_type = s[1], s[2]
                        salle_name = "?"
                        if s[6]:
                            salle = self.db.get_salle_by_id(s[6])
                            if salle: salle_name = salle[1]
                        
                        groupe_name = "?"
                        if s[8]:
                            groupe = self.db.get_groupe_by_id(s[8])
                            if groupe: groupe_name = groupe[1]
                        
                        if session_type == "Cours": color = COLORS['primary']
                        elif session_type == "TD": color = COLORS['success']
                        else: color = COLORS['accent']
                        
                        txt = f"{module_name}\n📍 {salle_name}\n👥 {groupe_name}\n({session_type})"
                        self.set_course(self.schedule_table, row, day_idx, txt, color)
        except Exception as e:
            print(f"Schedule load error: {e}")

    def set_course(self, table, row, col, text, color):
        item = QLabel(text)
        item.setAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setStyleSheet(f"background-color: {color}; color: white; border-radius: 8px; margin: 2px; padding: 4px; font-weight: 600; font-size: 11px;")
        item.setWordWrap(True)
        table.setCellWidget(row, col, item)

    def _get_teacher_specialite(self):
        """Get the teacher's department/speciality from DB or from their taught groups"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT specialite FROM utilisateurs WHERE id = ?', (self.user.id,))
            result = cursor.fetchone()
            conn.close()
            if result and result[0]:
                # Map specialite to department using Database mapping
                spec = result[0].lower().strip()
                return self.db.FILIERE_TO_DEPT.get(spec, result[0])
        except:
            pass
        return None

    def _update_time_slots(self, date_edit, time_combo):
        """Update time slot combo based on selected date — Friday excludes 12:30-14:00"""
        all_slots = ["09:00 - 10:30", "10:45 - 12:15", "12:30 - 14:00", "14:15 - 15:45", "16:00 - 17:30"]
        selected_date = date_edit.date()
        day_of_week = selected_date.dayOfWeek()  # 5 = Friday
        
        current = time_combo.currentText()
        time_combo.clear()
        if day_of_week == 5:  # Friday — skip 12:30-14:00
            slots = [s for s in all_slots if s != "12:30 - 14:00"]
        else:
            slots = all_slots
        time_combo.addItems(slots)
        # Restore previous selection if still valid
        idx = time_combo.findText(current)
        if idx >= 0:
            time_combo.setCurrentIndex(idx)

    def _update_salle_combo(self, combo, session_type):
        """Update a salle combo box based on session type with specialty filtering"""
        combo.clear()
        spec = self._get_teacher_specialite()
        salles = self.db.get_salles_for_session_type(session_type, enseignant_specialite=spec)
        for s in salles:
            combo.addItem(s[1])

    def _on_res_type_changed(self, new_type):
        """When reservation type changes, update available rooms"""
        if hasattr(self, 'new_res_salle'):
            self._update_salle_combo(self.new_res_salle, new_type)

    def submit_reservation(self):
        """Submit reservation logic with conflict checking"""
        date = self.new_res_date.date().toString("yyyy-MM-dd")
        
        # Get time from combo (e.g. "09:00 - 10:30")
        time_text = self.new_res_time.currentText()
        try:
            parts = time_text.split(" - ")
            heure_debut = parts[0].strip()
            heure_fin = parts[1].strip()
        except (IndexError, AttributeError):
            QMessageBox.warning(self, "Erreur", "Créneau horaire invalide")
            return
        
        # Get text from combos
        groupe_nom = self.new_res_groupe.currentText()
        salle_nom = self.new_res_salle.currentText()
        subject = self.new_res_subject.currentText()
        res_type = self.new_res_type.currentText()
        
        if not subject.strip():
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner une matière")
            return
        
        # Resolve IDs
        groupes = self.db.get_tous_groupes()
        groupe_id = next((g[0] for g in groupes if g[1] == groupe_nom), None)
        
        salles = self.db.get_toutes_salles()
        salle_id = next((s[0] for s in salles if s[1] == salle_nom), None)
        
        if not salle_id:
            QMessageBox.warning(self, "Erreur", "Salle non trouvée")
            return
        
        # ═══ CONFLICT CHECK ═══
        conflits_seances = self.db.verifier_conflit_seance(
            date, heure_debut, heure_fin, salle_id=salle_id,
            enseignant_id=self.user.id, groupe_id=groupe_id
        )
        conflits_reservations = self.db.verifier_conflit_reservation(
            date, heure_debut, heure_fin, salle_id
        )
        
        if conflits_seances or conflits_reservations:
            msg = "⚠️ Conflits détectés:\n\n"
            for c in conflits_seances:
                msg += f"• {c}\n"
            for cr in conflits_reservations:
                prof_name = f"{cr[-2]} {cr[-1]}" if len(cr) >= 2 else "Inconnu"
                msg += f"• Salle réservée par {prof_name} ({cr[4]}-{cr[5]})\n"
            msg += "\nVoulez-vous quand même envoyer la demande?"
            
            reply = QMessageBox.question(self, "Conflit de disponibilité", msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
        
        try:
            self.db.ajouter_reservation(
                enseignant_id=self.user.id, salle_id=salle_id, date=date,
                heure_debut=heure_debut, heure_fin=heure_fin,
                motif=f"{subject} - {res_type}", groupe_id=groupe_id
            )
            QMessageBox.information(self, "Succès", "✅ Votre demande de réservation a été envoyée!")
            self.load_my_reservations()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur: {e}")

    def save_unavailability(self):
        """Save unavailability with notifications"""
        d_start = self.ab_date_start.date().toString("yyyy-MM-dd")
        d_end = self.ab_date_end.date().toString("yyyy-MM-dd")
        reason = self.ab_reason.toPlainText()
        
        if self.ab_date_start.date() > self.ab_date_end.date():
            QMessageBox.warning(self, "Erreur", "Date fin < Date début.")
            return

        period_msg = f"[Période: {d_start} -> {d_end}]" if d_start != d_end else f"[Date: {d_start}]"
        if self.chk_full_day.isChecked(): period_msg += " [Journée entière]"
        final_motif = f"{period_msg} {reason}"
            
        try:
            # ═══════════════════════════════════════════════════════════
            # STEP 1: Save unavailability to DB (close connection immediately)
            # ═══════════════════════════════════════════════════════════
            conn = self.db.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO disponibilites (enseignant_id, date_debut, date_fin, motif) VALUES (?, ?, ?, ?)', 
                             (self.user.id, d_start, d_end, final_motif))
            except:
                cursor.execute('INSERT INTO disponibilites (enseignant_id, date, motif) VALUES (?, ?, ?)', 
                             (self.user.id, d_start, final_motif))
            conn.commit()
            
            # Collect group IDs before closing
            cursor.execute('SELECT DISTINCT groupe_id FROM seances WHERE enseignant_id = ? AND groupe_id IS NOT NULL', (self.user.id,))
            group_ids = [row[0] for row in cursor.fetchall() if row[0]]
            conn.close()
            
            # ═══════════════════════════════════════════════════════════
            # STEP 2: Send notifications (each uses its own connection)
            # ═══════════════════════════════════════════════════════════
            try:
                for groupe_id in group_ids:
                    self.notification_service.notifier_groupe(
                        groupe_id=groupe_id,
                        type_notification='info',
                        titre=f'Enseignant indisponible',
                        message=f"Votre enseignant {self.user.prenom} {self.user.nom} sera indisponible {period_msg}. Raison: {reason or 'Non spécifiée'}"
                    )
                self.notification_service.notifier_admins(
                    type_notification='info',
                    titre=f"🚷 Indisponibilité: {self.user.nom} {self.user.prenom}",
                    message=f"L'enseignant {self.user.prenom} {self.user.nom} a déclaré une indisponibilité.\n{period_msg}\nRaison: {reason or 'Non spécifiée'}"
                )
            except Exception as e: print(f"Notif error: {e}")
            
            # ═══════════════════════════════════════════════════════════
            # STEP 3: Cancel/delete affected sessions (frees rooms)
            # ═══════════════════════════════════════════════════════════
            cancelled_count = 0
            try:
                conn2 = self.db.get_connection()
                cursor2 = conn2.cursor()
                cursor2.execute(
                    'SELECT id, titre, date, heure_debut, heure_fin, groupe_id FROM seances WHERE enseignant_id = ? AND date >= ? AND date <= ?',
                    (self.user.id, d_start, d_end)
                )
                affected = cursor2.fetchall()
                # Collect cancelled session info
                cancelled_sessions = []
                for s in affected:
                    s_id, s_titre, s_date, s_hd, s_hf, s_gid = s
                    cursor2.execute('DELETE FROM seances WHERE id = ?', (s_id,))
                    cancelled_count += 1
                    cancelled_sessions.append((s_titre, s_date, s_hd, s_hf, s_gid))
                
                # Also cancel/delete approved or pending reservations in the same period
                # so the rooms are freed for other professors
                cursor2.execute(
                    "SELECT id, motif, date, heure_debut, heure_fin, groupe_id FROM reservations WHERE enseignant_id = ? AND date >= ? AND date <= ? AND statut IN ('validee', 'en_attente')",
                    (self.user.id, d_start, d_end)
                )
                affected_reservations = cursor2.fetchall()
                cancelled_res_info = []
                for r in affected_reservations:
                    r_id, r_motif, r_date, r_hd, r_hf, r_gid = r
                    cursor2.execute('DELETE FROM reservations WHERE id = ?', (r_id,))
                    cancelled_count += 1
                    cancelled_res_info.append((r_motif or 'Réservation', r_date, r_hd, r_hf, r_gid))
                
                conn2.commit()
                conn2.close()
                
                # Send cancellation notifications after connection is closed
                for s_titre, s_date, s_hd, s_hf, s_gid in cancelled_sessions:
                    if s_gid:
                        try:
                            self.notification_service.notifier_groupe(
                                groupe_id=s_gid,
                                type_notification='annulation',
                                titre=f'⚠️ Séance annulée: {s_titre}',
                                message=f"La séance '{s_titre}' du {s_date} ({s_hd}-{s_hf}) a été annulée car l'enseignant {self.user.prenom} {self.user.nom} est indisponible."
                            )
                        except Exception as e: print(f"Notif cancel error: {e}")
                # Send cancellation notifications for cancelled reservations
                for r_motif, r_date, r_hd, r_hf, r_gid in cancelled_res_info:
                    if r_gid:
                        try:
                            self.notification_service.notifier_groupe(
                                groupe_id=r_gid,
                                type_notification='annulation',
                                titre=f'⚠️ Réservation annulée: {r_motif}',
                                message=f"La réservation '{r_motif}' du {r_date} ({r_hd}-{r_hf}) a été annulée car l'enseignant {self.user.prenom} {self.user.nom} est indisponible."
                            )
                        except Exception as e: print(f"Notif cancel res error: {e}")
                if cancelled_count > 0:
                    try:
                        self.notification_service.notifier_admins(
                            type_notification='alerte',
                            titre=f'⚠️ {cancelled_count} séance(s) annulée(s)',
                            message=f"{cancelled_count} séance(s) de {self.user.prenom} {self.user.nom} ont été automatiquement annulées suite à son indisponibilité {period_msg}."
                        )
                    except Exception as e: print(f"Notif admin error: {e}")
            except Exception as e: print(f"Auto-readjust error: {e}")
            
            cancelled_msg = f"\n\n⚠️ {cancelled_count} séance(s) ont été automatiquement annulées." if cancelled_count > 0 else ""
            QMessageBox.information(self, "Succès", f"Indisponibilité enregistrée.{cancelled_msg}")
            self.ab_reason.clear()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur: {e}")

    def load_my_reservations(self):
        # Clear existing cards
        while self.reservations_cards_layout.count() > 1:
            item = self.reservations_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            reservations = self.db.get_reservations_by_enseignant(self.user.id)
            
            if not reservations:
                empty_frame = QFrame()
                empty_frame.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border-radius: 16px;
                        border: 2px dashed #E2E8F0;
                    }
                """)
                empty_layout = QVBoxLayout(empty_frame)
                empty_layout.setContentsMargins(40, 60, 40, 60)
                empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                empty_icon = QLabel("📋")
                empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_icon.setStyleSheet("font-size: 48px; background: transparent; border: none;")
                empty_layout.addWidget(empty_icon)
                
                empty_text = QLabel("Aucune réservation pour le moment")
                empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_text.setStyleSheet("font-size: 16px; font-weight: 600; color: #94A3B8; background: transparent; border: none;")
                empty_layout.addWidget(empty_text)
                
                empty_sub = QLabel("Vos demandes de réservation apparaîtront ici")
                empty_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_sub.setStyleSheet("font-size: 13px; color: #CBD5E1; background: transparent; border: none;")
                empty_layout.addWidget(empty_sub)
                
                self.reservations_cards_layout.insertWidget(0, empty_frame)
            else:
                for res in reservations:
                    card = self._create_reservation_card(res)
                    self.reservations_cards_layout.insertWidget(self.reservations_cards_layout.count() - 1, card)
                    
        except Exception as e:
            print(f"Error loading reservations: {e}")
        self.mark_all_notifications_read()

    def mark_all_notifications_read(self):
        try: self.notification_service.marquer_toutes_lues(self.user.id)
        except: pass
        self.update_reservation_badge()

    def update_reservation_badge(self):
        try:
            count = self.notification_service.get_unread_count(self.user.id)
            badge = self.badge_labels.get("MyReservations")
            if badge:
                badge.setText(str(min(count, 99)))
                badge.setVisible(count > 0)
        except: pass

    def export_schedule(self, format_type):
        from src.logic.timetable_export_service import TimetableExportService
        try:
            export_service = TimetableExportService(self.db)
            fmt_map = {"PDF": "pdf", "Excel": "excel", "Image": "png"}
            success, path, error = export_service.export_teacher_timetable(self.user.id, format_type=fmt_map.get(format_type, "pdf"))
            if success: QMessageBox.information(self, "Export réussi", f"Fichier: {path}")
            else: QMessageBox.warning(self, "Erreur", str(error))
        except Exception as e: QMessageBox.warning(self, "Erreur", str(e))

    def _load_sessions_table(self):
        """Charge les séances de l'enseignant dans la table de modification"""
        self.sessions_table.setRowCount(0)
        try:
            seances = self.db.get_seances_by_enseignant(self.user.id)
            for s in seances:
                row = self.sessions_table.rowCount()
                self.sessions_table.insertRow(row)
                # s: id(0), titre(1), type_seance(2), date(3), heure_debut(4), heure_fin(5), salle_id(6), enseignant_id(7), groupe_id(8)
                self.sessions_table.setItem(row, 0, QTableWidgetItem(str(s[0])))  # ID (hidden)
                self.sessions_table.setItem(row, 1, QTableWidgetItem(str(s[1])))  # Module
                self.sessions_table.setItem(row, 2, QTableWidgetItem(str(s[2])))  # Type
                self.sessions_table.setItem(row, 3, QTableWidgetItem(str(s[3])))  # Date
                self.sessions_table.setItem(row, 4, QTableWidgetItem(f"{s[4]} - {s[5]}"))  # Heure
                # Salle name
                salle_name = "—"
                if s[6]:
                    salle = self.db.get_salle_by_id(s[6])
                    if salle: salle_name = salle[1]
                self.sessions_table.setItem(row, 5, QTableWidgetItem(salle_name))
                # Groupe name
                groupe_name = "—"
                if s[8]:
                    groupe = self.db.get_groupe_by_id(s[8])
                    if groupe: groupe_name = groupe[1]
                self.sessions_table.setItem(row, 6, QTableWidgetItem(groupe_name))
        except Exception as e:
            print(f"Load sessions error: {e}")

    def _on_session_selected(self, current, previous):
        """Show/hide modification form when a session row is selected"""
        if current:
            self.modify_form.setVisible(True)
        else:
            self.modify_form.setVisible(False)

    def modify_session(self):
        """Modify a session with conflict validation + notifications.
        Applies the change to ALL matching sessions across the entire semester
        (same module, type, prof, group, same original day-of-week & time)."""
        from datetime import datetime as dt, timedelta

        row = self.sessions_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner une séance à modifier.")
            return

        seance_id = int(self.sessions_table.item(row, 0).text())
        original = self.db.get_seance_by_id(seance_id)
        if not original:
            QMessageBox.warning(self, "Erreur", "Séance introuvable.")
            return

        new_date = self.mod_date.date().toString("yyyy-MM-dd")
        time_text = self.mod_time.currentText()
        try:
            parts = time_text.split(" - ")
            new_heure_debut = parts[0].strip()
            new_heure_fin = parts[1].strip()
        except (IndexError, AttributeError):
            QMessageBox.warning(self, "Erreur", "Créneau horaire invalide.")
            return

        # Resolve new salle
        salle_nom = self.mod_salle.currentText()
        salles = self.db.get_toutes_salles()
        new_salle_id = next((s[0] for s in salles if s[1] == salle_nom), None)
        if not new_salle_id:
            QMessageBox.warning(self, "Erreur", "Salle non trouvée.")
            return

        # Get the group of this session for conflict check
        groupe_id = original[8]
        module_name = original[1]
        type_seance = original[2]
        old_date_str = original[3]
        old_heure_debut = original[4]
        old_heure_fin = original[5]
        old_salle_id = original[6]

        # ── Find ALL sibling sessions across the semester ──
        # Same module, type, prof, group, same original day-of-week & time slot
        old_weekday = dt.strptime(old_date_str, "%Y-%m-%d").weekday()
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, date FROM seances
            WHERE enseignant_id = ? AND groupe_id = ? AND titre = ? AND type_seance = ?
              AND heure_debut = ? AND heure_fin = ?
        ''', (self.user.id, groupe_id, module_name, type_seance,
              old_heure_debut, old_heure_fin))
        sibling_rows = cursor.fetchall()
        conn.close()

        # Keep only those on the same day-of-week as the original
        sibling_ids = []
        for s_id, s_date in sibling_rows:
            try:
                if dt.strptime(s_date, "%Y-%m-%d").weekday() == old_weekday:
                    sibling_ids.append(s_id)
            except ValueError:
                continue

        if not sibling_ids:
            sibling_ids = [seance_id]  # fallback to just the selected one

        # ═══ CONFLICT CHECK (exclude ALL sibling sessions) ═══
        # We check conflicts for the new slot using a custom query that
        # excludes all sibling IDs so they don't conflict with themselves.
        new_weekday = dt.strptime(new_date, "%Y-%m-%d").weekday()
        conflict_found = False
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get all dates in seances sharing the new day-of-week
            cursor.execute("SELECT DISTINCT date FROM seances")
            all_dates = [r[0] for r in cursor.fetchall()]
            matching_dates = []
            for d in all_dates:
                try:
                    if dt.strptime(d, "%Y-%m-%d").weekday() == new_weekday:
                        matching_dates.append(d)
                except ValueError:
                    continue

            if matching_dates:
                ph = ",".join(["?"] * len(matching_dates))
                ex = ",".join(["?"] * len(sibling_ids))

                # Room conflict
                cursor.execute(f'''
                    SELECT 1 FROM seances
                    WHERE salle_id = ? AND date IN ({ph}) AND id NOT IN ({ex})
                    AND ((heure_debut < ? AND heure_fin > ?) OR
                         (heure_debut < ? AND heure_fin > ?) OR
                         (heure_debut >= ? AND heure_fin <= ?))
                    LIMIT 1
                ''', [new_salle_id] + matching_dates + sibling_ids +
                     [new_heure_fin, new_heure_debut,
                      new_heure_fin, new_heure_debut,
                      new_heure_debut, new_heure_fin])
                if cursor.fetchone():
                    conflict_found = True

                # Teacher conflict
                if not conflict_found:
                    cursor.execute(f'''
                        SELECT 1 FROM seances
                        WHERE enseignant_id = ? AND date IN ({ph}) AND id NOT IN ({ex})
                        AND ((heure_debut < ? AND heure_fin > ?) OR
                             (heure_debut < ? AND heure_fin > ?) OR
                             (heure_debut >= ? AND heure_fin <= ?))
                        LIMIT 1
                    ''', [self.user.id] + matching_dates + sibling_ids +
                         [new_heure_fin, new_heure_debut,
                          new_heure_fin, new_heure_debut,
                          new_heure_debut, new_heure_fin])
                    if cursor.fetchone():
                        conflict_found = True

                # Group conflict
                if not conflict_found and groupe_id:
                    cursor.execute(f'''
                        SELECT 1 FROM seances
                        WHERE groupe_id = ? AND date IN ({ph}) AND id NOT IN ({ex})
                        AND ((heure_debut < ? AND heure_fin > ?) OR
                             (heure_debut < ? AND heure_fin > ?) OR
                             (heure_debut >= ? AND heure_fin <= ?))
                        LIMIT 1
                    ''', [groupe_id] + matching_dates + sibling_ids +
                         [new_heure_fin, new_heure_debut,
                          new_heure_fin, new_heure_debut,
                          new_heure_debut, new_heure_fin])
                    if cursor.fetchone():
                        conflict_found = True

            # Also check reservation conflicts on the new day-of-week
            if not conflict_found:
                conflits_reservations = self.db.verifier_conflit_reservation(
                    new_date, new_heure_debut, new_heure_fin, new_salle_id
                )
                if conflits_reservations:
                    conflict_found = True

            conn.close()
        except Exception as e:
            print(f"Conflict check error: {e}")
            try: conn.close()
            except: pass

        if conflict_found:
            QMessageBox.warning(self, "Conflit de disponibilité",
                "⚠️ Ce créneau / salle est déjà occupé par une autre séance ou réservation.\n"
                "Impossible de déplacer la séance.")
            return

        # Save original info for notification
        old_heure = f"{old_heure_debut} - {old_heure_fin}"
        old_salle_name = "?"
        if old_salle_id:
            old_salle = self.db.get_salle_by_id(old_salle_id)
            if old_salle: old_salle_name = old_salle[1]

        # ── Apply modification to ALL sibling sessions ──
        # Compute the day-of-week shift (e.g. Monday→Wednesday = +2 days)
        old_date_obj = dt.strptime(old_date_str, "%Y-%m-%d")
        new_date_obj = dt.strptime(new_date, "%Y-%m-%d")
        day_shift = new_date_obj.weekday() - old_date_obj.weekday()

        updated_count = 0
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            for sid in sibling_ids:
                # Get this sibling's current date
                cursor.execute("SELECT date FROM seances WHERE id = ?", (sid,))
                row_data = cursor.fetchone()
                if not row_data:
                    continue
                sibling_date = dt.strptime(row_data[0], "%Y-%m-%d")
                # Shift the date by the day-of-week difference
                shifted_date = (sibling_date + timedelta(days=day_shift)).strftime("%Y-%m-%d")

                cursor.execute('''
                    UPDATE seances SET date = ?, heure_debut = ?, heure_fin = ?, salle_id = ?
                    WHERE id = ?
                ''', (shifted_date, new_heure_debut, new_heure_fin, new_salle_id, sid))
                updated_count += cursor.rowcount
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Bulk update error: {e}")
            try: conn.close()
            except: pass

        if updated_count > 0:
            # ═══ NOTIFY STUDENTS (group) AND ADMIN ═══
            try:
                notif_titre = f"Séance modifiée: {module_name}"
                notif_msg = (
                    f"La séance '{module_name}' a été reprogrammée par Prof. {self.user.nom} {self.user.prenom}.\n"
                    f"Ancien: {old_heure} (Salle {old_salle_name})\n"
                    f"Nouveau: {new_heure_debut}-{new_heure_fin} (Salle {salle_nom})\n"
                    f"Ce changement s'applique à tout le semestre ({updated_count} séance(s) mises à jour)."
                )
                if groupe_id:
                    self.notification_service.notifier_groupe(
                        groupe_id=groupe_id,
                        type_notification='modification',
                        titre=notif_titre,
                        message=notif_msg,
                        seance_id=seance_id
                    )
                self.notification_service.notifier_admins(
                    type_notification='modification',
                    titre=notif_titre,
                    message=notif_msg,
                    seance_id=seance_id
                )
            except Exception as e:
                print(f"Notification error: {e}")

            QMessageBox.information(self, "Succès",
                f"✅ La séance a été reprogrammée avec succès!\n"
                f"{updated_count} séance(s) mises à jour sur tout le semestre.\n"
                f"Les étudiants et l'administration ont été notifiés.")
            self._load_sessions_table()
            self.modify_form.setVisible(False)
            self.load_schedule()
        else:
            QMessageBox.warning(self, "Erreur", "Impossible de modifier la séance.")

    # ═══════════════════════════════════════════════════════════
    # MODERN UI CONSTRUCTION
    # ═══════════════════════════════════════════════════════════

    def create_sidebar(self):
        """Menu latéral Enseignant - même design que l'espace étudiant"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(280)
        self.sidebar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['sidebar_top']}, stop:0.5 {COLORS['sidebar_mid']}, stop:1 {COLORS['sidebar_bot']});
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(8)
        
        # Header avec dégradé
        header = QFrame()
        header.setFixedHeight(100)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
                border: none;
            }}
        """)
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(20, 25, 20, 25)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("ESPACE ENSEIGNANT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: white; 
            font-size: 18px;
            font-weight: 700; 
            letter-spacing: 1px;
            background: transparent;
        """)
        h_layout.addWidget(title)
        
        layout.addWidget(header)
        layout.addSpacing(16)
        
        self.menu_buttons = {}
        self.badge_labels = {}
        
        menus = [("Emploi du Temps", "Schedule"), ("Réserver une séance", "Reservation"), ("Chercher une Salle", "RoomSearch"), ("Mes Réservations", "MyReservations"), ("Indisponibilités", "Unavailability")]
        
        for label, pid in menus:
            btn_container = QWidget()
            btn_container.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(16, 0, 16, 0)
            
            btn = QPushButton(f"  {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(48)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: rgba(255, 255, 255, 0.75);
                    text-align: left;
                    padding: 12px 20px;
                    font-size: 15px;
                    font-weight: 500;
                    border: none;
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    background: rgba(255, 255, 255, 0.08);
                    color: white;
                }}
                QPushButton:checked {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
                    color: white;
                    font-weight: 700;
                }}
            """)
            btn.clicked.connect(lambda _, p=pid: self.switch_page(p))
            btn_layout.addWidget(btn)
            
            if pid == "MyReservations":
                badge = QLabel("0")
                badge.setFixedSize(24, 24)
                badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge.setStyleSheet("background-color: #EF4444; color: white; border-radius: 12px; font-size: 12px; font-weight: bold;")
                badge.setVisible(False)
                btn_layout.addWidget(badge)
                self.badge_labels[pid] = badge
            layout.addWidget(btn_container)
            self.menu_buttons[pid] = btn
            
        layout.addStretch()
        
        # Carte utilisateur
        user_frame = QFrame()
        user_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                margin: 12px 16px;
            }
        """)
        user_layout = QVBoxLayout(user_frame)
        user_layout.setContentsMargins(16, 16, 16, 16)
        user_layout.setSpacing(8)
        
        # Avatar "P" (Prof)
        avatar = QLabel("P")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 {COLORS['secondary']}, stop:1 {COLORS['primary']});
            color: white;
            font-size: 22px;
            font-weight: bold;
            border-radius: 25px;
            border: 2px solid rgba(255,255,255,0.3);
        """)
        
        avatar_layout = QHBoxLayout()
        avatar_layout.addStretch()
        avatar_layout.addWidget(avatar)
        avatar_layout.addStretch()
        user_layout.addLayout(avatar_layout)
        
        user_name = QLabel(f"Prof. {self.user.nom if self.user else 'Enseignant'}")
        user_name.setStyleSheet("color: white; font-size: 14px; font-weight: 600; background: transparent;")
        user_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(user_name)
        
        role_badge = QLabel("Enseignant")
        role_badge.setStyleSheet(f"""
            color: {COLORS['primary_light']};
            font-size: 11px;
            background: rgba(108, 92, 231, 0.2);
            padding: 4px 10px;
            border-radius: 8px;
        """)
        role_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_layout = QHBoxLayout()
        role_layout.addStretch()
        role_layout.addWidget(role_badge)
        role_layout.addStretch()
        user_layout.addLayout(role_layout)
        
        layout.addWidget(user_frame)
        
        # Bouton Déconnexion
        logout = QPushButton("Déconnexion")
        logout.setCursor(Qt.CursorShape.PointingHandCursor)
        logout.setStyleSheet(f"""
            QPushButton {{
                background: transparent; 
                color: {COLORS['error']}; 
                border: 2px solid {COLORS['error']};
                border-radius: 12px; 
                padding: 12px 20px; 
                margin: 8px 16px 16px 16px; 
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{ 
                background: {COLORS['error']}; 
                color: white;
                border: 2px solid {COLORS['error']};
            }}
        """)
        logout.clicked.connect(self.logout_signal.emit)
        layout.addWidget(logout)
        self.main_layout.addWidget(self.sidebar)

    def create_content_area(self):
        self.content = QFrame()
        self.content.setStyleSheet(f"background-color: {COLORS.get('bg_light', '#F1F5F9')};")
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(40, 40, 40, 40)
        
        self.page_title = QLabel("Mon Emploi du Temps")
        self.page_title.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {COLORS['text_dark']}; margin-bottom: 20px;")
        layout.addWidget(self.page_title)
        
        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_schedule_page())
        self.pages.addWidget(self.create_reservation_page())
        self.pages.addWidget(self.create_room_search_page())
        self.pages.addWidget(self.create_my_reservations_page())
        self.pages.addWidget(self.create_unavailability_page())
        layout.addWidget(self.pages)
        self.main_layout.addWidget(self.content)

    def create_schedule_page(self):
        """Page Emploi du temps - même design que l'espace étudiant"""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # Carte en-tête avec ombre
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 16px;
                border: 1px solid #E2E8F0;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 15))
        header_frame.setGraphicsEffect(shadow)
        
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(24, 20, 24, 20)
        
        # Info Enseignant
        info_label = QLabel(f"<b style='color:{COLORS['primary']}'>Prof:</b> <span style='color:{COLORS['text_dark']}'>{self.user.nom} {self.user.prenom}</span> | <b style='color:{COLORS['primary']}'>Email:</b> <span style='color:{COLORS['text_dark']}'>{getattr(self.user, 'email', '')}</span>")
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setStyleSheet("font-size: 15px; background: transparent;")
        h_layout.addWidget(info_label)
        h_layout.addStretch()
        # Boutons Export
        for fmt in ["PDF", "Excel", "Image"]:
            btn = QPushButton(f"Imprimer {fmt}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: white;
                    color: {COLORS['primary']};
                    border: 2px solid {COLORS['primary']};
                    border-radius: 10px;
                    padding: 10px 20px;
                    font-weight: 600;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background: rgba(108, 92, 231, 0.06);
                }}
            """)
            btn.clicked.connect(lambda _, f=fmt: self.export_schedule(f))
            h_layout.addWidget(btn)
        layout.addWidget(header_frame)
        
        # Table emploi du temps dans un cadre arrondi avec ombre
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 16px;
                border: 1px solid #E2E8F0;
            }
        """)
        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(20)
        shadow2.setXOffset(0)
        shadow2.setYOffset(4)
        shadow2.setColor(QColor(0, 0, 0, 15))
        table_frame.setGraphicsEffect(shadow2)
        
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.schedule_table = QTableWidget(5, 6)
        self.schedule_table.setHorizontalHeaderLabels(["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"])
        time_slots = ["08:30 - 10:00", "10:15 - 11:45", "12:00 - 13:30", "13:45 - 15:15", "15:30 - 17:00"]
        self.schedule_table.setVerticalHeaderLabels(time_slots)
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.schedule_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.schedule_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                border-radius: 16px;
                gridline-color: #E2E8F0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget QTableCornerButton::section {
                background: white;
                border: none;
                border-top-left-radius: 16px;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6C5CE7, stop:1 #5A4BD1);
                color: white;
                font-weight: 600;
                font-size: 13px;
                padding: 12px;
                border: none;
            }
        """)
        self.load_schedule()
        table_layout.addWidget(self.schedule_table)
        layout.addWidget(table_frame)
        return page

    def create_reservation_page(self):
        """Page Réserver / Modifier une séance — single clean layout"""
        # ── Shared styles ──
        card_style = """
            QFrame {
                background-color: #FFFFFF;
                border-radius: 20px;
                border: none;
            }
        """
        def _card_shadow():
            s = QGraphicsDropShadowEffect()
            s.setBlurRadius(16)
            s.setXOffset(0)
            s.setYOffset(8)
            s.setColor(QColor(0, 0, 0, 25))
            return s

        res_label_style = "font-family: 'Segoe UI', sans-serif; color: #0F172A; font-size: 15px; font-weight: 600;"
        res_input_style = """
            font-family: 'Segoe UI', sans-serif;
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 14px;
            color: #334155;
            min-height: 20px;
        """
        res_combo_style = res_input_style + """
            QComboBox::drop-down {
                border: none;
                width: 28px;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #64748B;
                margin-right: 8px;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                selection-background-color: #EEF2FF;
            }
        """

        from PyQt6.QtWidgets import QScrollArea

        page = QWidget()
        page.setStyleSheet("background: transparent;")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(scroll_content)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(24)
        layout.setContentsMargins(0, 0, 0, 24)

        # ═══════════════════════════════════════════════════
        # SECTION 1 — Modifier une séance existante
        # ═══════════════════════════════════════════════════
        modify_frame = QFrame()
        modify_frame.setStyleSheet(card_style)
        modify_frame.setGraphicsEffect(_card_shadow())
        modify_layout = QVBoxLayout(modify_frame)
        modify_layout.setSpacing(0)
        modify_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        modify_header = QFrame()
        modify_header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
                border: none;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }}
        """)
        modify_header.setFixedHeight(72)
        mh_layout = QVBoxLayout(modify_header)
        mh_layout.setContentsMargins(24, 16, 24, 16)
        mh_layout.setSpacing(4)
        lbl_modify = QLabel("Modifier une séance")
        lbl_modify.setStyleSheet("color: white; font-size: 18px; font-weight: 700; background: transparent;")
        lbl_modify_sub = QLabel("Sélectionnez une séance pour la reprogrammer")
        lbl_modify_sub.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 14px; background: transparent;")
        mh_layout.addWidget(lbl_modify)
        mh_layout.addWidget(lbl_modify_sub)
        modify_layout.addWidget(modify_header)

        # Sessions table
        modify_body = QWidget()
        modify_body_layout = QVBoxLayout(modify_body)
        modify_body_layout.setContentsMargins(24, 20, 24, 12)
        modify_body_layout.setSpacing(16)

        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(7)
        self.sessions_table.setHorizontalHeaderLabels(["ID", "Module", "Type", "Date", "Heure", "Salle", "Groupe"])
        self.sessions_table.setColumnHidden(0, True)
        self.sessions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sessions_table.verticalHeader().setVisible(False)
        self.sessions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sessions_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.sessions_table.setMaximumHeight(220)
        self.sessions_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #FFFFFF; border: 1px solid #E5E7EB;
                border-radius: 12px; gridline-color: #F1F5F9;
            }}
            QTableWidget::item {{
                padding: 10px 12px; color: {COLORS['text_dark']}; font-size: 13px;
            }}
            QTableWidget::item:selected {{
                background-color: rgba(108, 92, 231, 0.08); color: {COLORS['primary']};
            }}
            QHeaderView::section {{
                background: #F8FAFC; color: #475569;
                font-weight: 600; font-size: 12px;
                padding: 10px 12px; border: none;
                border-bottom: 2px solid #E2E8F0;
            }}
        """)
        self.sessions_table.currentItemChanged.connect(self._on_session_selected)
        modify_body_layout.addWidget(self.sessions_table)

        # Modification form (hidden until a session is selected)
        self.modify_form = QFrame()
        self.modify_form.setStyleSheet("QFrame { background: #F8FAFC; border-radius: 12px; border: 1px solid #E5E7EB; }")
        self.modify_form.setVisible(False)
        mf_layout = QVBoxLayout(self.modify_form)
        mf_layout.setContentsMargins(20, 20, 20, 20)
        mf_layout.setSpacing(16)

        mf_title = QLabel("Reprogrammer la séance sélectionnée")
        mf_title.setStyleSheet(f"color: {COLORS['primary']}; font-size: 15px; font-weight: 700; background: transparent;")
        mf_layout.addWidget(mf_title)

        grid_m = QGridLayout()
        grid_m.setSpacing(16)
        for col, label_text in enumerate(["Nouvelle Date", "Nouveau Créneau", "Nouvelle Salle"]):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(res_label_style)
            grid_m.addWidget(lbl, 0, col)

        self.mod_date = QDateEdit(QDate.currentDate())
        self.mod_date.setCalendarPopup(True)
        self.mod_date.setMinimumDate(QDate.currentDate())
        self.mod_date.setDisplayFormat("dd/MM/yyyy")
        self.mod_date.setStyleSheet(res_input_style)
        self.mod_date.setMinimumHeight(44)
        self.mod_date.dateChanged.connect(lambda: self._update_time_slots(self.mod_date, self.mod_time))
        grid_m.addWidget(self.mod_date, 1, 0)

        self.mod_time = QComboBox()
        self._update_time_slots(self.mod_date, self.mod_time)
        self.mod_time.setStyleSheet(res_combo_style)
        self.mod_time.setMinimumHeight(44)
        grid_m.addWidget(self.mod_time, 1, 1)

        self.mod_salle = QComboBox()
        self.mod_salle.addItems([s[1] for s in self.db.get_toutes_salles()])
        self.mod_salle.setStyleSheet(res_combo_style)
        self.mod_salle.setMinimumHeight(44)
        grid_m.addWidget(self.mod_salle, 1, 2)
        mf_layout.addLayout(grid_m)

        btn_modify_row = QHBoxLayout()
        btn_modify_row.addStretch()
        btn_modify = QPushButton("Appliquer la modification")
        btn_modify.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_modify.setMinimumHeight(44)
        btn_modify.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
                color: #FFFFFF; font-weight: 700; font-size: 15px;
                border: none; border-radius: 10px; padding: 12px 32px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary_dark']}, stop:1 {COLORS['primary']});
            }}
        """)
        btn_modify.clicked.connect(self.modify_session)
        btn_modify_row.addWidget(btn_modify)
        mf_layout.addLayout(btn_modify_row)
        modify_body_layout.addWidget(self.modify_form)
        modify_layout.addWidget(modify_body)
        layout.addWidget(modify_frame)

        # ═══════════════════════════════════════════════════
        # SECTION 2 — Nouvelle réservation
        # ═══════════════════════════════════════════════════
        new_frame = QFrame()
        new_frame.setStyleSheet(card_style)
        new_frame.setGraphicsEffect(_card_shadow())
        new_layout = QVBoxLayout(new_frame)
        new_layout.setSpacing(0)
        new_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        new_header = QFrame()
        new_header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent']}, stop:1 {COLORS['accent_warm']});
                border: none;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }}
        """)
        new_header.setFixedHeight(72)
        nh_layout = QVBoxLayout(new_header)
        nh_layout.setContentsMargins(24, 16, 24, 16)
        nh_layout.setSpacing(4)
        lbl_new = QLabel("Nouvelle Réservation")
        lbl_new.setStyleSheet("color: white; font-size: 18px; font-weight: 700; background: transparent;")
        lbl_new_sub = QLabel("Demander une nouvelle séance avec vérification automatique des conflits")
        lbl_new_sub.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 14px; background: transparent;")
        nh_layout.addWidget(lbl_new)
        nh_layout.addWidget(lbl_new_sub)
        new_layout.addWidget(new_header)

        # Form body
        form_b = QWidget()
        form_b_layout = QVBoxLayout(form_b)
        form_b_layout.setContentsMargins(24, 24, 24, 24)
        form_b_layout.setSpacing(20)

        grid_b = QGridLayout()
        for col, label_text in enumerate(["Date", "Créneau", "Matière", "Type"]):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(res_label_style)
            lbl.setMinimumHeight(24)
            grid_b.addWidget(lbl, 0, col)

        self.new_res_date = QDateEdit(QDate.currentDate())
        self.new_res_date.setCalendarPopup(True)
        self.new_res_date.setMinimumDate(QDate.currentDate())
        self.new_res_date.setDisplayFormat("dd/MM/yyyy")
        self.new_res_date.setStyleSheet(res_input_style)
        self.new_res_date.setMinimumHeight(44)
        self.new_res_date.dateChanged.connect(lambda: self._update_time_slots(self.new_res_date, self.new_res_time))
        grid_b.addWidget(self.new_res_date, 1, 0)

        self.new_res_time = QComboBox()
        self._update_time_slots(self.new_res_date, self.new_res_time)
        self.new_res_time.setStyleSheet(res_combo_style)
        self.new_res_time.setMinimumHeight(44)
        grid_b.addWidget(self.new_res_time, 1, 1)

        self.new_res_subject = QComboBox()
        self.new_res_subject.setEditable(True)
        self.new_res_subject.setPlaceholderText("Saisir ou choisir une matière...")
        prof_modules = self.db.get_modules_by_enseignant(self.user.id)
        if prof_modules:
            self.new_res_subject.addItems(prof_modules)
        else:
            self.new_res_subject.addItems(["Algorithmique", "Base de données", "Réseaux", "POO", "Anglais"])
        self.new_res_subject.setStyleSheet(res_combo_style)
        self.new_res_subject.setMinimumHeight(44)
        grid_b.addWidget(self.new_res_subject, 1, 2)

        self.new_res_type = QComboBox()
        self.new_res_type.addItems(["Cours", "TP", "TD", "Examen"])
        self.new_res_type.setStyleSheet(res_combo_style)
        self.new_res_type.setMinimumHeight(44)
        self.new_res_type.currentTextChanged.connect(self._on_res_type_changed)
        grid_b.addWidget(self.new_res_type, 1, 3)
        form_b_layout.addLayout(grid_b)

        # Second row: Groupe + Salle
        grid_b2 = QGridLayout()
        for col, label_text in enumerate(["Groupe", "Salle"]):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(res_label_style)
            lbl.setMinimumHeight(24)
            grid_b2.addWidget(lbl, 0, col)

        self.new_res_groupe = QComboBox()
        prof_groupes = self.db.get_groupes_by_enseignant(self.user.id)
        if prof_groupes:
            self.new_res_groupe.addItems([g[1] for g in prof_groupes])
        else:
            self.new_res_groupe.addItems([g[1] for g in self.db.get_tous_groupes()])
        self.new_res_groupe.setStyleSheet(res_combo_style)
        self.new_res_groupe.setMinimumHeight(44)
        grid_b2.addWidget(self.new_res_groupe, 1, 0)

        self.new_res_salle = QComboBox()
        # Initially load rooms based on default type (Cours)
        self._update_salle_combo(self.new_res_salle, "Cours")
        self.new_res_salle.setStyleSheet(res_combo_style)
        self.new_res_salle.setMinimumHeight(44)
        grid_b2.addWidget(self.new_res_salle, 1, 1)
        form_b_layout.addLayout(grid_b2)

        form_b_layout.addSpacing(12)
        btn_layout_b = QHBoxLayout()
        btn_layout_b.addStretch()
        btn_b = QPushButton("Envoyer Demande")
        btn_b.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent']}, stop:1 {COLORS['accent_warm']});
                color: #FFFFFF; font-weight: 700; font-size: 16px;
                border: none; border-radius: 10px; padding: 12px 32px;
                min-height: 24px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E8607A, stop:1 #E0B73E);
            }}
        """)
        btn_b.setMinimumHeight(44)
        btn_b.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_b.clicked.connect(self.submit_reservation)
        btn_layout_b.addWidget(btn_b)
        form_b_layout.addLayout(btn_layout_b)
        new_layout.addWidget(form_b)

        layout.addWidget(new_frame)
        layout.addStretch()

        scroll.setWidget(scroll_content)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        # Load sessions into the table
        self._load_sessions_table()

        return page

    # ═══════════════════════════════════════════════════════════
    # ROOM SEARCH PAGE — Chercher une Salle
    # ═══════════════════════════════════════════════════════════

    def create_room_search_page(self):
        """Page permettant à l'enseignant de chercher une salle vacante par critères"""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(24)

        # Filters Card
        filters_frame = QFrame()
        filters_frame.setObjectName("filtersCard")
        filters_frame.setStyleSheet("""
            QFrame#filtersCard {
                background-color: white;
                border-radius: 20px;
                border: 1px solid #E2E8F0;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(108, 92, 231, 25))
        filters_frame.setGraphicsEffect(shadow)

        f_layout = QVBoxLayout(filters_frame)
        f_layout.setContentsMargins(32, 28, 32, 28)
        f_layout.setSpacing(20)

        section_title = QLabel("🔍  Rechercher une Salle Vacante")
        section_title.setStyleSheet("color: #1E293B; font-size: 20px; font-weight: 700; background: transparent;")
        f_layout.addWidget(section_title)

        section_desc = QLabel("Trouvez une salle disponible selon la date, le créneau, la capacité et le type")
        section_desc.setStyleSheet("color: #64748B; font-size: 14px; background: transparent;")
        f_layout.addWidget(section_desc)

        input_style = """
            QDateEdit, QComboBox, QSpinBox {
                background-color: #F8FAFC;
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                color: #1E293B;
                min-width: 150px;
            }
            QDateEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 2px solid #6C5CE7;
                background: white;
            }
        """
        label_style = "color: #374151; font-size: 13px; font-weight: 600; background: transparent;"

        # Row 1: Date + Time slot
        row1 = QHBoxLayout()
        row1.setSpacing(20)

        date_c = QVBoxLayout()
        date_c.setSpacing(6)
        date_c.addWidget(QLabel("📅 Date"))
        date_c.itemAt(0).widget().setStyleSheet(label_style)
        self.rs_date = QDateEdit(QDate.currentDate())
        self.rs_date.setCalendarPopup(True)
        self.rs_date.setDisplayFormat("dd/MM/yyyy")
        self.rs_date.setStyleSheet(input_style)
        self.rs_date.dateChanged.connect(self._update_rs_time_slots)
        date_c.addWidget(self.rs_date)
        row1.addLayout(date_c)

        time_c = QVBoxLayout()
        time_c.setSpacing(6)
        time_c.addWidget(QLabel("🕐 Créneau"))
        time_c.itemAt(0).widget().setStyleSheet(label_style)
        self.rs_time_slot = QComboBox()
        self._update_rs_time_slots()
        self.rs_time_slot.setStyleSheet(input_style)
        time_c.addWidget(self.rs_time_slot)
        row1.addLayout(time_c)

        # Row 1 continued: capacity + type
        cap_c = QVBoxLayout()
        cap_c.setSpacing(6)
        cap_c.addWidget(QLabel("👥 Capacité min."))
        cap_c.itemAt(0).widget().setStyleSheet(label_style)
        from PyQt6.QtWidgets import QSpinBox
        self.rs_capacity = QSpinBox()
        self.rs_capacity.setRange(0, 500)
        self.rs_capacity.setValue(0)
        self.rs_capacity.setSpecialValueText("Toutes")
        self.rs_capacity.setStyleSheet(input_style)
        cap_c.addWidget(self.rs_capacity)
        row1.addLayout(cap_c)

        type_c = QVBoxLayout()
        type_c.setSpacing(6)
        type_c.addWidget(QLabel("🏫 Type"))
        type_c.itemAt(0).widget().setStyleSheet(label_style)
        self.rs_type = QComboBox()
        self.rs_type.addItems(["Tous", "Salle", "Amphithéâtre", "Laboratoire"])
        self.rs_type.setStyleSheet(input_style)
        type_c.addWidget(self.rs_type)
        row1.addLayout(type_c)

        row1.addStretch()

        btn_search = QPushButton("🔍  Rechercher")
        btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search.setFixedSize(160, 48)
        btn_search.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
                color: white; border: none; border-radius: 12px;
                font-weight: 700; font-size: 14px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary_dark']}, stop:1 {COLORS['secondary_dark']});
            }}
        """)
        btn_search.clicked.connect(self._search_rooms)
        btn_c = QVBoxLayout()
        btn_c.addSpacing(22)
        btn_c.addWidget(btn_search)
        row1.addLayout(btn_c)

        f_layout.addLayout(row1)
        layout.addWidget(filters_frame)

        # Results Table
        table_frame = QFrame()
        table_frame.setStyleSheet("QFrame { background-color: white; border-radius: 16px; border: 1px solid #E2E8F0; }")
        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(20)
        shadow2.setXOffset(0)
        shadow2.setYOffset(4)
        shadow2.setColor(QColor(0, 0, 0, 15))
        table_frame.setGraphicsEffect(shadow2)

        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.rs_results_table = QTableWidget()
        self.rs_results_table.setColumnCount(5)
        self.rs_results_table.setHorizontalHeaderLabels(["Nom", "Type", "Capacité", "Équipements", "État"])
        self.rs_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.rs_results_table.verticalHeader().setVisible(False)
        self.rs_results_table.setShowGrid(False)
        self.rs_results_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: white; border: none; border-radius: 16px;
            }}
            QTableWidget::item {{
                padding: 12px; color: {COLORS['text_dark']};
            }}
            QHeaderView::section {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_dark']});
                color: white; font-weight: 600; font-size: 13px;
                padding: 14px; border: none;
            }}
        """)
        table_layout.addWidget(self.rs_results_table)
        layout.addWidget(table_frame)

        return page

    def _update_rs_time_slots(self):
        """Update room search time slots — Friday excludes 12:30-14:00"""
        all_slots = ["09:00 - 10:30", "10:45 - 12:15", "12:30 - 14:00", "14:15 - 15:45", "16:00 - 17:30"]
        day_of_week = self.rs_date.date().dayOfWeek()
        current = self.rs_time_slot.currentText()
        self.rs_time_slot.clear()
        slots = [s for s in all_slots if s != "12:30 - 14:00"] if day_of_week == 5 else all_slots
        self.rs_time_slot.addItems(slots)
        idx = self.rs_time_slot.findText(current)
        if idx >= 0:
            self.rs_time_slot.setCurrentIndex(idx)

    def _search_rooms(self):
        """Search for available rooms by criteria (date, time, capacity, type, equipment)"""
        from datetime import datetime

        date_val = self.rs_date.date().toString("yyyy-MM-dd")
        time_text = self.rs_time_slot.currentText()
        min_cap = self.rs_capacity.value()
        room_type = self.rs_type.currentText()

        try:
            parts = time_text.split(" - ")
            heure_debut, heure_fin = parts[0].strip(), parts[1].strip()
        except (IndexError, AttributeError):
            QMessageBox.warning(self, "Erreur", "Sélectionnez un créneau horaire valide.")
            return

        try:
            date_obj = datetime.strptime(date_val, "%Y-%m-%d")
            day_of_week = date_obj.weekday()
        except ValueError:
            return

        try:
            all_rooms = self.db.get_toutes_salles()

            # Filter by capacity and type
            filtered_rooms = []
            for r in all_rooms:
                cap = r[2] if len(r) > 2 else 0
                rtype = r[3] if len(r) > 3 else "Salle"
                if min_cap > 0 and cap < min_cap:
                    continue
                if room_type != "Tous" and rtype != room_type:
                    continue
                filtered_rooms.append(r)

            # Find occupied rooms
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT DISTINCT date FROM seances")
            all_dates = [row[0] for row in cursor.fetchall()]
            matching_dates = [d for d in all_dates if datetime.strptime(d, "%Y-%m-%d").weekday() == day_of_week]

            occupied_ids = set()
            if matching_dates:
                ph = ",".join(["?"] * len(matching_dates))
                cursor.execute(f"""
                    SELECT DISTINCT salle_id FROM seances
                    WHERE date IN ({ph})
                    AND ((heure_debut < ? AND heure_fin > ?) OR
                         (heure_debut >= ? AND heure_fin <= ?))
                """, matching_dates + [heure_fin, heure_debut, heure_debut, heure_fin])
                occupied_ids.update(row[0] for row in cursor.fetchall())

            cursor.execute("""
                SELECT DISTINCT salle_id FROM reservations
                WHERE date = ? AND statut = 'validee'
                AND ((heure_debut < ? AND heure_fin > ?) OR
                     (heure_debut >= ? AND heure_fin <= ?))
            """, (date_val, heure_fin, heure_debut, heure_debut, heure_fin))
            occupied_ids.update(row[0] for row in cursor.fetchall())
            conn.close()

            free = [r for r in filtered_rooms if r[0] not in occupied_ids]
            busy = [r for r in filtered_rooms if r[0] in occupied_ids]

            self.rs_results_table.setRowCount(len(free) + len(busy))
            row_idx = 0
            for r in free:
                self.rs_results_table.setItem(row_idx, 0, QTableWidgetItem(r[1]))
                self.rs_results_table.setItem(row_idx, 1, QTableWidgetItem(r[3] if len(r) > 3 else ""))
                self.rs_results_table.setItem(row_idx, 2, QTableWidgetItem(str(r[2])))
                equip = (r[4] or "").replace(";", ", ").replace("_", " ").title() if len(r) > 4 else ""
                self.rs_results_table.setItem(row_idx, 3, QTableWidgetItem(equip))
                lbl = QLabel("✅ LIBRE")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet("background: #DCFCE7; color: #15803D; font-weight: 600; font-size: 11px; padding: 6px 12px; border-radius: 12px;")
                self.rs_results_table.setCellWidget(row_idx, 4, lbl)
                self.rs_results_table.setRowHeight(row_idx, 50)
                row_idx += 1

            for r in busy:
                self.rs_results_table.setItem(row_idx, 0, QTableWidgetItem(r[1]))
                self.rs_results_table.setItem(row_idx, 1, QTableWidgetItem(r[3] if len(r) > 3 else ""))
                self.rs_results_table.setItem(row_idx, 2, QTableWidgetItem(str(r[2])))
                equip = (r[4] or "").replace(";", ", ").replace("_", " ").title() if len(r) > 4 else ""
                self.rs_results_table.setItem(row_idx, 3, QTableWidgetItem(equip))
                lbl = QLabel("❌ OCCUPÉE")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet("background: #FEE2E2; color: #DC2626; font-weight: 600; font-size: 11px; padding: 6px 12px; border-radius: 12px;")
                self.rs_results_table.setCellWidget(row_idx, 4, lbl)
                self.rs_results_table.setRowHeight(row_idx, 50)
                row_idx += 1

        except Exception as e:
            print(f"Room search error: {e}")

    def create_my_reservations_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 8, 0, 24)
        
        # Gradient header card
        header_card = QFrame()
        header_card.setObjectName("resHeader")
        header_card.setStyleSheet(f"""
            QFrame#resHeader {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:0.5 #A29BFE, stop:1 {COLORS['secondary']});
                border-radius: 20px;
                border: none;
            }}
        """)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(32, 28, 32, 28)
        
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(8)
        
        header_title = QLabel("📋  Mes Réservations")
        header_title.setStyleSheet("color: white; font-size: 24px; font-weight: 700; background: transparent;")
        header_text_layout.addWidget(header_title)
        
        header_desc = QLabel("Suivez l'état de vos demandes de réservation de salles")
        header_desc.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 14px; background: transparent;")
        header_text_layout.addWidget(header_desc)
        
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()
        
        btn_refresh = QPushButton("🔄  Actualiser")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setFixedHeight(42)
        btn_refresh.setMinimumWidth(140)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2); color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600; font-size: 13px;
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 10px; padding: 0 20px;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 0.3); }
            QPushButton:pressed { background: rgba(255, 255, 255, 0.15); }
        """)
        btn_refresh.clicked.connect(self.load_my_reservations)
        header_layout.addWidget(btn_refresh)
        
        layout.addWidget(header_card)
        
        # Reservation cards scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #F1F5F9; width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #94A3B8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        
        self.reservations_container = QWidget()
        self.reservations_container.setStyleSheet("background: transparent;")
        self.reservations_cards_layout = QVBoxLayout(self.reservations_container)
        self.reservations_cards_layout.setSpacing(12)
        self.reservations_cards_layout.setContentsMargins(0, 0, 8, 0)
        self.reservations_cards_layout.addStretch()
        
        scroll.setWidget(self.reservations_container)
        layout.addWidget(scroll)
        
        return page

    def _create_reservation_card(self, res):
        """Create a styled reservation card
        Query columns: id=0, enseignant_id=1, salle_nom=2, date=3, heure_debut=4,
                       heure_fin=5, motif=6, statut=7, groupe_nom=8, groupe_id=9
        """
        date_val = str(res[3])
        heure_debut = str(res[4])
        heure_fin = str(res[5]) if len(res) > 5 and res[5] else ""
        heure_val = f"{heure_debut} - {heure_fin}" if heure_fin else heure_debut
        salle_val = str(res[2])
        motif_val = str(res[6]) if len(res) > 6 and res[6] else ""
        statut = res[7] if len(res) > 7 else "en_attente"
        groupe_nom = str(res[8]) if len(res) > 8 and res[8] else ""
        
        status_config = {
            'validee': {'icon': '✅', 'color': '#10B981', 'bg': '#ECFDF5', 'label': 'Acceptée'},
            'rejetee': {'icon': '❌', 'color': '#EF4444', 'bg': '#FEF2F2', 'label': 'Rejetée'},
            'en_attente': {'icon': '⏳', 'color': '#F59E0B', 'bg': '#FFFBEB', 'label': 'En attente'},
        }
        cfg = status_config.get(statut, status_config['en_attente'])
        
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border-radius: 14px;
                border-left: 4px solid {cfg['color']};
                border-top: 1px solid #F1F5F9;
                border-right: 1px solid #F1F5F9;
                border-bottom: 1px solid #F1F5F9;
            }}
            QFrame:hover {{
                background-color: {cfg['bg']};
                border-top: 1px solid {cfg['color']}30;
                border-right: 1px solid {cfg['color']}30;
                border-bottom: 1px solid {cfg['color']}30;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 12))
        card.setGraphicsEffect(shadow)
        
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(16)
        
        # Status icon circle
        icon_frame = QFrame()
        icon_frame.setFixedSize(48, 48)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {cfg['bg']};
                border-radius: 24px;
                border: 2px solid {cfg['color']}40;
            }}
        """)
        icon_label = QLabel(cfg['icon'])
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 20px; background: transparent; border: none;")
        icon_inner = QVBoxLayout(icon_frame)
        icon_inner.setContentsMargins(0, 0, 0, 0)
        icon_inner.addWidget(icon_label)
        card_layout.addWidget(icon_frame)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)
        
        # Title row: salle + status badge
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        
        salle_label = QLabel(f"🏫  Salle {salle_val}")
        salle_label.setStyleSheet(f"""
            font-family: 'Segoe UI', sans-serif;
            font-size: 15px; font-weight: 700;
            color: {COLORS['text_dark']}; background: transparent; border: none;
        """)
        title_row.addWidget(salle_label)
        
        status_badge = QLabel(f"{cfg['icon']} {cfg['label']}")
        status_badge.setFixedHeight(26)
        status_badge.setStyleSheet(f"""
            background-color: {cfg['bg']};
            color: {cfg['color']};
            font-size: 11px; font-weight: 700;
            padding: 3px 12px;
            border-radius: 13px;
            border: 1px solid {cfg['color']}40;
        """)
        title_row.addWidget(status_badge)
        title_row.addStretch()
        content_layout.addLayout(title_row)
        
        # Details row
        details_row = QHBoxLayout()
        details_row.setSpacing(20)
        
        date_info = QLabel(f"📅 {date_val}")
        date_info.setStyleSheet("font-size: 13px; color: #64748B; background: transparent; border: none;")
        details_row.addWidget(date_info)
        
        time_info = QLabel(f"🕐 {heure_val}")
        time_info.setStyleSheet("font-size: 13px; color: #64748B; background: transparent; border: none;")
        details_row.addWidget(time_info)
        
        details_row.addStretch()
        content_layout.addLayout(details_row)
        
        # Motif
        if motif_val:
            motif_label = QLabel(f"💬  {motif_val}")
            motif_label.setWordWrap(True)
            motif_label.setStyleSheet("font-size: 13px; color: #94A3B8; background: transparent; border: none;")
            content_layout.addWidget(motif_label)
        
        # Group info
        if groupe_nom:
            grp_frame = QFrame()
            grp_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(108, 92, 231, 0.06);
                    border-radius: 8px;
                    border: 1px solid rgba(108, 92, 231, 0.15);
                    padding: 4px;
                }}
            """)
            grp_layout = QHBoxLayout(grp_frame)
            grp_layout.setContentsMargins(10, 6, 10, 6)
            grp_icon = QLabel("👥")
            grp_icon.setStyleSheet("background: transparent; border: none; font-size: 13px;")
            grp_layout.addWidget(grp_icon)
            grp_text = QLabel(f"Groupe: {groupe_nom}")
            grp_text.setStyleSheet(f"font-size: 12px; color: {COLORS['primary']}; font-weight: 600; background: transparent; border: none;")
            grp_layout.addWidget(grp_text, 1)
            content_layout.addWidget(grp_frame)
        
        card_layout.addLayout(content_layout, 1)
        
        return card

    def create_unavailability_page(self):
        """Page Mes Indisponibilités - design avec dégradé, ombres et formulaire soigné"""
        # Styles alignés sur l'image
        label_style = "font-family: 'Segoe UI', sans-serif; color: #343a40; font-size: 14px; font-weight: 600;"
        input_style = """
            font-family: 'Segoe UI', sans-serif;
            background-color: #ffffff;
            border: 1px solid #CED4DA;
            border-radius: 8px;
            padding: 12px 14px;
            font-size: 14px;
            color: #343a40;
        """

        page = QWidget()
        page.setStyleSheet("background-color: #f4f6f9; font-family: 'Segoe UI', sans-serif;")
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(20)

        # Bannière dégradé (rouge-orange)
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent']}, stop:1 {COLORS['accent_warm']});
                border: none;
                border-radius: 12px;
            }}
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(24, 20, 24, 20)
        header_layout.setSpacing(6)

        title_header = QLabel("Signaler une Indisponibilité")
        title_header.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            color: #ffffff;
            font-size: 18px;
            font-weight: bold;
            background: transparent;
        """)
        header_layout.addWidget(title_header)

        subtitle_header = QLabel("Informez l'administration de vos absences ou indisponibilités")
        subtitle_header.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            color: #f8f9fa;
            font-size: 13px;
            font-weight: normal;
            background: transparent;
        """)
        header_layout.addWidget(subtitle_header)
        layout.addWidget(header_frame)

        # Carte formulaire avec ombre
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 10px;
                border: none;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 25))
        form_frame.setGraphicsEffect(shadow)

        form_main = QVBoxLayout(form_frame)
        form_main.setSpacing(18)
        form_main.setContentsMargins(24, 24, 24, 24)

        # Ligne des deux dates
        date_row = QHBoxLayout()
        date_row.setSpacing(20)

        col_start = QVBoxLayout()
        col_start.setSpacing(6)
        lbl_start = QLabel("Date de Début")
        lbl_start.setStyleSheet(label_style)
        col_start.addWidget(lbl_start)
        self.ab_date_start = QDateEdit(QDate.currentDate())
        self.ab_date_start.setCalendarPopup(True)
        self.ab_date_start.setMinimumHeight(42)
        self.ab_date_start.setMinimumDate(QDate.currentDate())
        self.ab_date_start.setDisplayFormat("dd/MM/yyyy")
        self.ab_date_start.setStyleSheet("QDateEdit { " + input_style + " min-width: 180px; }")
        col_start.addWidget(self.ab_date_start)
        date_row.addLayout(col_start)

        col_end = QVBoxLayout()
        col_end.setSpacing(6)
        lbl_end = QLabel("Date de Fin (Optionnel)")
        lbl_end.setStyleSheet(label_style)
        col_end.addWidget(lbl_end)
        self.ab_date_end = QDateEdit(QDate.currentDate())
        self.ab_date_end.setCalendarPopup(True)
        self.ab_date_end.setMinimumHeight(42)
        self.ab_date_end.setMinimumDate(QDate.currentDate())
        self.ab_date_end.setDisplayFormat("dd/MM/yyyy")
        self.ab_date_end.setStyleSheet("QDateEdit { " + input_style + " min-width: 180px; }")
        col_end.addWidget(self.ab_date_end)
        date_row.addLayout(col_end)
        date_row.addStretch()
        form_main.addLayout(date_row)

        # Checkbox Journée Entière
        self.chk_full_day = QCheckBox("Journée Entière")
        self.chk_full_day.setStyleSheet("""
            QCheckBox {
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-weight: normal;
                color: #343a40;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #CED4DA;
                background: #ffffff;
            }
            QCheckBox::indicator:checked {
                background: #FD79A8;
                border: 2px solid #FD79A8;
            }
        """)
        self.chk_full_day.setChecked(True)
        form_main.addWidget(self.chk_full_day)

        # Motif de l'absence
        lbl_motif = QLabel("Motif de l'absence")
        lbl_motif.setStyleSheet(label_style)
        form_main.addWidget(lbl_motif)
        self.ab_reason = QTextEdit()
        self.ab_reason.setPlaceholderText("Décrivez la raison de votre indisponibilité...")
        self.ab_reason.setStyleSheet("""
            QTextEdit {
                font-family: 'Segoe UI', sans-serif;
                background-color: #ffffff;
                border: 1px solid #CED4DA;
                border-radius: 8px;
                padding: 12px 14px;
                font-size: 14px;
                color: #343a40;
            }
        """)
        self.ab_reason.setMinimumHeight(100)
        self.ab_reason.setMaximumHeight(130)
        form_main.addWidget(self.ab_reason)

        # Bouton centré avec dégradé
        btn_submit = QPushButton("Signaler Indisponibilité")
        btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_submit.setStyleSheet(f"""
            QPushButton {{
                font-family: 'Segoe UI', sans-serif;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent']}, stop:1 {COLORS['accent_warm']});
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 12px 28px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E8607A, stop:1 #E0B73E);
            }}
        """)
        btn_submit.clicked.connect(self.save_unavailability)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_submit)
        btn_row.addStretch()
        form_main.addLayout(btn_row)

        layout.addWidget(form_frame)
        layout.addStretch()
        return page

    def switch_page(self, page_id):
        titles = {"Schedule": "Mon Emploi du Temps", "Reservation": "Réserver", "RoomSearch": "Chercher une Salle", "MyReservations": "Mes Réservations", "Unavailability": "Indisponibilités"}
        self.page_title.setText(titles.get(page_id, page_id))
        
        mapping = {"Schedule": 0, "Reservation": 1, "RoomSearch": 2, "MyReservations": 3, "Unavailability": 4}
        if page_id in mapping:
            self.pages.setCurrentIndex(mapping[page_id])
            if page_id == "Schedule": self.load_schedule()
            elif page_id == "Reservation": self._load_sessions_table()
            elif page_id == "MyReservations": self.load_my_reservations()
            
        for pid, btn in self.menu_buttons.items():
            btn.setChecked(pid == page_id)