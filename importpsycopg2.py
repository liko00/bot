from turtle import update
import psycopg2
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import datetime, asyncio
from aiogram.utils import executor

#https://t.me/aiogrampgadmin_bot

conn = psycopg2.connect(
    host="localhost",
    database="aiogram",
    user="postgres",
    password="871336",
    port="5432"
)
cursor = conn.cursor()

bot = Bot(token="6006469701:AAG-KwjBr1lLXRbLCP_WivCKHznYTd_YWSw")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

async def send_message_to_user(bot: Bot, user_id: int, message: str):
    await bot.send_message(user_id, message)

class Form(StatesGroup):
    username = State()
    name = State()
    visits = State()
    count = State()
    days = State()
    num_days = State()
    time = State()
    info_username = State()
    delete_username = State()
    visit = State()

    def __init__(self):
        self.times_selected = {}

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Hi\nPlease type /newprofile, /info, /deleteprofile or /reset. If you have a profile and you visited today then type /visit", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add("/newprofile", "/deleteprofile", "/info", "/reset", "/visit"))

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
    # Check if username exists in database
    username = message.text.strip()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    if user:
        await message.reply("This username already exists, please choose another one:")
        return
    else:
        await state.update_data(username=username)
        await message.reply("Enter number of visits:")
        await Form.visits.set()

@dp.message_handler(state=Form.visits)
async def process_visits(message: types.Message, state: FSMContext):
    visits = message.text.strip()
    if not visits.isdigit() or int(visits) <= 0:
        await message.reply("Please enter a valid integer for number of visits.")
        return
    else:
        visits = int(visits)
        await state.update_data(visits=visits)
        await Form.num_days.set()
        await message.reply("Select how many days of the week we want to visit:")


days_of_week = [
    ('Monday', 'monday'),
    ('Tuesday', 'tuesday'),
    ('Wednesday', 'wednesday'),
    ('Thursday', 'thursday'),
    ('Friday', 'friday'),
    ('Saturday', 'saturday'),
    ('Sunday', 'sunday')
]

# Create an inline keyboard markup for the days of the week
days_keyboard = InlineKeyboardMarkup(row_width=3)

# Add day selection buttons
days_buttons = [
    InlineKeyboardButton(day, callback_data=day) for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
]
days_keyboard.add(*days_buttons)

@dp.message_handler(state=Form.num_days)
async def process_num_days(message: types.Message, state: FSMContext):
    num_days = int(message.text)
    num_days = int(message.text)
    if num_days < 1:
        await message.reply("Sorry, the minimum value is 1. Please select again.")
        return
    elif num_days > 7:
        await message.reply("Sorry, the maximum value is 7. Please select again.")
        return
    await state.update_data(num_days=num_days)
    await message.reply("Please select the days of the week:", reply_markup=days_keyboard)
    await Form.days.set()

@dp.message_handler(state=Form.days)
async def process_days(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        days = data.get("days", [])
        selected_day = message.text
        if selected_day in days:
            await message.reply(f"{selected_day} has already been selected. Please choose a different day.")
            return
        days.append(selected_day)
        data["days"] = days
        num_days = data.get("num_days", 0)
        if len(days) >= num_days:
            # Store the selected days in the state
            await state.update_data(days=days)
            await Form.time.set()
            # Ask the user to select a time for each day of the week
            await message.reply("Please select the time for each day of the week:")
        else:
            await message.reply(f"Please select {num_days - len(days)} more day(s) of the week:", reply_markup=days_keyboard)

@dp.callback_query_handler(lambda callback_query: callback_query.data in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], state=Form.days)
async def process_callback_days(callback_query: types.CallbackQuery, state: FSMContext):
    # Get the selected day from the callback data
    selected_day = callback_query.data
    # Update the state with the selected day
    async with state.proxy() as data:
        days = data.get("days", [])
        if selected_day in days:
            await bot.answer_callback_query(callback_query.id, text=f"{selected_day} has already been selected. Please choose a different day.")
            return
        days.append(selected_day)
        data["days"] = days
        num_days = data.get("num_days", 0)
        if len(days) >= num_days:
            await state.update_data(days=selected_day)
            await bot.answer_callback_query(callback_query.id)
            await bot.send_message(callback_query.message.chat.id, f"You have selected {num_days} days: {', '.join(days)}")
            await Form.time.set()
            
            await bot.send_message(callback_query.message.chat.id, "Please select the time you want to visit (hour):", reply_markup=keyboard)
        else:
            remaining_days = [day for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] if day not in days]
            remaining_days_buttons = [
                InlineKeyboardButton(day, callback_data=day) for day in remaining_days
            ]
            days_keyboard = InlineKeyboardMarkup(row_width=3)
            days_keyboard.add(*remaining_days_buttons)
            await bot.answer_callback_query(callback_query.id)
            await bot.edit_message_text(f"Select {num_days - len(days)} more days. Remaining days:", callback_query.message.chat.id, callback_query.message.message_id, reply_markup=days_keyboard)

# Define the hours and minutes ranges
HOURS_RANGE = range(0, 24)
MINUTES_RANGE = range(0, 60)

# Create an inline keyboard markup for the hour and minute selection
keyboard = InlineKeyboardMarkup(row_width=6)

# Add hour selection buttons
hour_buttons = [InlineKeyboardButton(str(hour), callback_data=f"hour_{hour}") for hour in HOURS_RANGE]
keyboard.add(*hour_buttons)

@dp.message_handler(state=Form.time)
async def process_times(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        times_selected = state.times_selected
        days = data["days"]
        selected_time = message.text
        times_selected[selected_days] = selected_time
        selected_days = [
            value for name, value in days_of_week
            if name in message.text
        ]
        if len(times_selected) == len(days):
            # Store the selected times in the state
            await state.update_data(times=times_selected)
            # Display the summary to the user
            summary = "\n".join([f"{day}: {times_selected[day]}" for day in days])
            await message.reply(f"You have selected the following times:\n{summary}")
            # Move to the next state or finish the conversation
        else:
            # Ask the user to select the time for the next day
            next_day = [day for day in days if day not in times_selected][0]
            await message.reply(f"Please select the time for {next_day}:")


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('hour'), state=Form.time)
async def process_hour(callback_query: types.CallbackQuery, state: FSMContext):
    # Get the selected hour from the callback data
    hour = int(callback_query.data.split("_")[1])
    # Check that the hour value is within the valid range of 0 to 23
    if hour < 0 or hour > 23:
        await bot.answer_callback_query(callback_query.id, text="Invalid hour value. Please select a value between 0 and 23.")
        return
    # Update the state with the selected hour
    data = await state.get_data()
    data['hour'] = hour
    await state.set_data(data)
    # Create a new keyboard markup for selecting minutes
    keyboard = types.InlineKeyboardMarkup()
    # Add buttons for each possible minute value
    for minute in range(0, 60, 10):
        keyboard.add(types.InlineKeyboardButton(f"{minute:02d}", callback_data=f"minute_{minute}"))
    # Edit the message to show the selected hour and the new keyboard for selecting minutes
    await bot.edit_message_text(f"You selected {hour:02d}:00. Please select the minute:", callback_query.message.chat.id, callback_query.message.message_id, reply_markup=keyboard)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('minute'), state=Form.time)
async def process_minute(callback_query: types.CallbackQuery, state: FSMContext):
    # Get the selected minute from the callback data
    minute = int(callback_query.data.split("_")[1])
    # Update the state with the selected minute
    data = await state.get_data()
    data['minute'] = minute
    await state.set_data(data)
    # Edit the message to show the selected hour and minute
    data = await state.get_data()
    hour = data['hour']
    await bot.edit_message_text(f"You selected {hour:02d}:{minute:02d}.", callback_query.message.chat.id, callback_query.message.message_id)
    # Save the user data to the database
    user_data = await state.get_data()
    name = user_data['name']
    username = user_data['username']
    visits = user_data['visits']
    days = user_data['days']
    time = f"{hour:02d}:{minute:02d}"
    try:
        cursor.execute("INSERT INTO users (name, username, visits, days, time) VALUES (%s, %s, %s, %s, %s)", (name, username, visits, days, time))
        conn.commit()
        await bot.send_message(callback_query.message.chat.id, f"User data for {username} has been successfully saved.")
    except Exception as e:
        conn.rollback()
        await bot.send_message(callback_query.message.chat.id, "An error occurred while processing your request. Please try again later.")
        print(f"Error: {e}")
    # Finish the state machine
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


@dp.message_handler(commands=['deleteprofile'])
async def process_deleteprofile_command(message: types.Message):
    await message.reply("Please enter the username of the profile you want to delete:")

    # Set the state to get the user's username for the delete command
    await Form.delete_username.set()


@dp.message_handler(state=Form.delete_username)
async def process_username_for_delete(message: types.Message, state: FSMContext):
    # Get the username entered by the user
    username = message.text
    try:
        # Check if user exists in the database
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result is not None:
            # Delete the user data from the database
            cursor.execute("DELETE FROM users WHERE username = %s", (username,))

            conn.commit()
            await message.reply(f"The profile with username {username} has been deleted.")
        else:
            # If the user doesn't exist in the database, send a message saying so
            await message.reply("User not found.")
    except:
        # If an exception is raised, send an error message to the user
        await message.reply("An error occurred while processing your request. Please try again later.")

    # Finish the form state for the delete command
    await state.finish()

@dp.message_handler(commands=['visit'])
async def change_command_handler(message: types.Message):
    await message.reply("Please enter the username of the profile:")

    # Set the state to get the user's username for the delete command
    await Form.visit.set()

@dp.message_handler(state=Form.visit)
async def change_username_handler(message: types.Message, state: FSMContext):
    # Get the username entered by the user
    username = message.text
    try:
        # Check if user exists in the database
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result is not None:
            # Subtract one from the visits column for the user
            cursor.execute("UPDATE users SET visits = visits - 1 WHERE username = %s", (username,))

            conn.commit()
            await message.reply(f"The profile with username {username} has been updated.")
        else:
            # If the user doesn't exist in the database, send a message saying so
            await message.reply("User not found.")
    except:
        # If an exception is raised, send an error message to the user
        await message.reply("An error occurred while processing your request. Please try again later.")

    # Finish the form state for the delete command
    await state.finish()

  
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp)
    
