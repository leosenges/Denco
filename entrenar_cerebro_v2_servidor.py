#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de entrenamiento del modelo de IA para DENCO - VERSIÓN SERVIDOR
Usa datos reales de PostgreSQL en i7 (192.168.1.100)
Version: 2.0 - Adaptado para PostgreSQL
"""

import psycopg2
import psycopg2.extras
import pandas as pd
import numpy as np
import joblib
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import logging
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import datetime

# Importar configuracion
import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOGS_DIR / f'entrenamiento_servidor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def conectar_postgres():
    """Conecta a PostgreSQL en el servidor i7"""
    try:
        cfg = config.SERVIDOR_CONFIG['postgres']
        conn = psycopg2.connect(
            host=cfg['host'],
            database=cfg['database'],
            user=cfg['user'],
            password=cfg['password'],
            port=cfg['port'],
            connect_timeout=5
        )
        logger.info(f"✅ Conectado a PostgreSQL en {cfg['host']}:{cfg['port']}")
        return conn
    except Exception as e:
        logger.error(f"❌ Error conectando a PostgreSQL: {e}")
        return None

def cargar_datos_entrenamiento(conn, min_sesiones=None):
    """
    Carga datos de sesiones para entrenamiento con validaciones
    """
    if min_sesiones is None:
        min_sesiones = config.IA_CONFIG['min_muestras_entrenamiento']
    
    query = """
        SELECT 
            tvoc_medio, 
            eco2_medio, 
            temp_media, 
            hum_media, 
            flujo_medio_Lps, 
            volumen_total_L, 
            correlacion_voc_flujo
        FROM sesiones 
        WHERE valida = 1 
          AND tvoc_medio > 0 
          AND eco2_medio > 0
          AND volumen_total_L > 0.1
          AND flujo_medio_Lps > 0
    """
    
    df = pd.read_sql_query(query, conn)
    
    logger.info(f"Datos cargados: {len(df)} sesiones validas desde servidor")
    
    if len(df) < min_sesiones:
        logger.warning(f"Datos insuficientes: {len(df)}/{min_sesiones}")
        return None
    
    # Estadisticas basicas
    logger.info("\n📊 Estadisticas de los datos:")
    logger.info(f"  TVOC medio: {df['tvoc_medio'].mean():.1f} ± {df['tvoc_medio'].std():.1f} ppb")
    logger.info(f"  eCO2 medio: {df['eco2_medio'].mean():.1f} ± {df['eco2_medio'].std():.1f} ppm")
    logger.info(f"  Temperatura media: {df['temp_media'].mean():.1f} ± {df['temp_media'].std():.1f} °C")
    logger.info(f"  Humedad media: {df['hum_media'].mean():.1f} ± {df['hum_media'].std():.1f} %")
    logger.info(f"  Flujo medio: {df['flujo_medio_Lps'].mean():.3f} ± {df['flujo_medio_Lps'].std():.3f} L/s")
    logger.info(f"  Volumen medio: {df['volumen_total_L'].mean():.3f} ± {df['volumen_total_L'].std():.3f} L")
    logger.info(f"  Correlación media: {df['correlacion_voc_flujo'].mean():.3f} ± {df['correlacion_voc_flujo'].std():.3f}")
    
    return df

def visualizar_clustering(df, clusters, scaler, kmeans):
    """
    Genera visualizaciones del clustering
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # 1. Matriz de correlacion
    corr_matrix = df.corr()
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', ax=axes[0,0])
    axes[0,0].set_title('Matriz de Correlacion de Features')
    
    # 2. Distribucion de clusters (TVOC vs eCO2)
    scatter = axes[0,1].scatter(
        df['tvoc_medio'], 
        df['eco2_medio'],
        c=clusters, 
        cmap='viridis', 
        s=100, 
        alpha=0.7,
        edgecolors='black',
        linewidth=1
    )
    axes[0,1].set_xlabel('TVOC medio (ppb)')
    axes[0,1].set_ylabel('eCO2 medio (ppm)')
    axes[0,1].set_title('Clusters: TVOC vs eCO2')
    plt.colorbar(scatter, ax=axes[0,1], label='Cluster')
    
    # 3. Distribucion de clusters (Flujo vs Volumen)
    scatter = axes[1,0].scatter(
        df['flujo_medio_Lps'], 
        df['volumen_total_L'],
        c=clusters, 
        cmap='viridis', 
        s=100, 
        alpha=0.7,
        edgecolors='black',
        linewidth=1
    )
    axes[1,0].set_xlabel('Flujo medio (L/s)')
    axes[1,0].set_ylabel('Volumen total (L)')
    axes[1,0].set_title('Clusters: Flujo vs Volumen')
    plt.colorbar(scatter, ax=axes[1,0], label='Cluster')
    
    # 4. Centroides de clusters (en escala original)
    if hasattr(kmeans, 'cluster_centers_'):
        centroids_df = pd.DataFrame(
            scaler.inverse_transform(kmeans.cluster_centers_),
            columns=df.columns
        )
        centroids_df.T.plot(kind='bar', ax=axes[1,1])
        axes[1,1].set_title('Centroides de Clusters (valores originales)')
        axes[1,1].set_xlabel('Features')
        axes[1,1].set_ylabel('Valor')
        axes[1,1].legend(title='Cluster')
        axes[1,1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    # Guardar figura
    plot_path = config.MODELOS_DIR / f'clustering_vis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    logger.info(f"✅ Visualizacion guardada: {plot_path}")
    plt.close()

def entrenar_modelo():
    """
    Entrena el modelo de clustering con validacion de calidad
    """
    logger.info("="*70)
    logger.info("🧠 ENTRENAMIENTO DE MODELO IA - MODO SERVIDOR")
    logger.info("="*70)
    logger.info(f"📡 Servidor: {config.SERVIDOR_CONFIG['ip']}")
    logger.info(f"🗄️ Base de datos: {config.SERVIDOR_CONFIG['postgres']['database']}")
    logger.info("="*70)
    
    # Conectar a PostgreSQL
    conn = conectar_postgres()
    if not conn:
        logger.error("No se pudo conectar a PostgreSQL")
        return False
    
    try:
        # Cargar datos
        df = cargar_datos_entrenamiento(conn)
        if df is None:
            logger.error("No hay suficientes datos para entrenar")
            return False
        
        # Normalizar datos
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df)
        
        # Probar diferentes numeros de clusters
        best_k = config.IA_CONFIG['n_clusters']
        best_score = -1
        best_model = None
        
        logger.info("\n📊 Evaluando diferentes numeros de clusters...")
        max_k = min(6, len(df)//3 + 2)
        for k in range(2, max_k):
            kmeans = KMeans(n_clusters=k, random_state=config.IA_CONFIG['random_state'], n_init=10)
            labels = kmeans.fit_predict(X_scaled)
            
            if len(set(labels)) > 1:  # Necesitamos al menos 2 clusters para silhouette
                score = silhouette_score(X_scaled, labels)
                logger.info(f"  k={k}: Silhouette score = {score:.3f}")
                
                if score > best_score:
                    best_score = score
                    best_k = k
                    best_model = kmeans
        
        logger.info(f"\n✅ Mejor numero de clusters: {best_k} (score={best_score:.3f})")
        
        # Entrenar modelo final con mejor k
        kmeans = KMeans(
            n_clusters=best_k,
            random_state=config.IA_CONFIG['random_state'],
            n_init=10
        )
        clusters = kmeans.fit_predict(X_scaled)
        
        # Identificar cluster normal (menor TVOC/eCO2)
        df_temp = df.copy()
        df_temp['cluster'] = clusters
        cluster_stats = df_temp.groupby('cluster').agg({
            'tvoc_medio': 'mean',
            'eco2_medio': 'mean'
        }).sum(axis=1)
        
        grupo_normal = int(cluster_stats.idxmin())
        
        # Calcular metricas por cluster
        logger.info("\n📈 Estadisticas por cluster:")
        for cluster in range(best_k):
            mask = clusters == cluster
            tamaño = mask.sum()
            porcentaje = tamaño/len(df)*100
            
            if cluster == grupo_normal:
                logger.info(f"\n  ✅ Cluster {cluster} (NORMAL):")
            elif df[mask]['tvoc_medio'].mean() > df['tvoc_medio'].mean() * 1.5:
                logger.info(f"\n  🔴 Cluster {cluster} (ANÓMALO):")
            else:
                logger.info(f"\n  ⚠️ Cluster {cluster} (SOSPECHOSO):")
                
            logger.info(f"     Tamaño: {tamaño} sesiones ({porcentaje:.1f}%)")
            logger.info(f"     TVOC: {df[mask]['tvoc_medio'].mean():.1f} ± {df[mask]['tvoc_medio'].std():.1f} ppb")
            logger.info(f"     eCO2: {df[mask]['eco2_medio'].mean():.1f} ± {df[mask]['eco2_medio'].std():.1f} ppm")
            logger.info(f"     Volumen: {df[mask]['volumen_total_L'].mean():.3f} ± {df[mask]['volumen_total_L'].std():.3f} L")
        
        logger.info(f"\n✅ Cluster identificado como NORMAL: {grupo_normal}")
        
        # Guardar modelos
        modelo_path = config.IA_CONFIG['modelo_path']
        scaler_path = config.IA_CONFIG['scaler_path']
        
        joblib.dump(kmeans, modelo_path)
        joblib.dump(scaler, scaler_path)
        
        # Guardar metadatos
        metadata = {
            'fecha_entrenamiento': datetime.now().isoformat(),
            'n_sesiones': len(df),
            'n_clusters': best_k,
            'grupo_normal': int(grupo_normal),
            'silhouette_score': float(best_score),
            'features': list(df.columns),
            'cluster_centers': kmeans.cluster_centers_.tolist(),
            'cluster_sizes': [int((clusters == i).sum()) for i in range(best_k)],
            'cluster_means': {
                str(i): {
                    'tvoc': float(df[clusters == i]['tvoc_medio'].mean()),
                    'eco2': float(df[clusters == i]['eco2_medio'].mean()),
                    'volumen': float(df[clusters == i]['volumen_total_L'].mean())
                }
                for i in range(best_k)
            },
            'servidor': config.SERVIDOR_CONFIG['ip'],
            'base_datos': 'PostgreSQL'
        }
        
        metadata_path = config.MODELOS_DIR / 'metadata_servidor.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"\n💾 Modelo guardado en: {modelo_path}")
        logger.info(f"💾 Scaler guardado en: {scaler_path}")
        logger.info(f"💾 Metadatos guardados en: {metadata_path}")
        
        # Generar visualizaciones
        visualizar_clustering(df, clusters, scaler, kmeans)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error durante el entrenamiento: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
    finally:
        conn.close()

def verificar_modelo():
    """
    Verifica que el modelo guardado sea valido
    """
    logger.info("\n" + "="*60)
    logger.info("🔍 VERIFICANDO MODELO GUARDADO")
    logger.info("="*60)
    
    modelo_path = config.IA_CONFIG['modelo_path']
    scaler_path = config.IA_CONFIG['scaler_path']
    metadata_path = config.MODELOS_DIR / 'metadata_servidor.json'
    
    if not modelo_path.exists() or not scaler_path.exists():
        logger.error("❌ Modelo o scaler no encontrados")
        return False
    
    try:
        # Cargar modelos
        kmeans = joblib.load(modelo_path)
        scaler = joblib.load(scaler_path)
        
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {"error": "metadata no encontrada"}
        
        logger.info(f"✅ Modelo cargado correctamente")
        logger.info(f"\n📋 Metadatos:")
        logger.info(f"   - Fecha entrenamiento: {metadata.get('fecha_entrenamiento', 'N/A')}")
        logger.info(f"   - Sesiones usadas: {metadata.get('n_sesiones', 'N/A')}")
        logger.info(f"   - Clusters: {metadata.get('n_clusters', 'N/A')}")
        logger.info(f"   - Cluster normal: {metadata.get('grupo_normal', 'N/A')}")
        logger.info(f"   - Silhouette score: {metadata.get('silhouette_score', 'N/A'):.3f}")
        
        # Probar con datos de aire ambiente
        test_data = np.array([[30, 450, 31.1, 34.8, 0.24, 1.07, 0.09]])
        test_scaled = scaler.transform(test_data)
        pred = kmeans.predict(test_scaled)
        
        logger.info(f"\n🧪 Prueba con aire ambiente:")
        logger.info(f"   TVOC=30, eCO2=450 → Cluster {pred[0]}")
        
        if pred[0] == metadata.get('grupo_normal', -1):
            logger.info(f"   ✅ Correcto: aire ambiente = NORMAL")
        else:
            logger.info(f"   ⚠️ Aire ambiente no clasificado como normal")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando modelo: {e}")
        return False

def main():
    """Funcion principal"""
    
    print("\n" + "="*80)
    print("🧠 ENTRENADOR DE MODELO IA - SISTEMA DENCO v2.0 (MODO SERVIDOR)")
    print("="*80)
    print(f"\n📡 Servidor: {config.SERVIDOR_CONFIG['ip']}")
    print(f"🗄️ Base de datos: {config.SERVIDOR_CONFIG['postgres']['database']}")
    print(f"📁 Directorio modelos: {config.MODELOS_DIR}")
    print("="*80)
    
    # Preguntar si desea continuar
    respuesta = input("\n¿Desea iniciar el entrenamiento? (s/n): ")
    if respuesta.lower() != 's':
        print("Entrenamiento cancelado.")
        return
    
    # Entrenar modelo
    success = entrenar_modelo()
    
    if success:
        # Verificar modelo
        verificar_modelo()
        
        print("\n" + "="*80)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("="*80)
        print("\nEl modelo ha sido actualizado con datos reales del servidor")
        print(f"📁 Modelo guardado en: {config.IA_CONFIG['modelo_path']}")
        print("\n🚀 Listo para usar con el servidor i7")
    else:
        print("\n" + "="*80)
        print("❌ ERROR EN EL ENTRENAMIENTO")
        print("="*80)
        print("\nRevisa:")
        print("1. Conexión al servidor i7 (192.168.1.100)")
        print("2. Que existan suficientes sesiones en la BD")
        print("3. El archivo de log para mas detalles")

if __name__ == "__main__":
    main()