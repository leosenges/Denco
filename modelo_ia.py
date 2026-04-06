#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelo de IA — Cliente del Servicio REST en i7 (192.168.1.100)
CORRECCIONES v3.1:
  - Ya no calcula el riesgo localmente con if cluster==0/1/2 (era incorrecto).
  - Usa el campo 'riesgo' que ahora devuelve el servidor (continuo, semántico).
  - Usa el campo 'label' para mostrar NORMAL/SOSPECHOSO/ANOMALO.
  - Acepta respuesta antigua (sin 'riesgo') para compatibilidad hacia atrás.
"""
import logging
import requests
import json
import socket
import config

logger = logging.getLogger(__name__)


class ModeloIA:
    def __init__(self):
        self.api_url             = config.SERVIDOR_CONFIG['ia_api']['url']
        self.endpoint_prediccion = config.SERVIDOR_CONFIG['ia_api']['endpoint_prediccion']
        self.timeout             = config.SERVIDOR_CONFIG['ia_api']['timeout']
        self.entrenado           = False
        self._verificar_conexion()

    # ------------------------------------------------------------------
    # Conexión
    # ------------------------------------------------------------------

    def _verificar_conexion(self):
        """Verifica si el puerto 5000 del servidor está abierto."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('192.168.1.100', 5000))
            sock.close()
            if result == 0:
                self.entrenado = True
                logger.info("✅ Servidor IA accesible en 192.168.1.100:5000")
            else:
                logger.warning("⚠️  Puerto 5000 no accesible en 192.168.1.100")
                self.entrenado = False
        except Exception as e:
            logger.error(f"Error verificando servidor IA: {e}")
            self.entrenado = False

    def cargar(self):
        """Verifica la conexión (simula 'carga' del modelo remoto)."""
        self._verificar_conexion()
        return self.entrenado

    # ------------------------------------------------------------------
    # Predicción
    # ------------------------------------------------------------------

    def predecir(self, datos_muestra):
        """
        Envía los 7 features al servidor y devuelve (cluster, riesgo).

        Args:
            datos_muestra: lista/array de 7 valores en el orden:
                [tvoc_medio, eco2_medio, temp_media, hum_media,
                 flujo_medio_Lps, volumen_total_L, correlacion_voc_flujo]

        Returns:
            (cluster: int, riesgo: float[0-1])
            En caso de error devuelve (-1, 0.5).
        """
        if len(datos_muestra) != 7:
            logger.error(f"Se esperaban 7 features, recibí {len(datos_muestra)}")
            return -1, 0.5

        payload = {
            'tvoc_medio':            float(datos_muestra[0]),
            'eco2_medio':            float(datos_muestra[1]),
            'temp_media':            float(datos_muestra[2]),
            'hum_media':             float(datos_muestra[3]),
            'flujo_medio_Lps':       float(datos_muestra[4]),
            'volumen_total_L':       float(datos_muestra[5]),
            'correlacion_voc_flujo': float(datos_muestra[6])
        }

        try:
            url = f"{self.api_url}{self.endpoint_prediccion}"
            response = requests.post(url, json=payload, timeout=self.timeout)

            if response.status_code == 200:
                resultado = response.json()

                if resultado.get('status') == 'success':
                    cluster = int(resultado.get('resultado', -1))
                    label   = resultado.get('label', '?')

                    # ── CORRECCIÓN PRINCIPAL ──────────────────────────────────
                    # Usar el riesgo calculado por el servidor (semántico,
                    # basado en grupo_normal del metadata).
                    # Si el servidor es viejo y no devuelve 'riesgo', usamos
                    # una tabla de fallback basada en 'label'.
                    if 'riesgo' in resultado:
                        riesgo = float(resultado['riesgo'])
                    else:
                        # Compatibilidad con servidor_ia.py anterior (sin 'riesgo')
                        riesgo = {'NORMAL': 0.15, 'SOSPECHOSO': 0.55,
                                  'ANOMALO': 0.85}.get(label, 0.50)
                        logger.warning("Servidor antiguo detectado — riesgo estimado localmente")
                    # ─────────────────────────────────────────────────────────

                    logger.info(f"Predicción: cluster={cluster} ({label}) riesgo={riesgo:.3f}")
                    return cluster, riesgo

                else:
                    logger.error(f"Error del servidor: {resultado.get('error', '?')}")

            else:
                logger.error(f"HTTP {response.status_code} del servidor IA")

        except requests.exceptions.Timeout:
            logger.error(f"⏱️  Timeout ({self.timeout}s) al conectar con servidor IA")
        except requests.exceptions.ConnectionError:
            logger.error("🔌 Error de conexión con servidor IA en 192.168.1.100")
            self.entrenado = False
        except json.JSONDecodeError:
            logger.error("Error decodificando respuesta JSON")
        except Exception as e:
            logger.error(f"Error inesperado en predicción: {e}")

        return -1, 0.5

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    def obtener_info_modelo(self):
        """Obtiene metadata del modelo desde el endpoint /info del servidor."""
        if not self.entrenado:
            return {
                'entrenado': False,
                'conexion': 'offline',
                'mensaje': 'No hay conexión con el servidor IA'
            }
        try:
            response = requests.get(f"{self.api_url}/info", timeout=2)
            if response.status_code == 200:
                info = response.json()
                info['entrenado'] = True
                info['conexion']  = 'remota'
                return info
        except Exception as e:
            logger.debug(f"No se pudo obtener /info: {e}")

        return {
            'entrenado': True,
            'conexion': 'remota',
            'servidor': '192.168.1.100:5000',
            'modelo': 'KMeans (servidor v3.1)'
        }