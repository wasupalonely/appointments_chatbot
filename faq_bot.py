from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Función para manejar el comando /start
async def start(update: Update, context: CallbackContext) -> None:
    # Crear un teclado personalizado con las categorías principales
    keyboard = [
        ['Horarios', 'Contacto'],
        ['Servicios', 'Ubicación']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        '¡Hola! Soy tu asistente de preguntas frecuentes. ¿En qué puedo ayudarte hoy?',
        reply_markup=reply_markup
    )

# Función para manejar las categorías principales
async def handle_main_menu(update: Update, context: CallbackContext) -> None:
    text = update.message.text

    if text == 'Horarios':
        # Mostrar submenú de horarios
        keyboard = [
            ['Horario de atención', 'Horario de citas'],
            ['Volver al menú principal']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            'Selecciona una opción relacionada con horarios:',
            reply_markup=reply_markup
        )
    elif text == 'Contacto':
        # Mostrar submenú de contacto
        keyboard = [
            ['Teléfono', 'Correo electrónico'],
            ['Volver al menú principal']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            'Selecciona una opción relacionada con contacto:',
            reply_markup=reply_markup
        )
    elif text == 'Servicios':
        # Mostrar submenú de servicios
        keyboard = [
            ['Consulta general', 'Especialidades'],
            ['Volver al menú principal']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            'Selecciona una opción relacionada con servicios:',
            reply_markup=reply_markup
        )
    elif text == 'Ubicación':
        # Mostrar submenú de ubicación
        keyboard = [
            ['Dirección', 'Cómo llegar'],
            ['Volver al menú principal']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            'Selecciona una opción relacionada con ubicación:',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text('Por favor, selecciona una opción del menú.')

# Función para manejar las opciones de los submenús
async def handle_submenu(update: Update, context: CallbackContext) -> None:
    text = update.message.text

    if text == 'Horario de atención':
        await update.message.reply_text('Nuestro horario de atención es de lunes a viernes de 8:00 AM a 6:00 PM.')
    elif text == 'Horario de citas':
        await update.message.reply_text('Las citas están disponibles de lunes a viernes de 9:00 AM a 5:00 PM.')
    elif text == 'Teléfono':
        await update.message.reply_text('Puedes contactarnos al número 123-456-7890.')
    elif text == 'Correo electrónico':
        await update.message.reply_text('Nuestro correo electrónico es info@clinica.com.')
    elif text == 'Consulta general':
        await update.message.reply_text('Ofrecemos consultas generales de lunes a viernes. ¡Agenda tu cita!')
    elif text == 'Especialidades':
        await update.message.reply_text('Contamos con especialidades en Cardiología, Dermatología y Pediatría.')
    elif text == 'Dirección':
        await update.message.reply_text('Estamos ubicados en Calle Falsa 123, Ciudad, País.')
    elif text == 'Cómo llegar':
        await update.message.reply_text('Puedes llegar en transporte público o en auto. ¡Te esperamos!')
    elif text == 'Volver al menú principal':
        await start(update, context)
    else:
        await update.message.reply_text('Por favor, selecciona una opción del menú.')

def main() -> None:
    # Reemplaza 'TU_TOKEN_AQUI' con el token que te dio BotFather
    application = Application.builder().token("7956078143:AAFB6aKiCMgdaOLfRCBlf18Xh5K-VMMjzw8").build()

    # Maneja el comando /start
    application.add_handler(CommandHandler("start", start))

    # Maneja las opciones del menú principal
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))

    # Maneja las opciones de los submenús
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_submenu))

    # Inicia el bot
    application.run_polling()

if __name__ == '__main__':
    main()