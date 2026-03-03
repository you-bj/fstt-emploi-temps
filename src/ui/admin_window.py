# src/ui/admin_window.py
"""
Modern Admin Dashboard - Professional UI with Charts and Icons
MERGED: Visuals from admin_window10 + Full Logic from admin_window
"""

import os
import math
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QStackedWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QGridLayout,
    QGraphicsDropShadowEffect, QSizePolicy, QComboBox, QFormLayout,
    QSpinBox, QDateEdit, QFileDialog, QProgressDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QSize, QRectF, pyqtSignal, QPropertyAnimation, QEasingCurve, QDate
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QBrush, QPen, QFont, QLinearGradient, QPainterPath

# Import configs
from configUI import WINDOW_CONFIG, COLORS, FST_LOGO_IMAGE
from config import FILIERES_LST, FILIERES_MST, FILIERES_INGENIEUR, MATIERES_COMPLETES
from src.ui.styles import (
    GLOBAL_STYLE, SIDEBAR_STYLE, SIDEBAR_BUTTON_STYLE, 
    SIDEBAR_USER_INFO_STYLE, SIDEBAR_HEADER_STYLE,
    CARD_STYLE, CARD_TITLE_STYLE, CARD_VALUE_STYLE,
    PRIMARY_BUTTON_STYLE, SECONDARY_BUTTON_STYLE,
    SUCCESS_BUTTON_STYLE, DANGER_BUTTON_STYLE,
    TABLE_STYLE, SOBER_BUTTON_STYLE, CHART_CONTAINER_STYLE,
    CHART_TITLE_STYLE, PAGE_TITLE_STYLE, LOGOUT_BUTTON_STYLE
)

# ═══════════════════════════════════════════════════════════
# 1. MODERN VISUAL COMPONENTS (From Window 10)
# ═══════════════════════════════════════════════════════════

class ModernDonutChart(QWidget):
    """Beautiful donut chart with gradient colors and animations"""
    
    def __init__(self, data, title="Chart"):
        super().__init__()
        self.data = data  # List of tuples: (label, value, color)
        self.chart_title = title
        self.setMinimumSize(350, 300)
        self.hovered_segment = -1
        self.setMouseTracking(True)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Background
        painter.fillRect(0, 0, w, h, QColor("#FFFFFF"))
        
        # Draw rounded rectangle border
        painter.setPen(QPen(QColor(COLORS.get('border', '#E2E8F0')), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(1, 1, w-2, h-2, 20, 20)
        
        # Title
        title_font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(COLORS.get('text_dark', '#1E293B')))
        painter.drawText(24, 36, self.chart_title)
        
        if not self.data or sum([v for _, v, _ in self.data]) == 0:
            painter.setPen(QColor(COLORS.get('text_light', '#888')))
            msg_font = QFont("Segoe UI", 12)
            painter.setFont(msg_font)
            painter.drawText(QRectF(0, 60, w, h-60), Qt.AlignmentFlag.AlignCenter, "Aucune donnée")
            return
        
        # Chart dimensions
        chart_size = min(w - 80, h - 120)
        chart_x = (w - chart_size) // 2
        chart_y = 60
        
        # Draw donut
        total = sum([v for _, v, _ in self.data])
        start_angle = 90 * 16
        
        for i, (label, value, color) in enumerate(self.data):
            if value <= 0: continue
            span_angle = int((value / total) * 360 * 16)
            painter.setPen(Qt.PenStyle.NoPen)
            gradient = QLinearGradient(chart_x, chart_y, chart_x + chart_size, chart_y + chart_size)
            base_color = QColor(color)
            lighter_color = base_color.lighter(115)
            gradient.setColorAt(0, lighter_color)
            gradient.setColorAt(1, base_color)
            painter.setBrush(QBrush(gradient))
            painter.drawPie(int(chart_x), int(chart_y), int(chart_size), int(chart_size), int(start_angle), int(span_angle))
            start_angle += span_angle
        
        # Hole
        hole_size = chart_size * 0.55
        hole_x = chart_x + (chart_size - hole_size) / 2
        hole_y = chart_y + (chart_size - hole_size) / 2
        painter.setBrush(QColor("#FFFFFF"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(hole_x, hole_y, hole_size, hole_size))
        
        # Center text
        center_font = QFont("Segoe UI", 20, QFont.Weight.Bold)
        painter.setFont(center_font)
        painter.setPen(QColor(COLORS.get('text_dark', '#1E293B')))
        painter.drawText(QRectF(hole_x, hole_y, hole_size, hole_size), Qt.AlignmentFlag.AlignCenter, str(int(total)))
        
        # Legend
        legend_y = chart_y + chart_size + 20
        legend_x = 24
        legend_font = QFont("Segoe UI", 10)
        painter.setFont(legend_font)
        for i, (label, value, color) in enumerate(self.data):
            if i >= 4: break
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(legend_x + (i * (w-48) / 4)), int(legend_y), 10, 10)
            painter.setPen(QColor(COLORS.get('text_medium', '#666')))
            painter.drawText(int(legend_x + 16 + (i * (w-48) / 4)), int(legend_y + 9), f"{label}: {value}")


class ModernBarChart(QWidget):
    """Gradient bar chart with smooth design"""
    
    def __init__(self, data, title="Statistics"):
        super().__init__()
        self.data = data
        self.chart_title = title
        self.setMinimumSize(400, 300)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        painter.fillRect(0, 0, w, h, QColor("#FFFFFF"))
        painter.setPen(QPen(QColor(COLORS.get('border', '#E2E8F0')), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(1, 1, w-2, h-2, 20, 20)
        
        title_font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(COLORS.get('text_dark', '#1E293B')))
        painter.drawText(24, 36, self.chart_title)
        
        margin_left, margin_right, margin_top, margin_bottom = 50, 30, 60, 50
        graph_w = w - margin_left - margin_right
        graph_h = h - margin_top - margin_bottom
        
        if not self.data:
            return
            
        max_val = max([v for _, v in self.data]) if self.data else 10
        max_val = max(max_val, 5)
        
        painter.setPen(QPen(QColor(COLORS.get('border_light', '#eee')), 1, Qt.PenStyle.DashLine))
        grid_lines = 5
        for i in range(grid_lines + 1):
            y = margin_top + (graph_h * i / grid_lines)
            painter.drawLine(int(margin_left), int(y), int(w - margin_right), int(y))
            label_font = QFont("Segoe UI", 9)
            painter.setFont(label_font)
            painter.setPen(QColor(COLORS.get('text_light', '#888')))
            val = int(max_val * (grid_lines - i) / grid_lines)
            painter.drawText(int(margin_left - 35), int(y + 4), str(val))
        
        count = len(self.data)
        bar_width = (graph_w - 20) / count - 20
        bar_width = min(bar_width, 60)
        
        colors = [
            (COLORS.get('primary', '#6366F1'), COLORS.get('secondary', '#06B6D4')),
            (COLORS.get('card_cyan', '#06B6D4'), COLORS.get('card_emerald', '#10B981')),
            (COLORS.get('card_purple', '#8B5CF6'), COLORS.get('primary', '#6366F1')),
            (COLORS.get('card_amber', '#F59E0B'), COLORS.get('card_rose', '#F43F5E')),
            (COLORS.get('card_emerald', '#10B981'), COLORS.get('card_cyan', '#06B6D4')),
        ]
        
        for i, (label, value) in enumerate(self.data):
            x = margin_left + 20 + (i * (graph_w - 20) / count) + ((graph_w - 20) / count - bar_width) / 2
            if value > 0:
                bar_h = (value / max_val) * graph_h
                y = margin_top + graph_h - bar_h
                color_pair = colors[i % len(colors)]
                gradient = QLinearGradient(x, y, x, margin_top + graph_h)
                gradient.setColorAt(0, QColor(color_pair[0]))
                gradient.setColorAt(1, QColor(color_pair[1]))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(gradient))
                path = QPainterPath()
                radius = 8
                path.moveTo(x, margin_top + graph_h)
                path.lineTo(x, y + radius)
                path.quadTo(x, y, x + radius, y)
                path.lineTo(x + bar_width - radius, y)
                path.quadTo(x + bar_width, y, x + bar_width, y + radius)
                path.lineTo(x + bar_width, margin_top + graph_h)
                path.closeSubpath()
                painter.drawPath(path)
                
                value_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
                painter.setFont(value_font)
                painter.setPen(QColor(color_pair[0]))
                painter.drawText(QRectF(x, y - 25, bar_width, 20), Qt.AlignmentFlag.AlignCenter, str(value))
            
            label_font = QFont("Segoe UI", 10)
            painter.setFont(label_font)
            painter.setPen(QColor(COLORS.get('text_medium', '#666')))
            painter.drawText(QRectF(x - 10, margin_top + graph_h + 10, bar_width + 20, 30), Qt.AlignmentFlag.AlignCenter, label)


class ModernStatCard(QFrame):
    """Beautiful stat card with icon and gradient accent"""
    
    def __init__(self, title, value, icon_text, accent_color, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.icon_text = icon_text
        self.accent_color = accent_color
        self.is_hovered = False
        
        self.setMinimumSize(200, 140)
        self.setMaximumHeight(160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        icon_frame = QFrame()
        icon_frame.setFixedSize(56, 56)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {self.accent_color}, stop:1 {QColor(self.accent_color).darker(120).name()});
                border-radius: 14px;
            }}
        """)
        
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel(self.icon_text)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("QLabel { color: white; font-size: 24px; font-weight: bold; }")
        icon_layout.addWidget(icon_label)
        layout.addWidget(icon_frame)
        
        text_container = QVBoxLayout()
        text_container.setSpacing(4)
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet(f"QLabel {{ color: {COLORS.get('text_light', '#888')}; font-size: 13px; font-weight: 500; letter-spacing: 0.5px; }}")
        self.value_label = QLabel(str(self.value))
        self.value_label.setStyleSheet(f"QLabel {{ color: {COLORS.get('text_dark', '#1E293B')}; font-size: 32px; font-weight: bold; }}")
        text_container.addWidget(self.title_label)
        text_container.addWidget(self.value_label)
        text_container.addStretch()
        layout.addLayout(text_container)
        layout.addStretch()
        self.update_style()
        
    def update_style(self):
        border_color = COLORS.get('border', '#E2E8F0')
        if self.is_hovered:
            self.setStyleSheet(f"QFrame {{ background-color: white; border: 2px solid {self.accent_color}; border-radius: 20px; }}")
        else:
            self.setStyleSheet(f"QFrame {{ background-color: white; border: 1px solid {border_color}; border-radius: 20px; border-left: 4px solid {self.accent_color}; }}")
    
    def enterEvent(self, event):
        self.is_hovered = True
        self.update_style()
        
    def leaveEvent(self, event):
        self.is_hovered = False
        self.update_style()
    
    def set_value(self, value):
        self.value = value
        self.value_label.setText(str(value))


class UserWrapper:
    def __init__(self, user_tuple):
        self.id = user_tuple[0] if len(user_tuple) > 0 else 0
        self.nom = user_tuple[1] if len(user_tuple) > 1 else "Inconnu"
        self.prenom = user_tuple[2] if len(user_tuple) > 2 else ""
        self.email = user_tuple[3] if len(user_tuple) > 3 else ""


# ═══════════════════════════════════════════════════════════
# 2. MAIN ADMIN WINDOW LOGIC + UI
# ═══════════════════════════════════════════════════════════

class AdminWindow(QWidget):
    logout_signal = pyqtSignal()

    def __init__(self, user, db):
        super().__init__()
        
        if isinstance(user, tuple):
            self.user = UserWrapper(user)
        else:
            self.user = user
            
        self.db = db
        
        self.setWindowTitle("UniSchedule-Gestion d'emploi du Temps FSTT")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(GLOBAL_STYLE)
        
        # Load logic data
        self.reservations_data = []
        self.load_reservations_from_db()

        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.create_sidebar()
        self.create_content_area()
        self.switch_page("Dashboard")
        
    # ═══════════════════════════════════════════════════════════
    # BUSINESS LOGIC (PRESERVED FROM ORIGINAL)
    # ═══════════════════════════════════════════════════════════

    def calculate_stats(self):
        """Calculate dynamic statistics using logic from admin_window.py"""
        stats = {}
        try:
            stats['enseignants'] = len(self.db.get_tous_utilisateurs('enseignant'))
            stats['etudiants'] = len(self.db.get_tous_utilisateurs('etudiant'))
        except:
            stats['enseignants'] = 0
            stats['etudiants'] = 0
            
        # From config
        nb_filieres = len(FILIERES_LST) + len(FILIERES_MST) + len(FILIERES_INGENIEUR)
        stats['filieres'] = nb_filieres
        
        nb_matieres = 0
        for prog, subjects in MATIERES_COMPLETES.items():
            nb_matieres += len(subjects)
        stats['matieres'] = nb_matieres
        
        return stats

    def refresh_dashboard(self):
        """Update dashboard stats and charts"""
        stats = self.calculate_stats()
        if hasattr(self, 'stat_cards'):
            self.stat_cards['Enseignants'].set_value(stats['enseignants'])
            self.stat_cards['Étudiants'].set_value(stats['etudiants'])
            self.stat_cards['Filières'].set_value(stats['filieres'])
            self.stat_cards['Matières'].set_value(stats['matieres'])
        # Refresh Volume Horaire chart with real data
        if hasattr(self, 'volume_chart'):
            new_data = self._calculate_volume_horaire()
            self.volume_chart.data = new_data
            self.volume_chart.update()

    def _calculate_volume_horaire(self):
        """Calculate total hours per day of week from actual seances in DB."""
        day_names = ["Lun", "Mar", "Mer", "Jeu", "Ven"]
        day_hours = {d: 0.0 for d in day_names}
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            # Sum hours per day of week (strftime %w: 0=Sun, 1=Mon, ..., 5=Fri)
            cursor.execute('''
                SELECT strftime('%w', date) as dow,
                       SUM((CAST(substr(heure_fin,1,2) AS REAL)*60 + CAST(substr(heure_fin,4,2) AS REAL)
                           - CAST(substr(heure_debut,1,2) AS REAL)*60 - CAST(substr(heure_debut,4,2) AS REAL)) / 60.0) as total_h
                FROM seances
                GROUP BY dow
            ''')
            dow_map = {'1': 'Lun', '2': 'Mar', '3': 'Mer', '4': 'Jeu', '5': 'Ven'}
            for row in cursor.fetchall():
                label = dow_map.get(str(row[0]))
                if label:
                    day_hours[label] = round(row[1], 1)
            conn.close()
        except Exception as e:
            print(f"Volume horaire error: {e}")
        return [(d, day_hours[d]) for d in day_names]

    def _calculate_occupation_stats(self):
        """Calculate real-time room occupation statistics for the dashboard."""
        from datetime import datetime as dt
        
        today = dt.now().strftime("%Y-%m-%d")
        time_slots = [
            ("09:00-10:30", "09:00", "10:30"),
            ("10:45-12:15", "10:45", "12:15"),
            ("12:30-14:00", "12:30", "14:00"),
            ("14:15-15:45", "14:15", "15:45"),
            ("16:00-17:30", "16:00", "17:30"),
        ]
        
        result = {
            'slots': [],
            'total_rate': 0,
            'total_rooms': 0,
            'sessions_today': 0,
            'busiest_slot': "—",
            'pending_reservations': 0,
            'stats_date': today,
        }
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            salles = self.db.get_toutes_salles()
            total_rooms = len(salles)
            result['total_rooms'] = total_rooms
            
            if total_rooms == 0:
                return result
            
            # Smart date: if no sessions today, find nearest date with data
            cursor.execute("SELECT COUNT(*) FROM seances WHERE date = ?", (today,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("SELECT date FROM seances WHERE date >= ? ORDER BY date ASC LIMIT 1", (today,))
                row = cursor.fetchone()
                if not row:
                    cursor.execute("SELECT date FROM seances ORDER BY date DESC LIMIT 1")
                    row = cursor.fetchone()
                if row:
                    today = row[0]
                    result['stats_date'] = today
            
            # Sessions on target date
            cursor.execute("SELECT COUNT(*) FROM seances WHERE date = ?", (today,))
            result['sessions_today'] = cursor.fetchone()[0]
            
            # Pending reservations
            cursor.execute("SELECT COUNT(*) FROM reservations WHERE statut = 'en_attente'")
            result['pending_reservations'] = cursor.fetchone()[0]
            
            max_occ = 0
            busiest = "—"
            total_occupied_sum = 0
            
            for slot_name, h_debut, h_fin in time_slots:
                # Count occupied rooms for this slot today
                cursor.execute('''
                    SELECT COUNT(DISTINCT salle_id) FROM seances
                    WHERE date = ?
                    AND ((heure_debut < ? AND heure_fin > ?) OR
                         (heure_debut < ? AND heure_fin > ?) OR
                         (heure_debut >= ? AND heure_fin <= ?))
                ''', (today, h_fin, h_debut, h_fin, h_debut, h_debut, h_fin))
                occ_seances = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT COUNT(DISTINCT salle_id) FROM reservations
                    WHERE date = ? AND statut = 'validee'
                    AND ((heure_debut < ? AND heure_fin > ?) OR
                         (heure_debut < ? AND heure_fin > ?) OR
                         (heure_debut >= ? AND heure_fin <= ?))
                ''', (today, h_fin, h_debut, h_fin, h_debut, h_debut, h_fin))
                occ_res = cursor.fetchone()[0]
                
                occupied = occ_seances + occ_res
                rate = min(100, (occupied / total_rooms) * 100) if total_rooms else 0
                result['slots'].append((slot_name, round(rate, 1)))
                total_occupied_sum += occupied
                
                if occupied > max_occ:
                    max_occ = occupied
                    busiest = slot_name
            
            num_slots = len(time_slots)
            result['total_rate'] = (total_occupied_sum / (total_rooms * num_slots)) * 100 if total_rooms else 0
            result['busiest_slot'] = busiest
            
            conn.close()
        except Exception as e:
            print(f"Occupation stats error: {e}")
        
        return result

    def load_reservations_from_db(self):
        """Load reservations logic from admin_window.py"""
        self.reservations_data = []
        try:
            # Rattrapages
            demandes = self.db.get_demandes_en_attente()
            for d in demandes:
                self.reservations_data.append({
                    'db_id': d[0],
                    'type': 'rattrapage',
                    'enseignant_id': d[1],
                    'groupe_id': d[2],
                    'salle_id': d[3],
                    'date': d[4],
                    'heure_debut': d[5],
                    'heure_fin': d[6],
                    'prof': f"{d[13]} {d[12]}",
                    'salle': d[14],
                    'motif': f"Rattrapage: {d[7]}" if d[7] else "Rattrapage",
                    'groupe': d[15]
                })
            
            # Reservations
            reservations = self.db.get_reservations_by_statut('en_attente')
            for r in reservations:
                ens = self.db.get_utilisateur_by_id(r[1])
                salle = self.db.get_salle_by_id(r[2])
                self.reservations_data.append({
                    'db_id': r[0],
                    'type': 'reservation',
                    'enseignant_id': r[1],
                    'salle_id': r[2],
                    'groupe_id': r[3],
                    'date': r[4],
                    'heure_debut': r[5] if len(r) > 5 else None,
                    'heure_fin': r[6] if len(r) > 6 else None,
                    'prof': f"{ens[2]} {ens[1]}" if ens else "Inconnu",
                    'salle': salle[1] if salle else "Inconnue",
                    'motif': r[8] if len(r) > 8 and r[8] else "Réservation",
                    'groupe': r[10] if len(r) > 10 else None
                })
        except Exception as e:
            print(f"Erreur chargement réservations: {e}")

    def run_import(self, type_import):
        """Execute import via ImportManager"""
        from src.import_manager import ImportManager
        file_path, _ = QFileDialog.getOpenFileName(self, f"Sélectionner le fichier {type_import} CSV", "", "CSV Files (*.csv)")
        
        if not file_path: return
        filename = os.path.basename(file_path)
            
        manager = ImportManager()
        success = False
        if type_import == "salles": success = manager.import_salles(file_path)
        elif type_import == "enseignants": success = manager.import_enseignants(file_path)
        elif type_import == "etudiants": success = manager.import_etudiants(file_path)
        elif type_import == "groupes": success = manager.import_groupes(file_path)
        
        self._update_upload_status(type_import, success, filename)
        if success:
            QMessageBox.information(self, "Succès", f"Import {type_import} réussi !")
            self.refresh_dashboard()
        else:
            QMessageBox.critical(self, "Erreur", f"Echec de l'import {type_import}. Vérifiez le format.")

    def run_generate_timetable(self):
        """
        Génère l'emploi du temps complet pour tous les groupes.
        Preserves original logic including constraints, modules, and progress dialog.
        """
        from src.logic.schedule_generator import ScheduleGenerator
        
        progress = QProgressDialog("Génération de l'emploi du temps en cours...", "Annuler", 0, 100, self)
        progress.setWindowTitle("Génération")
        progress.setMinimumWidth(400)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        try:
            groupes = self.db.get_tous_groupes()
            enseignants = self.db.get_tous_utilisateurs('enseignant')
            salles = self.db.get_toutes_salles()
            
            if not groupes or not enseignants or not salles:
                QMessageBox.warning(self, "Attention", "Données manquantes (groupes, enseignants ou salles). Importez d'abord les données.")
                progress.close()
                return
            
            # ═══════════════════════════════════════════════════════════
            # CLEAR OLD SEANCES before generating fresh ones
            # This prevents session accumulation (> 6 Cours + 6 TD)
            # ═══════════════════════════════════════════════════════════
            existing_count = len(self.db.get_toutes_seances() or [])
            if existing_count > 0:
                reply = QMessageBox.question(
                    self, "Régénérer l'emploi du temps",
                    f"Il y a {existing_count} séances existantes.\n"
                    f"Elles seront supprimées et remplacées par un nouvel emploi du temps.\n\n"
                    f"Continuer?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    progress.close()
                    return
                # Delete all existing seances
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM seances")
                conn.commit()
                conn.close()
                print(f"🗑️ {existing_count} anciennes séances supprimées")
            
            # Logic for dates
            today = datetime.now()
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0: days_until_monday = 7
            next_monday = today + timedelta(days=days_until_monday)
            semaine_debut = next_monday.strftime("%Y-%m-%d")
            
            # Load existing (now empty after cleanup) + reservations
            existing_res = self.db.get_toutes_reservations()
            existing_res_dict = [{'id':r[0], 'enseignant_id':r[1], 'salle_id':r[2], 'date':r[3], 'heure_debut':r[4], 'heure_fin':r[5], 'statut':r[6]} for r in existing_res] if existing_res else []
            
            generator = ScheduleGenerator(self.db, [], existing_res_dict)
            
            # Tracking variables
            teacher_weekly_hours, teacher_daily_hours, group_daily_hours, group_weekly_hours = {}, {}, {}, {}
            NB_SUBJECTS_PER_GROUP = 6
            types_cours = [('Cours', 1.5, 1), ('TD', 1.5, 1)]  # 1 Cours + 1 TD per subject × 6 subjects = 6 Cours + 6 TD per week
            
            # ═══════════════════════════════════════════════════════════
            # FULL MODULE MAPPING (RESTORED)
            # ═══════════════════════════════════════════════════════════
            FILIERES_MODULES = {
                'génie civil': [
                    ("Résistance des Matériaux", "Génie Civil"),
                    ("Béton Armé", "Génie Civil"),
                    ("Mécanique des Sols", "Génie Civil"),
                    ("Topographie", "Génie Civil"),
                    ("Hydraulique", "Génie Civil"),
                    ("Matériaux de Construction", "Génie Civil"),
                ],
                'énergies renouvelables': [
                    ("Énergie Solaire", "Énergies Renouvelables"),
                    ("Énergie Éolienne", "Énergies Renouvelables"),
                    ("Thermodynamique", "Physique"),
                    ("Électrotechnique", "Génie Électrique"),
                    ("Conversion d'Énergie", "Physique"),
                    ("Stockage d'Énergie", "Physique"),
                ],
                'analytique des données': [
                    ("Algorithmique et Programmation", "Informatique"),
                    ("Bases de Données", "Informatique"),
                    ("Machine Learning", "Informatique"),
                    ("Statistiques", "Mathématiques"),
                    ("Data Mining", "Informatique"),
                    ("Big Data", "Informatique"),
                ],
                "ingénierie de développement d'applications informatiques": [
                    ("Programmation Web", "Informatique"),
                    ("Bases de Données", "Informatique"),
                    ("Génie Logiciel", "Informatique"),
                    ("Java/JEE", "Informatique"),
                    ("Réseaux", "Informatique"),
                    ("Sécurité Informatique", "Informatique"),
                ],
                'statistique et science des données': [
                    ("Statistiques Descriptives", "Statistique"),
                    ("Probabilités", "Mathématiques"),
                    ("Analyse de Données", "Statistique"),
                    ("Régression", "Statistique"),
                    ("Échantillonnage", "Statistique"),
                    ("Économétrie", "Statistique"),
                ],
                'mathématiques et informatique décisionnelles': [
                    ("Recherche Opérationnelle", "Mathématiques"),
                    ("Optimisation", "Mathématiques"),
                    ("Algorithmique", "Informatique"),
                    ("Analyse Numérique", "Mathématiques"),
                    ("Programmation Linéaire", "Mathématiques"),
                    ("Aide à la Décision", "Informatique"),
                ],
                'biotechnologies': [
                    ("Biologie Moléculaire", "Biotechnologie"),
                    ("Génie Génétique", "Biotechnologie"),
                    ("Microbiologie", "Biologie"),
                    ("Biochimie", "Biologie"),
                    ("Culture Cellulaire", "Biotechnologie"),
                    ("Fermentation", "Biotechnologie"),
                ],
                'génie des procédés': [
                    ("Opérations Unitaires", "Chimie"),
                    ("Transfert de Matière", "Chimie"),
                    ("Réacteurs Chimiques", "Chimie"),
                    ("Thermodynamique Chimique", "Chimie"),
                    ("Séparation", "Chimie"),
                    ("Procédés Industriels", "Chimie"),
                ],
                "techniques d'analyses chimiques": [
                    ("Chimie Analytique", "Chimie"),
                    ("Spectroscopie", "Chimie"),
                    ("Chromatographie", "Chimie"),
                    ("Électrochimie", "Chimie"),
                    ("Chimie Organique", "Chimie"),
                    ("Qualité et Normes", "Chimie"),
                ],
                'risques et ressources naturels': [
                    ("Géologie Structurale", "Sciences de l'Environnement"),
                    ("Hydrogéologie", "Sciences de l'Environnement"),
                    ("Risques Naturels", "Sciences de l'Environnement"),
                    ("Gestion des Ressources", "Sciences de l'Environnement"),
                    ("Télédétection", "Sciences de l'Environnement"),
                    ("SIG", "Informatique"),
                ],
                'génie électrique & système industriel': [
                    ("Électronique de Puissance", "Génie Électrique"),
                    ("Automatique", "Génie Électrique"),
                    ("Machines Électriques", "Génie Électrique"),
                    ("Électrotechnique", "Génie Électrique"),
                    ("Commande des Systèmes", "Génie Électrique"),
                    ("Instrumentation", "Génie Électrique"),
                ],
                'génie industriel': [
                    ("Gestion de Production", "Génie Industriel"),
                    ("Qualité", "Génie Industriel"),
                    ("Logistique", "Génie Industriel"),
                    ("Lean Manufacturing", "Génie Industriel"),
                    ("Maintenance", "Génie Industriel"),
                    ("Ergonomie", "Génie Industriel"),
                ],
                'design industriel et productique': [
                    ("CAO/DAO", "Génie Mécanique"),
                    ("Fabrication Mécanique", "Génie Mécanique"),
                    ("Design Produit", "Génie Mécanique"),
                    ("Matériaux", "Génie Mécanique"),
                    ("Prototypage Rapide", "Génie Mécanique"),
                    ("Plasturgie", "Génie Mécanique"),
                ],
            }
            
            DEFAULT_MODULES = [
                ("Mathématiques", "Mathématiques"),
                ("Physique", "Physique"),
                ("Informatique", "Informatique"),
                ("Communication", "Langues"),
                ("Anglais", "Langues"),
                ("Méthodologie", "Gestion"),
            ]
            
            # Sort groups: GP_ (promo, 50 students, need Amphis) first,
            # then Gr_ (subgroups, 25 students, can use Salles)
            groupes = sorted(groupes, key=lambda g: (0 if g[1].startswith('GP_') else 1, g[1]))
            
            total_groups = len(groupes)
            sessions_created = 0
            errors = []
            
            for idx, groupe in enumerate(groupes):
                groupe_id, groupe_nom = groupe[0], groupe[1]
                progress.setValue(int((idx / total_groups) * 100))
                progress.setLabelText(f"Traitement du groupe: {groupe_nom}...")
                if progress.wasCanceled(): break
                
                # Determine modules
                filiere_id = groupe[3] if len(groupe) > 3 else None
                filiere_nom = None
                if filiere_id:
                    try:
                        f = self.db.get_filiere_by_id(filiere_id)
                        if f: filiere_nom = f[1] if isinstance(f, tuple) else f.get('nom')
                    except: pass
                
                modules = DEFAULT_MODULES
                if filiere_nom:
                    key = filiere_nom.lower()
                    # Try exact then partial
                    if key in FILIERES_MODULES:
                        modules = FILIERES_MODULES[key]
                    else:
                        for k, v in FILIERES_MODULES.items():
                            if k in key or key in k: 
                                modules = v; break
                
                # Generate
                for matiere_nom, departement in modules[:NB_SUBJECTS_PER_GROUP]:
                    enseignant_id = generator.find_suitable_teacher_for_module(departement, teacher_weekly_hours, [])
                    if not enseignant_id:
                        errors.append(f"⚠️ {groupe_nom}/{matiere_nom}: Pas d'enseignant disponible")
                        continue
                        
                    for type_seance, duree, nb_sessions in types_cours:
                        try:
                            sessions = generator.generate_schedule_for_group(
                                groupe_id, matiere_nom, type_seance, duree, enseignant_id, nb_sessions, semaine_debut,
                                teacher_weekly_hours, teacher_daily_hours, departement, group_daily_hours, group_weekly_hours
                            )
                            for s in sessions:
                                sid = self.db.ajouter_seance(s['titre'], s['type_seance'], s['date'], s['heure_debut'], s['heure_fin'], s['salle_id'], s['enseignant_id'], s['groupe_id'])
                                if sid:
                                    sessions_created += 1
                                    generator.conflict_detector.add_session({'id':sid, 'date':s['date'], 'heure_debut':s['heure_debut'], 'heure_fin':s['heure_fin'], 'salle_id':s['salle_id'], 'enseignant_id':s['enseignant_id'], 'groupe_id':s['groupe_id']})
                        except Exception as e:
                            errors.append(f"{groupe_nom}/{matiere_nom}: {str(e)}")
            
            # ═══════════════════════════════════════════════════════════
            # SEMESTER REPLICATION: Copy week 1 schedule to weeks 2-16
            # The schedule repeats every week for the entire semester
            # ═══════════════════════════════════════════════════════════
            SEMESTER_WEEKS = 16
            if sessions_created > 0:
                progress.setLabelText("Réplication sur le semestre (16 semaines)...")
                progress.setValue(50)
                
                try:
                    conn = self.db.get_connection()
                    cursor = conn.cursor()
                    # Get all base week sessions
                    cursor.execute("""
                        SELECT titre, type_seance, date, heure_debut, heure_fin,
                               salle_id, enseignant_id, groupe_id
                        FROM seances ORDER BY date, heure_debut
                    """)
                    base_sessions = cursor.fetchall()
                    
                    replicated = 0
                    for week_offset in range(1, SEMESTER_WEEKS):
                        offset_days = week_offset * 7
                        for sess in base_sessions:
                            original_date = datetime.strptime(sess[2], "%Y-%m-%d")
                            new_date = (original_date + timedelta(days=offset_days)).strftime("%Y-%m-%d")
                            cursor.execute("""
                                INSERT INTO seances (titre, type_seance, date, heure_debut, heure_fin,
                                                     salle_id, enseignant_id, groupe_id)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (sess[0], sess[1], new_date, sess[3], sess[4], sess[5], sess[6], sess[7]))
                            replicated += 1
                        progress.setValue(50 + int((week_offset / SEMESTER_WEEKS) * 50))
                    
                    conn.commit()
                    conn.close()
                    sessions_created += replicated
                    print(f"📆 Semestre: {replicated} séances répliquées sur {SEMESTER_WEEKS-1} semaines")
                except Exception as e:
                    print(f"Semester replication error: {e}")
            
            progress.setValue(100)
            progress.close()
            
            if sessions_created > 0:
                weeks_info = f"\n• Durée: {SEMESTER_WEEKS} semaines (semestre complet)"
                msg = f"Génération terminée !\n\n• {sessions_created} séances créées\n• {total_groups} groupes traités{weeks_info}"
                if errors: msg += f"\n\n⚠️ {len(errors)} avertissements"
                QMessageBox.information(self, "Succès", msg)
            else:
                QMessageBox.warning(self, "Attention", "Aucune séance créée.")
            self.refresh_dashboard()
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Erreur", f"Erreur fatale: {str(e)}")

    def handle_reservation(self, index, accepted):
        """Handle reservation approval/rejection with conflict checking & notifications"""
        if 0 <= index < len(self.reservations_data):
            data = self.reservations_data[index]
            res_id = data.get('db_id')
            
            if accepted:
                # ═══ CONFLICT CHECK before approval ═══
                salle_id = data.get('salle_id')
                date = data.get('date')
                heure_debut = data.get('heure_debut')
                heure_fin = data.get('heure_fin')
                
                if salle_id and date and heure_debut and heure_fin:
                    enseignant_id = data.get('enseignant_id')
                    groupe_id = data.get('groupe_id')
                    
                    conflits_seances = self.db.verifier_conflit_seance(
                        date, heure_debut, heure_fin, 
                        salle_id=salle_id,
                        enseignant_id=enseignant_id,
                        groupe_id=groupe_id
                    )
                    conflits_reservations = self.db.verifier_conflit_reservation(
                        date, heure_debut, heure_fin, salle_id
                    )
                    
                    if conflits_seances or conflits_reservations:
                        msg = "⚠️ Cette salle présente des conflits:\n\n"
                        for c in conflits_seances:
                            msg += f"• {c}\n"
                        for cr in conflits_reservations:
                            prof_name = f"{cr[-2]} {cr[-1]}" if len(cr) >= 2 else "Inconnu"
                            msg += f"• Réservation existante par {prof_name} ({cr[4]}-{cr[5]})\n"
                        msg += "\nApprouver quand même?"
                        
                        reply = QMessageBox.question(self, "⚠️ Conflit de salle", msg,
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                        if reply == QMessageBox.StandardButton.No:
                            return
                
                if data.get('type') == 'rattrapage' and res_id:
                    self.db.approuver_demande(res_id)
                elif res_id:
                    self.db.modifier_statut_reservation(res_id, 'validee')
                
                # Notifications Logic
                from src.services_notification import NotificationService
                ns = NotificationService(self.db)
                if data.get('enseignant_id'):
                    ns.notifier_reservation_approuvee(data.get('enseignant_id'), data.get('salle'), data.get('date'), data.get('heure_debut', '00:00'), data.get('heure_fin', '00:00'), data.get('motif'), data.get('groupe_id'))
                
                data['status'] = "Acceptée"
                QMessageBox.information(self, "Succès", "✅ Réservation approuvée et notifiée.")
            else:
                motif_rejet, ok = QInputDialog.getText(self, "Motif de Refus", "Motif (obligatoire):")
                if not ok or not motif_rejet.strip():
                    return
                
                if data.get('type') == 'rattrapage' and res_id:
                    self.db.rejeter_demande(res_id, motif_rejet)
                elif res_id:
                    self.db.modifier_reservation_avec_motif(res_id, 'rejetee', motif_rejet)
                
                # Notifications Logic
                from src.services_notification import NotificationService
                ns = NotificationService(self.db)
                if data.get('enseignant_id'):
                    ns.notifier_reservation_rejetee(data.get('enseignant_id'), data.get('salle'), data.get('date'), data.get('heure_debut', '00:00'), data.get('heure_fin', '00:00'), motif_rejet)
                
                data['status'] = "Refusée"
                QMessageBox.information(self, "Refusé", "Réservation refusée et notifiée.")
                
            self.refresh_reservations()

    # ═══════════════════════════════════════════════════════════
    # 3. MODERN UI CONSTRUCTION (REFACTORED WITH LOOPS)
    # ═══════════════════════════════════════════════════════════

    def create_sidebar(self):
        """Modern Sidebar with gradient"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(280)
        self.sidebar.setStyleSheet(f"QFrame {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {COLORS['sidebar_top']}, stop:0.5 {COLORS['sidebar_mid']}, stop:1 {COLORS['sidebar_bot']}); }}")
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(8)
        
        # Header
        header = QFrame()
        header.setFixedHeight(100)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
            }}
        """)
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(20, 25, 20, 25)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("ADMINISTRATEUR")
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
        
        # Menu
        self.menu_buttons = {}
        menus = [("Dashboard", "Dashboard"), ("Generer Emploi", "Generation"), ("Salles", "Rooms"), ("Reservations", "Reservations"), ("Notifications", "Notifications")]
        
        for label, pid in menus:
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
            layout.addWidget(btn)
            self.menu_buttons[pid] = btn
            
        layout.addStretch()
        
        # User Info
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
        
        avatar = QLabel("A")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
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
        
        user_name = QLabel(f"Admin. {self.user.nom if self.user else 'Administrateur'}")
        user_name.setStyleSheet("color: white; font-size: 14px; font-weight: 600; background: transparent;")
        user_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(user_name)
        
        role_badge = QLabel("Administrateur")
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
        logout = QPushButton("Deconnexion")
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
        """Create main content area"""
        self.content_area = QFrame()
        self.content_area.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {COLORS.get('bg_light', '#F3F6FB')}, stop:1 #E2E8F0);
            }}
        """)
        
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(40, 32, 40, 32)
        content_layout.setSpacing(8)
        
        # Page title
        self.page_title = QLabel("Tableau de Bord")
        self.page_title.setStyleSheet(PAGE_TITLE_STYLE)
        content_layout.addWidget(self.page_title)
        
        # Page subtitle
        self.page_subtitle = QLabel("Vue d'ensemble de votre système")
        self.page_subtitle.setStyleSheet(f"""
            color: {COLORS.get('text_light', '#888')}; 
            font-size: 14px; 
            margin-bottom: 20px;
        """)
        content_layout.addWidget(self.page_subtitle)
        
        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_dashboard_page())
        self.pages.addWidget(self.create_generation_page())
        self.pages.addWidget(self.create_rooms_page())
        self.pages.addWidget(self.create_reservations_page())
        self.pages.addWidget(self.create_notifications_page())
        
        content_layout.addWidget(self.pages)
        self.main_layout.addWidget(self.content_area)

    def create_dashboard_page(self):
        from PyQt6.QtWidgets import QScrollArea
        
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Stats cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        current_stats = self.calculate_stats()
        
        cards_config = [
            ("Enseignants", current_stats['enseignants'], "👨‍🏫", COLORS.get('card_purple', '#8B5CF6')),
            ("Étudiants", current_stats['etudiants'], "👨‍🎓", COLORS.get('card_cyan', '#06B6D4')),
            ("Filières", current_stats['filieres'], "📚", COLORS.get('card_emerald', '#10B981')),
            ("Matières", current_stats['matieres'], "📖", COLORS.get('card_amber', '#F59E0B'))
        ]
        
        self.stat_cards = {}
        for title, value, icon, color in cards_config:
            card = ModernStatCard(title, value, icon, color)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.stat_cards[title] = card
            stats_layout.addWidget(card)
        layout.addLayout(stats_layout)
        
        # Charts Row 1 — Room distribution + Volume horaire
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)
        
        # Donut — Fixed color mapping for actual type_salle values
        try:
            salles = self.db.get_toutes_salles()
            type_counts = {}
            for s in salles:
                t = s[3] if len(s) > 3 else 'Autre'
                type_counts[t] = type_counts.get(t, 0) + 1
            colors_map = {
                'Amphithéâtre': COLORS.get('card_purple', '#8B5CF6'),
                'Salle': COLORS.get('card_cyan', '#06B6D4'),
                'Laboratoire': COLORS.get('card_emerald', '#10B981'),
            }
            salles_data = [(label, count, colors_map.get(label, COLORS.get('primary', '#6366F1')))
                          for label, count in type_counts.items()]
        except: salles_data = []
        donut_chart = ModernDonutChart(salles_data, "Répartition des Salles")
        donut_chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        charts_layout.addWidget(donut_chart)
        
        # Bar — Dynamic volume horaire
        heures_data = self._calculate_volume_horaire()
        self.volume_chart = ModernBarChart(heures_data, "Volume Horaire")
        charts_layout.addWidget(self.volume_chart)
        
        layout.addLayout(charts_layout)
        
        # Charts Row 2 — Occupation stats
        occ_layout = QHBoxLayout()
        occ_layout.setSpacing(20)
        
        # Occupation rate by time slot
        occ_data = self._calculate_occupation_stats()
        occ_chart = ModernBarChart(occ_data['slots'], "Taux d'Occupation par Créneau (%)")
        occ_chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        occ_layout.addWidget(occ_chart)
        
        # Occupation summary card
        summary_card = QFrame()
        summary_card.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 20px;
            }
        """)
        summary_card.setMinimumSize(350, 300)
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(24, 24, 24, 24)
        summary_layout.setSpacing(16)
        
        sum_title = QLabel("📊 Statistiques d'Occupation")
        sum_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #1E293B;")
        summary_layout.addWidget(sum_title)
        
        # Total occupation rate
        total_occ = occ_data['total_rate']
        occ_color = '#10B981' if total_occ < 50 else ('#F59E0B' if total_occ < 80 else '#EF4444')
        
        rate_label = QLabel(f"{total_occ:.0f}%")
        rate_label.setStyleSheet(f"font-size: 42px; font-weight: 800; color: {occ_color};")
        rate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        summary_layout.addWidget(rate_label)
        
        rate_desc = QLabel("Taux d'occupation global")
        rate_desc.setStyleSheet("font-size: 13px; color: #64748B;")
        rate_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        summary_layout.addWidget(rate_desc)
        
        summary_layout.addSpacing(8)
        
        # Details
        stats_date = occ_data.get('stats_date', '')
        date_label_text = "Séances ce jour" if stats_date == __import__('datetime').datetime.now().strftime("%Y-%m-%d") else f"Séances ({stats_date})"
        for label, value in [
            ("Salles totales", str(occ_data['total_rooms'])),
            (date_label_text, str(occ_data['sessions_today'])),
            ("Créneau le plus chargé", occ_data['busiest_slot']),
            ("Réservations en attente", str(occ_data['pending_reservations'])),
        ]:
            row_w = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 13px; color: #64748B;")
            row_w.addWidget(lbl)
            row_w.addStretch()
            val = QLabel(value)
            val.setStyleSheet("font-size: 13px; font-weight: 700; color: #1E293B;")
            row_w.addWidget(val)
            summary_layout.addLayout(row_w)
        
        summary_layout.addStretch()
        occ_layout.addWidget(summary_card)
        
        layout.addLayout(occ_layout)
        
        scroll.setWidget(scroll_content)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
        return page

    def create_generation_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Import Card
        import_card = QFrame()
        import_card.setObjectName("importCard")
        import_card.setStyleSheet("""
            QFrame#importCard {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
        """)
        import_layout = QVBoxLayout(import_card)
        import_layout.setContentsMargins(25, 25, 25, 25)
        import_layout.setSpacing(8)
        
        import_title = QLabel("Importation des Donnees (CSV)")
        import_title.setStyleSheet("color: #1E293B; font-size: 20px; font-weight: 700; background: transparent;")
        import_layout.addWidget(import_title)
        import_desc = QLabel("Selectionnez les fichiers CSV a importer dans le systeme")
        import_desc.setStyleSheet("color: #64748B; font-size: 14px; background: transparent;")
        import_layout.addWidget(import_desc)
        import_layout.addSpacing(20)
        
        self.upload_cards = {}
        grid = QGridLayout()
        grid.setSpacing(20)
        
        unified_btn_style = f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
                color: white; border: none; border-radius: 10px;
                font-size: 14px; font-weight: 600; padding: 0 24px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['primary_dark']}, stop:1 {COLORS['secondary_dark']});
            }}
        """
        
        for idx, (key, title) in enumerate([("salles", "Importer les Salles"), ("enseignants", "Importer Enseignants"), ("etudiants", "Importer Etudiants"), ("groupes", "Importer Groupes")]):
            btn = QPushButton(title)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(45)
            btn.setStyleSheet(unified_btn_style)
            btn.clicked.connect(lambda _, k=key: self.run_import(k))
            self.upload_cards[key] = {'button': btn}
            grid.addWidget(btn, idx // 2, idx % 2)
        import_layout.addLayout(grid)
        layout.addWidget(import_card)
        
        # Generation Card
        gen_card = QFrame()
        gen_card.setObjectName("genCard")
        gen_card.setStyleSheet("""
            QFrame#genCard {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
        """)
        gen_layout = QVBoxLayout(gen_card)
        gen_layout.setContentsMargins(25, 25, 25, 25)
        gen_layout.setSpacing(8)
        
        gen_title = QLabel("Generation")
        gen_title.setStyleSheet("color: #1E293B; font-size: 20px; font-weight: 700; background: transparent;")
        gen_layout.addWidget(gen_title)
        gen_desc = QLabel("Generez automatiquement l'emploi du temps optimise pour tous les groupes")
        gen_desc.setStyleSheet("color: #64748B; font-size: 14px; background: transparent;")
        gen_layout.addWidget(gen_desc)
        gen_layout.addSpacing(20)
        
        self.btn_generate = QPushButton("Lancer la Generation de l'Emploi du Temps")
        self.btn_generate.setObjectName("btnGenerate")
        self.btn_generate.setFixedHeight(45)
        self.btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate.setStyleSheet(f"""
            QPushButton#btnGenerate {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
                color: white; border: none; border-radius: 10px;
                font-size: 14px; font-weight: 600; padding: 0 32px;
            }}
            QPushButton#btnGenerate:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['primary_dark']}, stop:1 {COLORS['secondary_dark']});
            }}
        """)
        self.btn_generate.clicked.connect(self.run_generate_timetable)
        gen_layout.addWidget(self.btn_generate, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(gen_card)

        # ── Export Card ──
        export_card = QFrame()
        export_card.setObjectName("exportCard")
        export_card.setStyleSheet("""
            QFrame#exportCard {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
        """)
        export_layout = QVBoxLayout(export_card)
        export_layout.setContentsMargins(25, 25, 25, 25)
        export_layout.setSpacing(8)

        export_title = QLabel("Exporter l'Emploi du Temps (PDF)")
        export_title.setStyleSheet("color: #1E293B; font-size: 20px; font-weight: 700; background: transparent;")
        export_layout.addWidget(export_title)
        export_desc = QLabel("Sélectionnez un groupe ou enseignant pour prévisualiser puis exporter en PDF")
        export_desc.setStyleSheet("color: #64748B; font-size: 14px; background: transparent;")
        export_layout.addWidget(export_desc)
        export_layout.addSpacing(12)

        # ── Group export row ──
        grp_row_label = QLabel("📚 Emploi du temps par Groupe")
        grp_row_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #1E293B;")
        export_layout.addWidget(grp_row_label)

        export_row = QHBoxLayout()
        export_row.setSpacing(16)

        grp_label = QLabel("Groupe:")
        grp_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #1E293B;")
        export_row.addWidget(grp_label)

        self.export_group_combo = QComboBox()
        self.export_group_combo.setMinimumWidth(200)
        self.export_group_combo.setStyleSheet("""
            QComboBox { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; font-size: 14px; }
            QComboBox QAbstractItemView { background: white; border: 1px solid #E2E8F0; selection-background-color: #EEF2FF; }
        """)
        try:
            groupes = self.db.get_tous_groupes()
            for g in groupes:
                self.export_group_combo.addItem(g[1], g[0])
        except:
            pass
        self.export_group_combo.currentIndexChanged.connect(self._preview_group_timetable)
        export_row.addWidget(self.export_group_combo)

        btn_preview_grp = QPushButton("👁 Prévisualiser")
        btn_preview_grp.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_preview_grp.setFixedHeight(42)
        btn_preview_grp.setStyleSheet(f"""
            QPushButton {{
                background: #F1F5F9; color: {COLORS['primary']};
                border: 2px solid {COLORS['primary']}; border-radius: 10px;
                font-size: 13px; font-weight: 600; padding: 0 20px;
            }}
            QPushButton:hover {{ background: {COLORS['primary']}; color: white; }}
        """)
        btn_preview_grp.clicked.connect(self._preview_group_timetable)
        export_row.addWidget(btn_preview_grp)

        fmt_label_grp = QLabel("Format:")
        fmt_label_grp.setStyleSheet("font-size: 14px; font-weight: 600; color: #1E293B;")
        export_row.addWidget(fmt_label_grp)

        self.export_group_format = QComboBox()
        self.export_group_format.addItems(["PDF", "Excel", "Image"])
        self.export_group_format.setMinimumWidth(100)
        self.export_group_format.setStyleSheet("""
            QComboBox { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; font-size: 14px; }
            QComboBox QAbstractItemView { background: white; border: 1px solid #E2E8F0; selection-background-color: #EEF2FF; }
        """)
        export_row.addWidget(self.export_group_format)

        btn_export_grp = QPushButton("📤 Exporter Groupe")
        btn_export_grp.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export_grp.setFixedHeight(42)
        btn_export_grp.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent']}, stop:1 {COLORS['accent_warm']});
                color: white; border: none; border-radius: 10px;
                font-size: 14px; font-weight: 600; padding: 0 24px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E8607A, stop:1 #E0B73E);
            }}
        """)
        btn_export_grp.clicked.connect(self._export_group_timetable)
        export_row.addWidget(btn_export_grp)
        export_row.addStretch()
        export_layout.addLayout(export_row)

        export_layout.addSpacing(16)

        # ── Teacher export row ──
        prof_row_label = QLabel("👨‍🏫 Emploi du temps par Enseignant")
        prof_row_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #1E293B;")
        export_layout.addWidget(prof_row_label)

        teacher_row = QHBoxLayout()
        teacher_row.setSpacing(16)

        prof_label = QLabel("Enseignant:")
        prof_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #1E293B;")
        teacher_row.addWidget(prof_label)

        self.export_teacher_combo = QComboBox()
        self.export_teacher_combo.setMinimumWidth(200)
        self.export_teacher_combo.setStyleSheet("""
            QComboBox { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; font-size: 14px; }
            QComboBox QAbstractItemView { background: white; border: 1px solid #E2E8F0; selection-background-color: #EEF2FF; }
        """)
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nom, prenom FROM utilisateurs WHERE type_user='enseignant' ORDER BY nom")
            enseignants = cursor.fetchall()
            conn.close()
            for e in enseignants:
                self.export_teacher_combo.addItem(f"{e[1]} {e[2]}", e[0])
        except:
            pass
        self.export_teacher_combo.currentIndexChanged.connect(self._preview_teacher_timetable)
        teacher_row.addWidget(self.export_teacher_combo)

        btn_preview_prof = QPushButton("👁 Prévisualiser")
        btn_preview_prof.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_preview_prof.setFixedHeight(42)
        btn_preview_prof.setStyleSheet(f"""
            QPushButton {{
                background: #F1F5F9; color: {COLORS['primary']};
                border: 2px solid {COLORS['primary']}; border-radius: 10px;
                font-size: 13px; font-weight: 600; padding: 0 20px;
            }}
            QPushButton:hover {{ background: {COLORS['primary']}; color: white; }}
        """)
        btn_preview_prof.clicked.connect(self._preview_teacher_timetable)
        teacher_row.addWidget(btn_preview_prof)

        fmt_label_prof = QLabel("Format:")
        fmt_label_prof.setStyleSheet("font-size: 14px; font-weight: 600; color: #1E293B;")
        teacher_row.addWidget(fmt_label_prof)

        self.export_teacher_format = QComboBox()
        self.export_teacher_format.addItems(["PDF", "Excel", "Image"])
        self.export_teacher_format.setMinimumWidth(100)
        self.export_teacher_format.setStyleSheet("""
            QComboBox { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; font-size: 14px; }
            QComboBox QAbstractItemView { background: white; border: 1px solid #E2E8F0; selection-background-color: #EEF2FF; }
        """)
        teacher_row.addWidget(self.export_teacher_format)

        btn_export_teacher = QPushButton("📤 Exporter Enseignant")
        btn_export_teacher.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export_teacher.setFixedHeight(42)
        btn_export_teacher.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
                color: white; border: none; border-radius: 10px;
                font-size: 14px; font-weight: 600; padding: 0 24px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary_dark']}, stop:1 {COLORS['secondary_dark']});
            }}
        """)
        btn_export_teacher.clicked.connect(self._export_teacher_timetable)
        teacher_row.addWidget(btn_export_teacher)
        teacher_row.addStretch()
        export_layout.addLayout(teacher_row)

        layout.addWidget(export_card)
        
        layout.addStretch()
        return page

    def _update_upload_status(self, key, success, filename=""):
        if key in self.upload_cards:
            btn = self.upload_cards[key]['button']
            if success:
                short_name = filename[:15] + "..." if len(filename) > 15 else filename
                btn.setText(f"✓ {short_name}")
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:0.5 #059669, stop:1 #047857);
                        color: white; border: none; border-radius: 12px; font-size: 14px; font-weight: 600; padding: 0 24px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:0.5 #047857, stop:1 #065F46);
                    }
                """)
            else:
                btn.setText("✗ Erreur d'import")
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EF4444, stop:0.5 #DC2626, stop:1 #B91C1C);
                        color: white; border: none; border-radius: 12px; font-size: 14px; font-weight: 600; padding: 0 24px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #DC2626, stop:0.5 #B91C1C, stop:1 #991B1B);
                    }
                """)

    # ═══════════════════════════════════════════════════════════
    # ROOMS PAGE — Occupation des Salles
    # ═══════════════════════════════════════════════════════════

    def create_rooms_page(self):
        """Page showing room availability status with date/time filter"""
        from PyQt6.QtWidgets import QScrollArea

        page = QWidget()
        page.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(page)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(0, 8, 0, 24)

        # ── Filter bar in a card ──
        filter_frame = QFrame()
        filter_frame.setStyleSheet("QFrame { background: white; border-radius: 16px; border: 1px solid #E2E8F0; }")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setXOffset(0); shadow.setYOffset(4); shadow.setColor(QColor(0,0,0,15))
        filter_frame.setGraphicsEffect(shadow)

        f_layout = QHBoxLayout(filter_frame)
        f_layout.setContentsMargins(24, 16, 24, 16)
        f_layout.setSpacing(20)

        f_layout.addWidget(QLabel("📅 Date:"))
        self.rooms_filter_date = QDateEdit(QDate.currentDate())
        self.rooms_filter_date.setCalendarPopup(True)
        self.rooms_filter_date.setDisplayFormat("dd/MM/yyyy")
        self.rooms_filter_date.setStyleSheet("""
            QDateEdit { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 12px; min-width: 140px; }
        """)
        self.rooms_filter_date.dateChanged.connect(self._update_rooms_time_filter)
        f_layout.addWidget(self.rooms_filter_date)

        f_layout.addWidget(QLabel("🕐 Créneau:"))
        self.rooms_filter_time = QComboBox()
        self._update_rooms_time_filter()
        self.rooms_filter_time.setStyleSheet("""
            QComboBox { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 12px; min-width: 140px; }
        """)
        f_layout.addWidget(self.rooms_filter_time)

        btn_refresh_rooms = QPushButton("🔄 Actualiser")
        btn_refresh_rooms.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh_rooms.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
                color: white; border: none;
                border-radius: 10px; padding: 10px 28px; font-weight: 700; font-size: 13px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary_dark']}, stop:1 {COLORS['secondary_dark']});
            }}
        """)
        btn_refresh_rooms.clicked.connect(self._refresh_rooms_status)
        f_layout.addWidget(btn_refresh_rooms)
        f_layout.addStretch()
        main_layout.addWidget(filter_frame)

        # ── Stats summary cards row ──
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        
        self.room_stat_free = self._create_room_stat_card("🟢", "Libres", "0", COLORS['success'])
        self.room_stat_occupied = self._create_room_stat_card("🔴", "Occupées", "0", COLORS['error'])
        self.room_stat_total = self._create_room_stat_card("📊", "Total", "0", COLORS['primary'])
        self.room_stat_rate = self._create_room_stat_card("📈", "Taux Occup.", "0%", COLORS['accent_warm'])
        
        stats_row.addWidget(self.room_stat_free)
        stats_row.addWidget(self.room_stat_occupied)
        stats_row.addWidget(self.room_stat_total)
        stats_row.addWidget(self.room_stat_rate)
        main_layout.addLayout(stats_row)

        # ── Rooms content in scrollable area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.rooms_content_widget = QWidget()
        self.rooms_content_widget.setStyleSheet("background: transparent;")
        self.rooms_content_layout = QVBoxLayout(self.rooms_content_widget)
        self.rooms_content_layout.setSpacing(20)
        scroll.setWidget(self.rooms_content_widget)
        main_layout.addWidget(scroll)

        return page

    def _create_room_stat_card(self, icon, title, value, color):
        """Create a small stats card for room occupation summary"""
        card = QFrame()
        card.setFixedHeight(80)
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFFFFF, stop:1 {color}15);
                border-radius: 14px; border: 1px solid {color}30;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12); shadow.setXOffset(0); shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 10))
        card.setGraphicsEffect(shadow)
        
        ly = QHBoxLayout(card)
        ly.setContentsMargins(16, 10, 16, 10)
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 28px; background: transparent;")
        ly.addWidget(icon_lbl)
        
        text_ly = QVBoxLayout()
        text_ly.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 600; background: transparent;")
        val_lbl = QLabel(value)
        val_lbl.setObjectName("stat_value")
        val_lbl.setStyleSheet(f"font-size: 22px; color: {color}; font-weight: 800; background: transparent;")
        text_ly.addWidget(title_lbl)
        text_ly.addWidget(val_lbl)
        ly.addLayout(text_ly)
        ly.addStretch()
        return card

    def _update_rooms_time_filter(self):
        """Update room time filter — Friday excludes 12:30-14:00"""
        all_slots = ["Tous", "09:00 - 10:30", "10:45 - 12:15", "12:30 - 14:00", "14:15 - 15:45", "16:00 - 17:30"]
        day_of_week = self.rooms_filter_date.date().dayOfWeek()  # 5 = Friday
        current = self.rooms_filter_time.currentText()
        self.rooms_filter_time.clear()
        if day_of_week == 5:
            slots = [s for s in all_slots if s != "12:30 - 14:00"]
        else:
            slots = all_slots
        self.rooms_filter_time.addItems(slots)
        idx = self.rooms_filter_time.findText(current)
        if idx >= 0:
            self.rooms_filter_time.setCurrentIndex(idx)

    def _refresh_rooms_status(self):
        """Refresh the rooms display grouped by type with mini timeline bars"""
        from datetime import datetime as dt

        # Clear content
        while self.rooms_content_layout.count():
            item = self.rooms_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        date_str = self.rooms_filter_date.date().toString("yyyy-MM-dd")
        time_filter = self.rooms_filter_time.currentText()

        # Smart date: if no seances on selected date, find nearest date with timetable data
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM seances WHERE date = ?', (date_str,))
            count_today = cursor.fetchone()[0]
            
            if count_today == 0:
                # Find nearest date with seances (future first, then past)
                cursor.execute('''
                    SELECT date FROM seances WHERE date >= ?
                    ORDER BY date ASC LIMIT 1
                ''', (date_str,))
                row = cursor.fetchone()
                if not row:
                    cursor.execute('''
                        SELECT date FROM seances WHERE date < ?
                        ORDER BY date DESC LIMIT 1
                    ''', (date_str,))
                    row = cursor.fetchone()
                
                if row:
                    date_str = row[0]
                    parts = date_str.split('-')
                    self.rooms_filter_date.blockSignals(True)
                    self.rooms_filter_date.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
                    self.rooms_filter_date.blockSignals(False)
                    self._update_rooms_time_filter()
                    time_filter = self.rooms_filter_time.currentText()
            conn.close()
        except Exception as e:
            print(f"Smart date error: {e}")

        salles = self.db.get_toutes_salles()
        free_count = 0
        occupied_count = 0

        # Group by type
        TYPE_CONFIG = {
            'Salle': {'icon': '🏫', 'color': '#6C5CE7', 'bg': '#F0EDFF', 'border': '#D4CCFF'},
            'Amphithéâtre': {'icon': '🎭', 'color': '#E17055', 'bg': '#FFF0EC', 'border': '#FFDDD2'},
            'Laboratoire': {'icon': '🔬', 'color': '#00B894', 'bg': '#E8FFF5', 'border': '#B2F5EA'},
        }
        
        categorized = {'Salle': [], 'Amphithéâtre': [], 'Laboratoire': []}
        
        time_slots = [
            ("09:00", "10:30"), ("10:45", "12:15"), ("12:30", "14:00"),
            ("14:15", "15:45"), ("16:00", "17:30")
        ]

        for salle in salles:
            salle_id = salle[0]
            salle_nom = salle[1]
            salle_capacite = salle[2] if len(salle) > 2 else "—"
            salle_type = salle[3] if len(salle) > 3 else "Salle"
            salle_equip = salle[4] if len(salle) > 4 else ""

            # Check each slot for the timeline
            slot_statuses = []
            is_occupied_now = False
            occupant_info = ""
            
            try:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                for h_d, h_f in time_slots:
                    cursor.execute('''
                        SELECT s.titre, s.type_seance, u.prenom, u.nom
                        FROM seances s LEFT JOIN utilisateurs u ON s.enseignant_id = u.id
                        WHERE s.salle_id = ? AND s.date = ?
                        AND s.heure_debut < ? AND s.heure_fin > ?
                    ''', (salle_id, date_str, h_f, h_d))
                    row_s = cursor.fetchone()
                    if row_s:
                        slot_statuses.append(('seance', row_s))
                    else:
                        cursor.execute('''
                            SELECT r.motif, u.prenom, u.nom
                            FROM reservations r LEFT JOIN utilisateurs u ON r.enseignant_id = u.id
                            WHERE r.salle_id = ? AND r.date = ? AND r.statut IN ('acceptee', 'validee')
                            AND r.heure_debut < ? AND r.heure_fin > ?
                        ''', (salle_id, date_str, h_f, h_d))
                        row_r = cursor.fetchone()
                        if row_r:
                            slot_statuses.append(('reservation', row_r))
                        else:
                            slot_statuses.append(('free', None))
                
                conn.close()
            except Exception as e:
                slot_statuses = [('free', None)] * 5
                print(f"Room check error: {e}")

            # Determine current status based on filter
            if time_filter != "Tous":
                parts = time_filter.split(" - ")
                h_d_f, h_f_f = parts[0].strip(), parts[1].strip()
                slot_idx = None
                for i, (h_d, h_f) in enumerate(time_slots):
                    if h_d == h_d_f:
                        slot_idx = i
                        break
                if slot_idx is not None and slot_statuses[slot_idx][0] != 'free':
                    is_occupied_now = True
                    data = slot_statuses[slot_idx][1]
                    if slot_statuses[slot_idx][0] == 'seance':
                        occupant_info = f"📖 {data[0]} ({data[1]}) — {data[2] or ''} {data[3] or ''}"
                    else:
                        occupant_info = f"📌 {data[0]} — {data[1] or ''} {data[2] or ''}"
            else:
                busy_slots = [s for s in slot_statuses if s[0] != 'free']
                if busy_slots:
                    is_occupied_now = True
                    occupant_info = f"📋 {len(busy_slots)}/5 créneaux occupés"

            if is_occupied_now:
                occupied_count += 1
            else:
                free_count += 1

            room_data = {
                'id': salle_id, 'nom': salle_nom, 'capacite': salle_capacite,
                'type': salle_type, 'equip': salle_equip,
                'occupied': is_occupied_now, 'info': occupant_info,
                'slots': slot_statuses
            }
            cat = salle_type if salle_type in categorized else 'Salle'
            categorized[cat].append(room_data)

        # Update stats cards
        total = len(salles)
        occ_pct = (occupied_count / total * 100) if total else 0
        self.room_stat_free.findChild(QLabel, "stat_value").setText(str(free_count))
        self.room_stat_occupied.findChild(QLabel, "stat_value").setText(str(occupied_count))
        self.room_stat_total.findChild(QLabel, "stat_value").setText(str(total))
        self.room_stat_rate.findChild(QLabel, "stat_value").setText(f"{occ_pct:.0f}%")

        # Build category sections
        for cat_type, rooms in categorized.items():
            if not rooms:
                continue
            cfg = TYPE_CONFIG.get(cat_type, TYPE_CONFIG['Salle'])
            
            # Category header
            cat_free = sum(1 for r in rooms if not r['occupied'])
            cat_occ = len(rooms) - cat_free
            cat_pct = (cat_occ / len(rooms) * 100) if rooms else 0
            
            header = QFrame()
            header.setStyleSheet(f"""
                QFrame {{
                    background: {cfg['bg']}; border-radius: 12px;
                    border: 1px solid {cfg['border']};
                }}
            """)
            h_ly = QHBoxLayout(header)
            h_ly.setContentsMargins(20, 12, 20, 12)
            
            h_title = QLabel(f"{cfg['icon']}  {cat_type}s  ({len(rooms)})")
            h_title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {cfg['color']}; background: transparent;")
            h_ly.addWidget(h_title)
            h_ly.addStretch()
            
            # Mini progress bar for category
            prog_container = QFrame()
            prog_container.setFixedWidth(200)
            prog_container.setFixedHeight(24)
            prog_container.setStyleSheet("background: transparent;")
            prog_ly = QHBoxLayout(prog_container)
            prog_ly.setContentsMargins(0, 0, 0, 0)
            prog_ly.setSpacing(6)
            
            bar_bg = QFrame()
            bar_bg.setFixedHeight(8)
            bar_bg.setStyleSheet("background: #E2E8F0; border-radius: 4px;")
            bar_bg_ly = QHBoxLayout(bar_bg)
            bar_bg_ly.setContentsMargins(0, 0, 0, 0)
            bar_fg = QFrame()
            bar_fg.setFixedHeight(8)
            pct_width = max(int(cat_pct), 2) if cat_occ > 0 else 0
            bar_fg.setStyleSheet(f"background: {cfg['color']}; border-radius: 4px; max-width: {pct_width}%;")
            bar_bg_ly.addWidget(bar_fg)
            if pct_width < 100:
                bar_bg_ly.addStretch()
            prog_ly.addWidget(bar_bg)
            
            pct_lbl = QLabel(f"{cat_free} libres")
            pct_lbl.setStyleSheet(f"font-size: 11px; color: {cfg['color']}; font-weight: 600; background: transparent;")
            prog_ly.addWidget(pct_lbl)
            h_ly.addWidget(prog_container)
            
            self.rooms_content_layout.addWidget(header)

            # Room cards grid (4 per row)
            grid_widget = QWidget()
            grid_widget.setStyleSheet("background: transparent;")
            grid = QGridLayout(grid_widget)
            grid.setSpacing(14)
            col_count = 4

            for idx, room in enumerate(rooms):
                card = self._create_room_card(room, cfg)
                grid.addWidget(card, idx // col_count, idx % col_count)
            
            self.rooms_content_layout.addWidget(grid_widget)

        self.rooms_content_layout.addStretch()

    def _create_room_card(self, room, cfg):
        """Create a single room card with timeline bar"""
        card = QFrame()
        status_color = COLORS['error'] if room['occupied'] else COLORS['success']
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 {cfg['bg']});
                border-radius: 14px;
                border-left: 4px solid {status_color};
                border: 1px solid #E2E8F0;
                border-left: 4px solid {status_color};
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12); shadow.setXOffset(0); shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 12))
        card.setGraphicsEffect(shadow)
        card.setFixedHeight(170)

        c_ly = QVBoxLayout(card)
        c_ly.setContentsMargins(14, 10, 14, 10)
        c_ly.setSpacing(4)

        # Top: name + badge
        top = QHBoxLayout()
        name_lbl = QLabel(f"{cfg['icon']} {room['nom']}")
        name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {COLORS['text_dark']}; background: transparent;")
        top.addWidget(name_lbl)
        top.addStretch()
        
        if room['occupied']:
            badge = QLabel("OCCUPÉE")
            badge.setStyleSheet("background: #FF6B6B; color: white; font-size: 9px; font-weight: 700; padding: 2px 8px; border-radius: 6px;")
        else:
            badge = QLabel("LIBRE")
            badge.setStyleSheet("background: #00B894; color: white; font-size: 9px; font-weight: 700; padding: 2px 8px; border-radius: 6px;")
        top.addWidget(badge)
        c_ly.addLayout(top)

        # Meta: type + capacity
        meta = QLabel(f"{room['type']}  •  {room['capacite']} places")
        meta.setStyleSheet("font-size: 10px; color: #94A3B8; font-weight: 500; background: transparent;")
        c_ly.addWidget(meta)

        # Timeline mini-bar (5 slots)
        timeline = QHBoxLayout()
        timeline.setSpacing(3)
        slot_labels = ["9h", "10h45", "12h30", "14h15", "16h"]
        for i, (status, _data) in enumerate(room['slots']):
            slot_frame = QFrame()
            slot_frame.setFixedHeight(14)
            if status == 'seance':
                slot_frame.setStyleSheet("background: #FF6B6B; border-radius: 3px;")
                slot_frame.setToolTip(f"{slot_labels[i]}: {_data[0] if _data else 'Séance'}")
            elif status == 'reservation':
                slot_frame.setStyleSheet("background: #FDCB6E; border-radius: 3px;")
                slot_frame.setToolTip(f"{slot_labels[i]}: Réservation - {_data[0] if _data else ''}")
            else:
                slot_frame.setStyleSheet("background: #E2E8F0; border-radius: 3px;")
                slot_frame.setToolTip(f"{slot_labels[i]}: Libre")
            timeline.addWidget(slot_frame)
        c_ly.addLayout(timeline)

        # Occupant info
        if room['occupied'] and room['info']:
            occ = QLabel(room['info'])
            occ.setStyleSheet("font-size: 9px; color: #DC2626; font-weight: 500; background: transparent;")
            occ.setWordWrap(True)
            c_ly.addWidget(occ)

        # Equipment
        if room['equip']:
            equips = room['equip'].split(';')[:2]
            eq_text = " • ".join(e.strip().replace('_', ' ').title() for e in equips if e.strip())
            if eq_text:
                eq_lbl = QLabel(f"🛠 {eq_text}")
                eq_lbl.setStyleSheet("font-size: 9px; color: #94A3B8; background: transparent;")
                c_ly.addWidget(eq_lbl)

        c_ly.addStretch()
        return card

    def _create_preview_dialog(self, title_text, seances):
        """Create and show a popup dialog with a full timetable preview"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox
        from PyQt6.QtGui import QFont
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"📋 {title_text}")
        dialog.setMinimumSize(900, 550)
        dialog.setStyleSheet("background: #F8FAFC;")
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)
        
        # Title
        lbl = QLabel(f"📋 Emploi du temps — {title_text}")
        lbl.setStyleSheet(f"""
            font-size: 18px; font-weight: 700; color: {COLORS['primary']};
            background: rgba(108, 92, 231, 0.08); padding: 12px 20px;
            border-radius: 12px;
        """)
        layout.addWidget(lbl)
        
        if not seances:
            empty = QLabel("Aucune séance trouvée pour cette sélection.")
            empty.setStyleSheet("font-size: 14px; color: #64748B; padding: 40px; background: white; border-radius: 12px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)
        else:
            # Build timetable
            days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
            slots = ["09:00-10:30", "10:45-12:15", "12:30-14:00", "14:15-15:45", "16:00-17:30"]
            slot_starts = ["09:00", "10:45", "12:30", "14:15", "16:00"]
            type_colors = {
                'Cours': '#6C5CE7', 'TD': '#00CEC9', 'TP': '#FD79A8',
                'Examen': '#FF7675', 'Rattrapage': '#FDCB6E'
            }
            
            table = QTableWidget()
            table.setRowCount(len(slots))
            table.setColumnCount(len(days))
            table.setHorizontalHeaderLabels(days)
            table.setVerticalHeaderLabels(slots)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            table.verticalHeader().setDefaultSectionSize(80)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.setStyleSheet(f"""
                QTableWidget {{
                    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
                    gridline-color: #E2E8F0; font-size: 12px;
                }}
                QTableWidget::item {{
                    padding: 8px; color: #1E293B;
                }}
                QHeaderView::section {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_dark']});
                    color: white; font-weight: 700; font-size: 13px;
                    padding: 12px 8px; border: none;
                }}
            """)
            
            # Init empty cells with light gray bg
            for r in range(table.rowCount()):
                for c in range(table.columnCount()):
                    item = QTableWidgetItem("")
                    item.setBackground(QColor("#F8FAFC"))
                    table.setItem(r, c, item)
            
            from datetime import datetime as dt
            for s in seances:
                titre = s[1] if len(s) > 1 else "?"
                type_s = s[2] if len(s) > 2 else ""
                date_str = s[3] if len(s) > 3 else ""
                heure = s[4] if len(s) > 4 else ""
                salle_id = s[6] if len(s) > 6 else None
                
                try:
                    date_obj = dt.strptime(date_str, "%Y-%m-%d")
                    col = date_obj.weekday()
                except:
                    continue
                if col > 4:
                    continue
                
                row = -1
                for i, ss in enumerate(slot_starts):
                    if heure.startswith(ss):
                        row = i
                        break
                if row < 0:
                    continue
                
                salle_nom = ""
                if salle_id:
                    try:
                        salle = self.db.get_salle_by_id(salle_id)
                        if salle: salle_nom = salle[1]
                    except: pass
                
                color = type_colors.get(type_s, '#475569')
                cell_text = f"{titre}\n{type_s} | {salle_nom}"
                item = QTableWidgetItem(cell_text)
                item.setBackground(QColor(color))
                item.setForeground(QColor("white"))
                font = QFont()
                font.setBold(True)
                font.setPointSize(10)
                item.setFont(font)
                table.setItem(row, col, item)
            
            layout.addWidget(table)
        
        # Close button
        btn_close = QPushButton("Fermer")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setFixedHeight(42)
        btn_close.setFixedWidth(160)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']}; color: white; border: none;
                border-radius: 10px; font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {COLORS['primary_dark']}; }}
        """)
        btn_close.clicked.connect(dialog.close)
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)
        
        dialog.exec()

    def _preview_group_timetable(self):
        """Preview the timetable of the selected group in a popup dialog"""
        groupe_id = self.export_group_combo.currentData()
        groupe_name = self.export_group_combo.currentText()
        if groupe_id is None:
            return
        try:
            seances = self.db.get_seances_by_groupe(groupe_id)
            self._create_preview_dialog(f"Groupe: {groupe_name}", seances)
        except Exception as e:
            print(f"Preview error: {e}")

    def _preview_teacher_timetable(self):
        """Preview the timetable of the selected teacher in a popup dialog"""
        enseignant_id = self.export_teacher_combo.currentData()
        enseignant_name = self.export_teacher_combo.currentText()
        if enseignant_id is None:
            return
        try:
            seances = self.db.get_seances_by_enseignant(enseignant_id)
            self._create_preview_dialog(f"Enseignant: {enseignant_name}", seances)
        except Exception as e:
            print(f"Preview error: {e}")

    def _export_group_timetable(self):
        """Export the timetable of the selected group in the chosen format"""
        from src.logic.timetable_export_service import TimetableExportService

        groupe_id = self.export_group_combo.currentData()
        groupe_name = self.export_group_combo.currentText()
        fmt_map = {"PDF": "pdf", "Excel": "excel", "Image": "image"}
        format_type = fmt_map.get(self.export_group_format.currentText(), "pdf")

        if groupe_id is None:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un groupe.")
            return

        try:
            export_service = TimetableExportService(self.db)
            file_path = export_service.export_group_timetable(groupe_id, format_type=format_type)

            if file_path:
                QMessageBox.information(
                    self, "Succès",
                    f"L'emploi du temps du groupe '{groupe_name}' a été exporté avec succès.\n\n"
                    f"Fichier : {file_path}"
                )
            else:
                QMessageBox.warning(
                    self, "Attention",
                    f"Aucune séance trouvée pour le groupe '{groupe_name}'."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur",
                f"Erreur lors de l'export : {str(e)}"
            )

    def _export_teacher_timetable(self):
        """Export the timetable of the selected teacher in the chosen format"""
        from src.logic.timetable_export_service import TimetableExportService

        enseignant_id = self.export_teacher_combo.currentData()
        enseignant_name = self.export_teacher_combo.currentText()
        fmt_map = {"PDF": "pdf", "Excel": "excel", "Image": "image"}
        format_type = fmt_map.get(self.export_teacher_format.currentText(), "pdf")

        if enseignant_id is None:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un enseignant.")
            return

        try:
            export_service = TimetableExportService(self.db)
            file_path = export_service.export_teacher_timetable(enseignant_id, format_type=format_type)

            if file_path:
                QMessageBox.information(
                    self, "Succès",
                    f"L'emploi du temps de '{enseignant_name}' a été exporté avec succès.\n\n"
                    f"Fichier : {file_path}"
                )
            else:
                QMessageBox.warning(
                    self, "Attention",
                    f"Aucune séance trouvée pour '{enseignant_name}'."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur",
                f"Erreur lors de l'export : {str(e)}"
            )

    def create_reservations_page(self):
        page = QWidget()
        page.setStyleSheet("background: #f3f6fb;")
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        layout.setContentsMargins(0, 8, 0, 24)
        
        # Header card with shadow
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: none;
                border-radius: 16px;
            }
        """)
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(24)
        header_shadow.setXOffset(0)
        header_shadow.setYOffset(4)
        header_shadow.setColor(QColor(0, 0, 0, 12))
        header_frame.setGraphicsEffect(header_shadow)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(24, 20, 24, 20)
        
        title = QLabel("Demandes de Reservation")
        title.setStyleSheet(f"""
            font-family: 'Segoe UI', sans-serif;
            font-size: 17px; font-weight: 600;
            background: rgba(108, 92, 231, 0.08); color: {COLORS['primary']};
            padding: 10px 20px; border-radius: 12px; border: none;
        """)
        
        self.counter_label = QLabel("0 demandes en attente")
        self.counter_label.setStyleSheet(f"""
            color: #FFFFFF; font-family: 'Segoe UI', sans-serif;
            font-size: 13px; font-weight: 600;
            background: {COLORS['primary']}; padding: 10px 20px;
            border-radius: 12px; border: none;
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.counter_label)
        layout.addWidget(header_frame)
        
        # Table card with shadow
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: none;
                border-radius: 16px;
            }
        """)
        table_shadow = QGraphicsDropShadowEffect()
        table_shadow.setBlurRadius(24)
        table_shadow.setXOffset(0)
        table_shadow.setYOffset(4)
        table_shadow.setColor(QColor(0, 0, 0, 12))
        table_frame.setGraphicsEffect(table_shadow)
        
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.res_table = QTableWidget()
        self.res_table.setColumnCount(5)
        self.res_table.setHorizontalHeaderLabels(["DATE", "ENSEIGNANT", "SALLE", "MOTIF", "ACTIONS"])
        self.res_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.res_table.verticalHeader().setVisible(False)
        self.res_table.setShowGrid(False)
        self.res_table.setWordWrap(True)
        self.res_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.res_table.verticalHeader().setMinimumSectionSize(50)
        self.res_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #FFFFFF; border: none;
                border-bottom-left-radius: 16px; border-bottom-right-radius: 16px;
                gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 12px 16px; border-bottom: 1px solid #F0F0F5;
                color: {COLORS['text_dark']}; font-size: 13px;
            }}
            QTableWidget::item:selected {{
                background-color: rgba(108, 92, 231, 0.06); color: {COLORS['primary']};
            }}
            QHeaderView::section {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_dark']});
                color: #FFFFFF;
                font-weight: 600; font-size: 13px;
                padding: 14px 16px; border: none;
            }}
        """)
        
        table_layout.addWidget(self.res_table)
        layout.addWidget(table_frame)
        
        self.refresh_reservations()
        return page

    def refresh_reservations(self):
        self.res_table.setRowCount(0)
        pending = sum(1 for r in self.reservations_data if 'status' not in r)
        self.counter_label.setText(f"{pending} demande{'s' if pending != 1 else ''} en attente")
        
        if pending == 0:
            self.counter_label.setStyleSheet(f"""
                color: #FFFFFF; font-family: 'Segoe UI', sans-serif;
                font-size: 13px; font-weight: 600;
                background: {COLORS['success']}; padding: 10px 20px;
                border-radius: 12px; border: none;
            """)
        else:
            self.counter_label.setStyleSheet(f"""
                color: #FFFFFF; font-family: 'Segoe UI', sans-serif;
                font-size: 13px; font-weight: 600;
                background: {COLORS['primary']}; padding: 10px 20px;
                border-radius: 12px; border: none;
            """)
        
        for i, row_data in enumerate(self.reservations_data):
            self.res_table.insertRow(i)
            
            for j, key in enumerate(['date', 'prof', 'salle', 'motif']):
                item = QTableWidgetItem(row_data.get(key, ''))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.res_table.setItem(i, j, item)
            
            actions_widget = QWidget()
            actions_widget.setStyleSheet("background: transparent;")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(10, 6, 10, 6)
            actions_layout.setSpacing(12)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if 'status' in row_data:
                status = row_data['status']
                lbl_status = QLabel(status)
                color = "#10B981" if status == "Acceptée" else "#EF4444"
                lbl_status.setStyleSheet(f"""
                    color: #FFFFFF; font-family: 'Segoe UI', sans-serif;
                    font-weight: 600; font-size: 13px;
                    background: {color}; padding: 8px 20px;
                    border-radius: 12px; border: none;
                """)
                actions_layout.addWidget(lbl_status)
            else:
                btn_accept = QPushButton("✓  Accepter")
                btn_accept.setFixedHeight(32)
                btn_accept.setMinimumWidth(88)
                btn_accept.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_accept.setStyleSheet("""
                    QPushButton { 
                        background: #FFFFFF; color: #0F172A;
                        font-family: 'Segoe UI', sans-serif;
                        font-weight: 700; font-size: 11px;
                        border: 2px solid #22C55E; border-radius: 8px; padding: 0 12px;
                    }
                    QPushButton:hover { background: #F0FDF4; border: 2px solid #16A34A; }
                    QPushButton:pressed { background: #DCFCE7; }
                """)
                btn_accept.clicked.connect(lambda _, idx=i: self.handle_reservation(idx, True))
                
                btn_refuse = QPushButton("✗  Refuser")
                btn_refuse.setFixedHeight(32)
                btn_refuse.setMinimumWidth(88)
                btn_refuse.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_refuse.setStyleSheet("""
                    QPushButton { 
                        background: #FFFFFF; color: #0F172A;
                        font-family: 'Segoe UI', sans-serif;
                        font-weight: 700; font-size: 11px;
                        border: 2px solid #EF4444; border-radius: 8px; padding: 0 12px;
                    }
                    QPushButton:hover { background: #FEF2F2; border: 2px solid #DC2626; }
                    QPushButton:pressed { background: #FEE2E2; }
                """)
                btn_refuse.clicked.connect(lambda _, idx=i: self.handle_reservation(idx, False))
                
                actions_layout.addWidget(btn_accept)
                actions_layout.addWidget(btn_refuse)
            
            self.res_table.setCellWidget(i, 4, actions_widget)
            self.res_table.setRowHeight(i, 60)

    def create_notifications_page(self):
        page = QWidget()
        page.setStyleSheet("background: #f3f6fb;")
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 8, 0, 24)
        
        # ── Header card ──
        header_frame = QFrame()
        header_frame.setStyleSheet("QFrame { background-color: white; border-radius: 18px; border: none; }")
        h_shadow = QGraphicsDropShadowEffect()
        h_shadow.setBlurRadius(30); h_shadow.setXOffset(0); h_shadow.setYOffset(6)
        h_shadow.setColor(QColor(108, 92, 231, 20))
        header_frame.setGraphicsEffect(h_shadow)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(28, 18, 28, 18)

        title_icon = QLabel("🔔")
        title_icon.setStyleSheet("font-size: 28px; background: transparent;")
        header_layout.addWidget(title_icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Centre de Notifications")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {COLORS['text_dark']}; background: transparent;")
        title_col.addWidget(title)
        self.notif_count_label = QLabel("Chargement...")
        self.notif_count_label.setStyleSheet("font-size: 13px; color: #94A3B8; background: transparent;")
        title_col.addWidget(self.notif_count_label)
        header_layout.addLayout(title_col)
        header_layout.addStretch()

        # Filter buttons
        self.notif_filter = "all"
        filter_btns_layout = QHBoxLayout()
        filter_btns_layout.setSpacing(8)
        filter_opts = [("Tout", "all"), ("Info", "info"), ("Alertes", "alerte"), ("Indispo.", "indisponibilite"), ("Annulation", "annulation")]
        self._filter_btn_refs = []
        for label, fval in filter_opts:
            fb = QPushButton(label)
            fb.setCursor(Qt.CursorShape.PointingHandCursor)
            fb.setFixedHeight(34)
            fb.setProperty("filter_val", fval)
            fb.clicked.connect(lambda _, v=fval, b=fb: self._set_notif_filter(v))
            self._filter_btn_refs.append(fb)
            filter_btns_layout.addWidget(fb)
        header_layout.addLayout(filter_btns_layout)
        self._update_filter_btn_styles()

        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setFixedHeight(38)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
                color: white; border: none; border-radius: 10px;
                font-weight: 600; font-size: 13px; padding: 0 20px;
            }}
            QPushButton:hover {{ background: {COLORS['primary_dark']}; }}
        """)
        btn_refresh.clicked.connect(self._refresh_notifications_table)
        header_layout.addWidget(btn_refresh)

        layout.addWidget(header_frame)

        # ── Scrollable notification cards area ──
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #F1F5F9; width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1; min-height: 30px; border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover { background: #94A3B8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self.notif_cards_container = QWidget()
        self.notif_cards_container.setStyleSheet("background: transparent;")
        self.notif_cards_layout = QVBoxLayout(self.notif_cards_container)
        self.notif_cards_layout.setSpacing(12)
        self.notif_cards_layout.setContentsMargins(4, 4, 4, 4)
        self.notif_cards_layout.addStretch()

        scroll.setWidget(self.notif_cards_container)
        layout.addWidget(scroll)

        self._load_notifications_data()
        return page

    def _set_notif_filter(self, filter_val):
        self.notif_filter = filter_val
        self._update_filter_btn_styles()
        self._load_notifications_data()

    def _update_filter_btn_styles(self):
        for btn in self._filter_btn_refs:
            fv = btn.property("filter_val")
            if fv == self.notif_filter:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {COLORS['primary']}; color: white;
                        border: none; border-radius: 8px;
                        font-weight: 600; font-size: 12px; padding: 0 14px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: #F1F5F9; color: #64748B;
                        border: 1px solid #E2E8F0; border-radius: 8px;
                        font-size: 12px; padding: 0 14px;
                    }}
                    QPushButton:hover {{ background: #E2E8F0; color: {COLORS['primary']}; }}
                """)

    def _load_notifications_data(self):
        """Load notifications into beautiful cards"""
        # Clear existing cards
        while self.notif_cards_layout.count() > 1:
            item = self.notif_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            conn = self.db.get_connection()
            cur = conn.cursor()
            
            all_items = []
            
            # 1. Real notifications
            cur.execute("""
                SELECT n.date_creation, n.type_notification, n.titre, n.message, n.lue
                FROM notifications n 
                WHERE n.destinataire_id = ?
                ORDER BY n.date_creation DESC
                LIMIT 50
            """, (self.user.id,))
            for row in cur.fetchall():
                all_items.append({
                    'date': str(row[0])[:16] if row[0] else "",
                    'type': row[1], 'titre': row[2],
                    'message': row[3], 'lue': row[4]
                })
            
            # 2. Teacher indisponibilité declarations
            try:
                cur.execute("""
                    SELECT d.date_debut, u.nom, u.prenom, d.motif
                    FROM disponibilites d JOIN utilisateurs u ON d.enseignant_id = u.id
                    ORDER BY d.id DESC LIMIT 30
                """)
                for row in cur.fetchall():
                    all_items.append({
                        'date': str(row[0]) if row[0] else "",
                        'type': 'indisponibilite',
                        'titre': f"Indisponibilité: {row[1]} {row[2]}",
                        'message': row[3] or "Pas de motif",
                        'lue': 1
                    })
            except:
                pass
            
            conn.close()
            
            # Sort by date (newest first)
            all_items.sort(key=lambda x: x['date'], reverse=True)

            # Apply filter
            if self.notif_filter != "all":
                all_items = [n for n in all_items if n['type'] == self.notif_filter]

            self.notif_count_label.setText(f"{len(all_items)} notification(s)")

            if not all_items:
                empty = QFrame()
                empty.setStyleSheet("QFrame { background: white; border-radius: 16px; border: 2px dashed #E2E8F0; }")
                el = QVBoxLayout(empty)
                el.setContentsMargins(40, 60, 40, 60)
                el.setAlignment(Qt.AlignmentFlag.AlignCenter)
                ei = QLabel("🔕")
                ei.setAlignment(Qt.AlignmentFlag.AlignCenter)
                ei.setStyleSheet("font-size: 48px; background: transparent; border: none;")
                el.addWidget(ei)
                et = QLabel("Aucune notification")
                et.setAlignment(Qt.AlignmentFlag.AlignCenter)
                et.setStyleSheet("font-size: 16px; font-weight: 600; color: #94A3B8; background: transparent; border: none;")
                el.addWidget(et)
                self.notif_cards_layout.insertWidget(0, empty)
            else:
                for item in all_items:
                    card = self._create_notif_card_admin(item)
                    self.notif_cards_layout.insertWidget(self.notif_cards_layout.count() - 1, card)

            # Mark as read
            self.db.marquer_toutes_notifications_lues(self.user.id)
        except Exception as e:
            print(f"Erreur notifs: {e}")

    def _create_notif_card_admin(self, item):
        """Create a beautiful notification card for admin"""
        type_config = {
            'info':             {'icon': 'ℹ️',  'color': '#3B82F6', 'bg': '#EFF6FF',  'label': 'Information'},
            'modification':     {'icon': '🔄', 'color': '#6C5CE7', 'bg': '#F0EDFF',  'label': 'Modification'},
            'annulation':       {'icon': '❌', 'color': '#EF4444', 'bg': '#FEF2F2',  'label': 'Annulation'},
            'alerte':           {'icon': '⚠️',  'color': '#F59E0B', 'bg': '#FFFBEB',  'label': 'Alerte'},
            'reservation':      {'icon': '📋', 'color': '#10B981', 'bg': '#ECFDF5',  'label': 'Réservation'},
            'indisponibilite':  {'icon': '🚷', 'color': '#E17055', 'bg': '#FFF5F0',  'label': 'Indisponibilité'},
            'rappel':           {'icon': '🔔', 'color': '#8B5CF6', 'bg': '#F5F3FF',  'label': 'Rappel'},
        }
        cfg = type_config.get(item['type'], {'icon': '🔔', 'color': '#64748B', 'bg': '#F8FAFC', 'label': item['type']})
        is_unread = not item.get('lue', True)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 14px;
                border-left: 4px solid {cfg['color']};
                {"border: 2px solid " + cfg['color'] + ";" if is_unread else ""}
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16 if is_unread else 10)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 18 if is_unread else 10))
        card.setGraphicsEffect(shadow)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(14)

        # Left: Icon circle
        icon_frame = QFrame()
        icon_frame.setFixedSize(48, 48)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {cfg['bg']};
                border-radius: 24px;
                border: none;
            }}
        """)
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel(cfg['icon'])
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 22px; background: transparent; border: none;")
        icon_layout.addWidget(icon_label)
        card_layout.addWidget(icon_frame)

        # Middle: Title + Message
        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        badge = QLabel(cfg['label'].upper())
        badge.setStyleSheet(f"""
            background-color: {cfg['bg']}; color: {cfg['color']};
            font-size: 10px; font-weight: 700;
            padding: 3px 10px; border-radius: 6px;
            border: none;
        """)
        badge.setFixedHeight(22)
        top_row.addWidget(badge)

        if is_unread:
            new_badge = QLabel("● NOUVEAU")
            new_badge.setStyleSheet(f"color: {cfg['color']}; font-size: 10px; font-weight: 700; background: transparent; border: none;")
            top_row.addWidget(new_badge)

        top_row.addStretch()

        date_label = QLabel(f"🕐  {item['date']}")
        date_label.setStyleSheet("color: #94A3B8; font-size: 11px; background: transparent; border: none;")
        top_row.addWidget(date_label)

        text_col.addLayout(top_row)

        titre_label = QLabel(item['titre'])
        titre_label.setWordWrap(True)
        titre_weight = "700" if is_unread else "600"
        titre_label.setStyleSheet(f"color: #1E293B; font-size: 14px; font-weight: {titre_weight}; background: transparent; border: none;")
        text_col.addWidget(titre_label)

        msg = item['message'][:200]
        if len(item['message']) > 200:
            msg += "..."
        msg_label = QLabel(msg)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: #64748B; font-size: 12px; line-height: 1.4; background: transparent; border: none;")
        text_col.addWidget(msg_label)

        card_layout.addLayout(text_col, 1)

        return card

    def _bold_font(self):
        from PyQt6.QtGui import QFont
        f = QFont()
        f.setBold(True)
        return f

    def _refresh_notifications_table(self):
        """Refresh the notifications table"""
        self._load_notifications_data()

    def switch_page(self, page_id):
        titles = {
            "Dashboard": ("Tableau de Bord", "Vue d'ensemble de votre système"),
            "Generation": ("Génération Emploi du Temps", "Importez les données et générez l'emploi"),
            "Rooms": ("Occupation des Salles", "Visualisez la disponibilité des salles en temps réel"),
            "Reservations": ("Gestion des Réservations", "Gérez les demandes de réservation des salles"),
            "Notifications": ("Notifications Système", "Suivez les alertes et notifications")
        }
        t, s = titles.get(page_id, (page_id, ""))
        self.page_title.setText(t)
        self.page_subtitle.setText(s)
        if page_id in ("Notifications", "Reservations"):
            self.page_subtitle.setStyleSheet("color: #607c9b; font-size: 14px;")
        else:
            self.page_subtitle.setStyleSheet(f"color: {COLORS.get('text_light', '#888')}; font-size: 14px;")
        
        for pid, btn in self.menu_buttons.items():
            btn.setChecked(pid == page_id)
            
        mapping = {"Dashboard": 0, "Generation": 1, "Rooms": 2, "Reservations": 3, "Notifications": 4}
        if page_id in mapping:
            self.pages.setCurrentIndex(mapping[page_id])
            if page_id == "Rooms":
                self._refresh_rooms_status()