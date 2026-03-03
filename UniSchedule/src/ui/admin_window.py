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
    GLOBAL_STYLE, PAGE_TITLE_STYLE
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
        """Update dashboard stats"""
        stats = self.calculate_stats()
        if hasattr(self, 'stat_cards'):
            self.stat_cards['Enseignants'].set_value(stats['enseignants'])
            self.stat_cards['Étudiants'].set_value(stats['etudiants'])
            self.stat_cards['Filières'].set_value(stats['filieres'])
            self.stat_cards['Matières'].set_value(stats['matieres'])

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
            
            # Logic for dates
            today = datetime.now()
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0: days_until_monday = 7
            next_monday = today + timedelta(days=days_until_monday)
            semaine_debut = next_monday.strftime("%Y-%m-%d")
            
            # Load existing
            existing_seances = self.db.get_toutes_seances()
            existing_seances_dict = [{'id':s[0], 'titre':s[1], 'type_seance':s[2], 'date':s[3], 'heure_debut':s[4], 'heure_fin':s[5], 'salle_id':s[6], 'enseignant_id':s[7], 'groupe_id':s[8]} for s in existing_seances] if existing_seances else []
            
            existing_res = self.db.get_toutes_reservations()
            existing_res_dict = [{'id':r[0], 'enseignant_id':r[1], 'salle_id':r[2], 'date':r[3], 'heure_debut':r[4], 'heure_fin':r[5], 'statut':r[6]} for r in existing_res] if existing_res else []
            
            generator = ScheduleGenerator(self.db, existing_seances_dict, existing_res_dict)
            
            # Tracking variables
            teacher_weekly_hours, teacher_daily_hours, group_daily_hours, group_weekly_hours = {}, {}, {}, {}
            NB_SUBJECTS_PER_GROUP = 6
            types_cours = [('Cours', 1.5, 1), ('TD', 1.5, 1)]
            
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
            
            progress.setValue(100)
            progress.close()
            
            if sessions_created > 0:
                msg = f"Génération terminée !\n\n• {sessions_created} séances créées\n• {total_groups} groupes traités"
                if errors: msg += f"\n\n⚠️ {len(errors)} avertissements"
                QMessageBox.information(self, "Succès", msg)
            else:
                QMessageBox.warning(self, "Attention", "Aucune séance créée.")
            self.refresh_dashboard()
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Erreur", f"Erreur fatale: {str(e)}")

    def handle_reservation(self, index, accepted):
        """Handle reservation approval/rejection with notifications"""
        if 0 <= index < len(self.reservations_data):
            data = self.reservations_data[index]
            res_id = data.get('db_id')
            
            if accepted:
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
                QMessageBox.information(self, "Succès", "Réservation approuvée et notifiée.")
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
        self.sidebar.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E1B4B, stop:0.5 #312E81, stop:1 #1E1B4B); }")
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(8)
        
        # Header
        header = QFrame()
        header.setFixedHeight(100)
        header.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #06B6D4); }")
        h_layout = QVBoxLayout(header)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("ADMINISTRATEUR")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: 700; background: transparent;")
        h_layout.addWidget(title)
        layout.addWidget(header)
        layout.addSpacing(16)
        
        # Menu
        self.menu_buttons = {}
        menus = [("Dashboard", "Dashboard"), ("Generer Emploi", "Generation"), ("Reservations", "Reservations"), ("Notifications", "Notifications")]
        
        for label, pid in menus:
            btn = QPushButton(f"  {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(48)
            btn.setStyleSheet("""
                QPushButton { background: transparent; color: #FFFFFF; text-align: left; padding: 12px 20px; font-size: 15px; font-weight: 600; border: none; border-radius: 12px; margin: 4px 16px; }
                QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(99, 102, 241, 0.3), stop:1 rgba(6, 182, 212, 0.2)); }
                QPushButton:checked { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #06B6D4); color: white; }
            """)
            btn.clicked.connect(lambda _, p=pid: self.switch_page(p))
            layout.addWidget(btn)
            self.menu_buttons[pid] = btn
            
        layout.addStretch()
        
        # User Info
        user_frame = QFrame()
        user_frame.setStyleSheet("QFrame { background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 14px; margin: 12px 16px; }")
        user_layout = QVBoxLayout(user_frame)
        avatar = QLabel("A")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8B5CF6, stop:1 #6366F1); color: white; font-size: 22px; font-weight: bold; border-radius: 25px; border: 2px solid rgba(255,255,255,0.3);")
        user_layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)
        user_name = QLabel(f"{self.user.nom}")
        user_name.setStyleSheet("color: white; font-size: 14px; font-weight: 600; background: transparent;")
        user_layout.addWidget(user_name, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(user_frame)
        
        # Logout
        logout = QPushButton("Deconnexion")
        logout.setCursor(Qt.CursorShape.PointingHandCursor)
        logout.setStyleSheet("QPushButton { background: transparent; color: #F87171; border: 2px solid #F87171; border-radius: 10px; padding: 12px; margin: 8px 16px; font-weight: 600; } QPushButton:hover { background: #EF4444; color: white; }")
        logout.clicked.connect(self.logout_signal.emit)
        layout.addWidget(logout)
        
        self.main_layout.addWidget(self.sidebar)

    def create_content_area(self):
        """Create main content area"""
        self.content_area = QFrame()
        self.content_area.setStyleSheet(f"QFrame {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {COLORS.get('bg_light', '#F3F6FB')}, stop:1 #E2E8F0); }}")
        
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(40, 32, 40, 32)
        content_layout.setSpacing(8)
        
        self.page_title = QLabel("Tableau de Bord")
        self.page_title.setStyleSheet(PAGE_TITLE_STYLE)
        content_layout.addWidget(self.page_title)
        
        self.page_subtitle = QLabel("Vue d'ensemble")
        self.page_subtitle.setStyleSheet(f"color: {COLORS.get('text_light', '#888')}; font-size: 14px; margin-bottom: 20px;")
        content_layout.addWidget(self.page_subtitle)
        
        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_dashboard_page())
        self.pages.addWidget(self.create_generation_page())
        self.pages.addWidget(self.create_reservations_page())
        self.pages.addWidget(self.create_notifications_page())
        
        content_layout.addWidget(self.pages)
        self.main_layout.addWidget(self.content_area)

    def create_dashboard_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Stats
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        current_stats = self.calculate_stats()
        
        # FIX: Added .get() with default hex codes to prevent key errors
        cards_config = [
            ("Enseignants", current_stats['enseignants'], "👨‍🏫", COLORS.get('card_purple', '#8B5CF6')),
            ("Étudiants", current_stats['etudiants'], "👨‍🎓", COLORS.get('card_cyan', '#06B6D4')),
            ("Filières", current_stats['filieres'], "📚", COLORS.get('card_emerald', '#10B981')),
            ("Matières", current_stats['matieres'], "📖", COLORS.get('card_amber', '#F59E0B'))
        ]
        
        self.stat_cards = {}
        for title, value, icon, color in cards_config:
            card = ModernStatCard(title, value, icon, color)
            self.stat_cards[title] = card
            stats_layout.addWidget(card)
        layout.addLayout(stats_layout)
        
        # Charts
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)
        
        # Donut
        try:
            salles = self.db.get_toutes_salles()
            type_counts = {}
            for s in salles: type_counts[s[3]] = type_counts.get(s[3], 0) + 1
            salles_data = [(k, v, COLORS.get('card_cyan', '#06B6D4')) for k, v in type_counts.items()]
        except: salles_data = []
        charts_layout.addWidget(ModernDonutChart(salles_data, "Répartition Salles"))
        
        # Bar
        heures_data = [("Lun", 24), ("Mar", 20), ("Mer", 18), ("Jeu", 22), ("Ven", 16)]
        charts_layout.addWidget(ModernBarChart(heures_data, "Volume Horaire"))
        
        layout.addLayout(charts_layout)
        return page

    def create_generation_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        
        # Import Card
        import_card = QFrame()
        import_card.setStyleSheet("background-color: white; border-radius: 16px; border: 1px solid #E2E8F0;")
        import_layout = QVBoxLayout(import_card)
        import_layout.addWidget(QLabel("Importation Données", styleSheet="font-size: 20px; font-weight: bold;"))
        
        self.upload_cards = {}
        grid = QGridLayout()
        btn_style = "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #06B6D4); color: white; border-radius: 8px; padding: 12px; font-weight: 600; }"
        
        for idx, (key, title) in enumerate([("salles", "Salles"), ("enseignants", "Enseignants"), ("etudiants", "Etudiants"), ("groupes", "Groupes")]):
            btn = QPushButton(title)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, k=key: self.run_import(k))
            self.upload_cards[key] = {'button': btn}
            grid.addWidget(btn, idx // 2, idx % 2)
        import_layout.addLayout(grid)
        layout.addWidget(import_card)
        
        # Generation Card
        gen_card = QFrame()
        gen_card.setStyleSheet("background-color: white; border-radius: 16px; border: 1px solid #E2E8F0;")
        gen_layout = QVBoxLayout(gen_card)
        gen_layout.addWidget(QLabel("Génération Automatique", styleSheet="font-size: 20px; font-weight: bold;"))
        
        self.btn_generate = QPushButton("Lancer la Génération de l'Emploi du Temps")
        self.btn_generate.setFixedHeight(50)
        self.btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate.setStyleSheet(btn_style)
        self.btn_generate.clicked.connect(self.run_generate_timetable)
        gen_layout.addWidget(self.btn_generate)
        layout.addWidget(gen_card)
        
        layout.addStretch()
        return page

    def _update_upload_status(self, key, success, filename=""):
        if key in self.upload_cards:
            btn = self.upload_cards[key]['button']
            if success:
                btn.setText(f"✓ {filename[:15]}...")
                btn.setStyleSheet("QPushButton { background: #10B981; color: white; border-radius: 8px; font-weight: 600; }")
            else:
                btn.setText("✗ Erreur")
                btn.setStyleSheet("QPushButton { background: #EF4444; color: white; border-radius: 8px; font-weight: 600; }")

    def create_reservations_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        
        header = QFrame()
        header.setStyleSheet("background: white; border-radius: 16px;")
        h_layout = QHBoxLayout(header)
        title = QLabel("Demandes")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E40AF;")
        self.counter_label = QLabel("0 attente")
        self.counter_label.setStyleSheet("background: #6A5ACD; color: white; padding: 8px; border-radius: 10px;")
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(self.counter_label)
        layout.addWidget(header)
        
        self.res_table = QTableWidget()
        self.res_table.setColumnCount(5)
        self.res_table.setHorizontalHeaderLabels(["DATE", "PROF", "SALLE", "MOTIF", "ACTIONS"])
        self.res_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.res_table.verticalHeader().setVisible(False)
        self.res_table.setStyleSheet("QTableWidget { background: white; border-radius: 12px; border: none; } QHeaderView::section { background: #6A5ACD; color: white; padding: 12px; border: none; }")
        layout.addWidget(self.res_table)
        
        self.refresh_reservations()
        return page

    def refresh_reservations(self):
        self.res_table.setRowCount(0)
        pending = sum(1 for r in self.reservations_data if 'status' not in r)
        self.counter_label.setText(f"{pending} demandes en attente")
        
        for i, row in enumerate(self.reservations_data):
            self.res_table.insertRow(i)
            self.res_table.setItem(i, 0, QTableWidgetItem(row.get('date')))
            self.res_table.setItem(i, 1, QTableWidgetItem(row.get('prof')))
            self.res_table.setItem(i, 2, QTableWidgetItem(row.get('salle')))
            self.res_table.setItem(i, 3, QTableWidgetItem(row.get('motif')))
            
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 5, 5, 5)
            
            if 'status' in row:
                lbl = QLabel(row['status'])
                color = "#10B981" if row['status'] == "Acceptée" else "#EF4444"
                lbl.setStyleSheet(f"color: white; background: {color}; padding: 4px 8px; border-radius: 6px;")
                layout.addWidget(lbl)
            else:
                btn_acc = QPushButton("✓")
                btn_acc.setStyleSheet("background: #10B981; color: white; border-radius: 6px; font-weight: bold; min-width: 30px;")
                btn_acc.clicked.connect(lambda _, idx=i: self.handle_reservation(idx, True))
                
                btn_ref = QPushButton("✗")
                btn_ref.setStyleSheet("background: #EF4444; color: white; border-radius: 6px; font-weight: bold; min-width: 30px;")
                btn_ref.clicked.connect(lambda _, idx=i: self.handle_reservation(idx, False))
                
                layout.addWidget(btn_acc)
                layout.addWidget(btn_ref)
            
            self.res_table.setCellWidget(i, 4, widget)

    def create_notifications_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        
        frame = QFrame()
        frame.setStyleSheet("background: white; border-radius: 16px;")
        f_layout = QVBoxLayout(frame)
        
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["DATE", "TYPE", "MESSAGE"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setStyleSheet("QTableWidget { border: none; } QHeaderView::section { background: #6A5ACD; color: white; padding: 12px; }")
        
        try:
            conn = self.db.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT d.date_debut, u.nom, u.prenom, d.motif FROM disponibilites d JOIN utilisateurs u ON d.enseignant_id = u.id ORDER BY d.id DESC LIMIT 20")
            rows = cur.fetchall()
            conn.close()
            table.setRowCount(len(rows))
            for i, (d, n, p, m) in enumerate(rows):
                table.setItem(i, 0, QTableWidgetItem(str(d)))
                table.setItem(i, 1, QTableWidgetItem("Indisponibilité"))
                table.setItem(i, 2, QTableWidgetItem(f"Prof {n} {p}: {m}"))
        except: pass
        
        f_layout.addWidget(table)
        layout.addWidget(frame)
        return page

    def switch_page(self, page_id):
        titles = {
            "Dashboard": ("Tableau de Bord", "Vue d'ensemble"),
            "Generation": ("Génération", "Importer et générer"),
            "Reservations": ("Réservations", "Gérer les demandes"),
            "Notifications": ("Notifications", "Alertes système")
        }
        t, s = titles.get(page_id, (page_id, ""))
        self.page_title.setText(t)
        self.page_subtitle.setText(s)
        
        for pid, btn in self.menu_buttons.items():
            btn.setChecked(pid == page_id)
            
        mapping = {"Dashboard": 0, "Generation": 1, "Reservations": 2, "Notifications": 3}
        if page_id in mapping: self.pages.setCurrentIndex(mapping[page_id])