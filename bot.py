import config
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from random import randint
import sqlite3

conn = sqlite3.connect("movie_database.db")
cur = conn.cursor()

cur.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id TEXT NOT NULL
        )
    ''')

conn.commit()
conn.close()

bot = telebot.TeleBot(config.API_TOKEN)

def send_info(bot, message, row):
    info = f"""
🎬Title of movie:   {row[2]}
🕗Year:                   {row[3]}
🎲Genres:              {row[4]}
🔢Rating IMDB:      {row[5]}


🔻🔻🔻🔻🔻🔻🔻🔻🔻🔻🔻
{row[6]}
"""
    bot.send_photo(message.chat.id, row[1])
    bot.send_message(message.chat.id, info, reply_markup=add_to_favorite(row[0]))

def add_to_favorite(id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Добавить фильм в избранное 🌟", callback_data=f'favorite_{id}'),
        InlineKeyboardButton("Удалить из избранного ❌", callback_data=f'remove_favorite_{id}')
    )
    return markup

def main_markup():
    markup = ReplyKeyboardMarkup()
    markup.add(KeyboardButton('/random'))
    return markup

def main_markup2():
    markup = ReplyKeyboardMarkup()
    markup.add(KeyboardButton('/favorite'))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data.startswith("favorite"):
        id = call.data[call.data.find("_")+1:]
        con = sqlite3.connect("movie_database.db")
        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO favorites (movie_id) VALUES (?)", (id,))
            con.commit()
            bot.answer_callback_query(call.id, "Фильм добавлен в избранное! 🌟")
        cur.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_favorite"))
def remove_favorite(call):
    id = call.data.split("_")[2]
    print(f"Attempting to remove movie with ID: {id}") 
    try:
        con = sqlite3.connect("movie_database.db")
        with con:
            cur = con.cursor()
            cur.execute("DELETE FROM favorites WHERE movie_id = ?", (id,))
            con.commit()
            if cur.rowcount > 0:
                bot.answer_callback_query(call.id, "Фильм удален из избранного! ❌")
            else:
                bot.answer_callback_query(call.id, "Фильм не найден в избранном.")
    except Exception as e:
        print(f"Error occurred: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка при удалении фильма.")
    finally:
        con.close()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, """Hello! You're welcome to the best Movie-Chat-Bot🎥!
Here you can find 1000 movies 🔥
Click /random to get random movie
Or write the title of movie and I will try to find it! 🎬 """, reply_markup=main_markup())

@bot.message_handler(commands=['favorite'])
def end_favorite_movies(message):
    bot.send_message(message.chat.id, """And here you can look at your own favorite movies 🔥! 🎬
Click /favorite_movie to get a list of favorite movies!!!""", reply_markup=main_markup2())
    
@bot.message_handler(commands=['favorite_movie'])
def end_favorite_movies(message):
    con = sqlite3.connect("movie_database.db")
    with con:
        cur = con.cursor()
        cur.execute("SELECT movie_id FROM favorites")
        favorite_movies = cur.fetchall()

        if not favorite_movies:
            bot.send_message(message.chat.id, "У вас нет сохраненных фильмов! 🌟")
            return

        favorite_movie_info = []

        for movie in favorite_movies:
            movie_id = movie[0]
            cur.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
            movie_info = cur.fetchone()
            if movie_info:
                favorite_movie_info.append(movie_info)

        for row in favorite_movie_info:
            send_info(bot, message, row)

    cur.close()

@bot.message_handler(commands=['random'])
def random_movie(message):
    con = sqlite3.connect("movie_database.db")
    with con:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM movies")
        total_movies = cur.fetchone()[0]
        random_index = randint(0, total_movies - 1)
        cur.execute(f"SELECT * FROM movies LIMIT 1 OFFSET {random_index}")
        row = cur.fetchall()[0]
    
    send_info(bot, message, row)


bot.infinity_polling()


