/*
 * SISTEMA DENCO - Versión Optimizada para ATmega328PB v2.3
 * CORREGIDO: Clasificación ISO 13138 basada en VOLUMEN (no en conteo de muestras)
 * - Clasifica como ESPACIO_MUERTO hasta superar 237 mL
 * - Cambia a ALVEOLAR después de volumen muerto
 */

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include "Adafruit_CCS811.h"

// ===== CONFIGURACIÓN =====
const float D_ENTRADA_MM = 26.8;
const float D_CUELLO_MM = 17.9;
const float COEF_DESCARGA = 0.995;
const float FACTOR_VELOCIDAD = 1.0 / sqrt(1.0 - pow(D_CUELLO_MM / D_ENTRADA_MM, 4));
const float AREA_CUELLO_M2 = PI * pow(D_CUELLO_MM / 1000.0, 2) / 4.0;

// Umbrales de detección
const float UMBRAL_TEMP_INICIO = 0.3; // REDUCIDO para mejor detección
const float UMBRAL_HUM_INICIO = 3.0;  // REDUCIDO
const float UMBRAL_TEMP_FIN = 0.2;
const int TIMEOUT_SOPLIDO_MS = 15000; // 15 segundos
const unsigned long INTERVALO_MUESTREO_MS = 100;
const float DT = INTERVALO_MUESTREO_MS / 1000.0;

// ===== CONFIGURACIÓN ISO 13138 =====
// Volumen muerto: 150 mL anatómico + 87 mL instrumental = 237 mL
const float VOLUMEN_MUERTO_ML = 237.0;
const float VOLUMEN_MUERTO_L = VOLUMEN_MUERTO_ML / 1000.0; // 0.237 L

// ===== SENSORES =====
Adafruit_BME280 bme;
Adafruit_CCS811 ccs;

// ===== VARIABLES DE ESTADO =====
bool soplando = false;
bool sistema_iniciado = false;
unsigned long tiempo_anterior = 0;
unsigned long tiempo_inicio_soplido = 0;
unsigned long contador_muestras = 0;
unsigned long numero_muestra = 0;
float volumen_total_L = 0.0;
float flujo_anterior = -1.0; // -1 indica primera muestra
float temp_anterior = 0;
float hum_anterior = 0;
float tvoc_anterior = 0;
float volumen_ultima_muestra = 0.0; // Para seguimiento

// ===== OPTIMIZACIÓN: Enum en lugar de String =====
enum Fraccion
{
  FRACCION_DESCONOCIDA,
  FRACCION_ESPACIO_MUERTO,
  FRACCION_ALVEOLAR
};
Fraccion fraccion_respiratoria = FRACCION_DESCONOCIDA;

// ===== FUNCIONES =====
float calcularDensidadAire(float temp, float hum, float pres_hPa)
{
  float T_kelvin = temp + 273.15;
  float P_pascales = pres_hPa * 100.0;
  float es = 6.1078 * pow(10, (7.5 * temp / (temp + 237.3)));
  float pv = (hum / 100.0) * es * 100.0;
  float pd = P_pascales - pv;
  const float Rd = 287.05;
  const float Rv = 461.495;
  return (pd / (Rd * T_kelvin)) + (pv / (Rv * T_kelvin));
}

float calcularFlujoVenturi(float deltaP_Pa, float densidad)
{
  if (deltaP_Pa <= 0)
    return 0;

  float qm = COEF_DESCARGA * FACTOR_VELOCIDAD * AREA_CUELLO_M2 *
             sqrt(2.0 * densidad * deltaP_Pa);
  float qv = qm / densidad;
  float qv_Lps = qv * 1000.0;

  return qv_Lps;
}

// TODO: Reemplazar con sensor de presión real MPXV7002DP
float estimarDeltaP(float tvoc_derivada)
{
  const float DELTA_P_MIN = 50.0;
  const float DELTA_P_MAX = 500.0;
  const float TVOC_DERIVADA_MAX = 500.0;
  float derivada_normalizada = constrain(tvoc_derivada, 0, TVOC_DERIVADA_MAX) / TVOC_DERIVADA_MAX;
  return DELTA_P_MIN + derivada_normalizada * (DELTA_P_MAX - DELTA_P_MIN);
}

// ===== FUNCIÓN CORREGIDA: Clasificación basada en VOLUMEN (ISO 13138) =====
Fraccion clasificarFraccionISO13138(float volumen_actual_L)
{
  if (volumen_actual_L < VOLUMEN_MUERTO_L)
  {
    return FRACCION_ESPACIO_MUERTO;
  }
  else
  {
    return FRACCION_ALVEOLAR;
  }
}

const char *fraccionToString(Fraccion f)
{
  switch (f)
  {
  case FRACCION_ESPACIO_MUERTO:
    return "ESPACIO_MUERTO";
  case FRACCION_ALVEOLAR:
    return "ALVEOLAR";
  default:
    return "DESCONOCIDA";
  }
}

void enviarInicioSistema()
{
  Serial.print("INICIO_SISTEMA,");
  Serial.println(millis());
  sistema_iniciado = true;
}

void enviarInicioExhalacion()
{
  Serial.print("INICIO_EXHALACION,");
  Serial.println(millis());
}

void enviarFinExhalacion(float volumen, bool timeout)
{
  if (timeout)
  {
    Serial.print("FIN_EXHALACION_TIMEOUT,");
  }
  else
  {
    Serial.print("FIN_EXHALACION,");
  }
  Serial.print(volumen, 3);
  Serial.print(",");
  Serial.println(millis());
}

void enviarMuestra(unsigned long num,
                   uint16_t tvoc,
                   uint16_t eco2,
                   float temp,
                   float hum,
                   float pres,
                   float flujo,
                   float volumen,
                   float deltaP,
                   Fraccion fraccion)
{
  Serial.print("MUESTRA,");
  Serial.print(num);
  Serial.print(",");
  Serial.print(tvoc);
  Serial.print(",");
  Serial.print(eco2);
  Serial.print(",");
  Serial.print(temp, 1);
  Serial.print(",");
  Serial.print(hum, 1);
  Serial.print(",");
  Serial.print(pres, 1);
  Serial.print(",");
  Serial.print(flujo, 3);
  Serial.print(",");
  Serial.print(volumen, 3);
  Serial.print(",");
  Serial.print(deltaP, 0);
  Serial.print(",");
  Serial.print(fraccionToString(fraccion));
  Serial.print(",");
  Serial.println(millis());
}

void reiniciarVariablesSoplido()
{
  soplando = true;
  contador_muestras = 0;
  numero_muestra = 0;
  volumen_total_L = 0.0;
  flujo_anterior = -1.0;
  volumen_ultima_muestra = 0.0;
  tiempo_inicio_soplido = millis();
  fraccion_respiratoria = FRACCION_DESCONOCIDA;
}

// ===== SETUP =====
void setup()
{
  Serial.begin(115200);
  Serial.println(F("\n=== SISTEMA DENCO v2.3 (ISO 13138 Volumétrica) ==="));

  Serial.print(F("Venturi: D="));
  Serial.print(D_ENTRADA_MM);
  Serial.print(F("mm, d="));
  Serial.print(D_CUELLO_MM);
  Serial.println(F("mm"));

  Serial.print(F("Volumen muerto ISO 13138: "));
  Serial.print(VOLUMEN_MUERTO_ML);
  Serial.println(F(" mL"));

  if (!bme.begin(0x76))
  {
    Serial.println(F("ERROR: No se encontro BME280"));
    while (1)
      ;
  }
  Serial.println(F("BME280 iniciado"));

  if (!ccs.begin(0x5A))
  {
    Serial.println(F("ERROR: No se encontro CCS811"));
    while (1)
      ;
  }

  ccs.setDriveMode(CCS811_DRIVE_MODE_250MS);
  Serial.println(F("CCS811 iniciado (modo 250ms)"));

  Serial.println(F("Estabilizando sensores..."));
  int intentos = 0;
  while (!ccs.available() && intentos < 50)
  {
    delay(100);
    intentos++;
  }

  enviarInicioSistema();
  Serial.println(F("Sistema listo. Esperando exhalacion..."));
}

// ===== LOOP PRINCIPAL =====
void loop()
{
  unsigned long tiempo_actual = millis();

  if (tiempo_actual - tiempo_anterior < INTERVALO_MUESTREO_MS)
  {
    return;
  }
  tiempo_anterior = tiempo_actual;

  float temp = bme.readTemperature();
  float hum = bme.readHumidity();
  float pres = bme.readPressure() / 100.0F;

  if (isnan(temp) || isnan(hum) || isnan(pres))
  {
    Serial.println(F("ERROR: Lectura BME280 invalida"));
    return;
  }

  ccs.setEnvironmentalData(hum, temp);

  if (ccs.available() && !ccs.readData())
  {
    uint16_t tvoc = ccs.getTVOC();
    uint16_t eco2 = ccs.geteCO2();

    // ===== DETECCION DE INICIO =====
    if (!soplando)
    {
      if ((temp - temp_anterior) > UMBRAL_TEMP_INICIO ||
          (hum - hum_anterior) > UMBRAL_HUM_INICIO)
      {
        reiniciarVariablesSoplido();
        enviarInicioExhalacion();
        Serial.println(F("Exhalacion detectada!"));
      }
    }

    // ===== DETECCION DE FIN =====
    if (soplando)
    {
      bool finDetectado = false;
      bool esTimeout = false;

      if ((temp_anterior - temp) > UMBRAL_TEMP_FIN)
      {
        finDetectado = true;
        Serial.println(F("Fin por temperatura"));
      }

      if (millis() - tiempo_inicio_soplido > TIMEOUT_SOPLIDO_MS)
      {
        finDetectado = true;
        esTimeout = true;
        Serial.println(F("Fin por timeout"));
      }

      if (finDetectado)
      {
        soplando = false;
        enviarFinExhalacion(volumen_total_L, esTimeout);
        Serial.print(F("Exhalacion finalizada. Volumen total: "));
        Serial.print(volumen_total_L, 3);
        Serial.print(F(" L, Espacio muerto: "));
        Serial.print(VOLUMEN_MUERTO_L, 3);
        Serial.println(F(" L"));
      }
    }

    // ===== ACTUALIZAR ANTERIORES =====
    if (tvoc > 0 || eco2 > 0)
    {
      temp_anterior = temp;
      hum_anterior = hum;
    }

    // ===== CALCULO DE FLUJO Y VOLUMEN =====
    if (soplando)
    {
      contador_muestras++;
      numero_muestra++;

      float densidad = calcularDensidadAire(temp, hum, pres);

      float deriv_tvoc = 0;
      if (tvoc_anterior > 0)
      {
        deriv_tvoc = abs(tvoc - tvoc_anterior) * 10;
      }
      tvoc_anterior = tvoc;

      float delta_P = estimarDeltaP(deriv_tvoc);
      float flujo_Lps = calcularFlujoVenturi(delta_P, densidad);

      // Acumular volumen usando método del trapecio
      if (flujo_anterior >= 0)
      {
        float flujo_medio = (flujo_Lps + flujo_anterior) / 2.0;
        volumen_total_L += flujo_medio * DT;
      }
      flujo_anterior = flujo_Lps;

      //  CLASIFICACIÓN CORREGIDA: Basada en VOLUMEN ACUMULADO 
      fraccion_respiratoria = clasificarFraccionISO13138(volumen_total_L);

      // Enviar muestra con clasificación correcta
      enviarMuestra(numero_muestra, tvoc, eco2, temp, hum, pres,
                    flujo_Lps, volumen_total_L, delta_P, fraccion_respiratoria);

      // DEBUG: Mostrar cambio de fase
      if (volumen_total_L >= VOLUMEN_MUERTO_L && volumen_ultima_muestra < VOLUMEN_MUERTO_L)
      {
        Serial.print(F(">>> CAMBIO A FASE ALVEOLAR en volumen: "));
        Serial.print(volumen_total_L, 3);
        Serial.println(F(" L <<<"));
      }
      volumen_ultima_muestra = volumen_total_L;
    }
  }
}