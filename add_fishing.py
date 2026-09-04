# add_fishing.py
import database as db
from game_content import FISHING_XP_PER_LEVEL, PLAYER_XP_PER_LEVEL # <-- ИСПРАВЛЕНИЕ: Добавлен необходимый импорт

# --- ИЗМЕНИТЕ ЭТИ ЗНАЧЕНИЯ ---
USER_ID = 5302040216             # Замените на ID нужного пользователя
# --- Награды (0, если не нужно) ---
DIVINE_ORBS_TO_ADD = 1000
CHAOS_AMOUNT_TO_ADD = 0

# --- Уровни (0, если не нужно менять) ---
TARGET_CHARACTER_LEVEL = 100
TARGET_FISHING_LEVEL = 0
# -----------------------------

def give_divine_orbs(user_id, amount):
    """Начисляет Divine Orbs пользователю."""
    print(f"Попытка начислить {amount} 💎 пользователю с ID {user_id}...")
    db.add_rewards(user_id, divines=amount, mirrors=0)
    player_info = db.get_player_info(user_id)
    if player_info:
        print(f"✅ Успешно! Новый баланс: {player_info.get('divine_orbs', 0)} 💎.")
    else:
        print(f"❌ Ошибка: не удалось найти профиль игрока для {user_id}.")

def give_chaos_orbs(user_id, amount):
    """Начисляет Хаос Орбы пользователю."""
    print(f"Попытка начислить {amount} 🟢 пользователю с ID {user_id}...")
    db.add_fishing_chaos(user_id, amount)
    stats = db.get_fishing_stats(user_id)
    if stats:
        print(f"✅ Успешно! Новый баланс: {stats.get('chaos_orbs', 0)} 🟢.")
    else:
        print(f"❌ Ошибка: не удалось найти профиль рыбалки для {user_id}.")

def set_level(user_id, target_level, level_type):
    """
    (ОБЪЕДИНЕННАЯ ФУНКЦИЯ)
    Безопасно устанавливает уровень персонажа или рыбалки, начисляя очки.
    level_type может быть 'character' или 'fishing'.
    """
    # --- Конфигурация в зависимости от типа уровня ---
    if level_type == 'character':
        get_data_func = db.get_player_info
        points_field = 'skill_points'
        max_level_table = PLAYER_XP_PER_LEVEL
        log_name = "персонажа"
        profile_name = "игрока"
    elif level_type == 'fishing':
        get_data_func = db.get_fishing_stats
        points_field = 'unspent_perk_points'
        max_level_table = FISHING_XP_PER_LEVEL
        log_name = "рыбалки"
        profile_name = "рыбалки"
    else:
        print(f"❌ Неизвестный тип уровня: {level_type}")
        return
    # ---------------------------------------------

    print(f"Попытка установить {target_level} уровень {log_name} для пользователя {user_id}...")
    
    stats = get_data_func(user_id)
    if not stats:
        print(f"❌ Ошибка: Профиль {profile_name} для пользователя {user_id} не найден.")
        return

    current_level = stats.get('level', 1)
    if target_level <= current_level:
        print(f"❌ Ошибка: Целевой уровень ({target_level}) не выше текущего ({current_level}).")
        return
    
    # Проверка максимального уровня
    max_level = len(max_level_table) - 1
    if target_level > max_level:
        print(f"❌ Ошибка: Максимальный уровень {log_name} - {max_level}.")
        return

    levels_gained = target_level - current_level
    new_points = stats.get(points_field, 0) + levels_gained

    # --- Обновление данных в зависимости от типа ---
    if level_type == 'character':
        with db.sqlite3.connect(db.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE players SET level = ?, xp = 0, skill_points = ? WHERE user_id = ?",
                (target_level, new_points, user_id)
            )
    elif level_type == 'fishing':
        stats['level'] = target_level
        stats['xp'] = 0
        stats[points_field] = new_points
        db.update_fishing_stats(user_id, stats)
    # ---------------------------------------------

    print(f"✅ Успешно! Пользователь {user_id} теперь имеет:")
    print(f"   - Уровень {log_name}: {target_level}")
    print(f"   - Нераспределенных очков: {new_points}")

def main():
    """
    Главная функция для выполнения всех административных действий.
    """
    print("--- Запуск административного скрипта ---")
    
    if DIVINE_ORBS_TO_ADD > 0:
        give_divine_orbs(USER_ID, DIVINE_ORBS_TO_ADD)
        print("-" * 20)
    if CHAOS_AMOUNT_TO_ADD > 0:
        give_chaos_orbs(USER_ID, CHAOS_AMOUNT_TO_ADD)
        print("-" * 20)
        
    if TARGET_CHARACTER_LEVEL > 0:
        set_level(USER_ID, TARGET_CHARACTER_LEVEL, 'character')
        print("-" * 20)
    if TARGET_FISHING_LEVEL > 0:
        set_level(USER_ID, TARGET_FISHING_LEVEL, 'fishing')
        print("-" * 20)
            
    print("--- Скрипт завершил работу ---")

if __name__ == '__main__':
    main()