import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, Message
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = ""  # Замените на ваш токен
ADMIN_ID = 0    # Замените на ID администратора
bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_FILE = "teleusers.db"

class BD:
    def __init__(self, db_file=DB_FILE):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS teleusers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE
            )
        """)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def user_exists(self, username):
        self.cursor.execute("SELECT 1 FROM teleusers WHERE username = ?", (username,))
        return self.cursor.fetchone() is not None

    def add_user(self, username):
        try:
            self.cursor.execute("INSERT INTO teleusers (username) VALUES (?)", (username,))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_user(self, username):
        self.cursor.execute("DELETE FROM teleusers WHERE username = ?", (username,))
        self.conn.commit()

class AdminActions(StatesGroup):
    waiting_for_add_username = State()
    waiting_for_remove_username = State()

def admin_keyboard():
    button1 = KeyboardButton(text="Добавить пользователя")
    button2 = KeyboardButton(text="Удалить пользователя")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[button1, button2]])
    return keyboard

@dp.message(CommandStart())
async def start(message: Message):
    db = BD()
    username = message.from_user.username
    if db.user_exists(username):
        await message.answer("Вы уже зарегистрированы.")
    elif message.from_user.id == ADMIN_ID:
        await message.answer("Вы администратор. Для добавления или удаления пользователя используйте кнопки ниже.", reply_markup=admin_keyboard())
    else:
        await message.answer("Вы не добавлены в систему. Обратитесь к администратору.")
    db.close()

@dp.message(F.text == "Добавить пользователя")
async def add_user_button(message: Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.reply("Введите username пользователя для добавления:")
        await state.set_state(AdminActions.waiting_for_add_username)

@dp.message(F.text == "Удалить пользователя")
async def remove_user_button(message: Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.reply("Введите username пользователя для удаления:")
        await state.set_state(AdminActions.waiting_for_remove_username)

@dp.message(AdminActions.waiting_for_add_username)
async def add_user_from_input(message: Message, state: FSMContext):
    db = BD()
    username = message.text
    if db.add_user(username):
        await message.reply(f"Пользователь с username {username} успешно добавлен!")
        # Уведомляем пользователя о том, что он добавлен
        await bot.send_message(username, "Вы успешно добавлены в систему! Теперь вы можете использовать бота.")
    else:
        await message.reply(f"Пользователь с username {username} уже существует или ошибка добавления.")
    db.close()
    await state.clear()

@dp.message(AdminActions.waiting_for_remove_username)
async def remove_user_from_input(message: Message, state: FSMContext):
    db = BD()
    username = message.text
    if db.user_exists(username):
        db.remove_user(username)
        await message.reply(f"Пользователь с username {username} успешно удален!")
    else:
        await message.reply(f"Пользователь с username {username} не найден.")
    db.close()
    await state.clear()

@dp.message()
async def handle_message(message: types.Message):
    db = BD()
    username = message.from_user.username
    if db.user_exists(username):
        await message.answer(f"Вы авторизованы. Ваше сообщение: {message.text}")
    else:
        await message.answer("Вы не добавлены в систему. Обратитесь к администратору.")
    db.close()

if __name__ == "__main__":
    dp.run_polling(bot)
