from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler, CallbackQueryHandler
import logging
import json
import os
from datetime import datetime
import pickle
import asyncio  # Necesario para funciones async/await
from telegram.error import BadRequest, TelegramError

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Estados para el ConversationHandler
NOMBRE = 0
IDIOMA = 1
MENU_PRINCIPAL = 2
SUBMENU = 3
FEEDBACK = 4

# Diccionarios para almacenar datos de usuarios y el estado de las conversaciones
user_data = {}
conversation_states = {}

# Ruta para el archivo de persistencia de datos
DATA_FILE = 'user_data.pkl'

# Cargar datos si existe el archivo
def load_data():
    global user_data, conversation_states
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'rb') as f:
                data = pickle.load(f)
                user_data = data.get('user_data', {})
                conversation_states = data.get('conversation_states', {})
            logger.info("Datos de usuarios cargados correctamente")
    except Exception as e:
        logger.error(f"Error al cargar datos: {e}")

# Guardar datos
def save_data():
    try:
        with open(DATA_FILE, 'wb') as f:
            data = {
                'user_data': user_data,
                'conversation_states': conversation_states
            }
            pickle.dump(data, f)
        logger.info("Datos de usuarios guardados correctamente")
    except Exception as e:
        logger.error(f"Error al guardar datos: {e}")

# Traducciones
translations = {
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

# Función para obtener traducción
def get_text(key, lang, *args):
    if lang not in translations:
        lang = 'es'  # Idioma por defecto
    text = translations[lang].get(key, translations['es'].get(key, key))
    if args:
        return text.format(*args)
    return text

# Actualizar traducciones para las nuevas opciones
def update_translations():
    # Actualizar las opciones de ubicación en español
    translations['es']['location'] = ['Sede Principal', 'Sede Secundaria']
    # Actualizar las opciones de ubicación en inglés
    translations['en']['location'] = ['Main Office', 'Secondary Office']
    
    # Menú principal con "Ver fotos" como opción separada
    translations['es']['menu_options'] = ['Horarios', 'Contacto', 'Servicios', 'Ubicación', 'Ver fotos']
    translations['en']['menu_options'] = ['Hours', 'Contact', 'Services', 'Location', 'See Photos']

# Función auxiliar para enviar un mensaje y rastrearlo para eliminarlo después
async def send_and_track_message(update, context, message_function, *args, **kwargs):
    """
    Envía un mensaje y lo añade a la lista de seguimiento para poder eliminarlo después
    Ej: send_and_track_message(update, context, context.bot.send_location, latitude=123, longitude=456)
    """
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

# Función auxiliar para eliminar el último mensaje y enviar uno nuevo
async def replace_message(update, context, text, reply_markup=None):
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

# Función para manejar el comando /start e iniciar la conversación
async def start(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    
    # Inicializar user_data para este usuario si no existe
    if not context.user_data:
        context.user_data.clear()  # Asegurarse de que no haya datos residuales
    
    # Verificar si el usuario ya existe
    if user_id in user_data:
        user = user_data[user_id]
        lang = user.get('language', 'es')
        name = user.get('name', '')
        
        # Registrar actividad
        user['last_active'] = datetime.now().isoformat()
        save_data()
        
        # Crear teclado inline para el menú principal
        keyboard = []
        menu_options = get_text('menu_options', lang)
        for i in range(0, len(menu_options), 2):
            row = []
            for j in range(i, min(i + 2, len(menu_options))):
                row.append(InlineKeyboardButton(menu_options[j], callback_data=f"menu_{menu_options[j]}"))
            keyboard.append(row)
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            # Usar nuestra nueva función para reemplazar mensajes
            await replace_message(
                update, 
                context, 
                get_text('welcome_back', lang, name),
                reply_markup=reply_markup
            )
            
            # Restaurar el estado anterior de la conversación si existe
            if user_id in conversation_states:
                state = conversation_states[user_id]
                context_text = state.get('context', 'información general')
                
                # Preguntar si quiere continuar donde lo dejó
                keyboard = [
                    [InlineKeyboardButton("Sí", callback_data="resume_yes"),
                     InlineKeyboardButton("No", callback_data="resume_no")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await replace_message(
                    update, 
                    context, 
                    get_text('session_resumed', lang, name, context_text),
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Error en start para usuario existente: {e}")
            # Intentar enviar un mensaje básico en caso de error
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text('error_message', lang)
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text('welcome_back', lang, name),
                reply_markup=reply_markup
            )
            
        return MENU_PRINCIPAL
    
    # Nuevo usuario
    try:
        await replace_message(
            update, 
            context, 
            get_text('welcome', 'es'),
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Error en start para nuevo usuario: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=get_text('welcome', 'es'),
            reply_markup=ReplyKeyboardRemove()
        )
    
    return NOMBRE

# Función para seleccionar idioma
async def select_language(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {}
    
    # Guardar nombre si viene de /start
    if update.message and update.message.text and 'name' not in user_data[user_id]:
        user_data[user_id]['name'] = update.message.text
    
    # Teclado para selección de idioma
    keyboard = [
        [InlineKeyboardButton("Español 🇪🇸", callback_data="lang_es")],
        [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await replace_message(
            update, 
            context, 
            get_text('language_selection', 'es'),
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error en select_language: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=get_text('language_selection', 'es'),
            reply_markup=reply_markup
        )
    
    return IDIOMA

# Manejar selección de idioma
async def handle_language_selection(update: Update, context: CallbackContext) -> int:
    try:
        query = update.callback_query
        
        user_id = update.effective_user.id
        lang = query.data.split('_')[1]
        
        # Guardar idioma
        if isinstance(user_data[user_id], str):
            # Convertir de formato antiguo a nuevo formato
            user_data[user_id] = {
                'name': user_data[user_id],
                'language': lang,
                'last_active': datetime.now().isoformat()
            }
        else:
            user_data[user_id]['language'] = lang
            user_data[user_id]['last_active'] = datetime.now().isoformat()
        
        save_data()
        
        # Mostrar menú principal
        keyboard = []
        menu_options = get_text('menu_options', lang)
        for i in range(0, len(menu_options), 2):
            row = []
            for j in range(i, min(i + 2, len(menu_options))):
                row.append(InlineKeyboardButton(menu_options[j], callback_data=f"menu_{menu_options[j]}"))
            keyboard.append(row)
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        name = user_data[user_id].get('name', '')
        
        await replace_message(
            update, 
            context, 
            get_text('menu_greeting', lang, name),
            reply_markup=reply_markup
        )
        
        return MENU_PRINCIPAL
    except Exception as e:
        logger.error(f"Error en handle_language_selection: {e}")
        # Intentar recuperarse del error
        user_id = update.effective_user.id
        lang = 'es'  # Valor predeterminado en caso de error
        
        if user_id in user_data and isinstance(user_data[user_id], dict):
            lang = user_data[user_id].get('language', 'es')
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=get_text('error_message', lang)
        )
        # Reiniciar el bot
        return await start(update, context)

# Crear markup para el menú principal
async def create_main_menu_markup(lang):
    keyboard = []
    menu_options = get_text('menu_options', lang)
    for i in range(0, len(menu_options), 2):
        row = []
        for j in range(i, min(i + 2, len(menu_options))):
            row.append(InlineKeyboardButton(menu_options[j], callback_data=f"menu_{menu_options[j]}"))
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

# Actualizar función show_main_menu para eliminar fotos y mapas
async def show_main_menu(update, context, user_id, lang):
    name = user_data.get(user_id, {}).get('name', '')
    
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
    keyboard = []
    menu_options = get_text('menu_options', lang)
    for i in range(0, len(menu_options), 2):
        row = []
        for j in range(i, min(i + 2, len(menu_options))):
            row.append(InlineKeyboardButton(menu_options[j], callback_data=f"menu_{menu_options[j]}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await replace_message(
            update, 
            context, 
            get_text('what_else', lang, name),
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error en show_main_menu: {e}")
        try:
            # Intentar enviar un nuevo mensaje en caso de error
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text('what_else', lang, name),
                reply_markup=reply_markup
            )
        except Exception as inner_e:
            logger.error(f"Error crítico en show_main_menu: {inner_e}")

# Modificar la función handle_main_menu_callback
async def handle_main_menu_callback(update: Update, context: CallbackContext) -> int:
    try:
        query = update.callback_query
        
        user_id = update.effective_user.id
        lang = user_data.get(user_id, {}).get('language', 'es')
        name = user_data.get(user_id, {}).get('name', '')
        
        # Registrar el contexto actual para recuperación de sesión
        data = query.data.split('_', 1)[1] if '_' in query.data else query.data
        conversation_states[user_id] = {
            'state': MENU_PRINCIPAL,
            'context': data,
            'timestamp': datetime.now().isoformat()
        }
        save_data()
        
        # Manejar la opción "Reanudar sesión"
        if query.data == "resume_yes":
            state = conversation_states.get(user_id, {})
            context_text = state.get('context', '')
            
            try:
                # Simular la selección del menú correspondiente
                if context_text in get_text('menu_options', lang):
                    # Simular un callback para la opción del menú
                    # Modificamos update.callback_query.data
                    query.data = f"menu_{context_text}"
                    # Y luego procesamos normalmente
                    return await handle_main_menu_callback(update, context)
                else:
                    # Volver al menú principal si no se puede determinar el contexto
                    await show_main_menu(update, context, user_id, lang)
                    return MENU_PRINCIPAL
            except Exception as e:
                logger.error(f"Error al reanudar sesión: {e}")
                # Si falla, enviamos un nuevo mensaje en lugar de editar
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=get_text('what_else', lang, name),
                    reply_markup=await create_main_menu_markup(lang)
                )
                return MENU_PRINCIPAL
                
        elif query.data == "resume_no":
            await show_main_menu(update, context, user_id, lang)
            return MENU_PRINCIPAL
        
        # Manejar las opciones del menú principal
        menu_options = get_text('menu_options', lang)
        
        if "Horarios" in data or "Hours" in data:
            keyboard = []
            hours_options = get_text('hours', lang)
            for option in hours_options:
                keyboard.append([InlineKeyboardButton(option, callback_data=f"submenu_{option}")])
            keyboard.append([InlineKeyboardButton(get_text('back', lang), callback_data="back_to_main")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await replace_message(
                update, 
                context, 
                get_text('select_hours', lang, name),
                reply_markup=reply_markup
            )
            return SUBMENU
            
        elif "Contacto" in data or "Contact" in data:
            keyboard = []
            contact_options = get_text('contact', lang)
            for option in contact_options:
                keyboard.append([InlineKeyboardButton(option, callback_data=f"submenu_{option}")])
            keyboard.append([InlineKeyboardButton(get_text('back', lang), callback_data="back_to_main")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await replace_message(
                update, 
                context, 
                get_text('select_contact', lang, name),
                reply_markup=reply_markup
            )
            return SUBMENU
            
        elif "Servicios" in data or "Services" in data:
            keyboard = []
            services_options = get_text('services', lang)
            for option in services_options:
                keyboard.append([InlineKeyboardButton(option, callback_data=f"submenu_{option}")])
            keyboard.append([InlineKeyboardButton(get_text('back', lang), callback_data="back_to_main")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await replace_message(
                update, 
                context, 
                get_text('select_services', lang, name),
                reply_markup=reply_markup
            )
            return SUBMENU
            
        elif "Ubicación" in data or "Location" in data:
            # Ahora mostramos directamente las opciones de sedes
            keyboard = []
            location_options = get_text('location', lang)
            for option in location_options:
                keyboard.append([InlineKeyboardButton(option, callback_data=f"location_{option}")])
            keyboard.append([InlineKeyboardButton(get_text('back', lang), callback_data="back_to_main")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await replace_message(
                update, 
                context, 
                get_text('select_location', lang, name),
                reply_markup=reply_markup
            )
            return SUBMENU
        
        elif "Ver fotos" in data or "See Photos" in data:
            # Mostrar opciones para elegir de qué sede ver las fotos
            keyboard = [
                [InlineKeyboardButton("Sede Principal", callback_data="fotos_sede_principal")],
                [InlineKeyboardButton("Sede Secundaria", callback_data="fotos_sede_secundaria")],
                [InlineKeyboardButton(get_text('back', lang), callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Añadir mensaje de debug para ver qué ocurre
            debug_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Debug: Seleccionada opción Ver fotos"
            )
            if 'additional_messages' not in context.user_data:
                context.user_data['additional_messages'] = []
            context.user_data['additional_messages'].append(debug_message.message_id)
            
            await replace_message(
                update, 
                context, 
                get_text('select_photos', lang, name),
                reply_markup=reply_markup
            )
            return SUBMENU
        
        else:
            await replace_message(
                update, 
                context, 
                get_text('choose_menu_option', lang, name),
                reply_markup=await create_main_menu_markup(lang)
            )
            return MENU_PRINCIPAL
    except Exception as e:
        logger.error(f"Error en handle_main_menu_callback: {e}")
        # Intentar recuperarse del error
        try:
            user_id = update.effective_user.id
            lang = user_data.get(user_id, {}).get('language', 'es')
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text('error_message', lang)
            )
            # Mostrar menú principal como último recurso
            keyboard = await create_main_menu_markup(lang)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text('what_else', lang, user_data.get(user_id, {}).get('name', '')),
                reply_markup=keyboard
            )
            return MENU_PRINCIPAL
        except Exception as inner_e:
            logger.error(f"Error crítico en handle_main_menu_callback: {inner_e}")
            return MENU_PRINCIPAL

# Función para manejar las opciones de los submenús
async def handle_submenu_callback(update: Update, context: CallbackContext) -> int:
    try:
        query = update.callback_query
        
        user_id = update.effective_user.id
        lang = user_data.get(user_id, {}).get('language', 'es')
        name = user_data.get(user_id, {}).get('name', '')
        
        # Registrar el contexto actual
        data = query.data.split('_', 1)[1] if '_' in query.data else query.data
        conversation_states[user_id] = {
            'state': SUBMENU,
            'context': data,
            'timestamp': datetime.now().isoformat()
        }
        save_data()
        
        # Preparar botón de volver al menú principal
        back_button = [[InlineKeyboardButton(get_text('back', lang), callback_data="back_to_main")]]
        
        # Volver al menú principal
        if query.data == "back_to_main":
            await show_main_menu(update, context, user_id, lang)
            return MENU_PRINCIPAL
        
        # Manejar las opciones de los submenús
        hours_options = get_text('hours', lang)
        contact_options = get_text('contact', lang)
        services_options = get_text('services', lang)
        location_options = get_text('location', lang)
        
        # Procesar submenús
        if hours_options[0] in data:  # Horario de atención / Opening hours
            await replace_message(
                update, 
                context, 
                get_text('opening_hours', lang, name),
                reply_markup=InlineKeyboardMarkup(back_button)
            )
            return SUBMENU
            
        elif hours_options[1] in data:  # Horario de citas / Appointment hours
            await replace_message(
                update, 
                context, 
                get_text('appointment_hours', lang, name),
                reply_markup=InlineKeyboardMarkup(back_button)
            )
            return SUBMENU
        
        # Opción de contacto
        elif contact_options[0] in data:  # Teléfono / Phone
            await replace_message(
                update, 
                context, 
                get_text('phone', lang, name),
                reply_markup=InlineKeyboardMarkup(back_button)
            )
            return SUBMENU
            
        elif contact_options[1] in data:  # Correo electrónico / Email
            await replace_message(
                update, 
                context, 
                get_text('email', lang, name),
                reply_markup=InlineKeyboardMarkup(back_button)
            )
            return SUBMENU
        
        # Opción de servicios
        elif services_options[0] in data:  # Consulta general / General consultation
            await replace_message(
                update, 
                context, 
                get_text('general_consultation', lang, name),
                reply_markup=InlineKeyboardMarkup(back_button)
            )
            return SUBMENU
            
        elif services_options[1] in data:  # Especialidades / Specialties
            await replace_message(
                update, 
                context, 
                get_text('specialties', lang, name),
                reply_markup=InlineKeyboardMarkup(back_button)
            )
            return SUBMENU
        
        # Ubicación - Opciones modificadas
        elif location_options[0] in data or "Sede Principal" in data or "Main Office" in data:
            # Mostrar información y mapa de la sede principal
            mensaje = "Sede Principal:\nCalle 9 #15-25, Neiva, Huila."
            
            # Primero enviamos el mensaje con botón de volver
            await replace_message(
                update, 
                context, 
                mensaje,
                reply_markup=InlineKeyboardMarkup(back_button)
            )
            
            try:
                # Luego enviamos la ubicación y la rastreamos
                await send_and_track_message(
                    update, 
                    context, 
                    context.bot.send_location,
                    chat_id=update.effective_chat.id,
                    latitude=2.9371,
                    longitude=-75.2958
                )
            except Exception as e:
                logger.error(f"Error al enviar ubicación: {e}")
            
            return SUBMENU
            
        elif location_options[1] in data or "Sede Secundaria" in data or "Secondary Office" in data:
            # Mostrar información y mapa de la sede secundaria
            mensaje = "Sede Secundaria:\nCl. 9 #15-25, Neiva, Huila."
            
            # Primero enviamos el mensaje con botón de volver
            await replace_message(
                update, 
                context, 
                mensaje,
                reply_markup=InlineKeyboardMarkup(back_button)
            )
            
            try:
                # Luego enviamos la ubicación y la rastreamos
                await send_and_track_message(
                    update, 
                    context, 
                    context.bot.send_location,
                    chat_id=update.effective_chat.id,
                    latitude=2.9428,
                    longitude=-75.2981
                )
            except Exception as e:
                logger.error(f"Error al enviar ubicación: {e}")
            
            return SUBMENU
        
        # NUEVA IMPLEMENTACIÓN PARA MOSTRAR FOTOS
        elif "fotos_sede_principal" in query.data:
            try:
                # Inicializar la lista de mensajes adicionales si no existe
                if 'additional_messages' not in context.user_data:
                    context.user_data['additional_messages'] = []
                    
                # Enviar mensaje con botón de volver
                mensaje_inicial = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Fotos de la Sede Principal:",
                    reply_markup=InlineKeyboardMarkup(back_button)
                )
                context.user_data['additional_messages'].append(mensaje_inicial.message_id)
                
                # Obtener directorio actual
                import os
                current_dir = os.getcwd()
                
                # Mensaje de depuración
                debug_msg = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Debug: Directorio actual = {current_dir}"
                )
                context.user_data['additional_messages'].append(debug_msg.message_id)
                
                # Intentar varias rutas posibles para las imágenes
                possible_paths = [
                    # Opción 1: Ruta estándar (desde directorio actual)
                    (os.path.join(current_dir, "fotos", "sede_principal", "1.jpg"), 
                     os.path.join(current_dir, "fotos", "sede_principal", "2.png")),
                    
                    # Opción 2: Ruta absoluta explícita
                    ("/app/fotos/sede_principal/1.jpg", 
                     "/app/fotos/sede_principal/2.png"),
                    
                    # Opción 3: Ruta relativa sin directorio actual
                    ("fotos/sede_principal/1.jpg", 
                     "fotos/sede_principal/2.png"),
                     
                    # Opción 4: Directamente desde /fotos
                    (os.path.join(current_dir, "fotos", "1.jpg"), 
                     os.path.join(current_dir, "fotos", "2.png"))
                ]
                
                # Mensaje con todas las rutas que probaremos
                path_msg = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Buscando en múltiples rutas. Verificando permisos..."
                )
                context.user_data['additional_messages'].append(path_msg.message_id)
                
                # Verificar permisos en las carpetas principales
                folders_to_check = [
                    os.path.join(current_dir, "fotos"),
                    os.path.join(current_dir, "fotos", "sede_principal"),
                    "/app/fotos",
                    "/app/fotos/sede_principal"
                ]
                
                folder_info = ""
                for folder in folders_to_check:
                    if os.path.exists(folder):
                        folder_info += f"✅ Carpeta existe: {folder}\n"
                        # Verificar si es legible
                        if os.access(folder, os.R_OK):
                            folder_info += f"   📖 Permiso de lectura: Sí\n"
                        else:
                            folder_info += f"   ❌ Permiso de lectura: No\n"
                    else:
                        folder_info += f"❌ Carpeta no existe: {folder}\n"
                
                perm_msg = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=folder_info
                )
                context.user_data['additional_messages'].append(perm_msg.message_id)
                
                # Intentar cargar las imágenes usando las diferentes rutas
                image_found = False
                
                for photo_path1, photo_path2 in possible_paths:
                    path_info = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"Intentando ruta:\n{photo_path1}\n{photo_path2}\nExisten: {os.path.isfile(photo_path1)}, {os.path.isfile(photo_path2)}"
                    )
                    context.user_data['additional_messages'].append(path_info.message_id)
                    
                    # Intentar enviar la primera foto si existe
                    if os.path.isfile(photo_path1):
                        try:
                            with open(photo_path1, 'rb') as photo:
                                sent_photo = await context.bot.send_photo(
                                    chat_id=update.effective_chat.id,
                                    photo=photo
                                )
                                context.user_data['additional_messages'].append(sent_photo.message_id)
                                image_found = True
                        except Exception as img_error:
                            error_msg = await context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text=f"Error al enviar foto {photo_path1}: {str(img_error)}"
                            )
                            context.user_data['additional_messages'].append(error_msg.message_id)
                        
                    # Intentar enviar la segunda foto si existe
                    if os.path.isfile(photo_path2):
                        try:
                            with open(photo_path2, 'rb') as photo:
                                sent_photo = await context.bot.send_photo(
                                    chat_id=update.effective_chat.id,
                                    photo=photo
                                )
                                context.user_data['additional_messages'].append(sent_photo.message_id)
                                image_found = True
                        except Exception as img_error:
                            error_msg = await context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text=f"Error al enviar foto {photo_path2}: {str(img_error)}"
                            )
                            context.user_data['additional_messages'].append(error_msg.message_id)
                
                # Si no se encontró ninguna imagen
                if not image_found:
                    no_photo_msg = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="No se encontraron imágenes en ninguna de las rutas intentadas."
                    )
                    context.user_data['additional_messages'].append(no_photo_msg.message_id)
                        
            except Exception as e:
                logger.error(f"Error al enviar fotos: {str(e)}")
                # Asegurar que la lista de mensajes adicionales exista
                if 'additional_messages' not in context.user_data:
                    context.user_data['additional_messages'] = []
                    
                error_msg = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Error al enviar fotos: {str(e)}"
                )
                context.user_data['additional_messages'].append(error_msg.message_id)
            
            return SUBMENU
            
        elif "fotos_sede_secundaria" in query.data:
            try:
                # Inicializar la lista de mensajes adicionales si no existe
                if 'additional_messages' not in context.user_data:
                    context.user_data['additional_messages'] = []
                    
                # Enviar mensaje con botón de volver
                mensaje_inicial = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Fotos de la Sede Secundaria:",
                    reply_markup=InlineKeyboardMarkup(back_button)
                )
                context.user_data['additional_messages'].append(mensaje_inicial.message_id)
                
                # Obtener directorio actual
                import os
                current_dir = os.getcwd()
                
                # Mensaje de depuración
                debug_msg = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Debug: Directorio actual = {current_dir}"
                )
                context.user_data['additional_messages'].append(debug_msg.message_id)
                
                # Intentar varias rutas posibles para las imágenes
                possible_paths = [
                    # Opción 1: Ruta estándar (desde directorio actual)
                    (os.path.join(current_dir, "fotos", "sede_secundaria", "1.jpg"), 
                     os.path.join(current_dir, "fotos", "sede_secundaria", "2.png")),
                    
                    # Opción 2: Ruta absoluta explícita
                    ("/app/fotos/sede_secundaria/1.jpg", 
                     "/app/fotos/sede_secundaria/2.png"),
                    
                    # Opción 3: Ruta relativa sin directorio actual
                    ("fotos/sede_secundaria/1.jpg", 
                     "fotos/sede_secundaria/2.png"),
                     
                    # Opción 4: Directamente desde /fotos
                    (os.path.join(current_dir, "fotos", "3.jpg"), 
                     os.path.join(current_dir, "fotos", "4.png"))
                ]
                
                # Mensaje con todas las rutas que probaremos
                path_msg = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Buscando en múltiples rutas. Verificando permisos..."
                )
                context.user_data['additional_messages'].append(path_msg.message_id)
                
                # Verificar permisos en las carpetas principales
                folders_to_check = [
                    os.path.join(current_dir, "fotos"),
                    os.path.join(current_dir, "fotos", "sede_secundaria"),
                    "/app/fotos",
                    "/app/fotos/sede_secundaria"
                ]
                
                folder_info = ""
                for folder in folders_to_check:
                    if os.path.exists(folder):
                        folder_info += f"✅ Carpeta existe: {folder}\n"
                        # Verificar si es legible
                        if os.access(folder, os.R_OK):
                            folder_info += f"   📖 Permiso de lectura: Sí\n"
                        else:
                            folder_info += f"   ❌ Permiso de lectura: No\n"
                    else:
                        folder_info += f"❌ Carpeta no existe: {folder}\n"
                
                perm_msg = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=folder_info
                )
                context.user_data['additional_messages'].append(perm_msg.message_id)
                
                # Intentar cargar las imágenes usando las diferentes rutas
                image_found = False
                
                for photo_path1, photo_path2 in possible_paths:
                    path_info = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"Intentando ruta:\n{photo_path1}\n{photo_path2}\nExisten: {os.path.isfile(photo_path1)}, {os.path.isfile(photo_path2)}"
                    )
                    context.user_data['additional_messages'].append(path_info.message_id)
                    
                    # Intentar enviar la primera foto si existe
                    if os.path.isfile(photo_path1):
                        try:
                            with open(photo_path1, 'rb') as photo:
                                sent_photo = await context.bot.send_photo(
                                    chat_id=update.effective_chat.id,
                                    photo=photo
                                )
                                context.user_data['additional_messages'].append(sent_photo.message_id)
                                image_found = True
                        except Exception as img_error:
                            error_msg = await context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text=f"Error al enviar foto {photo_path1}: {str(img_error)}"
                            )
                            context.user_data['additional_messages'].append(error_msg.message_id)
                        
                    # Intentar enviar la segunda foto si existe
                    if os.path.isfile(photo_path2):
                        try:
                            with open(photo_path2, 'rb') as photo:
                                sent_photo = await context.bot.send_photo(
                                    chat_id=update.effective_chat.id,
                                    photo=photo
                                )
                                context.user_data['additional_messages'].append(sent_photo.message_id)
                                image_found = True
                        except Exception as img_error:
                            error_msg = await context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text=f"Error al enviar foto {photo_path2}: {str(img_error)}"
                            )
                            context.user_data['additional_messages'].append(error_msg.message_id)
                
                # Si no se encontró ninguna imagen
                if not image_found:
                    no_photo_msg = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="No se encontraron imágenes en ninguna de las rutas intentadas."
                    )
                    context.user_data['additional_messages'].append(no_photo_msg.message_id)
                        
            except Exception as e:
                logger.error(f"Error al enviar fotos: {str(e)}")
                # Asegurar que la lista de mensajes adicionales exista
                if 'additional_messages' not in context.user_data:
                    context.user_data['additional_messages'] = []
                    
                error_msg = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Error al enviar fotos: {str(e)}"
                )
                context.user_data['additional_messages'].append(error_msg.message_id)
            
            return SUBMENU
            
        else:
            await replace_message(
                update, 
                context, 
                get_text('choose_menu_option', lang, name),
                reply_markup=InlineKeyboardMarkup(back_button)
            )
            return SUBMENU
    except Exception as e:
        logger.error(f"Error en handle_submenu_callback: {e}")
        # Intentar recuperarse del error
        try:
            user_id = update.effective_user.id
            lang = user_data.get(user_id, {}).get('language', 'es')
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text('error_message', lang)
            )
            # Mostrar menú principal como último recurso
            keyboard = await create_main_menu_markup(lang)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text('what_else', lang, user_data.get(user_id, {}).get('name', '')),
                reply_markup=keyboard
            )
            return MENU_PRINCIPAL
        except Exception as inner_e:
            logger.error(f"Error crítico en handle_submenu_callback: {inner_e}")
            return MENU_PRINCIPAL

# Actualizar otros manejadores para usar la nueva función
async def handle_help(update: Update, context: CallbackContext) -> None:
    try:
        user_id = update.effective_user.id
        lang = user_data.get(user_id, {}).get('language', 'es')
        
        await replace_message(
            update, 
            context, 
            get_text('help_text', lang),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text('back', lang), callback_data="back_to_main")]])
        )
    except Exception as e:
        logger.error(f"Error en handle_help: {e}")
        try:
            # Intento de recuperación
            user_id = update.effective_user.id
            lang = user_data.get(user_id, {}).get('language', 'es')
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text('help_text', lang),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text('back', lang), callback_data="back_to_main")]])
            )
        except Exception as inner_e:
            logger.error(f"Error crítico en handle_help: {inner_e}")

async def handle_info(update: Update, context: CallbackContext) -> None:
    try:
        user_id = update.effective_user.id
        lang = user_data.get(user_id, {}).get('language', 'es')
        
        await replace_message(
            update, 
            context, 
            get_text('info_text', lang),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text('back', lang), callback_data="back_to_main")]])
        )
    except Exception as e:
        logger.error(f"Error en handle_info: {e}")
        try:
            # Intento de recuperación
            user_id = update.effective_user.id
            lang = user_data.get(user_id, {}).get('language', 'es')
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text('info_text', lang),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text('back', lang), callback_data="back_to_main")]])
            )
        except Exception as inner_e:
            logger.error(f"Error crítico en handle_info: {inner_e}")

async def handle_menu(update: Update, context: CallbackContext) -> int:
    try:
        user_id = update.effective_user.id
        
        if user_id not in user_data:
            return await start(update, context)
        
        lang = user_data.get(user_id, {}).get('language', 'es')
        name = user_data.get(user_id, {}).get('name', '')
        
        keyboard = []
        menu_options = get_text('menu_options', lang)
        for i in range(0, len(menu_options), 2):
            row = []
            for j in range(i, min(i + 2, len(menu_options))):
                row.append(InlineKeyboardButton(menu_options[j], callback_data=f"menu_{menu_options[j]}"))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await replace_message(
            update, 
            context, 
            get_text('what_else', lang, name),
            reply_markup=reply_markup
        )
        
        return MENU_PRINCIPAL
    except Exception as e:
        logger.error(f"Error en handle_menu: {e}")
        try:
            # Intento de recuperación
            user_id = update.effective_user.id
            lang = 'es'
            if user_id in user_data and isinstance(user_data[user_id], dict):
                lang = user_data[user_id].get('language', 'es')
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text('error_message', lang)
            )
            # Reiniciar el bot
            return await start(update, context)
        except Exception as inner_e:
            logger.error(f"Error crítico en handle_menu: {inner_e}")
            return MENU_PRINCIPAL

async def handle_contact(update: Update, context: CallbackContext) -> None:
    try:
        user_id = update.effective_user.id
        lang = user_data.get(user_id, {}).get('language', 'es')
        name = user_data.get(user_id, {}).get('name', '')
        
        contact_text = (
            f"{get_text('phone', lang, name)}\n"
            f"{get_text('email', lang, name)}"
        )
        
        await replace_message(
            update, 
            context, 
            contact_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text('back', lang), callback_data="back_to_main")]])
        )
    except Exception as e:
        logger.error(f"Error en handle_contact: {e}")
        try:
            # Intento de recuperación
            user_id = update.effective_user.id
            lang = user_data.get(user_id, {}).get('language', 'es')
            name = user_data.get(user_id, {}).get('name', '')
            
            contact_text = (
                f"{get_text('phone', lang, name)}\n"
                f"{get_text('email', lang, name)}"
            )
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=contact_text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text('back', lang), callback_data="back_to_main")]])
            )
        except Exception as inner_e:
            logger.error(f"Error crítico en handle_contact: {inner_e}")

# Comando para cambiar idioma
async def handle_language_command(update: Update, context: CallbackContext) -> int:
    try:
        return await select_language(update, context)
    except Exception as e:
        logger.error(f"Error en handle_language_command: {e}")
        # Intentar recuperarse
        return await start(update, context)

# Función para solicitar feedback
async def request_feedback(update: Update, context: CallbackContext) -> int:
    try:
        user_id = update.effective_user.id
        lang = user_data.get(user_id, {}).get('language', 'es')
        name = user_data.get(user_id, {}).get('name', '')
        
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
            get_text('feedback', lang, name),
            reply_markup=reply_markup
        )
        
        return FEEDBACK
    except Exception as e:
        logger.error(f"Error en request_feedback: {e}")
        # En caso de error, volver al menú principal
        return MENU_PRINCIPAL

# Función para manejar el feedback
async def handle_feedback(update: Update, context: CallbackContext) -> int:
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        lang = user_data.get(user_id, {}).get('language', 'es')
        name = user_data.get(user_id, {}).get('name', '')
        
        # Guardar la calificación
        rating = int(query.data.split('_')[1])
        user_data[user_id]['feedback'] = rating
        save_data()
        
        # Agradecer el feedback
        try:
            await query.message.edit_text(
                get_text('thanks_feedback', lang, name)
            )
            
            # Volver al menú principal después de un breve delay
            await query.message.reply_text(
                get_text('what_else', lang, name),
                reply_markup=await create_main_menu_markup(lang)
            )
        except Exception as e:
            logger.error(f"Error al editar mensaje en feedback: {e}")
            # Si falla, enviar un nuevo mensaje
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text('thanks_feedback', lang, name)
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text('what_else', lang, name),
                reply_markup=await create_main_menu_markup(lang)
            )
        
        return MENU_PRINCIPAL
    except Exception as e:
        logger.error(f"Error en handle_feedback: {e}")
        # En caso de error, volver al menú principal
        try:
            user_id = update.effective_user.id
            lang = user_data.get(user_id, {}).get('language', 'es')
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text('what_else', lang, user_data.get(user_id, {}).get('name', '')),
                reply_markup=await create_main_menu_markup(lang)
            )
        except Exception as inner_e:
            logger.error(f"Error crítico en handle_feedback: {inner_e}")
        return MENU_PRINCIPAL

# Función para manejar comandos desconocidos
async def unknown(update: Update, context: CallbackContext) -> None:
    try:
        if update.message and update.message.text == "/start":
            return await start(update, context)
            
        user_id = update.effective_user.id
        lang = user_data.get(user_id, {}).get('language', 'es')
        name = user_data.get(user_id, {}).get('name', '')
        
        await update.message.reply_text(
            get_text('unknown_command', lang, name)
        )
    except Exception as e:
        logger.error(f"Error en unknown: {e}")
        # En caso de error, intentar recuperarse
        try:
            if update.message:
                await update.message.reply_text("Lo siento, ha ocurrido un error. Por favor intente con /start")
        except Exception as inner_e:
            logger.error(f"Error crítico en unknown: {inner_e}")

# Función para manejar errores
async def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if update.effective_user:
            user_id = update.effective_user.id
            lang = user_data.get(user_id, {}).get('language', 'es')
            
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
        
# Función para limpiar mensajes antiguos
async def clean_old_messages(context: CallbackContext):
    for user_id, data in context.chat_data.items():
        if 'last_bot_messages' in data:
            for msg_id in data['last_bot_messages']:
                try:
                    await context.bot.delete_message(chat_id=user_id, message_id=msg_id)
                except Exception as e:
                    logger.debug(f"No se pudo eliminar mensaje antiguo: {e}")
            data['last_bot_messages'] = []

def main() -> None:
    # Cargar datos guardados
    load_data()
    
    # Actualizar traducciones para las nuevas opciones
    update_translations()
    
    # Reemplaza con tu token real
    token = os.environ.get("TELEGRAM_TOKEN", "7550776917:AAGGRdAXV4_iNJOaJNMcApll2uh7jeRJ_nk")
    application = Application.builder().token(token).build()

    # Configurar el ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_language)],
            IDIOMA: [CallbackQueryHandler(handle_language_selection, pattern=r"^lang_")],
            MENU_PRINCIPAL: [
                CallbackQueryHandler(handle_main_menu_callback, pattern=r"^menu_|^resume_"),
                CommandHandler("menu", handle_menu),
                CommandHandler("help", handle_help),
                CommandHandler("contacto", handle_contact),
                CommandHandler("idioma", handle_language_command),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unknown),
            ],
            SUBMENU: [
                CallbackQueryHandler(handle_submenu_callback),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unknown),
            ],
            FEEDBACK: [
                CallbackQueryHandler(handle_feedback, pattern=r"^feedback_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unknown),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("help", handle_help),
            CommandHandler("menu", handle_menu),
            CommandHandler("contacto", handle_contact),
            CommandHandler("idioma", handle_language_command),
            MessageHandler(filters.COMMAND, unknown),
            MessageHandler(filters.TEXT & ~filters.COMMAND, unknown)
        ],
        name="main_conversation",
        persistent=False,
        per_message=False
    )

    # Agregar manejadores
    application.add_handler(conv_handler)
    
    # Comandos adicionales fuera de la conversación
    application.add_handler(CommandHandler("info", handle_info))
    
    # Manejador de errores
    application.add_error_handler(error_handler)
    
    # Intentar programar limpieza periódica si está disponible el JobQueue
    try:
        job_queue = application.job_queue
        if job_queue:
            job_queue.run_repeating(clean_old_messages, interval=3600)
    except Exception as e:
        logger.warning(f"No se pudo configurar el JobQueue: {e}")
        logger.info("Para usar JobQueue, instala python-telegram-bot[job-queue]")

    # Iniciar el bot
    application.run_polling()

if __name__ == '__main__':
    main()