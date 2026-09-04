# harvest_manager.py
import time
import json
import random
from telegram import Update
from telegram.ext import ContextTypes
import database as db
import ui_components as ui
from game_content import HARVEST_SEEDS, HARVEST_PLANTS, HARVEST_FERTILIZERS, HARVEST_BED_UPGRADES, HARVEST_CRAFTING_CONFIG
from utils import escape_markdown

def get_harvest_level_info(xp):
    """Определяет уровень и прогресс по опыту."""
    from game_content import HARVEST_XP_PER_LEVEL
    level = 1
    xp_for_next = HARVEST_XP_PER_LEVEL[level]
    while xp >= xp_for_next:
        xp -= xp_for_next
        level += 1
        if level >= len(HARVEST_XP_PER_LEVEL):
            return 100, 0, 'MAX' # Максимальный уровень
        xp_for_next = HARVEST_XP_PER_LEVEL[level]
    return level, xp, xp_for_next

def add_xp(stats, amount):
    """
    ИЗМЕНЕНИЕ: Начисляет опыт в переданный объект stats, не сохраняя его в БД.
    Возвращает обновленный объект stats и информацию о повышении уровня.
    """
    stats['xp'] += amount
    
    # Используем старый уровень из объекта, чтобы избежать лишнего вызова get_harvest_level_info
    current_level = stats['level']
    new_level, _, _ = get_harvest_level_info(stats['xp'])
    
    leveled_up = new_level > current_level
    if leveled_up:
        stats['level'] = new_level
        
    return stats, leveled_up, new_level

def add_seed(user_id, seed_id):
    """Добавляет семя игроку."""
    stats = db.get_harvest_stats(user_id)
    stats['seeds'][seed_id] = stats['seeds'].get(seed_id, 0) + 1
    db.update_harvest_stats(user_id, stats)

def plant_seed(user_id, bed_index, seed_id):
    """Сажает семя в грядку."""
    stats = db.get_harvest_stats(user_id)
    seed_info = HARVEST_SEEDS[seed_id]
    
    if stats['seeds'].get(seed_id, 0) < 1:
        return False, "У вас нет таких семян\\."

    if seed_info['tier'] > 1:
        fertilizer_id = f"fertilizer_t{seed_info['tier']}"
        if stats['fertilizers'].get(fertilizer_id, 0) < 1:
            return False, f"Для посадки семян Т{seed_info['tier']} требуется удобрение того же тира\\."
        stats['fertilizers'][fertilizer_id] -= 1

    base_growth_time = seed_info['growth_time']
    speed_bonus = stats.get('growth_speed_bonus', 0)
    final_growth_time = int(base_growth_time * (1 - speed_bonus))

    stats['seeds'][seed_id] -= 1
    stats['beds'][bed_index] = {
        'seed_id': seed_id,
        'plant_time': int(time.time()),
        'growth_duration': final_growth_time
    }
    db.update_harvest_stats(user_id, stats)
    return True, f"Семя '{escape_markdown(seed_info['name'])}' посажено\\! Созреет через ~{final_growth_time // 60} мин\\."

def harvest_plant(user_id, bed_index):
    """Собирает урожай с грядки."""
    stats = db.get_harvest_stats(user_id)
    bed = stats['beds'][bed_index]

    # --- НАЧАЛО ИЗМЕНЕНИЙ: Проверка на пустую грядку ---
    if bed is None:
        return False, "Эта грядка уже пуста или урожай был собран\\."
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    seed_id = bed['seed_id']
    plant_id = HARVEST_SEEDS[seed_id]['produces']
    plant_info = HARVEST_PLANTS[plant_id]

    # Добавляем растение в инвентарь
    stats['plants'][plant_id] = stats['plants'].get(plant_id, 0) + 1
    # Освобождаем грядку
    stats['beds'][bed_index] = None
    
    stats, leveled_up, new_level = add_xp(stats, plant_info['xp'])
    
    db.update_harvest_stats(user_id, stats)
    
    message = f"Вы собрали урожай: *{escape_markdown(plant_info['name'])}*\\! Получено *{plant_info['xp']}* опыта\\."
    if leveled_up:
        message += f"\n\n🎉 *УРОВЕНЬ ХАРВЕСТА ПОВЫШЕН\\!* 🎉\nВы достигли *{new_level}* уровня\\!"
    return True, message

def buy_fertilizer(user_id, fertilizer_id, amount=1):
    """Покупка удобрения."""
    stats = db.get_harvest_stats(user_id)
    cost_per_one = HARVEST_FERTILIZERS[fertilizer_id]['cost']
    total_cost = cost_per_one * amount
    
    if stats['lifeforce'] < total_cost:
        return False, f"Недостаточно Жизненной Силы\\! Нужно {total_cost} 🟢\\."
        
    stats['lifeforce'] -= total_cost
    stats['fertilizers'][fertilizer_id] = stats['fertilizers'].get(fertilizer_id, 0) + amount
    db.update_harvest_stats(user_id, stats)
    return True, f"Вы купили *{escape_markdown(HARVEST_FERTILIZERS[fertilizer_id]['name'])}* x{amount}\\!"

def exchange_all_plants(user_id):
    """Обмен всех растений на валюту."""
    stats = db.get_harvest_stats(user_id)
    if not any(stats['plants'].values()):
        return 0, 0, 0
        
    total_lifeforce = 0
    total_crystalline = 0
    total_items = 0

    for plant_id, count in stats['plants'].items():
        if count > 0:
            plant_info = HARVEST_PLANTS[plant_id]
            total_items += count
            if plant_info['currency'] == 'lifeforce':
                total_lifeforce += plant_info['value'] * count
            elif plant_info['currency'] == 'crystalline':
                total_crystalline += plant_info['value'] * count
    
    stats['lifeforce'] += total_lifeforce
    stats['crystalline_lifeforce'] += total_crystalline
    stats['plants'] = {}
    db.update_harvest_stats(user_id, stats)
    
    return total_items, total_lifeforce, total_crystalline

def buy_bed_upgrade(user_id, upgrade_id):
    """Покупка улучшения для грядок."""
    stats = db.get_harvest_stats(user_id)
    upgrade_info = HARVEST_BED_UPGRADES[upgrade_id]
    
    if stats.get('growth_speed_bonus', 0) >= upgrade_info['bonus']:
        return False, "У вас уже есть такое или лучшее улучшение\\."
        
    if stats['lifeforce'] < upgrade_info['cost']:
        return False, "Недостаточно Жизненной Силы\\."
        
    stats['lifeforce'] -= upgrade_info['cost']
    stats['growth_speed_bonus'] = upgrade_info['bonus']
    db.update_harvest_stats(user_id, stats)
    
    return True, f"Улучшение '{escape_markdown(upgrade_info['name'])}' приобретено\\!"

async def process_casino_bet(user_id, currency, amount_str):
    """Обработка ставки в казино. Возвращает словарь с результатом или строку с ошибкой."""
    stats = db.get_harvest_stats(user_id)
    player_info = db.get_player_info(user_id)
    
    if stats.get('crystalline_lifeforce', 0) < 1:
        return "Для ставки требуется 1 Кристаллическая Сила\\."

    balance = player_info.get(currency, 0)
    amount = 0
    if amount_str == 'all':
        amount = balance
    else:
        amount = int(amount_str)

    if balance < amount or amount <= 0:
        return "Недостаточно средств для такой ставки\\."

    stats['crystalline_lifeforce'] -= 1
    db.update_harvest_stats(user_id, stats)
    db.add_rewards(user_id, -amount if currency == 'divine_orbs' else 0, -amount if currency == 'mirrors' else 0)
    
    currency_map = {'divine_orbs': '💎 Divine Orb', 'mirrors': '🪞 Mirror'}
    
    if random.random() < 0.5: # Проигрыш
        return {'status': 'loss', 'lost_amount': amount, 'currency_name': currency_map[currency]}
    else: # Выигрыш
        winnings = amount * 2
        db.add_rewards(user_id, winnings if currency == 'divine_orbs' else 0, winnings if currency == 'mirrors' else 0)
        return {'status': 'win', 'winnings': winnings, 'currency_name': currency_map[currency]}


async def start_item_craft(user_id, context: ContextTypes.DEFAULT_TYPE, rarity):
    """Начинает сессию крафта, проверяет стоимость и запрашивает этаж."""
    # ИЗМЕНЕНИЕ: Проверка стоимости происходит здесь
    config = HARVEST_CRAFTING_CONFIG['rarity_config'][rarity]
    stats = db.get_harvest_stats(user_id)
    
    if stats.get('crystalline_lifeforce', 0) < config['cost']:
        return False, "Недостаточно Кристаллической Силы для создания предмета такой редкости\\."
    
    context.user_data['item_craft_session'] = {
        'rarity': rarity,
        'cost': config['cost'], # Сразу сохраняем стоимость
    }
    return True, "Редкость выбрана\\. Теперь укажите, на каком этаже будет выпадать ваш предмет\\."


async def set_craft_floor_and_start(user_id, context: ContextTypes.DEFAULT_TYPE, floor):
    """Устанавливает этаж и инициализирует очки крафта."""
    session = context.user_data.get('item_craft_session')
    if not session or 'rarity' not in session:
        return False, "Сессия крафта не найдена или не выбрана редкость\\. Начните заново\\."

    rarity = session['rarity']
    try:
        # ИЗМЕНЕНИЕ: Получаем только очки из новой структуры
        points = HARVEST_CRAFTING_CONFIG['floor_points'][str(floor)][rarity]
    except KeyError:
        return False, "Ошибка конфигурации для данного этажа и редкости\\."

    # ИЗМЕНЕНИЕ: Инициализируем полную сессию здесь, стоимость уже проверена
    session.update({
        'floor': floor,
        'points': points,
        'max_points': points,
        'slot': None,
        'name': None,
        'stats': {}
    })
    
    return True, "Этаж выбран\\. Теперь выберите слот для вашего будущего предмета\\."

async def add_stat_to_custom_item(user_id, context: ContextTypes.DEFAULT_TYPE, stat_id):
    """Добавляет стат к создаваемому предмету."""
    session = context.user_data.get('item_craft_session')
    if not session:
        return False, "Сессия крафта не найдена\\."

    stat_config = HARVEST_CRAFTING_CONFIG['stat_costs'][stat_id]
    cost = stat_config['cost']
    
    if session['points'] < cost:
        return False, "Недостаточно очков для добавления этого свойства\\."
        
    session['points'] -= cost
    session['stats'][stat_id] = session['stats'].get(stat_id, 0) + stat_config['value']
    
    return True, "Свойство добавлено\\."

async def finalize_custom_item(user_id, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет созданный предмет в базу данных."""
    session = context.user_data.get('item_craft_session')
    if not session:
        return False, "Сессия крафта не найдена\\."
        
    stats = db.get_harvest_stats(user_id)
    stats['crystalline_lifeforce'] -= session['cost']
    db.update_harvest_stats(user_id, stats)
    
    # ИЗМЕНЕНИЕ: Передаем floor в функцию сохранения
    db.add_custom_item(
        owner_id=user_id,
        name=session['name'],
        rarity=session['rarity'],
        slot=session['slot'],
        stats_json=json.dumps(session['stats']),
        floor=session['floor']
    )
    
    del context.user_data['item_craft_session']
    
    return True, "Ваш предмет был успешно создан и добавлен в мир игры\\!"