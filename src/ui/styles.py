# src/ui/styles.py
"""
Modern Design System — UniSchedule FSTT
Sleek dark sidebar • Glassmorphism cards • Vibrant gradients
"""

from configUI import COLORS

# ═══════════════════════════════════════════════════════════
# GLOBAL APPLICATION STYLE
# ═══════════════════════════════════════════════════════════

GLOBAL_STYLE = f"""
QWidget {{
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 14px;
    color: {COLORS['text_dark']};
}}
QFrame, QLabel, QPushButton {{
    border: none;
}}
QToolTip {{
    background: {COLORS['bg_sidebar']};
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 13px;
}}
"""

# ═══════════════════════════════════════════════════════════
# LOGIN PAGE STYLES
# ═══════════════════════════════════════════════════════════

LOGIN_TITLE_STYLE = f"""
QLabel {{
    color: {COLORS['primary']};
    font-size: 28px;
    font-weight: 800;
    letter-spacing: 0.5px;
}}
"""

LOGIN_SUBTITLE_STYLE = f"""
QLabel {{
    color: {COLORS['text_medium']};
    font-size: 14px;
    padding: 4px 0;
}}
"""

LOGIN_MAIN_BUTTON_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
    color: white;
    font-size: 22px;
    font-weight: 700;
    padding: 22px 56px;
    border: none;
    border-radius: 16px;
    letter-spacing: 2px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary_dark']}, stop:1 {COLORS['secondary_dark']});
}}
QPushButton:pressed {{
    background: {COLORS['primary_dark']};
}}
"""

LOGIN_FORM_CONTAINER_STYLE = f"""
QFrame {{
    background-color: rgba(255, 255, 255, 0.97);
    border-radius: 24px;
    border: 1px solid rgba(108, 92, 231, 0.15);
}}
"""

LOGIN_INPUT_STYLE = f"""
QLineEdit {{
    background-color: {COLORS['bg_light']};
    border: 2px solid #E8E8EE;
    border-radius: 12px;
    padding: 14px 16px;
    font-size: 15px;
    color: {COLORS['text_dark']};
}}
QLineEdit:focus {{
    border: 2px solid {COLORS['primary']};
    background-color: #FFFFFF;
}}
QLineEdit:hover {{
    border: 2px solid {COLORS['primary_light']};
}}
"""

LOGIN_LABEL_STYLE = f"""
QLabel {{
    color: {COLORS['text_dark']};
    font-size: 13px;
    font-weight: 600;
    padding: 4px 0;
}}
"""

LOGIN_SUBMIT_BUTTON_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
    color: white;
    font-size: 16px;
    font-weight: 700;
    padding: 14px;
    border: none;
    border-radius: 12px;
    letter-spacing: 0.5px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary_dark']}, stop:1 {COLORS['secondary_dark']});
}}
QPushButton:disabled {{
    background: #D5D5E0;
    color: #999;
}}
"""

LOGIN_QUIT_BUTTON_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: {COLORS['text_medium']};
    font-size: 14px;
    padding: 12px;
    border: 2px solid #DDD;
    border-radius: 12px;
}}
QPushButton:hover {{
    background-color: {COLORS['error']};
    color: white;
    border: 2px solid {COLORS['error']};
}}
"""

LOGIN_ERROR_STYLE = f"""
QLabel {{
    color: {COLORS['error']};
    font-size: 13px;
    padding: 10px 14px;
    background-color: rgba(255, 118, 117, 0.1);
    border-left: 4px solid {COLORS['error']};
    border-radius: 8px;
}}
"""

LOGIN_SUCCESS_STYLE = f"""
QLabel {{
    color: {COLORS['success']};
    font-size: 13px;
    padding: 10px 14px;
    background-color: rgba(0, 184, 148, 0.1);
    border-left: 4px solid {COLORS['success']};
    border-radius: 8px;
}}
"""

# ═══════════════════════════════════════════════════════════
# SIDEBAR STYLES
# ═══════════════════════════════════════════════════════════

SIDEBAR_STYLE = f"""
QFrame {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['sidebar_top']}, stop:0.5 {COLORS['sidebar_mid']}, stop:1 {COLORS['sidebar_bot']});
    border: none;
}}
"""

SIDEBAR_BUTTON_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: rgba(255, 255, 255, 0.75);
    text-align: left;
    padding: 14px 24px;
    font-size: 15px;
    font-weight: 500;
    border: none;
    border-radius: 12px;
    margin: 2px 14px;
}}
QPushButton:hover {{
    background: rgba(255, 255, 255, 0.08);
    color: #FFFFFF;
}}
QPushButton:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
    color: white;
    font-weight: 700;
}}
"""

SIDEBAR_TITLE_STYLE = f"""
QLabel {{
    color: white;
    font-size: 16px;
    font-weight: 800;
    letter-spacing: 2px;
    background: transparent;
}}
"""

SIDEBAR_USER_INFO_STYLE = """
QFrame {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    margin: 8px 14px;
}
"""

SIDEBAR_HEADER_STYLE = f"""
QFrame {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
    border: none;
}}
"""

# ═══════════════════════════════════════════════════════════
# TABLE STYLES
# ═══════════════════════════════════════════════════════════

TABLE_STYLE = f"""
QTableWidget {{
    background-color: white;
    border: none;
    border-radius: 16px;
    gridline-color: #F0F0F5;
    font-size: 13px;
}}
QTableWidget::item {{
    padding: 12px 16px;
    border-bottom: 1px solid #F0F0F5;
    color: {COLORS['text_dark']};
}}
QTableWidget::item:selected {{
    background-color: rgba(108, 92, 231, 0.08);
    color: {COLORS['primary']};
}}
QHeaderView::section {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_dark']});
    color: white;
    font-weight: 600;
    font-size: 13px;
    padding: 14px 16px;
    border: none;
}}
QTableWidget QTableCornerButton::section {{
    background: {COLORS['primary']};
    border: none;
}}
"""

# ═══════════════════════════════════════════════════════════
# BUTTON STYLES
# ═══════════════════════════════════════════════════════════

PRIMARY_BUTTON_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
    color: white;
    font-size: 14px;
    font-weight: 600;
    padding: 12px 28px;
    border: none;
    border-radius: 10px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary_dark']}, stop:1 {COLORS['secondary_dark']});
}}
QPushButton:disabled {{
    background: #D5D5E0;
    color: #999;
}}
"""

SECONDARY_BUTTON_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: {COLORS['primary']};
    font-size: 14px;
    font-weight: 600;
    padding: 12px 28px;
    border: 2px solid {COLORS['primary']};
    border-radius: 10px;
}}
QPushButton:hover {{
    background-color: {COLORS['primary']};
    color: white;
}}
"""

SUCCESS_BUTTON_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['success']}, stop:1 #55EFC4);
    color: white;
    font-size: 14px;
    font-weight: 600;
    padding: 12px 28px;
    border: none;
    border-radius: 10px;
}}
QPushButton:hover {{
    background: {COLORS['success']};
}}
"""

DANGER_BUTTON_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['error']}, stop:1 #FAB1A0);
    color: white;
    font-size: 14px;
    font-weight: 600;
    padding: 12px 28px;
    border: none;
    border-radius: 10px;
}}
QPushButton:hover {{
    background: {COLORS['error']};
}}
"""

# ═══════════════════════════════════════════════════════════
# CARD STYLES
# ═══════════════════════════════════════════════════════════

CARD_STYLE = f"""
QFrame {{
    background-color: white;
    border: 1px solid rgba(0, 0, 0, 0.04);
    border-radius: 20px;
}}
"""

CARD_TITLE_STYLE = f"""
QLabel {{
    color: {COLORS['text_dark']};
    font-size: 18px;
    font-weight: 700;
}}
"""

CARD_VALUE_STYLE = f"""
QLabel {{
    color: {COLORS['primary']};
    font-size: 36px;
    font-weight: 800;
}}
"""

# ═══════════════════════════════════════════════════════════
# SCHEDULE
# ═══════════════════════════════════════════════════════════

SCHEDULE_GRID_STYLE = """
QFrame {
    background-color: white;
    border: none;
    border-radius: 20px;
}
"""

SCHEDULE_CELL_COURS_STYLE = f"""
QLabel {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_light']});
    color: white;
    padding: 8px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 11px;
}}
"""

SCHEDULE_CELL_TD_STYLE = f"""
QLabel {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {COLORS['success']}, stop:1 #55EFC4);
    color: white;
    padding: 8px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 11px;
}}
"""

SCHEDULE_CELL_TP_STYLE = f"""
QLabel {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #FDCB6E, stop:1 #F9CA24);
    color: {COLORS['text_dark']};
    padding: 8px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 11px;
}}
"""

SCHEDULE_CELL_EXAMEN_STYLE = f"""
QLabel {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {COLORS['error']}, stop:1 {COLORS['accent']});
    color: white;
    padding: 8px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 11px;
}}
"""

# ═══════════════════════════════════════════════════════════
# INPUT STYLES
# ═══════════════════════════════════════════════════════════

INPUT_STYLE = f"""
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit, QTimeEdit {{
    background-color: {COLORS['bg_light']};
    border: 2px solid #E8E8EE;
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 14px;
    color: {COLORS['text_dark']};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {{
    border: 2px solid {COLORS['primary']};
    background: white;
}}
QComboBox::drop-down {{
    border: none;
    width: 32px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_medium']};
    margin-right: 10px;
}}
QComboBox QAbstractItemView {{
    background: white;
    border: 1px solid #E8E8EE;
    border-radius: 12px;
    selection-background-color: rgba(108, 92, 231, 0.08);
    selection-color: {COLORS['primary']};
    padding: 4px;
}}
"""

# ═══════════════════════════════════════════════════════════
# SCROLLBAR
# ═══════════════════════════════════════════════════════════

SCROLLBAR_STYLE = f"""
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    border-radius: 4px;
    margin: 4px 0;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['primary_light']};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['primary']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['primary_light']};
    border-radius: 4px;
    min-width: 24px;
}}
"""

# ═══════════════════════════════════════════════════════════
# CHART & PAGE TITLES
# ═══════════════════════════════════════════════════════════

CHART_CONTAINER_STYLE = """
QFrame {
    background-color: white;
    border: 1px solid rgba(0, 0, 0, 0.04);
    border-radius: 20px;
}
"""

CHART_TITLE_STYLE = f"""
QLabel {{
    color: {COLORS['text_dark']};
    font-size: 16px;
    font-weight: 700;
}}
"""

PAGE_TITLE_STYLE = f"""
QLabel {{
    color: {COLORS['text_dark']};
    font-size: 28px;
    font-weight: 800;
}}
"""

LOGOUT_BUTTON_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: {COLORS['error']};
    border: 2px solid {COLORS['error']};
    border-radius: 12px;
    padding: 12px 20px;
    margin: 8px 14px 16px 14px;
    font-weight: 600;
    font-size: 14px;
}}
QPushButton:hover {{
    background-color: {COLORS['error']};
    color: white;
    border: 2px solid {COLORS['error']};
}}
"""

# ═══════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════

def get_icon_button_style(color=None):
    bg = color or COLORS['primary']
    return f"""
    QPushButton {{
        background-color: {bg};
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px;
        font-size: 14px;
        font-weight: 600;
    }}
    QPushButton:hover {{ opacity: 0.85; }}
    """

SOBER_BUTTON_STYLE = f"""
QPushButton {{
    background-color: transparent;
    color: {COLORS['text_dark']};
    font-size: 14px;
    font-weight: 500;
    padding: 12px 24px;
    border: 1px solid #E0E0E8;
    border-radius: 10px;
}}
QPushButton:hover {{
    border: 1px solid {COLORS['primary']};
    color: {COLORS['primary']};
    background-color: rgba(108, 92, 231, 0.04);
}}
"""