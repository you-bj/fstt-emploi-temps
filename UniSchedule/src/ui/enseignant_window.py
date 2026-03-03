# src/ui/enseignant_window.py
"""
Fenêtre principale de l'enseignant - Modern SaaS Design
MERGED: Visuals from enseignant_window 10 + Full Logic + Notification Fix
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QStackedWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QComboBox, QDateEdit,
    QTimeEdit, QTextEdit, QMessageBox, QGridLayout,
    QGraphicsDropShadowEffect, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QColor

from configUI import WINDOW_CONFIG, COLORS, FST_LOGO_IMAGE
from src.services_notification import NotificationService
from datetime import datetime, timedelta

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
        self.setStyleSheet("QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; }")
        
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
                        
                        if session_type == "Cours": color = "#6366F1"
                        elif session_type == "TD": color = "#10B981"
                        else: color = "#8B5CF6"
                        
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

    def submit_reservation(self):
        """Submit reservation logic (Option B)"""
        date = self.new_res_date.date().toString("yyyy-MM-dd")
        heure_debut = self.new_res_time.time().toString("HH:mm")
        
        # Get text from combos
        groupe_nom = self.new_res_groupe.currentText()
        salle_nom = self.new_res_salle.currentText()
        subject = self.new_res_subject.currentText()
        res_type = self.new_res_type.currentText()
        
        start_time = datetime.strptime(heure_debut, "%H:%M")
        end_time = start_time + timedelta(hours=1, minutes=30)
        heure_fin = end_time.strftime("%H:%M")
        
        # Resolve IDs
        groupes = self.db.get_tous_groupes()
        groupe_id = next((g[0] for g in groupes if g[1] == groupe_nom), None)
        
        salles = self.db.get_toutes_salles()
        salle_id = next((s[0] for s in salles if s[1] == salle_nom), None)
        
        if not salle_id:
            QMessageBox.warning(self, "Erreur", "Salle non trouvée")
            return
        
        try:
            self.db.ajouter_reservation(
                enseignant_id=self.user.id, salle_id=salle_id, date=date,
                heure_debut=heure_debut, heure_fin=heure_fin,
                motif=f"{subject} - {res_type}", groupe_id=groupe_id
            )
            QMessageBox.information(self, "Succès", "Votre demande de réservation a été envoyée!")
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
            conn = self.db.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO disponibilites (enseignant_id, date_debut, date_fin, motif) VALUES (?, ?, ?, ?)', 
                             (self.user.id, d_start, d_end, final_motif))
            except:
                cursor.execute('INSERT INTO disponibilites (enseignant_id, date, motif) VALUES (?, ?, ?)', 
                             (self.user.id, d_start, final_motif))
            conn.commit()
            
            # Notify groups (REQUESTED FIX APPLIED HERE)
            try:
                cursor.execute('SELECT DISTINCT groupe_id FROM seances WHERE enseignant_id = ? AND groupe_id IS NOT NULL', (self.user.id,))
                for (groupe_id,) in cursor.fetchall():
                    if groupe_id:
                        self.notification_service.notifier_groupe(
                            groupe_id=groupe_id,
                            type_notification='info',  # Using 'info' as requested
                            titre=f'Enseignant indisponible',
                            message=f"Votre enseignant {self.user.prenom} {self.user.nom} sera indisponible {period_msg}. Raison: {reason or 'Non spécifiée'}"
                        )
            except Exception as e: print(f"Notif error: {e}")
            
            conn.close()
            QMessageBox.information(self, "Succès", "Indisponibilité enregistrée.")
            self.ab_reason.clear()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur: {e}")

    def load_my_reservations(self):
        self.reservations_table.setRowCount(0)
        try:
            reservations = self.db.get_reservations_by_enseignant(self.user.id)
            for res in reservations:
                row = self.reservations_table.rowCount()
                self.reservations_table.insertRow(row)
                self.reservations_table.setItem(row, 0, QTableWidgetItem(str(res[3])))
                self.reservations_table.setItem(row, 1, QTableWidgetItem(str(res[4])))
                self.reservations_table.setItem(row, 2, QTableWidgetItem(str(res[2])))
                self.reservations_table.setItem(row, 3, QTableWidgetItem(str(res[5])))
                
                statut = res[6] if len(res) > 6 else "en_attente"
                item = QTableWidgetItem(statut)
                if statut == "acceptee": item.setBackground(QColor("#10B981")); item.setForeground(QColor("white"))
                elif statut == "rejetee": item.setBackground(QColor("#EF4444")); item.setForeground(QColor("white"))
                else: item.setBackground(QColor("#F59E0B")); item.setForeground(QColor("white"))
                self.reservations_table.setItem(row, 4, item)
                
                reponse = res[7] if len(res) > 7 else ""
                self.reservations_table.setItem(row, 5, QTableWidgetItem(str(reponse)))
        except Exception as e: print(e)
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

    # ═══════════════════════════════════════════════════════════
    # MODERN UI CONSTRUCTION
    # ═══════════════════════════════════════════════════════════

    def create_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(280)
        self.sidebar.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E1B4B, stop:0.5 #312E81, stop:1 #1E1B4B); border: none; }")
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(8)
        
        header = QFrame()
        header.setFixedHeight(100)
        header.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #06B6D4); border: none; }")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(20, 25, 20, 25)
        title = QLabel("ESPACE ENSEIGNANT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 18px; font-weight: 700; background: transparent;")
        h_layout.addWidget(title)
        layout.addWidget(header)
        layout.addSpacing(16)
        
        self.menu_buttons = {}
        self.badge_labels = {}
        
        menus = [("Emploi du Temps", "Schedule"), ("Réserver une séance", "Reservation"), ("Mes Réservations", "MyReservations"), ("Indisponibilités", "Unavailability")]
        
        for label, pid in menus:
            btn_container = QWidget()
            btn_container.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(16, 0, 16, 0)
            
            btn = QPushButton(f"  {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(48)
            btn.setStyleSheet("""
                QPushButton { background-color: transparent; color: #FFFFFF; text-align: left; padding: 12px 20px; font-size: 15px; font-weight: 600; border: none; border-radius: 12px; }
                QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(99, 102, 241, 0.3), stop:1 rgba(6, 182, 212, 0.2)); }
                QPushButton:checked { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #06B6D4); color: white; font-weight: 700; }
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
        
        user_frame = QFrame()
        user_frame.setStyleSheet("QFrame { background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 14px; margin: 12px 16px; }")
        user_layout = QVBoxLayout(user_frame)
        avatar = QLabel("P")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #06B6D4, stop:1 #6366F1); color: white; font-size: 22px; font-weight: bold; border-radius: 25px; border: 2px solid rgba(255,255,255,0.3);")
        user_layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)
        user_name = QLabel(f"Prof. {self.user.nom} {self.user.prenom}")
        user_name.setStyleSheet("color: white; font-size: 14px; font-weight: 600; background: transparent;")
        user_layout.addWidget(user_name, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(user_frame)
        
        logout = QPushButton("Déconnexion")
        logout.setCursor(Qt.CursorShape.PointingHandCursor)
        logout.setStyleSheet("QPushButton { background: transparent; color: #F87171; border: 2px solid #F87171; border-radius: 10px; padding: 12px 20px; margin: 8px 16px 16px 16px; font-weight: 600; } QPushButton:hover { background: #EF4444; color: white; border: 2px solid #EF4444; }")
        logout.clicked.connect(self.logout_signal.emit)
        layout.addWidget(logout)
        self.main_layout.addWidget(self.sidebar)

    def create_content_area(self):
        self.content = QFrame()
        self.content.setStyleSheet(f"background-color: {COLORS.get('bg_light', '#F1F5F9')};")
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(40, 40, 40, 40)
        
        self.page_title = QLabel("Mon Emploi du Temps")
        self.page_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1E293B; margin-bottom: 20px;")
        layout.addWidget(self.page_title)
        
        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_schedule_page())
        self.pages.addWidget(self.create_reservation_page())
        self.pages.addWidget(self.create_my_reservations_page())
        self.pages.addWidget(self.create_unavailability_page())
        layout.addWidget(self.pages)
        self.main_layout.addWidget(self.content)

    def create_schedule_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        
        header_frame = QFrame()
        header_frame.setStyleSheet("QFrame { background-color: white; border-radius: 16px; border: 1px solid #E2E8F0; }")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(24, 20, 24, 20)
        info_label = QLabel(f"<b style='color:#6366F1'>Prof:</b> {self.user.nom} {self.user.prenom} | <b style='color:#6366F1'>Email:</b> {getattr(self.user, 'email', '')}")
        info_label.setStyleSheet("font-size: 15px; background: transparent;")
        h_layout.addWidget(info_label)
        h_layout.addStretch()
        for fmt in ["PDF", "Excel", "Image"]:
            btn = QPushButton(f"Exporter {fmt}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("QPushButton { background: white; color: #6366F1; border: 2px solid #6366F1; border-radius: 8px; padding: 8px 16px; font-weight: 600; } QPushButton:hover { background: #EEF2FF; }")
            btn.clicked.connect(lambda _, f=fmt: self.export_schedule(f))
            h_layout.addWidget(btn)
        layout.addWidget(header_frame)
        
        table_frame = QFrame()
        table_frame.setStyleSheet("QFrame { background-color: white; border-radius: 16px; border: 1px solid #E2E8F0; }")
        table_layout = QVBoxLayout(table_frame)
        self.schedule_table = QTableWidget(5, 6)
        self.schedule_table.setHorizontalHeaderLabels(["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"])
        self.schedule_table.setVerticalHeaderLabels(["09:00", "10:45", "12:30", "14:15", "16:00"])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.schedule_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.schedule_table.setStyleSheet("QTableWidget { border: none; gridline-color: #E2E8F0; } QHeaderView::section { background: #6366F1; color: white; padding: 10px; border: none; }")
        self.load_schedule()
        table_layout.addWidget(self.schedule_table)
        layout.addWidget(table_frame)
        return page

    def create_reservation_page(self):
        """Page with options"""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        
        # Option B (Primary - New Reservation)
        opt2_frame = QFrame()
        opt2_frame.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 20px; border: 1px solid #E2E8F0; }")
        opt2_layout = QVBoxLayout(opt2_frame)
        
        header_b = QFrame()
        header_b.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #16C0B9, stop:1 #8AE2DE); border-top-left-radius: 20px; border-top-right-radius: 20px;")
        header_b.setFixedHeight(60)
        hb_lbl = QLabel("Nouvelle Réservation")
        hb_lbl.setStyleSheet("color: white; font-weight: bold; font-size: 16px; padding-left: 20px;")
        hb_l = QVBoxLayout(header_b)
        hb_l.addWidget(hb_lbl)
        opt2_layout.addWidget(header_b)
        
        form_b = QWidget()
        form_b_layout = QGridLayout(form_b)
        form_b_layout.setSpacing(15)
        
        self.new_res_date = QDateEdit(QDate.currentDate())
        self.new_res_date.setCalendarPopup(True)
        self.new_res_time = QTimeEdit(QTime(8, 30))
        self.new_res_groupe = QComboBox()
        self.new_res_groupe.addItems([g[1] for g in self.db.get_tous_groupes()])
        self.new_res_subject = QComboBox()
        self.new_res_subject.addItems(["Algorithmique", "Base de données", "Réseaux", "POO", "Anglais"])
        self.new_res_type = QComboBox()
        self.new_res_type.addItems(["Cours", "TP", "TD", "Examen"])
        self.new_res_salle = QComboBox()
        self.new_res_salle.addItems([s[1] for s in self.db.get_toutes_salles()])
        
        widgets = [("Date", self.new_res_date), ("Heure", self.new_res_time), 
                   ("Groupe", self.new_res_groupe), ("Matière", self.new_res_subject),
                   ("Type", self.new_res_type), ("Salle", self.new_res_salle)]
        
        for i, (lbl, w) in enumerate(widgets):
            w.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px; min-height: 30px;")
            form_b_layout.addWidget(QLabel(lbl), i//2 * 2, i%2)
            form_b_layout.addWidget(w, i//2 * 2 + 1, i%2)
            
        opt2_layout.addWidget(form_b)
        
        btn_b = QPushButton("Envoyer Demande")
        btn_b.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_b.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #16C0B9, stop:1 #0D9488); color: white; border-radius: 10px; padding: 12px; font-weight: bold; }")
        btn_b.clicked.connect(self.submit_reservation)
        opt2_layout.addWidget(btn_b)
        
        layout.addWidget(opt2_frame)
        layout.addStretch()
        return page

    def create_my_reservations_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        
        header = QFrame()
        header.setStyleSheet("background: white; border-radius: 16px;")
        h_layout = QHBoxLayout(header)
        h_layout.addWidget(QLabel("Mes Demandes", styleSheet="font-size: 18px; font-weight: bold; color: #1E293B;"))
        btn = QPushButton("Actualiser")
        btn.clicked.connect(self.load_my_reservations)
        btn.setStyleSheet("background: #6366F1; color: white; padding: 8px; border-radius: 6px;")
        h_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(header)
        
        self.reservations_table = QTableWidget()
        self.reservations_table.setColumnCount(6)
        self.reservations_table.setHorizontalHeaderLabels(["Date", "Heure", "Salle", "Motif", "Statut", "Réponse"])
        self.reservations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.reservations_table.setStyleSheet("QTableWidget { background: white; border-radius: 16px; border: none; } QHeaderView::section { background: #6366F1; color: white; padding: 10px; }")
        layout.addWidget(self.reservations_table)
        
        return page

    def create_unavailability_page(self):
        page = QWidget()
        page.setStyleSheet("background: #f4f6f9;")
        layout = QVBoxLayout(page)
        
        header = QFrame()
        header.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E74C3C, stop:1 #F39C12); border-radius: 10px;")
        h_layout = QVBoxLayout(header)
        h_layout.addWidget(QLabel("Signaler Indisponibilité", styleSheet="color: white; font-size: 18px; font-weight: bold;"))
        layout.addWidget(header)
        
        form_frame = QFrame()
        form_frame.setStyleSheet("background: white; border-radius: 10px;")
        f_layout = QVBoxLayout(form_frame)
        f_layout.setSpacing(15)
        
        self.ab_date_start = QDateEdit(QDate.currentDate())
        self.ab_date_end = QDateEdit(QDate.currentDate())
        self.chk_full_day = QCheckBox("Journée Entière")
        self.chk_full_day.setChecked(True)
        self.ab_reason = QTextEdit()
        self.ab_reason.setPlaceholderText("Motif...")
        
        for w in [self.ab_date_start, self.ab_date_end, self.ab_reason]:
            w.setStyleSheet("background: #F8FAFC; border: 1px solid #CED4DA; border-radius: 8px; padding: 8px;")
            
        f_layout.addWidget(QLabel("Du"))
        f_layout.addWidget(self.ab_date_start)
        f_layout.addWidget(QLabel("Au"))
        f_layout.addWidget(self.ab_date_end)
        f_layout.addWidget(self.chk_full_day)
        f_layout.addWidget(QLabel("Motif"))
        f_layout.addWidget(self.ab_reason)
        
        btn = QPushButton("Signaler")
        btn.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E74C3C, stop:1 #F39C12); color: white; padding: 12px; border-radius: 10px; font-weight: bold;")
        btn.clicked.connect(self.save_unavailability)
        f_layout.addWidget(btn)
        
        layout.addWidget(form_frame)
        layout.addStretch()
        return page

    def switch_page(self, page_id):
        titles = {"Schedule": "Mon Emploi du Temps", "Reservation": "Réserver", "MyReservations": "Mes Réservations", "Unavailability": "Indisponibilités"}
        self.page_title.setText(titles.get(page_id, page_id))
        
        mapping = {"Schedule": 0, "Reservation": 1, "MyReservations": 2, "Unavailability": 3}
        if page_id in mapping:
            self.pages.setCurrentIndex(mapping[page_id])
            if page_id == "Schedule": self.load_schedule()
            elif page_id == "MyReservations": self.load_my_reservations()
            
        for pid, btn in self.menu_buttons.items():
            btn.setChecked(pid == page_id)