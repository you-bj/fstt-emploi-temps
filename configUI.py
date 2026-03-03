import os
from pathlib import Path
from config import MESSAGES, BASE_DIR

# ═══════════════════════════════════════════════════════════
# CHEMINS DES ASSETS
# ═══════════════════════════════════════════════════════════

ASSETS_DIR = BASE_DIR / 'assets'
IMAGES_DIR = ASSETS_DIR / 'images'

# Créer les dossiers s'ils n'existent pas
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

FST_BACKGROUND_IMAGE = str(IMAGES_DIR / 'fst_background.png')
FST_LOGO_IMAGE = str(IMAGES_DIR / 'fst_log.png')

# ═══════════════════════════════════════════════════════════
# COULEURS (CHARTE GRAPHIQUE FSTT)
# ═══════════════════════════════════════════════════════════

COLORS = {
    # ─── Primary Palette ───
    'primary': '#6C5CE7',           # Vivid purple - main brand
    'primary_dark': '#5A4BD1',      # Darker purple (hover)
    'primary_light': '#A29BFE',     # Light purple (accents)
    'secondary': '#00CEC9',         # Vibrant teal - secondary
    'secondary_dark': '#00B5B0',    # Darker teal
    'accent': '#FD79A8',            # Coral pink - highlights
    'accent_warm': '#FDCB6E',       # Warm gold - badges
    
    # ─── Legacy keys (backwards compat) ───
    'primary_blue': '#6C5CE7',
    'secondary_blue': '#5A4BD1',
    'primary_yellow': '#FDCB6E',
    'secondary_yellow': '#F9CA24',
    
    # ─── Text ───
    'text_dark': '#2D3436',
    'text_medium': '#636E72',
    'text_light': '#B2BEC3',
    'text_white': '#FFFFFF',
    
    # ─── Backgrounds ───
    'bg_light': '#F8F9FD',
    'bg_dark': '#1A1A2E',
    'bg_card': '#FFFFFF',
    'bg_sidebar': '#16213E',
    
    # ─── Sidebar gradient stops ───
    'sidebar_top': '#0F3460',
    'sidebar_mid': '#16213E',
    'sidebar_bot': '#1A1A2E',
    
    # ─── Status ───
    'success': '#00B894',
    'error': '#FF7675',
    'warning': '#FFEAA7',
    'info': '#74B9FF',
    
    # ─── Stat card colors ───
    'card_purple': '#6C5CE7',
    'card_cyan': '#00CEC9',
    'card_emerald': '#00B894',
    'card_amber': '#FDCB6E',
    'card_rose': '#FD79A8',
    
    # ─── Overlay ───
    'overlay_dark': 'rgba(0, 0, 0, 180)',
    'glass': 'rgba(255, 255, 255, 0.08)',
}

# ═══════════════════════════════════════════════════════════
# CONFIGURATION DES FENÊTRES
# ═══════════════════════════════════════════════════════════

WINDOW_CONFIG = {
    'login': {
        'title': 'FST Tanger - Connexion',
        'width': 1280,
        'height': 720
    },
    'admin': {
        'title': 'FST Tanger - Administration',
        'width': 1400,
        'height': 900
    },
    'enseignant': {
        'title': 'FST Tanger - Espace Enseignant',
        'width': 1280,
        'height': 800
    },
    'etudiant': {
        'title': 'FST Tanger - Espace Étudiant',
        'width': 1280,
        'height': 800
    }
}
