# src/ui/etudiant_window.py
"""
Fenêtre principale de l'étudiant - Modern SaaS Design
Fonctionnalités : Emploi du temps groupe, Salles libres, Mises à jour
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
import os

class UserWrapper:
    def __init__(self, user_tuple):
        self.id = user_tuple[0]
        self.nom = user_tuple[1]
        self.prenom = user_tuple[2]
        self.email = user_tuple[3]

class EtudiantWindow(QWidget):
    logout_signal = pyqtSignal()
    
    def __init__(self, user, db):
        super().__init__()
        if isinstance(user, tuple):
            self.user = UserWrapper(user)
        else:
            self.user = user
            
        self.db = db
        
        self.setWindowTitle(WINDOW_CONFIG['etudiant']['title'])
        self.setMinimumSize(1024, 768)
        self.showMaximized()
        
        # Modern Global Style
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

    def create_sidebar(self):
        """Modern Sidebar - Dark gradient with glassmorphism"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(280)
        self.sidebar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1E1B4B, stop:0.5 #312E81, stop:1 #1E1B4B);
                border: none;
            }
        """)
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(8)
        
        # Header with gradient
        header = QFrame()
        header.setFixedHeight(100)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366F1, stop:1 #06B6D4);
                border: none;
            }
        """)
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(20, 25, 20, 25)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("ESPACE ETUDIANT")
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
        
        # Menu buttons
        self.menu_buttons = {}
        menus = [
            ("Emploi du Temps", "Schedule"),
            ("Salles Libres", "Search"),
            ("Mises a jour", "Updates")
        ]
        
        for label, pid in menus:
            btn = QPushButton(f"  {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(48)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #FFFFFF;
                    text-align: left;
                    padding: 12px 20px;
                    font-size: 15px;
                    font-weight: 600;
                    border: none;
                    border-radius: 12px;
                    margin: 4px 16px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 rgba(99, 102, 241, 0.3), stop:1 rgba(6, 182, 212, 0.2));
                }
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #6366F1, stop:1 #06B6D4);
                    color: white;
                    font-weight: 700;
                }
            """)
            btn.clicked.connect(lambda _, p=pid: self.switch_page(p))
            layout.addWidget(btn)
            self.menu_buttons[pid] = btn
            
        layout.addStretch()
        
        # User info card
        user_frame = QFrame()
        user_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 14px;
                margin: 12px 16px;
            }
        """)
        user_layout = QVBoxLayout(user_frame)
        user_layout.setContentsMargins(16, 16, 16, 16)
        user_layout.setSpacing(8)
        
        # Avatar
        avatar = QLabel("E")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 #06B6D4, stop:1 #6366F1);
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
        
        user_name = QLabel(f"{self.user.nom} {self.user.prenom}")
        user_name.setStyleSheet("color: white; font-size: 14px; font-weight: 600; background: transparent;")
        user_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(user_name)
        
        role_badge = QLabel("Etudiant LST-GI")
        role_badge.setStyleSheet("""
            color: #A5B4FC;
            font-size: 11px;
            background: rgba(99, 102, 241, 0.2);
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
        
        # Logout button
        logout = QPushButton("Deconnexion")
        logout.setCursor(Qt.CursorShape.PointingHandCursor)
        logout.setStyleSheet("""
            QPushButton {
                background: transparent; 
                color: #F87171; 
                border: 2px solid #F87171;
                border-radius: 10px; 
                padding: 12px 20px; 
                margin: 8px 16px 16px 16px; 
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover { 
                background: #EF4444; 
                color: white;
                border: 2px solid #EF4444;
            }
        """)
        logout.clicked.connect(self.logout_signal.emit)
        layout.addWidget(logout)
        
        self.main_layout.addWidget(self.sidebar)

    def create_content_area(self):
        self.content = QFrame()
        self.content.setStyleSheet("background-color: #F1F5F9;")
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        self.page_title = QLabel("Emploi du Temps")
        self.page_title.setStyleSheet("""
            font-size: 32px; 
            font-weight: 700; 
            color: #1E293B; 
            background: transparent;
        """)
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
        layout.setSpacing(20)
        
        # Header Card
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
        
        # Info Étudiant
        info_label = QLabel(f"<b style='color:#6366F1'>Etudiant:</b> <span style='color:#1E293B'>{self.user.nom} {self.user.prenom}</span> | <b style='color:#6366F1'>Email:</b> <span style='color:#1E293B'>{self.user.email}</span>")
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setStyleSheet("font-size: 15px; background: transparent;")
        h_layout.addWidget(info_label)
        h_layout.addStretch()
        
        # Export buttons
        for fmt in ["PDF", "Excel", "Image"]:
            btn = QPushButton(f"Imprimer {fmt}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: white;
                    color: #6366F1;
                    border: 2px solid #6366F1;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: 600;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #EEF2FF;
                }
            """)
            btn.clicked.connect(lambda _, f=fmt: QMessageBox.information(self, "Export", f"Export {f} lance..."))
            h_layout.addWidget(btn)
            
        layout.addWidget(header_frame)
        
        # Schedule Table
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
                    stop:0 #6366F1, stop:1 #4F46E5);
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

    def load_schedule(self):
        self.schedule_table.clearContents()
        try:
             if hasattr(self.user, 'groupe_id') and self.user.groupe_id:
                 conn = self.db.get_connection()
                 cursor = conn.cursor()
                 cursor.execute('''
                    SELECT s.date, s.heure_debut, s.titre, s.type_seance, sa.nom, u.nom
                    FROM seances s
                    LEFT JOIN salles sa ON s.salle_id = sa.id
                    LEFT JOIN utilisateurs u ON s.enseignant_id = u.id
                    WHERE s.groupe_id = ?
                 ''', (self.user.groupe_id,))
                 seances = cursor.fetchall()
                 conn.close()
                 
                 def get_row(time_str):
                    if "08" in time_str or "09" in time_str: return 0
                    if "10" in time_str or "11" in time_str: return 1
                    if "12" in time_str or "13" in time_str: return 2
                    if "14" in time_str or "15" in time_str: return 3
                    if "16" in time_str or "17" in time_str: return 4
                    return -1

                 for s in seances:
                    date_str = s[0]
                    qdate = QDate.fromString(date_str, "yyyy-MM-dd")
                    day_idx = qdate.dayOfWeek() - 1 
                    
                    if 0 <= day_idx <= 5:
                        row = get_row(s[1])
                        if row != -1:
                            self.set_course(self.schedule_table, row, day_idx, s[2], s[4] if s[4] else "?", "#6366F1")
        except Exception as e:
            print(f"Student schedule error: {e}")

    def set_course(self, table, row, col, subject, room, color):
        item = QLabel(f"{subject}\n{room}")
        item.setAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366F1, stop:1 #8B5CF6);
            color: white; 
            border-radius: 8px; 
            margin: 4px; 
            padding: 8px;
            font-weight: 600;
            font-size: 12px;
        """)
        table.setCellWidget(row, col, item)

    def create_search_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        # Filters Card - Modern Design
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
        shadow.setColor(QColor(99, 102, 241, 25))
        filters_frame.setGraphicsEffect(shadow)
        
        f_layout = QVBoxLayout(filters_frame)
        f_layout.setContentsMargins(32, 28, 32, 28)
        f_layout.setSpacing(24)
        
        # Section Title
        section_title = QLabel("Rechercher une Salle")
        section_title.setStyleSheet("""
            color: #1E293B; 
            font-size: 20px; 
            font-weight: 700; 
            background: transparent;
        """)
        f_layout.addWidget(section_title)
        
        section_desc = QLabel("Selectionnez une date et une heure pour trouver les salles disponibles")
        section_desc.setStyleSheet("color: #64748B; font-size: 14px; background: transparent;")
        f_layout.addWidget(section_desc)
        
        f_layout.addSpacing(8)
        
        # Input fields row
        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(24)
        
        # Input style
        input_style = """
            QDateEdit, QTimeEdit {
                background-color: #F8FAFC;
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                padding: 14px 18px;
                font-size: 15px;
                color: #1E293B;
                min-width: 200px;
                min-height: 20px;
            }
            QDateEdit:focus, QTimeEdit:focus {
                border: 2px solid #6366F1;
                background: white;
            }
            QDateEdit:hover, QTimeEdit:hover {
                border-color: #818CF8;
            }
        """
        
        label_style = "color: #374151; font-size: 14px; font-weight: 600; background: transparent; margin-bottom: 6px;"
        
        # Date field
        date_container = QVBoxLayout()
        date_container.setSpacing(8)
        date_lbl = QLabel("Date")
        date_lbl.setStyleSheet(label_style)
        self.search_date = QDateEdit(QDate.currentDate())
        self.search_date.setCalendarPopup(True)
        self.search_date.setStyleSheet(input_style)
        self.search_date.setDisplayFormat("dd/MM/yyyy")
        date_container.addWidget(date_lbl)
        date_container.addWidget(self.search_date)
        inputs_layout.addLayout(date_container)
        
        # Time field
        time_container = QVBoxLayout()
        time_container.setSpacing(8)
        time_lbl = QLabel("Heure")
        time_lbl.setStyleSheet(label_style)
        self.search_time = QTimeEdit(QTime.currentTime())
        self.search_time.setStyleSheet(input_style)
        self.search_time.setDisplayFormat("HH:mm")
        time_container.addWidget(time_lbl)
        time_container.addWidget(self.search_time)
        inputs_layout.addLayout(time_container)
        
        inputs_layout.addStretch()
        
        # Search button - Gradient style
        btn_search = QPushButton("  Rechercher")
        btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search.setFixedSize(180, 52)
        btn_search.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366F1, stop:0.5 #8B5CF6, stop:1 #06B6D4);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 14px 28px;
                font-weight: 700;
                font-size: 15px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4F46E5, stop:0.5 #7C3AED, stop:1 #0891B2);
            }
        """)
        btn_search.clicked.connect(self.find_available_rooms)
        
        btn_container = QVBoxLayout()
        btn_container.addSpacing(28)
        btn_container.addWidget(btn_search)
        inputs_layout.addLayout(btn_container)
        
        f_layout.addLayout(inputs_layout)
        
        layout.addWidget(filters_frame)
        
        # Results section header
        results_header = QHBoxLayout()
        results_label = QLabel("Salles Disponibles")
        results_label.setStyleSheet("color: #1E293B; font-size: 18px; font-weight: 700; background: transparent;")
        results_header.addWidget(results_label)
        results_header.addStretch()
        layout.addLayout(results_header)
        
        # Results Table
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
        
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(4)
        self.rooms_table.setHorizontalHeaderLabels(["Nom", "Type", "Capacite", "Etat"])
        self.rooms_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.rooms_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                border-radius: 16px;
                gridline-color: #E2E8F0;
            }
            QTableWidget::item {
                padding: 12px;
                color: #1E293B;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6366F1, stop:1 #4F46E5);
                color: white;
                font-weight: 600;
                font-size: 13px;
                padding: 14px;
                border: none;
            }
        """)
        table_layout.addWidget(self.rooms_table)
        layout.addWidget(table_frame)
        
        return page

    def find_available_rooms(self):
        date_Val = self.search_date.date().toString("yyyy-MM-dd")
        time_Val = self.search_time.time().toString("HH:mm")
        
        try:
             all_rooms = self.db.get_toutes_salles()
             conn = self.db.get_connection()
             cursor = conn.cursor()
             
             query = """
                SELECT DISTINCT salle_id FROM seances 
                WHERE date = ? 
                AND ? BETWEEN heure_debut AND heure_fin
             """
             cursor.execute(query, (date_Val, time_Val))
             occupied_ids = [row[0] for row in cursor.fetchall()]
             conn.close()
             
             available = [r for r in all_rooms if r[0] not in occupied_ids]
             
             self.rooms_table.setRowCount(len(available))
             for i, r in enumerate(available):
                 self.rooms_table.setItem(i, 0, QTableWidgetItem(r[1]))
                 self.rooms_table.setItem(i, 1, QTableWidgetItem(r[3]))
                 self.rooms_table.setItem(i, 2, QTableWidgetItem(str(r[2])))
                 
                 # Status badge
                 status_widget = QLabel("LIBRE")
                 status_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                 status_widget.setStyleSheet("""
                     background: #DCFCE7;
                     color: #15803D;
                     font-weight: 600;
                     font-size: 11px;
                     padding: 6px 12px;
                     border-radius: 12px;
                 """)
                 self.rooms_table.setCellWidget(i, 3, status_widget)
                 self.rooms_table.setRowHeight(i, 50)
                 
        except Exception as e:
            print(f"Room search error: {e}")

    def create_updates_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        # Header Card
        header_card = QFrame()
        header_card.setObjectName("notifHeader")
        header_card.setStyleSheet("""
            QFrame#notifHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366F1, stop:0.5 #8B5CF6, stop:1 #06B6D4);
                border-radius: 20px;
                border: none;
            }
        """)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(32, 28, 32, 28)
        header_layout.setSpacing(8)
        
        header_title = QLabel("Mes Notifications")
        header_title.setStyleSheet("color: white; font-size: 24px; font-weight: 700; background: transparent;")
        header_layout.addWidget(header_title)
        
        header_desc = QLabel("Restez informe des dernieres mises a jour et modifications")
        header_desc.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 14px; background: transparent;")
        header_layout.addWidget(header_desc)
        
        layout.addWidget(header_card)
        
        # Notifications Table Card
        table_frame = QFrame()
        table_frame.setObjectName("notifTable")
        table_frame.setStyleSheet("""
            QFrame#notifTable {
                background-color: white;
                border-radius: 20px;
                border: 1px solid #E2E8F0;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(99, 102, 241, 20))
        table_frame.setGraphicsEffect(shadow)
        
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        notif_list = QTableWidget()
        notif_list.setColumnCount(2)
        notif_list.setHorizontalHeaderLabels(["Date", "Message"])
        notif_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        notif_list.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                border-radius: 20px;
                gridline-color: #F1F5F9;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 16px;
                color: #1E293B;
                border-bottom: 1px solid #F1F5F9;
            }
            QTableWidget::item:selected {
                background-color: #EEF2FF;
                color: #4F46E5;
            }
            QHeaderView::section {
                background: #F8FAFC;
                color: #475569;
                font-weight: 700;
                font-size: 13px;
                padding: 16px 20px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
            }
            QHeaderView::section:first {
                border-top-left-radius: 20px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 20px;
            }
        """)
        
        try:
             conn = self.db.get_connection()
             cursor = conn.cursor()
             cursor.execute('''
                SELECT d.date_debut, u.nom, u.prenom, d.motif
                FROM disponibilites d
                JOIN utilisateurs u ON d.enseignant_id = u.id
                ORDER BY d.id DESC LIMIT 20
             ''')
             rows = cursor.fetchall()
             conn.close()
             
             notif_list.setRowCount(len(rows))
             for i, (date, nom, prenom, motif) in enumerate(rows):
                 notif_list.setItem(i, 0, QTableWidgetItem(date))
                 msg = f"Prof. {nom} {prenom} : {motif}"
                 notif_list.setItem(i, 1, QTableWidgetItem(msg))
                 notif_list.setRowHeight(i, 50)
                 
        except Exception as e:
            pass

        table_layout.addWidget(notif_list)
        layout.addWidget(table_frame)
        return page

    def switch_page(self, page_id):
        titles = {
            "Schedule": "Mon Emploi du Temps",
            "Search": "Trouver une Salle",
            "Updates": "Actualites & Modifications"
        }
        self.page_title.setText(titles.get(page_id, page_id))
        
        mapping = {"Schedule": 0, "Search": 1, "Updates": 2}
        if page_id in mapping:
            self.pages.setCurrentIndex(mapping[page_id])
            
        for pid, btn in self.menu_buttons.items():
            btn.setChecked(pid == page_id)
