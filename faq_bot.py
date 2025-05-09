"""
Telegram Bot para Clínica Médica - Estructura Base
-------------------------------------------------
Este bot proporciona información sobre una clínica médica, incluyendo horarios,
servicios, contacto, ubicaciones y fotos de las instalaciones.
"""
import asyncio
import json
import logging
import os
import pickle
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any

import dotenv
from telegram import (
    Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup,
    ReplyKeyboardRemove, Update, InputMediaPhoto
)
from telegram.ext import (
    Application, CallbackContext, CallbackQueryHandler, CommandHandler,
    ConversationHandler, MessageHandler, filters
)
from telegram.error import BadRequest, TelegramError

# Cargar variables de entorno
dotenv.load_dotenv()

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# Estados para el ConversationHandler
class States:
    NOMBRE = 0
    IDIOMA = 1
    MENU_PRINCIPAL = 2
    SUBMENU = 3
    FEEDBACK = 4

# Configuración de rutas y archivos
class Config:
    DATA_FILE = 'user_data.pkl'
    PHOTOS_DIR = os.getenv('PHOTOS_DIR', 'fotos')
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    @classmethod
    def get_photo_path(cls, sede: str, num: int) -> str:
        """Devuelve la ruta a una foto específica"""
        return os.path.join(cls.PHOTOS_DIR, sede, f"{num}.jpg")
# Clase para manejar los datos de usuario
class UserDataManager:
    def __init__(self):
        self.user_data = {}
        self.conversation_states = {}
        self.load_data()
    
    def load_data(self) -> None:
        """Carga los datos del archivo de persistencia"""
        try:
            if os.path.exists(Config.DATA_FILE):
                with open(Config.DATA_FILE, 'rb') as f:
                    data = pickle.load(f)
                    self.user_data = data.get('user_data', {})
                    self.conversation_states = data.get('conversation_states', {})
                logger.info("Datos de usuarios cargados correctamente")
        except Exception as e:
            logger.error(f"Error al cargar datos: {e}")
    
    def save_data(self) -> None:
        """Guarda los datos al archivo de persistencia"""
        try:
            with open(Config.DATA_FILE, 'wb') as f:
                data = {
                    'user_data': self.user_data,
                    'conversation_states': self.conversation_states
                }
                pickle.dump(data, f)
            logger.info("Datos de usuarios guardados correctamente")
        except Exception as e:
            logger.error(f"Error al guardar datos: {e}")
def get_user(self, user_id: int) -> Dict[str, Any]:
        """Obtiene los datos de un usuario, o crea un nuevo registro si no existe"""
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        return self.user_data[user_id]
    
    def get_language(self, user_id: int) -> str:
        """Obtiene el idioma de un usuario, o devuelve el idioma por defecto"""
        user = self.get_user(user_id)
        return user.get('language', 'es')
    
    def get_name(self, user_id: int) -> str:
        """Obtiene el nombre de un usuario, o devuelve una cadena vacía"""
        user = self.get_user(user_id)
        return user.get('name', '')
    
    def update_user(self, user_id: int, data: Dict[str, Any]) -> None:
        """Actualiza los datos de un usuario"""
        user = self.get_user(user_id)
        user.update(data)
        user['last_active'] = datetime.now().isoformat()
        self.save_data()
    
    def save_conversation_state(self, user_id: int, state: int, context: str) -> None:
        """Guarda el estado de la conversación de un usuario"""
        self.conversation_states[user_id] = {
            'state': state,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        self.save_data()
    
    def get_conversation_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene el estado de la conversación de un usuario"""
        return self.conversation_states.get(user_id)
# Clase para manejar traducciones
class TranslationManager:
    """Maneja las traducciones del bot en diferentes idiomas"""
    
    def __init__(self):
        self.translations = {
            'es': {
                'welcome': '¡Hola! Podría ingresar su nombre, por favor:',
                'welcome_back': '¡Bienvenido de nuevo, {}! ¿En qué podemos ayudarle hoy?',
                'language_selection': 'Por favor, seleccione su idioma preferido:',
                'menu_greeting': '¡Hola {}! Soy su asistente informativo. Espero serle de ayuda. Por favor, elija una opción:',
                'menu_options': ['Horarios', 'Contacto', 'Servicios', 'Ubicación', 'Ver fotos'],
                'select_option': '{}, por favor seleccione una opción:',
                'hours': ['Horario de atención', 'Horario de citas'],
                'contact': ['Teléfono', 'Correo electrónico'],
                'services': ['Consulta general', 'Especialidades'],
                'location': ['Sede Principal', 'Sede Secundaria'],
                'back': 'Volver al menú principal',
                'help_text': 'Este bot le ayuda a obtener información sobre nuestra clínica. Utilice los botones para navegar, o puede usar estos comandos:\n'
                             '/start - Iniciar o reiniciar el bot\n'
                             '/help - Mostrar esta ayuda\n'
                             '/menu - Ir al menú principal\n'
                             '/contacto - Información de contacto directo\n'
                             '/idioma - Cambiar el idioma',
                'info_text': 'Somos una clínica comprometida con su salud y bienestar. Ofrecemos servicios médicos de alta calidad con profesionales altamente calificados.',
                'unknown_command': '{}, lo siento, no entiendo ese comando. Utilice /help para ver los comandos disponibles.',
                'select_hours': '{}, seleccione una opción relacionada con horarios:',
                'select_contact': '{}, seleccione una opción relacionada con contacto:',
                'en': {
                'welcome': 'Hello! Could you please enter your name:',
                'welcome_back': 'Welcome back, {}! How can we help you today?',
                'language_selection': 'Please select your preferred language:',
                'menu_greeting': 'Hello {}! I am your information assistant. I hope to be of help. Please choose an option:',
                'menu_options': ['Hours', 'Contact', 'Services', 'Location', 'See Photos'],
                'select_option': '{}, please select an option:',
                'hours': ['Opening hours', 'Appointment hours'],
                'contact': ['Phone', 'Email'],
                'services': ['General consultation', 'Specialties'],
                'location': ['Main Office', 'Secondary Office'],
                'back': 'Back to main menu',
                'help_text': 'This bot helps you get information about our clinic. Use the buttons to navigate, or you can use these commands:\n'
                             '/start - Start or restart the bot\n'
                             '/help - Show this help\n'
                             '/menu - Go to the main menu\n'
                             '/contact - Direct contact information\n'
                             '/language - Change language',
                'info_text': 'We are a clinic committed to your health and wellbeing. We offer high-quality medical services with highly qualified professionals.',
                'unknown_command': '{}, I\'m sorry, I don\'t understand that command. Use /help to see available commands.',
                'select_hours': '{}, select an option related to hours:',
                'select_contact': '{}, select an option related to contact:',
                'select_services': '{}, select an option related to services:',
                'select_location': '{}, select an option related to location:',
                'opening_hours': '{}, our opening hours are Monday to Friday from 8:00 AM to 6:00 PM.',
                'appointment_hours': '{}, appointments are available Monday to Friday from 9:00 AM to 5:00 PM.',
                'phone': '{}, you can contact us at 123-456-7890.',
                'email': '{}, our email is info@clinic.com.',
                'general_consultation': '{}, we offer general consultations Monday to Friday. Schedule your appointment!',
                'specialties': '{}, we have specialties in Cardiology, Dermatology, and Pediatrics.',
                'address': '{}, we are located at Specialized Clinic, Calle 9 #15-25, Neiva, Huila.',
                'how_to_get': '{}, to reach our clinic, you can head to Universidad Surcolombiana in Neiva, Huila. Here is the exact location:',
                'see_photos': '{}, here you can see photos of our facilities:',
                'what_else': '{}, what else can I help you with? Please choose an option:',
                'choose_menu_option': '{}, please select an option from the menu.',
                'session_resumed': '{}, we have recovered your previous session. You were inquiring about {}. Would you like to continue?',
                'feedback': '{}, how would you rate your experience with our bot?',
                'thanks_feedback': '{}, thank you for your feedback. We will take it into account to improve our service.',
                'error_message': 'An error has occurred. We will restart the conversation to ensure proper functioning.',
                'select_photos': '{}, which office photos would you like to see?'
            }
        }
        
        # Constantes para geolocalizaciones
        self.locations = {
            'main_office': (2.9371, -75.2958),  # Coordenadas de la sede principal
            'secondary_office': (2.9428, -75.2981)  # Coordenadas de la sede secundaria
        }
    
    def get_text(self, key: str, lang: str, *args) -> str:
        """Obtiene un texto traducido por su clave"""
        if lang not in self.translations:
            lang = 'es'  # Idioma por defecto
        
        text = self.translations[lang].get(key, self.translations['es'].get(key, key))
        
        if args:
            return text.format(*args)
        
        return text
# Parte de la clase ClinicBot - Métodos auxiliares
class ClinicBot:
    def __init__(self):
        """Inicializa el bot y sus componentes"""
        self.user_data_manager = UserDataManager()
        self.translation_manager = TranslationManager()
        
        if not Config.TOKEN:
            raise ValueError("No se ha configurado el token de Telegram. Revise el archivo .env")
            
        self.application = Application.builder().token(Config.TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self) -> None:
        """Configura los manejadores de comandos y conversaciones"""
        # Configurar el ConversationHandler principal
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                States.NOMBRE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.select_language)
                ],
                States.IDIOMA: [
                    CallbackQueryHandler(self.handle_language_selection, pattern=r"^lang_")
                ],
States.MENU_PRINCIPAL: [
                    CallbackQueryHandler(self.handle_main_menu_callback, pattern=r"^menu_|^resume_"),
                    CommandHandler("menu", self.handle_menu),
                    CommandHandler("help", self.handle_help),
                    CommandHandler("contacto", self.handle_contact),
                    CommandHandler("idioma", self.handle_language_command),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown)
                ],
                States.SUBMENU: [
                    CallbackQueryHandler(self.handle_submenu_callback),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown)
                ],
                States.FEEDBACK: [
                    CallbackQueryHandler(self.handle_feedback, pattern=r"^feedback_"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown)
                ],
            },
            fallbacks=[
                CommandHandler("start", self.start),
                CommandHandler("help", self.handle_help),
                CommandHandler("menu", self.handle_menu),
                CommandHandler("contacto", self.handle_contact),
                CommandHandler("idioma", self.handle_language_command),
                MessageHandler(filters.COMMAND, self.unknown),
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown)
            ],
            name="main_conversation",
            persistent=False,
            per_message=False
        )

        # Agregar manejadores
        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("info", self.handle_info))
        self.application.add_error_handler(self.error_handler)
        
        # Programar tareas periódicas
        try:
            job_queue = self.application.job_queue
            if job_queue:
                job_queue.run_repeating(self.clean_old_messages, interval=3600)
        except Exception as e:
            logger.warning(f"No se pudo configurar el JobQueue: {e}")
    
    def run(self) -> None:
        """Inicia el bot"""
        logger.info("Iniciando el bot")
        return
# Métodos auxiliares
    async def send_and_track_message(self, update: Update, context: CallbackContext, 
                                     message_function, *args, **kwargs) -> Optional[Any]:
        """Envía un mensaje y lo rastrea para poder eliminarlo después"""
        try:
            message = await message_function(*args, **kwargs)
            
            # Inicializar lista de mensajes adicionales si no existe
            if 'additional_messages' not in context.user_data:
                context.user_data['additional_messages'] = []
            
            # Añadir el ID del mensaje a la lista
            context.user_data['additional_messages'].append(message.message_id)
            
            return message
        except Exception as e:
            logger.error(f"Error al enviar y rastrear mensaje: {e}")
            return None
    
    async def replace_message(self, update: Update, context: CallbackContext, 
                              text: str, reply_markup=None) -> Optional[Any]:
        """Elimina el mensaje anterior y envía uno nuevo, o edita el mensaje existente"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        try:
            # Eliminar el mensaje anterior si existe
            if 'last_bot_message_id' in context.user_data:
                try:
                    await context.bot.delete_message(
                        chat_id=chat_id, 
                        message_id=context.user_data['last_bot_message_id']
                    )
                except Exception as e:
                    logger.debug(f"No se pudo eliminar mensaje anterior: {e}")
# Enviar nuevo mensaje
            if update.callback_query:
                # Si viene de un callback_query, editamos el mensaje existente
                try:
                    await update.callback_query.answer()
                    message = await update.callback_query.message.edit_text(
                        text=text,
                        reply_markup=reply_markup
                    )
                except (BadRequest, TelegramError) as e:
                    logger.warning(f"No se pudo editar el mensaje: {e}. Enviando un nuevo mensaje.")
                    # Si falla la edición, enviamos un mensaje nuevo
                    message = await context.bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=reply_markup
                    )
            else:
                # Si viene de un mensaje normal, enviamos uno nuevo
                message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup
                )
            
            # Guardar el ID del nuevo mensaje
            context.user_data['last_bot_message_id'] = message.message_id
            
            return message
        except Exception as e:
            logger.error(f"Error en replace_message: {e}")
            # Enviar un mensaje nuevo como último recurso
            try:
                message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup
                )
                context.user_data['last_bot_message_id'] = message.message_id
                return message
            except Exception as inner_e:
                logger.error(f"Error crítico al enviar mensaje: {inner_e}")
                return None

    async def create_main_menu_markup(self, lang: str) -> InlineKeyboardMarkup:
        """Crea un markup de teclado para el menú principal"""
        keyboard = []
        menu_options = self.translation_manager.get_text('menu_options', lang)
        
        for i in range(0, len(menu_options), 2):
            row = []
            for j in range(i, min(i + 2, len(menu_options))):
                row.append(InlineKeyboardButton(menu_options[j], callback_data=f"menu_{menu_options[j]}"))
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
async def show_main_menu(self, update: Update, context: CallbackContext, 
                             user_id: int, lang: str) -> None:
        """Muestra el menú principal, eliminando mensajes adicionales"""
        name = self.user_data_manager.get_name(user_id)
        
        # Eliminar mensajes adicionales (ubicaciones, fotos, etc.)
        if 'additional_messages' in context.user_data:
            try:
                for msg_id in context.user_data['additional_messages']:
                    try:
                        await context.bot.delete_message(
                            chat_id=update.effective_chat.id,
                            message_id=msg_id
                        )
                    except Exception as e:
                        logger.debug(f"No se pudo eliminar mensaje adicional {msg_id}: {e}")
                
                # Limpiar la lista después de intentar eliminar todos los mensajes
                context.user_data['additional_messages'] = []
            except Exception as e:
                logger.error(f"Error al eliminar mensajes adicionales: {e}")
        
        # Crear teclado inline para el menú principal
        reply_markup = await self.create_main_menu_markup(lang)
        
        try:
            await self.replace_message(
                update, 
                context, 
                self.translation_manager.get_text('what_else', lang, name),
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error en show_main_menu: {e}")
            try:
                # Intentar enviar un nuevo mensaje en caso de error
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.translation_manager.get_text('what_else', lang, name),
                    reply_markup=reply_markup
                )
            except Exception as inner_e:
                logger.error(f"Error crítico en show_main_menu: {inner_e}")
    
    async def send_photos(self, update: Update, context: CallbackContext, 
                          sede: str, lang: str) -> None:
        """Envía fotos de una sede específica"""
        # Inicializar la lista de mensajes adicionales si no existe
        if 'additional_messages' not in context.user_data:
            context.user_data['additional_messages'] = []
            
        # Mensaje con botón de volver
        back_button = [[InlineKeyboardButton(
            self.translation_manager.get_text('back', lang), 
            callback_data="back_to_main"
        )]]
# Determinar carpeta según la sede
        if sede == "sede_principal":
            folder_name = "sede_principal"
            sede_text = "Sede Principal"
        else:
            folder_name = "sede_secundaria"
            sede_text = "Sede Secundaria"
        
        # Enviar mensaje inicial
        mensaje_inicial = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Fotos de la {sede_text}:",
            reply_markup=InlineKeyboardMarkup(back_button)
        )
        context.user_data['additional_messages'].append(mensaje_inicial.message_id)
        
        # Intentar enviar fotos
        fotos_enviadas = False
        photo_dir = os.path.join(Config.PHOTOS_DIR, folder_name)
        
        # Verificar si la carpeta existe
        if os.path.exists(photo_dir) and os.path.isdir(photo_dir):
            # Listar archivos de la carpeta
            files = [f for f in os.listdir(photo_dir) 
                    if os.path.isfile(os.path.join(photo_dir, f)) and 
                    f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            for file in files:
                try:
                    photo_path = os.path.join(photo_dir, file)
                    with open(photo_path, 'rb') as photo:
                        sent_photo = await context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=photo
                        )
                        context.user_data['additional_messages'].append(sent_photo.message_id)
                        fotos_enviadas = True
                except Exception as e:
                    logger.error(f"Error al enviar foto {photo_path}: {e}")
        
        # Si no hay fotos o no se pudieron enviar
        if not fotos_enviadas:
            no_photos_msg = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"No se encontraron fotos para la {sede_text}."
            )
            context.user_data['additional_messages'].append(no_photos_msg.message_id)
            
    async def clean_old_messages(self, context: CallbackContext):
        """Limpia mensajes antiguos"""
        for user_id, data in context.chat_data.items():
            if 'last_bot_messages' in data:
                for msg_id in data['last_bot_messages']:
                    try:
                        await context.bot.delete_message(chat_id=user_id, message_id=msg_id)
                    except Exception as e:
                        logger.debug(f"No se pudo eliminar mensaje antiguo: {e}")
                data['last_bot_messages'] = []


# Función principal para iniciar el bot
def main() -> None:
    """Función principal para iniciar el bot"""
    try:
        # Crear e iniciar el bot
        bot = ClinicBot()
        bot.run()
    except Exception as e:
        logger.critical(f"Error crítico al iniciar el bot: {e}")


if __name__ == '__main__':
    main()
