#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ventana de búsqueda de pacientes para DENCO
Permite buscar, ver historial y comparar sesiones
ACTUALIZADO v3.3: Incluye ubicación geográfica y dirección
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class BuscadorDialog:
    def __init__(self, parent, db_manager, visualizador, callback_seleccionar):
        """
        Diálogo de búsqueda de pacientes
        
        Args:
            parent: Ventana padre
            db_manager: Instancia de DatabaseManager
            visualizador: Instancia de Visualizador
            callback_seleccionar: Función a llamar cuando se selecciona un paciente
        """
        self.parent = parent
        self.db = db_manager
        self.viz = visualizador
        self.callback = callback_seleccionar
        
        self.resultados = []
        self.sesiones_actuales = []
        self.paciente_seleccionado = None
        
        # Crear ventana
        self.top = tk.Toplevel(parent)
        self.top.title("Buscar Paciente - Historial de Sesiones")
        self.top.geometry("1300x800")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.crear_interfaz()
        
    def crear_interfaz(self):
        # Frame superior de búsqueda
        frame_busqueda = tk.LabelFrame(self.top, text="[BUSCAR] Paciente", 
                                       font=('Arial', 10, 'bold'))
        frame_busqueda.pack(fill='x', padx=10, pady=10)
        
        # Fila 1: Búsqueda por texto
        row1 = tk.Frame(frame_busqueda)
        row1.pack(fill='x', padx=5, pady=5)
        
        tk.Label(row1, text="Nombre, ID, Direccion o Ubicacion:").pack(side='left', padx=5)
        self.entry_busqueda = tk.Entry(row1, width=40)
        self.entry_busqueda.pack(side='left', padx=5)
        self.entry_busqueda.bind('<Return>', lambda e: self.buscar())
        
        tk.Button(row1, text="Buscar", command=self.buscar,
                 bg='#3498db', fg='white').pack(side='left', padx=5)
        
        # Fila 2: Filtros geográficos
        row2 = tk.Frame(frame_busqueda)
        row2.pack(fill='x', padx=5, pady=5)
        
        tk.Label(row2, text="Filtrar por:").pack(side='left', padx=(0,10))
        
        tk.Label(row2, text="Pais:").pack(side='left')
        self.filtro_pais = tk.Entry(row2, width=15)
        self.filtro_pais.pack(side='left', padx=2)
        
        tk.Label(row2, text="Departamento:").pack(side='left', padx=(10,0))
        self.filtro_departamento = tk.Entry(row2, width=15)
        self.filtro_departamento.pack(side='left', padx=2)
        
        tk.Label(row2, text="Ciudad:").pack(side='left', padx=(10,0))
        self.filtro_ciudad = tk.Entry(row2, width=15)
        self.filtro_ciudad.pack(side='left', padx=2)
        
        tk.Label(row2, text="Institucion:").pack(side='left', padx=(10,0))
        self.filtro_institucion = tk.Entry(row2, width=15)
        self.filtro_institucion.pack(side='left', padx=2)
        
        tk.Button(row2, text="Aplicar Filtros", command=self.buscar,
                 bg='#27ae60', fg='white').pack(side='left', padx=10)
        
        tk.Button(row2, text="Limpiar Filtros", command=self.limpiar_filtros,
                 bg='#e67e22', fg='white').pack(side='left', padx=5)
        
        # Frame de resultados (dividido en dos columnas)
        frame_principal = tk.Frame(self.top)
        frame_principal.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Panel izquierdo: Lista de pacientes encontrados
        frame_pacientes = tk.LabelFrame(frame_principal, text="[LISTA] Pacientes Encontrados",
                                        font=('Arial', 10, 'bold'))
        frame_pacientes.pack(side='left', fill='both', expand=True, padx=5)
        
        # Treeview para pacientes - CON UBICACIÓN GEOGRÁFICA Y DIRECCIÓN
        columns = ('ID', 'Nombre', 'Edad', 'Direccion', 'Ciudad', 'Departamento', 'Pais', 'Institucion', 'Contacto', 'Registro')
        self.tree_pacientes = ttk.Treeview(frame_pacientes, columns=columns, 
                                           show='headings', height=12)
        
        self.tree_pacientes.heading('ID', text='ID')
        self.tree_pacientes.heading('Nombre', text='Nombre')
        self.tree_pacientes.heading('Edad', text='Edad')
        self.tree_pacientes.heading('Direccion', text='Direccion')
        self.tree_pacientes.heading('Ciudad', text='Ciudad')
        self.tree_pacientes.heading('Departamento', text='Depto.')
        self.tree_pacientes.heading('Pais', text='Pais')
        self.tree_pacientes.heading('Institucion', text='Institucion')
        self.tree_pacientes.heading('Contacto', text='Contacto')
        self.tree_pacientes.heading('Registro', text='Fecha Registro')
        
        self.tree_pacientes.column('ID', width=50)
        self.tree_pacientes.column('Nombre', width=150)
        self.tree_pacientes.column('Edad', width=50)
        self.tree_pacientes.column('Direccion', width=180)
        self.tree_pacientes.column('Ciudad', width=100)
        self.tree_pacientes.column('Departamento', width=100)
        self.tree_pacientes.column('Pais', width=80)
        self.tree_pacientes.column('Institucion', width=120)
        self.tree_pacientes.column('Contacto', width=100)
        self.tree_pacientes.column('Registro', width=100)
        
        scroll_pac = ttk.Scrollbar(frame_pacientes, orient='vertical', 
                                   command=self.tree_pacientes.yview)
        self.tree_pacientes.configure(yscrollcommand=scroll_pac.set)
        
        self.tree_pacientes.pack(side='left', fill='both', expand=True)
        scroll_pac.pack(side='right', fill='y')
        
        self.tree_pacientes.bind('<<TreeviewSelect>>', self.on_paciente_seleccionado)
        
        # Panel derecho: Historial de sesiones
        frame_historial = tk.LabelFrame(frame_principal, text="[HISTORIAL] Sesiones",
                                        font=('Arial', 10, 'bold'))
        frame_historial.pack(side='right', fill='both', expand=True, padx=5)
        
        # Treeview para sesiones
        columns_ses = ('#', 'Fecha', 'TVOC', 'eCO2', 'Riesgo', 'Volumen', 'Notas')
        self.tree_sesiones = ttk.Treeview(frame_historial, columns=columns_ses,
                                          show='headings', height=12)
        
        self.tree_sesiones.heading('#', text='Sesion')
        self.tree_sesiones.heading('Fecha', text='Fecha')
        self.tree_sesiones.heading('TVOC', text='TVOC (ppb)')
        self.tree_sesiones.heading('eCO2', text='eCO2 (ppm)')
        self.tree_sesiones.heading('Riesgo', text='Riesgo %')
        self.tree_sesiones.heading('Volumen', text='Vol (L)')
        self.tree_sesiones.heading('Notas', text='Notas')
        
        self.tree_sesiones.column('#', width=50)
        self.tree_sesiones.column('Fecha', width=120)
        self.tree_sesiones.column('TVOC', width=70)
        self.tree_sesiones.column('eCO2', width=70)
        self.tree_sesiones.column('Riesgo', width=70)
        self.tree_sesiones.column('Volumen', width=60)
        self.tree_sesiones.column('Notas', width=150)
        
        scroll_ses = ttk.Scrollbar(frame_historial, orient='vertical',
                                   command=self.tree_sesiones.yview)
        self.tree_sesiones.configure(yscrollcommand=scroll_ses.set)
        
        self.tree_sesiones.pack(side='left', fill='both', expand=True)
        scroll_ses.pack(side='right', fill='y')
        
        self.tree_sesiones.bind('<<TreeviewSelect>>', self.on_sesion_seleccionado)
        
        # Frame de evolución y gráfico
        frame_evolucion = tk.LabelFrame(self.top, text="[GRAFICO] Analisis de Evolucion",
                                        font=('Arial', 10, 'bold'))
        frame_evolucion.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Frame para gráfico
        self.frame_grafico = tk.Frame(frame_evolucion, bg='white', height=200)
        self.frame_grafico.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Etiqueta de resumen de evolución
        self.label_evolucion = tk.Label(frame_evolucion, text="Seleccione un paciente para ver su evolucion",
                                         font=('Arial', 10, 'italic'), fg='gray')
        self.label_evolucion.pack(pady=5)
        
        # Etiqueta de ubicación del paciente
        self.label_ubicacion = tk.Label(frame_evolucion, text="",
                                         font=('Arial', 9), fg='#3498db')
        self.label_ubicacion.pack(pady=2)
        
        # Etiqueta de dirección del paciente
        self.label_direccion = tk.Label(frame_evolucion, text="",
                                         font=('Arial', 9), fg='#27ae60')
        self.label_direccion.pack(pady=2)
        
        # Frame de botones
        frame_botones = tk.Frame(self.top)
        frame_botones.pack(fill='x', padx=10, pady=10)
        
        tk.Button(frame_botones, text="[+] Agregar Nota a Sesion",
                 command=self.agregar_nota,
                 bg='#f39c12', fg='white', font=('Arial', 10)).pack(side='left', padx=5)
        
        tk.Button(frame_botones, text="[COMP] Comparar Dos Sesiones",
                 command=self.comparar_sesiones,
                 bg='#27ae60', fg='white', font=('Arial', 10)).pack(side='left', padx=5)
        
        tk.Button(frame_botones, text="[MAPA] Ver Ubicacion",
                 command=self.ver_mapa_ubicacion,
                 bg='#9b59b6', fg='white', font=('Arial', 10)).pack(side='left', padx=5)
        
        tk.Button(frame_botones, text="[DIR] Ver Direccion",
                 command=self.ver_direccion_completa,
                 bg='#1abc9c', fg='white', font=('Arial', 10)).pack(side='left', padx=5)
        
        tk.Button(frame_botones, text="[SEL] Seleccionar Paciente",
                 command=self.seleccionar_paciente,
                 bg='#2c3e50', fg='white', font=('Arial', 10, 'bold')).pack(side='right', padx=5)
        
        tk.Button(frame_botones, text="[X] Cerrar",
                 command=self.top.destroy,
                 bg='#e74c3c', fg='white').pack(side='right', padx=5)
    
    def limpiar_filtros(self):
        """Limpia todos los filtros de búsqueda"""
        self.filtro_pais.delete(0, tk.END)
        self.filtro_departamento.delete(0, tk.END)
        self.filtro_ciudad.delete(0, tk.END)
        self.filtro_institucion.delete(0, tk.END)
        self.buscar()
    
    def buscar(self):
        """Ejecuta la búsqueda de pacientes con filtros geográficos"""
        termino = self.entry_busqueda.get().strip()
        
        # Construir filtros
        filtros = {}
        pais = self.filtro_pais.get().strip()
        if pais:
            filtros['pais'] = pais
        
        departamento = self.filtro_departamento.get().strip()
        if departamento:
            filtros['departamento'] = departamento
        
        ciudad = self.filtro_ciudad.get().strip()
        if ciudad:
            filtros['ciudad'] = ciudad
        
        institucion = self.filtro_institucion.get().strip()
        if institucion:
            filtros['institucion'] = institucion
        
        # Limpiar árboles
        for item in self.tree_pacientes.get_children():
            self.tree_pacientes.delete(item)
        for item in self.tree_sesiones.get_children():
            self.tree_sesiones.delete(item)
        
        # Buscar
        self.resultados = self.db.buscar_pacientes(termino, filtros if filtros else None)
        
        if not self.resultados:
            msg = f"No se encontraron pacientes"
            if termino:
                msg += f" con '{termino}'"
            if filtros:
                msg += f"\nFiltros aplicados:"
                for k, v in filtros.items():
                    msg += f"\n  {k}: {v}"
            messagebox.showinfo("Sin resultados", msg)
            self.label_evolucion.config(text="No se encontraron resultados")
            self.label_ubicacion.config(text="")
            self.label_direccion.config(text="")
            return
        
        # Mostrar resultados
        for r in self.resultados:
            # Manejar fecha_registro
            fecha_registro = r.get('fecha_registro')
            if fecha_registro:
                if isinstance(fecha_registro, datetime):
                    fecha = fecha_registro.strftime('%d/%m/%Y')
                elif isinstance(fecha_registro, str):
                    try:
                        fecha = datetime.fromisoformat(fecha_registro).strftime('%d/%m/%Y')
                    except:
                        fecha = fecha_registro[:10] if len(fecha_registro) > 10 else fecha_registro
                else:
                    fecha = str(fecha_registro)
            else:
                fecha = 'N/A'
            
            # Obtener dirección
            direccion = r.get('direccion', '') or 'N/A'
            if len(direccion) > 25:
                direccion = direccion[:22] + "..."
            
            self.tree_pacientes.insert('', 'end', values=(
                r.get('id', ''),
                r.get('nombre', ''),
                r.get('edad', ''),
                direccion,
                r.get('ciudad', '') or 'N/A',
                r.get('departamento', '') or 'N/A',
                r.get('pais', '') or 'N/A',
                r.get('institucion', '') or 'N/A',
                r.get('contacto', ''),
                fecha
            ))
        
        self.label_evolucion.config(text=f"Se encontraron {len(self.resultados)} pacientes")
    
    def on_paciente_seleccionado(self, event):
        """Cuando se selecciona un paciente, mostrar su historial"""
        selection = self.tree_pacientes.selection()
        if not selection:
            return
        
        item = self.tree_pacientes.item(selection[0])
        paciente_id = item['values'][0]
        
        # Guardar paciente seleccionado
        for p in self.resultados:
            if p.get('id') == paciente_id:
                self.paciente_seleccionado = p
                break
        
        # Mostrar ubicación del paciente
        ubicacion = []
        if self.paciente_seleccionado.get('ciudad'):
            ubicacion.append(self.paciente_seleccionado['ciudad'])
        if self.paciente_seleccionado.get('departamento'):
            ubicacion.append(self.paciente_seleccionado['departamento'])
        if self.paciente_seleccionado.get('pais'):
            ubicacion.append(self.paciente_seleccionado['pais'])
        
        texto_ubicacion = f"[UBIC] {', '.join(ubicacion)}" if ubicacion else "[UBIC] No especificada"
        if self.paciente_seleccionado.get('institucion'):
            texto_ubicacion += f" | [INS] {self.paciente_seleccionado['institucion']}"
        
        self.label_ubicacion.config(text=texto_ubicacion)
        
        # Mostrar dirección
        direccion = self.paciente_seleccionado.get('direccion', '')
        if direccion:
            texto_direccion = f"[DIR] {direccion[:60]}{'...' if len(direccion) > 60 else ''}"
        else:
            texto_direccion = "[DIR] No especificada"
        self.label_direccion.config(text=texto_direccion)
        
        # Obtener historial
        self.sesiones_actuales = self.db.obtener_historial_paciente(paciente_id)
        
        # Limpiar árbol de sesiones
        for item in self.tree_sesiones.get_children():
            self.tree_sesiones.delete(item)
        
        # Mostrar sesiones
        for sesion in self.sesiones_actuales:
            riesgo_pct = sesion.get('riesgo', 0) * 100 if sesion.get('riesgo') else 0
            notas = sesion.get('notas_seguimiento', '')
            if notas and len(notas) > 20:
                notas = notas[:20] + "..."
            
            self.tree_sesiones.insert('', 'end', values=(
                f"{sesion.get('num_sesion', '')}a",
                sesion.get('fecha', ''),
                f"{sesion.get('tvoc_medio', 0):.0f}",
                f"{sesion.get('eco2_medio', 0):.0f}",
                f"{riesgo_pct:.1f}%",
                f"{sesion.get('volumen', 0):.3f}",
                notas
            ), tags=(sesion.get('id'),))
        
        # Mostrar evolución
        self.mostrar_evolucion()
    
    def on_sesion_seleccionado(self, event):
        """Cuando se selecciona una sesión, mostrar detalles"""
        selection = self.tree_sesiones.selection()
        if not selection or not self.paciente_seleccionado:
            return
        
        item = self.tree_sesiones.item(selection[0])
        sesion_id = item['tags'][0]
        
        # Obtener sesión completa
        sesion = self.db.obtener_sesion_completa(sesion_id)
        
        if sesion and sesion.get('muestras'):
            # Mostrar gráfico rápido de la sesión
            self.mostrar_grafico_sesion(sesion['muestras'])
    
    def mostrar_evolucion(self):
        """Muestra el gráfico de evolución del paciente"""
        if len(self.sesiones_actuales) < 1:
            return
        
        # Limpiar frame anterior
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()
        
        # Crear gráfico de evolución
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3))
        
        # Extraer datos
        fechas = [s.get('fecha', '') for s in self.sesiones_actuales]
        tvocs = [s.get('tvoc_medio', 0) for s in self.sesiones_actuales]
        riesgos = [s.get('riesgo', 0) * 100 for s in self.sesiones_actuales]
        
        x = range(len(fechas))
        
        # Gráfico TVOC
        ax1.plot(x, tvocs, 'bo-', linewidth=2, markersize=8)
        ax1.set_xlabel('Sesion')
        ax1.set_ylabel('TVOC (ppb)')
        ax1.set_title('Evolucion de TVOC')
        ax1.set_xticks(x)
        ax1.set_xticklabels([f"{i+1}a" for i in x])
        ax1.grid(True, alpha=0.3)
        
        # Calcular tendencia
        if len(tvocs) > 1:
            cambio = tvocs[-1] - tvocs[0]
            cambio_pct = (cambio / tvocs[0] * 100) if tvocs[0] > 0 else 0
            
            if cambio < -10:
                color = 'green'
                texto = f"[MEJORA] {cambio_pct:.1f}%"
            elif cambio > 10:
                color = 'red'
                texto = f"[EMPEORA] +{cambio_pct:.1f}%"
            else:
                color = 'orange'
                texto = f"[ESTABLE] {cambio_pct:.1f}%"
            
            ax1.set_title(f'Evolucion de TVOC - {texto}', color=color)
        
        # Gráfico riesgo
        ax2.plot(x, riesgos, 'ro-', linewidth=2, markersize=8)
        ax2.set_xlabel('Sesion')
        ax2.set_ylabel('Riesgo (%)')
        ax2.set_title('Evolucion del Riesgo IA')
        ax2.set_xticks(x)
        ax2.set_xticklabels([f"{i+1}a" for i in x])
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Mostrar nuevo gráfico
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Actualizar texto de evolución
        if len(self.sesiones_actuales) >= 2:
            primera = self.sesiones_actuales[0]
            ultima = self.sesiones_actuales[-1]
            cambio = ultima.get('tvoc_medio', 0) - primera.get('tvoc_medio', 0)
            cambio_pct = (cambio / primera.get('tvoc_medio', 1) * 100) if primera.get('tvoc_medio', 0) > 0 else 0
            
            texto = f"[{len(self.sesiones_actuales)} sesiones] "
            texto += f"1a: {primera.get('tvoc_medio', 0):.0f} ppb | "
            texto += f"Ultima: {ultima.get('tvoc_medio', 0):.0f} ppb | "
            texto += f"Cambio: {cambio_pct:+.1f}%"
            
            if cambio < -10:
                texto += " [MEJORA SIGNIFICATIVA]"
            elif cambio > 10:
                texto += " [EMPEORAMIENTO]"
            
            self.label_evolucion.config(text=texto, fg='black')
    
    def mostrar_grafico_sesion(self, muestras):
        """Muestra un gráfico rápido de una sesión específica"""
        if not muestras:
            return
        
        # Limpiar frame anterior
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3))
        
        # CORRECCIÓN: usar las claves correctas según captura_serial.py
        nums = [m.get('num', i) for i, m in enumerate(muestras, 1)]
        tvocs = [m.get('tvoc', 0) for m in muestras]
        flujos = [m.get('flujo', 0) for m in muestras]
        
        # Colorear por fracción
        colores = []
        for m in muestras:
            if m.get('fraccion') == 'ALVEOLAR':
                colores.append('green')
            elif m.get('fraccion') == 'ESPACIO_MUERTO':
                colores.append('orange')
            else:
                colores.append('blue')
        
        ax1.scatter(nums, tvocs, c=colores, alpha=0.6, s=15)
        ax1.plot(nums, tvocs, 'b-', alpha=0.3)
        ax1.set_title('TVOC (ppb)')
        ax1.set_xlabel('Muestra')
        ax1.grid(True, alpha=0.3)
        
        ax2.scatter(nums, flujos, c=colores, alpha=0.6, s=15)
        ax2.plot(nums, flujos, 'g-', alpha=0.3)
        ax2.set_title('Flujo (L/s)')
        ax2.set_xlabel('Muestra')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def agregar_nota(self):
        """Abre diálogo para agregar nota a una sesión"""
        selection = self.tree_sesiones.selection()
        if not selection:
            messagebox.showwarning("Seleccion requerida", "Seleccione una sesion")
            return
        
        item = self.tree_sesiones.item(selection[0])
        sesion_id = item['tags'][0]
        sesion_info = item['values']
        
        # Diálogo para nota
        dialog = tk.Toplevel(self.top)
        dialog.title("Agregar Nota de Seguimiento")
        dialog.geometry("400x250")
        dialog.transient(self.top)
        
        tk.Label(dialog, text=f"Sesion: {sesion_info[0]} - {sesion_info[1]}",
                font=('Arial', 10, 'bold')).pack(pady=10)
        
        if self.paciente_seleccionado:
            ubicacion = []
            if self.paciente_seleccionado.get('ciudad'):
                ubicacion.append(self.paciente_seleccionado['ciudad'])
            if self.paciente_seleccionado.get('institucion'):
                ubicacion.append(self.paciente_seleccionado['institucion'])
            if ubicacion:
                tk.Label(dialog, text=f"Paciente: {self.paciente_seleccionado.get('nombre')} - {', '.join(ubicacion)}",
                        font=('Arial', 9), fg='gray').pack()
        
        tk.Label(dialog, text="Nota:").pack()
        text_nota = tk.Text(dialog, height=6, width=50)
        text_nota.pack(pady=5)
        
        # Cargar nota existente si hay
        for s in self.sesiones_actuales:
            if s.get('id') == sesion_id and s.get('notas_seguimiento'):
                text_nota.insert('1.0', s['notas_seguimiento'])
                break
        
        def guardar():
            nota = text_nota.get('1.0', 'end-1c').strip()
            self.db.guardar_nota_seguimiento(sesion_id, nota)
            messagebox.showinfo("Exito", "Nota guardada correctamente")
            dialog.destroy()
            # Actualizar lista
            self.on_paciente_seleccionado(None)
        
        tk.Button(dialog, text="Guardar", command=guardar,
                 bg='#27ae60', fg='white').pack(pady=10)
    
    def comparar_sesiones(self):
        """Compara dos sesiones seleccionadas"""
        selection = self.tree_sesiones.selection()
        if len(selection) != 2:
            messagebox.showwarning("Seleccion requerida", 
                                  "Seleccione EXACTAMENTE DOS sesiones para comparar")
            return
        
        # Obtener IDs de las sesiones
        item1 = self.tree_sesiones.item(selection[0])
        item2 = self.tree_sesiones.item(selection[1])
        sesion1_id = item1['tags'][0]
        sesion2_id = item2['tags'][0]
        
        # Obtener sesiones completas
        sesion1 = self.db.obtener_sesion_completa(sesion1_id)
        sesion2 = self.db.obtener_sesion_completa(sesion2_id)
        
        if not sesion1 or not sesion2:
            messagebox.showerror("Error", "No se pudieron cargar las sesiones")
            return
        
        # Crear ventana de comparación
        comp_window = tk.Toplevel(self.top)
        comp_window.title("Comparacion de Sesiones")
        comp_window.geometry("1000x700")
        
        # Agregar información del paciente
        if self.paciente_seleccionado:
            info_frame = tk.Frame(comp_window, bg='#f0f0f0', relief=tk.RIDGE, bd=1)
            info_frame.pack(fill='x', padx=10, pady=5)
            
            paciente_text = f"Paciente: {self.paciente_seleccionado.get('nombre')} | "
            if self.paciente_seleccionado.get('ciudad'):
                paciente_text += f"Ciudad: {self.paciente_seleccionado.get('ciudad')} | "
            if self.paciente_seleccionado.get('institucion'):
                paciente_text += f"Institucion: {self.paciente_seleccionado.get('institucion')}"
            if self.paciente_seleccionado.get('direccion'):
                direccion_corta = self.paciente_seleccionado.get('direccion', '')[:40]
                paciente_text += f"\nDireccion: {direccion_corta}"
            
            tk.Label(info_frame, text=paciente_text, font=('Arial', 9), bg='#f0f0f0', 
                    wraplength=900, justify=tk.LEFT).pack(pady=5)
        
        # Crear figura con subplots
        fig, axes = plt.subplots(2, 3, figsize=(12, 9))
        
        # Datos sesión 1
        nums1 = [m.get('num', i) for i, m in enumerate(sesion1.get('muestras', []), 1)]
        tvocs1 = [m.get('tvoc', 0) for m in sesion1.get('muestras', [])]
        eco2s1 = [m.get('eco2', 0) for m in sesion1.get('muestras', [])]
        flujos1 = [m.get('flujo', 0) for m in sesion1.get('muestras', [])]
        
        # Datos sesión 2
        nums2 = [m.get('num', i) for i, m in enumerate(sesion2.get('muestras', []), 1)]
        tvocs2 = [m.get('tvoc', 0) for m in sesion2.get('muestras', [])]
        eco2s2 = [m.get('eco2', 0) for m in sesion2.get('muestras', [])]
        flujos2 = [m.get('flujo', 0) for m in sesion2.get('muestras', [])]
        
        # TVOC
        axes[0,0].plot(nums1, tvocs1, 'b-', label=f"Sesion {item1['values'][0]}")
        axes[0,0].plot(nums2, tvocs2, 'r-', label=f"Sesion {item2['values'][0]}")
        axes[0,0].set_title('TVOC (ppb)')
        axes[0,0].set_xlabel('Muestra')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        # eCO2
        axes[0,1].plot(nums1, eco2s1, 'b-', label=f"Sesion {item1['values'][0]}")
        axes[0,1].plot(nums2, eco2s2, 'r-', label=f"Sesion {item2['values'][0]}")
        axes[0,1].set_title('eCO2 (ppm)')
        axes[0,1].set_xlabel('Muestra')
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)
        
        # Flujo
        axes[0,2].plot(nums1, flujos1, 'b-', label=f"Sesion {item1['values'][0]}")
        axes[0,2].plot(nums2, flujos2, 'r-', label=f"Sesion {item2['values'][0]}")
        axes[0,2].set_title('Flujo (L/s)')
        axes[0,2].set_xlabel('Muestra')
        axes[0,2].legend()
        axes[0,2].grid(True, alpha=0.3)
        
        # Tabla comparativa
        axes[1,0].axis('off')
        axes[1,1].axis('off')
        axes[1,2].axis('off')
        
        # Texto comparativo
        cambio_tvoc = sesion2.get('tvoc_medio', 0) - sesion1.get('tvoc_medio', 0)
        cambio_riesgo = (sesion2.get('riesgo', 0) - sesion1.get('riesgo', 0)) * 100
        
        texto = f"""
        {'='*50}
        COMPARACION DE SESIONES
        {'='*50}
        
        [FECHA]:
        Sesion {item1['values'][0]}: {item1['values'][1]}
        Sesion {item2['values'][0]}: {item2['values'][1]}
        
        [TVOC MEDIO] (ppb):
        Sesion 1: {sesion1.get('tvoc_medio', 0):.0f}
        Sesion 2: {sesion2.get('tvoc_medio', 0):.0f}
        Diferencia: {cambio_tvoc:+.0f}
        
        [RIESGO IA]:
        Sesion 1: {sesion1.get('riesgo', 0)*100:.1f}%
        Sesion 2: {sesion2.get('riesgo', 0)*100:.1f}%
        Diferencia: {cambio_riesgo:+.1f}%
        
        [VOLUMEN] (L):
        Sesion 1: {sesion1.get('volumen_total_L', 0):.3f}
        Sesion 2: {sesion2.get('volumen_total_L', 0):.3f}
        
        [CORRELACION VOC-Flujo]:
        Sesion 1: {sesion1.get('correlacion_voc_flujo', 0):.3f}
        Sesion 2: {sesion2.get('correlacion_voc_flujo', 0):.3f}
        
        {'='*50}
        """
        
        # Evaluación del cambio
        if cambio_tvoc < -50:
            texto += "\n[MEJORA SIGNIFICATIVA] en TVOC"
        elif cambio_tvoc > 50:
            texto += "\n[EMPEORAMIENTO SIGNIFICATIVO] en TVOC"
        
        if cambio_riesgo < -10:
            texto += "\n[REDUCCION] del riesgo"
        elif cambio_riesgo > 10:
            texto += "\n[AUMENTO] del riesgo"
        
        axes[1,1].text(0.1, 0.5, texto, fontsize=9, 
                       verticalalignment='center',
                       family='monospace',
                       transform=axes[1,1].transAxes,
                       bbox=dict(boxstyle="round,pad=0.5", facecolor='lightyellow'))
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=comp_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Botón para guardar comparación
        def guardar_comparacion():
            mejora_tvoc = sesion1.get('tvoc_medio', 0) - sesion2.get('tvoc_medio', 0)
            mejora_riesgo = sesion1.get('riesgo', 0) - sesion2.get('riesgo', 0)
            
            self.db.registrar_comparacion_evolucion(
                self.paciente_seleccionado.get('id'),
                sesion1_id,
                sesion2_id,
                mejora_tvoc,
                sesion1.get('eco2_medio', 0) - sesion2.get('eco2_medio', 0),
                mejora_riesgo,
                "Comparacion generada automaticamente"
            )
            messagebox.showinfo("Exito", "Comparacion guardada en el historial")
        
        btn_frame = tk.Frame(comp_window)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Guardar Comparacion",
                 command=guardar_comparacion,
                 bg='#27ae60', fg='white').pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="Cerrar",
                 command=comp_window.destroy,
                 bg='#e74c3c', fg='white').pack(side='left', padx=5)
    
    def ver_mapa_ubicacion(self):
        """Muestra estadísticas y abre Google Maps con la ubicación del paciente"""
        if not self.paciente_seleccionado:
            messagebox.showwarning("Sin paciente", "Seleccione un paciente primero")
            return
        
        # Obtener datos con valores por defecto
        ciudad = self.paciente_seleccionado.get('ciudad', '') or ''
        departamento = self.paciente_seleccionado.get('departamento', '') or ''
        pais = self.paciente_seleccionado.get('pais', '') or ''
        direccion = self.paciente_seleccionado.get('direccion', '') or ''
        institucion = self.paciente_seleccionado.get('institucion', '') or ''
        nombre = self.paciente_seleccionado.get('nombre', 'Desconocido')
        paciente_id = self.paciente_seleccionado.get('id', 'N/A')
        
        if not ciudad and not departamento and not pais and not direccion:
            messagebox.showinfo("Sin ubicacion", 
                              "Este paciente no tiene ubicacion registrada.\n"
                              "Puede actualizar su perfil para agregar ubicacion.")
            return
        
        # Construir dirección para Google Maps
        partes_direccion = []
        if direccion and direccion.strip():
            partes_direccion.append(direccion.strip())
        if ciudad and ciudad.strip():
            partes_direccion.append(ciudad.strip())
        if departamento and departamento.strip():
            partes_direccion.append(departamento.strip())
        if pais and pais.strip():
            partes_direccion.append(pais.strip())
        
        direccion_completa = ", ".join(partes_direccion) if partes_direccion else ""
        
        # Crear ventana de información
        map_window = tk.Toplevel(self.top)
        map_window.title(f"Informacion Geografica - {nombre}")
        map_window.geometry("550x500")
        
        # Frame de información del paciente
        info_frame = tk.LabelFrame(map_window, text="Datos del Paciente", font=('Arial', 10, 'bold'))
        info_frame.pack(fill='x', padx=10, pady=5)
        
        info_text = f"""
Paciente: {nombre}
ID: {paciente_id}
{'='*40}
Pais: {pais if pais else 'N/A'}
Departamento: {departamento if departamento else 'N/A'}
Ciudad: {ciudad if ciudad else 'N/A'}
Institucion: {institucion if institucion else 'N/A'}
Direccion: {direccion if direccion else 'N/A'}
"""
        txt_info = tk.Text(info_frame, wrap=tk.WORD, font=('Courier', 10), height=8)
        txt_info.insert('1.0', info_text)
        txt_info.config(state=tk.DISABLED)
        txt_info.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Frame de estadísticas
        stats_frame = tk.LabelFrame(map_window, text="Estadisticas de la Ubicacion", font=('Arial', 10, 'bold'))
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        # Obtener estadísticas con manejo de errores
        try:
            stats = self.db.obtener_estadisticas_geograficas(pais, departamento, ciudad)
        except Exception as e:
            stats = []
            print(f"Error obteniendo estadísticas: {e}")
        
        stats_content = ""
        if stats:
            for stat in stats:
                # Convertir valores a números con manejo seguro
                total_pacientes = stat.get('total_pacientes', 0)
                if total_pacientes is None:
                    total_pacientes = 0
                
                total_sesiones = stat.get('total_sesiones', 0)
                if total_sesiones is None:
                    total_sesiones = 0
                
                tvoc_promedio = stat.get('tvoc_promedio', 0)
                if tvoc_promedio is None:
                    tvoc_promedio = 0
                
                riesgo_promedio = stat.get('riesgo_promedio', 0)
                if riesgo_promedio is None:
                    riesgo_promedio = 0
                
                muestras_alto_riesgo = stat.get('muestras_alto_riesgo', 0)
                if muestras_alto_riesgo is None:
                    muestras_alto_riesgo = 0
                
                if ciudad and stat.get('ciudad') == ciudad:
                    stats_content = f"""
{'='*40}
Total pacientes en {ciudad}: {total_pacientes}
Total sesiones: {total_sesiones}
TVOC promedio: {float(tvoc_promedio):.0f} ppb
Riesgo promedio: {float(riesgo_promedio)*100:.1f}%
Muestras alto riesgo: {muestras_alto_riesgo}
"""
                    break
        
        if not stats_content:
            stats_content = "\nNo hay datos estadisticos disponibles para esta ubicacion."
        
        txt_stats = tk.Text(stats_frame, wrap=tk.WORD, font=('Courier', 9), height=6)
        txt_stats.insert('1.0', stats_content)
        txt_stats.config(state=tk.DISABLED)
        txt_stats.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Frame de botones
        btn_frame = tk.Frame(map_window)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        # Botón para Google Maps (si hay dirección)
        if direccion_completa:
            def abrir_maps():
                import webbrowser
                import urllib.parse
                url = f"https://www.google.com/maps/search/{urllib.parse.quote(direccion_completa)}"
                webbrowser.open(url)
                print(f"[INFO] Abriendo Google Maps para: {direccion_completa}")
            
            btn_maps = tk.Button(btn_frame, text="🌍 Ver en Google Maps", 
                               command=abrir_maps,
                               bg='#34a853', fg='white', font=('Arial', 10, 'bold'),
                               padx=15, pady=5)
            btn_maps.pack(side=tk.LEFT, padx=5)
            
            def copiar_direccion():
                map_window.clipboard_clear()
                map_window.clipboard_append(direccion_completa)
                messagebox.showinfo("Copiado", "Dirección copiada al portapapeles")
            
            btn_copiar = tk.Button(btn_frame, text="📋 Copiar Direccion",
                                  command=copiar_direccion,
                                  bg='#fbbc04', fg='black',
                                  padx=10, pady=5)
            btn_copiar.pack(side=tk.LEFT, padx=5)
        else:
            # Si no hay dirección completa, mostrar advertencia
            tk.Label(btn_frame, text="⚠️ No hay direccion completa para mostrar en mapa",
                    fg='orange', font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        
        btn_cerrar = tk.Button(btn_frame, text="✖ Cerrar",
                              command=map_window.destroy,
                              bg='#e74c3c', fg='white',
                              padx=20, pady=5)
        btn_cerrar.pack(side=tk.RIGHT, padx=5)
        
        # Sugerencia si falta dirección
        if not direccion:
            tk.Label(map_window, 
                    text="💡 Sugerencia: Agregue una direccion para mejor precision en el mapa",
                    fg='orange', font=('Arial', 9)).pack(pady=5)
        """Muestra un mapa de ubicación del paciente (simulado)"""
        if not self.paciente_seleccionado:
            messagebox.showwarning("Sin paciente", "Seleccione un paciente primero")
            return
        
        ciudad = self.paciente_seleccionado.get('ciudad', '')
        departamento = self.paciente_seleccionado.get('departamento', '')
        pais = self.paciente_seleccionado.get('pais', '')
        
        if not ciudad and not departamento and not pais:
            messagebox.showinfo("Sin ubicacion", 
                              "Este paciente no tiene ubicacion registrada.\n"
                              "Puede actualizar su perfil para agregar ubicacion.")
            return
        
        # Crear ventana de información geográfica
        map_window = tk.Toplevel(self.top)
        map_window.title(f"Informacion Geografica - {self.paciente_seleccionado.get('nombre')}")
        map_window.geometry("550x500")
        
        # Información de ubicación
        info_text = f"""
        [UBICACION] INFORMACION GEOGRAFICA
        
        Paciente: {self.paciente_seleccionado.get('nombre')}
        ID: {self.paciente_seleccionado.get('id')}
        
        Ubicacion registrada:
        {'='*40}
        """
        
        if pais:
            info_text += f"\nPais: {pais}"
        if departamento:
            info_text += f"\nDepartamento: {departamento}"
        if ciudad:
            info_text += f"\nCiudad: {ciudad}"
        if self.paciente_seleccionado.get('institucion'):
            info_text += f"\nInstitucion: {self.paciente_seleccionado.get('institucion')}"
        if self.paciente_seleccionado.get('direccion'):
            info_text += f"\nDireccion: {self.paciente_seleccionado.get('direccion')}"
        
        # Estadísticas de la ubicación
        info_text += f"\n\n{'='*40}\n[ESTADISTICAS] DE LA UBICACION\n{'='*40}\n"
        
        # Obtener estadísticas de esta ubicación
        stats = self.db.obtener_estadisticas_geograficas(pais, departamento, ciudad)
        
        for stat in stats:
            if stat.get('ciudad') == ciudad or (ciudad and stat.get('ciudad') == ciudad):
                info_text += f"""
Total pacientes en {ciudad}: {stat.get('total_pacientes', 0)}
Total sesiones: {stat.get('total_sesiones', 0)}
TVOC promedio: {stat.get('tvoc_promedio', 0):.0f} ppb
Riesgo promedio: {stat.get('riesgo_promedio', 0)*100:.1f}%
Muestras alto riesgo: {stat.get('muestras_alto_riesgo', 0)}
                """
                break
        else:
            info_text += "\nNo hay datos estadisticos disponibles para esta ubicacion."
        
        # Mostrar texto
        text_widget = tk.Text(map_window, wrap=tk.WORD, font=('Courier', 10))
        text_widget.insert('1.0', info_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Botón para cerrar
        tk.Button(map_window, text="Cerrar", command=map_window.destroy,
                 bg='#3498db', fg='white').pack(pady=10)
        
        # Sugerencia para actualizar ubicación
        if not ciudad and not departamento:
            tk.Label(map_window, text="[SUGERENCIA] Actualice la ubicacion del paciente para mejor seguimiento",
                    fg='orange', font=('Arial', 9)).pack(pady=5)
    
    def ver_direccion_completa(self):
        """Muestra la dirección completa del paciente"""
        if not self.paciente_seleccionado:
            messagebox.showwarning("Sin paciente", "Seleccione un paciente primero")
            return
        
        direccion = self.paciente_seleccionado.get('direccion', '')
        nombre = self.paciente_seleccionado.get('nombre', '')
        
        if not direccion:
            messagebox.showinfo("Sin direccion", 
                              f"El paciente {nombre} no tiene direccion registrada.\n"
                              "Puede actualizar su perfil para agregar direccion.")
            return
        
        # Crear ventana de dirección
        dir_window = tk.Toplevel(self.top)
        dir_window.title(f"Direccion Completa - {nombre}")
        dir_window.geometry("500x200")
        
        info_text = f"""
        [DIRECCION] DEL PACIENTE
        
        Paciente: {nombre}
        ID: {self.paciente_seleccionado.get('id')}
        
        {'='*50}
        Direccion registrada:
        
        {direccion}
        {'='*50}
        """
        
        text_widget = tk.Text(dir_window, wrap=tk.WORD, font=('Courier', 11))
        text_widget.insert('1.0', info_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Button(dir_window, text="Cerrar", command=dir_window.destroy,
                 bg='#3498db', fg='white').pack(pady=10)
    
    def seleccionar_paciente(self):
        """Selecciona el paciente actual y cierra el diálogo"""
        if not self.paciente_seleccionado:
            messagebox.showwarning("Seleccion requerida", "Seleccione un paciente")
            return
        
        # Llamar al callback con el paciente seleccionado
        self.callback(self.paciente_seleccionado)
        self.top.destroy()