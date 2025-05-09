"""
Punto de entrada para el despliegue del bot en Render.com
Este archivo combina un servidor web simple con el bot de Telegram
"""
import os
import threading
import logging
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Variable global para el estado del bot
BOT_RUNNING = False
BOT_START_TIME = None

class BotServerHandler(BaseHTTPRequestHandler):
    """Manejador para el servidor HTTP simple"""
    
    def _set_response(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()
    
    def do_GET(self):
        """Manejar solicitudes GET"""
        if self.path == '/health' or self.path == '/healthz':
            # Endpoint de health check para Render
            uptime = time.time() - BOT_START_TIME if BOT_START_TIME else 0
            response = {
                'status': 'up',
                'timestamp': time.time(),
                'bot_status': 'running' if BOT_RUNNING else 'stopped',
                'uptime_seconds': uptime
            }
            self._set_response()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            # Página principal con información básica
            self._set_response(content_type='text/html')
            self.wfile.write(b'<html><head><title>Bot de Clinica Medica</title></head>')
            self.wfile.write(b'<body><h1>Bot de Telegram para Clinica Medica</h1>')
            self.wfile.write(b'<p>El bot esta activo y ejecutandose.</p>')
            self.wfile.write(b'<p>Visita <a href="/health">/health</a> para ver el estado del bot.</p>')
            self.wfile.write(b'</body></html>')

def run_web_server():
    """Ejecuta el servidor web en el puerto especificado por Render"""
    port = int(os.environ.get('PORT', 8080))
    server_address = ('', port)
    httpd = HTTPServer(server_address, BotServerHandler)
    logger.info(f'Iniciando servidor HTTP en puerto {port}')
    httpd.serve_forever()

def run_telegram_bot():
    """Ejecuta el bot de Telegram en un hilo separado"""
    global BOT_RUNNING, BOT_START_TIME
    
    try:
        # Intentar cargar el módulo del bot
        from faq_bot import ClinicBot
        
        logger.info("Iniciando bot de Telegram...")
        BOT_START_TIME = time.time()
        bot = ClinicBot()
        BOT_RUNNING = True
        bot.run()  # Este método bloquea hasta que el bot se detiene
        
        logger.warning("El bot de Telegram se ha detenido.")
        BOT_RUNNING = False
    except Exception as e:
        logger.error(f"Error al iniciar el bot de Telegram: {e}")
        BOT_RUNNING = False

def main():
    """Función principal que inicia el servidor web y el bot"""
    # Iniciar el servidor web en un hilo
    logger.info("Iniciando la aplicación en Render.com")
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    logger.info("Servidor web iniciado en segundo plano")
    
    # Iniciar el bot en un hilo separado
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    logger.info("Bot de Telegram iniciado en segundo plano")
    
    logger.info("Aplicación iniciada correctamente")
    
    try:
        # Mantener el proceso principal vivo
        while True:
            time.sleep(60)
            logger.info("Aplicación en ejecución... Bot estado: " + 
                       ("ACTIVO" if BOT_RUNNING else "DETENIDO"))
    except KeyboardInterrupt:
        logger.info("Deteniendo la aplicación...")

if __name__ == '__main__':
    main()
