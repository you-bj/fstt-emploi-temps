# src/ui/enseignant_window.py
"""
Fenêtre principale de l'enseignant
Fonctionnalités : Emploi du temps, Réservations, Recherche Salles, Indisponibilités
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QStackedWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QComboBox, QDateEdit,
    QTimeEdit, QTextEdit, QMessageBox, QGridLayout,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QColor

from configUI import WINDOW_CONFIG, COLORS, FST_LOGO_IMAGE
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
        # Map other fields if necessary

class EnseignantWindow(QWidget):
    logout_signal = pyqtSignal()

    def __init__(self, user, db):
        super().__init__()
        # Handle tuple vs object
        if isinstance(user, tuple):
            self.user = UserWrapper(user)
        else:
            self.user = user
            
        self.db = db
        
        self.setWindowTitle(WINDOW_CONFIG['enseignant']['title'])
        self.setMinimumSize(1024, 768)
        self.showMaximized()
        self.setStyleSheet(GLOBAL_STYLE)
        
        # Layout principal
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.create_sidebar()
        self.create_content_area()
        self.switch_page("Emploi du Temps")

    def create_sidebar(self):
        """Menu latéral Enseignant - même design que l'espace étudiant"""
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
        
        # Header avec dégradé (comme étudiant)
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
        
        # Boutons du menu (même style que étudiant)
        self.menu_buttons = {}
        menus = [
            ("Emploi du Temps", "Schedule"),
            ("Réserver une séance", "Reservation"),
            ("Indisponibilités", "Unavailability")
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
        
        # Carte utilisateur (comme étudiant)
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
        
        # Avatar "P" (Prof)
        avatar = QLabel("P")
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
        
        user_name = QLabel(f"Prof. {self.user.nom if self.user else 'Enseignant'}")
        user_name.setStyleSheet("color: white; font-size: 14px; font-weight: 600; background: transparent;")
        user_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(user_name)
        
        role_badge = QLabel("Enseignant")
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
        
        # Bouton Déconnexion (même style que étudiant)
        logout = QPushButton("Déconnexion")
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
        self.content.setStyleSheet(f"background-color: {COLORS['bg_light']};")
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(40, 40, 40, 40)
        
        self.page_title = QLabel("Mon Emploi du Temps")
        self.page_title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {COLORS['text_dark']}; margin-bottom: 20px;")
        layout.addWidget(self.page_title)
        
        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_schedule_page())
        self.pages.addWidget(self.create_reservation_page()) 
        self.pages.addWidget(self.create_unavailability_page())
        # Removed create_search_page (Room Search)
        
        layout.addWidget(self.pages)
        self.main_layout.addWidget(self.content)

    def create_schedule_page(self):
        """Page Emploi du temps - même design que l'espace étudiant"""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # Carte en-tête (comme étudiant)
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
        info_label = QLabel(f"<b style='color:#6366F1'>Prof:</b> <span style='color:#1E293B'>{self.user.nom} {self.user.prenom}</span> | <b style='color:#6366F1'>Email:</b> <span style='color:#1E293B'>{getattr(self.user, 'email', '')}</span>")
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setStyleSheet("font-size: 15px; background: transparent;")
        h_layout.addWidget(info_label)
        h_layout.addStretch()
        
        # Boutons Export (même style que étudiant)
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
            btn.clicked.connect(lambda _, f=fmt: QMessageBox.information(self, "Export", f"Export {f} lancé..."))
            h_layout.addWidget(btn)
            
        layout.addWidget(header_frame)
        
        # Table emploi du temps dans un cadre arrondi (comme étudiant)
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
        """Charge l'emploi du temps de l'enseignant"""
        self.schedule_table.clearContents()
        
        # Mapping jours/heures
        days_map = {'Lundi': 0, 'Mardi': 1, 'Mercredi': 2, 'Jeudi': 3, 'Vendredi': 4, 'Samedi': 5}
        # Time mapping (Simplified)
        def get_row(time_str):
            if "08" in time_str or "09" in time_str: return 0
            if "10" in time_str or "11" in time_str: return 1
            if "12" in time_str or "13" in time_str: return 2
            if "14" in time_str or "15" in time_str: return 3
            if "16" in time_str or "17" in time_str: return 4
            return -1

        try:
            # Assuming get_seances_by_enseignant exists in DB
            seances = self.db.get_seances_by_enseignant(self.user.id)
            for s in seances:
                # s: id, titre, type, date, h_debut, h_fin, salle_id...
                # We need day of week from date
                date_str = s[3]
                qdate = QDate.fromString(date_str, "yyyy-MM-dd")
                day_idx = qdate.dayOfWeek() - 1 # 1=Mon, 7=Sun
                
                if 0 <= day_idx <= 5:
                    row = get_row(s[4]) # h_debut
                    if row != -1:
                        # Fetch Room Name
                        salle_name = "Salle ?"
                        if s[6]: # salle_id
                            # Need to fetch salle name. ideally JOIN in get_seances_by_enseignant
                            # Hack: do query or cache.
                            pass
                        
                        txt = f"{s[1]}\n{s[2]}"
                        self.set_course(self.schedule_table, row, day_idx, s[1], s[2], "#6366F1")
                        
        except Exception as e:
            print(f"Schedule load error: {e}")

    def set_course(self, table, row, col, subject, room, color):
        item = QLabel(f"{subject}\n{room}")
        item.setAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setStyleSheet(f"background-color: {color}; color: white; border-radius: 5px; margin: 2px; font-weight: bold;")
        table.setCellWidget(row, col, item)

    def create_reservation_page(self):
        """Page Réserver une séance - design comme l'image (dégradés, cartes blanches, bouton bleu-cyan)"""
        # Styles alignés sur l'image
        page_bg = """
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #EFF6FF, stop:1 #FFFFFF);
        """
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

        header_a_style = """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #A28DF7, stop:1 #D4CBF3);
                border: none;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }
        """
        header_b_style = """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #16C0B9, stop:1 #8AE2DE);
                border: none;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }
        """
        res_label_style = """
            font-family: 'Segoe UI', sans-serif;
            color: #0F172A;
            font-size: 15px;
            font-weight: 600;
        """
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
        btn_res_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5846F0, stop:1 #8B83FC);
                color: #FFFFFF;
                font-weight: 700;
                font-size: 16px;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                min-height: 24px;
            }
            QPushButton:hover { opacity: 0.95; }
            QPushButton:pressed { opacity: 0.9; }
        """

        page = QWidget()
        page.setStyleSheet("QWidget { " + page_bg + " }")
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(24)
        layout.setContentsMargins(32, 24, 32, 24)

        # ----- Option A -----
        opt1_frame = QFrame()
        opt1_frame.setStyleSheet(card_style)
        opt1_frame.setGraphicsEffect(_card_shadow())
        opt1_layout = QVBoxLayout(opt1_frame)
        opt1_layout.setSpacing(0)
        opt1_layout.setContentsMargins(0, 0, 0, 0)

        header_a = QFrame()
        header_a.setStyleSheet(header_a_style)
        header_a.setFixedHeight(72)
        ha_layout = QVBoxLayout(header_a)
        ha_layout.setContentsMargins(24, 16, 24, 16)
        ha_layout.setSpacing(4)
        lbl_opt_a = QLabel("Option A")
        lbl_opt_a.setStyleSheet("color: #6A1B9A; font-size: 18px; font-weight: 700; background: transparent;")
        lbl_sub_a = QLabel("Pour une séance existante")
        lbl_sub_a.setStyleSheet("color: #9C27B0; font-size: 14px; background: transparent;")
        ha_layout.addWidget(lbl_opt_a)
        ha_layout.addWidget(lbl_sub_a)
        opt1_layout.addWidget(header_a)

        form_a = QWidget()
        form_a_layout = QVBoxLayout(form_a)
        form_a_layout.setContentsMargins(24, 24, 24, 24)
        form_a_layout.setSpacing(20)

        grid_a = QGridLayout()
        lbl_grp = QLabel("Groupe")
        lbl_grp.setStyleSheet(res_label_style)
        lbl_grp.setMinimumHeight(24)
        grid_a.addWidget(lbl_grp, 0, 0)
        lbl_seance = QLabel("Séance")
        lbl_seance.setStyleSheet(res_label_style)
        lbl_seance.setMinimumHeight(24)
        grid_a.addWidget(lbl_seance, 0, 1)
        self.res_group_cb = QComboBox()
        self.res_group_cb.addItems(["G1 - Génie Info", "G2 - Génie Info", "G3 - Génie Info", "G1 - Génie Méca"])
        self.res_group_cb.setStyleSheet(res_combo_style)
        self.res_group_cb.setMinimumHeight(44)
        grid_a.addWidget(self.res_group_cb, 1, 0)
        self.res_session_cb = QComboBox()
        self.res_session_cb.addItems(["Lundi 08:30 - Java", "Lundi 10:15 - UML", "Mardi 08:30 - Java", "Mercredi 14:00 - Anglais"])
        self.res_session_cb.setStyleSheet(res_combo_style)
        self.res_session_cb.setMinimumHeight(44)
        grid_a.addWidget(self.res_session_cb, 1, 1)
        form_a_layout.addLayout(grid_a)
        form_a_layout.addSpacing(28)

        btn_layout_a = QHBoxLayout()
        btn_layout_a.addStretch()
        btn_a = QPushButton("Envoyer Demande")
        btn_a.setStyleSheet(btn_res_style)
        btn_a.setMinimumHeight(44)
        btn_a.clicked.connect(
            lambda: QMessageBox.information(self, "Réservation", "Demande envoyée pour une séance existante.")
        )
        btn_layout_a.addWidget(btn_a)
        form_a_layout.addLayout(btn_layout_a)
        opt1_layout.addWidget(form_a)

        layout.addWidget(opt1_frame)

        # ----- Option B -----
        opt2_frame = QFrame()
        opt2_frame.setStyleSheet(card_style)
        opt2_frame.setGraphicsEffect(_card_shadow())
        opt2_layout = QVBoxLayout(opt2_frame)
        opt2_layout.setSpacing(0)
        opt2_layout.setContentsMargins(0, 0, 0, 0)

        header_b = QFrame()
        header_b.setStyleSheet(header_b_style)
        header_b.setFixedHeight(72)
        hb_layout = QVBoxLayout(header_b)
        hb_layout.setContentsMargins(24, 16, 24, 16)
        hb_layout.setSpacing(4)
        lbl_opt_b = QLabel("Option B")
        lbl_opt_b.setStyleSheet("color: #00695C; font-size: 18px; font-weight: 700; background: transparent;")
        lbl_sub_b = QLabel("Créer une nouvelle séance")
        lbl_sub_b.setStyleSheet("color: #004D40; font-size: 14px; font-weight: 500; background: transparent;")
        hb_layout.addWidget(lbl_opt_b)
        hb_layout.addWidget(lbl_sub_b)
        opt2_layout.addWidget(header_b)

        form_b = QWidget()
        form_b_layout = QVBoxLayout(form_b)
        form_b_layout.setContentsMargins(24, 24, 24, 24)
        form_b_layout.setSpacing(20)

        grid_b = QGridLayout()
        for col, (label_text, _) in enumerate([
            ("Date", None),
            ("Heure", None),
            ("Matière", None),
            ("Type", None),
        ]):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(res_label_style)
            lbl.setMinimumHeight(24)
            grid_b.addWidget(lbl, 0, col)
        self.new_res_date = QDateEdit(QDate.currentDate())
        self.new_res_date.setCalendarPopup(True)
        self.new_res_date.setStyleSheet(res_input_style)
        self.new_res_date.setMinimumHeight(44)
        grid_b.addWidget(self.new_res_date, 1, 0)
        self.new_res_time = QTimeEdit(QTime(8, 30))
        self.new_res_time.setStyleSheet(res_input_style)
        self.new_res_time.setMinimumHeight(44)
        grid_b.addWidget(self.new_res_time, 1, 1)
        self.new_res_subject = QComboBox()
        self.new_res_subject.addItems(["Java", "UML", "Anglais"])
        self.new_res_subject.setStyleSheet(res_combo_style)
        self.new_res_subject.setMinimumHeight(44)
        grid_b.addWidget(self.new_res_subject, 1, 2)
        self.new_res_type = QComboBox()
        self.new_res_type.addItems(["Cours", "TP", "TD", "Examen", "Rattrapage"])
        self.new_res_type.setStyleSheet(res_combo_style)
        self.new_res_type.setMinimumHeight(44)
        grid_b.addWidget(self.new_res_type, 1, 3)
        form_b_layout.addLayout(grid_b)

        form_b_layout.addSpacing(32)
        btn_layout_b = QHBoxLayout()
        btn_layout_b.addStretch()
        btn_b = QPushButton("Envoyer Demande")
        btn_b.setStyleSheet(btn_res_style)
        btn_b.setMinimumHeight(44)
        btn_b.clicked.connect(
            lambda: QMessageBox.information(self, "Réservation", "Demande envoyée pour une nouvelle séance.")
        )
        btn_layout_b.addWidget(btn_b)
        form_b_layout.addLayout(btn_layout_b)
        opt2_layout.addWidget(form_b)

        layout.addWidget(opt2_frame)
        layout.addStretch()
        return page
    # Removed perform_session_search


    # Old Search Page Removed


    def create_unavailability_page(self):
        """Page Mes Indisponibilités - même design que l'image (couleurs, polices, mise en page)"""
        from PyQt6.QtWidgets import QCheckBox

        # Styles alignés sur l'image : fond #f4f6f9, titre #343a40, dégradé #E74C3C → #F39C12
        label_style = "font-family: 'Segoe UI', sans-serif; color: #343a40; font-size: 14px; font-weight: 600;"
        input_border = "1px solid #CED4DA"
        input_style = f"""
            font-family: 'Segoe UI', sans-serif;
            background-color: #ffffff;
            border: {input_border};
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

        # Bannière dégradé (rouge-orange #E74C3C → orange #F39C12)
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E74C3C, stop:1 #F39C12);
                border: none;
                border-radius: 10px;
            }
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

        # Carte formulaire (blanc, ombre, coins arrondis 10px)
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

        # Ligne des deux dates (labels au-dessus, champs côte à côte)
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
        self.ab_date_end.setStyleSheet("QDateEdit { " + input_style + " min-width: 180px; }")
        col_end.addWidget(self.ab_date_end)
        date_row.addLayout(col_end)
        date_row.addStretch()
        form_main.addLayout(date_row)

        # Checkbox Journée Entière (carré rouge quand coché)
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
                background: #E74C3C;
                border: 2px solid #E74C3C;
            }
        """)
        self.chk_full_day.setChecked(True)
        form_main.addWidget(self.chk_full_day)

        # Heure Début / Fin (cachés si journée entière)
        self.time_row = QWidget()
        time_layout = QHBoxLayout(self.time_row)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(20)
        self.lbl_h_start = QLabel("Heure Début:")
        self.lbl_h_start.setStyleSheet(label_style)
        self.ab_time_start = QTimeEdit(QTime(8, 30))
        self.ab_time_start.setStyleSheet("QTimeEdit { " + input_style + " }")
        self.lbl_h_end = QLabel("Heure Fin:")
        self.lbl_h_end.setStyleSheet(label_style)
        self.ab_time_end = QTimeEdit(QTime(18, 30))
        self.ab_time_end.setStyleSheet("QTimeEdit { " + input_style + " }")
        time_layout.addWidget(self.lbl_h_start)
        time_layout.addWidget(self.ab_time_start)
        time_layout.addWidget(self.lbl_h_end)
        time_layout.addWidget(self.ab_time_end)
        time_layout.addStretch()
        form_main.addWidget(self.time_row)

        def toggle_time():
            self.time_row.setVisible(not self.chk_full_day.isChecked())
        self.chk_full_day.toggled.connect(toggle_time)
        self.time_row.setVisible(False)

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

        # Bouton centré (même dégradé que la bannière, ombre)
        btn_submit = QPushButton("Signaler Indisponibilité")
        btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_submit.setStyleSheet("""
            QPushButton {
                font-family: 'Segoe UI', sans-serif;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E74C3C, stop:1 #F39C12);
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 12px 28px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #c0392b, stop:1 #d68910);
            }
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

    def save_unavailability(self):
        d_start = self.ab_date_start.date().toString("yyyy-MM-dd")
        d_end = self.ab_date_end.date().toString("yyyy-MM-dd") 
        reason = self.ab_reason.toPlainText()
        
        # Validation Date
        if self.ab_date_start.date() > self.ab_date_end.date():
             QMessageBox.warning(self, "Erreur", "La date de fin doit être postérieure à la date de début.")
             return

        # Construction du motif avec les périodes
        full_msg = reason
        period_msg = ""
        
        # Période de dates
        if d_start != d_end:
            period_msg = f"[Période: {d_start} -> {d_end}]"
        else:
            period_msg = f"[Date: {d_start}]"

        # Période d'heures
        if not self.chk_full_day.isChecked():
            t_start = self.ab_time_start.time().toString("HH:mm")
            t_end = self.ab_time_end.time().toString("HH:mm")
            
            if self.ab_time_start.time() >= self.ab_time_end.time():
                QMessageBox.warning(self, "Erreur", "L'heure de fin doit être postérieure à l'heure de début.")
                return
                
            period_msg += f" [Heure: {t_start} -> {t_end}]"
        else:
            period_msg += " [Journée entière]"
            
        final_motif = f"{period_msg} {full_msg}"
            
        try:
             conn = self.db.get_connection()
             cursor = conn.cursor()
             
             # Tentative d'insertion avec gestion adaptative des colonnes
             try:
                 # Le schéma standard a date_debut ET date_fin (NOT NULL)
                 cursor.execute('''
                    INSERT INTO disponibilites (enseignant_id, date_debut, date_fin, motif) 
                    VALUES (?, ?, ?, ?)
                 ''', (self.user.id, d_start, d_end, final_motif))
             except Exception as e:
                 # Fallback sur 'date' si la colonne 'date_debut' n'existe pas (ancienne version)
                 # Note: Si date_fin manque, cela echouera aussi si on essaie d'inserer date_fin.
                 # On suppose ici un fallback simple.
                 cursor.execute('''
                    INSERT INTO disponibilites (enseignant_id, date, motif) 
                    VALUES (?, ?, ?)
                 ''', (self.user.id, d_start, final_motif))
                 
             conn.commit()
             conn.close()
             QMessageBox.information(self, "Succès", "Votre indisponibilité a été enregistrée avec succès.")
             self.ab_reason.clear()
        except Exception as e:
             QMessageBox.warning(self, "Erreur", f"Erreur lors de l'enregistrement: {e}")

    def switch_page(self, page_id):
        titles = {
            "Schedule": "Mon Emploi du Temps",
            "Reservation": "Réserver une Salle",
            # "Search": "Rechercher une Salle Vide", # Removed
            "Unavailability": "Mes Indisponibilités"
        }
        self.page_title.setText(titles.get(page_id, page_id))
        
        # Correct mapping based on create_content_area order:
        # 0: Schedule, 1: Reservation, 2: Unavailability
        mapping = {"Schedule": 0, "Reservation": 1, "Unavailability": 2}
        
        if page_id in mapping:
            self.pages.setCurrentIndex(mapping[page_id])

        # Titre "Mes Indisponibilités" avec la même couleur que l'image (#343a40)
        if page_id == "Unavailability":
            self.page_title.setStyleSheet("font-family: 'Segoe UI', sans-serif; font-size: 26px; font-weight: bold; color: #343a40; margin-bottom: 20px;")
        else:
            self.page_title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {COLORS['text_dark']}; margin-bottom: 20px;")

        for pid, btn in self.menu_buttons.items():
            btn.setChecked(pid == page_id)

import sys
import os
