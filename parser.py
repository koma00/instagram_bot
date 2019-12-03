from instagram import WebAgentAccount, Account, Media
import os.path
import sqlite3
import time

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
    conn.commit()

def get_follows_and_followers(id, user, password):
    account = Account(user)

    agent = WebAgentAccount(user)
    agent.auth(password)

    print("Starting getting follows")
    pointer = ''
    while pointer != None:
        follows, pointer = agent.get_follows(account, pointer)
        for follow in follows:
            sql = "INSERT INTO follows VALUES ({id_user}, '{follow}')".format(id_user=id, follow=follow)
            cursor.execute(sql)
            conn.commit()
        time.sleep(5)
    conn.commit()

    print("Starting getting followers")
    pointer = ''
    while pointer != None:
        followers, pointer = agent.get_followers(account, pointer)
        for follower in followers:
            sql = "INSERT INTO followers VALUES ({id_user}, '{follower}')".format(id_user=id, follower=follower)
            cursor.execute(sql)
            conn.commit()
        time.sleep(5)
    conn.commit()
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

while (1):
    while(True):
        print('What do we do?')
        print('1 - Get follows and followers')
        print('0 - Exit')
        action = input()
        if action == '0':
            exit()
        if action == '1':
            print('Starting getting follows and followers')
            get_follows_and_followers(id, login, password)
            print('Getting follows and followers finished')