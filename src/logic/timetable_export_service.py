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
        Exports timetable to PDF using reportlab with colored session types
        """
        try:
            # Use custom filepath if provided, otherwise use EXPORT_FOLDER
            if custom_filepath:
                filepath = custom_filepath
                # Ensure parent directory exists
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
            else:
                filepath = os.path.join(EXPORT_FOLDER, f"{filename}.pdf")
            
            if not HAS_REPORTLAB:
                # Fallback to text file if reportlab not available
                return self._export_text_fallback(data, filename, "pdf", custom_filepath)
            
            # Create PDF with reportlab
            doc = SimpleDocTemplate(
                filepath,
                pagesize=landscape(A4),
                rightMargin=1*cm,
                leftMargin=1*cm,
                topMargin=1*cm,
                bottomMargin=1*cm
            )
            
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Title'],
                fontSize=18,
                spaceAfter=12,
                alignment=1  # Center
            )
            elements.append(Paragraph(data['title'], title_style))
            
            # Subtitle
            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=6,
                alignment=1
            )
            elements.append(Paragraph(data['subtitle'], subtitle_style))
            elements.append(Paragraph(f"Période: {data['period']}", subtitle_style))
            
            # Role info
            if data.get('enseignant_nom'):
                elements.append(Paragraph(f"Enseignant: {data['enseignant_nom']}", subtitle_style))
            if data.get('groupe_nom'):
                elements.append(Paragraph(f"Groupe: {data['groupe_nom']}", subtitle_style))
            
            elements.append(Spacer(1, 0.5*cm))
            
            # Build table data and track row types for coloring
            days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
            table_data = [['Jour', 'Horaire', 'Cours', 'Type', 'Salle', 'Prof/Groupe']]
            row_types = []  # Track session types for each row
            
            for day in days:
                sessions = data['schedule'].get(day, [])
                if sessions:
                    for session in sessions:
                        teacher_or_group = session.get('teacher', '') or session.get('group', '')
                        table_data.append([
                            day,
                            session['time'],
                            session['course'][:30],  # Truncate long names
                            session['type'],
                            session['room'],
                            teacher_or_group[:20]
                        ])
                        row_types.append(session['type'])
            
            if len(table_data) > 1:
                # Create table
                table = Table(table_data, colWidths=[2*cm, 3*cm, 6*cm, 2.5*cm, 2.5*cm, 4*cm])
                
                # Base style
                style_commands = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
                ]
                
                # Add colored backgrounds for each row based on session type
                for row_idx, session_type in enumerate(row_types, start=1):
                    color_hex = self._get_type_color(session_type)
                    # Use lighter version of color for background
                    style_commands.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor(color_hex + '20')))
                    # Color the Type column cell with full color
                    style_commands.append(('BACKGROUND', (3, row_idx), (3, row_idx), colors.HexColor(color_hex)))
                    style_commands.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.white))
                
                table.setStyle(TableStyle(style_commands))
                elements.append(table)
                
                # Add legend
                elements.append(Spacer(1, 0.5*cm))
                legend_style = ParagraphStyle('Legend', parent=styles['Normal'], fontSize=9)
                legend_text = "Légende: "
                legend_items = [
                    ("<font color='#4F46E5'>■</font> Cours", "#4F46E5"),
                    ("<font color='#059669'>■</font> TD", "#059669"),
                    ("<font color='#D97706'>■</font> TP", "#D97706"),
                    ("<font color='#EF4444'>■</font> Rattrapage", "#EF4444"),
                ]
                elements.append(Paragraph(legend_text + "  |  ".join([f"<font color='{c}'><b>■</b></font> {t.split('>')[-1].split('<')[0]}" for t, c in legend_items]), legend_style))
            else:
                elements.append(Paragraph("Aucune séance programmée.", styles['Normal']))
            
            # Build PDF
            doc.build(elements)
            
            return True, filepath, None
        except Exception as e:
            return False, None, f"Erreur export PDF: {e}"
    
    def _export_excel(self, data: Dict, filename: str, custom_filepath: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Exports timetable to Excel using openpyxl with colored session types
        """
        try:
            # Use custom filepath if provided, otherwise use EXPORT_FOLDER
            if custom_filepath:
                filepath = custom_filepath
                # Ensure parent directory exists
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
            else:
                filepath = os.path.join(EXPORT_FOLDER, f"{filename}.xlsx")
            
            if not HAS_OPENPYXL:
                # Fallback to CSV if openpyxl not available
                return self._export_csv_fallback(data, filename, custom_filepath)
            
            # Create Excel workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Emploi du Temps"
            
            # Styles
            header_fill = PatternFill(start_color="1e3a8a", end_color="1e3a8a", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True, size=11)
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
            
            # Session type colors (matching UI)
            type_colors = {
                'cours': PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid"),
                'td': PatternFill(start_color="059669", end_color="059669", fill_type="solid"),
                'tp': PatternFill(start_color="D97706", end_color="D97706", fill_type="solid"),
                'rattrapage': PatternFill(start_color="EF4444", end_color="EF4444", fill_type="solid"),
                'reservation': PatternFill(start_color="8B5CF6", end_color="8B5CF6", fill_type="solid"),
            }
            type_row_colors = {
                'cours': PatternFill(start_color="EEF2FF", end_color="EEF2FF", fill_type="solid"),  # Light indigo
                'td': PatternFill(start_color="ECFDF5", end_color="ECFDF5", fill_type="solid"),     # Light green
                'tp': PatternFill(start_color="FFFBEB", end_color="FFFBEB", fill_type="solid"),     # Light amber
                'rattrapage': PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid"), # Light red
                'reservation': PatternFill(start_color="F5F3FF", end_color="F5F3FF", fill_type="solid"), # Light purple
            }
            
            # Title
            ws.merge_cells('A1:F1')
            ws['A1'] = data['title']
            ws['A1'].font = Font(bold=True, size=16)
            ws['A1'].alignment = Alignment(horizontal='center')
            
            ws.merge_cells('A2:F2')
            ws['A2'] = data['subtitle']
            ws['A2'].alignment = Alignment(horizontal='center')
            
            ws.merge_cells('A3:F3')
            ws['A3'] = f"Période: {data['period']}"
            ws['A3'].alignment = Alignment(horizontal='center')
            
            # Role info
            row_offset = 4
            if data.get('enseignant_nom'):
                ws.merge_cells(f'A{row_offset}:F{row_offset}')
                ws[f'A{row_offset}'] = f"Enseignant: {data['enseignant_nom']}"
                ws[f'A{row_offset}'].alignment = Alignment(horizontal='center')
                row_offset += 1
            if data.get('groupe_nom'):
                ws.merge_cells(f'A{row_offset}:F{row_offset}')
                ws[f'A{row_offset}'] = f"Groupe: {data['groupe_nom']}"
                ws[f'A{row_offset}'].alignment = Alignment(horizontal='center')
                row_offset += 1
            
            header_row = row_offset + 1
            
            # Headers
            headers = ['Jour', 'Horaire', 'Cours', 'Type', 'Salle', 'Prof/Groupe']
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=header_row, column=col, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.border = border
                cell.alignment = center_align
            
            # Data
            row = header_row + 1
            days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
            for day in days:
                sessions = data['schedule'].get(day, [])
                if sessions:
                    for session in sessions:
                        teacher_or_group = session.get('teacher', '') or session.get('group', '')
                        values = [
                            day,
                            session['time'],
                            session['course'],
                            session['type'],
                            session['room'],
                            teacher_or_group
                        ]
                        
                        # Determine color based on session type
                        session_type = (session['type'] or '').lower()
                        row_fill = None
                        type_fill = None
                        for key in type_row_colors:
                            if key in session_type:
                                row_fill = type_row_colors[key]
                                type_fill = type_colors[key]
                                break
                        
                        for col, value in enumerate(values, 1):
                            cell = ws.cell(row=row, column=col, value=value)
                            cell.border = border
                            cell.alignment = center_align
                            
                            # Apply row background color
                            if row_fill:
                                cell.fill = row_fill
                            
                            # Apply full color to Type column
                            if col == 4 and type_fill:
                                cell.fill = type_fill
                                cell.font = Font(color="FFFFFF", bold=True)
                        
                        row += 1
            
            # Add legend
            legend_row = row + 2
            ws.cell(row=legend_row, column=1, value="Légende:").font = Font(bold=True)
            legend_items = [
                ('Cours', '4F46E5'),
                ('TD', '059669'),
                ('TP', 'D97706'),
                ('Rattrapage', 'EF4444'),
            ]
            for i, (name, color) in enumerate(legend_items):
                cell = ws.cell(row=legend_row, column=i+2, value=name)
                cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = center_align
            
            # Adjust column widths
            ws.column_dimensions['A'].width = 12
            ws.column_dimensions['B'].width = 15
            ws.column_dimensions['C'].width = 30
            ws.column_dimensions['D'].width = 12
            ws.column_dimensions['E'].width = 12
            ws.column_dimensions['F'].width = 20
            
            # Save
            wb.save(filepath)
            
            return True, filepath, None
        except Exception as e:
            return False, None, f"Erreur export Excel: {e}"
    
    def _export_image(self, data: Dict, filename: str, format_type: str, custom_filepath: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Exports timetable to Image (PNG/JPG) using Pillow with colored session types
        """
        try:
            # Use custom filepath if provided, otherwise use EXPORT_FOLDER
            if custom_filepath:
                filepath = custom_filepath
                # Ensure parent directory exists
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
            else:
                filepath = os.path.join(EXPORT_FOLDER, f"{filename}.{format_type.lower()}")
            
            if not HAS_PILLOW:
                # Fallback to text file if Pillow not available
                return self._export_text_fallback(data, filename, format_type, custom_filepath)
            
            # Image dimensions
            width = 1200
            height = 900
            
            # Create image with white background
            img = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a better font, fallback to default
            try:
                title_font = ImageFont.truetype("arial.ttf", 24)
                header_font = ImageFont.truetype("arial.ttf", 14)
                text_font = ImageFont.truetype("arial.ttf", 12)
            except:
                title_font = ImageFont.load_default()
                header_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
            
            # Colors matching UI
            header_bg = (30, 58, 138)  # #1e3a8a
            header_text = (255, 255, 255)
            text_color = (0, 0, 0)
            border_color = (209, 213, 219)  # #d1d5db
            
            # Session type colors (matching UI)
            type_colors = {
                'cours': (79, 70, 229),    # Indigo
                'td': (5, 150, 105),       # Green
                'tp': (217, 119, 6),       # Amber
                'rattrapage': (239, 68, 68),  # Red
                'reservation': (139, 92, 246), # Purple
            }
            type_light_colors = {
                'cours': (238, 242, 255),    # Light indigo
                'td': (236, 253, 245),       # Light green
                'tp': (255, 251, 235),       # Light amber
                'rattrapage': (254, 242, 242),  # Light red
                'reservation': (245, 243, 255), # Light purple
            }
            
            # Draw title
            draw.text((width//2 - 200, 20), data['title'], fill=text_color, font=title_font)
            draw.text((width//2 - 150, 55), data['subtitle'], fill=(100, 100, 100), font=header_font)
            draw.text((width//2 - 100, 80), f"Période: {data['period']}", fill=(100, 100, 100), font=text_font)
            
            # Role info
            y_offset = 100
            if data.get('enseignant_nom'):
                draw.text((width//2 - 100, y_offset), f"Enseignant: {data['enseignant_nom']}", fill=(100, 100, 100), font=text_font)
                y_offset += 20
            if data.get('groupe_nom'):
                draw.text((width//2 - 100, y_offset), f"Groupe: {data['groupe_nom']}", fill=(100, 100, 100), font=text_font)
                y_offset += 20
            
            # Table dimensions
            table_top = y_offset + 20
            row_height = 30
            col_widths = [100, 120, 300, 100, 100, 200]
            x_start = 50
            
            # Draw header row
            x = x_start
            headers = ['Jour', 'Horaire', 'Cours', 'Type', 'Salle', 'Prof/Groupe']
            draw.rectangle([x, table_top, x + sum(col_widths), table_top + row_height], fill=header_bg)
            for i, header in enumerate(headers):
                draw.text((x + 5, table_top + 8), header, fill=header_text, font=header_font)
                x += col_widths[i]
            
            # Draw data rows
            y = table_top + row_height
            row_num = 0
            days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
            
            for day in days:
                sessions = data['schedule'].get(day, [])
                if sessions:
                    for session in sessions:
                        if y + row_height > height - 80:
                            break
                        
                        # Determine color based on session type
                        session_type = (session.get('type', '') or '').lower()
                        row_bg = (255, 255, 255)  # Default white
                        type_bg = (107, 114, 128)  # Default gray
                        
                        for key in type_colors:
                            if key in session_type:
                                row_bg = type_light_colors[key]
                                type_bg = type_colors[key]
                                break
                        
                        # Draw row background
                        draw.rectangle([x_start, y, x_start + sum(col_widths), y + row_height], fill=row_bg)
                        
                        # Draw row data
                        x = x_start
                        teacher_or_group = session.get('teacher', '') or session.get('group', '')
                        values = [day, session['time'], session['course'][:35], session['type'], session['room'], teacher_or_group[:20]]
                        for i, value in enumerate(values):
                            # Special handling for Type column (index 3)
                            if i == 3:
                                # Draw colored background for type
                                draw.rectangle([x, y, x + col_widths[i], y + row_height], fill=type_bg)
                                draw.text((x + 5, y + 8), str(value), fill=(255, 255, 255), font=text_font)
                            else:
                                draw.text((x + 5, y + 8), str(value), fill=text_color, font=text_font)
                            x += col_widths[i]
                        
                        y += row_height
                        row_num += 1
            
            # Draw grid lines
            for i in range(row_num + 2):
                y_line = table_top + i * row_height
                draw.line([(x_start, y_line), (x_start + sum(col_widths), y_line)], fill=border_color)
            
            x = x_start
            for col_width in col_widths + [0]:
                draw.line([(x, table_top), (x, table_top + (row_num + 1) * row_height)], fill=border_color)
                x += col_width
            
            # Draw legend
            legend_y = table_top + (row_num + 2) * row_height + 10
            draw.text((x_start, legend_y), "Légende:", fill=text_color, font=header_font)
            legend_x = x_start + 80
            for name, color in [('Cours', type_colors['cours']), ('TD', type_colors['td']), 
                               ('TP', type_colors['tp']), ('Rattrapage', type_colors['rattrapage'])]:
                draw.rectangle([legend_x, legend_y, legend_x + 60, legend_y + 20], fill=color)
                draw.text((legend_x + 5, legend_y + 3), name, fill=(255, 255, 255), font=text_font)
                legend_x += 80
            
            # Save image
            if format_type.lower() == 'jpg' or format_type.lower() == 'jpeg':
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
                writer.writerow(['Jour', 'Horaire', 'Cours', 'Type', 'Salle', 'Enseignant/Groupe'])
                
                for day, sessions in data['schedule'].items():
                    if sessions:
                        for session in sessions:
                            teacher_or_group = session.get('teacher') or session.get('group', '')
                            writer.writerow([
                                day,
                                session['time'],
                                session['course'],
                                session['type'],
                                session['room'],
                                teacher_or_group
                            ])
            
            return True, filepath, "Note: Excel library not installed. CSV file created instead."
        except Exception as e:
            return False, None, f"Erreur export CSV: {e}"

