# admin_tools.py
import database as db
import copy
from game_content import FISHING_XP_PER_LEVEL, PLAYER_XP_PER_LEVEL, CONTENT

# --- ИЗМЕНИТЕ ЭТИ ЗНАЧЕНИЯ ---
USER_ID = 381025103 # Замените на ID нужного пользователя

# --- Набор предметов для выдачи (0, если не нужно) ---
ITEM_SEQUENCE_TO_GIVE = [
    'Единство',
    'Dragon Heart Onyx Amulet',
    'Предвестник Заката',
    'Воля Императора',
    'Солнечный камень',
    'Хрупкая Корона',
    'Плащ Тени',
    'Маска Тени',
    'The Pariah'
]
# -----------------------------

# --- Остальные настройки (0, если не нужно) ---
DIVINE_ORBS_TO_ADD = 0
CHAOS_AMOUNT_TO_ADD = 0
TARGET_CHARACTER_LEVEL = 0
TARGET_FISHING_LEVEL = 0
# -------------------------------------------------

# --- НОВЫЙ БЛОК: Улучшенный поиск предметов ---
_item_lookup_cache = None

def _build_item_lookup():
    """Создает и кэширует плоский словарь для быстрого поиска всех предметов по имени."""
    global _item_lookup_cache
    if _item_lookup_cache is not None:
        return _item_lookup_cache
    
    print("Создание кэша предметов для поиска...")
    lookup = {}
    for floor_data in CONTENT.values():
        for rarity, items in floor_data.get('items', {}).items():
            for item in items:
                if item['name'] not in lookup:
                    item_data = copy.deepcopy(item)
                    item_data['rarity'] = rarity
                    lookup[item['name']] = item_data
    _item_lookup_cache = lookup
    print(f"Кэш создан. Найдено {len(lookup)} уникальных предметов.")
    return _item_lookup_cache

def give_item_sequence(user_id, item_names):
    """
    (ИСПРАВЛЕНО)
    Надежно добавляет последовательность предметов в 'pending_loot' игрока.
    """
    print(f"Попытка выдать набор предметов пользователю {user_id}...")
    
    run_state = db.get_pve_run_state(user_id)
    if not run_state:
        print(f"❌ Ошибка: У пользователя {user_id} нет активного забега. Сначала начните забег в боте.")
        return

    item_lookup = _build_item_lookup()
    items_to_give = []
    not_found_items = []

    for item_name in item_names:
        found_item_data = item_lookup.get(item_name)
        if found_item_data:
            items_to_give.append(copy.deepcopy(found_item_data))
        else:
            not_found_items.append(item_name)

    if items_to_give:
        char = run_state['character']
        char.setdefault('pending_loot', []).extend(items_to_give)
        char['current_events'] = []
        db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
        
        added_names = [f"'{item['name']}'" for item in items_to_give]
        print(f"✅ Успешно! Предметы {', '.join(added_names)} добавлены в 'pending_loot'.")
        print("   Зайдите в игру и продолжите забег, чтобы увидеть предметы.")
    else:
        print("⚠️ Не было добавлено ни одного предмета.")

    if not_found_items:
        print(f"❌ Внимание! Следующие предметы не были найдены в игре: {', '.join(not_found_items)}")

# --- Остальные функции (без изменений) ---

def give_divine_orbs(user_id, amount):
    print(f"Попытка начислить {amount} 💎 пользователю с ID {user_id}...")
    db.add_rewards(user_id, divines=amount, mirrors=0)
    player_info = db.get_player_info(user_id)
    if player_info: print(f"✅ Успешно! Новый баланс: {player_info.get('divine_orbs', 0)} 💎.")
    else: print(f"❌ Ошибка: не удалось найти профиль игрока для {user_id}.")

def give_chaos_orbs(user_id, amount):
    print(f"Попытка начислить {amount} 🟢 пользователю с ID {user_id}...")
    db.add_fishing_chaos(user_id, amount)
    stats = db.get_fishing_stats(user_id)
    if stats: print(f"✅ Успешно! Новый баланс: {stats.get('chaos_orbs', 0)} 🟢.")
    else: print(f"❌ Ошибка: не удалось найти профиль рыбалки для {user_id}.")

def set_level(user_id, target_level, level_type):
    if level_type == 'character':
        get_data_func, points_field, max_level_table, log_name, profile_name = (db.get_player_info, 'skill_points', PLAYER_XP_PER_LEVEL, "персонажа", "игрока")
    elif level_type == 'fishing':
        get_data_func, points_field, max_level_table, log_name, profile_name = (db.get_fishing_stats, 'unspent_perk_points', FISHING_XP_PER_LEVEL, "рыбалки", "рыбалки")
    else:
        print(f"❌ Неизвестный тип уровня: {level_type}"); return

    print(f"Попытка установить {target_level} уровень {log_name} для пользователя {user_id}...")
    stats = get_data_func(user_id)
    if not stats: print(f"❌ Ошибка: Профиль {profile_name} для {user_id} не найден."); return
    current_level = stats.get('level', 1)
    if target_level <= current_level: print(f"❌ Ошибка: Целевой уровень ({target_level}) не выше текущего ({current_level})."); return
    max_level = len(max_level_table) - 1
    if target_level > max_level: print(f"❌ Ошибка: Максимальный уровень {log_name} - {max_level}."); return

    levels_gained = target_level - current_level
    new_points = stats.get(points_field, 0) + levels_gained

    if level_type == 'character':
        with db.sqlite3.connect(db.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE players SET level = ?, xp = 0, skill_points = ? WHERE user_id = ?", (target_level, new_points, user_id))
    elif level_type == 'fishing':
        stats.update({'level': target_level, 'xp': 0, points_field: new_points})
        db.update_fishing_stats(user_id, stats)

    print(f"✅ Успешно! Пользователь {user_id} теперь имеет:\n   - Уровень {log_name}: {target_level}\n   - Нераспределенных очков: {new_points}")

def main():
    print("--- Запуск административного скрипта ---")
    
    if DIVINE_ORBS_TO_ADD > 0: give_divine_orbs(USER_ID, DIVINE_ORBS_TO_ADD); print("-" * 20)
    if CHAOS_AMOUNT_TO_ADD > 0: give_chaos_orbs(USER_ID, CHAOS_AMOUNT_TO_ADD); print("-" * 20)
    if TARGET_CHARACTER_LEVEL > 0: set_level(USER_ID, TARGET_CHARACTER_LEVEL, 'character'); print("-" * 20)
    if TARGET_FISHING_LEVEL > 0: set_level(USER_ID, TARGET_FISHING_LEVEL, 'fishing'); print("-" * 20)
    
    if ITEM_SEQUENCE_TO_GIVE:
        give_item_sequence(USER_ID, ITEM_SEQUENCE_TO_GIVE)
        print("-" * 20)
            
    print("--- Скрипт завершил работу ---")

if __name__ == '__main__':
    main()