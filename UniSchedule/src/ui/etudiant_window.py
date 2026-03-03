# src/ui/etudiant_window.py
"""
Fenêtre principale de l'étudiant - Modern SaaS Design
MERGED: Visuals from etudiant_window 10 + Full Logic from etudiant_window
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QStackedWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QComboBox, QListWidget,
    QListWidgetItem, QDateEdit, QTimeEdit, QMessageBox, QGridLayout,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTime
from PyQt6.QtGui import QIcon, QPixmap, QColor

from configUI import WINDOW_CONFIG, COLORS, FST_LOGO_IMAGE
from src.services_notification import NotificationService
import os

class UserWrapper:
    def __init__(self, user_tuple):
        self.id = user_tuple[0]
        self.nom = user_tuple[1]
        self.prenom = user_tuple[2]
        self.email = user_tuple[3]
        # Get groupe_id from database if needed
        self.groupe_id = None

class EtudiantWindow(QWidget):
    logout_signal = pyqtSignal()
    
    def __init__(self, user, db):
        super().__init__()
        if isinstance(user, tuple):
            self.user = UserWrapper(user)
        else:
            self.user = user
            
        self.db = db
        self.notification_service = NotificationService(db)
        
        # Get student's groupe_id (LOGIC PRESERVED)
        self._load_groupe_id()
        
        self.setWindowTitle("UniSchedule-Gestion d'emploi du Temps FSTT")
        self.setMinimumSize(1024, 768)
        self.showMaximized()
        
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
                font-size: 14px;
            }
        """)
        
        # Layout principal
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.create_sidebar()
        self.create_content_area()
        self.switch_page("Schedule")
        self.update_notification_badge()

    # ═══════════════════════════════════════════════════════════
    # LOGIC METHODS (PRESERVED)
    # ═══════════════════════════════════════════════════════════

    def _load_groupe_id(self):
        """Load student's groupe_id from database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT groupe_id FROM utilisateurs WHERE id = ?', (self.user.id,))
            result = cursor.fetchone()
            conn.close()
            if result:
                self.user.groupe_id = result[0]
        except Exception as e:
            print(f"Error loading groupe_id: {e}")

    def load_schedule(self):
        """Load student's group schedule with enhanced display"""
        self.schedule_table.clearContents()
        
        def get_row(time_str):
            if "08" in time_str or "09" in time_str: return 0
            if "10" in time_str or "11" in time_str: return 1
            if "12" in time_str or "13" in time_str: return 2
            if "14" in time_str or "15" in time_str: return 3
            if "16" in time_str or "17" in time_str: return 4
            return -1

        try:
            if hasattr(self.user, 'groupe_id') and self.user.groupe_id:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT s.date, s.heure_debut, s.titre, s.type_seance, sa.nom, u.nom, u.prenom
                    FROM seances s
                    LEFT JOIN salles sa ON s.salle_id = sa.id
                    LEFT JOIN utilisateurs u ON s.enseignant_id = u.id
                    WHERE s.groupe_id = ?
                ''', (self.user.groupe_id,))
                seances = cursor.fetchall()
                conn.close()
                
                for s in seances:
                    date_str = s[0]
                    qdate = QDate.fromString(date_str, "yyyy-MM-dd")
                    day_idx = qdate.dayOfWeek() - 1
                    
                    if 0 <= day_idx <= 5:
                        row = get_row(s[1])
                        if row != -1:
                            module = s[2]
                            session_type = s[3]
                            salle = s[4] if s[4] else "?"
                            prof = f"{s[5]} {s[6]}" if s[5] else "?"
                            
                            # Color based on type
                            if session_type == "Cours": color = "#6366F1"  # Indigo
                            elif session_type == "TD": color = "#10B981"  # Green
                            elif session_type == "TP": color = "#F59E0B"  # Amber
                            else: color = "#8B5CF6"  # Purple
                            
                            txt = f"{module}\n📍 {salle}\n👨‍🏫 {prof}\n({session_type})"
                            self.set_course(self.schedule_table, row, day_idx, txt, color)
        except Exception as e:
            print(f"Student schedule error: {e}")

    def set_course(self, table, row, col, text, color):
        item = QLabel(text)
        item.setAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setStyleSheet(f"""
            background-color: {color};
            color: white; 
            border-radius: 8px; 
            margin: 2px; 
            padding: 4px;
            font-weight: 600;
            font-size: 11px;
        """)
        item.setWordWrap(True)
        table.setCellWidget(row, col, item)

    def export_schedule(self, format_type):
        """Export schedule logic"""
        from src.logic.timetable_export_service import TimetableExportService
        try:
            export_service = TimetableExportService(self.db)
            
            if not hasattr(self.user, 'groupe_id') or not self.user.groupe_id:
                QMessageBox.warning(self, "Erreur", "Groupe non défini pour cet étudiant")
                return
            
            fmt_map = {"PDF": "pdf", "Excel": "excel", "Image": "png"}
            fmt = fmt_map.get(format_type, "pdf")
            
            success, path, error = export_service.export_group_timetable(
                self.user.groupe_id, 
                format_type=fmt
            )
            
            if success and path:
                QMessageBox.information(self, "Export réussi", f"Fichier exporté:\n{path}")
            else:
                QMessageBox.warning(self, "Erreur", f"Erreur export: {error}")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur export: {e}")

    def load_notifications(self):
        """Load notifications from database"""
        self.notif_table.setRowCount(0)
        try:
            notifications = self.notification_service.get_notifications_utilisateur(self.user.id)
            
            for notif in notifications:
                row = self.notif_table.rowCount()
                self.notif_table.insertRow(row)
                
                date_item = QTableWidgetItem(str(notif.get('date_creation', '')))
                type_item = QTableWidgetItem(str(notif.get('type', '')))
                titre_item = QTableWidgetItem(str(notif.get('titre', '')))
                msg_item = QTableWidgetItem(str(notif.get('message', '')))
                
                is_read = notif.get('lue', True)
                if not is_read:
                    for item in [date_item, type_item, titre_item, msg_item]:
                        item.setBackground(QColor("#EEF2FF"))
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                
                self.notif_table.setItem(row, 0, date_item)
                self.notif_table.setItem(row, 1, type_item)
                self.notif_table.setItem(row, 2, titre_item)
                self.notif_table.setItem(row, 3, msg_item)
                self.notif_table.setRowHeight(row, 50)
        except Exception as e:
            print(f"Error loading notifications: {e}")
        self.mark_all_read()

    def mark_all_read(self):
        try:
            self.notification_service.marquer_toutes_lues(self.user.id)
        except: pass
        self.update_notification_badge()

    def update_notification_badge(self):
        try:
            count = self.notification_service.get_unread_count(self.user.id)
            badge = self.badge_labels.get("Updates")
            if badge:
                if count > 0:
                    badge.setText(str(min(count, 99)))
                    badge.setVisible(True)
                else:
                    badge.setVisible(False)
        except: pass

    def find_available_rooms(self):
        """Room search logic"""
        date_val = self.search_date.date().toString("yyyy-MM-dd")
        time_val = self.search_time.time().toString("HH:mm")
        
        try:
            all_rooms = self.db.get_toutes_salles()
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT salle_id FROM seances 
                WHERE date = ? 
                AND ? BETWEEN heure_debut AND heure_fin
            """, (date_val, time_val))
            occupied_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            available = [r for r in all_rooms if r[0] not in occupied_ids]
            
            self.rooms_table.setRowCount(len(available))
            for i, r in enumerate(available):
                self.rooms_table.setItem(i, 0, QTableWidgetItem(r[1]))
                self.rooms_table.setItem(i, 1, QTableWidgetItem(r[3] if len(r) > 3 else ""))
                self.rooms_table.setItem(i, 2, QTableWidgetItem(str(r[2])))
                
                status_widget = QLabel("LIBRE")
                status_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                status_widget.setStyleSheet("background: #DCFCE7; color: #15803D; font-weight: 600; font-size: 11px; padding: 6px 12px; border-radius: 12px;")
                self.rooms_table.setCellWidget(i, 3, status_widget)
                self.rooms_table.setRowHeight(i, 50)
                
        except Exception as e:
            print(f"Room search error: {e}")

    # ═══════════════════════════════════════════════════════════
    # MODERN UI CONSTRUCTION
    # ═══════════════════════════════════════════════════════════

    def create_sidebar(self):
        """Modern Sidebar"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(280)
        self.sidebar.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E1B4B, stop:0.5 #312E81, stop:1 #1E1B4B); border: none; }")
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(8)
        
        # Header
        header = QFrame()
        header.setFixedHeight(100)
        header.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #06B6D4); border: none; }")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(20, 25, 20, 25)
        title = QLabel("ESPACE ETUDIANT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 18px; font-weight: 700; background: transparent;")
        h_layout.addWidget(title)
        layout.addWidget(header)
        layout.addSpacing(16)
        
        # Menu buttons
        self.menu_buttons = {}
        self.badge_labels = {}
        
        menus = [("Emploi du Temps", "Schedule", False), ("Salles Libres", "Search", False), ("Mises à jour", "Updates", True)]
        
        for label, pid, has_badge in menus:
            btn_container = QWidget()
            btn_container.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(16, 0, 16, 0)
            btn_layout.setSpacing(0)
            
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
            
            if has_badge:
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
        
        # User info
        user_frame = QFrame()
        user_frame.setStyleSheet("QFrame { background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 14px; margin: 12px 16px; }")
        user_layout = QVBoxLayout(user_frame)
        avatar = QLabel("E")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #06B6D4, stop:1 #6366F1); color: white; font-size: 22px; font-weight: bold; border-radius: 25px; border: 2px solid rgba(255,255,255,0.3);")
        user_layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)
        user_name = QLabel(f"{self.user.nom} {self.user.prenom}")
        user_name.setStyleSheet("color: white; font-size: 14px; font-weight: 600; background: transparent;")
        user_layout.addWidget(user_name, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(user_frame)
        
        # Logout
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
        
        self.page_title = QLabel("Emploi du Temps")
        self.page_title.setStyleSheet("font-size: 32px; font-weight: 700; color: #1E293B; background: transparent;")
        layout.addWidget(self.page_title)
        
        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_schedule_page())
        self.pages.addWidget(self.create_search_page())
        self.pages.addWidget(self.create_updates_page())
        
        layout.addWidget(self.pages)
        self.main_layout.addWidget(self.content)

    def create_schedule_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("QFrame { background-color: white; border-radius: 16px; border: 1px solid #E2E8F0; }")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(24, 20, 24, 20)
        info_label = QLabel(f"<b style='color:#6366F1'>Étudiant:</b> {self.user.nom} {self.user.prenom} | <b style='color:#6366F1'>Email:</b> {self.user.email}")
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
        
        # Table
        table_frame = QFrame()
        table_frame.setStyleSheet("QFrame { background-color: white; border-radius: 16px; border: 1px solid #E2E8F0; }")
        table_layout = QVBoxLayout(table_frame)
        self.schedule_table = QTableWidget(5, 6)
        self.schedule_table.setHorizontalHeaderLabels(["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"])
        self.schedule_table.setVerticalHeaderLabels(["09:00", "10:45", "12:30", "14:15", "16:00"])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.schedule_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.schedule_table.setStyleSheet("QTableWidget { border: none; gridline-color: #E2E8F0; } QHeaderView::section { background: #6366F1; color: white; border: none; padding: 10px; }")
        self.load_schedule()
        table_layout.addWidget(self.schedule_table)
        layout.addWidget(table_frame)
        return page

    def create_search_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        
        # Filters
        filters_frame = QFrame()
        filters_frame.setStyleSheet("QFrame { background-color: white; border-radius: 20px; border: 1px solid #E2E8F0; }")
        f_layout = QVBoxLayout(filters_frame)
        f_layout.setContentsMargins(32, 28, 32, 28)
        
        title = QLabel("Rechercher une Salle")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")
        f_layout.addWidget(title)
        
        inputs_layout = QHBoxLayout()
        self.search_date = QDateEdit(QDate.currentDate())
        self.search_date.setCalendarPopup(True)
        self.search_date.setStyleSheet("QDateEdit { background: #F8FAFC; border: 2px solid #E2E8F0; border-radius: 12px; padding: 12px; }")
        self.search_time = QTimeEdit(QTime.currentTime())
        self.search_time.setStyleSheet("QTimeEdit { background: #F8FAFC; border: 2px solid #E2E8F0; border-radius: 12px; padding: 12px; }")
        
        inputs_layout.addWidget(QLabel("Date:"))
        inputs_layout.addWidget(self.search_date)
        inputs_layout.addWidget(QLabel("Heure:"))
        inputs_layout.addWidget(self.search_time)
        inputs_layout.addStretch()
        
        btn_search = QPushButton("Rechercher")
        btn_search.setStyleSheet("QPushButton { background: #6366F1; color: white; border-radius: 12px; padding: 12px 24px; font-weight: bold; }")
        btn_search.clicked.connect(self.find_available_rooms)
        inputs_layout.addWidget(btn_search)
        f_layout.addLayout(inputs_layout)
        layout.addWidget(filters_frame)
        
        # Results
        layout.addWidget(QLabel("Résultats", styleSheet="font-size: 18px; font-weight: bold; color: #1E293B;"))
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(4)
        self.rooms_table.setHorizontalHeaderLabels(["Nom", "Type", "Capacité", "État"])
        self.rooms_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.rooms_table.setStyleSheet("QTableWidget { background: white; border-radius: 16px; border: none; } QHeaderView::section { background: #6366F1; color: white; padding: 10px; }")
        layout.addWidget(self.rooms_table)
        
        return page

    def create_updates_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        
        header = QFrame()
        header.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #06B6D4); border-radius: 20px;")
        h_layout = QVBoxLayout(header)
        title = QLabel("Mes Notifications")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        h_layout.addWidget(title)
        layout.addWidget(header)
        
        btn_read = QPushButton("Tout marquer comme lu")
        btn_read.setStyleSheet("background: #10B981; color: white; border-radius: 8px; padding: 10px; font-weight: bold;")
        btn_read.clicked.connect(self.mark_all_read)
        layout.addWidget(btn_read, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.notif_table = QTableWidget()
        self.notif_table.setColumnCount(4)
        self.notif_table.setHorizontalHeaderLabels(["Date", "Type", "Titre", "Message"])
        self.notif_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.notif_table.setStyleSheet("QTableWidget { background: white; border-radius: 20px; border: none; } QHeaderView::section { background: #F8FAFC; color: #475569; padding: 10px; }")
        layout.addWidget(self.notif_table)
        
        return page

    def switch_page(self, page_id):
        titles = {"Schedule": "Mon Emploi du Temps", "Search": "Trouver une Salle", "Updates": "Actualités"}
        self.page_title.setText(titles.get(page_id, page_id))
        
        mapping = {"Schedule": 0, "Search": 1, "Updates": 2}
        if page_id in mapping:
            self.pages.setCurrentIndex(mapping[page_id])
            if page_id == "Schedule": self.load_schedule()
            elif page_id == "Updates": self.load_notifications()
        
        for pid, btn in self.menu_buttons.items():
            btn.setChecked(pid == page_id)