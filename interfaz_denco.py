#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTERFAZ GRAFICA DENCO v3.9 - MODO SERVIDOR CON COMBOBOX FLUIDAS
MEJORADO v3.9:
 
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from datetime import datetime
import numpy as np
import sys
import os
from pathlib import Path
import logging
from difflib import get_close_matches

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Asegurar que podemos importar nuestros modulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importaciones de nuestro sistema
from database_manager import DatabaseManager
from modelo_ia import ModeloIA
from visualizador import Visualizador
from pdf_generator import generar_pdf
from captura_serial import SerialManager, calcular_emisiones_iso16000
from buscador_dialog import BuscadorDialog
from analisis_evolucion import AnalizadorEvolucion
import config

# Configurar matplotlib para Tkinter
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Configurar fuentes
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Constantes
COLOR_FONDO = '#f0f0f0'
COLOR_PRIMARIO = '#2c3e50'
COLOR_SECUNDARIO = '#3498db'
COLOR_EXITO = '#27ae60'
COLOR_PELIGRO = '#e74c3c'
COLOR_ALVEOLAR = '#27ae60'
COLOR_MUERTO = '#e67e22'
COLOR_ADVERTENCIA = '#f39c12'
COLOR_INFO = '#3498db'

# Datos de países, departamentos y ciudades (ejemplo con datos de Latinoamérica)
DATOS_GEOGRAFICOS = {
    'Argentina': {
        'departamentos': ['Buenos Aires', 'Córdoba', 'Santa Fe', 'Mendoza', 'Tucumán', 'Salta', 'Entre Ríos', 'Corrientes', 'Misiones', 'Chaco'],
        'ciudades': {
            'Buenos Aires': ['Buenos Aires', 'La Plata', 'Mar del Plata', 'Bahía Blanca', 'Quilmes', 'Morón'],
            'Córdoba': ['Córdoba', 'Villa Carlos Paz', 'Río Cuarto', 'San Francisco'],
            'Santa Fe': ['Rosario', 'Santa Fe', 'Rafaela', 'Venado Tuerto'],
            'Mendoza': ['Mendoza', 'San Rafael', 'Godoy Cruz', 'Luján de Cuyo'],
            'Tucumán': ['San Miguel de Tucumán', 'Concepción', 'Tafí Viejo'],
            'Salta': ['Salta', 'San Ramón de la Nueva Orán', 'Tartagal'],
            'Entre Ríos': ['Paraná', 'Concordia', 'Gualeguaychú'],
            'Corrientes': ['Corrientes', 'Goya', 'Mercedes'],
            'Misiones': ['Posadas', 'Oberá', 'Puerto Iguazú'],
            'Chaco': ['Resistencia', 'Sáenz Peña', 'Villa Ángela']
        }
    },
    'Uruguay': {
        'departamentos': ['Montevideo', 'Canelones', 'Maldonado', 'Salto', 'Paysandú', 'Rivera', 'Tacuarembó', 'Colonia', 'Artigas', 'Rocha', 'San José', 'Cerro Largo', 'Durazno', 'Florida', 'Flores', 'Lavalleja', 'Río Negro', 'Soriano', 'Treinta y Tres'],
        'ciudades': {
            'Montevideo': ['Montevideo', 'Ciudad de la Costa', 'Pando', 'Las Piedras', 'La Paz'],
            'Canelones': ['Canelones', 'Santa Lucía', 'Progreso', 'Sauce'],
            'Maldonado': ['Maldonado', 'Punta del Este', 'San Carlos', 'Piriápolis'],
            'Salto': ['Salto', 'Constitución', 'Belén'],
            'Paysandú': ['Paysandú', 'Guichón', 'Quebracho'],
            'Rivera': ['Rivera', 'Tranqueras', 'Minas de Corrales'],
            'Tacuarembó': ['Tacuarembó', 'Paso de los Toros', 'San Gregorio de Polanco'],
            'Colonia': ['Colonia del Sacramento', 'Carmelo', 'Nueva Helvecia'],
            'Artigas': ['Artigas', 'Bella Unión', 'Tomás Gomensoro'],
            'Rocha': ['Rocha', 'Castillos', 'Chuy']
        }
    },
    'Brasil': {
        'departamentos': ['São Paulo', 'Rio de Janeiro', 'Minas Gerais', 'Rio Grande do Sul', 'Bahia', 'Paraná', 'Pernambuco', 'Ceará', 'Santa Catarina', 'Goiás'],
        'ciudades': {
            'São Paulo': ['São Paulo', 'Campinas', 'Santos', 'São José dos Campos', 'Ribeirão Preto'],
            'Rio de Janeiro': ['Rio de Janeiro', 'Niterói', 'Duque de Caxias', 'Nova Iguaçu'],
            'Minas Gerais': ['Belo Horizonte', 'Uberlândia', 'Contagem', 'Juiz de Fora'],
            'Rio Grande do Sul': ['Porto Alegre', 'Caxias do Sul', 'Pelotas', 'Canoas'],
            'Bahia': ['Salvador', 'Feira de Santana', 'Vitória da Conquista'],
            'Paraná': ['Curitiba', 'Londrina', 'Maringá', 'Ponta Grossa'],
            'Pernambuco': ['Recife', 'Olinda', 'Jaboatão dos Guararapes'],
            'Ceará': ['Fortaleza', 'Caucaia', 'Juazeiro do Norte'],
            'Santa Catarina': ['Florianópolis', 'Joinville', 'Blumenau'],
            'Goiás': ['Goiânia', 'Aparecida de Goiânia', 'Anápolis']
        }
    },
    'Chile': {
        'departamentos': ['Santiago', 'Valparaíso', 'Concepción', 'La Araucanía', 'Antofagasta', 'Coquimbo', 'O\'Higgins', 'Maule', 'Los Lagos', 'Arica y Parinacota'],
        'ciudades': {
            'Santiago': ['Santiago', 'Puente Alto', 'Maipú', 'Las Condes', 'La Florida'],
            'Valparaíso': ['Valparaíso', 'Viña del Mar', 'Quilpué', 'Villa Alemana'],
            'Concepción': ['Concepción', 'Talcahuano', 'Chillán', 'Los Ángeles'],
            'La Araucanía': ['Temuco', 'Padre Las Casas', 'Villarrica'],
            'Antofagasta': ['Antofagasta', 'Calama', 'Tocopilla'],
            'Coquimbo': ['La Serena', 'Coquimbo', 'Ovalle'],
            'O\'Higgins': ['Rancagua', 'San Fernando', 'Rengo'],
            'Maule': ['Talca', 'Curicó', 'Linares'],
            'Los Lagos': ['Puerto Montt', 'Osorno', 'Castro'],
            'Arica y Parinacota': ['Arica', 'Putre']
        }
    },
    'Colombia': {
        'departamentos': ['Bogotá D.C.', 'Antioquia', 'Valle del Cauca', 'Cundinamarca', 'Atlántico', 'Bolívar', 'Santander', 'Nariño', 'Caldas', 'Risaralda'],
        'ciudades': {
            'Bogotá D.C.': ['Bogotá', 'Soacha', 'Zipaquirá', 'Facatativá'],
            'Antioquia': ['Medellín', 'Bello', 'Itagüí', 'Envigado'],
            'Valle del Cauca': ['Cali', 'Palmira', 'Buenaventura', 'Tuluá'],
            'Cundinamarca': ['Girardot', 'Zipaquirá', 'Facatativá', 'Chía'],
            'Atlántico': ['Barranquilla', 'Soledad', 'Malambo'],
            'Bolívar': ['Cartagena', 'Magangué', 'Turbaco'],
            'Santander': ['Bucaramanga', 'Floridablanca', 'Girón'],
            'Nariño': ['Pasto', 'Tumaco', 'Ipiales'],
            'Caldas': ['Manizales', 'Villamaría', 'Chinchiná'],
            'Risaralda': ['Pereira', 'Dosquebradas', 'Santa Rosa de Cabal']
        }
    },
    'Paraguay': {
        'departamentos': ['Asunción', 'Central', 'Alto Paraná', 'Itapúa', 'Cordillera', 'San Pedro', 'Caaguazú', 'Caazapá', 'Concepción', 'Misiones'],
        'ciudades': {
            'Asunción': ['Asunción', 'Fernando de la Mora', 'Lambaré'],
            'Central': ['San Lorenzo', 'Luque', 'Capiatá', 'Itauguá'],
            'Alto Paraná': ['Ciudad del Este', 'Presidente Franco', 'Minga Guazú'],
            'Itapúa': ['Encarnación', 'Carmen del Paraná', 'Hohenau'],
            'Cordillera': ['Caacupé', 'Eusebio Ayala', 'Itacurubí de la Cordillera'],
            'San Pedro': ['San Pedro de Ycuamandiyú', 'Santa Rosa del Aguaray'],
            'Caaguazú': ['Coronel Oviedo', 'Caaguazú', 'Repatriación'],
            'Caazapá': ['Caazapá', 'Abaí', 'Yuty'],
            'Concepción': ['Concepción', 'Horqueta', 'Belén'],
            'Misiones': ['San Juan Bautista', 'Ayolas', 'San Ignacio']
        }
    },
    'Bolivia': {
        'departamentos': ['La Paz', 'Santa Cruz', 'Cochabamba', 'Potosí', 'Chuquisaca', 'Oruro', 'Tarija', 'Beni', 'Pando'],
        'ciudades': {
            'La Paz': ['La Paz', 'El Alto', 'Viacha', 'Caranavi'],
            'Santa Cruz': ['Santa Cruz de la Sierra', 'Montero', 'Warnes', 'La Guardia'],
            'Cochabamba': ['Cochabamba', 'Quillacollo', 'Sacaba', 'Colcapirhua'],
            'Potosí': ['Potosí', 'Llallagua', 'Uyuni'],
            'Chuquisaca': ['Sucre', 'Monteagudo', 'Camargo'],
            'Oruro': ['Oruro', 'Huanuni', 'Caracollo'],
            'Tarija': ['Tarija', 'Yacuiba', 'Villamontes'],
            'Beni': ['Trinidad', 'Riberalta', 'Guayaramerín'],
            'Pando': ['Cobija', 'Puerto Rico', 'Porvenir']
        }
    }
}


class AutocompleteCombobox(ttk.Combobox):
    """Combobox con autocompletado fluido y que permite escribir libremente"""
    
    def __init__(self, parent, completevalues=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._completevalues = completevalues or []
        self._autocomplete_enabled = True
        self._last_search = ""
        self._update_after_id = None
        
        self.set('')
        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<FocusOut>', self._on_focusout)
        self.bind('<Button-1>', self._on_click)
        
    @property
    def completevalues(self):
        return self._completevalues
    
    @completevalues.setter
    def completevalues(self, values):
        self._completevalues = values if values else []
        self['values'] = self._completevalues
        
    def set_completevalues(self, values):
        """Actualizar la lista de valores completos"""
        self._completevalues = values if values else []
        self['values'] = self._completevalues
        
    def _on_keyrelease(self, event):
        """Manejar la liberación de teclas para autocompletado"""
        if not self._autocomplete_enabled:
            return
            
        # Ignorar teclas especiales
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Return', 'Tab', 'Escape', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R'):
            return
            
        # Cancelar actualización pendiente
        if self._update_after_id:
            self.after_cancel(self._update_after_id)
        
        # Programar actualización
        self._update_after_id = self.after(50, self._perform_autocomplete)
    
    def _perform_autocomplete(self):
        """Realizar el autocompletado"""
        self._update_after_id = None
        
        typed = self.get()
        if not typed:
            self['values'] = self._completevalues
            return
            
        # Buscar coincidencias (insensible a mayúsculas)
        typed_lower = typed.lower()
        matches = []
        
        for val in self._completevalues:
            if typed_lower in val.lower():
                matches.append(val)
            elif len(typed) > 1:
                # Usar coincidencias aproximadas para términos cercanos
                close_matches = get_close_matches(typed, [val], cutoff=0.6)
                if close_matches and val not in matches:
                    matches.append(val)
        
        # Actualizar lista desplegable
        if matches:
            self['values'] = matches
            # Mostrar la lista desplegable si hay coincidencias
            if len(matches) > 0 and self.focus_get() == self:
                self.event_generate('<Down>')
        else:
            self['values'] = self._completevalues
        
    def _on_focusout(self, event):
        """Manejar pérdida de foco"""
        current = self.get()
        if current and current not in self._completevalues:
            # El valor actual no está en la lista, mantenerlo como texto libre
            self.set(current)
    
    def _on_click(self, event):
        """Manejar clic para mostrar la lista completa"""
        if self._completevalues:
            self['values'] = self._completevalues
            if self.focus_get() == self:
                self.event_generate('<Down>')
    
    def get_value(self):
        """Obtener el valor actual (puede ser texto libre)"""
        return self.get().strip()
    
    def set_value(self, value):
        """Establecer valor sin activar autocompletado"""
        self._autocomplete_enabled = False
        self.set(value)
        self._autocomplete_enabled = True


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)

    def show_tip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None


class InterfazDenco:
    def __init__(self, root):
        self.root = root
        self.root.title(f"SISTEMA DENCO v3.9 - Deteccion de Efecto Warburg")
        self.root.geometry("1300x800")
        self.root.configure(bg=COLOR_FONDO)

        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=COLOR_FONDO)
        style.configure('TNotebook.Tab', padding=[15, 5], font=('Arial', 10, 'bold'))

        # Variables de estado
        self.paciente_actual = None
        self.sesion_actual = None
        self.muestras_actuales = []
        self.volumen_total = 0.0
        self.capturando = False
        self.captura_thread = None
        self.serial_mgr = SerialManager()
        self.modelo_ia = ModeloIA()
        self.db = DatabaseManager()
        self.viz = Visualizador()
        self.analizador = None

        # Buffers para graficas
        self.tiempo_buffer = []
        self.tvoc_buffer = []
        self.flujo_buffer = []
        self.vol_buffer = []
        self.tiempo_inicio_sesion = 0

        self.status_var = tk.StringVar()
        self.status_var.set("Inicializando sistema...")

        self.after_id_grafica = None

        self.root.after(100, self.cargar_modelo_inicial)
        self.crear_menu()
        self.crear_notebook()
        self.conectar_db()
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_app)

    def cargar_modelo_inicial(self):
        try:
            if self.modelo_ia.cargar():
                self.status_var.set("[OK] Modelo de IA conectado")
            else:
                self.status_var.set("[!] No se pudo conectar al servidor de IA")
        except Exception as e:
            self.status_var.set(f"[!] Error: {e}")

    def conectar_db(self):
        try:
            if self.db.conectar():
                self.analizador = AnalizadorEvolucion(self.db)
                self.status_var.set("[OK] Conectado a base de datos")
            else:
                self.status_var.set("[X] Error conectando a BD")
        except Exception as e:
            messagebox.showerror("Error DB", f"No se pudo conectar: {e}")

    def crear_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        archivo_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=archivo_menu)
        archivo_menu.add_command(label="Configurar Puerto Serial", command=self.configurar_puerto)
        archivo_menu.add_command(label="Ver Carpeta de Reportes", command=self.ver_carpeta_reportes)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Salir", command=self.cerrar_app)

        herramientas_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=herramientas_menu)
        herramientas_menu.add_command(label="Analizar Evolucion", command=self.analizar_evolucion_actual)
        herramientas_menu.add_command(label="Exportar Historial", command=self.exportar_historial)
        herramientas_menu.add_separator()
        herramientas_menu.add_command(label="Estadisticas Geograficas", command=self.mostrar_estadisticas_geograficas)
        herramientas_menu.add_command(label="Verificar Servidor", command=self.verificar_servidor)

        ayuda_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=ayuda_menu)
        ayuda_menu.add_command(label="Acerca de", command=self.mostrar_acerca)
        ayuda_menu.add_command(label="Guia Rapida", command=self.mostrar_guia)

    def crear_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.tab_paciente = ttk.Frame(self.notebook)
        self.tab_captura = ttk.Frame(self.notebook)
        self.tab_resultados = ttk.Frame(self.notebook)
        self.tab_evolucion = ttk.Frame(self.notebook)
        self.tab_geografia = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_paciente, text=' Registro Paciente')
        self.notebook.add(self.tab_captura, text=' Captura en Tiempo Real')
        self.notebook.add(self.tab_resultados, text=' Resultados')
        self.notebook.add(self.tab_evolucion, text=' Evolucion')
        self.notebook.add(self.tab_geografia, text=' Geografia')

        self.crear_pestania_paciente()
        self.crear_pestania_captura()
        self.crear_pestania_resultados()
        self.crear_pestania_evolucion()
        self.crear_pestania_geografia()

        modo = "SERVIDOR" if config.MODO_SERVIDOR else "LOCAL"
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def crear_pestania_paciente(self):
        frame = self.tab_paciente

        tk.Label(frame, text="Registro de Nuevo Paciente", font=('Arial', 16, 'bold'),
                 bg=COLOR_FONDO, fg=COLOR_PRIMARIO).pack(pady=15)

        main_frame = tk.Frame(frame, bg=COLOR_FONDO)
        main_frame.pack(fill='both', expand=True, padx=20)
        
        canvas = tk.Canvas(main_frame, bg=COLOR_FONDO)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLOR_FONDO)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        form_frame = tk.Frame(scrollable_frame, bg=COLOR_FONDO)
        form_frame.pack(pady=10)
        
        tk.Label(form_frame, text="DATOS PERSONALES", font=('Arial', 12, 'bold'),
                 bg=COLOR_FONDO, fg=COLOR_PRIMARIO).grid(row=0, column=0, columnspan=2, pady=10, sticky='w')
        
        campos = [
            ("Nombre Completo:", 40, 1, 0),
            ("Edad:", 10, 2, 0),
            ("Peso (kg):", 10, 3, 0),
            ("Telefono:", 20, 4, 0),
            ("Email:", 30, 5, 0),
            ("Direccion:", 50, 6, 0),
        ]
        
        self.entries_paciente = {}
        for label_text, width, row, col in campos:
            tk.Label(form_frame, text=label_text, bg=COLOR_FONDO, font=('Arial', 10)).grid(row=row, column=col, sticky='e', padx=5, pady=5)
            entry = tk.Entry(form_frame, width=width, font=('Arial', 10))
            entry.grid(row=row, column=col+1, sticky='w', padx=5, pady=5)
            self.entries_paciente[label_text] = entry
        
        tk.Label(form_frame, text="", bg=COLOR_FONDO).grid(row=7, column=0, columnspan=2, pady=10)
        
        tk.Label(form_frame, text="UBICACION GEOGRAFICA", font=('Arial', 12, 'bold'),
                 bg=COLOR_FONDO, fg=COLOR_PRIMARIO).grid(row=8, column=0, columnspan=2, pady=10, sticky='w')
        
        # Campos geográficos con combobox con autocompletado
        # País
        tk.Label(form_frame, text="Pais:", bg=COLOR_FONDO, font=('Arial', 10)).grid(row=9, column=0, sticky='e', padx=5, pady=5)
        self.combo_pais = AutocompleteCombobox(form_frame, completevalues=list(DATOS_GEOGRAFICOS.keys()), width=30, font=('Arial', 10))
        self.combo_pais.grid(row=9, column=1, sticky='w', padx=5, pady=5)
        self.combo_pais.bind('<<ComboboxSelected>>', self.on_pais_seleccionado)
        ToolTip(self.combo_pais, "Escriba el nombre del pais o seleccione de la lista")
        
        # Departamento/Provincia
        tk.Label(form_frame, text="Departamento/Provincia:", bg=COLOR_FONDO, font=('Arial', 10)).grid(row=10, column=0, sticky='e', padx=5, pady=5)
        self.combo_departamento = AutocompleteCombobox(form_frame, completevalues=[], width=30, font=('Arial', 10))
        self.combo_departamento.grid(row=10, column=1, sticky='w', padx=5, pady=5)
        self.combo_departamento.bind('<<ComboboxSelected>>', self.on_departamento_seleccionado)
        ToolTip(self.combo_departamento, "Seleccione el departamento o provincia")
        
        # Ciudad
        tk.Label(form_frame, text="Ciudad:", bg=COLOR_FONDO, font=('Arial', 10)).grid(row=11, column=0, sticky='e', padx=5, pady=5)
        self.combo_ciudad = AutocompleteCombobox(form_frame, completevalues=[], width=30, font=('Arial', 10))
        self.combo_ciudad.grid(row=11, column=1, sticky='w', padx=5, pady=5)
        ToolTip(self.combo_ciudad, "Escriba el nombre de la ciudad o seleccione de la lista")
        
        # Institución
        tk.Label(form_frame, text="Institucion:", bg=COLOR_FONDO, font=('Arial', 10)).grid(row=12, column=0, sticky='e', padx=5, pady=5)
        self.entry_institucion = tk.Entry(form_frame, width=40, font=('Arial', 10))
        self.entry_institucion.grid(row=12, column=1, sticky='w', padx=5, pady=5)
        
        tk.Label(form_frame, text="Observaciones:", bg=COLOR_FONDO, font=('Arial', 10)).grid(row=13, column=0, sticky='ne', padx=5, pady=5)
        self.obs_text = tk.Text(form_frame, width=60, height=4, font=('Arial', 10))
        self.obs_text.grid(row=13, column=1, sticky='w', padx=5, pady=5)
        
        btn_frame = tk.Frame(scrollable_frame, bg=COLOR_FONDO)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Registrar Paciente", command=self.registrar_paciente,
                  bg=COLOR_PRIMARIO, fg='white', font=('Arial', 11, 'bold'),
                  padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="Buscar Paciente", command=self.buscar_paciente,
                  bg=COLOR_SECUNDARIO, fg='white', font=('Arial', 11, 'bold'),
                  padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        self.info_frame = tk.Frame(scrollable_frame, bg=COLOR_FONDO, relief=tk.GROOVE, bd=2)
        self.info_frame.pack(fill='x', padx=20, pady=10)
        
        self.info_paciente_var = tk.StringVar()
        self.info_paciente_var.set("No hay paciente seleccionado")
        tk.Label(self.info_frame, textvariable=self.info_paciente_var, bg=COLOR_FONDO,
                 fg=COLOR_PRIMARIO, font=('Arial', 11, 'bold')).pack(pady=5)
        
        self.info_ubicacion_var = tk.StringVar()
        self.info_ubicacion_var.set("")
        tk.Label(self.info_frame, textvariable=self.info_ubicacion_var, bg=COLOR_FONDO,
                 fg=COLOR_INFO, font=('Arial', 10)).pack(pady=2)
        
        self.sesiones_info_var = tk.StringVar()
        self.sesiones_info_var.set("")
        tk.Label(self.info_frame, textvariable=self.sesiones_info_var, bg=COLOR_FONDO,
                 fg=COLOR_INFO, font=('Arial', 10)).pack(pady=2)
        
        self.paciente_captura_var = tk.StringVar()
        self.paciente_captura_var.set("Paciente: Ninguno")
        self.num_sesion_var = tk.StringVar()
        self.num_sesion_var.set("")
        self.cond_var = tk.StringVar()
        self.cond_var.set("T: --C | H: --% | P: -- hPa")
        self.estado_captura_var = tk.StringVar()
        self.estado_captura_var.set("Esperando inicio...")

    def on_pais_seleccionado(self, event=None):
        """Actualizar departamentos según el país seleccionado"""
        pais = self.combo_pais.get_value()
        if pais in DATOS_GEOGRAFICOS:
            departamentos = DATOS_GEOGRAFICOS[pais]['departamentos']
            self.combo_departamento.set_completevalues(departamentos)
            self.combo_departamento.set('')
            self.combo_ciudad.set_completevalues([])
            self.combo_ciudad.set('')
        else:
            # País no está en la lista predefinida, permitir escribir libremente
            self.combo_departamento.set_completevalues([])
            self.combo_ciudad.set_completevalues([])

    def on_departamento_seleccionado(self, event=None):
        """Actualizar ciudades según el departamento seleccionado"""
        pais = self.combo_pais.get_value()
        departamento = self.combo_departamento.get_value()
        
        if pais in DATOS_GEOGRAFICOS and departamento in DATOS_GEOGRAFICOS[pais]['ciudades']:
            ciudades = DATOS_GEOGRAFICOS[pais]['ciudades'][departamento]
            self.combo_ciudad.set_completevalues(ciudades)
        else:
            # Departamento no está en la lista, permitir escribir libremente
            self.combo_ciudad.set_completevalues([])

    def registrar_paciente(self):
        try:
            nombre = self.entries_paciente["Nombre Completo:"].get().strip()
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            
            edad_str = self.entries_paciente["Edad:"].get().strip()
            edad = int(edad_str) if edad_str else 0
            peso_str = self.entries_paciente["Peso (kg):"].get().strip()
            peso = float(peso_str) if peso_str else 0.0
            contacto = self.entries_paciente["Telefono:"].get().strip()
            email = self.entries_paciente["Email:"].get().strip()
            direccion = self.entries_paciente["Direccion:"].get().strip()
            observaciones = self.obs_text.get("1.0", "end-1c").strip()
            
            # Obtener valores de los combobox (pueden ser texto libre)
            pais = self.combo_pais.get_value()
            departamento = self.combo_departamento.get_value()
            ciudad = self.combo_ciudad.get_value()
            institucion = self.entry_institucion.get().strip()
            
            paciente_id = self.db.registrar_paciente(
                nombre, edad, peso, contacto, email, observaciones,
                pais, departamento, ciudad, institucion, direccion
            )
            
            if paciente_id:
                self.paciente_actual = {
                    'id': paciente_id, 'nombre': nombre, 'edad': edad, 'peso': peso,
                    'contacto': contacto, 'email': email, 'direccion': direccion,
                    'pais': pais, 'departamento': departamento, 'ciudad': ciudad, 'institucion': institucion
                }
                self.actualizar_info_paciente()
                messagebox.showinfo("Exito", f"Paciente {nombre} registrado con ID {paciente_id}")
                self.limpiar_formulario_paciente()
                respuesta = messagebox.askyesno("Ir a Captura", "¿Desea ir a la pestaña de captura?")
                if respuesta:
                    self.notebook.select(self.tab_captura)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar: {e}")

    def limpiar_formulario_paciente(self):
        for campo in self.entries_paciente:
            self.entries_paciente[campo].delete(0, tk.END)
        self.combo_pais.set('')
        self.combo_departamento.set('')
        self.combo_ciudad.set('')
        self.entry_institucion.delete(0, tk.END)
        self.obs_text.delete("1.0", tk.END)

    def buscar_paciente(self):
        def on_paciente_seleccionado(paciente):
            self.paciente_actual = paciente
            self.actualizar_info_paciente()
            self.notebook.select(self.tab_evolucion)
            self.cambiar_paciente_evolucion()
        
        BuscadorDialog(self.root, self.db, self.viz, on_paciente_seleccionado)

    def actualizar_info_paciente(self):
        if not self.paciente_actual:
            return
        
        self.info_paciente_var.set(f"Paciente: {self.paciente_actual['nombre']} (ID: {self.paciente_actual['id']})")
        
        ubicacion = []
        if self.paciente_actual.get('ciudad'):
            ubicacion.append(self.paciente_actual['ciudad'])
        if self.paciente_actual.get('departamento'):
            ubicacion.append(self.paciente_actual['departamento'])
        if self.paciente_actual.get('pais'):
            ubicacion.append(self.paciente_actual['pais'])
        
        if ubicacion:
            self.info_ubicacion_var.set(f"Ubicacion: {', '.join(ubicacion)} | Institucion: {self.paciente_actual.get('institucion', 'N/A')}")
        
        self.paciente_captura_var.set(f"Paciente: {self.paciente_actual['nombre']}")
        
        sesiones = self.db.obtener_historial_paciente(self.paciente_actual['id'])
        if sesiones:
            num_sesiones = len(sesiones)
            ultima = sesiones[-1]
            self.sesiones_info_var.set(
                f"Sesiones previas: {num_sesiones} | "
                f"Ultima: {ultima['fecha']} | "
                f"TVOC: {ultima['tvoc_medio']:.0f} ppb | "
                f"Riesgo: {ultima['riesgo']*100:.1f}%"
            )
            self.num_sesion_var.set(f"(Sesion N° {num_sesiones + 1})")
        else:
            self.sesiones_info_var.set("Primera sesion para este paciente")
            self.num_sesion_var.set("(Primera sesion)")
        
        self.btn_iniciar.config(state='normal')

    # ========== METODOS PRINCIPALES DE CAPTURA ==========
    # (Los métodos de captura se mantienen igual que en la versión anterior)

    def crear_pestania_captura(self):
        frame = self.tab_captura

        top_frame = tk.Frame(frame, bg=COLOR_FONDO)
        top_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(top_frame, textvariable=self.paciente_captura_var,
                 bg=COLOR_FONDO, font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=10)
        tk.Label(top_frame, textvariable=self.num_sesion_var,
                 bg=COLOR_FONDO, font=('Arial', 10, 'italic')).pack(side=tk.LEFT, padx=10)
        tk.Label(top_frame, textvariable=self.cond_var,
                 bg=COLOR_FONDO, font=('Arial', 10)).pack(side=tk.RIGHT, padx=10)

        control_frame = tk.Frame(frame, bg=COLOR_FONDO)
        control_frame.pack(pady=10)

        self.btn_iniciar = tk.Button(control_frame, text="INICIAR CAPTURA",
                                     command=self.iniciar_captura,
                                     bg=COLOR_EXITO, fg='white', font=('Arial', 12, 'bold'),
                                     padx=30, pady=10, state='disabled')
        self.btn_iniciar.pack(side=tk.LEFT, padx=10)

        self.btn_parar = tk.Button(control_frame, text="DETENER",
                                   command=self.parar_captura,
                                   bg=COLOR_PELIGRO, fg='white', font=('Arial', 12, 'bold'),
                                   padx=30, pady=10, state='disabled')
        self.btn_parar.pack(side=tk.LEFT, padx=10)

        tk.Label(frame, textvariable=self.estado_captura_var,
                 bg=COLOR_FONDO, font=('Arial', 11, 'italic')).pack(pady=5)

        graficos_frame = tk.Frame(frame, bg='white')
        graficos_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.fig = Figure(figsize=(10, 5), dpi=80)
        self.fig.patch.set_facecolor('white')

        self.ax1 = self.fig.add_subplot(131)
        self.ax1.set_title('TVOC (ppb)', fontsize=10)
        self.ax1.set_xlabel('Tiempo (s)')
        self.ax1.grid(True, alpha=0.3)
        self.line_tvoc, = self.ax1.plot([], [], 'b-', linewidth=2)

        self.ax2 = self.fig.add_subplot(132)
        self.ax2.set_title('Flujo (L/s)', fontsize=10)
        self.ax2.set_xlabel('Tiempo (s)')
        self.ax2.grid(True, alpha=0.3)
        self.line_flujo, = self.ax2.plot([], [], 'g-', linewidth=2)

        self.ax3 = self.fig.add_subplot(133)
        self.ax3.set_title('Volumen (L)', fontsize=10)
        self.ax3.set_xlabel('Tiempo (s)')
        self.ax3.grid(True, alpha=0.3)
        self.line_vol, = self.ax3.plot([], [], 'r-', linewidth=2)

        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=graficos_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def iniciar_captura(self):
        if self.paciente_actual is None:
            messagebox.showerror("Error", "Debe seleccionar un paciente primero")
            return

        self.serial_mgr.cerrar()
        time.sleep(0.5)
        
        if not config.MODO_SIMULACION:
            if not self.serial_mgr.conectar():
                messagebox.showerror("Error", "No se pudo conectar al Arduino. Verifique el puerto serial.")
                return
        
        self.capturando = True
        self.btn_iniciar.config(state='disabled')
        self.btn_parar.config(state='normal')
        self.estado_captura_var.set("Capturando... Espere la exhalacion")

        self.tiempo_buffer = []
        self.tvoc_buffer = []
        self.flujo_buffer = []
        self.vol_buffer = []
        self.tiempo_inicio_sesion = 0

        self.line_tvoc.set_data([], [])
        self.line_flujo.set_data([], [])
        self.line_vol.set_data([], [])
        
        self.ax1.set_xlim(0, 35)
        self.ax1.set_ylim(0, 1000)
        self.ax2.set_xlim(0, 35)
        self.ax2.set_ylim(0, 5)
        self.ax3.set_xlim(0, 35)
        self.ax3.set_ylim(0, 10)
        self.canvas.draw_idle()

        self.sesion_actual = self.db.crear_sesion(self.paciente_actual['id'])

        self.captura_thread = threading.Thread(target=self.hilo_captura, daemon=True)
        self.captura_thread.start()
        self.iniciar_actualizacion_grafica()

    def iniciar_actualizacion_grafica(self):
        if self.after_id_grafica:
            try:
                self.root.after_cancel(self.after_id_grafica)
            except:
                pass
        self.actualizar_grafica()

    def actualizar_grafica(self):
        try:
            if not self.root.winfo_exists():
                return
            
            if self.tiempo_buffer and self.capturando:
                self.line_tvoc.set_data(self.tiempo_buffer, self.tvoc_buffer)
                self.line_flujo.set_data(self.tiempo_buffer, self.flujo_buffer)
                self.line_vol.set_data(self.tiempo_buffer, self.vol_buffer)
                
                if self.tvoc_buffer:
                    self.ax1.set_ylim(0, max(max(self.tvoc_buffer), 10) * 1.1)
                if self.flujo_buffer:
                    self.ax2.set_ylim(0, max(max(self.flujo_buffer), 0.5) * 1.2)
                if self.vol_buffer:
                    self.ax3.set_ylim(0, max(max(self.vol_buffer), 1) * 1.1)
                
                if self.tiempo_buffer:
                    max_t = max(self.tiempo_buffer)
                    self.ax1.set_xlim(0, max(max_t + 2, 35))
                    self.ax2.set_xlim(0, max(max_t + 2, 35))
                    self.ax3.set_xlim(0, max(max_t + 2, 35))
                
                self.canvas.draw_idle()
            
            if self.capturando:
                self.after_id_grafica = self.root.after(100, self.actualizar_grafica)
        except Exception as e:
            print(f"Error grafica: {e}")

    def agregar_punto_grafica(self, muestra):
        if not self.capturando:
            return
        
        timestamp = muestra.get('timestamp', 0)
        if self.tiempo_inicio_sesion == 0:
            self.tiempo_inicio_sesion = timestamp
        
        tiempo_rel = (timestamp - self.tiempo_inicio_sesion) / 1000.0
        
        self.tiempo_buffer.append(tiempo_rel)
        self.tvoc_buffer.append(muestra['tvoc'])
        self.flujo_buffer.append(muestra['flujo'])
        self.vol_buffer.append(muestra.get('volumen', 0))
        
        max_buffer = 200
        if len(self.tiempo_buffer) > max_buffer:
            self.tiempo_buffer = self.tiempo_buffer[-max_buffer:]
            self.tvoc_buffer = self.tvoc_buffer[-max_buffer:]
            self.flujo_buffer = self.flujo_buffer[-max_buffer:]
            self.vol_buffer = self.vol_buffer[-max_buffer:]

    def hilo_captura(self):
        try:
            self.serial_mgr.limpiar_buffer()
            self.root.after(0, lambda: self.estado_captura_var.set("Esperando exhalacion..."))
            
            tiempo_inicio = time.time()
            sesion_activa = False
            muestras_temp = []
            lineas_recibidas = 0
            
            while self.capturando and (time.time() - tiempo_inicio) < 45:
                linea = self.serial_mgr.leer_linea()
                
                if linea:
                    lineas_recibidas += 1
                    print(f"[DEBUG] Linea {lineas_recibidas}: {linea[:80]}")
                    
                    if 'INICIO_EXHALACION' in linea:
                        sesion_activa = True
                        muestras_temp = []
                        self.root.after(0, lambda: self.estado_captura_var.set("Capturando en tiempo real..."))
                        print("[DEBUG] EXHALACION INICIADA!")
                    
                    elif 'MUESTRA' in linea and sesion_activa:
                        partes = linea.split(',')
                        if len(partes) >= 12:
                            try:
                                muestra = {
                                    'num': int(partes[1]),
                                    'tvoc': int(partes[2]),
                                    'eco2': int(partes[3]),
                                    'temp': float(partes[4]),
                                    'hum': float(partes[5]),
                                    'pres': float(partes[6]),
                                    'flujo': float(partes[7]),
                                    'volumen': float(partes[8]),
                                    'deltaP': float(partes[9]),
                                    'fraccion': partes[10].strip(),
                                    'timestamp': int(partes[11])
                                }
                                muestras_temp.append(muestra)
                                self.root.after(0, self.agregar_punto_grafica, muestra)
                                
                                if len(muestras_temp) % 10 == 0:
                                    print(f"[DEBUG] Muestra {muestra['num']}: TVOC={muestra['tvoc']}, Flujo={muestra['flujo']:.2f}")
                            except Exception as e:
                                print(f"[DEBUG] Error: {e}")
                    
                    elif ('FIN_EXHALACION' in linea or 'FIN_EXHALACION_TIMEOUT' in linea) and sesion_activa:
                        self.muestras_actuales = muestras_temp
                        self.volumen_total = muestras_temp[-1]['volumen'] if muestras_temp else 0
                        print(f"[DEBUG] EXHALACION FINALIZADA! {len(muestras_temp)} muestras")
                        self.root.after(0, self.captura_completada, muestras_temp, self.volumen_total)
                        return
                
                time.sleep(0.01)
            
            if not sesion_activa:
                self.root.after(0, self.captura_fallida, f"No se detecto exhalacion")
            elif muestras_temp:
                self.root.after(0, self.captura_completada, muestras_temp, self.volumen_total)
            else:
                self.root.after(0, self.captura_fallida, "No se recibieron muestras")
                
        except Exception as e:
            print(f"[DEBUG] Error: {e}")
            self.root.after(0, self.captura_fallida, str(e))
        finally:
            self.capturando = False
            self.root.after(0, lambda: self.btn_parar.config(state='disabled'))
            self.root.after(0, lambda: self.btn_iniciar.config(state='normal'))

    def captura_completada(self, muestras, volumen):
        self.estado_captura_var.set("Captura completada. Procesando...")
        
        if muestras:
            for m in muestras:
                self.db.guardar_muestra(self.sesion_actual, m)
            self.mostrar_resultados()
        
        self.btn_iniciar.config(state='normal')
        self.btn_parar.config(state='disabled')
        self.estado_captura_var.set("Captura finalizada. Vaya a Resultados.")
        
        self.serial_mgr.cerrar()
        logger.info("Puerto serial cerrado para proxima captura")
        
        if muestras:
            self.notebook.select(self.tab_resultados)

    def captura_fallida(self, razon):
        self.estado_captura_var.set(f"Captura fallida: {razon}")
        self.btn_iniciar.config(state='normal')
        self.btn_parar.config(state='disabled')
        self.capturando = False
        self.serial_mgr.cerrar()

    def parar_captura(self):
        self.capturando = False
        self.estado_captura_var.set("Captura detenida")
        self.btn_iniciar.config(state='normal')
        self.btn_parar.config(state='disabled')
        self.serial_mgr.cerrar()

    def mostrar_resultados(self):
        if not self.muestras_actuales:
            return

        muestras_alv = [m for m in self.muestras_actuales if m.get('fraccion') == 'ALVEOLAR']
        if not muestras_alv:
            muestras_alv = self.muestras_actuales

        tvocs = [m['tvoc'] for m in muestras_alv]
        eco2s = [m['eco2'] for m in muestras_alv]
        flujos = [m['flujo'] for m in muestras_alv]

        resumen = {
            'tvoc': np.mean(tvocs) if tvocs else 0,
            'eco2': np.mean(eco2s) if eco2s else 0,
            'temp': np.mean([m['temp'] for m in muestras_alv]) if muestras_alv else 0,
            'hum': np.mean([m['hum'] for m in muestras_alv]) if muestras_alv else 0,
            'pres': np.mean([m['pres'] for m in muestras_alv]) if muestras_alv else 0,
            'flujo_medio': np.mean(flujos) if flujos else 0
        }

        correl, pendiente = self.viz.calcular_correlacion(self.muestras_actuales)

        X_pred = [
            resumen['tvoc'], resumen['eco2'], resumen['temp'],
            resumen['hum'], resumen['flujo_medio'], self.volumen_total, correl
        ]
        cluster, riesgo = self.modelo_ia.predecir(X_pred)

        iqm = self.calcular_iqm(muestras_alv, self.volumen_total, correl)

        duracion_ms = self.muestras_actuales[-1]['timestamp'] - self.muestras_actuales[0]['timestamp']
        self.db.actualizar_sesion(
            self.sesion_actual, resumen, self.volumen_total, duracion_ms,
            max(flujos) if flujos else 0, min(flujos) if flujos else 0, correl, pendiente, cluster, riesgo
        )

        self.resultados_text.delete(1.0, tk.END)

        sesiones = self.db.obtener_historial_paciente(self.paciente_actual['id'])
        num_sesion = len(sesiones)

        texto = f"""
{'='*60}
RESULTADOS DE BIOPSIA DE ALIENTO - SESION N° {num_sesion}
{'='*60}

Paciente: {self.paciente_actual['nombre']}
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Sesion ID: {self.sesion_actual}

[UBICACION]:
Ciudad: {self.paciente_actual.get('ciudad', 'N/A')}
Departamento: {self.paciente_actual.get('departamento', 'N/A')}
Pais: {self.paciente_actual.get('pais', 'N/A')}
Institucion: {self.paciente_actual.get('institucion', 'N/A')}
Direccion: {self.paciente_actual.get('direccion', 'N/A')}

 PARAMETROS CUANTITATIVOS
{'-'*40}
TVOC Medio (ppb):       {resumen['tvoc']:>8.0f}
eCO2 Medio (ppm):       {resumen['eco2']:>8.0f}
Temperatura Media (C): {resumen['temp']:>8.1f}
Humedad Media (%):      {resumen['hum']:>8.1f}

[FLUJO] PARAMETROS DE FLUJO
{'-'*40}
Flujo Medio (L/s):      {resumen['flujo_medio']:>8.3f}
Flujo Maximo (L/s):     {max(flujos) if flujos else 0:>8.3f}
Volumen Total (L):      {self.volumen_total:>8.3f}
Duracion (s):           {duracion_ms/1000:>8.1f}

 ANALISIS AVANZADO
{'-'*40}
Correlacion VOC-Flujo:  {correl:>+8.3f}
Pendiente (ppb/L/s):    {pendiente:>8.2f}
Cluster IA:             {cluster}
Riesgo IA:              {riesgo*100:>5.1f}%
Calidad Muestra (IQM):  {iqm:>5.1f}%

 NORMA ISO 16000-9 (Emisiones)
{'-'*40}
Conc. Masica (µg/m³):   {self.calcular_emisiones()['concentracion_ug_m3']:>8.1f}
Tasa Emision (µg/min):  {self.calcular_emisiones()['tasa_emision_ug_min']:>8.2f}

 CLASIFICACION ISO 13138
{'-'*40}
Muestras Alveolares:    {len([m for m in self.muestras_actuales if m.get('fraccion')=='ALVEOLAR'])}
Muestras Esp. Muerto:   {len([m for m in self.muestras_actuales if m.get('fraccion')=='ESPACIO_MUERTO'])}

 SEGUIMIENTO
{'-'*40}
Esta es la sesion N° {num_sesion} para este paciente
{'='*60}
        """
        self.resultados_text.insert(1.0, texto)

    def calcular_iqm(self, muestras, volumen, correlacion):
        score = 0.0

        if volumen >= config.DETECCION_CONFIG.get('volumen_minimo_L', 0.3):
            score += 30
        elif volumen > 0.05:
            score += 15

        num_alv = len(muestras)
        if num_alv >= 10:
            score += 30
        elif num_alv >= 5:
            score += 20
        elif num_alv >= 3:
            score += 10

        if abs(correlacion) < 0.2:
            score += 40
        elif abs(correlacion) < 0.4:
            score += 30
        elif abs(correlacion) < 0.6:
            score += 15

        return min(score, 100)

    def calcular_emisiones(self):
        if not self.muestras_actuales:
            return {'concentracion_ug_m3': 0, 'tasa_emision_ug_min': 0}
        duracion = (self.muestras_actuales[-1]['timestamp'] - self.muestras_actuales[0]['timestamp']) / 1000.0
        return calcular_emisiones_iso16000(self.muestras_actuales, self.volumen_total, duracion)

    def generar_pdf(self):
        if not self.muestras_actuales:
            messagebox.showwarning("Sin datos", "No hay una sesion reciente para generar PDF")
            return

        try:
            muestras_alv = [m for m in self.muestras_actuales if m.get('fraccion') == 'ALVEOLAR']
            if not muestras_alv:
                muestras_alv = self.muestras_actuales

            tvocs = [m['tvoc'] for m in muestras_alv]
            eco2s = [m['eco2'] for m in muestras_alv]
            flujos = [m['flujo'] for m in muestras_alv]

            resumen = {
                'tvoc': np.mean(tvocs) if tvocs else 0,
                'eco2': np.mean(eco2s) if eco2s else 0,
                'temp': np.mean([m['temp'] for m in muestras_alv]) if muestras_alv else 0,
                'hum': np.mean([m['hum'] for m in muestras_alv]) if muestras_alv else 0,
                'pres': np.mean([m['pres'] for m in muestras_alv]) if muestras_alv else 0,
                'flujo_medio': np.mean(flujos) if flujos else 0
            }

            correl, pendiente = self.viz.calcular_correlacion(self.muestras_actuales)

            X_pred = [
                resumen['tvoc'], resumen['eco2'], resumen['temp'],
                resumen['hum'], resumen['flujo_medio'], self.volumen_total, correl
            ]
            cluster, riesgo = self.modelo_ia.predecir(X_pred)

            duracion_ms = self.muestras_actuales[-1]['timestamp'] - self.muestras_actuales[0]['timestamp']

            emisiones = self.calcular_emisiones()

            curva_img = self.viz.curva_completa(self.muestras_actuales, self.volumen_total)
            corr_img, _, _ = self.viz.correlacion_voc_flujo(self.muestras_actuales)

            filepath = generar_pdf(
                self.paciente_actual,
                self.muestras_actuales,
                self.volumen_total,
                resumen,
                duracion_ms,
                max(flujos) if flujos else 0,
                min(flujos) if flujos else 0,
                correl,
                pendiente,
                riesgo,
                cluster,
                curva_img,
                corr_img,
                emisiones
            )

            messagebox.showinfo("PDF Generado", f"Reporte guardado en:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Error PDF", f"No se pudo generar el PDF: {e}")

    def ver_grafico_detallado(self):
        if not self.muestras_actuales:
            messagebox.showwarning("Sin datos", "No hay datos para graficar")
            return

        top = tk.Toplevel(self.root)
        top.title("Grafico Detallado de la Sesion")
        top.geometry("1000x600")

        fig = Figure(figsize=(12, 8), dpi=100)
        fig.patch.set_facecolor('white')

        ax1 = fig.add_subplot(221)
        ax2 = fig.add_subplot(222)
        ax3 = fig.add_subplot(223)
        ax4 = fig.add_subplot(224)

        nums = [m['num'] for m in self.muestras_actuales]
        tvocs = [m['tvoc'] for m in self.muestras_actuales]
        eco2s = [m['eco2'] for m in self.muestras_actuales]
        flujos = [m['flujo'] for m in self.muestras_actuales]
        volumenes = [m['volumen'] for m in self.muestras_actuales]

        colores = [COLOR_ALVEOLAR if m.get('fraccion') == 'ALVEOLAR' else COLOR_MUERTO for m in self.muestras_actuales]

        ax1.scatter(nums, tvocs, c=colores, alpha=0.7, s=20)
        ax1.set_title('TVOC (ppb)', fontsize=12)
        ax1.set_xlabel('Muestra')
        ax1.grid(True, alpha=0.3)

        ax2.scatter(nums, eco2s, c=colores, alpha=0.7, s=20)
        ax2.set_title('eCO2 (ppm)', fontsize=12)
        ax2.set_xlabel('Muestra')
        ax2.grid(True, alpha=0.3)

        ax3.scatter(nums, flujos, c=colores, alpha=0.7, s=20)
        ax3.set_title('Flujo (L/s)', fontsize=12)
        ax3.set_xlabel('Muestra')
        ax3.grid(True, alpha=0.3)

        ax4.plot(nums, volumenes, 'b-', linewidth=2)
        ax4.set_title('Volumen Acumulado (L)', fontsize=12)
        ax4.set_xlabel('Muestra')
        ax4.grid(True, alpha=0.3)
        ax4.fill_between(nums, 0, volumenes, alpha=0.2, color='blue')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=COLOR_ALVEOLAR, alpha=0.7, label='Alveolar'),
            Patch(facecolor=COLOR_MUERTO, alpha=0.7, label='Espacio Muerto')
        ]
        ax1.legend(handles=legend_elements, loc='upper right')

    def ver_en_evolucion(self):
        if not self.paciente_actual:
            messagebox.showwarning("Sin paciente", "No hay un paciente seleccionado")
            return
        self.notebook.select(self.tab_evolucion)
        self.cambiar_paciente_evolucion()

    def cambiar_paciente_evolucion(self):
        if not self.paciente_actual:
            messagebox.showwarning("Sin paciente", "Primero seleccione un paciente")
            self.buscar_paciente()
            return
        self.evol_paciente_var.set(f"{self.paciente_actual['nombre']} (ID: {self.paciente_actual['id']})")
        self.actualizar_graficos_evolucion()

    def crear_pestania_resultados(self):
        frame = self.tab_resultados

        resumen_frame = tk.LabelFrame(frame, text="Resumen de la Ultima Sesion",
                                       bg=COLOR_FONDO, font=('Arial', 11, 'bold'))
        resumen_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.resultados_text = tk.Text(resumen_frame, height=15, width=80, font=('Courier', 10))
        self.resultados_text.pack(side=tk.LEFT, padx=5, pady=5, fill='both', expand=True)

        scrollbar = tk.Scrollbar(resumen_frame, command=self.resultados_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        self.resultados_text.config(yscrollcommand=scrollbar.set)

        btn_frame = tk.Frame(frame, bg=COLOR_FONDO)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Generar PDF", command=self.generar_pdf,
                  bg=COLOR_PRIMARIO, fg='white', font=('Arial', 10, 'bold'),
                  padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Ver Grafico Detallado", command=self.ver_grafico_detallado,
                  bg=COLOR_SECUNDARIO, fg='white', font=('Arial', 10, 'bold'),
                  padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Ver en Evolucion", 
                 command=lambda: self.ver_en_evolucion(),
                  bg=COLOR_ADVERTENCIA, fg='white', font=('Arial', 10, 'bold'),
                  padx=15, pady=5).pack(side=tk.LEFT, padx=5)

    def crear_pestania_evolucion(self):
        frame = self.tab_evolucion

        top_frame = tk.Frame(frame, bg=COLOR_FONDO)
        top_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(top_frame, text="Paciente:", bg=COLOR_FONDO, font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.evol_paciente_var = tk.StringVar()
        self.evol_paciente_var.set("Seleccione un paciente")
        tk.Label(top_frame, textvariable=self.evol_paciente_var, 
                bg=COLOR_FONDO, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)

        tk.Button(top_frame, text="Cambiar Paciente", command=self.cambiar_paciente_evolucion,
                 bg=COLOR_SECUNDARIO, fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
        tk.Button(top_frame, text="Actualizar", command=self.actualizar_graficos_evolucion,
                 bg=COLOR_EXITO, fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=5)

        graficos_frame = tk.Frame(frame, bg='white')
        graficos_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.fig_evol = Figure(figsize=(12, 6), dpi=100)
        self.fig_evol.patch.set_facecolor('white')

        self.ax_evol1 = self.fig_evol.add_subplot(231)
        self.ax_evol2 = self.fig_evol.add_subplot(232)
        self.ax_evol3 = self.fig_evol.add_subplot(233)
        self.ax_evol4 = self.fig_evol.add_subplot(234)
        self.ax_evol5 = self.fig_evol.add_subplot(235)
        self.ax_evol6 = self.fig_evol.add_subplot(236)
        self.ax_evol6.axis('off')

        self.fig_evol.tight_layout()

        self.canvas_evol = FigureCanvasTkAgg(self.fig_evol, master=graficos_frame)
        self.canvas_evol.draw()
        self.canvas_evol.get_tk_widget().pack(fill='both', expand=True)

        pred_frame = tk.LabelFrame(frame, text="Prediccion para Proxima Sesion",
                                   bg=COLOR_FONDO, font=('Arial', 10, 'bold'))
        pred_frame.pack(fill='x', padx=10, pady=5)

        self.pred_text = tk.Text(pred_frame, height=4, width=80, font=('Courier', 9))
        self.pred_text.pack(pady=5)

    def actualizar_graficos_evolucion(self):
        if not self.paciente_actual:
            return
        
        try:
            sesiones = self.db.obtener_historial_paciente(self.paciente_actual['id'])
            if len(sesiones) < 1:
                self.limpiar_graficos_evolucion()
                self.pred_text.delete(1.0, tk.END)
                self.pred_text.insert(1.0, "No hay suficientes sesiones para analisis de evolucion.")
                return
            
            for ax in [self.ax_evol1, self.ax_evol2, self.ax_evol3, self.ax_evol4, self.ax_evol5]:
                ax.clear()
            
            x = list(range(1, len(sesiones) + 1))
            tvocs = [float(s.get('tvoc_medio', 0) or 0) for s in sesiones]
            riesgos = [float(s.get('riesgo', 0) or 0) * 100 for s in sesiones]
            volumenes = [float(s.get('volumen', 0) or 0) for s in sesiones]
            
            self.ax_evol1.plot(x, tvocs, 'bo-', linewidth=2, markersize=8)
            self.ax_evol1.set_title('Evolucion TVOC', fontsize=10)
            self.ax_evol1.set_xlabel('Sesion')
            self.ax_evol1.set_ylabel('TVOC (ppb)')
            self.ax_evol1.grid(True, alpha=0.3)
            self.ax_evol1.set_xticks(x)
            
            self.ax_evol2.plot(x, riesgos, 'ro-', linewidth=2, markersize=8)
            self.ax_evol2.set_title('Evolucion Riesgo IA', fontsize=10)
            self.ax_evol2.set_xlabel('Sesion')
            self.ax_evol2.set_ylabel('Riesgo (%)')
            self.ax_evol2.grid(True, alpha=0.3)
            self.ax_evol2.set_xticks(x)
            self.ax_evol2.set_ylim(0, 100)
            
            self.ax_evol3.plot(x, volumenes, 'go-', linewidth=2, markersize=8)
            self.ax_evol3.set_title('Evolucion Volumen', fontsize=10)
            self.ax_evol3.set_xlabel('Sesion')
            self.ax_evol3.set_ylabel('Volumen (L)')
            self.ax_evol3.grid(True, alpha=0.3)
            self.ax_evol3.set_xticks(x)
            
            correlaciones = []
            for s in sesiones:
                try:
                    sesion_completa = self.db.obtener_sesion_completa(s['id'])
                    if sesion_completa:
                        correlaciones.append(float(sesion_completa.get('correlacion_voc_flujo', 0) or 0))
                    else:
                        correlaciones.append(0.0)
                except Exception:
                    correlaciones.append(0.0)
            
            self.ax_evol4.plot(x, correlaciones, 'mo-', linewidth=2, markersize=8)
            self.ax_evol4.set_title('Correlacion VOC-Flujo', fontsize=10)
            self.ax_evol4.set_xlabel('Sesion')
            self.ax_evol4.set_ylabel('r')
            self.ax_evol4.grid(True, alpha=0.3)
            self.ax_evol4.set_xticks(x)
            self.ax_evol4.set_ylim(-1, 1)
            self.ax_evol4.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            
            self.ax_evol5.plot(x, tvocs, 'bo-', linewidth=2, markersize=8)
            self.ax_evol5.set_title('TVOC Medio por Sesion', fontsize=10)
            self.ax_evol5.set_xlabel('Sesion')
            self.ax_evol5.set_ylabel('TVOC (ppb)')
            self.ax_evol5.grid(True, alpha=0.3)
            self.ax_evol5.set_xticks(x)
            
            self.ax_evol6.clear()
            self.ax_evol6.axis('off')
            
            texto_resumen = f"""
 RESUMEN DE EVOLUCION
{'='*30}
Paciente: {self.paciente_actual['nombre']}
Total sesiones: {len(sesiones)}

 DATOS RECIENTES:
TVOC actual: {tvocs[-1]:.0f} ppb
Riesgo actual: {riesgos[-1]:.1f}%
Volumen actual: {volumenes[-1]:.2f} L
{'='*30}
            """
            
            self.ax_evol6.text(0.1, 0.5, texto_resumen, fontsize=9, 
                              verticalalignment='center',
                              family='monospace',
                              transform=self.ax_evol6.transAxes,
                              bbox=dict(boxstyle="round,pad=0.5", facecolor='lightyellow'))
            
            self.fig_evol.tight_layout()
            self.canvas_evol.draw()
            self.actualizar_prediccion()
            
        except Exception as e:
            self.status_var.set(f"Error en evolucion: {str(e)[:50]}")
            self.limpiar_graficos_evolucion()

    def limpiar_graficos_evolucion(self):
        for ax in [self.ax_evol1, self.ax_evol2, self.ax_evol3, self.ax_evol4, self.ax_evol5]:
            ax.clear()
        self.ax_evol6.clear()
        self.ax_evol6.axis('off')
        self.ax_evol6.text(0.5, 0.5, 'Seleccione un paciente con sesiones', 
                          ha='center', va='center', fontsize=12, transform=self.ax_evol6.transAxes)
        self.fig_evol.tight_layout()
        self.canvas_evol.draw()

    def actualizar_prediccion(self):
        if not self.paciente_actual or not self.analizador:
            return
        
        try:
            paciente_id = self.paciente_actual['id']
            sesiones = self.db.obtener_historial_paciente(paciente_id)
            
            if len(sesiones) < 2:
                self.pred_text.delete(1.0, tk.END)
                self.pred_text.insert(1.0, "Se necesitan al menos 2 sesiones para generar predicciones.")
                return
            
            prediccion = self.analizador.predecir_proxima_sesion(paciente_id)
            
            if prediccion:
                texto = f"""
 PREDICCION PARA PROXIMA SESION (Sesion N° {len(sesiones) + 1})
{'-'*60}
TVOC esperado: {prediccion['tvoc_esperado']:.0f} ppb
Rango probable (95%): [{prediccion['intervalo_tvoc'][0]:.0f} - {prediccion['intervalo_tvoc'][1]:.0f}] ppb
Riesgo esperado: {prediccion['riesgo_esperado']*100:.1f}%
Confianza: {prediccion['confianza']*100:.0f}%
                """
                self.pred_text.delete(1.0, tk.END)
                self.pred_text.insert(1.0, texto)
            else:
                self.pred_text.delete(1.0, tk.END)
                self.pred_text.insert(1.0, "No se pudo generar prediccion.\nSe necesitan mas datos.")
        except Exception as e:
            self.pred_text.delete(1.0, tk.END)
            self.pred_text.insert(1.0, f"Error al generar prediccion: {str(e)[:100]}")

    def guardar_sesion(self):
        messagebox.showinfo("Info", "La sesion ya fue guardada automaticamente en la base de datos.")

    def configurar_puerto(self):
        top = tk.Toplevel(self.root)
        top.title("Configurar Puerto Serial")
        top.geometry("300x150")

        tk.Label(top, text="Puerto COM:").pack(pady=5)
        entry = tk.Entry(top)
        entry.insert(0, config.SERIAL_CONFIG.get('puerto', 'COM3'))
        entry.pack(pady=5)

        def guardar():
            config.SERIAL_CONFIG['puerto'] = entry.get()
            messagebox.showinfo("Info", f"Puerto configurado a {entry.get()}")
            top.destroy()

        tk.Button(top, text="Guardar", command=guardar).pack(pady=10)

    def ver_carpeta_reportes(self):
        import subprocess
        folder = str(config.PDF_CONFIG['directorio'].absolute())
        Path(folder).mkdir(parents=True, exist_ok=True)
        if os.name == 'nt':
            subprocess.run(['explorer', folder])

    def verificar_servidor(self):
        estado = "=== ESTADO DEL SERVIDOR i7 ===\n\n"
        try:
            if self.db.conn and self.db.cursor:
                self.db.cursor.execute("SELECT 1")
                estado += "[OK] Base de datos PostgreSQL: OK\n"
            else:
                estado += "[X] Base de datos: No conectada\n"
        except Exception as e:
            estado += f"[X] Base de datos: Error - {str(e)}\n"
        
        messagebox.showinfo("Estado del Servidor i7", estado)

    def analizar_evolucion_actual(self):
        if not self.paciente_actual:
            messagebox.showwarning("Sin paciente", "Primero seleccione un paciente")
            self.buscar_paciente()
            return
        self.notebook.select(self.tab_evolucion)
        self.cambiar_paciente_evolucion()

    def exportar_historial(self):
        if not self.paciente_actual:
            messagebox.showwarning("Sin paciente", "Seleccione un paciente primero")
            return
        
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Guardar historial como CSV"
        )
        
        if not filename:
            return
        
        try:
            sesiones = self.db.obtener_historial_paciente(self.paciente_actual['id'])
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Sesion', 'Fecha', 'TVOC (ppb)', 'eCO2 (ppm)', 
                               'Riesgo (%)', 'Volumen (L)', 'Notas'])
                
                for s in sesiones:
                    writer.writerow([
                        s['num_sesion'],
                        s['fecha'],
                        f"{s['tvoc_medio']:.0f}",
                        f"{s['eco2_medio']:.0f}",
                        f"{s['riesgo']*100:.1f}",
                        f"{s['volumen']:.3f}",
                        s.get('notas_seguimiento', '')
                    ])
            
            messagebox.showinfo("Exito", f"Historial exportado a:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def crear_pestania_geografia(self):
        frame = self.tab_geografia
        
        filtros_frame = tk.LabelFrame(frame, text="Filtros Geograficos", 
                                      font=('Arial', 10, 'bold'), bg=COLOR_FONDO)
        filtros_frame.pack(fill='x', padx=10, pady=5)
        
        row = 0
        tk.Label(filtros_frame, text="Pais:", bg=COLOR_FONDO).grid(row=row, column=0, padx=5, pady=5, sticky='e')
        self.filtro_pais = tk.Entry(filtros_frame, width=20)
        self.filtro_pais.grid(row=row, column=1, padx=5, pady=5)
        
        tk.Label(filtros_frame, text="Departamento:", bg=COLOR_FONDO).grid(row=row, column=2, padx=5, pady=5, sticky='e')
        self.filtro_depto = tk.Entry(filtros_frame, width=20)
        self.filtro_depto.grid(row=row, column=3, padx=5, pady=5)
        
        tk.Label(filtros_frame, text="Ciudad:", bg=COLOR_FONDO).grid(row=row+1, column=0, padx=5, pady=5, sticky='e')
        self.filtro_ciudad = tk.Entry(filtros_frame, width=20)
        self.filtro_ciudad.grid(row=row+1, column=1, padx=5, pady=5)
        
        tk.Label(filtros_frame, text="Institucion:", bg=COLOR_FONDO).grid(row=row+1, column=2, padx=5, pady=5, sticky='e')
        self.filtro_institucion = tk.Entry(filtros_frame, width=20)
        self.filtro_institucion.grid(row=row+1, column=3, padx=5, pady=5)
        
        btn_aplicar = tk.Button(filtros_frame, text="Aplicar Filtros", command=self.actualizar_estadisticas_geograficas,
                               bg=COLOR_SECUNDARIO, fg='white')
        btn_aplicar.grid(row=row+2, column=1, columnspan=2, pady=10)
        
        stats_frame = tk.LabelFrame(frame, text="Estadisticas por Ubicacion", 
                                    font=('Arial', 10, 'bold'), bg=COLOR_FONDO)
        stats_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        columns = ('Pais', 'Departamento', 'Ciudad', 'Institucion', 'Pacientes', 'Sesiones', 'TVOC Prom', 'Riesgo Prom', 'Alto Riesgo')
        self.tree_stats = ttk.Treeview(stats_frame, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.tree_stats.heading(col, text=col)
            if col in ['Pacientes', 'Sesiones']:
                self.tree_stats.column(col, width=80)
            elif col in ['TVOC Prom', 'Riesgo Prom']:
                self.tree_stats.column(col, width=100)
            elif col == 'Alto Riesgo':
                self.tree_stats.column(col, width=100)
            else:
                self.tree_stats.column(col, width=120)
        
        scroll_stats = ttk.Scrollbar(stats_frame, orient='vertical', command=self.tree_stats.yview)
        self.tree_stats.configure(yscrollcommand=scroll_stats.set)
        self.tree_stats.pack(side='left', fill='both', expand=True)
        scroll_stats.pack(side='right', fill='y')
        
        alertas_frame = tk.LabelFrame(frame, text="Alertas Geograficas", 
                                      font=('Arial', 10, 'bold'), bg=COLOR_FONDO)
        alertas_frame.pack(fill='x', padx=10, pady=5)
        
        self.text_alertas = tk.Text(alertas_frame, height=6, width=80, font=('Courier', 9))
        self.text_alertas.pack(pady=5)
        
        btn_exportar = tk.Button(frame, text="Exportar Estadisticas", 
                                 command=self.exportar_estadisticas_geograficas,
                                 bg=COLOR_EXITO, fg='white', font=('Arial', 10, 'bold'))
        btn_exportar.pack(pady=10)
        
        self.text_alertas.insert(1.0, "Esperando datos...")

    def actualizar_estadisticas_geograficas(self):
        try:
            if not self.db.conn or not self.db.cursor:
                self.status_var.set("[X] Base de datos no conectada")
                self.text_alertas.delete(1.0, tk.END)
                self.text_alertas.insert(1.0, "[!] No hay conexion con la base de datos.")
                return
            
            filtros = {}
            pais = self.filtro_pais.get().strip()
            if pais:
                filtros['pais'] = pais
            
            depto = self.filtro_depto.get().strip()
            if depto:
                filtros['departamento'] = depto
            
            ciudad = self.filtro_ciudad.get().strip()
            if ciudad:
                filtros['ciudad'] = ciudad
            
            stats = self.db.obtener_estadisticas_geograficas(
                filtros.get('pais', ''),
                filtros.get('departamento', ''),
                filtros.get('ciudad', '')
            )
            
            for item in self.tree_stats.get_children():
                self.tree_stats.delete(item)
            
            if not stats:
                self.status_var.set("[!] No hay datos estadisticos disponibles")
                self.text_alertas.delete(1.0, tk.END)
                self.text_alertas.insert(1.0, "No hay suficientes datos para generar estadisticas.")
                return
            
            for stat in stats:
                pais_val = stat.get('pais') or 'N/A'
                depto_val = stat.get('departamento') or 'N/A'
                ciudad_val = stat.get('ciudad') or 'N/A'
                institucion_val = stat.get('institucion') or 'N/A'
                pacientes_val = stat.get('total_pacientes', 0) or 0
                sesiones_val = stat.get('total_sesiones', 0) or 0
                tvoc_val = stat.get('tvoc_promedio', 0) or 0
                riesgo_val = stat.get('riesgo_promedio', 0) or 0
                riesgo_pct = riesgo_val * 100 if riesgo_val else 0
                alto_riesgo_val = stat.get('muestras_alto_riesgo', 0) or 0
                
                self.tree_stats.insert('', 'end', values=(
                    pais_val, depto_val, ciudad_val, institucion_val,
                    pacientes_val, sesiones_val,
                    f"{tvoc_val:.0f}" if tvoc_val else "0",
                    f"{riesgo_pct:.1f}%" if riesgo_pct else "0%",
                    alto_riesgo_val
                ))
            
            self.generar_alertas_geograficas(stats)
            self.status_var.set(f"[OK] Estadisticas actualizadas - {len(stats)} ubicaciones encontradas")
            
        except Exception as e:
            self.status_var.set(f"[X] Error: {str(e)[:50]}")
            self.text_alertas.delete(1.0, tk.END)
            self.text_alertas.insert(1.0, f"Error al cargar estadisticas:\n{str(e)}")

    def generar_alertas_geograficas(self, stats):
        self.text_alertas.delete(1.0, tk.END)
        
        if not stats:
            self.text_alertas.insert(1.0, "[!] No hay datos suficientes para generar alertas.")
            return
        
        alertas = []
        umbral_tvoc_alto = 800
        umbral_riesgo_alto = 0.6
        
        for stat in stats:
            tvoc = stat.get('tvoc_promedio', 0) or 0
            riesgo = stat.get('riesgo_promedio', 0) or 0
            total_sesiones = stat.get('total_sesiones', 0) or 0
            
            ciudad = stat.get('ciudad') or ''
            if not ciudad:
                continue
            
            ubicacion = f"{ciudad}, {stat.get('departamento', 'N/A')}"
            institucion = stat.get('institucion', 'N/A') or 'N/A'
            
            if total_sesiones >= 3:
                if tvoc > umbral_tvoc_alto:
                    alertas.append(f"[ALTA] CONCENTRACION TVOC en {ubicacion} ({institucion}): {tvoc:.0f} ppb")
                
                if riesgo > umbral_riesgo_alto:
                    alertas.append(f"[ALTO] RIESGO PROMEDIO en {ubicacion} ({institucion}): {riesgo*100:.1f}%")
        
        if alertas:
            self.text_alertas.insert(1.0, "\n".join(alertas))
        else:
            self.text_alertas.insert(1.0, "[OK] No se detectaron anomalias geograficas.")

    def exportar_estadisticas_geograficas(self):
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Guardar estadisticas geograficas como CSV"
        )
        
        if not filename:
            return
        
        try:
            stats = self.db.obtener_estadisticas_geograficas()
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Pais', 'Departamento', 'Ciudad', 'Institucion', 
                               'Total Pacientes', 'Total Sesiones', 'TVOC Promedio', 
                               'Riesgo Promedio (%)', 'Muestras Alto Riesgo'])
                
                for stat in stats:
                    writer.writerow([
                        stat.get('pais', '') or '',
                        stat.get('departamento', '') or '',
                        stat.get('ciudad', '') or '',
                        stat.get('institucion', '') or '',
                        stat.get('total_pacientes', 0) or 0,
                        stat.get('total_sesiones', 0) or 0,
                        f"{stat.get('tvoc_promedio', 0) or 0:.2f}",
                        f"{(stat.get('riesgo_promedio', 0) or 0)*100:.2f}",
                        stat.get('muestras_alto_riesgo', 0) or 0
                    ])
            
            messagebox.showinfo("Exito", f"Estadisticas exportadas a:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def mostrar_estadisticas_geograficas(self):
        self.notebook.select(self.tab_geografia)
        self.actualizar_estadisticas_geograficas()

    def mostrar_acerca(self):
        acerca_texto = """
SISTEMA DENCO v3.9 - MODO SERVIDOR
Deteccion de Efecto Warburg en Aliento

Caracteristicas:
[+] Graficas en tiempo real funcionando
[+] Capturas multiples consecutivas
[+] Cierre/reapertura de puerto entre capturas
[+] Registro de pacientes con ubicacion geografica
[+] Combobox con autocompletado fluido
[+] Sincronizacion Pais -> Departamento -> Ciudad
[+] Permite escribir texto libre si no esta en lista
[+] Analisis de evolucion longitudinal
[+] Prediccion de tendencias
[+] Clasificacion ISO 13138
[+] Calculos ISO 16000-9
[+] IA no supervisada
[+] Analisis geografico
[+] Generacion de reportes PDF

Desarrollado con Python, Tkinter, scikit-learn
        """
        messagebox.showinfo("Acerca de DENCO v3.9", acerca_texto)

    def mostrar_guia(self):
        guia = """
GUIA RAPIDA DE USO:

1. VERIFICAR CONEXIONES:
   - Asegurese de que el Arduino este conectado
   - Verifique el puerto COM en el menu Archivo

2. REGISTRAR PACIENTE:
   - Complete el formulario
   - En Pais, escriba o seleccione de la lista (ej: U uruguay)
   - El departamento y ciudad se actualizan automaticamente
   - Puede escribir cualquier texto si no esta en la lista
   - Click en "Registrar Paciente"

3. REALIZAR CAPTURA:
   - Vaya a pestaña "Captura en Tiempo Real"
   - Click "INICIAR CAPTURA"
   - El paciente debe exhalar
   - LAS GRAFICAS SE MUESTRAN EN TIEMPO REAL

4. VER RESULTADOS:
   - Vaya a pestaña "Resultados"
   - Revise los parametros calculados
   - Genere PDF

5. ANALIZAR EVOLUCION:
   - Vaya a pestaña "Evolucion"
   - Vea graficos de tendencia
        """
        messagebox.showinfo("Guia Rapida DENCO v3.9", guia)

    def cerrar_app(self):
        if self.capturando:
            self.capturando = False
            time.sleep(0.5)
        if self.after_id_grafica:
            try:
                self.root.after_cancel(self.after_id_grafica)
            except:
                pass
        self.serial_mgr.cerrar()
        self.db.cerrar()
        self.root.quit()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = InterfazDenco(root)
    root.mainloop()


if __name__ == "__main__":
    main()