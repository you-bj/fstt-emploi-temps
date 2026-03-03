# src/ui/etudiant_window.py
"""
Fenêtre principale de l'étudiant - Modern SaaS Design
MERGED: Visuals from etudiant_window 10 + Full Logic from etudiant_window
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QStackedWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QComboBox, QListWidget,
    QListWidgetItem, QDateEdit, QMessageBox, QGridLayout,
    QGraphicsDropShadowEffect, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QIcon, QPixmap, QColor

from configUI import WINDOW_CONFIG, COLORS, FST_LOGO_IMAGE
from src.services_notification import NotificationService
from src.ui.styles import GLOBAL_STYLE
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
        
        self.setStyleSheet(GLOBAL_STYLE)
        
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
        """Load student's group schedule with enhanced display — includes approved reservations"""
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
                
                # Regular sessions
                cursor.execute('''
                    SELECT s.date, s.heure_debut, s.titre, s.type_seance, sa.nom, u.nom, u.prenom
                    FROM seances s
                    LEFT JOIN salles sa ON s.salle_id = sa.id
                    LEFT JOIN utilisateurs u ON s.enseignant_id = u.id
                    WHERE s.groupe_id = ?
                ''', (self.user.groupe_id,))
                seances = cursor.fetchall()
                
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
                            
                            if session_type == "Cours": color = "#6C5CE7"
                            elif session_type == "TD": color = "#00B894"
                            elif session_type == "TP": color = "#FDCB6E"
                            else: color = "#FD79A8"
                            
                            txt = f"{module}\n📍 {salle}\n👨‍🏫 {prof}\n({session_type})"
                            self.set_course(self.schedule_table, row, day_idx, txt, color)
                
                # Approved reservations for this group (temporary sessions)
                from datetime import datetime as dt
                today = dt.now().strftime("%Y-%m-%d")
                cursor.execute('''
                    SELECT r.date, r.heure_debut, r.motif, sa.nom, u.nom, u.prenom
                    FROM reservations r
                    LEFT JOIN salles sa ON r.salle_id = sa.id
                    LEFT JOIN utilisateurs u ON r.enseignant_id = u.id
                    WHERE r.groupe_id = ? AND r.statut = 'validee' AND r.date >= ?
                ''', (self.user.groupe_id, today))
                reservations = cursor.fetchall()
                
                for r in reservations:
                    date_str = r[0]
                    qdate = QDate.fromString(date_str, "yyyy-MM-dd")
                    day_idx = qdate.dayOfWeek() - 1
                    
                    if 0 <= day_idx <= 5:
                        row = get_row(r[1])
                        if row != -1:
                            motif = r[2] if r[2] else "Réservation"
                            salle = r[3] if r[3] else "?"
                            prof = f"{r[4]} {r[5]}" if r[4] else "?"
                            
                            # Orange/amber color for reserved sessions to distinguish them
                            color = "#E17055"
                            txt = f"📌 {motif}\n📍 {salle}\n👨‍🏫 {prof}\n(Réservation)"
                            self.set_course(self.schedule_table, row, day_idx, txt, color)
                
                conn.close()
        except Exception as e:
            print(f"Student schedule error: {e}")

    def set_course(self, table, row, col, text, color):
        item = QLabel(text)
        item.setAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {color}, stop:1 #A29BFE);
            color: white; 
            border-radius: 8px; 
            margin: 4px; 
            padding: 8px;
            font-weight: 600;
            font-size: 12px;
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
        """Load notifications as styled cards"""
        # Clear existing cards
        while self.notif_cards_layout.count() > 1:
            item = self.notif_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            notifications = self.notification_service.get_notifications_utilisateur(self.user.id)
            
            if not notifications:
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
                
                empty_icon = QLabel("📭")
                empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_icon.setStyleSheet("font-size: 48px; background: transparent; border: none;")
                empty_layout.addWidget(empty_icon)
                
                empty_text = QLabel("Aucune notification pour le moment")
                empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_text.setStyleSheet("font-size: 16px; font-weight: 600; color: #94A3B8; background: transparent; border: none;")
                empty_layout.addWidget(empty_text)
                
                empty_sub = QLabel("Vous serez informé des modifications d'emploi du temps ici")
                empty_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_sub.setStyleSheet("font-size: 13px; color: #CBD5E1; background: transparent; border: none;")
                empty_layout.addWidget(empty_sub)
                
                self.notif_cards_layout.insertWidget(0, empty_frame)
            else:
                for notif in notifications:
                    card = self._create_notif_card(notif)
                    self.notif_cards_layout.insertWidget(self.notif_cards_layout.count() - 1, card)
                    
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

    def _update_search_time_slots(self):
        """Update search time slots — Friday excludes 12:30-14:00"""
        all_slots = ["09:00 - 10:30", "10:45 - 12:15", "12:30 - 14:00", "14:15 - 15:45", "16:00 - 17:30"]
        day_of_week = self.search_date.date().dayOfWeek()  # 5 = Friday
        current = self.search_time_slot.currentText()
        self.search_time_slot.clear()
        if day_of_week == 5:
            slots = [s for s in all_slots if s != "12:30 - 14:00"]
        else:
            slots = all_slots
        self.search_time_slot.addItems(slots)
        idx = self.search_time_slot.findText(current)
        if idx >= 0:
            self.search_time_slot.setCurrentIndex(idx)

    def find_available_rooms(self):
        """Room search logic - fixed to match by day-of-week across all seances"""
        date_val = self.search_date.date().toString("yyyy-MM-dd")
        
        # Get time slot from dropdown
        time_text = self.search_time_slot.currentText()
        try:
            parts = time_text.split(" - ")
            heure_debut = parts[0].strip()
            heure_fin = parts[1].strip()
        except (IndexError, AttributeError):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un créneau horaire valide.")
            return
        
        # Get day of week for the selected date (0=Monday … 6=Sunday)
        from datetime import datetime
        try:
            date_obj = datetime.strptime(date_val, "%Y-%m-%d")
            day_of_week = date_obj.weekday()  # 0=Mon,1=Tue,...
        except ValueError:
            return
        
        try:
            all_rooms = self.db.get_toutes_salles()
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Find all dates in seances that are the same day-of-week
            cursor.execute("SELECT DISTINCT date FROM seances")
            all_dates = [row[0] for row in cursor.fetchall()]
            matching_dates = []
            for d in all_dates:
                try:
                    dt = datetime.strptime(d, "%Y-%m-%d")
                    if dt.weekday() == day_of_week:
                        matching_dates.append(d)
                except ValueError:
                    continue
            
            occupied_ids = set()
            
            # Check seances for any matching day-of-week
            if matching_dates:
                placeholders = ",".join(["?"] * len(matching_dates))
                cursor.execute(f"""
                    SELECT DISTINCT salle_id FROM seances 
                    WHERE date IN ({placeholders})
                    AND ((heure_debut < ? AND heure_fin > ?) OR 
                         (heure_debut < ? AND heure_fin > ?) OR
                         (heure_debut >= ? AND heure_fin <= ?))
                """, matching_dates + [heure_fin, heure_debut, 
                      heure_fin, heure_debut, heure_debut, heure_fin])
                occupied_ids.update(row[0] for row in cursor.fetchall())
            
            # Also check approved reservations for the exact date
            cursor.execute("""
                SELECT DISTINCT salle_id FROM reservations 
                WHERE date = ? AND statut = 'validee'
                AND ((heure_debut < ? AND heure_fin > ?) OR 
                     (heure_debut < ? AND heure_fin > ?) OR
                     (heure_debut >= ? AND heure_fin <= ?))
            """, (date_val, heure_fin, heure_debut, 
                  heure_fin, heure_debut, heure_debut, heure_fin))
            occupied_ids.update(row[0] for row in cursor.fetchall())
            
            conn.close()
            
            free_rooms = [r for r in all_rooms if r[0] not in occupied_ids]
            busy_rooms = [r for r in all_rooms if r[0] in occupied_ids]
            
            total = len(free_rooms) + len(busy_rooms)
            self.rooms_table.setRowCount(total)
            
            row_idx = 0
            # Show free rooms first
            for r in free_rooms:
                self.rooms_table.setItem(row_idx, 0, QTableWidgetItem(r[1]))
                self.rooms_table.setItem(row_idx, 1, QTableWidgetItem(r[3] if len(r) > 3 else ""))
                self.rooms_table.setItem(row_idx, 2, QTableWidgetItem(str(r[2])))
                
                status_widget = QLabel("✅ LIBRE")
                status_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                status_widget.setStyleSheet("background: #DCFCE7; color: #15803D; font-weight: 600; font-size: 11px; padding: 6px 12px; border-radius: 12px;")
                self.rooms_table.setCellWidget(row_idx, 3, status_widget)
                self.rooms_table.setRowHeight(row_idx, 50)
                row_idx += 1
            
            # Then show occupied rooms
            for r in busy_rooms:
                self.rooms_table.setItem(row_idx, 0, QTableWidgetItem(r[1]))
                self.rooms_table.setItem(row_idx, 1, QTableWidgetItem(r[3] if len(r) > 3 else ""))
                self.rooms_table.setItem(row_idx, 2, QTableWidgetItem(str(r[2])))
                
                status_widget = QLabel("❌ OCCUPÉE")
                status_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                status_widget.setStyleSheet("background: #FEE2E2; color: #DC2626; font-weight: 600; font-size: 11px; padding: 6px 12px; border-radius: 12px;")
                self.rooms_table.setCellWidget(row_idx, 3, status_widget)
                self.rooms_table.setRowHeight(row_idx, 50)
                row_idx += 1
                
        except Exception as e:
            print(f"Room search error: {e}")

    # ═══════════════════════════════════════════════════════════
    # MODERN UI CONSTRUCTION
    # ═══════════════════════════════════════════════════════════

    def create_sidebar(self):
        """Modern Sidebar - Dark gradient with glassmorphism"""
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
        
        # Header with gradient
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
                    margin: 4px 16px;
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
        
        # User info card
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
        
        # Avatar
        avatar = QLabel("E")
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
        
        user_name = QLabel(f"{self.user.nom} {self.user.prenom}")
        user_name.setStyleSheet("color: white; font-size: 14px; font-weight: 600; background: transparent;")
        user_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(user_name)
        
        role_badge = QLabel("Etudiant")
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
        
        # Logout
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
        
        self.page_title = QLabel("Emploi du Temps")
        self.page_title.setStyleSheet(f"font-size: 32px; font-weight: 700; color: {COLORS['text_dark']}; background: transparent;")
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
        
        info_label = QLabel(f"<b style='color:{COLORS['primary']}'>Étudiant:</b> <span style='color:{COLORS['text_dark']}'>{self.user.nom} {self.user.prenom}</span> | <b style='color:{COLORS['primary']}'>Email:</b> <span style='color:{COLORS['text_dark']}'>{self.user.email}</span>")
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setStyleSheet("font-size: 15px; background: transparent;")
        h_layout.addWidget(info_label)
        h_layout.addStretch()
        
        for fmt in ["PDF", "Excel", "Image"]:
            btn = QPushButton(f"Exporter {fmt}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: white;
                    color: {COLORS['primary']};
                    border: 2px solid {COLORS['primary']};
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: 600;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background: rgba(108, 92, 231, 0.08);
                }}
            """)
            btn.clicked.connect(lambda _, f=fmt: self.export_schedule(f))
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
        self.schedule_table.setVerticalHeaderLabels(["08:30 - 10:00", "10:15 - 11:45", "12:00 - 13:30", "13:45 - 15:15", "15:30 - 17:00"])
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
        shadow.setColor(QColor(108, 92, 231, 25))
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
        
        section_desc = QLabel("Sélectionnez une date et un créneau pour trouver les salles disponibles")
        section_desc.setStyleSheet("color: #64748B; font-size: 14px; background: transparent;")
        f_layout.addWidget(section_desc)
        
        f_layout.addSpacing(8)
        
        # Input fields row
        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(24)
        
        # Input style
        input_style = """
            QDateEdit, QComboBox {
                background-color: #F8FAFC;
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                padding: 14px 18px;
                font-size: 15px;
                color: #1E293B;
                min-width: 200px;
                min-height: 20px;
            }
            QDateEdit:focus, QComboBox:focus {
                border: 2px solid #6C5CE7;
                background: white;
            }
            QDateEdit:hover, QComboBox:hover {
                border-color: #A29BFE;
            }
        """
        
        label_style = "color: #374151; font-size: 14px; font-weight: 600; background: transparent; margin-bottom: 6px;"
        
        # Date field
        date_container = QVBoxLayout()
        date_container.setSpacing(8)
        date_lbl = QLabel("📅 Date")
        date_lbl.setStyleSheet(label_style)
        self.search_date = QDateEdit(QDate.currentDate())
        self.search_date.setCalendarPopup(True)
        self.search_date.setStyleSheet(input_style)
        self.search_date.setDisplayFormat("dd/MM/yyyy")
        date_container.addWidget(date_lbl)
        date_container.addWidget(self.search_date)
        inputs_layout.addLayout(date_container)
        
        # Time slot field
        time_container = QVBoxLayout()
        time_container.setSpacing(8)
        time_lbl = QLabel("🕐 Créneau")
        time_lbl.setStyleSheet(label_style)
        self.search_time_slot = QComboBox()
        self._update_search_time_slots()
        self.search_date.dateChanged.connect(self._update_search_time_slots)
        self.search_time_slot.setStyleSheet(input_style)
        time_container.addWidget(time_lbl)
        time_container.addWidget(self.search_time_slot)
        inputs_layout.addLayout(time_container)
        
        inputs_layout.addStretch()
        
        # Search button - Gradient style
        btn_search = QPushButton("  Rechercher")
        btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search.setFixedSize(180, 52)
        btn_search.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6C5CE7, stop:0.5 #FD79A8, stop:1 #00CEC9);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 14px 28px;
                font-weight: 700;
                font-size: 15px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5A4BD1, stop:0.5 #E84393, stop:1 #00A8A3);
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
        results_label.setStyleSheet(f"color: {COLORS['text_dark']}; font-size: 18px; font-weight: 700; background: transparent;")
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
        self.rooms_table.setHorizontalHeaderLabels(["Nom", "Type", "Capacité", "État"])
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
                    stop:0 #6C5CE7, stop:1 #5A4BD1);
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

    def create_updates_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 8, 0, 24)
        
        # Header Card - Gradient
        header_card = QFrame()
        header_card.setObjectName("notifHeader")
        header_card.setStyleSheet("""
            QFrame#notifHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6C5CE7, stop:0.5 #FD79A8, stop:1 #00CEC9);
                border-radius: 20px;
                border: none;
            }
        """)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(32, 28, 32, 28)
        
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(8)
        
        header_title = QLabel("🔔  Mes Notifications")
        header_title.setStyleSheet("color: white; font-size: 24px; font-weight: 700; background: transparent;")
        header_text_layout.addWidget(header_title)
        
        header_desc = QLabel("Restez informé des dernières mises à jour et modifications")
        header_desc.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 14px; background: transparent;")
        header_text_layout.addWidget(header_desc)
        
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()
        
        btn_read = QPushButton("✓  Tout marquer comme lu")
        btn_read.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_read.setFixedHeight(42)
        btn_read.setMinimumWidth(200)
        btn_read.setStyleSheet("""
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
        btn_read.clicked.connect(self.mark_all_read)
        header_layout.addWidget(btn_read)
        
        layout.addWidget(header_card)
        
        # Notifications scroll area with cards
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
        
        self.notif_container = QWidget()
        self.notif_container.setStyleSheet("background: transparent;")
        self.notif_cards_layout = QVBoxLayout(self.notif_container)
        self.notif_cards_layout.setSpacing(12)
        self.notif_cards_layout.setContentsMargins(0, 0, 8, 0)
        self.notif_cards_layout.addStretch()
        
        scroll.setWidget(self.notif_container)
        layout.addWidget(scroll)
        
        return page

    def _create_notif_card(self, notif):
        """Create a styled notification card"""
        type_config = {
            'info': {'icon': 'ℹ️', 'color': '#3B82F6', 'bg': '#EFF6FF', 'label': 'Information'},
            'modification': {'icon': '✏️', 'color': '#F59E0B', 'bg': '#FFFBEB', 'label': 'Modification'},
            'annulation': {'icon': '❌', 'color': '#EF4444', 'bg': '#FEF2F2', 'label': 'Annulation'},
            'alerte': {'icon': '⚠️', 'color': '#F97316', 'bg': '#FFF7ED', 'label': 'Alerte'},
            'rappel': {'icon': '🔔', 'color': '#8B5CF6', 'bg': '#F5F3FF', 'label': 'Rappel'},
        }
        notif_type = notif.get('type', 'info')
        cfg = type_config.get(notif_type, type_config['info'])
        is_read = notif.get('lue', True)
        
        card = QFrame()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        unread_border = f"border-left: 4px solid {cfg['color']};" if not is_read else "border-left: 4px solid transparent;"
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {'#FFFFFF' if is_read else cfg['bg']};
                border-radius: 14px;
                {unread_border}
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
        shadow.setBlurRadius(16 if not is_read else 10)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 18 if not is_read else 10))
        card.setGraphicsEffect(shadow)
        
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(16)
        
        # Icon circle
        icon_frame = QFrame()
        icon_frame.setFixedSize(48, 48)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {cfg['color']}18;
                border-radius: 24px;
                border: 2px solid {cfg['color']}30;
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
        content_layout.setSpacing(6)
        
        # Title row with type badge
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        
        titre = notif.get('titre', '')
        title_label = QLabel(titre)
        title_weight = "700" if not is_read else "600"
        title_label.setStyleSheet(f"""
            font-family: 'Segoe UI', sans-serif;
            font-size: 15px; font-weight: {title_weight};
            color: #1E293B; background: transparent; border: none;
        """)
        title_row.addWidget(title_label)
        
        type_badge = QLabel(cfg['label'])
        type_badge.setFixedHeight(24)
        type_badge.setStyleSheet(f"""
            background-color: {cfg['color']}18;
            color: {cfg['color']};
            font-size: 11px; font-weight: 700;
            padding: 2px 10px;
            border-radius: 12px;
            border: 1px solid {cfg['color']}30;
        """)
        title_row.addWidget(type_badge)
        title_row.addStretch()
        content_layout.addLayout(title_row)
        
        # Message
        message = notif.get('message', '')
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"""
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px; color: #64748B;
            background: transparent; border: none;
            line-height: 1.4;
        """)
        content_layout.addWidget(msg_label)
        
        card_layout.addLayout(content_layout, 1)
        
        # Right side - date & unread dot
        right_layout = QVBoxLayout()
        right_layout.setSpacing(8)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        date_str = str(notif.get('date_creation', ''))
        if len(date_str) > 16:
            date_str = date_str[:16]
        date_label = QLabel(date_str)
        date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        date_label.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 11px; color: #94A3B8;
            background: transparent; border: none;
        """)
        right_layout.addWidget(date_label)
        
        if not is_read:
            dot = QFrame()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"""
                QFrame {{
                    background-color: {cfg['color']};
                    border-radius: 5px;
                    border: none;
                }}
            """)
            dot_container = QHBoxLayout()
            dot_container.addStretch()
            dot_container.addWidget(dot)
            right_layout.addLayout(dot_container)
        
        right_layout.addStretch()
        card_layout.addLayout(right_layout)
        
        return card

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