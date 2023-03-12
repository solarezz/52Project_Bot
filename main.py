import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from emoji_list import all_emoji
import aiomysql
import hashlib
import json
from config import TOKEN
from json import loads
from aiofiles import open as aiopen

# Здесь нужно заменить параметры на свои
DB_CONFIG = {
    'host': 'db4.myarena.ru',
    'user': 'u24939_universe',
    'password': 'Dbnz02082004',
    'db': 'u24939_universe',
}

pointer = lambda username: {
    "nickname": username,
    "password": "password",
    "user_id": user_id
}

# Инициализируем бота и хранилище состояний
#logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

online = []



# Описываем состояние для запроса логина
class Login(StatesGroup):
    waiting_for_login = State()

# Описываем состояние для запроса пароля
class Password(StatesGroup):
    waiting_for_password = State()

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    global user_id
    user_id = message.from_user.id
    firstname = message.from_user.username
    await message.reply("Привет! Введите свой никнейм:")
    with open("C:/IT/52Project/database.json", "r") as f_o:
        data_from_json = json.loads(f_o.read())

    if str(user_id) not in data_from_json:
            data_from_json[user_id] = pointer(firstname)

    with open("C:/IT/52Project/database.json", "w") as f_o:
        json.dump(data_from_json, f_o, indent=4, ensure_ascii=False)

    # Переходим в состояние ожидания логина
    await Login.waiting_for_login.set()

# Обработчик текстового сообщения
@dp.message_handler(state=Login.waiting_for_login)
async def process_login(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    # Получаем логин из сообщения
    with open("C:/IT/52Project/database.json", "r") as f_o:
        data_from_json = json.loads(f_o.read())
    login = message.text
    data_from_json[f"{user_id}"]["nickname"] = login
    with open("C:/IT/52Project/database.json", "w") as f_o:
        json.dump(data_from_json, f_o, indent=4, ensure_ascii=False)
    # Сохраняем логин в контексте состояния
    await state.update_data(login=login)

    # Просим ввести пароль
    await message.reply("Введите пароль:")

    # Переходим в состояние ожидания пароля
    await Password.waiting_for_password.set()

# Обработчик текстового сообщения
@dp.message_handler(state=Password.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    # Получаем пароль из сообщения
    user_id = message.from_user.id
    with open("C:/IT/52Project/database.json", "r") as f_o:
        data_from_json = json.loads(f_o.read())
    global password
    password = hashlib.md5(message.text.strip().encode( 'utf-8' ) ).hexdigest()
    data_from_json[f"{user_id}"]["password"] = password   

    with open("C:/IT/52Project/database.json", "w") as f_o:
        json.dump(data_from_json, f_o, indent=4, ensure_ascii=False)

    # Получаем логин из контекста состояния
    data = await state.get_data()
    login = data.get('login')

    # Устанавливаем соединение с базой данных
    async with aiomysql.create_pool(**DB_CONFIG) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Выполняем запрос на поиск пользователя в базе данных
                await cur.execute("SELECT * FROM accounts WHERE name=%s AND password=%s", (login, password))
                row = await cur.fetchone()

    # Проверяем, найден ли пользователь
    if row:
        ReplyKeyboardRemove()
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        bhouses = KeyboardButton('🏠ДОМА')
        bcars = KeyboardButton('🚗МАШИНЫ')
        bbiz = KeyboardButton('💼БИЗНЕСЫ')
        profile = KeyboardButton('👤ПРОФИЛЬ')
        binfo = KeyboardButton('❗ ИНФОРМАЦИЯ')
        markup.add(bhouses, bcars, bbiz, profile, binfo)
        await message.reply('✅ Успешный вход! Для начала пользования ботом, нажмите на кнопку "❗ ИНФОРМАЦИЯ".', reply_markup=markup)
    else:
        await message.reply("⛔ Неверный логин или пароль. Попробуйте еще раз.")

    # Сбрасываем состояние
    await state.finish()

@dp.message_handler(lambda msg: msg.text.startswith('❗ ИНФОРМАЦИЯ'))
async def information(message):
    await message.reply('❗ Информация о боте:\n\
Если вы поменяли ник в игре, то следует его поменять и в боте - /nick Ivan_Ivanov.\n\
Так же если вы сменили пароль в игре, то в боте тоже следует его поменять - /password QwErTy123\n\
\n\
dev: @solarezzov\n\
')

@dp.message_handler(commands=('password'))
async def setnick(message):
    with open("C:/IT/52Project/database.json", "r") as f_o:
            data_from_json = json.loads(f_o.read())
    user_id = message.from_user.id
    nick = data_from_json[f"{user_id}"]["nickname"]
    if message.text == "/password":
        await message.answer(f"{nick}, Вы оставили поле пустым!")
    else:
        user_id = message.from_user.id
        nick = data_from_json[f"{user_id}"]["nickname"]
        data_from_json[f"{user_id}"]["password"] = hashlib.md5(message.text[9:].strip().encode( 'utf-8' ) ).hexdigest()
        await message.answer(f'{nick}, вы сменили пароль на "{message.text[10:]}"')

        with open("C:/IT/52Project/database.json", "w") as f_o:
                json.dump(data_from_json, f_o, indent=4, ensure_ascii=False)

@dp.message_handler(commands=('nick'))
async def setnick(message):
    with open("C:/IT/52Project/database.json", "r") as f_o:
            data_from_json = json.loads(f_o.read())
    user_id = message.from_user.id
    nick = data_from_json[f"{user_id}"]["nickname"]
    if message.text == "/nick":
        await message.answer(f"{nick}, Вы оставили поле пустым!")
    for word in message.text:
        if word in all_emoji:
            await message.answer('⚠️ В нике запрещены эмоджи!')
            break
    else:
        user_id = message.from_user.id
        nick = data_from_json[f"{user_id}"]["nickname"]
        data_from_json[f"{user_id}"]["nickname"] = f"{message.text[6:]}"
        await message.answer(f'{nick}, вы сменили ник на "{message.text[6:]}"')

        with open("C:/IT/52Project/database.json", "w") as f_o:
                json.dump(data_from_json, f_o, indent=4, ensure_ascii=False)

@dp.message_handler(lambda msg: msg.text.startswith('🚗МАШИНЫ'))
async def houses_prf(message: types.Message):
    user_id = message.from_user.id
    with open("C:/IT/52Project/database.json", "r") as f_o:
        data_from_json = json.loads(f_o.read())

    username = data_from_json[f"{user_id}"]["nickname"]

    async with aiomysql.create_pool(**DB_CONFIG) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT vip, name FROM accounts WHERE name=%s", (username,))
                acc = await cur.fetchone()
                async with conn.cursor() as cur:
                    await cur.execute("SELECT taxes, owner, name FROM vehicles WHERE owner=%s", (username,))
                    car = await cur.fetchall()
        if(acc[0] == 1):
            if 4 in range(len(car)):
                    nickname = acc[1]
                    name_car = car[0][2]
                    car_paid_days = car[0][0]
                    car_paid_days2 = car[1][0]
                    name_car2 = car[1][2] 
                    car_paid_days3 = car[2][0]
                    name_car3 = car[2][2]
                    car_paid_days4 = car[3][0]
                    name_car4 = car[3][2]
                    car_paid_days5 = car[4][0]
                    name_car5 = car[4][2] 

                    profile_message = f"📋 {nickname}, информация по Вашим автомобилям:\n" \
                                f"1️⃣. Название автомобиля: {name_car}\n"\
                                    f"      Налог на автомобиль: {car_paid_days} рублей.\n"\
                                f"2️⃣. Название автомобиля: {name_car2}\n"\
                                    f"      Налог на автомобиль: {car_paid_days2} рублей.\n"\
                                f"3️⃣. Название автомобиля: {name_car3}\n"\
                                    f"      Налог на автомобиль: {car_paid_days3} рублей.\n"\
                                f"4️⃣. Название автомобиля: {name_car4}\n"\
                                    f"      Налог на автомобиль: {car_paid_days4} рублей.\n"\
                                f"5️⃣. Название автомобиля: {name_car5}\n"\
                                    f"      Налог на автомобиль: {car_paid_days5} рублей."
                                
                    await message.reply(profile_message)
            elif 3 in range(len(car)):    
                    nickname = acc[1]
                    name_car = car[0][2]
                    car_paid_days = car[0][0]
                    car_paid_days2 = car[1][0]
                    name_car2 = car[1][2] 
                    car_paid_days3 = car[2][0]
                    name_car3 = car[2][2]
                    car_paid_days4 = car[3][0]
                    name_car4 = car[3][2] 

                    profile_message = f"📋 {nickname}, информация по Вашим автомобилям:\n" \
                                f"1️⃣. Название автомобиля: {name_car}\n"\
                                    f"      Налог на автомобиль: {car_paid_days} рублей.\n"\
                                f"2️⃣. Название автомобиля: {name_car2}\n"\
                                    f"      Налог на автомобиль: {car_paid_days2} рублей.\n"\
                                f"3️⃣. Название автомобиля: {name_car3}\n"\
                                    f"      Налог на автомобиль: {car_paid_days3} рублей.\n"\
                                f"4️⃣. Название автомобиля: {name_car4}\n"\
                                    f"      Налог на автомобиль: {car_paid_days4} рублей."
                                
                    await message.reply(profile_message)
            elif 2 in range(len(car)):
                nickname = acc[1]
                name_car = car[0][2]
                car_paid_days = car[0][0]
                car_paid_days2 = car[1][0]
                name_car2 = car[1][2] 
                car_paid_days3 = car[2][0]
                name_car3 = car[2][2] 

                profile_message = f"📋 {nickname}, информация по Вашим автомобилям:\n" \
                            f"1️⃣. Название автомобиля: {name_car}\n"\
                                f"      Налог на автомобиль: {car_paid_days} рублей.\n"\
                            f"2️⃣. Название автомобиля: {name_car2}\n"\
                                f"      Налог на автомобиль: {car_paid_days2} рублей.\n"\
                            f"3️⃣. Название автомобиля: {name_car3}\n"\
                                f"      Налог на автомобиль: {car_paid_days3} рублей."\
                            
                await message.reply(profile_message)
            elif 1 in range(len(car)):
                nickname = acc[1]
                name_car = car[0][2]
                car_paid_days = car[0][0]
                car_paid_days2 = car[1][0]
                name_car2 = car[1][2] 

                profile_message = f"📋 {nickname}, информация по Вашим автомобилям:\n" \
                            f"1️⃣. Название автомобиля: {name_car}\n"\
                                f"      Налог на автомобиль: {car_paid_days} рублей.\n"\
                            f"2️⃣. Название автомобиля: {name_car2}\n"\
                                f"      Налог на автомобиль: {car_paid_days2} рублей."
                            
                await message.reply(profile_message)
            elif 0 in range(len(car)):
                print(car)
                nickname = acc[1]
                car_paid_days = car[0][0]
                name_car = car[0][2] 

                profile_message = f"📋 {nickname}, информация по Вашим автомобилям:\n" \
                                f"1️⃣. Название автомобиля: {name_car}\n"\
                                f"      Налог на автомобиль: {car_paid_days} рублей."
           
                await message.reply(profile_message)
            elif(acc):
                nickname = acc[1]
                profile_message = f"⛔ {nickname}, у вас нет автомобиля!"
                
                await message.reply(profile_message)
            else:
                nickname = acc[1]
                await message.reply(f"⛔ {nickname}, у вас нет автомобиля!")

        elif(acc[0] == 0):
            await message.reply("⭐ У вас нет VIP-статуса.")
        else:
            await message.reply("⛔ Вы не зарегистрированы в системе.")

@dp.message_handler(lambda msg: msg.text.startswith('💼БИЗНЕСЫ'))
async def houses_prf(message: types.Message):
    user_id = message.from_user.id
    with open("C:/IT/52Project/database.json", "r") as f_o:
        data_from_json = json.loads(f_o.read())

    username = data_from_json[f"{user_id}"]["nickname"]

    async with aiomysql.create_pool(**DB_CONFIG) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT vip, name FROM accounts WHERE name=%s", (username,))
                acc = await cur.fetchone()
                async with conn.cursor() as cur:
                    await cur.execute("SELECT day, owner, name FROM business WHERE owner=%s", (username,))
                    biz = await cur.fetchall()
        if(acc[0] == 1):
            if 2 in range(len(biz)):
                    nickname = acc[1]
                    name_biz = biz[0][2]
                    biz_paid_days = biz[0][0]
                    biz_paid_days2 = biz[1][0]
                    name_biz2 = biz[1][2] 
                    biz_paid_days3 = biz[2][0]
                    name_biz3 = biz[2][2]


                    profile_message = f"📋 {nickname}, информация по Вашим бизнесам:\n" \
                                f"1️⃣. Название бизнеса: {name_biz}\n"\
                                    f"      Бизнес оплачен на: {biz_paid_days} дня/дней/день.\n"\
                                f"2️⃣. Название бизнеса: {name_biz2}\n"\
                                    f"      Бизнес оплачен на: {biz_paid_days2} дня/дней/день.\n"\
                                f"3️⃣. Название бизнеса: {name_biz3}\n"\
                                    f"      Бизнес оплачен на: {biz_paid_days3} дня/дней/день."
                                
                    await message.reply(profile_message)
            elif 1 in range(len(biz)):    
                    nickname = acc[1]
                    name_biz = biz[0][2]
                    biz_paid_days = biz[0][0]
                    biz_paid_days2 = biz[1][0]
                    name_biz2 = biz[1][2] 

                    profile_message = f"📋 {nickname}, информация по Вашим бизнесам:\n" \
                                f"1️⃣. Название бизнеса: {name_biz}\n"\
                                    f"      Бизнес оплачен на: {biz_paid_days} дня/дней/день.\n"\
                                f"2️⃣. Название бизнеса: {name_biz2}\n"\
                                    f"      Бизнес оплачен на: {biz_paid_days2} дня/дней/день."
                                
                    await message.reply(profile_message)
            elif 0 in range(len(biz)):
                    nickname = acc[1]
                    name_biz = biz[0][2]
                    biz_paid_days = biz[0][0]

                    profile_message = f"📋 {nickname}, информация по Вашим бизнесам:\n" \
                                f"1️⃣. Название бизнеса: {name_biz}\n"\
                                    f"      Бизнес оплачен на: {biz_paid_days} дня/дней/день."
                            
                    await message.reply(profile_message)
            elif(acc):
                nickname = acc[1]


                profile_message = f"⛔ {nickname}, у вас нет бизнеса!"
                
                await message.reply(profile_message)
            else:
                nickname = acc[1]
                await message.reply(f"⛔ {nickname}, у вас нет бизнеса!")

        elif(acc[0] == 0):
            await message.reply("⭐ У вас нет VIP-статуса.")
        else:
            await message.reply("⛔ Вы не зарегистрированы в системе.")

@dp.message_handler(lambda msg: msg.text.startswith('🏠ДОМА'))
async def houses_prf(message: types.Message):
    user_id = message.from_user.id
    with open("C:/IT/52Project/database.json", "r") as f_o:
        data_from_json = json.loads(f_o.read())

    username = data_from_json[f"{user_id}"]["nickname"]

    async with aiomysql.create_pool(**DB_CONFIG) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT vip, name FROM accounts WHERE name=%s", (username,))
                acc = await cur.fetchone()
                async with conn.cursor() as cur:
                    await cur.execute("SELECT day, owner FROM houses WHERE owner=%s", (username,))
                    house = await cur.fetchone()
        if(acc[0] == 1):
            if(house):
                nickname = acc[1]
                house_paid_days = house[0]

                profile_message = f"📋 {nickname}, информация по Вашему дому:\n" \
                            f"1️⃣. Дом оплачен на: {house_paid_days} дня/дней/день."
                await message.reply(profile_message)
            else:
                nickname = acc[1]
                await message.reply(f"⛔ {nickname}, у вас нет дома!")
        elif(acc[0] == 0):
            await message.reply("⭐ У вас нет VIP-статуса.")
        else:
            await message.reply("⛔ Вы не зарегистрированы в системе.")


@dp.message_handler(lambda msg: msg.text.startswith('👤ПРОФИЛЬ'))
async def cmd_profile(message: types.Message):
    with open("C:/IT/52Project/database.json", "r") as f_o:
        data_from_json = json.loads(f_o.read())

        user_id = message.from_user.id
        username = data_from_json[f"{user_id}"]["nickname"]

        # Устанавливаем соединение с базой данных
        async with aiomysql.create_pool(**DB_CONFIG) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # Выполняем запрос на получение данных пользователя
                    await cur.execute("SELECT vip FROM accounts WHERE name=%s", (username,))
                    acc = await cur.fetchone()
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT online_type, lvl FROM accounts WHERE name=%s", (username,))
                        account = await cur.fetchone()
        if(acc[0] == 1):
            online_type = "ОНЛАЙН" if account[0] == 1 else "ОФФЛАЙН"
            nickname = data_from_json[f"{user_id}"]["nickname"]
            # Проверяем, найден ли пользователь
            await message.reply(f"🔍 {nickname}, Ваш профиль:\n\
🔰 Ваш уровень: {account[1]}\n\
🌍 Статус: {online_type}\n\
⭐ VIP-Статус: Есть\n\
")
        elif acc[0] == 0:
            await message.reply("⭐ У вас нет VIP-статуса.")
        else:
            await message.reply("⛔ Вы не зарегистрированы в системе.")


async def send_to_enter(nickname: str):
    async with aiopen('C:/IT/52Project/database.json', 'r', encoding='utf-8') as file:
        json_data = loads(await file.read())
    for telegram_id, telegram_data in list(json_data.items()): # Перебираем циклом распаковывая
        if (telegram_id not in online):
            username = telegram_data['nickname']
            async with aiomysql.create_pool(**DB_CONFIG) as pool:
                async with pool.acquire() as conn:
                    async with conn.cursor() as cur:
                    # Выполняем запрос на получение данных пользователя
                        await cur.execute("SELECT timevhod, login_ip FROM accounts WHERE name=%s", (username,))
                        vhod = await cur.fetchone()
            if telegram_data['nickname'] == nickname: # Если ник есть
                online.append(telegram_id)
                await bot.send_message( # Отправляем сообщение
                    chat_id=telegram_id, # Указываем telegram_id
                    text=f'➡️ Вы вошли на сервер! Время входа - {vhod[0]}.\n🖥️ IP - {vhod[1]}\n\nЕсли вход был совершён не Вами, срочно сообщите об этом администрации проекта!' # Отправляем сообщение
                )

async def send_to_exit(nickname: str):
    async with aiopen('C:/IT/52Project/database.json', 'r', encoding='utf-8') as file:
        json_data = loads(await file.read())
    for telegram_id, telegram_data in list(json_data.items()): # Перебираем циклом распаковывая
        if (telegram_id in online):
            if telegram_data['nickname'] == nickname: # Если ник есть
                online.remove(telegram_id)
                await bot.send_message( # Отправляем сообщение
                    chat_id=telegram_id, # Указываем telegram_id
                    text='⬅️ Вы вышли с сервера!' # Отправляем сообщение
                )

async def checker():
  while True:
    async with aiopen('C:/IT/52Project/database.json', 'r', encoding='utf-8') as file:
        json_database = loads(await file.read())

    async with aiomysql.create_pool(**DB_CONFIG) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                    # Выполняем запрос на получение данных пользователя
                await cur.execute("SELECT name, online_type FROM accounts")
                database = await cur.fetchall()
    for record in database:
      if (record[1]): # 1 - True, 0 - False
        await send_to_enter(record[0])
      else:
        await send_to_exit(record[0])
    await asyncio.sleep(5)


main_loop = asyncio.get_event_loop()

async def polling():
    executor.start_polling(dp, loop=main_loop, skip_updates=True)

if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    main_loop.create_task(checker())
    executor.start_polling(dp, loop=main_loop, skip_updates=True)
