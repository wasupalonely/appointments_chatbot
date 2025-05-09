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
                'select_services': '{}, seleccione una opción relacionada con servicios:',
                'select_location': '{}, seleccione una opción relacionada con ubicación:',
                'opening_hours': '{}, nuestro horario de atención es de lunes a viernes de 8:00 AM a 6:00 PM.',
                'appointment_hours': '{}, las citas están disponibles de lunes a viernes de 9:00 AM a 5:00 PM.',
                'phone': '{}, puede contactarnos al número 123-456-7890.',
                'email': '{}, nuestro correo electrónico es info@clinica.com.',
                'general_consultation': '{}, ofrecemos consultas generales de lunes a viernes. ¡Agenda su cita!',
                'specialties': '{}, contamos con especialidades en Cardiología, Dermatología y Pediatría.',
                'address': '{}, nuestra sede principal se encuentra ubicada en:  Calle 9 #15-25, Neiva, Huila. y  nuestra segunda sede se encuentra en :   Cl. 9 #15-25, Neiva, Huila. ',
                'how_to_get': '{}, para llegar a nuestra clínica, puede dirigirse a la Universidad Surcolombiana en Neiva, Huila. Aquí está la ubicación exacta:',
                'see_photos': '{}, aquí puede ver fotos de nuestras instalaciones:',
                'what_else': '{}, ¿en qué más puedo ayudarle? Por favor, elija una opción:',
                'choose_menu_option': '{}, por favor, seleccione una opción del menú.',
                'session_resumed': '{}, hemos recuperado su sesión anterior. Estaba consultando sobre {}. ¿Desea continuar?',
                'feedback': '{}, ¿cómo calificaría su experiencia con nuestro bot?',
                'thanks_feedback': '{}, gracias por su feedback. Lo tendremos en cuenta para mejorar nuestro servicio.',
                'error_message': 'Ha ocurrido un error. Vamos a reiniciar la conversación para asegurar un funcionamiento correcto.',
                'select_photos': '{}, ¿de qué sede desea ver las fotos?'
            },
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
                
                
    # Parte de la clase ClinicBot - Funciones de inicialización y menú principal
    
    async def start(self, update: Update, context: CallbackContext) -> int:
        """Inicia o reinicia la conversación con el bot"""
        user_id = update.effective_user.id
        
        # Inicializar user_data para este usuario si no existe
        if not context.user_data:
            context.user_data.clear()  # Asegurarse de que no haya datos residuales
        
        # Verificar si el usuario ya existe
        if user_id in self.user_data_manager.user_data:
            user = self.user_data_manager.get_user(user_id)
            lang = self.user_data_manager.get_language(user_id)
            name = self.user_data_manager.get_name(user_id)
            
            # Registrar actividad
            self.user_data_manager.update_user(user_id, {})
            
            # Crear teclado inline para el menú principal
            reply_markup = await self.create_main_menu_markup(lang)
            
            try:
                # Usar nuestra función para reemplazar mensajes
                await self.replace_message(
                    update, 
                    context, 
                    self.translation_manager.get_text('welcome_back', lang, name),
                    reply_markup=reply_markup
                )
                
                # Restaurar el estado anterior de la conversación si existe
                state = self.user_data_manager.get_conversation_state(user_id)
                if state:
                    context_text = state.get('context', 'información general')
                    
                    # Preguntar si quiere continuar donde lo dejó
                    keyboard = [
                        [InlineKeyboardButton("Sí", callback_data="resume_yes"),
                         InlineKeyboardButton("No", callback_data="resume_no")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await self.replace_message(
                        update, 
                        context, 
                        self.translation_manager.get_text('session_resumed', lang, name, context_text),
                        reply_markup=reply_markup
                    )
            except Exception as e:
                logger.error(f"Error en start para usuario existente: {e}")
                # Intentar enviar un mensaje básico en caso de error
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.translation_manager.get_text('error_message', lang)
                )
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.translation_manager.get_text('welcome_back', lang, name),
                    reply_markup=reply_markup
                )
                
            return States.MENU_PRINCIPAL
        
        # Nuevo usuario
        try:
            await self.replace_message(
                update, 
                context, 
                self.translation_manager.get_text('welcome', 'es'),
                reply_markup=ReplyKeyboardRemove()
            )
        except Exception as e:
            logger.error(f"Error en start para nuevo usuario: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=self.translation_manager.get_text('welcome', 'es'),
                reply_markup=ReplyKeyboardRemove()
            )
        
        return States.NOMBRE
    
    async def select_language(self, update: Update, context: CallbackContext) -> int:
        """Permite al usuario seleccionar su idioma preferido"""
        user_id = update.effective_user.id
        
        # Guardar nombre si viene de /start
        if update.message and update.message.text:
            self.user_data_manager.update_user(user_id, {'name': update.message.text})
        
        # Teclado para selección de idioma
        keyboard = [
            [InlineKeyboardButton("Español 🇪🇸", callback_data="lang_es")],
            [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await self.replace_message(
                update, 
                context, 
                self.translation_manager.get_text('language_selection', 'es'),
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error en select_language: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=self.translation_manager.get_text('language_selection', 'es'),
                reply_markup=reply_markup
            )
        
        return States.IDIOMA
    
    async def handle_language_selection(self, update: Update, context: CallbackContext) -> int:
        """Maneja la selección de idioma del usuario"""
        try:
            query = update.callback_query
            
            user_id = update.effective_user.id
            lang = query.data.split('_')[1]
            
            # Guardar idioma
            self.user_data_manager.update_user(user_id, {'language': lang})
            
            # Mostrar menú principal
            reply_markup = await self.create_main_menu_markup(lang)
            
            name = self.user_data_manager.get_name(user_id)
            
            await self.replace_message(
                update, 
                context, 
                self.translation_manager.get_text('menu_greeting', lang, name),
                reply_markup=reply_markup
            )
            
            return States.MENU_PRINCIPAL
        except Exception as e:
            logger.error(f"Error en handle_language_selection: {e}")
            # Intentar recuperarse del error
            user_id = update.effective_user.id
            lang = 'es'  # Valor predeterminado en caso de error
            
            if user_id in self.user_data_manager.user_data:
                lang = self.user_data_manager.get_language(user_id)
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=self.translation_manager.get_text('error_message', lang)
            )
            # Reiniciar el bot
            return await self.start(update, context)
        
    # Parte de la clase ClinicBot - Manejadores del menú principal y submenús

    async def handle_main_menu_callback(self, update: Update, context: CallbackContext) -> int:
        """Maneja las opciones del menú principal"""
        try:
            query = update.callback_query
            
            user_id = update.effective_user.id
            lang = self.user_data_manager.get_language(user_id)
            name = self.user_data_manager.get_name(user_id)
            
            # Registrar el contexto actual para recuperación de sesión
            data = query.data.split('_', 1)[1] if '_' in query.data else query.data
            self.user_data_manager.save_conversation_state(user_id, States.MENU_PRINCIPAL, data)
            
            # Manejar la opción "Reanudar sesión"
            if query.data == "resume_yes":
                state = self.user_data_manager.get_conversation_state(user_id)
                context_text = state.get('context', '')
                
                try:
                    # Simular la selección del menú correspondiente
                    if context_text in self.translation_manager.get_text('menu_options', lang):
                        # Simular un callback para la opción del menú
                        query.data = f"menu_{context_text}"
                        # Y luego procesamos normalmente
                        return await self.handle_main_menu_callback(update, context)
                    else:
                        # Volver al menú principal si no se puede determinar el contexto
                        await self.show_main_menu(update, context, user_id, lang)
                        return States.MENU_PRINCIPAL
                except Exception as e:
                    logger.error(f"Error al reanudar sesión: {e}")
                    # Si falla, enviamos un nuevo mensaje
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=self.translation_manager.get_text('what_else', lang, name),
                        reply_markup=await self.create_main_menu_markup(lang)
                    )
                    return States.MENU_PRINCIPAL
                    
            elif query.data == "resume_no":
                await self.show_main_menu(update, context, user_id, lang)
                return States.MENU_PRINCIPAL
            
            # Manejar las opciones del menú principal
            menu_options = self.translation_manager.get_text('menu_options', lang)
            
            if "Horarios" in data or "Hours" in data:
                keyboard = []
                hours_options = self.translation_manager.get_text('hours', lang)
                for option in hours_options:
                    keyboard.append([InlineKeyboardButton(option, callback_data=f"submenu_{option}")])
                keyboard.append([InlineKeyboardButton(self.translation_manager.get_text('back', lang), callback_data="back_to_main")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.replace_message(
                    update, 
                    context, 
                    self.translation_manager.get_text('select_hours', lang, name),
                    reply_markup=reply_markup
                )
                return States.SUBMENU
                
            elif "Contacto" in data or "Contact" in data:
                keyboard = []
                contact_options = self.translation_manager.get_text('contact', lang)
                for option in contact_options:
                    keyboard.append([InlineKeyboardButton(option, callback_data=f"submenu_{option}")])
                keyboard.append([InlineKeyboardButton(self.translation_manager.get_text('back', lang), callback_data="back_to_main")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.replace_message(
                    update, 
                    context, 
                    self.translation_manager.get_text('select_contact', lang, name),
                    reply_markup=reply_markup
                )
                return States.SUBMENU
                
            elif "Servicios" in data or "Services" in data:
                keyboard = []
                services_options = self.translation_manager.get_text('services', lang)
                for option in services_options:
                    keyboard.append([InlineKeyboardButton(option, callback_data=f"submenu_{option}")])
                keyboard.append([InlineKeyboardButton(self.translation_manager.get_text('back', lang), callback_data="back_to_main")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.replace_message(
                    update, 
                    context, 
                    self.translation_manager.get_text('select_services', lang, name),
                    reply_markup=reply_markup
                )
                return States.SUBMENU
                
            elif "Ubicación" in data or "Location" in data:
                # Mostrar directamente las opciones de sedes
                keyboard = []
                location_options = self.translation_manager.get_text('location', lang)
                for option in location_options:
                    keyboard.append([InlineKeyboardButton(option, callback_data=f"location_{option}")])
                keyboard.append([InlineKeyboardButton(self.translation_manager.get_text('back', lang), callback_data="back_to_main")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.replace_message(
                    update, 
                    context, 
                    self.translation_manager.get_text('select_location', lang, name),
                    reply_markup=reply_markup
                )
                return States.SUBMENU
            
            elif "Ver fotos" in data or "See Photos" in data:
                # Mostrar opciones para elegir de qué sede ver las fotos
                keyboard = [
                    [InlineKeyboardButton("Sede Principal", callback_data="fotos_sede_principal")],
                    [InlineKeyboardButton("Sede Secundaria", callback_data="fotos_sede_secundaria")],
                    [InlineKeyboardButton(self.translation_manager.get_text('back', lang), callback_data="back_to_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.replace_message(
                    update, 
                    context, 
                    self.translation_manager.get_text('select_photos', lang, name),
                    reply_markup=reply_markup
                )
                return States.SUBMENU
            
            else:
                await self.replace_message(
                    update, 
                    context, 
                    self.translation_manager.get_text('choose_menu_option', lang, name),
                    reply_markup=await self.create_main_menu_markup(lang)
                )
                return States.MENU_PRINCIPAL
        except Exception as e:
            logger.error(f"Error en handle_main_menu_callback: {e}")
            # Intentar recuperarse del error
            try:
                user_id = update.effective_user.id
                lang = self.user_data_manager.get_language(user_id)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.translation_manager.get_text('error_message', lang)
                )
                # Mostrar menú principal como último recurso
                keyboard = await self.create_main_menu_markup(lang)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.translation_manager.get_text('what_else', lang, self.user_data_manager.get_name(user_id)),
                    reply_markup=keyboard
                )
                return States.MENU_PRINCIPAL
            except Exception as inner_e:
                logger.error(f"Error crítico en handle_main_menu_callback: {inner_e}")
                return States.MENU_PRINCIPAL
                
    async def handle_submenu_callback(self, update: Update, context: CallbackContext) -> int:
        """Maneja las opciones de los submenús"""
        try:
            query = update.callback_query
            
            user_id = update.effective_user.id
            lang = self.user_data_manager.get_language(user_id)
            name = self.user_data_manager.get_name(user_id)
            
            # Registrar el contexto actual
            data = query.data.split('_', 1)[1] if '_' in query.data else query.data
            self.user_data_manager.save_conversation_state(user_id, States.SUBMENU, data)
            
            # Preparar botón de volver al menú principal
            back_button = [[InlineKeyboardButton(
                self.translation_manager.get_text('back', lang), 
                callback_data="back_to_main"
            )]]
            
            # Volver al menú principal
            if query.data == "back_to_main":
                await self.show_main_menu(update, context, user_id, lang)
                return States.MENU_PRINCIPAL
            
            # Obtener opciones traducidas
            hours_options = self.translation_manager.get_text('hours', lang)
            contact_options = self.translation_manager.get_text('contact', lang)
            services_options = self.translation_manager.get_text('services', lang)
            location_options = self.translation_manager.get_text('location', lang)
            
            # Horarios
            if hours_options[0] in data:  # Horario de atención / Opening hours
                await self.replace_message(
                    update, 
                    context, 
                    self.translation_manager.get_text('opening_hours', lang, name),
                    reply_markup=InlineKeyboardMarkup(back_button)
                )
                return States.SUBMENU
                
            elif hours_options[1] in data:  # Horario de citas / Appointment hours
                await self.replace_message(
                    update, 
                    context, 
                    self.translation_manager.get_text('appointment_hours', lang, name),
                    reply_markup=InlineKeyboardMarkup(back_button)
                )
                return States.SUBMENU
            
            # Contacto
            elif contact_options[0] in data:  # Teléfono / Phone
                await self.replace_message(
                    update, 
                    context, 
                    self.translation_manager.get_text('phone', lang, name),
                    reply_markup=InlineKeyboardMarkup(back_button)
                )
                return States.SUBMENU
                
            elif contact_options[1] in data:  # Correo electrónico / Email
                await self.replace_message(
                    update, 
                    context, 
                    self.translation_manager.get_text('email', lang, name),
                    reply_markup=InlineKeyboardMarkup(back_button)
                )
                return States.SUBMENU
            
            # Servicios
            elif services_options[0] in data:  # Consulta general / General consultation
                await self.replace_message(
                    update, 
                    context, 
                    self.translation_manager.get_text('general_consultation', lang, name),
                    reply_markup=InlineKeyboardMarkup(back_button)
                )
                return States.SUBMENU
                
            elif services_options[1] in data:  # Especialidades / Specialties
                await self.replace_message(
                    update, 
                    context, 
                    self.translation_manager.get_text('specialties', lang, name),
                    reply_markup=InlineKeyboardMarkup(back_button)
                )
                return States.SUBMENU
            
            # Ubicación
            elif location_options[0] in data or "Sede Principal" in data or "Main Office" in data:
                # Mostrar información y mapa de la sede principal
                mensaje = "Sede Principal:\nCalle 9 #15-25, Neiva, Huila."
                
                # Primero enviamos el mensaje con botón de volver
                await self.replace_message(
                    update, 
                    context, 
                    mensaje,
                    reply_markup=InlineKeyboardMarkup(back_button)
                )
                
                try:
                    # Luego enviamos la ubicación y la rastreamos
                    await self.send_and_track_message(
                        update, 
                        context, 
                        context.bot.send_location,
                        chat_id=update.effective_chat.id,
                        latitude=self.translation_manager.locations['main_office'][0],
                        longitude=self.translation_manager.locations['main_office'][1]
                    )
                except Exception as e:
                    logger.error(f"Error al enviar ubicación: {e}")
                
                return States.SUBMENU
                
            elif location_options[1] in data or "Sede Secundaria" in data or "Secondary Office" in data:
                # Mostrar información y mapa de la sede secundaria
                mensaje = "Sede Secundaria:\nCl. 9 #15-25, Neiva, Huila."
                
                # Primero enviamos el mensaje con botón de volver
                await self.replace_message(
                    update, 
                    context, 
                    mensaje,
                    reply_markup=InlineKeyboardMarkup(back_button)
                )
                
                try:
                    # Luego enviamos la ubicación y la rastreamos
                    await self.send_and_track_message(
                        update, 
                        context, 
                        context.bot.send_location,
                        chat_id=update.effective_chat.id,
                        latitude=self.translation_manager.locations['secondary_office'][0],
                        longitude=self.translation_manager.locations['secondary_office'][1]
                    )
                except Exception as e:
                    logger.error(f"Error al enviar ubicación: {e}")
                
                return States.SUBMENU
            
            # Fotos
            elif "fotos_sede_principal" in query.data:
                try:
                    await self.send_photos(update, context, "sede_principal", lang)
                except Exception as e:
                    logger.error(f"Error al enviar fotos de sede principal: {e}")
                    error_msg = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"Error al cargar las fotos: {str(e)}"
                    )
                    if 'additional_messages' not in context.user_data:
                        context.user_data['additional_messages'] = []
                    context.user_data['additional_messages'].append(error_msg.message_id)
                
                return States.SUBMENU
                
            elif "fotos_sede_secundaria" in query.data:
                try:
                    await self.send_photos(update, context, "sede_secundaria", lang)
                except Exception as e:
                    logger.error(f"Error al enviar fotos de sede secundaria: {e}")
                    error_msg = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"Error al cargar las fotos: {str(e)}"
                    )
                    if 'additional_messages' not in context.user_data:
                        context.user_data['additional_messages'] = []
                    context.user_data['additional_messages'].append(error_msg.message_id)
                
                return States.SUBMENU
                
            else:
                await self.replace_message(
                    update, 
                    context, 
                    self.translation_manager.get_text('choose_menu_option', lang, name),
                    reply_markup=InlineKeyboardMarkup(back_button)
                )
                return States.SUBMENU
        except Exception as e:
            logger.error(f"Error en handle_submenu_callback: {e}")
            # Intentar recuperarse del error
            try:
                user_id = update.effective_user.id
                lang = self.user_data_manager.get_language(user_id)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.translation_manager.get_text('error_message', lang)
                )
                # Mostrar menú principal como último recurso
                keyboard = await self.create_main_menu_markup(lang)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.translation_manager.get_text('what_else', lang, self.user_data_manager.get_name(user_id)),
                    reply_markup=keyboard
                )
                return States.MENU_PRINCIPAL
            except Exception as inner_e:
                logger.error(f"Error crítico en handle_submenu_callback: {inner_e}")
                return States.MENU_PRINCIPAL
            
    # Parte de la clase ClinicBot - Otros comandos y manejo de errores

    async def handle_help(self, update: Update, context: CallbackContext) -> None:
        """Muestra la ayuda del bot"""
        try:
            user_id = update.effective_user.id
            lang = self.user_data_manager.get_language(user_id)
            
            await self.replace_message(
                update, 
                context, 
                self.translation_manager.get_text('help_text', lang),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                    self.translation_manager.get_text('back', lang), 
                    callback_data="back_to_main"
                )]])
            )
        except Exception as e:
            logger.error(f"Error en handle_help: {e}")
            try:
                # Intento de recuperación
                user_id = update.effective_user.id
                lang = self.user_data_manager.get_language(user_id)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.translation_manager.get_text('help_text', lang),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                        self.translation_manager.get_text('back', lang), 
                        callback_data="back_to_main"
                    )]])
                )
            except Exception as inner_e:
                logger.error(f"Error crítico en handle_help: {inner_e}")
    
    async def handle_info(self, update: Update, context: CallbackContext) -> None:
        """Muestra información sobre la clínica"""
        try:
            user_id = update.effective_user.id
            lang = self.user_data_manager.get_language(user_id)
            
            await self.replace_message(
                update, 
                context, 
                self.translation_manager.get_text('info_text', lang),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                    self.translation_manager.get_text('back', lang), 
                    callback_data="back_to_main"
                )]])
            )
        except Exception as e:
            logger.error(f"Error en handle_info: {e}")
            try:
                # Intento de recuperación
                user_id = update.effective_user.id
                lang = self.user_data_manager.get_language(user_id)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.translation_manager.get_text('info_text', lang),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                        self.translation_manager.get_text('back', lang), 
                        callback_data="back_to_main"
                    )]])
                )
            except Exception as inner_e:
                logger.error(f"Error crítico en handle_info: {inner_e}")
    
    async def handle_menu(self, update: Update, context: CallbackContext) -> int:
        """Muestra el menú principal"""
        try:
            user_id = update.effective_user.id
            
            if user_id not in self.user_data_manager.user_data:
                return await self.start(update, context)
            
            lang = self.user_data_manager.get_language(user_id)
            name = self.user_data_manager.get_name(user_id)
            
            keyboard = await self.create_main_menu_markup(lang)
            
            await self.replace_message(
                update, 
                context, 
                self.translation_manager.get_text('what_else', lang, name),
                reply_markup=keyboard
            )
            
            return States.MENU_PRINCIPAL
        except Exception as e:
            logger.error(f"Error en handle_menu: {e}")
            try:
                # Intento de recuperación
                user_id = update.effective_user.id
                lang = 'es'
                if user_id in self.user_data_manager.user_data:
                    lang = self.user_data_manager.get_language(user_id)
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.translation_manager.get_text('error_message', lang)
                )
                # Reiniciar el bot
                return await self.start(update, context)
            except Exception as inner_e:
                logger.error(f"Error crítico en handle_menu: {inner_e}")
                return States.MENU_PRINCIPAL
    
    async def handle_contact(self, update: Update, context: CallbackContext) -> None:
        """Muestra la información de contacto"""
        try:
            user_id = update.effective_user.id
            lang = self.user_data_manager.get_language(user_id)
            name = self.user_data_manager.get_name(user_id)
            
            contact_text = (
                f"{self.translation_manager.get_text('phone', lang, name)}\n"
                f"{self.translation_manager.get_text('email', lang, name)}"
            )
            
            await self.replace_message(
                update, 
                context, 
                contact_text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                    self.translation_manager.get_text('back', lang), 
                    callback_data="back_to_main"
                )]])
            )
        except Exception as e:
            logger.error(f"Error en handle_contact: {e}")
            try:
                # Intento de recuperación
                user_id = update.effective_user.id
                lang = self.user_data_manager.get_language(user_id)
                name = self.user_data_manager.get_name(user_id)
                
                contact_text = (
                    f"{self.translation_manager.get_text('phone', lang, name)}\n"
                    f"{self.translation_manager.get_text('email', lang, name)}"
                )
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=contact_text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                        self.translation_manager.get_text('back', lang), 
                        callback_data="back_to_main"
                    )]])
                )
            except Exception as inner_e:
                logger.error(f"Error crítico en handle_contact: {inner_e}")
                
    # Continuación de la clase ClinicBot - Feedback y manejo de errores

    async def handle_language_command(self, update: Update, context: CallbackContext) -> int:
        """Permite cambiar el idioma"""
        try:
            return await self.select_language(update, context)
        except Exception as e:
            logger.error(f"Error en handle_language_command: {e}")
            # Intentar recuperarse
            return await self.start(update, context)
    
    async def request_feedback(self, update: Update, context: CallbackContext) -> int:
        """Solicita feedback al usuario"""
        try:
            user_id = update.effective_user.id
            lang = self.user_data_manager.get_language(user_id)
            name = self.user_data_manager.get_name(user_id)
            
            keyboard = [
                [
                    InlineKeyboardButton("⭐", callback_data="feedback_1"),
                    InlineKeyboardButton("⭐⭐", callback_data="feedback_2"),
                    InlineKeyboardButton("⭐⭐⭐", callback_data="feedback_3"),
                    InlineKeyboardButton("⭐⭐⭐⭐", callback_data="feedback_4"),
                    InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="feedback_5")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                self.translation_manager.get_text('feedback', lang, name),
                reply_markup=reply_markup
            )
            
            return States.FEEDBACK
        except Exception as e:
            logger.error(f"Error en request_feedback: {e}")
            # En caso de error, volver al menú principal
            return States.MENU_PRINCIPAL
    
    async def handle_feedback(self, update: Update, context: CallbackContext) -> int:
        """Procesa el feedback del usuario"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = update.effective_user.id
            lang = self.user_data_manager.get_language(user_id)
            name = self.user_data_manager.get_name(user_id)
            
            # Guardar la calificación
            rating = int(query.data.split('_')[1])
            self.user_data_manager.update_user(user_id, {'feedback': rating})
            
            # Agradecer el feedback
            try:
                await query.message.edit_text(
                    self.translation_manager.get_text('thanks_feedback', lang, name)
                )
                
                # Volver al menú principal después de un breve delay
                await query.message.reply_text(
                    self.translation_manager.get_text('what_else', lang, name),
                    reply_markup=await self.create_main_menu_markup(lang)
                )
            except Exception as e:
                logger.error(f"Error al editar mensaje en feedback: {e}")
                # Si falla, enviar un nuevo mensaje
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.translation_manager.get_text('thanks_feedback', lang, name)
                )
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.translation_manager.get_text('what_else', lang, name),
                    reply_markup=await self.create_main_menu_markup(lang)
                )
            
            return States.MENU_PRINCIPAL
        except Exception as e:
            logger.error(f"Error en handle_feedback: {e}")
            # En caso de error, volver al menú principal
            try:
                user_id = update.effective_user.id
                lang = self.user_data_manager.get_language(user_id)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.translation_manager.get_text('what_else', lang, self.user_data_manager.get_name(user_id)),
                    reply_markup=await self.create_main_menu_markup(lang)
                )
            except Exception as inner_e:
                logger.error(f"Error crítico en handle_feedback: {inner_e}")
            return States.MENU_PRINCIPAL
            
    async def unknown(self, update: Update, context: CallbackContext) -> None:
        """Maneja comandos desconocidos"""
        try:
            if update.message and update.message.text == "/start":
                return await self.start(update, context)
                
            user_id = update.effective_user.id
            lang = self.user_data_manager.get_language(user_id)
            name = self.user_data_manager.get_name(user_id)
            
            await update.message.reply_text(
                self.translation_manager.get_text('unknown_command', lang, name)
            )
        except Exception as e:
            logger.error(f"Error en unknown: {e}")
            # En caso de error, intentar recuperarse
            try:
                if update.message:
                    await update.message.reply_text("Lo siento, ha ocurrido un error. Por favor intente con /start")
            except Exception as inner_e:
                logger.error(f"Error crítico en unknown: {inner_e}")
    
    async def error_handler(self, update, context):
        """Maneja errores generales del bot"""
        logger.error(f"Update {update} caused error {context.error}")
        try:
            if update.effective_user:
                user_id = update.effective_user.id
                lang = self.user_data_manager.get_language(user_id)
                
                if update.message:
                    await update.message.reply_text(
                        "Lo siento, ha ocurrido un error. Por favor, intente nuevamente con /start." if lang == 'es' else
                        "Sorry, an error has occurred. Please try again with /start."
                    )
                elif update.callback_query:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Lo siento, ha ocurrido un error. Por favor, intente nuevamente con /start." if lang == 'es' else
                        "Sorry, an error has occurred. Please try again with /start."
                    )
        except:
            logger.error("Error en el manejador de errores")
            try:
                if update and update.effective_chat:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Error crítico. Por favor, intente con /start."
                    )
            except:
                logger.error("Error crítico en el manejador de errores")


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
