#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear modelo de IA inicial para DENCO v3.1
RECALIBRADO con valores reales del sensor CCS811 curado 48h:
  - TVOC ambiente: 1-5 ppb  (antes el modelo usaba 30 ppb como base → error)
  - eCO2 ambiente: 411 ppm
  - Temperatura: 26°C
  - Humedad: 42.9%

CORRECCIÓN CRÍTICA: el servidor_ia.py asignaba riesgo por NÚMERO de cluster
(cluster 0=bajo, 1=medio, 2=alto), lo cual es incorrecto porque KMeans asigna
etiquetas arbitrariamente. El riesgo debe basarse en el campo 'grupo_normal'
del metadata. Este script guarda ese campo correctamente.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import json
from datetime import datetime
import config
import os

def crear_modelo_inicial():
    """Crea modelo KMeans con datos sintéticos ajustados al hardware real curado."""

    print("=" * 70)
    print("🔬 CREANDO MODELO DE IA - SENSOR CURADO 48H (DENCO v3.1 RECALIBRADO)")
    print("=" * 70)
    print("\n📊 BASELINE REAL DEL SENSOR (mediciones sin soplar, ambiente):")
    print("   • TVOC:       1–5  ppb  ← valor real medido")
    print("   • eCO2:       411  ppm  ← valor real medido")
    print("   • Temperatura: 26.0 °C")
    print("   • Humedad:    42.9 %")
    print("   • Flujo basal: 0.9 L/s  (primera sesión real)")
    print("   • Volumen:     4.0 L    (primera sesión real)")
    print("=" * 70)

    os.makedirs(config.MODELOS_DIR, exist_ok=True)
    np.random.seed(42)
    n_sesiones = 60   # más datos → mejor separación de clusters

    # ------------------------------------------------------------------
    # GRUPO 0 — NORMAL / AIRE AMBIENTE (60%)
    # TVOC muy bajo (1–15 ppb), eCO2 cercano al ambiental (400-500)
    # ------------------------------------------------------------------
    n_norm = int(n_sesiones * 0.60)
    print(f"\n✅ Grupo NORMAL (60%): {n_norm} sesiones")
    tvoc_n  = np.abs(np.random.normal(5,   4,   n_norm))   # pico real = 1 ppb
    eco2_n  = np.random.normal(420,  30,  n_norm)
    temp_n  = np.random.normal(26.0,  0.5, n_norm)
    hum_n   = np.random.normal(43.0,  3,   n_norm)
    flujo_n = np.random.normal(0.90,  0.15,n_norm)
    vol_n   = np.random.normal(4.0,   0.5, n_norm)
    corr_n  = np.random.normal(0.39,  0.10,n_norm)         # correlación medida 0.388

    # ------------------------------------------------------------------
    # GRUPO 1 — SOSPECHOSO (25%)
    # Inflamación leve, inicio de actividad metabólica elevada
    # TVOC 50–200 ppb, eCO2 600–900 ppm
    # ------------------------------------------------------------------
    n_sosp = int(n_sesiones * 0.25)
    print(f"⚠️  Grupo SOSPECHOSO (25%): {n_sosp} sesiones")
    tvoc_s  = np.random.normal(120,  50,  n_sosp)
    eco2_s  = np.random.normal(750,  100, n_sosp)
    temp_s  = np.random.normal(32.0,  0.5, n_sosp)
    hum_s   = np.random.normal(55.0,  5,   n_sosp)
    flujo_s = np.random.normal(1.20,  0.20,n_sosp)
    vol_s   = np.random.normal(4.5,   0.4, n_sosp)
    corr_s  = np.random.normal(0.55,  0.12,n_sosp)

    # ------------------------------------------------------------------
    # GRUPO 2 — ANÓMALO / EFECTO WARBURG (15%)
    # VOC elevados, firma metabólica clara
    # TVOC > 300 ppb, eCO2 > 1200 ppm
    # ------------------------------------------------------------------
    n_anom = n_sesiones - n_norm - n_sosp
    print(f"🔴 Grupo ANÓMALO (15%): {n_anom} sesiones")
    tvoc_a  = np.random.normal(600,  150,  n_anom)
    eco2_a  = np.random.normal(1400,  250, n_anom)
    temp_a  = np.random.normal(33.5,   0.8, n_anom)
    hum_a   = np.random.normal(70.0,  10,   n_anom)
    flujo_a = np.random.normal(1.40,   0.25, n_anom)
    vol_a   = np.random.normal(5.0,    0.5,  n_anom)
    corr_a  = np.random.normal(0.72,   0.12, n_anom)

    # Combinar y construir DataFrame
    tvoc  = np.concatenate([tvoc_n,  tvoc_s,  tvoc_a])
    eco2  = np.concatenate([eco2_n,  eco2_s,  eco2_a])
    temp  = np.concatenate([temp_n,  temp_s,  temp_a])
    hum   = np.concatenate([hum_n,   hum_s,   hum_a])
    flujo = np.concatenate([flujo_n, flujo_s, flujo_a])
    vol   = np.concatenate([vol_n,   vol_s,   vol_a])
    corr  = np.concatenate([corr_n,  corr_s,  corr_a])

    # Forzar límites físicos
    tvoc  = np.clip(tvoc,  0, 5000)
    eco2  = np.clip(eco2,  400, 5000)
    hum   = np.clip(hum,   10,  100)
    flujo = np.clip(flujo, 0.1, 10)

    df = pd.DataFrame({
        'tvoc_medio':           tvoc,
        'eco2_medio':           eco2,
        'temp_media':           temp,
        'hum_media':            hum,
        'flujo_medio_Lps':      flujo,
        'volumen_total_L':      vol,
        'correlacion_voc_flujo': corr
    })

    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"\n📊 Total: {len(df)} sesiones sintéticas")
    print(f"   TVOC : {df['tvoc_medio'].min():.1f} – {df['tvoc_medio'].max():.1f} ppb")
    print(f"   eCO2 : {df['eco2_medio'].min():.0f} – {df['eco2_medio'].max():.0f} ppm")

    # Normalizar y entrenar
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=20)
    clusters = kmeans.fit_predict(X_scaled)

    # Identificar cluster normal = menor TVOC+eCO2 combinados
    df_temp = df.copy()
    df_temp['cluster'] = clusters
    cluster_stats = df_temp.groupby('cluster')[['tvoc_medio', 'eco2_medio']].mean().sum(axis=1)
    grupo_normal = int(cluster_stats.idxmin())

    print(f"\n🧠 CLUSTERS ENCONTRADOS:")
    for c in range(3):
        mask = clusters == c
        tag = "✅ NORMAL" if c == grupo_normal else (
              "🔴 ANÓMALO" if df[mask]['tvoc_medio'].mean() > 200 else "⚠️  SOSPECHOSO")
        print(f"   Cluster {c} ({tag}): {mask.sum()} sesiones | "
              f"TVOC={df[mask]['tvoc_medio'].mean():.0f} ppb | "
              f"eCO2={df[mask]['eco2_medio'].mean():.0f} ppm")

    # Guardar modelos
    joblib.dump(kmeans, config.IA_CONFIG['modelo_path'])
    joblib.dump(scaler, config.IA_CONFIG['scaler_path'])

    metadata = {
        'fecha_entrenamiento': datetime.now().isoformat(),
        'version': '3.1',
        'n_sesiones': len(df),
        'n_clusters': 3,
        'grupo_normal': grupo_normal,          # ← CLAVE para servidor_ia.py
        'baseline_real': {
            'tvoc_ppb': '1-5',
            'eco2_ppm': '411',
            'temp_c': '26.0',
            'hum_pct': '42.9'
        },
        'features': list(df.columns),
        'cluster_centers': kmeans.cluster_centers_.tolist(),
        'cluster_sizes': [int((clusters == i).sum()) for i in range(3)],
        'cluster_tvoc_means': {
            str(i): float(df[clusters == i]['tvoc_medio'].mean()) for i in range(3)
        },
        'descripcion': 'Modelo v3.1 — sensor curado 48h — baseline real 1-5 ppb'
    }

    metadata_path = config.MODELOS_DIR / 'metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n💾 Guardado:")
    print(f"   ✓ {config.IA_CONFIG['modelo_path']}")
    print(f"   ✓ {config.IA_CONFIG['scaler_path']}")
    print(f"   ✓ {metadata_path}")
    print(f"   → grupo_normal = {grupo_normal}")

    # Verificar con lectura real
    print(f"\n🔍 VERIFICACIÓN con valores reales (TVOC=1, eCO2=411):")
    test = np.array([[1, 411, 26.0, 42.9, 0.90, 4.0, 0.39]])
    pred = kmeans.predict(scaler.transform(test))
    ok = "✅ CORRECTO" if pred[0] == grupo_normal else "❌ ERROR — revisar distribuciones"
    print(f"   → Cluster predicho: {pred[0]}  (grupo_normal={grupo_normal})  {ok}")

    print("\n" + "=" * 70)
    print("✅ MODELO RECALIBRADO LISTO")
    print("=" * 70)
    return True


if __name__ == "__main__":
    crear_modelo_inicial()