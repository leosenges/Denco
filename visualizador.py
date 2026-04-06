#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funciones de visualizacion y generacion de graficos
"""
import io
import numpy as np
import matplotlib.pyplot as plt
import config

class Visualizador:
    @staticmethod
    def curva_completa(muestras, volumen_total):
        """Genera grafico de 4 paneles con la evolucion de la exhalacion"""
        if len(muestras) == 0:
            return None
        
        nums = [m['num'] for m in muestras]
        tvocs = [m['tvoc'] for m in muestras]
        eco2s = [m['eco2'] for m in muestras]
        flujos = [m['flujo'] for m in muestras]
        volumenes = [m['volumen'] for m in muestras]
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # TVOC
        axes[0,0].plot(nums, tvocs, color='blue', linewidth=1.5)
        axes[0,0].set_title(f'TVOC (ppb) - Pico: {max(tvocs)} | Medio: {np.mean(tvocs):.0f}')
        axes[0,0].set_xlabel('Muestra (10 Hz)')
        axes[0,0].grid(True, alpha=0.3)
        axes[0,0].axhline(y=np.mean(tvocs), color='blue', linestyle='--', alpha=0.5)
        
        # eCO2
        axes[0,1].plot(nums, eco2s, color='red', linewidth=1.5)
        axes[0,1].set_title(f'eCO2 (ppm) - Pico: {max(eco2s)} | Medio: {np.mean(eco2s):.0f}')
        axes[0,1].set_xlabel('Muestra (10 Hz)')
        axes[0,1].grid(True, alpha=0.3)
        axes[0,1].axhline(y=np.mean(eco2s), color='red', linestyle='--', alpha=0.5)
        
        # Flujo
        axes[1,0].plot(nums, flujos, color='green', linewidth=1.5)
        axes[1,0].set_title(f'Flujo (L/s) - Pico: {max(flujos):.2f} | Medio: {np.mean(flujos):.2f}')
        axes[1,0].set_xlabel('Muestra (10 Hz)')
        axes[1,0].set_ylabel('L/s')
        axes[1,0].grid(True, alpha=0.3)
        axes[1,0].fill_between(nums, 0, flujos, alpha=0.2, color='green')
        
        # Volumen
        axes[1,1].plot(nums, volumenes, color='purple', linewidth=2)
        axes[1,1].set_title(f'Volumen Acumulado - Total: {volumen_total:.3f} L')
        axes[1,1].set_xlabel('Muestra (10 Hz)')
        axes[1,1].set_ylabel('Litros')
        axes[1,1].grid(True, alpha=0.3)
        axes[1,1].fill_between(nums, 0, volumenes, alpha=0.2, color='purple')
        
        plt.tight_layout()
        
        # Guardar en buffer
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format='PNG', dpi=config.PDF_CONFIG['dpi_graficos'])
        img_buf.seek(0)
        plt.close(fig)
        
        return img_buf

    @staticmethod
    def correlacion_voc_flujo(muestras):
        """Genera grafico de correlacion entre VOC y flujo"""
        if len(muestras) < 10:
            return None, 0, 0
        
        tvocs = [m['tvoc'] for m in muestras]
        flujos = [m['flujo'] for m in muestras]
        nums = [m['num'] for m in muestras]
        
        # Calcular correlacion
        correlacion = np.corrcoef(tvocs, flujos)[0, 1]
        
        # Regresion lineal
        z = np.polyfit(flujos, tvocs, 1)
        pendiente = z[0]
        interseccion = z[1]
        
        flujo_linea = np.linspace(min(flujos), max(flujos), 50)
        tvoc_tendencia = pendiente * flujo_linea + interseccion
        
        # Crear figura
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Scatter plot
        scatter = axes[0].scatter(flujos, tvocs, c=nums, cmap='viridis', alpha=0.7, s=30)
        axes[0].plot(flujo_linea, tvoc_tendencia, 'r--', linewidth=2, 
                    label=f'Pendiente={pendiente:.2f}')
        axes[0].set_xlabel('Flujo Volumetrico (L/s)')
        axes[0].set_ylabel('TVOC (ppb)')
        axes[0].set_title(f'Correlacion VOC vs Flujo\nr = {correlacion:.3f}')
        axes[0].grid(True, alpha=0.3)
        axes[0].legend()
        axes[0].axhline(y=np.mean(tvocs), color='gray', linestyle=':', alpha=0.5)
        axes[0].axvline(x=np.mean(flujos), color='gray', linestyle=':', alpha=0.5)
        
        cbar = plt.colorbar(scatter, ax=axes[0])
        cbar.set_label('N° de Muestra (tiempo)')
        
        # Correlacion movil
        ventana = min(20, len(muestras)//5)
        correlaciones_moviles = []
        tiempos = []
        
        for i in range(len(muestras) - ventana):
            tvoc_ventana = tvocs[i:i+ventana]
            flujo_ventana = flujos[i:i+ventana]
            if np.std(tvoc_ventana) > 0 and np.std(flujo_ventana) > 0:
                r = np.corrcoef(tvoc_ventana, flujo_ventana)[0, 1]
                correlaciones_moviles.append(r)
                tiempos.append(nums[i+ventana//2])
        
        if correlaciones_moviles:
            axes[1].plot(tiempos, correlaciones_moviles, 'b-', linewidth=2)
            axes[1].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            axes[1].set_xlabel('N° de Muestra (tiempo)')
            axes[1].set_ylabel('Correlacion movil (r)')
            axes[1].set_title(f'Correlacion Movil (ventana={ventana})')
            axes[1].grid(True, alpha=0.3)
            axes[1].set_ylim(-1, 1)
        
        plt.tight_layout()
        
        # Guardar en buffer
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format='PNG', dpi=config.PDF_CONFIG['dpi_graficos'])
        img_buf.seek(0)
        plt.close(fig)
        
        return img_buf, correlacion, pendiente

    @staticmethod
    def calcular_correlacion(muestras):
        """Calcula solo la correlacion sin generar grafico"""
        if len(muestras) < 5:
            return 0, 0
        tvocs = [m['tvoc'] for m in muestras]
        flujos = [m['flujo'] for m in muestras]
        correl = np.corrcoef(tvocs, flujos)[0, 1]
        if np.isnan(correl):
            correl = 0
        return correl, 0