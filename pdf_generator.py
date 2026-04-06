#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de reportes PDF con integracion ISO
CORREGIDO: Guarda en unidad de red Z: si está en modo servidor
"""
from fpdf import FPDF
from datetime import datetime
import config
import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'REPORTE DE BIOPSIA DE ALIENTO - SISTEMA DENCO', 0, 1, 'C')
        self.set_font('Arial', 'I', 8)
        beta = config.PARAMETROS_CALCULADOS['beta']
        self.cell(0, 4, f'Venturi: beta={beta:.3f} | '
                  f'D={config.VENTURI_CONFIG["D_entrada_mm"]:.2f}mm '
                  f'd={config.VENTURI_CONFIG["D_cuello_mm"]:.2f}mm', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generar_pdf(paciente_info, muestras, volumen_total, resumen,
                duracion_ms, flujo_max, flujo_min,
                correlacion, pendiente, riesgo, cluster, curva_img, corr_img,
                emisiones_iso):
    """Genera el PDF de reporte completo - VERSION CORREGIDA CON SOPORTE SERVIDOR"""
    
    pdf = PDF()
    pdf.add_page()
    
    # Datos del paciente
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f"Paciente: {paciente_info['nombre']}", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, f"Edad: {paciente_info['edad']} anos | Peso: {paciente_info['peso']} kg", 0, 1)
    pdf.cell(0, 5, f"Contacto: {paciente_info['contacto']}", 0, 1)
    if paciente_info.get('email'):
        pdf.cell(0, 5, f"Email: {paciente_info['email']}", 0, 1)
    pdf.cell(0, 5, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 0, 1)
    pdf.ln(5)
    
    # Parametros del Venturi
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 6, "Parametros del Tubo Venturi (ISO 5167-4):", 0, 1)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 4, f"  Diametro entrada: {config.VENTURI_CONFIG['D_entrada_mm']:.2f} mm | "
              f"Garganta: {config.VENTURI_CONFIG['D_cuello_mm']:.2f} mm", 0, 1)
    pdf.cell(0, 4, f"  Relacion beta: {config.PARAMETROS_CALCULADOS['beta']:.3f} | "
              f"Area garganta: {config.PARAMETROS_CALCULADOS['area_cuello_m2']*1e6:.2f} mm2", 0, 1)
    pdf.ln(3)
    
    # ISO 13138
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 6, "Clasificacion Segun ISO 13138 (Convenciones de Muestreo):", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    
    num_alveolares = sum(1 for m in muestras if m.get('fraccion') == 'ALVEOLAR')
    num_muerto = sum(1 for m in muestras if m.get('fraccion') == 'ESPACIO_MUERTO')
    
    pdf.multi_cell(0, 4, "  Este sistema discrimina automaticamente entre el aire del espacio muerto "
                         "(vias aereas superiores) y la fraccion alveolar, alineandose con la "
                         "convencion de muestreo de la norma ISO 13138:2012.")
    pdf.ln(2)
    pdf.cell(0, 4, f"  - Muestras de Espacio Muerto (Traqueobronquial): {num_muerto}", 0, 1)
    pdf.cell(0, 4, f"  - Muestras de Fraccion Alveolar (Intercambio Gaseoso): {num_alveolares}", 0, 1)
    pdf.ln(3)
    
    # ISO 16000-9
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 102, 51)
    pdf.cell(0, 6, "Calculos de Emision Segun Principios de ISO 16000-9:", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 4, "  Los siguientes calculos de tasa de emision y concentracion masica "
                         "siguen los principios establecidos en la norma ISO 16000-9 para la "
                         "determinacion de emisiones de compuestos organicos volatiles (VOC).")
    pdf.ln(2)
    pdf.cell(0, 4, f"  - Concentracion Masica (µg/m³): {emisiones_iso['concentracion_ug_m3']:.1f}", 0, 1)
    pdf.cell(0, 4, f"  - Tasa de Emision (µg/min): {emisiones_iso['tasa_emision_ug_min']:.2f}", 0, 1)
    pdf.cell(0, 4, f"  - Masa Total de VOC Emitidos (µg): {emisiones_iso['masa_total_ug']:.2f}", 0, 1)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 4, f"    (Calculado usando masa molar promedio de {config.ISO_CONFIG['masa_molar_voc_g_mol']} g/mol)", 0, 1)
    pdf.set_font('Arial', '', 9)
    pdf.ln(5)
    
    # Biomarcadores
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 6, "Biomarcadores Cuantitativos (Alveolares):", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, f"  TVOC medio: {resumen['tvoc']:.0f} ppb", 0, 1)
    pdf.cell(0, 5, f"  eCO2 medio: {resumen['eco2']:.0f} ppm", 0, 1)
    pdf.cell(0, 5, f"  Temperatura media: {resumen['temp']:.1f} °C", 0, 1)
    pdf.cell(0, 5, f"  Humedad media: {resumen['hum']:.1f} %", 0, 1)
    pdf.ln(3)
    
    # Parametros de flujo
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 6, "Parametros de Flujo (ISO 5167-4):", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, f"  Flujo volumetrico medio: {resumen['flujo_medio']:.3f} L/s", 0, 1)
    pdf.cell(0, 5, f"  Flujo maximo: {flujo_max:.3f} L/s | Minimo: {flujo_min:.3f} L/s", 0, 1)
    pdf.cell(0, 5, f"  Volumen total exhalado: {volumen_total:.3f} L", 0, 1)
    pdf.cell(0, 5, f"  Duracion de la exhalacion: {duracion_ms/1000:.2f} s", 0, 1)
    pdf.cell(0, 5, f"  Tasa de emision de VOC (ng/s): {emisiones_iso['tasa_emision_ng_s']:.2f}", 0, 1)
    pdf.set_text_color(0, 100, 200)
    pdf.cell(0, 5, f"  VOC totales exhalados (ng): {emisiones_iso['masa_total_ng']:.2f}", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # Correlacion
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 6, "Analisis de Correlacion VOC vs Flujo:", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, f"  Coeficiente de correlacion (r): {correlacion:.3f}", 0, 1)
    pdf.cell(0, 5, f"  Pendiente de regresion: {pendiente:.2f} ppb/(L/s)", 0, 1)
    if correlacion > 0.5:
        pdf.multi_cell(0, 5, "  Interpretacion: Correlacion positiva. Los VOC aumentan con el flujo.")
    elif correlacion < -0.5:
        pdf.multi_cell(0, 5, "  Interpretacion: Correlacion negativa. Patron a observar.")
    else:
        pdf.multi_cell(0, 5, "  Interpretacion: Correlacion debil. VOC de origen alveolar.")
    pdf.ln(5)
    
    # IA
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 6, "Analisis por IA No Supervisada:", 0, 1)
    pdf.set_font('Arial', '', 10)
    if riesgo < 0.3:
        estado = "PATRON METABOLICO NORMAL"
        color = (0,128,0)
        interp = "Los biomarcadores y flujo estan dentro del rango esperado."
    elif riesgo < 0.7:
        estado = "PATRON SOSPECHOSO"
        color = (255,140,0)
        interp = "Niveles moderadamente elevados. Recomendar seguimiento."
    else:
        estado = "PATRON ANOMALO"
        color = (255,0,0)
        interp = "Firma de VOC sugiere estres metabolico (Efecto Warburg)."
    pdf.set_text_color(*color)
    pdf.cell(0, 5, f"  {estado} (riesgo: {riesgo*100:.1f}%)", 0, 1)
    pdf.set_text_color(0,0,0)
    pdf.multi_cell(0, 5, f"  {interp}")
    pdf.ln(5)
    
    # Gráficos - VERSIÓN CORREGIDA
    if curva_img and config.PDF_CONFIG['incluir_graficos']:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Evolucion Temporal de la Exhalacion', 0, 1, 'C')
        
        # Guardar el buffer a un archivo temporal
        temp_file = config.PDF_CONFIG['directorio'] / 'temp_curva.png'
        with open(temp_file, 'wb') as f:
            f.write(curva_img.getvalue())
        pdf.image(str(temp_file), x=10, w=190)
        temp_file.unlink()  # Eliminar archivo temporal
    
    if corr_img and config.PDF_CONFIG['incluir_graficos']:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Analisis de Correlacion VOC vs Flujo', 0, 1, 'C')
        
        temp_file = config.PDF_CONFIG['directorio'] / 'temp_corr.png'
        with open(temp_file, 'wb') as f:
            f.write(corr_img.getvalue())
        pdf.image(str(temp_file), x=10, w=190)
        temp_file.unlink()  # Eliminar archivo temporal
    
    # Nota legal
    pdf.add_page()
    pdf.set_font('Arial', 'I', 8)
    pdf.multi_cell(0, 4, config.PDF_CONFIG['nota_legal'])
    
    # Guardar PDF - AHORA EN LA UBICACIÓN CORRECTA (Z:/ o local)
    filename = config.PDF_CONFIG['nombre_formato'].format(
        paciente=paciente_info['nombre'].replace(' ', '_'),
        fecha=datetime.now().strftime('%Y%m%d_%H%M%S')
    )
    filepath = config.PDF_CONFIG['directorio'] / filename
    
    # Asegurarse de que el directorio de destino existe
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"No se pudo crear el directorio {filepath.parent}: {e}")
        # Fallback al directorio local
        fallback_dir = Path.cwd() / 'reportes'
        fallback_dir.mkdir(exist_ok=True)
        filepath = fallback_dir / filename
        logger.info(f"Usando directorio fallback: {filepath}")
    
    pdf.output(str(filepath))
    logger.info(f"📄 PDF guardado en: {filepath}")
    
    return filepath