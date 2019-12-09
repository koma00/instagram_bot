from instagram_private_api import Client, ClientCompatPatch
import os.path
import sqlite3
import time
import random
import requests

db_file_name = "parser.db"

def init_db(db_file_name):
    conn = sqlite3.connect(db_file_name)
    cursor = conn.cursor()

    # Создание таблицы c конфигурацией
    cursor.execute("""
        CREATE TABLE users(
            id INTEGER PRIMARY KEY,
            login text,
            password text
        )
    """)
    # Создание таблицы с подписками
    cursor.execute("""
        CREATE TABLE follows(
            id_user INTEGER,
            follow text
        )
    """)
    # Создание таблицы с подписчиками
    cursor.execute("""
        CREATE TABLE followers(
            id_user INTEGER,
            follower text
        )
    """)
    # Создание таблицы с постами
    cursor.execute("""
        CREATE TABLE media(
            id INTEGER PRIMARY KEY,
            id_user INTEGER,
            media_id text,
            code_media text
        )
    """)
    # Создание таблицы с отметками под постами
    cursor.execute("""
        CREATE TABLE comment_media(
            id_user INTEGER,
            media_id text,
            follow text
        )
    """)
    conn.commit()

def get_follows(api, user_id):
    rank_token = api.generate_uuid()
    next_max_id = None
    while (1):
        followings = api.user_following(user_id, rank_token, max_id=next_max_id)
        next_max_id = followings.get('next_max_id')
        for follow in followings.get('users'):
            sql = "INSERT INTO follows VALUES ({id_user}, '{follow}')".format(id_user=id, follow=follow["username"])
            cursor.execute(sql)
            conn.commit()        
        if not next_max_id:
            break
        time.sleep(5)
    return 0


def get_followers(api, user_id):
    rank_token = api.generate_uuid()
    next_max_id = None
    while (1):
        followers = api.user_followers(user_id, rank_token, max_id=next_max_id)
        next_max_id = followers.get('next_max_id')
        for follower in followers.get('users'):
            sql = "INSERT INTO followers VALUES ({id_user}, '{follower}')".format(id_user=id, follower=follower["username"])
            cursor.execute(sql)
            conn.commit()
        if not next_max_id:
            break
        time.sleep(5)
    return 0

def get_follows_and_followers(id, user, password):
    api = Client(user, password)
    user_id = api.current_user().get('user').get('pk')

    print("Starting getting follows")
    sql = "SELECT count(1) FROM follows WHERE id_user = {id_user}".format(id_user=id)
    cursor.execute(sql)
    count = cursor.fetchone()[0]
    if count > 0:
        while(True):
            print("In database storeged {count} follows on user {user}".format(count=count, user=user))
            print("What do we do?")
            print("1 - Updated follows")
            print("2 - Skip getting follows")
            print("3 - Return menu")
            print("0 - Exit")
            action = input()
            if action == '1':
                print("Updating follows")
                sql = "DELETE FROM follows WHERE id_user = {id_user}".format(id_user=id)
                cursor.execute(sql)
                get_follows(api, user_id)
                print("Getting follows finished")
                break
            if action == '2':
                print("Skip getting follows")
                break
            if action == '3':
                return 0
            if action == '0':
                exit()
    else:
        get_follows(api, user_id)
        print("Getting follows finished")

    print("Starting getting followers")
    sql = "SELECT count(1) FROM followers WHERE id_user = {id_user}".format(id_user=id)
    cursor.execute(sql)
    count = cursor.fetchone()[0]
    if count > 0:
        while(True):
            print("In database storeged {count} followers on user {user}".format(count=count, user=user))
            print("What do we do?")
            print("1 - Updated followers")
            print("2 - Skip getting followers")
            print("3 - Return menu")
            print("0 - Exit")
            action = input()
            if action == '1':
                print("Updating followers")
                sql = "DELETE FROM followers WHERE id_user = {id_user}".format(id_user=id)
                cursor.execute(sql)
                get_followers(api, user_id)
                print("Getting followers finished")
                break
            if action == '2':
                print("Skip getting followers")
                break
            if action == '3':
                return 0
            if action == '0':
                exit()
    else:
        get_followers(api, user_id)
        print("Getting followers finished")
        
    return 0

def add_post_db(id):
    print("Input Instagram post short_code: ", end='')
    code_media = input()
    sql = "SELECT count(1) FROM media WHERE id_user = {id_user} and code_media = '{code_media}'".format(id_user=id, code_media=code_media)
    cursor.execute(sql)
    count = cursor.fetchone()[0]
    if count > 0:
        print("Error! Post exist in database!")
    else:
        url = "https://api.instagram.com/oembed/"
        params = "callback=&url=https://www.instagram.com/p/{code_media}/".format(code_media=code_media)
        r = requests.get(url = url, params = params)
        media_id = r.json()['media_id']
        sql = "INSERT INTO media(id_user, media_id, code_media) VALUES ({id_user}, '{media_id}', '{code_media}')".format(
            id_user=id,
            media_id=media_id,
            code_media=code_media
        )
        cursor.execute(sql)
        conn.commit()
        print("Post {code_media} ({media_id}) added to database".format(code_media=code_media, media_id=media_id))
    return 0

def show_my_post_db(id):
    sql = "SELECT * FROM media WHERE id_user = {id_user}".format(id_user=id)
    cursor.execute(sql)
    media = cursor.fetchall()
    if len(media) > 0:
        print("My media:")
        for media_ in media:
            print(media_[2])
    else:
        print("No media in database!")
    return 0

def post_commenting(user_name, password, id):
    sql = "SELECT * FROM media WHERE id_user = {id_user}".format(id_user=id)
    cursor.execute(sql)
    posts = cursor.fetchall()
    if len(posts) > 0:
        while(1):
            print("Select media (0 - return menu):")
            print("id media")
            for post in posts:
                print(post[0], " ", post[2])
            post_id = input()
            if post_id == '0':
                return 0
            sql = "SELECT * FROM media WHERE id = {id} and id_user = {id_user}".format(id = post_id, id_user = id)
            cursor.execute(sql)
            post = cursor.fetchall()
            if len(post) == 1:
                break
        api = Client(user_name, password)
        media = post[0][2]
        sql = """
            select t1.follow
            from follows t1
            left join (
                select *
                from comment_media
                where media_id = {media_id}
            ) t2
            on t1.follow = t2.follow
            where t2.follow is null
        """.format(media_id=post_id)
        cursor.execute(sql)
        follows = cursor.fetchall()
        for follow in follows:
            print("@{follow}".format(follow=follow[0]))
            api.post_comment(media, "@{follow}".format(follow=follow[0]))
            sql = """INSERT INTO comment_media(id_user, media_id, follow) VALUES ({id_user}, '{media_id}', '{follow}')""".format(
                id_user=id,
                media_id=post_id,
                follow=follow[0]
            )
            cursor.execute(sql)
            conn.commit()
            sleep_time = random.randint(30*60, 120*60) #random pause 30..120 min
            print("Sleep {sleep_time_min} min {sleep_time_sec} sec".format(sleep_time_min=sleep_time//60, sleep_time_sec=sleep_time%60))
            time.sleep(sleep_time) #random pause 30..120 min
    else:
        print("No media in database!")
    return 0

# Check exist db
if not os.path.exists(db_file_name):
    init_db(db_file_name)

conn = sqlite3.connect(db_file_name)
cursor = conn.cursor()

print("Input Instagram login: ", end='')
login = input()

cursor.execute("SELECT * FROM users WHERE login = '{login}'".format(login=login))

if cursor.fetchone():
    print("User {user} exist in database. Continue[1] or update password user[2]?".format(user=login))
    action = input()
    if action == '1':
        exit
    if action == '2':
        print("Input new password on user {user}: ".format(user=login), end='')
        password = input()
        cursor.execute("UPDATE users SET password = '{password}' WHERE login = '{login}'".format(password=password, login=login))
        conn.commit()
    if action != '1' and action != '2':
        exit()
else:
    print("User {user} not exist in database. Create user[1] or exit[2]?".format(user=login))
    action = input()
    if action == '1':
        print("Input Instagram password on user {user}".format(user=login))
        password = input()
        cursor.execute("INSERT INTO users(login, password) VALUES ('{user}','{password}')".format(user=login, password=password))
        conn.commit()
    else:
        exit()

cursor.execute("SELECT * FROM users WHERE login = '{login}'".format(login=login))
rows = cursor.fetchall()

if len(rows) != 1:
    print('Error! Dublicate user name!')
    exit()

id = rows[0][0]
login = rows[0][1]
password = rows[0][2]

while(True):
    print('What do we do?')
    print('1 - Get follows and followers')
    print('2 - Add post to database')
    print('3 - Show my posts in database')
    print('4 - Post commenting')
    print('0 - Exit')
    action = input()
    if action == '0':
        exit()
    if action == '1':
        print('Starting getting follows and followers')
        get_follows_and_followers(id, login, password)
        print('Getting follows and followers finished')
    if action == '2':
        add_post_db(id)
    if action == '3':
        show_my_post_db(id)
    if action == '4':
        post_commenting(login, password, id)
