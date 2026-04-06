# config.py.example - Copiar a config.py y completar con tus datos reales

# Modo servidor
MODO_SERVIDOR = False

# Configuración PostgreSQL (solo si MODO_SERVIDOR = True)
SERVIDOR_CONFIG = {
    'ip': 'TU_IP_AQUI',
    'postgres': {
        'host': 'TU_IP_AQUI',
        'database': 'denco_db',
        'user': 'postgres',
        'password': 'TU_CONTRASEÑA_AQUI',
        'port': '5432'
    }
}

# Configuración Serial (Arduino)
SERIAL_CONFIG = {
    'puerto': 'COM4',  # Cambiar según tu sistema (COM4 Windows, /dev/ttyUSB0 Linux)
    'baud_rate': 115200,
    'timeout': 1
}

# Directorios
LOGS_DIR = './logs'
REPORTES_DIR = './reportes'
MODELOS_DIR = './modelos'