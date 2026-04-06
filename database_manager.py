#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manejador de base de datos para DENCO v3.3 - Modo Servidor (PostgreSQL)
ACTUALIZADO v3.3: Campos de ubicación geográfica e institución, estadísticas geográficas
AGREGADO v3.3: Campo dirección para pacientes
"""
import logging
from datetime import datetime
import pandas as pd
import config

# Importar el driver de PostgreSQL
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def conectar(self):
        """Establece conexion con PostgreSQL en el servidor i7 (192.168.1.100)"""
        try:
            cfg = config.SERVIDOR_CONFIG['postgres']
            # Usar la IP CORRECTA del servidor
            host = '192.168.1.100'  # Forzar la IP correcta
            
            self.conn = psycopg2.connect(
                host=host,
                database=cfg['database'],
                user=cfg['user'],
                password=cfg['password'],
                port=cfg['port'],
                connect_timeout=5
            )
            # Usar RealDictCursor para obtener resultados como diccionarios
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            self._inicializar_tablas()
            logger.info(f"✅ Conectado a PostgreSQL en {host}:{cfg['port']}")
            return True
        except psycopg2.Error as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado conectando a PostgreSQL: {e}")
            return False

    def _inicializar_tablas(self):
        """Crea las tablas si no existen (sintaxis PostgreSQL)"""
        try:
            # Tabla pacientes - CON CAMPOS GEOGRÁFICOS Y DIRECCION
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS pacientes (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    edad INTEGER,
                    peso REAL,
                    contacto TEXT,
                    email TEXT,
                    direccion TEXT DEFAULT '',
                    observaciones TEXT,
                    fecha_registro TIMESTAMP,
                    activo INTEGER DEFAULT 1,
                    pais TEXT DEFAULT '',
                    departamento TEXT DEFAULT '',
                    ciudad TEXT DEFAULT '',
                    institucion TEXT DEFAULT ''
                )
            ''')
            
            # Verificar y agregar columnas si no existen (para migración)
            self._agregar_columnas_geograficas()
            self._agregar_columna_direccion()
            
            # Tabla sesiones
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sesiones (
                    id SERIAL PRIMARY KEY,
                    paciente_id INTEGER REFERENCES pacientes(id),
                    fecha TIMESTAMP,
                    tvoc_medio REAL,
                    eco2_medio REAL,
                    temp_media REAL,
                    hum_media REAL,
                    pres_media REAL,
                    flujo_medio_Lps REAL,
                    flujo_maximo_Lps REAL,
                    flujo_minimo_Lps REAL,
                    volumen_total_L REAL,
                    duracion_ms INTEGER,
                    correlacion_voc_flujo REAL,
                    pendiente_voc_flujo REAL,
                    cluster_asignado INTEGER,
                    riesgo REAL,
                    valida INTEGER DEFAULT 1,
                    notas TEXT,
                    notas_seguimiento TEXT
                )
            ''')
            
            # Tabla muestras
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS muestras (
                    id SERIAL PRIMARY KEY,
                    sesion_id INTEGER REFERENCES sesiones(id),
                    num_muestra INTEGER,
                    tvoc INTEGER,
                    eco2 INTEGER,
                    temp REAL,
                    hum REAL,
                    pres REAL,
                    flujo_Lps REAL,
                    volumen_parcial_L REAL,
                    deltaP_estimado REAL,
                    timestamp_ms INTEGER,
                    fraccion TEXT
                )
            ''')
            
            # Tabla evolucion (comparaciones)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS evolucion (
                    id SERIAL PRIMARY KEY,
                    paciente_id INTEGER REFERENCES pacientes(id),
                    sesion_base_id INTEGER REFERENCES sesiones(id),
                    sesion_comparacion_id INTEGER REFERENCES sesiones(id),
                    fecha_comparacion TIMESTAMP,
                    mejora_tvoc REAL,
                    mejora_eco2 REAL,
                    mejora_riesgo REAL,
                    comentarios TEXT
                )
            ''')
            
            # Tabla para estadísticas geográficas (cache)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS estadisticas_geograficas (
                    id SERIAL PRIMARY KEY,
                    pais TEXT,
                    departamento TEXT,
                    ciudad TEXT,
                    institucion TEXT,
                    fecha_analisis TIMESTAMP,
                    total_pacientes INTEGER,
                    total_sesiones INTEGER,
                    tvoc_promedio REAL,
                    eco2_promedio REAL,
                    riesgo_promedio REAL,
                    volumen_promedio REAL,
                    muestras_anormales INTEGER,
                    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla para alertas geográficas
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS alertas_geograficas (
                    id SERIAL PRIMARY KEY,
                    pais TEXT,
                    departamento TEXT,
                    ciudad TEXT,
                    institucion TEXT,
                    tipo_alerta TEXT,
                    descripcion TEXT,
                    valor REAL,
                    umbral REAL,
                    fecha_alerta TIMESTAMP,
                    resuelta INTEGER DEFAULT 0
                )
            ''')
            
            # Indices para mejorar velocidad
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_muestras_sesion ON muestras(sesion_id)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_sesiones_paciente ON sesiones(paciente_id)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_sesiones_fecha ON sesiones(fecha)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_pacientes_ubicacion ON pacientes(pais, departamento, ciudad)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_pacientes_institucion ON pacientes(institucion)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_sesiones_riesgo ON sesiones(riesgo)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_pacientes_direccion ON pacientes(direccion)')
            
            self.conn.commit()
            logger.info("Tablas inicializadas correctamente en PostgreSQL")
        except Exception as e:
            logger.error(f"Error inicializando tablas: {e}")
            self.conn.rollback()
    
    def _agregar_columnas_geograficas(self):
        """Agrega columnas geográficas si no existen (para migración)"""
        try:
            columnas = [
                ("pais", "TEXT DEFAULT ''"),
                ("departamento", "TEXT DEFAULT ''"),
                ("ciudad", "TEXT DEFAULT ''"),
                ("institucion", "TEXT DEFAULT ''")
            ]
            
            for col_name, col_def in columnas:
                try:
                    self.cursor.execute(f"""
                        ALTER TABLE pacientes 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_def}
                    """)
                    self.conn.commit()
                except Exception as e:
                    logger.debug(f"Columna {col_name} ya existe o error: {e}")
                    self.conn.rollback()
        except Exception as e:
            logger.error(f"Error agregando columnas geográficas: {e}")
    
    def _agregar_columna_direccion(self):
        """Agrega la columna dirección si no existe"""
        try:
            self.cursor.execute("""
                ALTER TABLE pacientes 
                ADD COLUMN IF NOT EXISTS direccion TEXT DEFAULT ''
            """)
            self.conn.commit()
            logger.info("✅ Columna 'direccion' agregada a la tabla pacientes")
        except Exception as e:
            logger.debug(f"Columna direccion ya existe o error: {e}")
            self.conn.rollback()

    # ----------------------------------------------
    # METODOS CRUD ACTUALIZADOS
    # ----------------------------------------------

    def registrar_paciente(self, nombre, edad, peso, contacto, email="", observaciones="",
                           pais="", departamento="", ciudad="", institucion="", direccion=""):
        """Registra un nuevo paciente en la base de datos con ubicación geográfica y dirección"""
        try:
            fecha = datetime.now().isoformat()
            self.cursor.execute('''
                INSERT INTO pacientes 
                (nombre, edad, peso, contacto, email, observaciones, fecha_registro,
                 pais, departamento, ciudad, institucion, direccion) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (nombre, edad, peso, contacto, email, observaciones, fecha,
                  pais, departamento, ciudad, institucion, direccion))
            result = self.cursor.fetchone()
            if result:
                paciente_id = result['id']
                self.conn.commit()
                logger.info(f"✅ Paciente registrado: {nombre} (ID: {paciente_id}) - {ciudad}, {departamento}")
                return paciente_id
            return None
        except Exception as e:
            logger.error(f"Error registrando paciente: {e}")
            self.conn.rollback()
            return None

    def buscar_pacientes(self, termino="", filtros=None):
        """Busca pacientes por ID, nombre, contacto, dirección o ubicación
        
        Args:
            termino: Término de búsqueda (nombre, ID, contacto, dirección)
            filtros: Diccionario con filtros geográficos opcionales
                    {'pais': str, 'departamento': str, 'ciudad': str, 'institucion': str}
        
        Returns:
            Lista de pacientes encontrados
        """
        try:
            # Construir consulta base
            query = """
                SELECT id, nombre, edad, peso, contacto, email, direccion, fecha_registro, activo,
                       pais, departamento, ciudad, institucion
                FROM pacientes 
                WHERE activo = 1
            """
            params = []
            
            # Búsqueda por término
            if termino and termino.strip():
                if termino.isdigit():
                    query += " AND (id = %s OR nombre ILIKE %s OR contacto ILIKE %s OR direccion ILIKE %s)"
                    params.extend([int(termino), f'%{termino}%', f'%{termino}%', f'%{termino}%'])
                else:
                    query += " AND (nombre ILIKE %s OR contacto ILIKE %s OR direccion ILIKE %s OR pais ILIKE %s OR departamento ILIKE %s OR ciudad ILIKE %s OR institucion ILIKE %s)"
                    params.extend([f'%{termino}%', f'%{termino}%', f'%{termino}%', f'%{termino}%', f'%{termino}%', f'%{termino}%', f'%{termino}%'])
            
            # Filtros geográficos opcionales
            if filtros:
                if filtros.get('pais'):
                    query += " AND pais ILIKE %s"
                    params.append(f"%{filtros['pais']}%")
                if filtros.get('departamento'):
                    query += " AND departamento ILIKE %s"
                    params.append(f"%{filtros['departamento']}%")
                if filtros.get('ciudad'):
                    query += " AND ciudad ILIKE %s"
                    params.append(f"%{filtros['ciudad']}%")
                if filtros.get('institucion'):
                    query += " AND institucion ILIKE %s"
                    params.append(f"%{filtros['institucion']}%")
            
            query += " ORDER BY nombre"
            
            self.cursor.execute(query, params)
            
            resultados = []
            for row in self.cursor.fetchall():
                paciente = dict(row)
                # Asegurar que fecha_registro sea string
                if paciente.get('fecha_registro') and not isinstance(paciente['fecha_registro'], str):
                    try:
                        paciente['fecha_registro'] = paciente['fecha_registro'].isoformat()
                    except:
                        pass
                resultados.append(paciente)
            
            return resultados
        except Exception as e:
            logger.error(f"Error buscando pacientes: {e}")
            return []
    
    def obtener_paciente_por_id(self, paciente_id):
        """Obtiene un paciente por su ID"""
        try:
            self.cursor.execute('''
                SELECT id, nombre, edad, peso, contacto, email, direccion, observaciones, fecha_registro,
                       pais, departamento, ciudad, institucion, activo
                FROM pacientes 
                WHERE id = %s
            ''', (paciente_id,))
            
            row = self.cursor.fetchone()
            if row:
                paciente = dict(row)
                if paciente.get('fecha_registro') and not isinstance(paciente['fecha_registro'], str):
                    try:
                        paciente['fecha_registro'] = paciente['fecha_registro'].isoformat()
                    except:
                        pass
                return paciente
            return None
        except Exception as e:
            logger.error(f"Error obteniendo paciente: {e}")
            return None
    
    def actualizar_paciente(self, paciente_id, nombre=None, edad=None, peso=None, 
                           contacto=None, email=None, observaciones=None,
                           pais=None, departamento=None, ciudad=None, institucion=None,
                           direccion=None):
        """Actualiza los datos de un paciente existente"""
        try:
            updates = []
            params = []
            
            if nombre is not None:
                updates.append("nombre = %s")
                params.append(nombre)
            if edad is not None:
                updates.append("edad = %s")
                params.append(edad)
            if peso is not None:
                updates.append("peso = %s")
                params.append(peso)
            if contacto is not None:
                updates.append("contacto = %s")
                params.append(contacto)
            if email is not None:
                updates.append("email = %s")
                params.append(email)
            if observaciones is not None:
                updates.append("observaciones = %s")
                params.append(observaciones)
            if pais is not None:
                updates.append("pais = %s")
                params.append(pais)
            if departamento is not None:
                updates.append("departamento = %s")
                params.append(departamento)
            if ciudad is not None:
                updates.append("ciudad = %s")
                params.append(ciudad)
            if institucion is not None:
                updates.append("institucion = %s")
                params.append(institucion)
            if direccion is not None:
                updates.append("direccion = %s")
                params.append(direccion)
            
            if not updates:
                return True
            
            params.append(paciente_id)
            query = f"UPDATE pacientes SET {', '.join(updates)} WHERE id = %s"
            
            self.cursor.execute(query, params)
            self.conn.commit()
            logger.info(f"✅ Paciente {paciente_id} actualizado")
            return True
        except Exception as e:
            logger.error(f"Error actualizando paciente: {e}")
            self.conn.rollback()
            return False
    
    def actualizar_ubicacion_paciente(self, paciente_id, pais="", departamento="", ciudad="", institucion=""):
        """Actualiza la ubicación de un paciente existente"""
        try:
            self.cursor.execute('''
                UPDATE pacientes 
                SET pais = %s, departamento = %s, ciudad = %s, institucion = %s
                WHERE id = %s
            ''', (pais, departamento, ciudad, institucion, paciente_id))
            self.conn.commit()
            logger.info(f"✅ Ubicación actualizada para paciente {paciente_id}")
            return True
        except Exception as e:
            logger.error(f"Error actualizando ubicación: {e}")
            self.conn.rollback()
            return False

    def crear_sesion(self, paciente_id):
        """Crea una nueva sesión para un paciente"""
        try:
            fecha = datetime.now().isoformat()
            self.cursor.execute('''
                INSERT INTO sesiones 
                (paciente_id, fecha, tvoc_medio, eco2_medio, temp_media, hum_media, 
                 pres_media, flujo_medio_Lps, flujo_maximo_Lps, flujo_minimo_Lps, 
                 volumen_total_L, duracion_ms, correlacion_voc_flujo, pendiente_voc_flujo, 
                 cluster_asignado, riesgo, valida, notas, notas_seguimiento) 
                VALUES (%s, %s, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 1, '', '')
                RETURNING id
            ''', (paciente_id, fecha))
            result = self.cursor.fetchone()
            if result:
                sesion_id = result['id']
                self.conn.commit()
                logger.info(f"✅ Sesión creada: {sesion_id} para paciente {paciente_id}")
                return sesion_id
            return None
        except Exception as e:
            logger.error(f"Error creando sesión: {e}")
            self.conn.rollback()
            return None

    def guardar_muestra(self, sesion_id, muestra):
        """Guarda una muestra individual en la base de datos"""
        try:
            self.cursor.execute('''
                INSERT INTO muestras 
                (sesion_id, num_muestra, tvoc, eco2, temp, hum, pres, flujo_Lps, 
                 volumen_parcial_L, deltaP_estimado, timestamp_ms, fraccion) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (sesion_id, 
                  muestra['num'], 
                  muestra['tvoc'], 
                  muestra['eco2'], 
                  muestra['temp'], 
                  muestra['hum'], 
                  muestra['pres'], 
                  muestra['flujo'], 
                  muestra['volumen'], 
                  muestra.get('deltaP', 0), 
                  muestra['timestamp'], 
                  muestra.get('fraccion', 'DESCONOCIDA')))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error guardando muestra: {e}")
            self.conn.rollback()

    def actualizar_sesion(self, sesion_id, resumen, volumen_total, duracion_ms,
                          flujo_max, flujo_min, correlacion, pendiente, cluster, riesgo):
        """Actualiza los datos de una sesión completada"""
        try:
            self.cursor.execute('''
                UPDATE sesiones SET 
                    tvoc_medio = %s, eco2_medio = %s, temp_media = %s, hum_media = %s, 
                    pres_media = %s, flujo_medio_Lps = %s, flujo_maximo_Lps = %s, 
                    flujo_minimo_Lps = %s, volumen_total_L = %s, duracion_ms = %s, 
                    correlacion_voc_flujo = %s, pendiente_voc_flujo = %s, 
                    cluster_asignado = %s, riesgo = %s 
                WHERE id = %s
            ''', (resumen['tvoc'], resumen['eco2'], resumen['temp'], resumen['hum'],
                  resumen['pres'], resumen['flujo_medio'], flujo_max, flujo_min,
                  volumen_total, duracion_ms, correlacion, pendiente, cluster, riesgo,
                  sesion_id))
            self.conn.commit()
            logger.info(f"✅ Sesion {sesion_id} actualizada")
        except Exception as e:
            logger.error(f"Error actualizando sesión: {e}")
            self.conn.rollback()

    # ----------------------------------------------
    # METODOS DE CONSULTA
    # ----------------------------------------------

    def obtener_historial_paciente(self, paciente_id):
        """Obtiene el historial de sesiones de un paciente"""
        try:
            self.cursor.execute('''
                SELECT 
                    id, fecha, tvoc_medio, eco2_medio, flujo_medio_Lps, 
                    volumen_total_L, riesgo, cluster_asignado, notas, notas_seguimiento
                FROM sesiones 
                WHERE paciente_id = %s AND valida = 1
                ORDER BY fecha ASC
            ''', (paciente_id,))
            
            sesiones = []
            rows = self.cursor.fetchall()
            
            for i, row in enumerate(rows, 1):
                # Convertir row a diccionario si no lo es
                if hasattr(row, 'keys'):
                    row_dict = dict(row)
                else:
                    row_dict = row
                
                # Procesar fecha
                fecha_val = row_dict.get('fecha')
                if fecha_val:
                    if isinstance(fecha_val, datetime):
                        fecha_formateada = fecha_val.strftime('%d/%m/%Y %H:%M')
                        fecha_iso = fecha_val.isoformat()
                    else:
                        fecha_formateada = str(fecha_val)
                        fecha_iso = str(fecha_val)
                else:
                    fecha_formateada = 'Desconocida'
                    fecha_iso = ''
                
                # Obtener valores con manejo seguro de None
                tvoc_medio = row_dict.get('tvoc_medio')
                if tvoc_medio is None:
                    tvoc_medio = 0
                
                eco2_medio = row_dict.get('eco2_medio')
                if eco2_medio is None:
                    eco2_medio = 0
                
                flujo_medio = row_dict.get('flujo_medio_Lps')
                if flujo_medio is None:
                    flujo_medio = 0
                
                volumen = row_dict.get('volumen_total_L')
                if volumen is None:
                    volumen = 0
                
                riesgo = row_dict.get('riesgo')
                if riesgo is None:
                    riesgo = 0
                
                cluster = row_dict.get('cluster_asignado')
                if cluster is None:
                    cluster = -1
                
                notas = row_dict.get('notas', '')
                if notas is None:
                    notas = ''
                
                notas_seguimiento = row_dict.get('notas_seguimiento', '')
                if notas_seguimiento is None:
                    notas_seguimiento = ''
                
                sesiones.append({
                    'num_sesion': i,
                    'id': row_dict.get('id'),
                    'fecha': fecha_formateada,
                    'fecha_iso': fecha_iso,
                    'tvoc_medio': float(tvoc_medio),
                    'eco2_medio': float(eco2_medio),
                    'flujo_medio': float(flujo_medio),
                    'volumen': float(volumen),
                    'riesgo': float(riesgo),
                    'cluster': int(cluster),
                    'notas': str(notas),
                    'notas_seguimiento': str(notas_seguimiento)
                })
            
            return sesiones
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def obtener_sesion_completa(self, sesion_id):
        """Obtiene todos los datos de una sesión incluyendo muestras"""
        try:
            self.cursor.execute('''
                SELECT s.*, p.nombre as paciente_nombre, p.edad, p.peso,
                       p.pais, p.departamento, p.ciudad, p.institucion, p.direccion
                FROM sesiones s
                JOIN pacientes p ON s.paciente_id = p.id
                WHERE s.id = %s
            ''', (sesion_id,))
            
            row = self.cursor.fetchone()
            if not row:
                return None
            
            # Convertir a diccionario
            if hasattr(row, 'keys'):
                sesion = dict(row)
            else:
                sesion = row
            
            self.cursor.execute('''
                SELECT * FROM muestras 
                WHERE sesion_id = %s 
                ORDER BY num_muestra ASC
            ''', (sesion_id,))
            
            muestras = []
            for m in self.cursor.fetchall():
                if hasattr(m, 'keys'):
                    muestras.append(dict(m))
                else:
                    muestras.append(m)
            
            sesion['muestras'] = muestras
            sesion['total_muestras'] = len(muestras)
            
            return sesion
        except Exception as e:
            logger.error(f"Error obteniendo sesión completa: {e}")
            return None

    def guardar_nota_seguimiento(self, sesion_id, nota):
        """Guarda una nota de seguimiento para una sesión"""
        try:
            self.cursor.execute('''
                UPDATE sesiones 
                SET notas_seguimiento = %s 
                WHERE id = %s
            ''', (nota, sesion_id))
            self.conn.commit()
            logger.info(f"📝 Nota de seguimiento guardada para sesión {sesion_id}")
        except Exception as e:
            logger.error(f"Error guardando nota: {e}")
            self.conn.rollback()

    def registrar_comparacion_evolucion(self, paciente_id, sesion_base_id, 
                                        sesion_comparacion_id, mejora_tvoc, 
                                        mejora_eco2, mejora_riesgo, comentarios=""):
        """Registra una comparación entre dos sesiones para análisis de evolución"""
        try:
            fecha = datetime.now().isoformat()
            self.cursor.execute('''
                INSERT INTO evolucion 
                (paciente_id, sesion_base_id, sesion_comparacion_id, 
                 fecha_comparacion, mejora_tvoc, mejora_eco2, mejora_riesgo, comentarios) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (paciente_id, sesion_base_id, sesion_comparacion_id, 
                  fecha, mejora_tvoc, mejora_eco2, mejora_riesgo, comentarios))
            result = self.cursor.fetchone()
            self.conn.commit()
            if result:
                return result['id']
            return None
        except Exception as e:
            logger.error(f"Error registrando comparación: {e}")
            self.conn.rollback()
            return None

    def obtener_sesiones_para_entrenamiento(self, min_sesiones=20):
        """Obtiene datos de sesiones válidas para entrenar el modelo IA"""
        try:
            self.cursor.execute('''
                SELECT tvoc_medio, eco2_medio, temp_media, hum_media, 
                       flujo_medio_Lps, volumen_total_L, correlacion_voc_flujo 
                FROM sesiones 
                WHERE valida = 1 AND tvoc_medio > 0 AND volumen_total_L > 0.1 
                ORDER BY fecha DESC
            ''')
            rows = self.cursor.fetchall()
            
            if len(rows) < min_sesiones:
                logger.warning(f"Datos insuficientes: {len(rows)}/{min_sesiones}")
                return None
            
            # Convertir a DataFrame
            datos = []
            for row in rows:
                if hasattr(row, 'keys'):
                    datos.append(dict(row))
                else:
                    datos.append(row)
            
            df = pd.DataFrame(datos)
            logger.info(f"Obtenidas {len(df)} sesiones para entrenamiento")
            return df
        except Exception as e:
            logger.error(f"Error obteniendo datos para entrenamiento: {e}")
            return None

    # ----------------------------------------------
    # METODOS DE ESTADÍSTICAS GEOGRÁFICAS
    # ----------------------------------------------

    def obtener_estadisticas_geograficas(self, pais="", departamento="", ciudad=""):
        """Obtiene estadísticas agrupadas por ubicación
        
        Args:
            pais: Filtrar por país
            departamento: Filtrar por departamento
            ciudad: Filtrar por ciudad
        
        Returns:
            Lista de diccionarios con estadísticas por ubicación
        """
        try:
            query = """
                SELECT 
                    COALESCE(p.pais, '') as pais,
                    COALESCE(p.departamento, '') as departamento,
                    COALESCE(p.ciudad, '') as ciudad,
                    COALESCE(p.institucion, '') as institucion,
                    COUNT(DISTINCT p.id) as total_pacientes,
                    COUNT(s.id) as total_sesiones,
                    AVG(s.tvoc_medio) as tvoc_promedio,
                    AVG(s.eco2_medio) as eco2_promedio,
                    AVG(s.riesgo) as riesgo_promedio,
                    AVG(s.volumen_total_L) as volumen_promedio,
                    SUM(CASE WHEN s.riesgo > 0.7 THEN 1 ELSE 0 END) as muestras_alto_riesgo,
                    MIN(s.tvoc_medio) as tvoc_min,
                    MAX(s.tvoc_medio) as tvoc_max,
                    STDDEV(s.tvoc_medio) as tvoc_desviacion
                FROM pacientes p
                LEFT JOIN sesiones s ON p.id = s.paciente_id AND s.valida = 1
                WHERE p.activo = 1
            """
            params = []
            
            if pais:
                query += " AND p.pais ILIKE %s"
                params.append(f"%{pais}%")
            if departamento:
                query += " AND p.departamento ILIKE %s"
                params.append(f"%{departamento}%")
            if ciudad:
                query += " AND p.ciudad ILIKE %s"
                params.append(f"%{ciudad}%")
            
            query += """ GROUP BY p.pais, p.departamento, p.ciudad, p.institucion 
                         ORDER BY p.pais, p.departamento, p.ciudad"""
            
            self.cursor.execute(query, params)
            resultados = []
            for row in self.cursor.fetchall():
                if hasattr(row, 'keys'):
                    resultados.append(dict(row))
                else:
                    resultados.append(row)
            
            return resultados
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas geográficas: {e}")
            return []
    
    def obtener_estadisticas_por_institucion(self, institucion=""):
        """Obtiene estadísticas agrupadas por institución"""
        try:
            query = """
                SELECT 
                    p.institucion,
                    COUNT(DISTINCT p.id) as total_pacientes,
                    COUNT(s.id) as total_sesiones,
                    AVG(s.tvoc_medio) as tvoc_promedio,
                    AVG(s.riesgo) as riesgo_promedio,
                    AVG(s.volumen_total_L) as volumen_promedio,
                    MIN(s.fecha) as primera_sesion,
                    MAX(s.fecha) as ultima_sesion
                FROM pacientes p
                LEFT JOIN sesiones s ON p.id = s.paciente_id AND s.valida = 1
                WHERE p.activo = 1 AND p.institucion != ''
            """
            params = []
            
            if institucion:
                query += " AND p.institucion ILIKE %s"
                params.append(f"%{institucion}%")
            
            query += " GROUP BY p.institucion ORDER BY total_sesiones DESC"
            
            self.cursor.execute(query, params)
            resultados = []
            for row in self.cursor.fetchall():
                if hasattr(row, 'keys'):
                    resultados.append(dict(row))
                else:
                    resultados.append(row)
            
            return resultados
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas por institución: {e}")
            return []
    
    def obtener_pacientes_por_ubicacion(self, pais="", departamento="", ciudad=""):
        """Obtiene lista de pacientes filtrados por ubicación"""
        try:
            query = """
                SELECT id, nombre, edad, contacto, email, direccion, fecha_registro,
                       pais, departamento, ciudad, institucion
                FROM pacientes 
                WHERE activo = 1
            """
            params = []
            
            if pais:
                query += " AND pais ILIKE %s"
                params.append(f"%{pais}%")
            if departamento:
                query += " AND departamento ILIKE %s"
                params.append(f"%{departamento}%")
            if ciudad:
                query += " AND ciudad ILIKE %s"
                params.append(f"%{ciudad}%")
            
            query += " ORDER BY nombre"
            
            self.cursor.execute(query, params)
            resultados = []
            for row in self.cursor.fetchall():
                if hasattr(row, 'keys'):
                    resultados.append(dict(row))
                else:
                    resultados.append(row)
            
            return resultados
        except Exception as e:
            logger.error(f"Error obteniendo pacientes por ubicación: {e}")
            return []
    
    def obtener_alertas_geograficas(self, resuelta=False):
        """Obtiene las alertas geográficas registradas"""
        try:
            query = """
                SELECT * FROM alertas_geograficas 
                WHERE resuelta = %s
                ORDER BY fecha_alerta DESC
            """
            self.cursor.execute(query, (1 if resuelta else 0,))
            resultados = []
            for row in self.cursor.fetchall():
                if hasattr(row, 'keys'):
                    resultados.append(dict(row))
                else:
                    resultados.append(row)
            return resultados
        except Exception as e:
            logger.error(f"Error obteniendo alertas geográficas: {e}")
            return []
    
    def registrar_alerta_geografica(self, pais, departamento, ciudad, institucion,
                                     tipo_alerta, descripcion, valor, umbral):
        """Registra una alerta geográfica"""
        try:
            fecha = datetime.now().isoformat()
            self.cursor.execute('''
                INSERT INTO alertas_geograficas 
                (pais, departamento, ciudad, institucion, tipo_alerta, descripcion, 
                 valor, umbral, fecha_alerta, resuelta) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
            ''', (pais, departamento, ciudad, institucion, tipo_alerta, 
                  descripcion, valor, umbral, fecha))
            self.conn.commit()
            logger.info(f"⚠️ Alerta geográfica registrada: {tipo_alerta} en {ciudad}")
            return True
        except Exception as e:
            logger.error(f"Error registrando alerta geográfica: {e}")
            self.conn.rollback()
            return False
    
    def resolver_alerta_geografica(self, alerta_id):
        """Marca una alerta como resuelta"""
        try:
            self.cursor.execute('''
                UPDATE alertas_geograficas 
                SET resuelta = 1 
                WHERE id = %s
            ''', (alerta_id,))
            self.conn.commit()
            logger.info(f"✅ Alerta {alerta_id} resuelta")
            return True
        except Exception as e:
            logger.error(f"Error resolviendo alerta: {e}")
            self.conn.rollback()
            return False
    
    def actualizar_cache_estadisticas(self):
        """Actualiza la tabla de caché de estadísticas geográficas"""
        try:
            stats = self.obtener_estadisticas_geograficas()
            fecha = datetime.now().isoformat()
            
            # Limpiar caché anterior
            self.cursor.execute("DELETE FROM estadisticas_geograficas")
            
            # Insertar nuevos datos
            for stat in stats:
                self.cursor.execute('''
                    INSERT INTO estadisticas_geograficas 
                    (pais, departamento, ciudad, institucion, fecha_analisis,
                     total_pacientes, total_sesiones, tvoc_promedio, eco2_promedio,
                     riesgo_promedio, volumen_promedio, muestras_anormales)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    stat.get('pais', ''),
                    stat.get('departamento', ''),
                    stat.get('ciudad', ''),
                    stat.get('institucion', ''),
                    fecha,
                    stat.get('total_pacientes', 0),
                    stat.get('total_sesiones', 0),
                    stat.get('tvoc_promedio', 0),
                    stat.get('eco2_promedio', 0),
                    stat.get('riesgo_promedio', 0),
                    stat.get('volumen_promedio', 0),
                    stat.get('muestras_alto_riesgo', 0)
                ))
            
            self.conn.commit()
            logger.info(f"✅ Caché de estadísticas actualizado con {len(stats)} registros")
            return True
        except Exception as e:
            logger.error(f"Error actualizando caché de estadísticas: {e}")
            self.conn.rollback()
            return False
    
    def obtener_mapas_calor_geograficos(self):
        """Obtiene datos para generar mapas de calor de riesgo por ubicación"""
        try:
            query = """
                SELECT 
                    pais,
                    departamento,
                    ciudad,
                    COUNT(s.id) as total_sesiones,
                    AVG(s.riesgo) as riesgo_promedio,
                    AVG(s.tvoc_medio) as tvoc_promedio,
                    STDDEV(s.riesgo) as riesgo_desviacion
                FROM pacientes p
                JOIN sesiones s ON p.id = s.paciente_id AND s.valida = 1
                WHERE p.activo = 1 AND p.ciudad != ''
                GROUP BY pais, departamento, ciudad
                HAVING COUNT(s.id) >= 3
                ORDER BY riesgo_promedio DESC
            """
            self.cursor.execute(query)
            resultados = []
            for row in self.cursor.fetchall():
                if hasattr(row, 'keys'):
                    resultados.append(dict(row))
                else:
                    resultados.append(row)
            return resultados
        except Exception as e:
            logger.error(f"Error obteniendo datos para mapas de calor: {e}")
            return []
    
    # ----------------------------------------------
    # METODOS DE REPORTES Y EXPORTACIÓN
    # ----------------------------------------------
    
    def exportar_datos_ubicacion_csv(self, filepath):
        """Exporta todos los datos de ubicación a CSV"""
        import csv
        
        try:
            pacientes = self.buscar_pacientes()
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ID', 'Nombre', 'Edad', 'País', 'Departamento', 
                               'Ciudad', 'Institución', 'Direccion', 'Contacto', 'Email', 'Fecha Registro'])
                
                for p in pacientes:
                    writer.writerow([
                        p.get('id', ''),
                        p.get('nombre', ''),
                        p.get('edad', ''),
                        p.get('pais', ''),
                        p.get('departamento', ''),
                        p.get('ciudad', ''),
                        p.get('institucion', ''),
                        p.get('direccion', ''),
                        p.get('contacto', ''),
                        p.get('email', ''),
                        p.get('fecha_registro', '')
                    ])
            
            logger.info(f"✅ Datos de ubicación exportados a {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exportando datos de ubicación: {e}")
            return False
    
    def obtener_resumen_geografico(self):
        """Obtiene un resumen general de la distribución geográfica"""
        try:
            query = """
                SELECT 
                    COUNT(DISTINCT pais) as total_paises,
                    COUNT(DISTINCT departamento) as total_departamentos,
                    COUNT(DISTINCT ciudad) as total_ciudades,
                    COUNT(DISTINCT institucion) as total_instituciones,
                    COUNT(*) as total_pacientes,
                    SUM(CASE WHEN pais = '' THEN 1 ELSE 0 END) as pacientes_sin_ubicacion,
                    SUM(CASE WHEN direccion = '' THEN 1 ELSE 0 END) as pacientes_sin_direccion
                FROM pacientes
                WHERE activo = 1
            """
            self.cursor.execute(query)
            row = self.cursor.fetchone()
            if hasattr(row, 'keys'):
                return dict(row)
            return row
        except Exception as e:
            logger.error(f"Error obteniendo resumen geográfico: {e}")
            return {}
    
    # ----------------------------------------------
    # METODOS DE MANTENIMIENTO
    # ----------------------------------------------
    
    def cerrar(self):
        """Cierra la conexión a la base de datos"""
        try:
            if self.conn:
                self.conn.close()
                logger.info("Conexion a BD cerrada")
        except Exception as e:
            logger.error(f"Error cerrando conexión: {e}")