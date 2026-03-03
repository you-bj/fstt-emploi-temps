# src/logic/timetable_export_service.py
"""
Timetable Export Service - Backend logic for exporting timetables
Supports PDF, Excel, and Image (PNG/JPG) formats
"""

import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from config import EXPORT_FOLDER, ETABLISSEMENT, ANNEE_UNIVERSITAIRE

# Check for optional export libraries
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


class TimetableExportService:
    """Service for exporting timetables in various formats"""
    
    def __init__(self, db):
        """
        Initialize the export service
        Args:
            db: Database instance
        """
        self.db = db
        # Ensure export folder exists
        os.makedirs(EXPORT_FOLDER, exist_ok=True)
    
    def export_group_timetable(self, groupe_id: int, format_type: str = "pdf",
                              semaine_debut: str = None, semaine_fin: str = None,
                              custom_filepath: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Exports group timetable for students
        Args:
            groupe_id: Group ID
            format_type: Export format ("pdf", "excel", "png", "jpg")
            semaine_debut: Start week date (optional)
            semaine_fin: End week date (optional)
            custom_filepath: Custom file path (optional, if not provided uses EXPORT_FOLDER)
        Returns:
            (success, file_path, error_message)
        """
        try:
            # Get group information
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM groupes WHERE id = ?", (groupe_id,))
            groupe = cursor.fetchone()
            
            if not groupe:
                conn.close()
                return False, None, "Groupe introuvable"
            
            # Handle both tuple and dict access
            groupe_nom = groupe[1] if isinstance(groupe, tuple) else groupe.get('nom', f"Groupe_{groupe_id}")
            
            # Get seances for the group
            if semaine_debut and semaine_fin:
                seances = self.db.get_seances_by_groupe(groupe_id, semaine_debut, semaine_fin)
            else:
                seances = self.db.get_seances_by_groupe(groupe_id)
            
            conn.close()
            
            # Convert seances to dict format if needed
            seances_dict = []
            for s in seances:
                if isinstance(s, tuple):
                    seances_dict.append({
                        'id': s[0], 'titre': s[1], 'type_seance': s[2],
                        'date': s[3], 'heure_debut': s[4], 'heure_fin': s[5],
                        'salle_id': s[6], 'enseignant_id': s[7], 'groupe_id': s[8]
                    })
                elif isinstance(s, dict):
                    seances_dict.append(s)
                else:
                    try:
                        seances_dict.append(dict(s))
                    except (TypeError, ValueError):
                        continue
            
            # Prepare data for export
            export_data = self._prepare_timetable_data(seances_dict, groupe_nom, None)
            
            # Export based on format
            filename = f"emploi_du_temps_groupe_{groupe_nom}"
            if format_type.lower() == "pdf":
                return self._export_pdf(export_data, filename, custom_filepath)
            elif format_type.lower() in ["excel", "xlsx"]:
                return self._export_excel(export_data, filename, custom_filepath)
            elif format_type.lower() in ["png", "jpg", "jpeg"]:
                return self._export_image(export_data, filename, format_type, custom_filepath)
            else:
                return False, None, f"Format non supporté: {format_type}"
                
        except Exception as e:
            return False, None, f"Erreur lors de l'export: {e}"
    
    def export_teacher_timetable(self, enseignant_id: int, format_type: str = "pdf",
                                semaine_debut: str = None, semaine_fin: str = None,
                                custom_filepath: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Exports teacher personal timetable (including manual reservations)
        Args:
            enseignant_id: Teacher ID
            format_type: Export format ("pdf", "excel", "png", "jpg")
            semaine_debut: Start week date (optional)
            semaine_fin: End week date (optional)
            custom_filepath: Custom file path (optional, if not provided uses EXPORT_FOLDER)
        Returns:
            (success, file_path, error_message)
        """
        try:
            # Get teacher information
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM utilisateurs WHERE id = ?", (enseignant_id,))
            enseignant = cursor.fetchone()
            
            if not enseignant:
                conn.close()
                return False, None, "Enseignant introuvable"
            
            # Handle both tuple and dict access
            if isinstance(enseignant, tuple):
                # Structure: (id, nom, prenom, email, mot_de_passe, type_user, specialite, groupe_id, duree_max_jour, date_creation)
                enseignant_nom = f"{enseignant[2]} {enseignant[1]}"
            else:
                enseignant_nom = f"{enseignant.get('prenom', '')} {enseignant.get('nom', '')}"
            
            # Get seances for the teacher
            if semaine_debut and semaine_fin:
                seances = self.db.get_seances_by_enseignant(enseignant_id, semaine_debut, semaine_fin)
            else:
                seances = self.db.get_seances_by_enseignant(enseignant_id)
            
            # Convert seances to dict format
            seances_dict = []
            for s in seances:
                if isinstance(s, tuple):
                    seances_dict.append({
                        'id': s[0], 'titre': s[1], 'type_seance': s[2],
                        'date': s[3], 'heure_debut': s[4], 'heure_fin': s[5],
                        'salle_id': s[6], 'enseignant_id': s[7], 'groupe_id': s[8]
                    })
                elif isinstance(s, dict):
                    seances_dict.append(s)
                else:
                    try:
                        seances_dict.append(dict(s))
                    except (TypeError, ValueError):
                        continue
            
            # Get approved reservations for the teacher
            cursor.execute('''
                SELECT * FROM reservations
                WHERE enseignant_id = ? AND statut = 'validee'
            ''', (enseignant_id,))
            reservations_tuples = cursor.fetchall()
            
            # Convert reservations to seance format for display
            for res in reservations_tuples:
                if isinstance(res, tuple):
                    # Structure: (id, enseignant_id, salle_id, date, heure_debut, heure_fin, statut, motif, date_demande)
                    seances_dict.append({
                        'id': res[0],
                        'titre': f"Réservation - {res[7] or ''}",
                        'type_seance': 'Réservation',
                        'date': res[3],
                        'heure_debut': res[4],
                        'heure_fin': res[5],
                        'salle_id': res[2],
                        'enseignant_id': res[1],
                        'groupe_id': None
                    })
                else:
                    try:
                        res_dict = dict(res) if not isinstance(res, dict) else res
                        seances_dict.append({
                            'id': res_dict['id'],
                            'titre': f"Réservation - {res_dict.get('motif', '')}",
                            'type_seance': 'Réservation',
                            'date': res_dict['date'],
                            'heure_debut': res_dict['heure_debut'],
                            'heure_fin': res_dict['heure_fin'],
                            'salle_id': res_dict['salle_id'],
                            'enseignant_id': res_dict['enseignant_id'],
                            'groupe_id': None
                        })
                    except (TypeError, KeyError, ValueError):
                        continue
            
            conn.close()
            
            # Prepare data for export
            export_data = self._prepare_timetable_data(seances_dict, None, enseignant_nom)
            
            # Export based on format
            filename = f"emploi_du_temps_{enseignant_nom.replace(' ', '_')}"
            if format_type.lower() == "pdf":
                return self._export_pdf(export_data, filename, custom_filepath)
            elif format_type.lower() in ["excel", "xlsx"]:
                return self._export_excel(export_data, filename, custom_filepath)
            elif format_type.lower() in ["png", "jpg", "jpeg"]:
                return self._export_image(export_data, filename, format_type, custom_filepath)
            else:
                return False, None, f"Format non supporté: {format_type}"
                
        except Exception as e:
            return False, None, f"Erreur lors de l'export: {e}"
    
    def _prepare_timetable_data(self, seances: List, groupe_nom: Optional[str],
                               enseignant_nom: Optional[str]) -> Dict:
        """
        Prepares timetable data for export
        Args:
            seances: List of sessions (as dictionaries)
            groupe_nom: Group name (for student export)
            enseignant_nom: Teacher name (for teacher export)
        Returns:
            Dictionary with formatted data
        """
        # Get room names
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Organize by day and time
        weekly_schedule = {}
        days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
        
        for day in days:
            weekly_schedule[day] = []
        
        for seance in seances:
            date_str = seance.get('date', '')
            # Ensure date is a string
            if date_str and not isinstance(date_str, str):
                date_str = str(date_str)
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                day_name = days[date_obj.weekday()]
            except (ValueError, IndexError, TypeError):
                continue
            
            # Get room name
            salle_id = seance.get('salle_id')
            salle_nom = "N/A"
            if salle_id:
                cursor.execute("SELECT nom FROM salles WHERE id = ?", (salle_id,))
                salle = cursor.fetchone()
                if salle:
                    salle_nom = salle[0] if isinstance(salle, tuple) else salle.get('nom', 'N/A')
            
            # Get teacher name (for group timetable)
            enseignant_id = seance.get('enseignant_id')
            enseignant_nom_seance = "N/A"
            if enseignant_id:
                cursor.execute("SELECT nom, prenom FROM utilisateurs WHERE id = ?", (enseignant_id,))
                enseignant = cursor.fetchone()
                if enseignant:
                    if isinstance(enseignant, tuple):
                        enseignant_nom_seance = f"{enseignant[1]} {enseignant[0]}"
                    else:
                        enseignant_nom_seance = f"{enseignant.get('prenom', '')} {enseignant.get('nom', '')}"
            
            # Get group name (for teacher timetable)
            groupe_id = seance.get('groupe_id')
            groupe_nom_seance = "N/A"
            if groupe_id:
                cursor.execute("SELECT nom FROM groupes WHERE id = ?", (groupe_id,))
                groupe = cursor.fetchone()
                if groupe:
                    groupe_nom_seance = groupe[0] if isinstance(groupe, tuple) else groupe.get('nom', 'N/A')
            
            weekly_schedule[day_name].append({
                'time': f"{seance.get('heure_debut', '')} - {seance.get('heure_fin', '')}",
                'course': seance.get('titre', ''),
                'type': seance.get('type_seance', ''),
                'room': salle_nom,
                'teacher': enseignant_nom_seance,
                'group': groupe_nom_seance
            })
        
        conn.close()
        
        # Sort by time for each day
        for day in days:
            weekly_schedule[day].sort(key=lambda x: x['time'])
        
        return {
            'title': f"Emploi du Temps - {groupe_nom if groupe_nom else enseignant_nom}",
            'subtitle': f"{ETABLISSEMENT} - {ANNEE_UNIVERSITAIRE}",
            'groupe_nom': groupe_nom,
            'enseignant_nom': enseignant_nom,
            'schedule': weekly_schedule,
            'period': self._get_period_string(seances)
        }
    
    def _get_period_string(self, seances: List) -> str:
        """Gets period string from seances"""
        if not seances:
            return "Période non spécifiée"
        
        dates = [s.get('date') for s in seances if s.get('date')]
        if not dates:
            return "Période non spécifiée"
        
        try:
            # Ensure all dates are strings
            date_objs = [datetime.strptime(str(d), "%Y-%m-%d") for d in dates if d]
            if date_objs:
                min_date = min(date_objs)
                max_date = max(date_objs)
                return f"{min_date.strftime('%d/%m/%Y')} - {max_date.strftime('%d/%m/%Y')}"
        except ValueError:
            pass
        
        return "Période non spécifiée"
    
    def _get_type_color(self, session_type: str) -> str:
        """Returns color hex based on session type (matching UI table view)"""
        type_lower = (session_type or '').lower()
        if 'cours' in type_lower:
            return '#4F46E5'  # Indigo for Cours
        elif 'td' in type_lower:
            return '#059669'  # Green for TD
        elif 'tp' in type_lower:
            return '#D97706'  # Amber for TP
        elif 'rattrapage' in type_lower:
            return '#EF4444'  # Red for Rattrapage
        elif 'réservation' in type_lower or 'reservation' in type_lower:
            return '#8B5CF6'  # Purple for Reservation
        else:
            return '#6B7280'  # Gray for others
    
    def _get_type_color_rgb(self, session_type: str) -> tuple:
        """Returns RGB color tuple based on session type"""
        type_lower = (session_type or '').lower()
        if 'cours' in type_lower:
            return (79, 70, 229)   # Indigo for Cours
        elif 'td' in type_lower:
            return (5, 150, 105)   # Green for TD
        elif 'tp' in type_lower:
            return (217, 119, 6)   # Amber for TP
        elif 'rattrapage' in type_lower:
            return (239, 68, 68)   # Red for Rattrapage
        elif 'réservation' in type_lower or 'reservation' in type_lower:
            return (139, 92, 246)  # Purple for Reservation
        else:
            return (107, 114, 128) # Gray for others

    def _export_pdf(self, data: Dict, filename: str, custom_filepath: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Exports timetable to PDF in grid format (days as rows, time slots as columns)
        Matches the university reference style with module legend, alternating colors, and notes.
        """
        try:
            if custom_filepath:
                filepath = custom_filepath
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
            else:
                filepath = os.path.join(EXPORT_FOLDER, f"{filename}.pdf")
            
            if not HAS_REPORTLAB:
                return self._export_text_fallback(data, filename, "pdf", custom_filepath)
            
            doc = SimpleDocTemplate(
                filepath,
                pagesize=landscape(A4),
                rightMargin=1*cm, leftMargin=1*cm,
                topMargin=0.8*cm, bottomMargin=0.8*cm
            )
            
            elements = []
            styles = getSampleStyleSheet()
            
            # ═══ HEADER: University + Year ═══
            header_table_data = [
                [Paragraph("<b>Université Abdelmalek Essaâdi</b><br/>Faculté des Sciences et Techniques - Tanger", 
                          ParagraphStyle('Left', parent=styles['Normal'], fontSize=10, leading=14)),
                 Paragraph(f"<b>Année Universitaire {ANNEE_UNIVERSITAIRE}</b>", 
                          ParagraphStyle('Right', parent=styles['Normal'], fontSize=10, alignment=2))]
            ]
            header_table = Table(header_table_data, colWidths=[14*cm, 14*cm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 0.3*cm))
            
            # ═══ TITLE: Emploi du Temps ═══
            title_style = ParagraphStyle('GridTitle', parent=styles['Normal'], fontSize=13, 
                                          alignment=1, spaceAfter=4, fontName='Helvetica-Bold')
            subtitle_style = ParagraphStyle('GridSubtitle', parent=styles['Normal'], fontSize=11, 
                                            alignment=1, spaceAfter=2, fontName='Helvetica-Bold')
            info_style = ParagraphStyle('GridInfo', parent=styles['Normal'], fontSize=11, 
                                        alignment=1, spaceAfter=2, fontName='Helvetica-BoldOblique')
            
            elements.append(Paragraph("<u>Emploi du Temps</u>", title_style))
            
            if data.get('groupe_nom'):
                elements.append(Paragraph(f"«Filière : {data['groupe_nom']}»", info_style))
            elif data.get('enseignant_nom'):
                elements.append(Paragraph(f"Enseignant : {data['enseignant_nom']}", info_style))
            
            elements.append(Spacer(1, 0.3*cm))
            
            # ═══ MODULE LEGEND BOX ═══
            days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
            time_slots = ["09:00 - 10:30", "10:45 - 12:15", "12:30 - 14:00", "14:15 - 15:45", "16:00 - 17:30"]
            
            # Collect unique modules
            modules = {}
            for day in days:
                for session in data['schedule'].get(day, []):
                    course = session.get('course', '')
                    if course and course not in modules:
                        modules[course] = session.get('type', '')
            
            if modules:
                legend_lines = []
                for i, (mod_name, mod_type) in enumerate(modules.items()):
                    label = f"M{i+1}" if len(mod_name) > 25 else mod_name
                    legend_lines.append(f"<b>{mod_name}</b>")
                
                legend_text = "<br/>".join(legend_lines)
                legend_para = Paragraph(legend_text, ParagraphStyle('Legend', parent=styles['Normal'], 
                                        fontSize=8, leading=11, leftIndent=4))
                
                legend_table = Table([[legend_para]], colWidths=[26*cm])
                legend_table.setStyle(TableStyle([
                    ('BOX', (0, 0), (-1, -1), 1, colors.black),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(legend_table)
                elements.append(Spacer(1, 0.3*cm))
            
            # ═══ GRID TABLE ═══
            # Map sessions to grid slots
            def match_time_slot(session_time, slots):
                """Match a session time string to one of the predefined slots"""
                # Try exact match first
                for i, slot in enumerate(slots):
                    if session_time == slot:
                        return i
                # Try matching by start time
                try:
                    session_start = session_time.split(" - ")[0].strip()
                    for i, slot in enumerate(slots):
                        slot_start = slot.split(" - ")[0].strip()
                        if session_start == slot_start:
                            return i
                except:
                    pass
                return None
            
            # Build grid: first row = headers
            cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, 
                                         alignment=1, leading=10)
            cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontSize=8, 
                                       alignment=1, leading=10, fontName='Helvetica-Bold')
            header_cell = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontSize=9, 
                                          alignment=1, fontName='Helvetica-Bold', textColor=colors.black)
            
            # Header row
            header_labels = [""] + [s.replace(" - ", " - ") for s in time_slots]
            grid_data = [[Paragraph(h, header_cell) for h in header_labels]]
            
            # Day rows (each day gets 2 rows for module + salle)
            for day in days:
                sessions = data['schedule'].get(day, [])
                
                # Build cells for this day
                row_cells = [Paragraph(f"<b>{day.upper()}</b>", 
                            ParagraphStyle('DayCell', parent=styles['Normal'], fontSize=9, 
                                           fontName='Helvetica-Bold'))]
                
                for slot in time_slots:
                    # Find session for this slot
                    matched_session = None
                    for s in sessions:
                        slot_idx = match_time_slot(s['time'], time_slots)
                        if slot_idx is not None and time_slots[slot_idx] == slot:
                            matched_session = s
                            break
                    
                    if matched_session:
                        course_name = matched_session['course'][:25]
                        room_name = matched_session['room']
                        session_type = matched_session.get('type', '')
                        cell_text = f"<b>{course_name}</b><br/>{session_type} | {room_name}"
                        row_cells.append(Paragraph(cell_text, cell_style))
                    else:
                        row_cells.append(Paragraph("", cell_style))
                
                grid_data.append(row_cells)
            
            # Create grid table
            col_widths = [2.8*cm] + [4.7*cm] * 5  # Day column + 5 time slot columns
            grid_table = Table(grid_data, colWidths=col_widths, rowHeights=[0.8*cm] + [1.4*cm] * 6)
            
            # Grid styling
            grid_style = [
                # Header row
                ('BACKGROUND', (1, 0), (-1, 0), colors.HexColor('#D9E2F3')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                
                # All cells
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                
                # Day column bold
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('LEFTPADDING', (0, 1), (0, -1), 6),
            ]
            
            # Alternating row colors (blue/white like reference)
            for row_idx in range(1, len(grid_data)):
                if row_idx % 2 == 0:
                    grid_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#D9E2F3')))
                else:
                    grid_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.white))
            
            grid_table.setStyle(TableStyle(grid_style))
            elements.append(grid_table)
            
            # ═══ FOOTER NOTES ═══
            elements.append(Spacer(1, 0.5*cm))
            note_style = ParagraphStyle('Note', parent=styles['Normal'], fontSize=8, leading=11)
            elements.append(Paragraph(
                "<b><u>N.B :</u></b>   "
                ". Les plannings de Travaux Pratiques seront affichés dans les départements concernés.<br/>"
                "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                ". Le Vendredi après-midi, les cours commencent à 15h00",
                note_style
            ))
            
            doc.build(elements)
            return True, filepath, None
        except Exception as e:
            return False, None, f"Erreur export PDF: {e}"
    
    def _export_excel(self, data: Dict, filename: str, custom_filepath: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Exports timetable to Excel in grid format (days as rows, time slots as columns)
        Matches the PDF grid layout.
        """
        try:
            if custom_filepath:
                filepath = custom_filepath
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
            else:
                filepath = os.path.join(EXPORT_FOLDER, f"{filename}.xlsx")
            
            if not HAS_OPENPYXL:
                return self._export_csv_fallback(data, filename, custom_filepath)
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Emploi du Temps"
            
            # Styles
            header_fill = PatternFill(start_color="1e3a8a", end_color="1e3a8a", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True, size=11)
            light_blue_fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
            left_align = Alignment(horizontal='left', vertical='center', wrap_text=True)
            
            days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
            time_slots = ["09:00 - 10:30", "10:45 - 12:15", "12:30 - 14:00", "14:15 - 15:45", "16:00 - 17:30"]
            
            # ═══ HEADER ═══
            ws.merge_cells('A1:F1')
            ws['A1'] = "Université Abdelmalek Essaâdi - Faculté des Sciences et Techniques - Tanger"
            ws['A1'].font = Font(bold=True, size=12)
            ws['A1'].alignment = Alignment(horizontal='center')
            
            ws.merge_cells('A2:F2')
            ws['A2'] = f"Année Universitaire {ANNEE_UNIVERSITAIRE}"
            ws['A2'].font = Font(bold=True, size=11)
            ws['A2'].alignment = Alignment(horizontal='center')
            
            ws.merge_cells('A3:F3')
            title_text = "Emploi du Temps"
            if data.get('groupe_nom'):
                title_text += f" - Filière : {data['groupe_nom']}"
            elif data.get('enseignant_nom'):
                title_text += f" - {data['enseignant_nom']}"
            ws['A3'] = title_text
            ws['A3'].font = Font(bold=True, size=13, underline='single')
            ws['A3'].alignment = Alignment(horizontal='center')
            
            # ═══ MODULE LEGEND ═══
            modules = set()
            for day in days:
                for session in data['schedule'].get(day, []):
                    course = session.get('course', '')
                    if course:
                        modules.add(course)
            
            row_offset = 5
            if modules:
                ws.merge_cells(f'A{row_offset}:F{row_offset}')
                ws[f'A{row_offset}'] = "Modules : " + " | ".join(sorted(modules))
                ws[f'A{row_offset}'].font = Font(bold=True, size=9)
                ws[f'A{row_offset}'].border = border
                ws[f'A{row_offset}'].alignment = left_align
                row_offset += 2
            
            # ═══ GRID HEADER ROW ═══
            header_row = row_offset
            headers = [""] + time_slots
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=header_row, column=col, value=header)
                cell.fill = light_blue_fill
                cell.font = Font(bold=True, size=10)
                cell.border = border
                cell.alignment = center_align
            
            # Helper to match time slots
            def match_time_slot(session_time, slots):
                for i, slot in enumerate(slots):
                    if session_time == slot:
                        return i
                try:
                    session_start = session_time.split(" - ")[0].strip()
                    for i, slot in enumerate(slots):
                        slot_start = slot.split(" - ")[0].strip()
                        if session_start == slot_start:
                            return i
                except:
                    pass
                return None
            
            # ═══ DAY ROWS ═══
            for day_idx, day in enumerate(days):
                row = header_row + 1 + day_idx
                sessions = data['schedule'].get(day, [])
                
                # Day name cell
                day_cell = ws.cell(row=row, column=1, value=day.upper())
                day_cell.font = Font(bold=True, size=10)
                day_cell.border = border
                day_cell.alignment = left_align
                
                # Alternating row colors
                if day_idx % 2 == 1:
                    day_cell.fill = light_blue_fill
                
                # Time slot cells
                for slot_idx, slot in enumerate(time_slots):
                    col = slot_idx + 2
                    cell = ws.cell(row=row, column=col)
                    cell.border = border
                    cell.alignment = center_align
                    
                    if day_idx % 2 == 1:
                        cell.fill = light_blue_fill
                    
                    # Find session for this slot
                    matched = None
                    for s in sessions:
                        si = match_time_slot(s['time'], time_slots)
                        if si is not None and time_slots[si] == slot:
                            matched = s
                            break
                    
                    if matched:
                        course_name = matched['course'][:30]
                        session_type = matched.get('type', '')
                        room_name = matched['room']
                        cell.value = f"{course_name}\n{session_type} | {room_name}"
                        cell.font = Font(bold=True, size=9)
            
            # ═══ FOOTER NOTES ═══
            note_row = header_row + 1 + len(days) + 1
            ws.merge_cells(f'A{note_row}:F{note_row}')
            ws[f'A{note_row}'] = "N.B : Les plannings de TP seront affichés dans les départements concernés. Le Vendredi après-midi, les cours commencent à 15h00."
            ws[f'A{note_row}'].font = Font(italic=True, size=8)
            
            # Column widths
            ws.column_dimensions['A'].width = 14
            for i, col_letter in enumerate(['B', 'C', 'D', 'E', 'F']):
                ws.column_dimensions[col_letter].width = 25
            
            # Row heights
            for day_idx in range(len(days)):
                ws.row_dimensions[header_row + 1 + day_idx].height = 45
            
            wb.save(filepath)
            return True, filepath, None
        except Exception as e:
            return False, None, f"Erreur export Excel: {e}"
    
    def _export_image(self, data: Dict, filename: str, format_type: str, custom_filepath: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Exports timetable to Image (PNG/JPG) using Pillow — grid format matching PDF/Excel
        """
        try:
            if custom_filepath:
                filepath = custom_filepath
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
            else:
                filepath = os.path.join(EXPORT_FOLDER, f"{filename}.{format_type.lower()}")
            
            if not HAS_PILLOW:
                return self._export_text_fallback(data, filename, format_type, custom_filepath)
            
            days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
            time_slots = ["09:00 - 10:30", "10:45 - 12:15", "12:30 - 14:00", "14:15 - 15:45", "16:00 - 17:30"]
            
            # Grid dimensions
            day_col_width = 120
            slot_col_width = 200
            row_height = 60
            header_height = 40
            
            num_cols = len(time_slots) + 1  # day column + time slots
            grid_width = day_col_width + slot_col_width * len(time_slots)
            
            # Image dimensions
            margin = 40
            width = grid_width + 2 * margin
            header_area = 130  # university title area
            grid_height = header_height + row_height * len(days)
            footer_area = 80
            height = header_area + grid_height + footer_area + 2 * margin
            
            img = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Fonts
            try:
                title_font = ImageFont.truetype("arial.ttf", 18)
                header_font = ImageFont.truetype("arial.ttf", 13)
                text_font = ImageFont.truetype("arial.ttf", 11)
                small_font = ImageFont.truetype("arial.ttf", 9)
            except:
                title_font = ImageFont.load_default()
                header_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Colors
            header_bg = (217, 226, 243)       # #D9E2F3 light blue
            alt_row_bg = (217, 226, 243)
            border_color = (0, 0, 0)
            text_color = (0, 0, 0)
            gray_text = (100, 100, 100)
            
            # ═══ HEADER AREA ═══
            y = margin
            uni_text = "Université Abdelmalek Essaâdi - Faculté des Sciences et Techniques - Tanger"
            draw.text((width // 2 - len(uni_text) * 4, y), uni_text, fill=text_color, font=header_font)
            y += 25
            year_text = f"Année Universitaire {ANNEE_UNIVERSITAIRE}"
            draw.text((width // 2 - len(year_text) * 4, y), year_text, fill=text_color, font=header_font)
            y += 25
            title_text = "Emploi du Temps"
            if data.get('groupe_nom'):
                title_text += f" - Filière : {data['groupe_nom']}"
            elif data.get('enseignant_nom'):
                title_text += f" - {data['enseignant_nom']}"
            draw.text((width // 2 - len(title_text) * 5, y), title_text, fill=text_color, font=title_font)
            y += 35
            
            # ═══ MODULE LEGEND ═══
            modules = set()
            for day in days:
                for session in data['schedule'].get(day, []):
                    course = session.get('course', '')
                    if course:
                        modules.add(course)
            if modules:
                legend_text = "Modules : " + " | ".join(sorted(modules))
                draw.text((margin, y), legend_text, fill=gray_text, font=small_font)
                y += 20
            
            # ═══ GRID ═══
            grid_top = y
            grid_left = margin
            
            # Helper to match time slots
            def match_time_slot(session_time, slots):
                for i, slot in enumerate(slots):
                    if session_time == slot:
                        return i
                try:
                    session_start = session_time.split(" - ")[0].strip()
                    for i, slot in enumerate(slots):
                        slot_start = slot.split(" - ")[0].strip()
                        if session_start == slot_start:
                            return i
                except:
                    pass
                return None
            
            # Draw header row
            draw.rectangle([grid_left, grid_top, grid_left + day_col_width, grid_top + header_height], fill=header_bg, outline=border_color)
            # Empty corner cell
            x = grid_left + day_col_width
            for slot in time_slots:
                draw.rectangle([x, grid_top, x + slot_col_width, grid_top + header_height], fill=header_bg, outline=border_color)
                draw.text((x + 10, grid_top + 12), slot, fill=text_color, font=header_font)
                x += slot_col_width
            
            # Draw day rows
            for day_idx, day in enumerate(days):
                row_top = grid_top + header_height + day_idx * row_height
                sessions = data['schedule'].get(day, [])
                
                # Alternating row color
                row_bg = alt_row_bg if day_idx % 2 == 1 else (255, 255, 255)
                
                # Day cell
                draw.rectangle([grid_left, row_top, grid_left + day_col_width, row_top + row_height], fill=row_bg, outline=border_color)
                draw.text((grid_left + 8, row_top + 22), day.upper(), fill=text_color, font=header_font)
                
                # Time slot cells
                x = grid_left + day_col_width
                for slot_idx, slot in enumerate(time_slots):
                    cell_x = x + slot_idx * slot_col_width
                    draw.rectangle([cell_x, row_top, cell_x + slot_col_width, row_top + row_height], fill=row_bg, outline=border_color)
                    
                    # Find matching session
                    matched = None
                    for s in sessions:
                        si = match_time_slot(s['time'], time_slots)
                        if si is not None and time_slots[si] == slot:
                            matched = s
                            break
                    
                    if matched:
                        course = matched['course'][:25]
                        stype = matched.get('type', '')
                        room = matched['room']
                        draw.text((cell_x + 5, row_top + 8), course, fill=text_color, font=text_font)
                        draw.text((cell_x + 5, row_top + 24), f"{stype} | {room}", fill=gray_text, font=small_font)
            
            # ═══ FOOTER ═══
            footer_y = grid_top + header_height + len(days) * row_height + 15
            footer_text = "N.B : Les plannings de TP seront affichés dans les départements concernés."
            draw.text((margin, footer_y), footer_text, fill=gray_text, font=small_font)
            
            # Save
            if format_type.lower() in ('jpg', 'jpeg'):
                img = img.convert('RGB')
            img.save(filepath)
            
            return True, filepath, None
        except Exception as e:
            return False, None, f"Erreur export Image: {e}"
    
    def _export_text_fallback(self, data: Dict, filename: str, format_type: str, custom_filepath: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """Fallback text export when libraries not available"""
        try:
            # Use custom filepath if provided, otherwise use EXPORT_FOLDER
            if custom_filepath:
                # Change extension to .txt
                filepath = os.path.splitext(custom_filepath)[0] + ".txt"
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
            else:
                filepath = os.path.join(EXPORT_FOLDER, f"{filename}.txt")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"{data['title']}\n")
                f.write(f"{data['subtitle']}\n")
                f.write(f"Période: {data['period']}\n")
                f.write("=" * 60 + "\n\n")
                
                for day, sessions in data['schedule'].items():
                    if sessions:
                        f.write(f"\n{day}:\n")
                        f.write("-" * 40 + "\n")
                        for session in sessions:
                            f.write(f"  {session['time']} - {session['course']} ({session['type']})\n")
                            f.write(f"    Salle: {session['room']}\n")
                            if session.get('teacher') and session['teacher'] != 'N/A':
                                f.write(f"    Enseignant: {session['teacher']}\n")
                            if session.get('group') and session['group'] != 'N/A':
                                f.write(f"    Groupe: {session['group']}\n")
            
            return True, filepath, f"Note: {format_type.upper()} library not installed. Text file created instead."
        except Exception as e:
            return False, None, f"Erreur export: {e}"
    
    def _export_csv_fallback(self, data: Dict, filename: str, custom_filepath: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """Fallback CSV export when openpyxl not available"""
        try:
            import csv
            # Use custom filepath if provided, otherwise use EXPORT_FOLDER
            if custom_filepath:
                # Change extension to .csv
                filepath = os.path.splitext(custom_filepath)[0] + ".csv"
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
            else:
                filepath = os.path.join(EXPORT_FOLDER, f"{filename}.csv")
            
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([data['title']])
                writer.writerow([data['subtitle']])
                writer.writerow([f"Période: {data['period']}"])
                writer.writerow([])
                writer.writerow(['Jour', 'Horaire', 'Cours', 'Type', 'Salle', 'Enseignant', 'Groupe'])
                
                for day, sessions in data['schedule'].items():
                    if sessions:
                        for session in sessions:
                            writer.writerow([
                                day,
                                session['time'],
                                session['course'],
                                session['type'],
                                session['room'],
                                session.get('teacher', 'N/A'),
                                session.get('group', 'N/A')
                            ])
            
            return True, filepath, "Note: Excel library not installed. CSV file created instead."
        except Exception as e:
            return False, None, f"Erreur export CSV: {e}"

