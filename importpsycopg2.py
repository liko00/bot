import psycopg2
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage


#https://t.me/aiogrampgadmin_bot

conn = psycopg2.connect(
    host="localhost",
    database="bot",
    user="postgres",
    password="871336",
    port="5432"
)
cursor = conn.cursor()

bot = Bot(token="6006469701:AAG-KwjBr1lLXRbLCP_WivCKHznYTd_YWSw")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    username = State()
    name = State()
    visits = State()
    days = State()
    time = State()
    info_username = State()

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Hi\nPlease type /newprofile, /info, /deleteprofile or /reset", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add("/newprofile", "/deleteprofile", "/info", "/reset"))

@dp.message_handler(commands=['newprofile'])
async def process_newprofile_command(message: types.Message):
    await message.reply("Enter your name:")
    await Form.name.set()

@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply("Enter your username:")
    await Form.username.set()

@dp.message_handler(state=Form.username)
async def process_username(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    await message.reply("Enter number of visits:")
    await Form.visits.set()


@dp.message_handler(state=Form.visits)
async def process_visits(message: types.Message, state: FSMContext):
    await state.update_data(visits=message.text)
    await message.reply("Enter days of the week:")
    await Form.next()

@dp.message_handler(state=Form.days)
async def process_days(message: types.Message, state: FSMContext):
    await state.update_data(days=message.text)
    await message.reply("Enter time:")
    await Form.next()

@dp.message_handler(state=Form.time)
async def process_time(message: types.Message, state: FSMContext):
    await state.update_data(time=message.text)
    await message.reply("Thank you! Write /info to view about the profile")
    user_data = await state.get_data()
    name = user_data['name']
    username = user_data['username']
    visits = user_data['visits']
    days = user_data['days']
    time = user_data['time']
    # Save the user data to the database
    cursor.execute("INSERT INTO users (name, username, visits, days, time) VALUES (%s, %s, %s, %s, %s)", (name, username, visits, days, time))
    conn.commit()
    await state.finish()


@dp.message_handler(commands=['reset'])
async def reset_state(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("State has been reset. Starting from the beginning...")
    await process_start_command(message)

@dp.message_handler(commands=['info'])
async def process_info_command(message: types.Message):
   
    await message.reply("Please enter your username:")

    # Set the state to get the user's username for the info command
    await Form.info_username.set()

@dp.message_handler(state=Form.info_username)
async def process_username_for_info(message: types.Message, state: FSMContext):
    # Get the username entered by the user
    username = message.text

    try:
        # Get user data from database based on their username
        cursor.execute("SELECT name, username, visits, days, time FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        # Check if user exists in the database
        if result is not None:
            # Create a message with user info
            name, username, visits, days, time = result
            message_text = md.text(
                md.text("Name:", md.bold(name)),
                md.text("Username:", md.bold(username)),
                md.text("Visits:", md.bold(visits)),
                md.text("Days of the week:", md.bold(days)),
                md.text("Time:", md.bold(time)),
                sep='\n'
            )
            # Send the message to the user
            await message.reply(message_text, parse_mode=ParseMode.MARKDOWN)
        else:
            # If the user doesn't exist in the database, send a message saying so
            await message.reply("User not found.")
    except:
        # If an exception is raised, send an error message to the user
        await message.reply("An error occurred while processing your request. Please try again later.")

    # Finish the form state for the info command
    await state.finish()

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp)

