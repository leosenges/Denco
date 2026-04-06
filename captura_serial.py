#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manejo de comunicacion serial con Arduino y captura de muestras
Incluye modo simulacion para pruebas sin hardware
CORREGIDO v3.4: 
  - Clasificacion ESPACIO_MUERTO/ALVEOLAR basada en VOLUMEN (ISO 13138)
  - Agregado metodo reset() para limpiar estado entre capturas
  - Validacion menos estricta para sesiones reales
  - Mejor manejo de errores y timeouts
"""
import serial
import serial.tools.list_ports
import time
import logging
import numpy as np
import config
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)

class SerialManager:
    def __init__(self):
        self.ser = None
        self.config = config.SERIAL_CONFIG
        self.timeout = self.config['timeout']
        self._reset_sim_state()

    def _reset_sim_state(self):
        """Resetea el estado interno de simulacion"""
        self._sim_state = 'idle'
        self._sim_start = 0
        self._sim_muestras = 0
        self._sim_volumen_acumulado = 0.0
        self._sim_muestras_list = []

    def reset(self):
        """
        Resetea completamente el SerialManager para una nueva sesion.
        Limpia buffers y estado interno.
        LLAMAR ANTES DE CADA NUEVA CAPTURA.
        """
        logger.info("Reseteando SerialManager para nueva captura")
        
        # Resetear estado de simulacion
        self._reset_sim_state()
        
        # Limpiar buffer serial real si esta conectado
        if not config.MODO_SIMULACION and self.ser and self.ser.is_open:
            self.limpiar_buffer()
            logger.debug("Buffer serial real limpiado")
        
        # Pequena pausa para estabilizar
        time.sleep(0.1)

    def conectar(self):
        """Establece conexion con el puerto serial"""
        # Si estamos en modo simulacion, no intentar conexion real
        if config.MODO_SIMULACION:
            logger.info("MODO SIMULACION: No se requiere conexion serial")
            return True
            
        try:
            self.ser = serial.Serial(
                port=self.config['puerto'],
                baudrate=self.config['baud_rate'],
                timeout=self.config['timeout'],
                parity=getattr(serial, f"PARITY_{self.config['parity']}"),
                stopbits=self.config['stopbits'],
                bytesize=self.config['bytesize']
            )
            time.sleep(2)
            logger.info(f"Conectado a {self.config['puerto']} @ {self.config['baud_rate']} baud")
            self.ser.reset_input_buffer()
            return True
        except serial.SerialException as e:
            logger.error(f"Error conectando al puerto {self.config['puerto']}: {e}")
            self._listar_puertos_disponibles()
            return False
        except Exception as e:
            logger.error(f"Error inesperado en conexion serial: {e}")
            return False

    def _listar_puertos_disponibles(self):
        """Lista los puertos serial disponibles"""
        try:
            puertos = serial.tools.list_ports.comports()
            if puertos:
                logger.info("Puertos disponibles:")
                for port in puertos:
                    logger.info(f"  - {port.device}: {port.description}")
            else:
                logger.warning("No se encontraron puertos serial disponibles")
        except Exception as e:
            logger.error(f"Error listando puertos: {e}")

    def leer_linea(self) -> Optional[str]:
        """Lee una linea del puerto serial"""
        # Modo simulacion: generar datos ficticios
        if config.MODO_SIMULACION:
            return self._generar_datos_simulados()
            
        try:
            if self.ser and self.ser.in_waiting > 0:
                linea_bytes = self.ser.readline()
                if linea_bytes:
                    linea = linea_bytes.decode('utf-8').strip()
                    # Debug opcional (comentar en produccion)
                    # print(f"[SERIAL] {linea[:80]}")
                    return linea
            return None
        except UnicodeDecodeError as e:
            logger.error(f"Error decodificando datos: {e}")
            return None
        except serial.SerialException as e:
            logger.error(f"Error de puerto serial: {e}")
            return None
        except Exception as e:
            logger.error(f"Error leyendo del puerto serial: {e}")
            return None

    def _generar_datos_simulados(self):
        """Genera datos simulados para pruebas sin hardware - CON CLASIFICACION POR VOLUMEN"""
        import random
        
        # Asegurar que la lista existe
        if not hasattr(self, '_sim_muestras_list'):
            self._sim_muestras_list = []
        
        # Obtener volumen muerto de configuracion
        volumen_muerto_L = config.ISO_CONFIG.get('volumen_muerto_L', 0.237)
        
        # Cambiar estados aleatoriamente para simular una sesion
        if self._sim_state == 'idle' and random.random() < 0.01:  # 1% chance de iniciar
            self._sim_state = 'inicio'
            self._sim_start = time.time()
            self._sim_muestras = 0
            self._sim_volumen_acumulado = 0.0
            self._sim_muestras_list = []
            logger.info("SIMULACION: Iniciando exhalacion")
            return "INICIO_EXHALACION,12345"
        
        elif self._sim_state == 'inicio':
            self._sim_muestras += 1
            tiempo_rel = (time.time() - self._sim_start) * 1000  # ms
            
            # Simular curva de exhalacion realista
            progreso = min(1.0, self._sim_muestras / 60)
            
            # Flujo: curva que sube y baja (parabolica)
            flujo = 4.0 * np.sin(np.pi * progreso) + random.gauss(0, 0.1)
            flujo = max(0.1, flujo)
            
            # Volumen acumulado - integracion
            dt = 0.1
            delta_volumen = flujo * dt
            self._sim_volumen_acumulado += delta_volumen
            
            # TVOC: aumenta durante la exhalacion
            tvoc_base = 400 + 300 * progreso
            tvoc = int(tvoc_base + random.gauss(0, 20))
            
            # eCO2: similar
            eco2 = int(800 + 400 * progreso + random.gauss(0, 30))
            
            # Temperatura y humedad
            temp = 34.0 + 1.5 * progreso + random.gauss(0, 0.1)
            hum = 85.0 + 5.0 * progreso + random.gauss(0, 1)
            pres = 1013.0 + random.gauss(0, 1)
            
            # ⭐ CLASIFICACION CORRECTA: Basada en VOLUMEN (ISO 13138)
            if self._sim_volumen_acumulado < volumen_muerto_L:
                fraccion = "ESPACIO_MUERTO"
            else:
                fraccion = "ALVEOLAR"
            
            deltaP = 100 + 200 * np.sin(np.pi * progreso) + random.gauss(0, 10)
            
            muestra_info = {'num': self._sim_muestras, 'fraccion': fraccion, 
                           'volumen': self._sim_volumen_acumulado}
            self._sim_muestras_list.append(muestra_info)
            
            muestra = f"MUESTRA,{self._sim_muestras},{tvoc},{eco2},{temp:.1f},{hum:.1f},{pres:.1f},{flujo:.3f},{self._sim_volumen_acumulado:.3f},{deltaP:.0f},{fraccion},{int(tiempo_rel)}"
            
            # Finalizar despues de suficientes muestras
            if self._sim_muestras >= 60 or self._sim_volumen_acumulado >= 5.0:
                self._sim_state = 'fin'
                muestras_muerto = [m for m in self._sim_muestras_list if m.get('fraccion') == 'ESPACIO_MUERTO']
                logger.info(f"SIMULACION: Completada - {self._sim_muestras} muestras, "
                           f"{len(muestras_muerto)} espacio muerto, "
                           f"{self._sim_muestras - len(muestras_muerto)} alveolar")
                return muestra + "\n" + f"FIN_EXHALACION,{self._sim_volumen_acumulado:.3f}"
            
            return muestra
        
        elif self._sim_state == 'fin':
            if random.random() < 0.1:
                self._sim_state = 'idle'
                self._sim_muestras_list = []
            return None
        
        return None

    def limpiar_buffer(self):
        """Limpia el buffer de entrada"""
        if config.MODO_SIMULACION:
            return
        if self.ser:
            self.ser.reset_input_buffer()
            logger.debug("Buffer serial limpiado")

    def cerrar(self):
        """Cierra la conexion serial"""
        if config.MODO_SIMULACION:
            logger.info("MODO SIMULACION: Conexion cerrada (simulada)")
            return
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.info("Conexion serial cerrada")


class DataValidator:
    @staticmethod
    def validar_muestra(muestra: Dict) -> Tuple[bool, str]:
        """Valida que una muestra este dentro de rangos aceptables"""
        rangos = config.VALIDACION_CONFIG['rangos']
        
        # TVOC puede ser 0 al inicio (sensor estabilizandose)
        if muestra['tvoc'] < rangos['tvoc']['min'] or muestra['tvoc'] > rangos['tvoc']['max']:
            if muestra['tvoc'] == 0:
                logger.debug(f"TVOC=0 (normal al inicio)")
            else:
                return False, f"TVOC fuera de rango: {muestra['tvoc']}"
        
        if muestra['eco2'] < rangos['eco2']['min'] or muestra['eco2'] > rangos['eco2']['max']:
            return False, f"eCO2 fuera de rango: {muestra['eco2']}"
        
        if muestra['temp'] < rangos['temp']['min'] or muestra['temp'] > rangos['temp']['max']:
            if rangos['temp']['critico']:
                return False, f"Temperatura critica fuera de rango: {muestra['temp']}°C"
            else:
                logger.warning(f"Temperatura fuera de rango: {muestra['temp']}°C")
        
        if muestra['hum'] < rangos['hum']['min'] or muestra['hum'] > rangos['hum']['max']:
            return False, f"Humedad fuera de rango: {muestra['hum']}%"
        
        if muestra['flujo'] < rangos['flujo']['min'] or muestra['flujo'] > rangos['flujo']['max']:
            logger.warning(f"Flujo fuera de rango: {muestra['flujo']} L/s")
        
        return True, "OK"

    @staticmethod
    def validar_sesion(muestras: List[Dict], volumen_total: float) -> Tuple[bool, str]:
        """
        Valida que una sesion completa sea valida.
        VERSION CORREGIDA: Menos estricta para capturas reales.
        """
        # Reducido de 5 a 3 muestras minimas
        if len(muestras) < 3:
            return False, f"Muestras insuficientes: {len(muestras)}"
        
        # Reducido de 0.1 a 0.05 L
        if volumen_total < 0.05:
            return False, f"Volumen insuficiente: {volumen_total:.3f} L"
        
        # Validacion ISO 13138: Verificar espacio muerto (solo informativo)
        volumen_muerto_L = config.ISO_CONFIG.get('volumen_muerto_L', 0.237)
        
        # Contar muestras de espacio muerto
        muestras_muerto = [m for m in muestras if m.get('fraccion', '') == 'ESPACIO_MUERTO']
        
        if muestras_muerto:
            volumen_muerto_real = muestras_muerto[-1].get('volumen', 0)
            logger.info(f"📊 Espacio muerto: {len(muestras_muerto)} muestras, "
                       f"volumen: {volumen_muerto_real:.3f} L (ideal: {volumen_muerto_L:.3f} L)")
        else:
            logger.warning(f"⚠️ No se detectaron muestras de espacio muerto")
        
        # Verificar variacion en TVOC (solo advertencia, no error)
        tvocs = [m['tvoc'] for m in muestras if m['tvoc'] > 0]
        if tvocs and (max(tvocs) - min(tvocs)) < 5:
            logger.warning(f"⚠️ Poca variacion en TVOC: min={min(tvocs)}, max={max(tvocs)}")
        
        logger.info(f"✅ Sesion valida: {len(muestras)} muestras, {volumen_total:.3f} L")
        return True, "OK"


def calcular_emisiones_iso16000(muestras, volumen_total_L, duracion_s):
    """
    Calcula la tasa de emision y concentracion de VOC segun principios de ISO 16000-9.
    Usa solo muestras alveolares para mayor precision.
    """
    if not muestras or duracion_s <= 0:
        return {
            'concentracion_ug_m3': 0,
            'tasa_emision_ug_min': 0,
            'masa_total_ug': 0,
            'tasa_emision_ng_s': 0,
            'masa_total_ng': 0,
            'tvoc_medio_ppb': 0
        }

    # Usar solo muestras alveolares (ISO 13138)
    muestras_alveolares = [m for m in muestras if m.get('fraccion', '') == 'ALVEOLAR']
    
    # Si no hay muestras alveolares, usar todas (ej: sesion muy corta)
    if not muestras_alveolares:
        logger.warning("No se detectaron muestras alveolares, usando todas las muestras")
        muestras_alveolares = muestras
    
    # Filtrar TVOC=0 (sensor estabilizandose)
    tvocs_validos = [m['tvoc'] for m in muestras_alveolares if m['tvoc'] > 0]
    
    if not tvocs_validos:
        logger.warning("No hay valores de TVOC validos")
        tvoc_medio_ppb = 0
    else:
        tvoc_medio_ppb = np.mean(tvocs_validos)
    
    logger.info(f"📊 Analisis ISO: {len(muestras_alveolares)} muestras alveolares, "
                f"TVOC medio={tvoc_medio_ppb:.0f} ppb")

    MASA_MOLAR_VOC = config.ISO_CONFIG['masa_molar_voc_g_mol']
    VOLUMEN_MOLAR_L_mol = config.ISO_CONFIG['volumen_molar_L_mol']

    # Concentracion masica en µg/m³
    concentracion_ug_m3 = (tvoc_medio_ppb * MASA_MOLAR_VOC) / VOLUMEN_MOLAR_L_mol 

    # Tasa de emision en µg/min
    flujos_validos = [m['flujo'] for m in muestras_alveolares if m['flujo'] > 0]
    if flujos_validos:
        flujo_medio_Lps = np.mean(flujos_validos)
    else:
        flujo_medio_Lps = 0.5  # valor por defecto
    
    flujo_medio_m3s = flujo_medio_Lps / 1000.0
    tasa_emision_ug_min = concentracion_ug_m3 * flujo_medio_m3s * 60.0

    # Masa total emitida en µg
    masa_total_ug = tasa_emision_ug_min * (duracion_s / 60.0)

    # Unidades tradicionales
    tasa_emision_ng_s = tasa_emision_ug_min * 1000.0 / 60.0
    masa_total_ng = masa_total_ug * 1000.0

    return {
        'concentracion_ug_m3': concentracion_ug_m3,
        'tasa_emision_ug_min': tasa_emision_ug_min,
        'masa_total_ug': masa_total_ug,
        'tasa_emision_ng_s': tasa_emision_ng_s,
        'masa_total_ng': masa_total_ng,
        'tvoc_medio_ppb': tvoc_medio_ppb
    }


def capturar_muestras_serial(serial_mgr: SerialManager, duracion_max=35):
    """
    Captura las muestras del formato enriquecido del Arduino v2.3
    Con clasificacion correcta ISO 13138 basada en volumen.
    """
    muestras = []
    volumen_total = 0
    timestamp_inicio = 0
    sesion_activa = False
    errores_consecutivos = 0
    
    logger.info("Esperando inicio de exhalacion...")
    
    inicio_global = time.time()
    while time.time() - inicio_global < duracion_max:
        try:
            linea = serial_mgr.leer_linea()
            if not linea:
                time.sleep(0.01)
                continue
            
            errores_consecutivos = 0
            
            if 'INICIO_EXHALACION' in linea:
                sesion_activa = True
                muestras = []
                partes = linea.split(',')
                timestamp_inicio = float(partes[1]) if len(partes) >= 2 else time.time()*1000
                logger.info("✅ Exhalacion detectada! Capturando...")
                
            elif 'MUESTRA' in linea and sesion_activa:
                partes = linea.split(',')
                # Formato: MUESTRA,num,tvoc,eco2,temp,hum,pres,flujo,volumen,deltaP,FRACCION,timestamp
                if len(partes) >= 12:
                    try:
                        fraccion_recibida = partes[10]
                        
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
                            'fraccion': fraccion_recibida,
                            'timestamp': int(partes[11])
                        }
                        
                        valida, msg = DataValidator.validar_muestra(muestra)
                        if not valida:
                            logger.warning(f"Muestra invalida: {msg}")
                            continue
                        
                        muestras.append(muestra)
                        
                        # Log cada 10 muestras para no saturar
                        if len(muestras) % 10 == 0:
                            logger.debug(f"Muestra {muestra['num']}: TVOC={muestra['tvoc']}, "
                                       f"Flujo={muestra['flujo']:.2f} L/s, {muestra['fraccion']}")
                        
                    except (ValueError, IndexError) as e:
                        logger.error(f"Error parseando muestra: {e} - Linea: {linea[:50]}")
                        continue
                        
            elif 'FIN_EXHALACION' in linea and sesion_activa:
                partes = linea.split(',')
                if len(partes) >= 2:
                    try:
                        volumen_total = float(partes[1])
                    except:
                        if muestras:
                            volumen_total = muestras[-1]['volumen']
                
                # Estadisticas de la sesion
                muestras_muerto = [m for m in muestras if m.get('fraccion') == 'ESPACIO_MUERTO']
                muestras_alveolares = [m for m in muestras if m.get('fraccion') == 'ALVEOLAR']
                
                logger.info(f"✅ Exhalacion completada:")
                logger.info(f"   📊 Total: {len(muestras)} muestras")
                logger.info(f"   💨 Espacio muerto: {len(muestras_muerto)} muestras, "
                           f"volumen: {muestras_muerto[-1]['volumen'] if muestras_muerto else 0:.3f} L")
                logger.info(f"   🫁 Alveolar: {len(muestras_alveolares)} muestras, "
                           f"volumen: {volumen_total - (muestras_muerto[-1]['volumen'] if muestras_muerto else 0):.3f} L")
                
                # Validar sesion
                valida, msg = DataValidator.validar_sesion(muestras, volumen_total)
                if not valida:
                    logger.warning(f"⚠️ Sesion invalida: {msg}")
                else:
                    logger.info(f"✅ Sesion valida: {msg}")
                
                return muestras, volumen_total
                    
        except Exception as e:
            errores_consecutivos += 1
            logger.error(f"Error en captura ({errores_consecutivos}): {e}")
            if errores_consecutivos > 10:
                logger.critical("Demasiados errores consecutivos, abortando captura")
                break
    
    if sesion_activa and muestras:
        logger.warning(f"⚠️ Captura terminada por timeout, {len(muestras)} muestras recuperadas")
        return muestras, volumen_total
    
    logger.warning("No se detecto exhalacion")
    return muestras, volumen_total