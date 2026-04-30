import sqlite3
import json

DB_NAME = 'secret_santa.db'


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            code TEXT PRIMARY KEY,
            creator_id INTEGER,
            budget TEXT DEFAULT 'Не указан',
            status TEXT DEFAULT 'waiting',
            draw_results TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_code TEXT,
            user_id INTEGER,
            wishlist TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (game_code) REFERENCES games(code),
            UNIQUE(game_code, user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anonymous_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_code TEXT,
            from_user_id INTEGER,
            to_user_id INTEGER,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (game_code) REFERENCES games(code)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_active_game (
            user_id INTEGER PRIMARY KEY,
            game_code TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (game_code) REFERENCES games(code)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_names (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


def create_game(code, creator_id, budget):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO games (code, creator_id, budget, status)
        VALUES (?, ?, ?, ?)
    ''', (code, creator_id, budget, 'waiting'))

    cursor.execute('''
        INSERT INTO players (game_code, user_id)
        VALUES (?, ?)
    ''', (code, creator_id))

    conn.commit()
    conn.close()


def get_game(code):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM games WHERE code = ?', (code,))
    game = cursor.fetchone()

    if game:
        game = dict(game)
        if game['draw_results']:
            game['draw'] = json.loads(game['draw_results'])
        else:
            game['draw'] = {}

    conn.close()
    return game


def get_all_games():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM games')
    games_list = cursor.fetchall()

    result = {}
    for game in games_list:
        game_dict = dict(game)
        if game_dict['draw_results']:
            game_dict['draw'] = json.loads(game_dict['draw_results'])
        else:
            game_dict['draw'] = {}

        if 'creator_id' in game_dict:
            game_dict['creator'] = game_dict['creator_id']

        result[game_dict['code']] = game_dict

    conn.close()
    return result


def update_game_draw(code, draw_results):
    conn = get_connection()
    cursor = conn.cursor()

    draw_json = json.dumps(draw_results)
    cursor.execute('''
        UPDATE games 
        SET draw_results = ?, status = 'completed'
        WHERE code = ?
    ''', (draw_json, code))

    conn.commit()
    conn.close()


def delete_game(code):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM players WHERE game_code = ?', (code,))
    cursor.execute('DELETE FROM anonymous_messages WHERE game_code = ?', (code,))
    cursor.execute('DELETE FROM user_active_game WHERE game_code = ?', (code,))
    cursor.execute('DELETE FROM games WHERE code = ?', (code,))

    conn.commit()
    conn.close()


def add_player(game_code, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO players (game_code, user_id)
            VALUES (?, ?)
        ''', (game_code, user_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_players(game_code):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id, wishlist FROM players 
        WHERE game_code = ?
        ORDER BY joined_at
    ''', (game_code,))

    players = cursor.fetchall()
    conn.close()
    return [dict(p) for p in players]


def get_player_count(game_code):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT COUNT(*) as count FROM players 
        WHERE game_code = ?
    ''', (game_code,))

    count = cursor.fetchone()['count']
    conn.close()
    return count


def update_wishlist(user_id, wishlist_text):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE players 
        SET wishlist = ?
        WHERE user_id = ?
    ''', (wishlist_text, user_id))

    conn.commit()
    conn.close()


def get_wishlist(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT wishlist FROM players 
        WHERE user_id = ?
        ORDER BY id DESC LIMIT 1
    ''', (user_id,))

    result = cursor.fetchone()
    conn.close()
    return result['wishlist'] if result else None


def get_all_wishlists(game_code):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id, wishlist FROM players 
        WHERE game_code = ?
    ''', (game_code,))

    wishlists = {row['user_id']: row['wishlist'] for row in cursor.fetchall()}
    conn.close()
    return wishlists


def is_player_in_game(game_code, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 1 FROM players 
        WHERE game_code = ? AND user_id = ?
    ''', (game_code, user_id))

    result = cursor.fetchone() is not None
    conn.close()
    return result


def get_game_creator(game_code):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT creator_id FROM games WHERE code = ?', (game_code,))

    result = cursor.fetchone()
    conn.close()
    return result['creator_id'] if result else None


def set_active_game(user_id, game_code):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO user_active_game (user_id, game_code, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, game_code))

    conn.commit()
    conn.close()


def get_active_game(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT game_code FROM user_active_game 
        WHERE user_id = ?
    ''', (user_id,))

    result = cursor.fetchone()
    conn.close()
    return result['game_code'] if result else None


def clear_active_game(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM user_active_game WHERE user_id = ?', (user_id,))

    conn.commit()
    conn.close()


def save_anonymous_message(game_code, from_user_id, to_user_id, message_text):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO anonymous_messages (game_code, from_user_id, to_user_id, message)
        VALUES (?, ?, ?, ?)
    ''', (game_code, from_user_id, to_user_id, message_text))

    conn.commit()
    conn.close()


def get_anonymous_messages(game_code, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT from_user_id, message, created_at 
        FROM anonymous_messages 
        WHERE game_code = ? AND to_user_id = ?
        ORDER BY created_at
    ''', (game_code, user_id))

    messages = cursor.fetchall()
    conn.close()
    return [dict(m) for m in messages]


def save_user_name(user_id, name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO user_names (user_id, name, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, name))

    conn.commit()
    conn.close()


def get_user_name_from_cache(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT name FROM user_names WHERE user_id = ?', (user_id,))

    result = cursor.fetchone()
    conn.close()
    return result['name'] if result else None


def get_user_games(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT g.* FROM games g
        JOIN players p ON g.code = p.game_code
        WHERE p.user_id = ?
    ''', (user_id,))

    games_list = cursor.fetchall()
    result = []
    for game in games_list:
        game_dict = dict(game)
        if game_dict['draw_results']:
            game_dict['draw'] = json.loads(game_dict['draw_results'])
        else:
            game_dict['draw'] = {}
        result.append((game_dict['code'], game_dict))

    conn.close()
    return result


init_db()


def get_all_user_names():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT user_id, name FROM user_names')
    result = {row['user_id']: row['name'] for row in cursor.fetchall()}

    conn.close()
    return result