import logging
import asyncio
import secrets
import string
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import sqlite3


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ФИКСИРОВАННЫЕ ПАРЫ (кто → кому дарит)
FIXED_PAIRS = {
    "@kattwuuq": "@paribad0",  # Катя Трофимова → Диме Шаповаленко
    "@leonid565": "@RinatUwU0",  # Леня Хлусов → Саше Быковскому
    "@tupokk": "@IQwerty69l0",  # Илья Степанников → Артему Калинкину
    "@FibeeL": "@rimarrii0",  # Егор Фазутов → Соне Денисовой
    "@Saffex12344321": "@Sklifosofskaya0",  # Марсель Иржанов → Алене Токаревой
    "@dev_maber": "@maryryri0",  # Лев Шинкоренко → Маше Астранкиной
    "@maryryri": "@chakchakpro0",  # Маша Астранкина → Арине Бакиевой
    "@RinatUwU": "@zxqwvlz0",  # Саша Быковский → Лизе Пикаловой
    "@alyyya_a": "@Opaapopaa0",  # Аля Кучерук → Димке Скворцову
    "@Un_knowing": "@vascosto0",  # Лера Девятко → Стасу Сладкову
    "@IQwerty69l": "@Saffex123443210",  # Артем Калинкин → Марселю Иржанову
    "@rimarrii": "@absent50cent0",  # Соня Денисова → Тане Романейко
    "@Opaapopaa": "@Ikarnas0",  # Димка Скворцов → Вове Трофимову
    "@vascosto": "@FibeeL0",  # Стас Сладков → Егору Фазутову
    "@paribad": "@alyyya_a000",  # Дима Шаповаленко → Але Кучерук
    "@Ikarnas": "@Anna_z290",  # Вова Трофимов → Ане Зориной
    "@Anna_z29": "@Aasi_s0",  # Аня Зорина → Насте Кудисовой
    "@slaffee": "@dev_maber0",  # Марина Кузиняткина → Льву Шинкоренко
    "@fekjii": "@Un_knowing0",  # Лиза Рыскаль → Лере Девятко
    "@Aasi_s": "@Wififl0",  # Настя Кудисова → Соне Валиахметовой
    "@zxqwvlz": "@leonid5650",  # Лиза Пикалова → Лене Хлусову
    "@Wififl": "@tupokk0",  # Соня Валиахметова → Илье Степанникову
    "@absent50cent": "@kattwuuq0",  # Таня Романейко → Кате Трофимовой
    "@chakchakpro": "@Sofacritik0",  # Арина Бакиева → Диме Богатыреву
    "@Sofacritik": "@slaffee00",  # Дима Богатырев → Марине Кузиняткиной
    "@Sklifosofskaya": "@fekjii0",  # Алена Токарева → Лизе Рыскаль
    "@sivanera": "@alyyya_a0",  # Арина Симонова → Але Кучерук
    "larisa_alexandrovna": "@RinatUwU0",  # Лариса Александровна → Саше Быковскому
}

# Полные имена для красивого отображения
FULL_NAMES = {
    "@kattwuuq": "Катя Трофимова",
    "@leonid565": "Леня Хлусов",
    "@tupokk": "Илья Степанников",
    "@FibeeL": "Егор Фазутов",
    "@Saffex12344321": "Марсель Иржанов",
    "@dev_maber": "Лев Шинкоренко",
    "@maryryri": "Маша Астранкина",
    "@RinatUwU": "Саша Быковский",
    "@alyyya_a": "Аля Кучерук",
    "@Un_knowing": "Лера Девятко",
    "@IQwerty69l": "Артем Калинкин",
    "@rimarrii": "Соня Денисова",
    "@Opaapopaa": "Димка Скворцов",
    "@vascosto": "Стас Сладков",
    "@paribad": "Дима Шаповаленко",
    "@Ikarnas": "Вова Трофимов",
    "@Anna_z29": "Аня Зорина",
    "@slaffee": "Марина Кузиняткина",
    "@fekjii": "Лиза Рыскаль",
    "@Aasi_s": "Настя Кудисова",
    "@zxqwvlz": "Лиза Пикалова",
    "@Wififl": "Соня Валиахметова",
    "@absent50cent": "Таня Романейко",
    "@chakchakpro": "Арина Бакиева",
    "@Sofacritik": "Дима Богатырев",
    "@Sklifosofskaya": "Алена Токарева",
    "@sivanera": "Арина Симонова",
    "larisa_alexandrovna": "Лариса Александровна",
}

# Настройки бота
BOT_TOKEN = "8060657593:AAEmYvrtWE5iLwCikaDna3ZGtPcUs2eYzRg"
ADMIN_CHAT_ID = "@sivanera"  # Для уведомлений

# АБСОЛЮТНО СЛУЧАЙНЫЙ КОД БЕЗ РОЖДЕСТВА
GROUP_CODE = "TK8P4Q2R9M"


class SecretSantaBot:
    def __init__(self):
        self.db_conn = sqlite3.connect('secret_santa.db', check_same_thread=False)
        self.init_db()
        self.registered_users = set()

    def init_db(self):
        """Инициализация базы данных"""
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                full_name TEXT,
                recipient_username TEXT,
                recipient_full_name TEXT,
                notified BOOLEAN DEFAULT FALSE,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.db_conn.commit()

    def generate_random_id(self):
        """Генерация абсолютно случайного ID"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(12))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        username = f"@{user.username}" if user.username else None

        if not username:
            await update.message.reply_text(
                "❌ *Внимание!*\n\n"
                "Для участия у вас должен быть установлен *username* в Telegram.\n\n"
                "📱 *Как установить username:*\n"
                "1. Откройте настройки Telegram\n"
                "2. Перейдите в раздел 'Username'\n"
                "3. Установите уникальное имя\n"
                "4. Вернитесь и нажмите /start\n\n"
                f"🆔 *Код сессии:* `{GROUP_CODE}`",
                parse_mode='Markdown'
            )
            return

        cursor = self.db_conn.cursor()

        # Регистрируем пользователя
        if username not in self.registered_users:
            self.registered_users.add(username)
            logger.info(f"Зарегистрирован новый пользователь: {username}")

        # Проверяем, есть ли пользователь в фиксированных парах
        if username in FIXED_PAIRS:
            recipient_username = FIXED_PAIRS[username]
            recipient_full_name = FULL_NAMES.get(recipient_username, "Участник")

            # Сохраняем в базу
            cursor.execute(
                '''INSERT OR REPLACE INTO users 
                (username, full_name, recipient_username, recipient_full_name) 
                VALUES (?, ?, ?, ?)''',
                (username, FULL_NAMES.get(username, "Участник"), recipient_username, recipient_full_name)
            )
            self.db_conn.commit()

        # Показываем статус
        await self.show_welcome_message(update)

    async def show_welcome_message(self, update: Update):
        """Показывает приветственное сообщение"""
        registered_count = len(self.registered_users)
        total_count = len(FIXED_PAIRS)

        keyboard = [
            [InlineKeyboardButton("📖 Правила", callback_data="rules")],
            [InlineKeyboardButton("❓ Вопросы", callback_data="faq")],
            [InlineKeyboardButton("👥 Статус", callback_data="status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = (
            "🎲 *Добро пожаловать в игру!*\n\n"
            f"🆔 *Код сессии:* `{GROUP_CODE}`\n\n"
            f"📊 *Статус регистрации:*\n"
            f"✅ *Зарегистрировано:* {registered_count}/{total_count}\n\n"
            "⏰ *Результаты будут отправлены через 6 часов*\n\n"
            "_Ожидайте уведомления..._"
        )

        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_recipient(self, update: Update, recipient_username: str, recipient_full_name: str):
        """Показывает получателя подарка"""
        if recipient_username.startswith("@"):
            keyboard = [
                [InlineKeyboardButton(
                    f"📨 Написать {recipient_full_name}",
                    url=f"https://t.me/{recipient_username[1:]}"
                )]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message_text = (
                "🎯 *Результаты распределения:*\n\n"
                "✨ *Вы дарите подарок:*\n"
                f"🎁 *{recipient_full_name}* {recipient_username}\n\n"
                "_Нажмите на кнопку ниже, чтобы написать получателю_"
            )
        else:
            keyboard = []
            reply_markup = InlineKeyboardMarkup(keyboard)

            message_text = (
                "🎯 *Результаты распределения:*\n\n"
                "✨ *Вы дарите подарок:*\n"
                f"🎁 *{recipient_full_name}*\n\n"
                "_Свяжитесь с организатором для передачи подарка_"
            )

        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()

        if query.data == "rules":
            rules_text = (
                "📖 *Правила игры:*\n\n"
                "💰 *Бюджет:* 500-1000 рублей\n"
                "📅 *Срок:* до 25 декабря\n"
                "🤫 *Инкогнито:* обязательно\n\n"
                "🎁 *Идеи для подарков:*\n"
                "• Книги\n• Сладости\n• Косметика\n"
                "• Настольные игры\n• Аксессуары"
            )
            await query.edit_message_text(
                rules_text,
                parse_mode='Markdown'
            )

        elif query.data == "faq":
            faq_text = (
                "❓ *Частые вопросы:*\n\n"
                "🤔 *Когда узнаю кому дарю?*\n"
                "Через 6 часов после старта\n\n"
                "📦 *Как передать подарок?*\n"
                "Анонимно договоритесь о встрече\n\n"
                "🎭 *Можно раскрыться?*\n"
                "Только после вручения подарков"
            )
            await query.edit_message_text(
                faq_text,
                parse_mode='Markdown'
            )

        elif query.data == "status":
            registered_count = len(self.registered_users)
            total_count = len(FIXED_PAIRS)

            status_text = (
                "📊 *Статус регистрации:*\n\n"
                f"🆔 *Код сессии:* `{GROUP_CODE}`\n"
                f"👥 *Всего участников:* {total_count}\n"
                f"✅ *Зарегистрировано:* {registered_count}\n"
                f"⏳ *Осталось:* {total_count - registered_count}\n\n"
                "⏰ *Результаты через 6 часов*"
            )
            await query.edit_message_text(
                status_text,
                parse_mode='Markdown'
            )

    async def send_notifications(self, context: ContextTypes.DEFAULT_TYPE):
        """Отправка уведомлений всем участникам через 6 часов"""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT username, recipient_username, recipient_full_name FROM users WHERE notified = FALSE")
        users = cursor.fetchall()

        notified_count = 0

        for username, recipient_username, recipient_full_name in users:
            try:
                if username.startswith("@"):
                    keyboard = [
                        [InlineKeyboardButton(
                            f"📨 Написать {recipient_full_name}",
                            url=f"https://t.me/{recipient_username[1:]}"
                        )]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    message_text = (
                        "🎯 *Результаты распределения:*\n\n"
                        "✨ *Вы дарите подарок:*\n"
                        f"🎁 *{recipient_full_name}* {recipient_username}\n\n"
                        "_Нажмите на кнопку ниже, чтобы написать получателю_"
                    )

                    await context.bot.send_message(
                        chat_id=username,
                        text=message_text,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    # Для пользователей без username
                    await context.bot.send_message(
                        chat_id=ADMIN_CHAT_ID,
                        text=f"📨 {username} дарит: {recipient_full_name}",
                        parse_mode='Markdown'
                    )

                cursor.execute(
                    "UPDATE users SET notified = TRUE WHERE username = ?",
                    (username,)
                )
                self.db_conn.commit()

                notified_count += 1
                logger.info(f"Уведомление отправлено для {username}")

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Ошибка отправки для {username}: {e}")

        # Уведомление администратору
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"✅ Распределение завершено! Уведомлено {notified_count} участников",
            parse_mode='Markdown'
        )

    def setup_participants(self):
        """Настройка участников в базе данных"""
        cursor = self.db_conn.cursor()

        # Очищаем старые данные
        cursor.execute("DELETE FROM users")

        # Добавляем всех участников с фиксированными парами
        for giver_username, recipient_username in FIXED_PAIRS.items():
            recipient_full_name = FULL_NAMES.get(recipient_username, "Участник")
            giver_full_name = FULL_NAMES.get(giver_username, "Участник")

            cursor.execute(
                '''INSERT OR REPLACE INTO users 
                (username, full_name, recipient_username, recipient_full_name) 
                VALUES (?, ?, ?, ?)''',
                (giver_username, giver_full_name, recipient_username, recipient_full_name)
            )

        self.db_conn.commit()
        logger.info(f"Настроено {len(FIXED_PAIRS)} участников")

        # Проверяем уникальность получателей
        recipients = list(FIXED_PAIRS.values())
        unique_recipients = set(recipients)

        print("\n" + "=" * 60)
        print("🎲 НАСТРОЙКА СИСТЕМЫ РАСПРЕДЕЛЕНИЯ")
        print("=" * 60)
        print(f"🆔 АБСОЛЮТНО СЛУЧАЙНЫЙ КОД: {GROUP_CODE}")
        print(f"👥 Участников: {len(FIXED_PAIRS)}")
        print(f"🎯 Уникальных получателей: {len(unique_recipients)}")
        print(f"✅ Проверка: {'ВСЕ УНИКАЛЬНЫ' if len(recipients) == len(unique_recipients) else 'ЕСТЬ ПОВТОРЫ!'}")
        print("\n📋 РАСПРЕДЕЛЕНИЕ:")
        print("-" * 40)
        for giver, recipient in FIXED_PAIRS.items():
            giver_name = FULL_NAMES.get(giver, giver)
            recipient_name = FULL_NAMES.get(recipient, recipient)
            print(f"➡️ {giver_name} → {recipient_name}")
        print("=" * 60)
        print("\n🔗 ОБЩАЯ ССЫЛКА ДЛЯ ВСЕХ:")
        print(f"t.me/over_secret_santa_2026_bot?start={GROUP_CODE}")
        print("=" * 60)

    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для администратора"""
        user = update.effective_user
        if f"@{user.username}" != ADMIN_CHAT_ID:
            return

        cursor = self.db_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE notified = TRUE")
        notified_count = cursor.fetchone()[0]

        registered_count = len(self.registered_users)
        total_count = len(FIXED_PAIRS)

        status_text = (
            f"📊 *Статус системы:*\n\n"
            f"🆔 *Код сессии:* `{GROUP_CODE}`\n"
            f"👥 *Всего участников:* {total_count}\n"
            f"✅ *Зарегистрировано:* {registered_count}\n"
            f"⏳ *Осталось:* {total_count - registered_count}\n"
            f"🔔 *Уведомленных:* {notified_count}\n\n"
            f"⏰ *Уведомления через 6 часов*"
        )

        await update.message.reply_text(status_text, parse_mode='Markdown')

    async def schedule_notifications(self, application):
        """Планировщик отправки уведомлений через 6 часов"""
        notification_time = datetime.now() + timedelta(hours=6)

        application.job_queue.run_once(
            self.send_notifications,
            notification_time,
            name="distribution_notifications"
        )

        logger.info(f"Уведомления запланированы на {notification_time}")


async def main():
    """Основная функция"""
    bot = SecretSantaBot()
    bot.setup_participants()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CallbackQueryHandler(bot.button_handler))
    application.add_handler(CommandHandler("admin", bot.admin_command))

    await bot.schedule_notifications(application)

    logger.info("Бот запущен!")
    print("\n🎲 СИСТЕМА РАСПРЕДЕЛЕНИЯ ЗАПУЩЕНА!")
    print(f"🆔 АБСОЛЮТНО СЛУЧАЙНЫЙ КОД: {GROUP_CODE}")
    print(f"👥 Участников: {len(FIXED_PAIRS)}")
    print("⏰ Уведомления через 6 часов")
    print(f"🔗 ОБЩАЯ ССЫЛКА ДЛЯ ВСЕХ:")
    print(f"https://t.me/your_bot_username?start={GROUP_CODE}")
    print("\n✨ Отправьте эту ссылку в группу!")

    await application.run_polling()


if __name__ == "__main__":

    asyncio.run(main())
