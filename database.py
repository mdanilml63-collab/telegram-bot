# database.py
import sqlite3
import json
import time
import quest_manager
from utils import escape_markdown

DB_NAME = 'db.db'

def init_db():
    """Инициализирует/обновляет все таблицы базы данных, включая рыбалку."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('PRAGMA foreign_keys = ON;')

        # --- Таблица игроков с перками ---
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            pve_wins INTEGER DEFAULT 0,
            pvp_wins INTEGER DEFAULT 0,
            divine_orbs INTEGER DEFAULT 0,
            mirrors INTEGER DEFAULT 0,
            unlocked_mtx TEXT DEFAULT '[]',
            perm_attack_bonus INTEGER DEFAULT 0,
            perm_health_bonus INTEGER DEFAULT 0,
            perm_es_bonus INTEGER DEFAULT 0,
            perm_crit_chance_bonus INTEGER DEFAULT 0,
            perm_dodge_chance_bonus INTEGER DEFAULT 0,
            perm_block_chance_bonus INTEGER DEFAULT 0,
            perm_defense_bonus INTEGER DEFAULT 0
        )''')
        
        cursor.execute("PRAGMA table_info(players)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Словарь с новыми колонками, которые нужно добавить
        new_player_columns = {
            'level': 'INTEGER DEFAULT 1',
            'xp': 'INTEGER DEFAULT 0',
            'skill_points': 'INTEGER DEFAULT 0',
            'class_id': 'TEXT' # NULL по умолчанию, так как класс выбирается в забеге
        }

        # Проходим по словарю и добавляем недостающие колонки
        for col_name, col_type in new_player_columns.items():
            if col_name not in columns:
                cursor.execute(f"ALTER TABLE players ADD COLUMN {col_name} {col_type}")
                print(f"Столбец '{col_name}' добавлен в 'players'.")
        
        if 'unlocked_mtx' not in columns:
            cursor.execute("ALTER TABLE players ADD COLUMN unlocked_mtx TEXT DEFAULT '[]'")
            print("Столбец 'unlocked_mtx' добавлен в 'players'.")

        new_perk_columns = {
            'perm_attack_bonus': 'INTEGER DEFAULT 0', 'perm_health_bonus': 'INTEGER DEFAULT 0',
            'perm_es_bonus': 'INTEGER DEFAULT 0', 'perm_crit_chance_bonus': 'INTEGER DEFAULT 0',
            'perm_dodge_chance_bonus': 'INTEGER DEFAULT 0', 'perm_block_chance_bonus': 'INTEGER DEFAULT 0',
            'perm_defense_bonus': 'INTEGER DEFAULT 0',
            'perm_double_damage_bonus': 'INTEGER DEFAULT 0',
            'perm_defense_penetration_bonus': 'INTEGER DEFAULT 0',
            'perm_lifesteal_bonus': 'INTEGER DEFAULT 0',
            'perm_magic_find_bonus': 'INTEGER DEFAULT 0'
        }
        for col_name, col_type in new_perk_columns.items():
            if col_name not in columns:
                cursor.execute(f"ALTER TABLE players ADD COLUMN {col_name} {col_type}")
                print(f"Столбец '{col_name}' добавлен в 'players'.")

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fishing_stats (
            user_id INTEGER PRIMARY KEY,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            chaos_orbs INTEGER DEFAULT 0,
            divine_shards INTEGER DEFAULT 0,          
            unlocked_rods TEXT DEFAULT '[]',
            inventory TEXT DEFAULT '[]',
            purchased_upgrades TEXT DEFAULT '{}',
            unspent_perk_points INTEGER DEFAULT 0, 
            active_baits TEXT DEFAULT '{}',
            expedition_end_time INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES players(user_id)
        )''')
        
        cursor.execute("PRAGMA table_info(fishing_stats)")
        fishing_columns = [col[1] for col in cursor.fetchall()]

        if 'divine_shards' not in fishing_columns:
            cursor.execute("ALTER TABLE fishing_stats ADD COLUMN divine_shards INTEGER DEFAULT 0")
            print("Столбец 'divine_shards' добавлен в 'fishing_stats'.")
        if 'purchased_upgrades' not in fishing_columns:
            cursor.execute("ALTER TABLE fishing_stats ADD COLUMN purchased_upgrades TEXT DEFAULT '{}'")
            print("Столбец 'purchased_upgrades' добавлен в 'fishing_stats'.")
        if 'unspent_perk_points' not in fishing_columns:
            cursor.execute("ALTER TABLE fishing_stats ADD COLUMN unspent_perk_points INTEGER DEFAULT 0")
            print("Столбец 'unspent_perk_points' добавлен в 'fishing_stats'.")
        if 'active_baits' not in fishing_columns:
            cursor.execute("ALTER TABLE fishing_stats ADD COLUMN active_baits TEXT DEFAULT '{}'")
            print("Столбец 'active_baits' добавлен в 'fishing_stats'.")
        if 'expedition_end_time' not in fishing_columns:
            cursor.execute("ALTER TABLE fishing_stats ADD COLUMN expedition_end_time INTEGER DEFAULT 0")
            print("Столбец 'expedition_end_time' добавлен в 'fishing_stats'.")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pvp_characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL, floor INTEGER NOT NULL,
            character_data TEXT NOT NULL, FOREIGN KEY(owner_id) REFERENCES players(user_id))''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS champions (
            champion_id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER NOT NULL, character_data TEXT NOT NULL,
            passive_wins INTEGER DEFAULT 0, lives INTEGER DEFAULT 2, FOREIGN KEY(player_id) REFERENCES players(user_id))''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pve_runs (
            user_id INTEGER PRIMARY KEY, current_floor INTEGER NOT NULL, event_num INTEGER NOT NULL,
            character_state TEXT NOT NULL, floor_bosses TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES players(user_id))''')
            
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_quests (
            user_id INTEGER PRIMARY KEY,
            quests_data TEXT NOT NULL,
            reset_time INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES players(user_id)
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS world_boss (
            boss_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            stats TEXT NOT NULL,
            current_hp INTEGER NOT NULL,
            spawn_time INTEGER NOT NULL,
            end_time INTEGER NOT NULL,
            is_active BOOLEAN NOT NULL,
            is_defeated BOOLEAN NOT NULL
        )''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS world_boss_participants (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            damage_dealt INTEGER DEFAULT 0,
            last_attack_time INTEGER DEFAULT 0,
            reward_claimed BOOLEAN DEFAULT FALSE,
            FOREIGN KEY(user_id) REFERENCES players(user_id)
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS harvest_stats (
            user_id INTEGER PRIMARY KEY,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            lifeforce INTEGER DEFAULT 0,
            crystalline_lifeforce INTEGER DEFAULT 0,
            seeds TEXT DEFAULT '{}',
            plants TEXT DEFAULT '{}',
            fertilizers TEXT DEFAULT '{}',
            beds TEXT DEFAULT '[]',
            growth_speed_bonus REAL DEFAULT 0.0,
            FOREIGN KEY(user_id) REFERENCES players(user_id)
        )''')

        # ИЗМЕНЕНИЕ: Добавлено поле floor
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            rarity TEXT NOT NULL,
            slot TEXT NOT NULL,
            stats TEXT NOT NULL,
            floor INTEGER NOT NULL,
            FOREIGN KEY(owner_id) REFERENCES players(user_id)
        )''')

        # ИЗМЕНЕНИЕ: Проверка и добавление нового столбца для обратной совместимости
        cursor.execute("PRAGMA table_info(custom_items)")
        custom_items_columns = [col[1] for col in cursor.fetchall()]
        if 'floor' not in custom_items_columns:
            cursor.execute("ALTER TABLE custom_items ADD COLUMN floor INTEGER NOT NULL DEFAULT 1")
            print("Столбец 'floor' добавлен в 'custom_items'.")

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS divination_cards (
            user_id INTEGER NOT NULL,
            card_id TEXT NOT NULL,
            count INTEGER NOT NULL,
            PRIMARY KEY (user_id, card_id),
            FOREIGN KEY(user_id) REFERENCES players(user_id)
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS endless_run_leaderboard (
            user_id INTEGER PRIMARY KEY,
            max_floor INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES players(user_id)
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_skills (
            user_id INTEGER NOT NULL,
            skill_id TEXT NOT NULL,
            PRIMARY KEY (user_id, skill_id),
            FOREIGN KEY(user_id) REFERENCES players(user_id)
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_rewards_claims (
            user_id INTEGER NOT NULL,
            month_year TEXT NOT NULL,
            leaderboard_type TEXT NOT NULL,
            PRIMARY KEY (user_id, month_year, leaderboard_type),
            FOREIGN KEY(user_id) REFERENCES players(user_id)
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER PRIMARY KEY,
            reward_claimed BOOLEAN DEFAULT FALSE,
            FOREIGN KEY(referrer_id) REFERENCES players(user_id),
            FOREIGN KEY(referred_id) REFERENCES players(user_id)
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rhoa_races (
            race_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            rhoa_id INTEGER NOT NULL,
            bet_amount INTEGER NOT NULL,
            currency_type TEXT NOT NULL,
            status TEXT DEFAULT 'waiting',
            PRIMARY KEY (race_id, user_id)
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS hc_pvp_characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            floor INTEGER NOT NULL,
            character_data TEXT NOT NULL,
            FOREIGN KEY(owner_id) REFERENCES players(user_id)
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS hc_champions (
            champion_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            character_data TEXT NOT NULL,
            passive_wins INTEGER DEFAULT 0,
            lives INTEGER DEFAULT 2,
            FOREIGN KEY(player_id) REFERENCES players(user_id)
        )''')
        
        # --- Добавление столбца для ХК побед ---
        cursor.execute("PRAGMA table_info(players)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'hc_pvp_wins' not in columns:
            cursor.execute("ALTER TABLE players ADD COLUMN hc_pvp_wins INTEGER DEFAULT 0")
            print("Столбец 'hc_pvp_wins' добавлен в 'players'.")

        print("База данных успешно инициализирована.")


def add_or_update_player(user_id, username):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO players (user_id, username) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET username=excluded.username",
            (user_id, username)
        )

def get_player_info(user_id):
    """Возвращает полную информацию об игроке, включая MTX, уровень, класс и ХК победы."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # --- ИЗМЕНЕНИЕ: Добавлены level, xp, skill_points, class_id и hc_pvp_wins ---
        cursor.execute("""
            SELECT username, pve_wins, pvp_wins, divine_orbs, mirrors, unlocked_mtx, 
                   level, xp, skill_points, class_id, hc_pvp_wins 
            FROM players 
            WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                'username': row[0], 'pve_wins': row[1], 'pvp_wins': row[2],
                'divine_orbs': row[3], 'mirrors': row[4],
                'unlocked_mtx': json.loads(row[5]),
                'level': row[6], 'xp': row[7], 'skill_points': row[8],
                'class_id': row[9],
                'hc_pvp_wins': row[10]
            }
        return None



def purchase_mtx(user_id, mtx_id, cost, currency_type):
    """Атомарно обрабатывает покупку MTX."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT unlocked_mtx, " + currency_type + " FROM players WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row: return False

        unlocked_mtx_json, balance = row
        unlocked_mtx = json.loads(unlocked_mtx_json)

        if balance < cost or mtx_id in unlocked_mtx:
            return False

        unlocked_mtx.append(mtx_id)
        new_balance = balance - cost

        cursor.execute(f"UPDATE players SET unlocked_mtx = ?, {currency_type} = ? WHERE user_id = ?", (json.dumps(unlocked_mtx), new_balance, user_id))
        return True

# --- ИЗМЕНЕННЫЕ ФУНКЦИИ ЛИДЕРБОРДОВ ---
def get_pve_leaderboard_with_ids():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, pve_wins FROM players WHERE pve_wins > 0 ORDER BY pve_wins DESC LIMIT 10")
        return cursor.fetchall()

def get_pvp_leaderboard_with_ids():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, pvp_wins FROM players WHERE pvp_wins > 0 ORDER BY pvp_wins DESC LIMIT 10")
        return cursor.fetchall()

def get_champions_list_with_ids():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.player_id, p.username, c.passive_wins
            FROM champions c JOIN players p ON c.player_id = p.user_id
            ORDER BY c.passive_wins DESC
        """)
        return cursor.fetchall()

def end_pve_run(user_id, is_win=False, xp_reward=0):
    """Завершает прохождение, обновляя счетчики и начисляя награды."""
    run_state = get_pve_run_state(user_id)
    if not run_state: return

    is_pvp_run = run_state['character'].get('run_type') == 'pvp'
    is_endless_run = run_state['character'].get('run_type') == 'endless'
    # --- НОВАЯ ПРОВЕРКА ---
    is_hc_pvp_run = run_state['character'].get('run_type') == 'hc_pvp'

    if is_endless_run:
        update_endless_leaderboard(user_id, run_state['floor'])

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pve_runs WHERE user_id = ?", (user_id,))
        if is_win:
            level_up_message = add_xp_and_level_up(user_id, xp_reward, cursor_obj=cursor)
            if level_up_message:
                print(f"User {user_id} leveled up: {level_up_message}")
            if is_pvp_run:
                cursor.execute("UPDATE players SET pvp_wins = pvp_wins + 1 WHERE user_id = ?", (user_id,))
            # --- НОВЫЙ БЛОК ---
            elif is_hc_pvp_run:
                cursor.execute("UPDATE players SET hc_pvp_wins = hc_pvp_wins + 1, divine_orbs = divine_orbs + 5 WHERE user_id = ?", (user_id,))
            # --- КОНЕЦ НОВОГО БЛОКА ---
            elif not is_endless_run: # Обычная PVE победа
                cursor.execute("UPDATE players SET pve_wins = pve_wins + 1, divine_orbs = divine_orbs + 2 WHERE user_id = ?", (user_id,))
    
    if is_win and not is_pvp_run and not is_endless_run and not is_hc_pvp_run:
        quest_manager.update_quest_progress(user_id, 'pve_full_run_win')

# --- Функции для забегов (start, get, update) без изменений ---
def start_new_pve_run(user_id, initial_character_state, floor_bosses):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pve_runs WHERE user_id = ?", (user_id,))
        cursor.execute(
            "INSERT INTO pve_runs (user_id, current_floor, event_num, character_state, floor_bosses) VALUES (?, ?, ?, ?, ?)",
            (user_id, 1, 0, json.dumps(initial_character_state), json.dumps(floor_bosses))
        )

def get_pve_run_state(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT current_floor, event_num, character_state, floor_bosses FROM pve_runs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row: return None
        character_data = json.loads(row[2])
        character_data.setdefault('equipment', {})
        character_data.setdefault('pending_loot', [])
        character_data.setdefault('buffs', [])
        character_data.setdefault('permanent_bonuses', {})
        character_data.setdefault('cadiro_offer', None)
        return {
            'floor': row[0], 'event_num': row[1], 'character': character_data,
            'floor_bosses': json.loads(row[3])
        }

def update_pve_run_state(user_id, floor, event_num, character_state, floor_bosses):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE pve_runs SET current_floor = ?, event_num = ?, character_state = ?, floor_bosses = ? WHERE user_id = ?",
            (floor, event_num, json.dumps(character_state), json.dumps(floor_bosses), user_id)
        )

def save_character_for_pvp(owner_id, floor, character_data, telegram_user):
    """
    Сохраняет снимок персонажа для PVP.
    Принимает объект telegram_user для генерации корректного имени.
    """
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Логика генерации имени ---
    if telegram_user.username:
        display_name = telegram_user.username
    else:
        user_id_suffix = str(owner_id)[-4:]
        display_name = f"{telegram_user.first_name}#{user_id_suffix}"
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    # Принудительно обновляем имя в основной таблице игроков на всякий случай
    update_player_display_name(owner_id, display_name)

    pvp_snapshot = {
        'name': display_name,
        'stats': character_data['stats'],
        'equipment': character_data['equipment'],
        'class_id': character_data.get('class_id') # <-- ДОБАВЬТЕ ЭТУ СТРОКУ
    }
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pvp_characters (owner_id, floor, character_data) VALUES (?, ?, ?)",
            (owner_id, floor, json.dumps(pvp_snapshot))
        )

def update_player_display_name(user_id, display_name):
    """Принудительно обновляет отображаемое имя игрока в базе данных."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE players SET username = ? WHERE user_id = ?", (display_name, user_id))
               
def get_random_pvp_opponent(floor, exclude_user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT character_data FROM pvp_characters WHERE floor = ? AND owner_id != ? ORDER BY RANDOM() LIMIT 1",
            (floor, exclude_user_id)
        )
        row = cursor.fetchone()
        if not row:
            return None

        # --- НАЧАЛО ИЗМЕНЕНИЙ: Исправление здоровья и щита при загрузке ---
        # Загружаем данные персонажа из JSON
        character_data = json.loads(row[0])

        # Проверяем и восстанавливаем здоровье до максимального значения
        if 'stats' in character_data:
            stats = character_data['stats']
            max_health = stats.get('max_health', 100) # Используем 100 как запасной вариант
            stats['health'] = max_health

            # То же самое делаем для энергетического щита
            max_es = stats.get('max_energy_shield', 0)
            stats['energy_shield'] = max_es

        # Возвращаем уже исправленные данные
        return character_data
        # --- КОНЕЦ ИЗМЕНЕНИЙ ---

# --- Лидерборды ---
def get_pve_leaderboard():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, pve_wins FROM players WHERE pve_wins > 0 ORDER BY pve_wins DESC LIMIT 10")
        return cursor.fetchall()

def get_pvp_leaderboard():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, pvp_wins FROM players WHERE pvp_wins > 0 ORDER BY pvp_wins DESC LIMIT 10")
        return cursor.fetchall()
        
def get_champions_list():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.username, c.passive_wins
            FROM champions c JOIN players p ON c.player_id = p.user_id
            ORDER BY c.passive_wins DESC
        """)
        return cursor.fetchall()
        
# --- НОВЫЙ КОД: Функции для Чемпионов переписаны для поддержки множества чемпионов ---

def get_champions_list():
    """Возвращает список всех действующих чемпионов."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.username, c.passive_wins, c.lives
            FROM champions c
            JOIN players p ON c.player_id = p.user_id
            ORDER BY c.passive_wins DESC
        """)
        return cursor.fetchall()

def get_random_champion(exclude_user_id=None):
    """Возвращает полные данные случайного чемпиона из пула, включая его ID."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        query = """
            SELECT c.champion_id, c.player_id, p.username, c.character_data, c.lives, c.passive_wins
            FROM champions c
            JOIN players p ON c.player_id = p.user_id
        """
        params = []
        if exclude_user_id:
            query += " WHERE c.player_id != ?"
            params.append(exclude_user_id)
        
        query += " ORDER BY RANDOM() LIMIT 1"
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        if row:
            return {
                'champion_id': row[0], 'player_id': row[1], 'username': row[2],
                'character': json.loads(row[3]),
                'lives': row[4], 'passive_wins': row[5]
            }
        return None
def update_champion_character(player_id, character_data):
    """Обновляет данные персонажа существующего чемпиона и сбрасывает его жизни до 1."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            # ИЗМЕНЕНИЕ: lives = 1 вместо 3
            "UPDATE champions SET character_data = ?, lives = 1 WHERE player_id = ?",
            (json.dumps(character_data), player_id)
        )

    
def add_new_champion(player_id, character_data):
    """Добавляет нового чемпиона в пул, не удаляя старых."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # ИЗМЕНЕНИЕ: lives = 1 вместо 3
        cursor.execute(
            "INSERT INTO champions (player_id, character_data, passive_wins, lives) VALUES (?, ?, 0, 1)",
            (player_id, json.dumps(character_data))
        )
        # Также даем +1 к общему счету пвп побед за становление чемпионом
        cursor.execute("UPDATE players SET pvp_wins = pvp_wins + 1 WHERE user_id = ?", (player_id,))


def increment_champion_passive_win(champion_id, champion_player_id):
    """Увеличивает пассивные победы конкретного чемпиона и начисляет Mirror владельцу."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Обновляем победы ТОЛЬКО для чемпиона с конкретным ID
        cursor.execute("UPDATE champions SET passive_wins = passive_wins + 1 WHERE champion_id = ?", (champion_id,))
        # Награда по-прежнему начисляется владельцу
        cursor.execute("UPDATE players SET mirrors = mirrors + 1 WHERE user_id = ?", (champion_player_id,))
        

def delete_champion(champion_id):
    """Удаляет конкретного чемпиона из таблицы по его ID."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM champions WHERE champion_id = ?", (champion_id,))


def delete_pve_run(user_id):
    """Просто удаляет запись о текущем забеге, не начисляя наград."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pve_runs WHERE user_id = ?", (user_id,))

def is_player_a_champion(user_id):
    """Проверяет, является ли игрок уже активным чемпионом."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM champions WHERE player_id = ?", (user_id,))
        return cursor.fetchone() is not None

def reset_champion_lives(user_id):
    """Сбрасывает жизни существующего чемпиона до 1."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # ИЗМЕНЕНИЕ: lives = 1 вместо 3
        cursor.execute("UPDATE champions SET lives = 1 WHERE player_id = ?", (user_id,))

def increment_pvp_wins(user_id, amount=1):
    """Напрямую увеличивает счетчик PVP побед игрока."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE players SET pvp_wins = pvp_wins + ? WHERE user_id = ?", (amount, user_id))

def get_player_champions_info(user_id):
    """Возвращает информацию обо ВСЕХ чемпионах конкретного игрока в виде списка."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Ищем всех чемпионов по ID игрока
        cursor.execute("SELECT character_data, passive_wins, lives FROM champions WHERE player_id = ?", (user_id,))
        return cursor.fetchall() # Используем fetchall() для получения всех записей
        
def init_fishing_db():
    """Инициализирует таблицу для данных о рыбалке."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fishing_stats (
            user_id INTEGER PRIMARY KEY,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            chaos_orbs INTEGER DEFAULT 0,
            unlocked_rods TEXT DEFAULT '[]',
            inventory TEXT DEFAULT '[]',
            FOREIGN KEY(user_id) REFERENCES players(user_id)
        )''')
        print("Таблица 'fishing_stats' успешно инициализирована.")

def get_fishing_stats(user_id):
    """Возвращает статистику рыбалки игрока или создает новую запись."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # ИСПРАВЛЕНИЕ: Добавляем expedition_end_time в SELECT
        cursor.execute("SELECT level, xp, chaos_orbs, unlocked_rods, inventory, divine_shards, purchased_upgrades, unspent_perk_points, active_baits, expedition_end_time FROM fishing_stats WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                'level': row[0], 'xp': row[1], 'chaos_orbs': row[2],
                'unlocked_rods': json.loads(row[3]), 'inventory': json.loads(row[4]),
                'divine_shards': row[5],
                'purchased_upgrades': json.loads(row[6]),
                'unspent_perk_points': row[7],
                'active_baits': json.loads(row[8]),
                'expedition_end_time': row[9] # <-- ВОТ ИСПРАВЛЕНИЕ
            }
        else:
            # Создаем запись для нового рыбака
            default_stats = {'level': 1, 'xp': 0, 'chaos_orbs': 0, 'unlocked_rods': [], 'inventory': [], 'divine_shards': 0, 'purchased_upgrades': {}, 'unspent_perk_points': 0, 'active_baits': {}, 'expedition_end_time': 0}
            cursor.execute(
                # ИСПРАВЛЕНИЕ: Добавляем expedition_end_time в INSERT
                "INSERT INTO fishing_stats (user_id, unlocked_rods, inventory, divine_shards, purchased_upgrades, unspent_perk_points, active_baits, expedition_end_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, json.dumps(default_stats['unlocked_rods']), json.dumps(default_stats['inventory']), 0, json.dumps(default_stats['purchased_upgrades']), 0, json.dumps(default_stats['active_baits']), 0)
            )
            return default_stats


def update_fishing_stats(user_id, stats):
    """Обновляет статистику рыбалки игрока."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE fishing_stats SET 
               level = ?, xp = ?, chaos_orbs = ?, unlocked_rods = ?, inventory = ?, 
               divine_shards = ?, purchased_upgrades = ?, unspent_perk_points = ?, 
               active_baits = ?, expedition_end_time = ?
               WHERE user_id = ?""",
            (stats['level'], stats['xp'], stats['chaos_orbs'], 
             json.dumps(stats['unlocked_rods']), json.dumps(stats['inventory']),
             stats.get('divine_shards', 0), 
             json.dumps(stats.get('purchased_upgrades', {})),
             stats.get('unspent_perk_points', 0),
             json.dumps(stats.get('active_baits', {})),
             stats.get('expedition_end_time', 0), # <-- ВОТ ИСПРАВЛЕНИЕ
             user_id)
        )

# --- Функции для Мирового Босса ---

def get_world_boss():
    """Возвращает данные текущего мирового босса."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, stats, current_hp, spawn_time, end_time, is_active, is_defeated FROM world_boss WHERE boss_id = 1")
        row = cursor.fetchone()
        if row:
            return {
                'boss_id': 1, 'name': row[0], 'stats': json.loads(row[1]), 
                'current_hp': row[2], 'spawn_time': row[3], 'end_time': row[4],
                'is_active': row[5], 'is_defeated': row[6]
            }
        return None

def update_world_boss(boss_data):
    """Обновляет или создает запись о мировом боссе."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO world_boss 
               (boss_id, name, stats, current_hp, spawn_time, end_time, is_active, is_defeated) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (1, boss_data['name'], json.dumps(boss_data['stats']), boss_data['current_hp'], 
             boss_data['spawn_time'], boss_data['end_time'], boss_data['is_active'], boss_data['is_defeated'])
        )

def get_player_boss_damage(user_id):
    """Возвращает статистику участия игрока в битве с боссом."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT damage_dealt, last_attack_time, reward_claimed FROM world_boss_participants WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return {'damage_dealt': row[0], 'last_attack_time': row[1], 'reward_claimed': row[2]}
        return None

def update_player_boss_damage(user_id, damage):
    """Записывает урон, нанесенный игроком боссу."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Получаем имя игрока
        cursor.execute("SELECT username FROM players WHERE user_id = ?", (user_id,))
        username = cursor.fetchone()[0]
        # Добавляем или обновляем запись
        cursor.execute(
            """INSERT INTO world_boss_participants (user_id, username, damage_dealt) 
               VALUES (?, ?, ?) 
               ON CONFLICT(user_id) DO UPDATE SET 
               damage_dealt = damage_dealt + excluded.damage_dealt,
               username = excluded.username""",
            (user_id, username, damage)
        )

def set_player_boss_cooldown(user_id):
    """Устанавливает время последней атаки для отсчета кулдауна."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE world_boss_participants SET last_attack_time = ? WHERE user_id = ?", (int(time.time()), user_id))

def get_world_boss_leaderboard(limit=20):
    """Возвращает топ игроков по урону."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, damage_dealt FROM world_boss_participants WHERE damage_dealt > 0 ORDER BY damage_dealt DESC LIMIT ?", (limit,))
        return cursor.fetchall()

def reset_world_boss_participants():
    """Очищает таблицу участников для нового босса."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM world_boss_participants")

def set_player_reward_claimed(user_id):
    """Помечает, что игрок забрал свою награду."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE world_boss_participants SET reward_claimed = TRUE WHERE user_id = ?", (user_id,))

def add_rewards(user_id, divines, mirrors):
    """Добавляет игроку награды (Divine и Mirror)."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE players SET divine_orbs = divine_orbs + ?, mirrors = mirrors + ? WHERE user_id = ?", (divines, mirrors, user_id))
        
def add_fishing_chaos(user_id, chaos_amount):
    """Добавляет игроку Хаос Орбы (используем механику рыбалки)."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Убедимся, что у игрока есть запись в fishing_stats
        cursor.execute("INSERT OR IGNORE INTO fishing_stats (user_id) VALUES (?)", (user_id,))
        # Добавляем валюту
        cursor.execute("UPDATE fishing_stats SET chaos_orbs = chaos_orbs + ? WHERE user_id = ?", (chaos_amount, user_id))

def exchange_divine_shards(user_id):
    """
    Атомарно обменивает 10 осколков на 1 Divine Orb.
    Возвращает (True, "Сообщение") при успехе или (False, "Сообщение") при неудаче.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Проверяем баланс осколков
        cursor.execute("SELECT divine_shards FROM fishing_stats WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row or row[0] < 10:
            return False, "Недостаточно осколков для обмена\\! Нужно 10\\."
            
        # Выполняем обмен
        cursor.execute("UPDATE fishing_stats SET divine_shards = divine_shards - 10 WHERE user_id = ?", (user_id,))
        cursor.execute("UPDATE players SET divine_orbs = divine_orbs + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        
        return True, "Обмен успешен\\! Вы получили 1 💎 Divine Orb\\."
    
# --- Harvest and Custom Items ---

def get_harvest_stats(user_id):
    """Возвращает статистику Харвеста или создает новую запись."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT level, xp, lifeforce, crystalline_lifeforce, seeds, plants, fertilizers, beds, growth_speed_bonus FROM harvest_stats WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                'level': row[0], 'xp': row[1], 'lifeforce': row[2], 'crystalline_lifeforce': row[3],
                'seeds': json.loads(row[4]), 'plants': json.loads(row[5]), 'fertilizers': json.loads(row[6]),
                'beds': json.loads(row[7]), 'growth_speed_bonus': row[8]
            }
        else:
            # Создаем запись для нового фермера
            default_stats = {
                'level': 1, 'xp': 0, 'lifeforce': 0, 'crystalline_lifeforce': 0,
                'seeds': {}, 'plants': {}, 'fertilizers': {},
                'beds': [None] * 6, # 6 грядок, изначально пустые
                'growth_speed_bonus': 0.0
            }
            cursor.execute(
                """INSERT INTO harvest_stats (user_id, seeds, plants, fertilizers, beds, growth_speed_bonus) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, json.dumps(default_stats['seeds']), json.dumps(default_stats['plants']), 
                 json.dumps(default_stats['fertilizers']), json.dumps(default_stats['beds']), 
                 default_stats['growth_speed_bonus'])
            )
            return default_stats

def update_harvest_stats(user_id, stats):
    """Обновляет статистику Харвеста."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE harvest_stats SET 
               level = ?, xp = ?, lifeforce = ?, crystalline_lifeforce = ?, 
               seeds = ?, plants = ?, fertilizers = ?, beds = ?, growth_speed_bonus = ?
               WHERE user_id = ?""",
            (stats['level'], stats['xp'], stats['lifeforce'], stats['crystalline_lifeforce'],
             json.dumps(stats['seeds']), json.dumps(stats['plants']), json.dumps(stats['fertilizers']),
             json.dumps(stats['beds']), stats['growth_speed_bonus'], user_id)
        )

def add_custom_item(owner_id, name, rarity, slot, stats_json, floor):
    """Добавляет созданный игроком предмет в базу."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # ИЗМЕНЕНИЕ: Добавлен floor в INSERT
        cursor.execute(
            "INSERT INTO custom_items (owner_id, name, rarity, slot, stats, floor) VALUES (?, ?, ?, ?, ?, ?)",
            (owner_id, name, rarity, slot, stats_json, floor)
        )

def get_all_custom_items():
    """Возвращает все созданные игроками предметы с корректным типом."""
    slot_to_type_map = {
        'weapon1': 'Оружие', 'weapon2': 'Оружие', 'helmet': 'Шлем',
        'body_armour': 'Броня', 'gloves': 'Перчатки', 'boots': 'Ботинки',
        'ring1': 'Кольцо', 'ring2': 'Кольцо', 'amulet': 'Амулет', 'belt': 'Пояс'
    }
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # ИЗМЕНЕНИЕ: Добавлен floor в SELECT
        cursor.execute("SELECT name, rarity, slot, stats, floor FROM custom_items")
        items = []
        for row in cursor.fetchall():
            slot = row[2]
            display_type = slot_to_type_map.get(slot, 'Предмет')
            items.append({
                'name': row[0],
                'rarity': row[1],
                'slot': slot,
                'stats': json.loads(row[3]),
                'floor': row[4], # ИЗМЕНЕНИЕ: Добавлено поле floor
                'type': f'Кастомный {display_type}'
            })
        return items
    
def get_player_cards(user_id):
    """Возвращает словарь с картами игрока {card_id: count}."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT card_id, count FROM divination_cards WHERE user_id = ?", (user_id,))
        return {row[0]: row[1] for row in cursor.fetchall()}

def add_divination_card(user_id, card_id, amount=1):
    """Добавляет карту игроку или увеличивает ее количество."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO divination_cards (user_id, card_id, count) VALUES (?, ?, ?)
               ON CONFLICT(user_id, card_id) DO UPDATE SET count = count + excluded.count""",
            (user_id, card_id, amount)
        )

def remove_card_stack(user_id, card_id, amount):
    """Уменьшает количество карт у игрока после обмена."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE divination_cards SET count = count - ? WHERE user_id = ? AND card_id = ?",
            (amount, user_id, card_id)
        )

def update_endless_leaderboard(user_id, floor):
    """Обновляет рекорд игрока в Бесконечном Забеге, если он выше предыдущего."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Сначала получаем текущий рекорд
        cursor.execute("SELECT max_floor FROM endless_run_leaderboard WHERE user_id = ?", (user_id,))
        current_record = cursor.fetchone()
        
        # Обновляем только если новый результат лучше
        if not current_record or floor > current_record[0]:
            cursor.execute(
                "INSERT OR REPLACE INTO endless_run_leaderboard (user_id, max_floor) VALUES (?, ?)",
                (user_id, floor)
            )

def get_endless_max_floor(user_id):
    """Возвращает максимальный пройденный этаж для игрока из таблицы лидеров."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT max_floor FROM endless_run_leaderboard WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else 0
    

def add_xp_and_level_up(user_id, xp_to_add, cursor_obj=None):
    """
    Начисляет опыт и повышает уровень.
    Может работать как в своей транзакции, так и в существующей (через cursor_obj).
    """
    from game_content import PLAYER_XP_PER_LEVEL

    def _logic(cursor):
        """Внутренняя логика, работающая с переданным курсором."""
        cursor.execute("SELECT level, xp, skill_points FROM players WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        level, current_xp, skill_points = row
        new_xp = current_xp + xp_to_add
        levels_gained = 0
        
        # Цикл повышения уровня
        while level < 100 and new_xp >= PLAYER_XP_PER_LEVEL[level]:
            new_xp -= PLAYER_XP_PER_LEVEL[level]
            level += 1
            levels_gained += 1
        
        if level >= 100:
            new_xp = 0 # Обнуляем опыт на максимальном уровне
            
        new_skill_points = skill_points + levels_gained
        
        cursor.execute("UPDATE players SET level = ?, xp = ?, skill_points = ? WHERE user_id = ?", (level, new_xp, new_skill_points, user_id))
        
        if levels_gained > 0:
            return (f"✨ *УРОВЕНЬ ПОВЫШЕН\\!* ✨\n\n"
                    f"Вы достигли *{level}* уровня и получили *{levels_gained}* очко\\(а\\) умений\\!")
        else:
            return None

    if cursor_obj:
        # Если курсор передан, используем его
        return _logic(cursor_obj)
    else:
        # Иначе, создаем новое соединение
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            return _logic(cursor)

def get_player_skills(user_id):
    """Возвращает набор (set) ID всех изученных умений игрока."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT skill_id FROM player_skills WHERE user_id = ?", (user_id,))
        return {row[0] for row in cursor.fetchall()}

def spend_skill_point(user_id, skill_id):
    """Тратит очко умений (если требуется) и изучает новый навык."""
    from game_content import PASSIVE_SKILL_TREE # Локальный импорт

    skill_data = PASSIVE_SKILL_TREE.get(skill_id)
    if not skill_data:
        return False, "Умение не найдено\\."

    is_entry_node = skill_data.get('requires') is None
    cost = 0 if is_entry_node else 1

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        if cost > 0:
            cursor.execute("SELECT skill_points FROM players WHERE user_id = ?", (user_id,))
            points = cursor.fetchone()[0]
            if points < cost:
                # --- ИЗМЕНЕНИЕ: Возвращаем причину ошибки ---
                return False, "Недостаточно очков умений\\!"
            cursor.execute("UPDATE players SET skill_points = skill_points - ? WHERE user_id = ?", (cost, user_id))
        
        cursor.execute("INSERT INTO player_skills (user_id, skill_id) VALUES (?, ?)", (user_id, skill_id))
        return True, "Умение изучено\\!"
    
def reset_all_passive_skills(user_id):
    """Удаляет все изученные умения игрока."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM player_skills WHERE user_id = ?", (user_id,))
        
def refund_skill_points(user_id):
    """Возвращает все очки умений игроку, сбрасывая их до уровня персонажа."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Устанавливаем количество очков умений равным текущему уровню - 1
        # (т.к. на 1 уровне 0 очков, на 2 - 1 и т.д.)
        cursor.execute("""
            UPDATE players 
            SET skill_points = (level - 1) 
            WHERE user_id = ?
        """, (user_id,))

def handle_endless_victory_updates(user_id, run_state, xp_reward):
    """
    Атомарно обновляет состояние после победы над боссом в Бесконечном режиме:
    начисляет опыт и обновляет состояние забега.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Начисляем опыт, используя существующий курсор для атомарности
        level_up_msg = add_xp_and_level_up(user_id, xp_reward, cursor_obj=cursor)
        
        # Обновляем состояние забега в той же транзакции
        character_state = run_state['character']
        floor_bosses = run_state['floor_bosses']
        
        cursor.execute(
            "UPDATE pve_runs SET current_floor = ?, event_num = ?, character_state = ?, floor_bosses = ? WHERE user_id = ?",
            (run_state['floor'], run_state['event_num'], json.dumps(character_state), json.dumps(floor_bosses), user_id)
        )
    return level_up_msg

def handle_champion_victory_updates(challenger_id, champion_snapshot, defeated_champion_id, xp_reward):
    """
    Атомарно обрабатывает все изменения в БД после победы над чемпионом:
    добавляет нового чемпиона, удаляет старого, начисляет победу и опыт, удаляет забег.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # 1. Добавляем нового чемпиона
        cursor.execute(
            "INSERT INTO champions (player_id, character_data, passive_wins, lives) VALUES (?, ?, 0, 1)",
            (challenger_id, json.dumps(champion_snapshot))
        )
        
        # 2. Удаляем побежденного чемпиона
        cursor.execute("DELETE FROM champions WHERE champion_id = ?", (defeated_champion_id,))
        
        # 3. Начисляем победу в общий счетчик PVP
        cursor.execute("UPDATE players SET pvp_wins = pvp_wins + 1 WHERE user_id = ?", (challenger_id,))
        
        # 4. Начисляем опыт, используя тот же курсор для атомарности
        level_up_msg = add_xp_and_level_up(challenger_id, xp_reward, cursor_obj=cursor)
        
        # 5. Удаляем запись о текущем забеге претендента
        cursor.execute("DELETE FROM pve_runs WHERE user_id = ?", (challenger_id,))
        
    return level_up_msg

def reset_player_fishing_perk_stats(user_id):
    """Сбрасывает до 0 все перманентные статы, которые можно купить за очки рыбалки."""
    from game_content import FISHING_STAT_PERKS
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        for perk_id, perk_data in FISHING_STAT_PERKS.items():
            stat_column = perk_data['stat']
            # Безопасно обнуляем каждый столбец
            cursor.execute(f"UPDATE players SET {stat_column} = 0 WHERE user_id = ?", (user_id,))

def has_claimed_reward(user_id, month_year, leaderboard_type):
    """Проверяет, получил ли игрок уже награду за конкретный месяц и таблицу."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM monthly_rewards_claims WHERE user_id = ? AND month_year = ? AND leaderboard_type = ?",
                       (user_id, month_year, leaderboard_type))
        return cursor.fetchone() is not None

def mark_reward_as_claimed(user_id, month_year, leaderboard_type):
    """Помечает, что игрок получил награду."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO monthly_rewards_claims (user_id, month_year, leaderboard_type) VALUES (?, ?, ?)",
                       (user_id, month_year, leaderboard_type))
        
def add_referral(referrer_id, referred_id):
    """Добавляет запись о приглашении в базу данных."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Проверяем, не был ли этот пользователь уже приглашен
        cursor.execute("SELECT 1 FROM referrals WHERE referred_id = ?", (referred_id,))
        if cursor.fetchone():
            return False # Уже был приглашен
        
        cursor.execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)", (referrer_id, referred_id))
        return True

def get_all_referrals_with_levels(referrer_id):
    """Возвращает список всех приглашенных и их текущий уровень."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.referred_id, p.username, p.level
            FROM referrals r
            JOIN players p ON r.referred_id = p.user_id
            WHERE r.referrer_id = ?
            ORDER BY p.level DESC
        """, (referrer_id,))
        return cursor.fetchall()

def get_unclaimed_referrals(referrer_id, target_level):
    """Возвращает список приглашенных, достигших цели, за которых награда не получена."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.referred_id, p.username, p.level
            FROM referrals r
            JOIN players p ON r.referred_id = p.user_id
            WHERE r.referrer_id = ? AND r.reward_claimed = FALSE AND p.level >= ?
        """, (referrer_id, target_level))
        return cursor.fetchall()

def mark_referral_as_claimed(referrer_id, referred_id):
    """Помечает награду за приглашенного как полученную."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE referrals SET reward_claimed = TRUE WHERE referrer_id = ? AND referred_id = ?",
                       (referrer_id, referred_id))
        
def purchase_fishing_perk(user_id, perk_id, cost, stat_column, value_to_add):
    """
    (НОВАЯ ФУНКЦИЯ) Атомарно обрабатывает покупку перка рыбалки:
    списывает очки, добавляет стат и записывает покупку.
    """
    from game_content import FISHING_STAT_PERKS
    perk_name = FISHING_STAT_PERKS[perk_id]['name']

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Получаем текущие данные рыбалки
        cursor.execute("SELECT unspent_perk_points, purchased_upgrades FROM fishing_stats WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row or row[0] < cost:
            return False, "Недостаточно очков улучшений\\."
        
        points, upgrades_json = row
        upgrades = json.loads(upgrades_json or '{}')
        
        # Обновляем данные
        new_points = points - cost
        upgrades[perk_id] = upgrades.get(perk_id, 0) + 1
        
        # Применяем изменения
        cursor.execute(
            "UPDATE fishing_stats SET unspent_perk_points = ?, purchased_upgrades = ? WHERE user_id = ?",
            (new_points, json.dumps(upgrades), user_id)
        )
        cursor.execute(
            f"UPDATE players SET {stat_column} = {stat_column} + ? WHERE user_id = ?",
            (value_to_add, user_id)
        )
    
    return True, f"Вы успешно вложили очки в: *{escape_markdown(perk_name)}*\\!"


def reset_and_refund_fishing_perks(user_id):
    """
    (ИСПРАВЛЕНО) Атомарно сбрасывает перки рыбалки:
    1. Проверяет баланс хаос орбов.
    2. Читает, какие перки были куплены.
    3. Безопасно ВЫЧИТАЕТ их значения из статов игрока.
    4. Списывает стоимость сброса.
    5. Сбрасывает счетчик купленных перков.
    6. Возвращает все очки, заработанные за уровни рыбалки.
    """
    from game_content import FISHING_STAT_PERKS
    from fishing_manager import FISHING_PERK_RESET_COST # Импортируем стоимость
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Шаг 1: Получаем все необходимые данные в одной транзакции
        cursor.execute("SELECT purchased_upgrades, level, chaos_orbs FROM fishing_stats WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Не найден профиль рыбалки\\."
        
        upgrades_json, level, chaos_orbs = row
        
        # Шаг 2: Проверки перед выполнением
        if chaos_orbs < FISHING_PERK_RESET_COST:
            return False, f"Недостаточно хаос орбов! Нужно {FISHING_PERK_RESET_COST} 🟢."
            
        purchased_upgrades = json.loads(upgrades_json or '{}')
        if not purchased_upgrades:
            return False, "У вас нет улучшений от рыбалки для сброса\\."
            
        # Шаг 3: Вычитаем статы из таблицы players
        for perk_id, times_purchased in purchased_upgrades.items():
            if perk_id in FISHING_STAT_PERKS:
                perk_data = FISHING_STAT_PERKS[perk_id]
                stat_column = perk_data['stat']
                value_per_purchase = perk_data['value']
                total_value_to_remove = value_per_purchase * times_purchased
                
                cursor.execute(
                    f"UPDATE players SET {stat_column} = {stat_column} - ? WHERE user_id = ?",
                    (total_value_to_remove, user_id)
                )
        
        # Шаг 4: Списываем валюту, возвращаем очки и сбрасываем покупки
        total_points_to_refund = level - 1
        new_chaos_balance = chaos_orbs - FISHING_PERK_RESET_COST
        cursor.execute(
            "UPDATE fishing_stats SET unspent_perk_points = ?, purchased_upgrades = '{}', chaos_orbs = ? WHERE user_id = ?",
            (total_points_to_refund, new_chaos_balance, user_id)
        )
    
    return True, "Все ваши улучшения от рыбалки были успешно сброшены\\! Очки возвращены\\."

def get_current_race_bets():
    """Возвращает ставки всех игроков в текущей 'waiting' гонке."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Находим ID последней гонки
        cursor.execute("SELECT MAX(race_id) FROM rhoa_races")
        race_id_row = cursor.fetchone()
        if not race_id_row or race_id_row[0] is None:
            # Если гонок нет, создаем первую
            cursor.execute("INSERT INTO rhoa_races (race_id, user_id, username, rhoa_id, bet_amount, currency_type, status) VALUES (1, 0, 'dummy', 0, 0, 'none', 'finished')")
            return 1, []

        race_id = race_id_row[0]
        # Проверяем, не завершена ли она
        cursor.execute("SELECT user_id FROM rhoa_races WHERE race_id = ? AND status = 'waiting'", (race_id,))
        if not cursor.fetchall(): # Если в текущей гонке нет ждущих, значит она завершена, нужна новая
            race_id += 1
        
        cursor.execute("SELECT user_id, username, rhoa_id, bet_amount, currency_type FROM rhoa_races WHERE race_id = ? AND status = 'waiting'", (race_id,))
        return race_id, cursor.fetchall()

def add_bet_to_race(race_id, user_id, username, rhoa_id, bet_amount, currency_type):
    """Добавляет ставку игрока в текущую гонку."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO rhoa_races (race_id, user_id, username, rhoa_id, bet_amount, currency_type) VALUES (?, ?, ?, ?, ?, ?)",
            (race_id, user_id, username, rhoa_id, bet_amount, currency_type)
        )

def finish_race(race_id):
    """Помечает гонку как завершенную."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE rhoa_races SET status = 'finished' WHERE race_id = ?", (race_id,))

def get_last_race_results_for_player(user_id):
    """Находит последнюю завершенную гонку, в которой участвовал игрок."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Находим ID последней завершенной гонки, где был игрок
        cursor.execute("""
            SELECT race_id FROM rhoa_races 
            WHERE user_id = ? AND status = 'finished' 
            ORDER BY race_id DESC LIMIT 1
        """, (user_id,))
        row = cursor.fetchone()
        if not row:
            return None, None # Игрок не участвовал в завершенных гонках
        
        race_id = row[0]
        # Получаем всех участников этой гонки
        cursor.execute("SELECT user_id, username, rhoa_id, bet_amount, currency_type FROM rhoa_races WHERE race_id = ?", (race_id,))
        return race_id, cursor.fetchall()

def save_character_for_hc_pvp(owner_id, floor, character_data, telegram_user):
    """Сохраняет снимок персонажа для Хардкорного PVP."""
    if telegram_user.username:
        display_name = telegram_user.username
    else:
        user_id_suffix = str(owner_id)[-4:]
        display_name = f"{telegram_user.first_name}#{user_id_suffix}"
    
    update_player_display_name(owner_id, display_name)

    pvp_snapshot = {
        'name': display_name,
        'stats': character_data['stats'],
        'equipment': character_data['equipment'],
        'class_id': character_data.get('class_id') # <-- И ДОБАВЬТЕ ЭТУ СТРОКУ ЗДЕСЬ
    }
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO hc_pvp_characters (owner_id, floor, character_data) VALUES (?, ?, ?)",
            (owner_id, floor, json.dumps(pvp_snapshot))
        )

def get_random_hc_pvp_opponent(floor, exclude_user_id):
    """Возвращает случайного противника из пула Хардкорного PVP."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT character_data FROM hc_pvp_characters WHERE floor = ? AND owner_id != ? ORDER BY RANDOM() LIMIT 1",
            (floor, exclude_user_id)
        )
        row = cursor.fetchone()
        if not row:
            return None

        character_data = json.loads(row[0])
        if 'stats' in character_data:
            stats = character_data['stats']
            max_health = stats.get('max_health', 100)
            stats['health'] = max_health
            max_es = stats.get('max_energy_shield', 0)
            stats['energy_shield'] = max_es
        return character_data

def get_hc_pvp_leaderboard_with_ids():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, hc_pvp_wins FROM players WHERE hc_pvp_wins > 0 ORDER BY hc_pvp_wins DESC LIMIT 10")
        return cursor.fetchall()

def get_hc_champions_list_with_ids():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.player_id, p.username, c.passive_wins
            FROM hc_champions c JOIN players p ON c.player_id = p.user_id
            ORDER BY c.passive_wins DESC
        """)
        return cursor.fetchall()

def get_random_hc_champion(exclude_user_id=None):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        query = "SELECT c.champion_id, c.player_id, p.username, c.character_data, c.lives, c.passive_wins FROM hc_champions c JOIN players p ON c.player_id = p.user_id"
        params = []
        if exclude_user_id:
            query += " WHERE c.player_id != ?"
            params.append(exclude_user_id)
        query += " ORDER BY RANDOM() LIMIT 1"
        cursor.execute(query, params)
        row = cursor.fetchone()
        if row:
            return {'champion_id': row[0], 'player_id': row[1], 'username': row[2], 'character': json.loads(row[3]), 'lives': row[4], 'passive_wins': row[5]}
        return None

def add_new_hc_champion(player_id, character_data):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO hc_champions (player_id, character_data, passive_wins, lives) VALUES (?, ?, 0, 1)", (player_id, json.dumps(character_data)))
        cursor.execute("UPDATE players SET hc_pvp_wins = hc_pvp_wins + 1 WHERE user_id = ?", (player_id,))

def increment_hc_champion_passive_win(champion_id, champion_player_id):
    """Начисляет 3 Divine Orbs владельцу за пассивную победу."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE hc_champions SET passive_wins = passive_wins + 1 WHERE champion_id = ?", (champion_id,))
        cursor.execute("UPDATE players SET divine_orbs = divine_orbs + 3 WHERE user_id = ?", (champion_player_id,))

def delete_hc_champion(champion_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hc_champions WHERE champion_id = ?", (champion_id,))

def get_player_hc_champions_info(user_id):
    """Возвращает информацию о Хардкорных чемпионах игрока."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT character_data, passive_wins, lives FROM hc_champions WHERE player_id = ?", (user_id,))
        return cursor.fetchall()