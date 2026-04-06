import requests
import multiprocessing
import time
import random

# CONFIGURACIÓN DEL TEST
URL_BASE = "http://192.168.1.100:5000/api/muestras" # La IP de tu i7
NUM_PACIENTES_SIMULTANEOS = 20  # Cuántos "túneles" virtuales atacan a la vez
TEST_DURATION_SEC = 30         # Tiempo de la prueba

def simular_exhalacion(paciente_id):
    """Simula una sesión completa de exhalación (10 segundos de datos)"""
    respuestas = []
    # Simulamos 100 muestras (10 segundos a 10Hz)
    for i in range(100):
        data = {
            "paciente_id": f"STRESS_{paciente_id}",
            "flujo": random.uniform(5.0, 15.0),
            "tvoc": random.uniform(100, 2000),
            "humedad": random.uniform(80, 95),
            "presion_diferencial": random.uniform(10, 50)
        }
        try:
            start_time = time.time()
            response = requests.post(URL_BASE, json=data, timeout=2)
            latencia = (time.time() - start_time) * 1000 # ms
            respuestas.append(latencia)
        except Exception as e:
            respuestas.append(None)
        
        time.sleep(0.1) # Simula el intervalo real de 100ms
    return respuestas

if __name__ == "__main__":
    print(f"--- INICIANDO PRUEBA DE ESTRÉS SOBRE {URL_BASE} ---")
    print(f"Simulando {NUM_PACIENTES_SIMULTANEOS} pacientes concurrentes...")
    
    pool = multiprocessing.Pool(processes=NUM_PACIENTES_SIMULTANEOS)
    start_global = time.time()
    
    # Lanzar los procesos
    resultados = pool.map(simular_exhalacion, range(NUM_PACIENTES_SIMULTANEOS))
    
    end_global = time.time()
    
    # PROCESAMIENTO DE MÉTRICAS
    todas_latencias = [l for r in resultados for l in r if l is not None]
    errores = sum(1 for r in resultados for l in r if l is None)
    
    print("\n--- RESULTADOS DEL TEST ---")
    print(f"Tiempo Total: {end_global - start_global:.2f} s")
    print(f"Total Peticiones: {len(todas_latencias) + errores}")
    print(f"Latencia Promedio: {sum(todas_latencias)/len(todas_latencias):.2f} ms")
    print(f"Errores (Timeouts/Fallas): {errores}")
    print(f"Peticiones por Segundo (Throughput): {(len(todas_latencias)/30):.2f} req/s")