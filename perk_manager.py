# perk_manager.py
import database as db

# Каталог доступных для покупки перков
PERK_CATALOG = {
    # Усилено: больше статов за ту же цену
    'add_atk_1': {'name': "+2 к базовой Атаке", 'cost': 3, 'stat': 'perm_attack_bonus', 'value': 2},
    'add_hp_5':  {'name': "+10 к базовому Здоровью", 'cost': 3, 'stat': 'perm_health_bonus', 'value': 10},
    'add_es_3':  {'name': "+6 к базовому Энергощиту", 'cost': 3, 'stat': 'perm_es_bonus', 'value': 6},

    # Средние улучшения за 10 Divine Orbs
    'add_crit_1': {'name': "+1% к базовому Крит. шансу", 'cost': 8, 'stat': 'perm_crit_chance_bonus', 'value': 1},
    'add_dodge_1':{'name': "+1% к базовому Увороту", 'cost': 8, 'stat': 'perm_dodge_chance_bonus', 'value': 1},
    'add_block_1':{'name': "+1% к базовому Шансу блока", 'cost': 8, 'stat': 'perm_block_chance_bonus', 'value': 1},
    'add_def_1':  {'name': "+1% к базовой Защите", 'cost': 8, 'stat': 'perm_defense_bonus', 'value': 1},
}

MIRROR_PERK_CATALOG = {
    'add_dd_1': {'name': "+1% к шансу Двойного Урона", 'cost': 2, 'currency': 'mirrors', 'stat': 'perm_double_damage_bonus', 'value': 1},
    'add_pen_2':{'name': "+2% к Пробитию Защиты", 'cost': 3, 'currency': 'mirrors', 'stat': 'perm_defense_penetration_bonus', 'value': 2},
    'add_leech_1':{'name': "+1% к Вампиризму Здоровья", 'cost': 5, 'currency': 'mirrors', 'stat': 'perm_lifesteal_bonus', 'value': 1},
    'add_mf_10':{'name': "+10% к Поиску Предметов", 'cost': 1, 'currency': 'mirrors', 'stat': 'perm_magic_find_bonus', 'value': 10},
}

def get_player_perks(user_id):
    """Возвращает словарь со всеми купленными перками игрока (Divine и Mirror)."""
    with db.sqlite3.connect(db.DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                perm_attack_bonus, perm_health_bonus, perm_es_bonus, 
                perm_crit_chance_bonus, perm_dodge_chance_bonus, perm_block_chance_bonus, 
                perm_defense_bonus, perm_double_damage_bonus, perm_defense_penetration_bonus,
                perm_lifesteal_bonus, perm_magic_find_bonus
            FROM players 
            WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                'attack': row[0], 'max_health': row[1], 'max_energy_shield': row[2],
                'crit_chance': row[3], 'dodge_chance': row[4], 'block_chance': row[5], 'defense': row[6],
                'double_damage_chance': row[7], 'defense_penetration': row[8], 'lifesteal': row[9], 'magic_find': row[10]
            }
        return {}

def purchase_perk(user_id, perk_id):
    """Обрабатывает покупку перка, атомарно обновляя данные."""
    # Объединяем каталоги для поиска
    full_catalog = {**PERK_CATALOG, **MIRROR_PERK_CATALOG}
    
    if perk_id not in full_catalog:
        return False, "Перк не найден\\."

    perk = full_catalog[perk_id]
    cost = perk['cost']
    stat_column = perk['stat']
    value = perk['value']
    # Определяем тип валюты для проверки баланса
    currency_type = perk.get('currency', 'divine_orbs') 

    player_info = db.get_player_info(user_id)
    if not player_info or player_info.get(currency_type, 0) < cost:
        currency_name = "Divine Orbs" if currency_type == 'divine_orbs' else "Mirrors of Kalandra"
        return False, f"Недостаточно {currency_name}\\."

    with db.sqlite3.connect(db.DB_NAME) as conn:
        cursor = conn.cursor()
        # Вычитаем стоимость из правильного столбца валюты
        cursor.execute(f"UPDATE players SET {currency_type} = {currency_type} - ? WHERE user_id = ?", (cost, user_id))
        # Добавляем бонус
        cursor.execute(f"UPDATE players SET {stat_column} = {stat_column} + ? WHERE user_id = ?", (value, user_id))
        conn.commit()
    
    return True, f"Вы успешно приобрели перк: {perk['name']}\\!"