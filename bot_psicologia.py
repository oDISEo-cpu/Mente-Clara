import json
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

TOKEN = "8203941890:AAEaS-7vN9gzTe_9XNiAb5yMewZzG_QPs6Q"

ARCHIVO_CITAS = "citas.json"

menu_principal = [
    ["🧠 Servicios", "📅 Agendar cita"],
    ["📍 Ubicación", "📞 Contacto"]
]

def cargar_citas():
    """Carga las citas desde el archivo JSON."""
    try:
        with open(ARCHIVO_CITAS, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def guardar_citas(citas):
    """Guarda las citas en el archivo JSON."""
    with open(ARCHIVO_CITAS, "w") as f:
        json.dump(citas, f, indent=4)

async def enviar_recordatorio(app, user_id, nombre, fecha_str):
    """Envía un mensaje recordatorio al usuario."""
    await app.bot.send_message(
        chat_id=user_id,
        text=f"⏰ *Recordatorio de cita*\n\nHola {nombre}, te recordamos tu cita psicológica programada para hoy a las {fecha_str.split()[-1]} 🧠",
        parse_mode="Markdown"
    )

def programar_recordatorio(app, user_id, nombre, fecha_cita):
    """Programa un recordatorio 1 hora antes de la cita."""
    scheduler = BackgroundScheduler(timezone="America/Caracas")
    hora_recordatorio = fecha_cita - timedelta(hours=1)
    scheduler.add_job(
        enviar_recordatorio,
        "date",
        run_date=hora_recordatorio,
        args=[app, user_id, nombre, fecha_cita.strftime("%d/%m/%Y %H:%M")]
    )
    scheduler.start()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Bienvenido al *Consultorio Psicológico Serenamente*.\n\n"
        "Selecciona una opción del menú:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(menu_principal, resize_keyboard=True)
    )

async def mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    user_id = update.message.chat_id

    if texto == "🧠 Servicios":
        await update.message.reply_text(
            "Ofrecemos los siguientes servicios:\n"
            "1️⃣ Terapia individual\n"
            "2️⃣ Terapia de pareja\n"
            "3️⃣ Orientación vocacional\n"
            "4️⃣ Atención psicológica online\n\n"
            "Por favor, responde con el *número* del servicio que te interesa.",
            parse_mode="Markdown"
        )
        context.user_data["esperando_servicio"] = True
        return

    if context.user_data.get("esperando_servicio"):
        if texto in ["1", "2", "3", "4"]:
            context.user_data["esperando_servicio"] = False
            servicios = {
                "1": "Terapia individual",
                "2": "Terapia de pareja",
                "3": "Orientación vocacional",
                "4": "Atención psicológica online"
            }
            servicio = servicios[texto]
            await update.message.reply_text(
                f"Has seleccionado: *{servicio}*.\n\n¿Deseas agendar una cita para este servicio?\nEscribe tu *nombre completo* y la *fecha deseada*.\n\nEjemplo:\n`María López - 25/10/2025 15:00`",
                parse_mode="Markdown"
            )
            context.user_data["esperando_cita"] = servicio
            return
        else:
            await update.message.reply_text("Por favor, selecciona un número del 1 al 4. 😊")
            return

    if context.user_data.get("esperando_cita"):
        servicio = context.user_data["esperando_cita"]
        try:
            nombre, fecha_str = texto.split(" - ")
            fecha_cita = datetime.strptime(fecha_str.strip(), "%d/%m/%Y %H:%M")
        except ValueError:
            await update.message.reply_text(
                "❌ Formato incorrecto. Usa este formato:\n`Nombre Apellido - dd/mm/aaaa hh:mm`",
                parse_mode="Markdown"
            )
            return

        citas = cargar_citas()
        citas.append({
            "user_id": user_id,
            "nombre": nombre,
            "servicio": servicio,
            "fecha": fecha_cita.strftime("%d/%m/%Y %H:%M")
        })
        guardar_citas(citas)

        programar_recordatorio(context.application, user_id, nombre, fecha_cita)

        await update.message.reply_text(
            f"✅ Cita registrada correctamente.\n\n👤 *Paciente:* {nombre}\n🧠 *Servicio:* {servicio}\n📅 *Fecha:* {fecha_cita.strftime('%d/%m/%Y %H:%M')}\n\nTe enviaremos un recordatorio 1 hora antes de tu cita. 😊",
            parse_mode="Markdown"
        )

        context.user_data.pop("esperando_cita", None)
        await update.message.reply_text(
            "¿Deseas hacer algo más?",
            reply_markup=ReplyKeyboardMarkup(menu_principal, resize_keyboard=True)
        )
        return

    if texto == "📅 Agendar cita":
        await update.message.reply_text(
            "Por favor, escribe tu *nombre completo* y la *fecha deseada*.\nEjemplo: `María López - 25/10/2025 15:00`",
            parse_mode="Markdown"
        )
        context.user_data["esperando_cita"] = "General"
        return

    elif texto == "📍 Ubicación":
        await update.message.reply_text(
            "📍 Estamos en: Sector Las Lagunas Campus Universitario, Vía Salom, Nirgua 3205, Yaracuy 9:00 AM - 5:00 PM."
        )

    elif texto == "📞 Contacto":
        await update.message.reply_text(
            "Puedes comunicarte con nosotros:\n📱 WhatsApp: +58 412 1234567\n✉️ Correo: contacto@serenamente.com"
        )

    else:
        await update.message.reply_text("No entiendo esa opción, por favor usa el menú. 😊")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensajes))
    print("🤖 Bot de Psicología ejecutándose correctamente...")
    app.run_polling()

if __name__ == "__main__":
    main()
