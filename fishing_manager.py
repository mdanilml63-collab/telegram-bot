# fishing_manager.py (полная замена файла)

import random
import time
import math
import copy
import database as db
import quest_manager
from game_content import (FISHING_RODS, FISHING_LOOT_TABLE, FISHING_XP_PER_LEVEL, 
                          HARVEST_SEEDS, FISHING_STAT_PERKS, FISHING_BAITS)
from shared_data import USER_ACTION_LOCK
from utils import escape_markdown
import harvest_manager

FISHING_COOLDOWN = 10 # 10 секунд

def get_player_active_rod(stats):
    """Возвращает характеристики самой лучшей купленной удочки игрока."""
    unlocked_rods = stats.get('unlocked_rods', [])
    if not unlocked_rods:
        return None
    best_rod_id = unlocked_rods[-1]
    return FISHING_RODS[best_rod_id]

def _check_level_up(stats, user_id):
    """Проверяет, повышает уровень и начисляет очки перков."""
    from game_content import FISHING_XP_PER_LEVEL
    
    leveled_up = False
    old_level = stats['level']
    
    # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    # Определяем максимальный уровень динамически, по длине таблицы опыта
    max_level = len(FISHING_XP_PER_LEVEL) - 1
    
    if stats['level'] >= max_level:
        return stats, False # Если уровень уже максимальный, выходим

    xp_needed = FISHING_XP_PER_LEVEL[stats['level']]
    while stats['xp'] >= xp_needed:
        stats['xp'] -= xp_needed
        stats['level'] += 1
        leveled_up = True
        quest_manager.update_quest_progress(user_id, 'fish_level_up')

        # Если достигли нового максимального уровня, выходим из цикла
        if stats['level'] >= max_level:
            stats['xp'] = 0 # Обнуляем опыт на максимальном уровне
            break
        
        # Обновляем требование по опыту для следующего уровня
        xp_needed = FISHING_XP_PER_LEVEL[stats['level']]
        
    levels_gained = stats['level'] - old_level
    if levels_gained > 0:
        stats['unspent_perk_points'] = stats.get('unspent_perk_points', 0) + levels_gained
        
    return stats, leveled_up

def start_fishing(user_id):
    """Основная функция для процесса рыбалки с учетом наживок."""
    last_action_time = USER_ACTION_LOCK.get(f"fishing_{user_id}", 0)
    if time.time() - last_action_time < FISHING_COOLDOWN:
        return {'status': 'cooldown', 'wait_time': int(FISHING_COOLDOWN - (time.time() - last_action_time))}

    stats = db.get_fishing_stats(user_id)
    
    # --- НАЧАЛО ИЗМЕНЕНИЙ: БЛОКИРОВКА НА ВРЕМЯ ЭКСПЕДИЦИИ ---
    if stats.get('expedition_end_time', 0) > time.time():
        return {'status': 'on_expedition'}
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    
    active_rod = get_player_active_rod(stats)

    if not active_rod:
        return {'status': 'no_rod'}

    USER_ACTION_LOCK[f"fishing_{user_id}"] = time.time()
    
    # --- НОВАЯ ЛОГИКА: Применение и списание наживки ---
    active_baits = stats.get('active_baits', {})
    baits_updated = False
    if active_baits:
        for bait_id, data in list(active_baits.items()):
            data['casts'] -= 1
            if data['casts'] <= 0:
                del active_baits[bait_id]
        baits_updated = True
        stats['active_baits'] = active_baits
    
    # Сразу обновляем БД, если наживка была использована
    if baits_updated:
        db.update_fishing_stats(user_id, stats)
    # --- КОНЕЦ НОВОЙ ЛОГИКИ ---

    if random.randint(1, 100) > active_rod['stats']['catch_chance']:
        return {'status': 'fail'}

    # --- НОВАЯ ЛОГИКА: Шанс на сундук с учетом наживки ---
    chest_chance_multiplier = 1.0
    if 'bait_lucky' in active_baits:
        chest_chance_multiplier = FISHING_BAITS['bait_lucky']['effect']['multiplier']

    if random.random() < (0.01 * chest_chance_multiplier): # Базовый шанс 1%
        chest_data = FISHING_LOOT_TABLE['tier4']['special'][0]
        stats['divine_shards'] = stats.get('divine_shards', 0) + 1
        db.update_fishing_stats(user_id, stats)
        return {
            'status': 'success_special',
            'item_name': chest_data['name'],
            'new_shard_balance': stats['divine_shards']
        }
    # --- КОНЕЦ НОВОЙ ЛОГИКИ ---

    level = stats['level']
    available_tiers = ['tier1']
    if level >= 20: available_tiers.append('tier2')
    if level >= 40: available_tiers.append('tier3')
    if level >= 60: available_tiers.append('tier4')
    if level >= 80: available_tiers.append('tier5')
    
    chosen_tier_id = random.choices(available_tiers, weights=[i+1 for i in range(len(available_tiers))], k=1)[0]
    
    # --- НОВАЯ ЛОГИКА: Расчет редкости с учетом наживки ---
    rarity_roll = random.random() * 100
    uncommon_chance = 60 + active_baits.get('bait_common', {}).get('bonus', 0)
    rare_chance = 85 + active_baits.get('bait_rare', {}).get('bonus', 0)

    if rarity_roll <= uncommon_chance: rarity = 'common'
    elif rarity_roll <= rare_chance: rarity = 'uncommon'
    else: rarity = 'rare'
    # --- КОНЕЦ НОВОЙ ЛОГИКИ ---

    if rarity == 'rare':
        quest_manager.update_quest_progress(user_id, 'fish_rare')

    loot_pool = FISHING_LOOT_TABLE[chosen_tier_id][rarity]
    caught_item = copy.deepcopy(random.choice(loot_pool))

    # --- НОВАЯ ЛОГИКА: Расчет веса с учетом наживки ---
    min_weight = 1.0
    if 'bait_quality' in active_baits:
        min_weight = FISHING_BAITS['bait_quality']['effect']['bonus']
        
    weight_roll = random.random()
    if weight_roll < 0.7: weight = random.uniform(min_weight, 5.0)
    elif weight_roll < 0.95: weight = random.uniform(5.0, 10.0)
    else: weight = random.uniform(10.0, 15.0)
    
    weight_multiplier = 1.0 + (active_rod['stats']['big_catch_chance'] / 100.0)
    if 'bait_heavy' in active_baits:
        weight_multiplier += FISHING_BAITS['bait_heavy']['effect']['bonus']
        
    weight *= weight_multiplier
    weight = max(min_weight, round(weight, 2))
    # --- КОНЕЦ НОВОЙ ЛОГИКИ ---
    
    if weight > 7:
        quest_manager.update_quest_progress(user_id, 'fish_heavy')
    
    caught_item['weight'] = weight
    stats['inventory'].append(caught_item)

    # --- НОВАЯ ЛОГИКА: Расчет опыта с учетом наживки ---
    xp_gained = math.ceil(caught_item['base_xp'] * weight)
    if 'bait_xp' in active_baits:
        xp_gained = math.ceil(xp_gained * (1 + FISHING_BAITS['bait_xp']['effect']['bonus']))
    # --- КОНЕЦ НОВОЙ ЛОГИКИ ---

    quest_manager.update_quest_progress(user_id, 'fish_any')
    stats['xp'] += xp_gained
    stats, leveled_up = _check_level_up(stats, user_id)
    
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Логика выпадения семян ---
    dropped_seed_name = None
    seed_chance_bonus = 0.0
    if 'bait_seed' in active_baits:
        seed_chance_bonus = FISHING_BAITS['bait_seed']['effect']['bonus']

    # Теперь семена могут выпасть с любой успешной рыбалки
    harvest_stats = db.get_harvest_stats(user_id)
    harvest_level = harvest_stats.get('level', 1)

    seed_drop_chances = {
        'seed_t1': 0.05,
        'seed_t2': 0.04 if harvest_level >= 5 else 0,
        'seed_t3': 0.03 if harvest_level >= 10 else 0,
        'seed_t4': 0.02 if harvest_level >= 20 else 0,
        'seed_t5': 0.01 if harvest_level >= 25 else 0,
    }

    for seed_id, chance in seed_drop_chances.items():
        # Добавляем бонус от наживки к базовому шансу
        if random.random() < (chance + seed_chance_bonus):
            harvest_manager.add_seed(user_id, seed_id)
            dropped_seed_name = HARVEST_SEEDS[seed_id]['name']
            break # Гарантируем, что выпадет только одно семя за раз
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    db.update_fishing_stats(user_id, stats)

    return {
        'status': 'success',
        'item_name': caught_item['name'],
        'item_weight': weight,
        'xp_gained': xp_gained,
        'leveled_up': leveled_up,
        'new_level': stats['level'],
        'dropped_seed_name': dropped_seed_name
    }



def buy_rod(user_id, rod_id):
    """Покупка удочки."""
    stats = db.get_fishing_stats(user_id)
    rod_data = FISHING_RODS[rod_id]

    if rod_id in stats['unlocked_rods']:
        return False, "У вас уже есть эта удочка\\."
    if stats['level'] < rod_data['level_req']:
        return False, "Недостаточный уровень рыбалки\\."
    if stats['chaos_orbs'] < rod_data['cost']:
        return False, "Недостаточно хаос орбов\\."
    
    stats['chaos_orbs'] -= rod_data['cost']
    stats['unlocked_rods'].append(rod_id)
    db.update_fishing_stats(user_id, stats)
    return True, f"Вы приобрели: *{escape_markdown(rod_data['name'])}*\\!"

def sell_all_catch(user_id):
    """Продажа всего улова."""
    stats = db.get_fishing_stats(user_id)
    if not stats['inventory']:
        return 0, 0

    total_chaos = 0
    total_items = len(stats['inventory'])

    for item in stats['inventory']:
        # Умножаем базовую цену на вес, чтобы получить итоговую стоимость
        price = math.ceil(item['base_price'] * item['weight'])
        total_chaos += price
    
    stats['chaos_orbs'] += total_chaos
    quest_manager.update_quest_progress(user_id, 'fish_sell_chaos', value=total_chaos)
    stats['inventory'] = [] # Очищаем инвентарь
    db.update_fishing_stats(user_id, stats)
    
    return total_items, total_chaos

def spend_perk_point(user_id, perk_id):
    """(ИСПРАВЛЕНО) Тратит очки перков и отслеживает покупку."""
    if perk_id not in FISHING_STAT_PERKS:
        return False, "Улучшение не найдено\\."

    perk = FISHING_STAT_PERKS[perk_id]
    cost = perk['cost']
    stat_column = perk['stat']
    value_to_add = perk['value']

    fishing_stats = db.get_fishing_stats(user_id)
    
    if fishing_stats.get('unspent_perk_points', 0) < cost:
        return False, f"Недостаточно очков улучшений\\! Нужно {cost}."

    # --- НАЧАЛО ИЗМЕНЕНИЙ: Атомарная операция в БД ---
    success, message = db.purchase_fishing_perk(user_id, perk_id, cost, stat_column, value_to_add)
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    
    return success, message

def buy_bait(user_id, bait_id):
    """Покупка наживки."""
    if bait_id not in FISHING_BAITS:
        return False, "Наживка не найдена\\."
        
    bait = FISHING_BAITS[bait_id]
    stats = db.get_fishing_stats(user_id)
    
    if stats['chaos_orbs'] < bait['cost']:
        return False, f"Недостаточно хаос орбов\\! Нужно {bait['cost']}."
        
    stats['chaos_orbs'] -= bait['cost']
    
    # Стакаем количество забросов, если такая наживка уже есть
    active_baits = stats.get('active_baits', {})
    if bait_id in active_baits:
        active_baits[bait_id]['casts'] += bait['casts']
    else:
        active_baits[bait_id] = {'casts': bait['casts']}
        
    stats['active_baits'] = active_baits
    db.update_fishing_stats(user_id, stats)
    return True, f"Вы купили *{escape_markdown(bait['name'])}*\\! Эффект продлится *{bait['casts']}* забросов\\."


def start_expedition(user_id):
    """Отправляет игрока в экспедицию."""
    from game_content import EXPEDITION_CONFIG
    
    stats = db.get_fishing_stats(user_id)
    cost = EXPEDITION_CONFIG['cost']
    duration = EXPEDITION_CONFIG['duration_hours'] * 3600
    
    if stats.get('expedition_end_time', 0) > time.time():
        return False, "Вы уже в экспедиции\\."
    if stats.get('chaos_orbs', 0) < cost:
        return False, f"Недостаточно хаосов\\! Нужно {cost}."

    stats['chaos_orbs'] -= cost
    stats['expedition_end_time'] = int(time.time()) + duration
    db.update_fishing_stats(user_id, stats)
    return True, f"Вы отправились в долгую рыболовную экспедицию\\! Возвращайтесь через {EXPEDITION_CONFIG['duration_hours']} часа за уловом\\."

def claim_expedition_reward(user_id):
    """Забирает награду за экспедицию."""
    stats = db.get_fishing_stats(user_id)
    if stats.get('expedition_end_time', 0) == 0:
        return None, "Вы не были в экспедиции\\."
    if stats.get('expedition_end_time', 0) > time.time():
        return None, "Экспедиция еще не завершена\\."
        
    # Сбрасываем таймер
    stats['expedition_end_time'] = 0
    
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Новая логика генерации наград ---
    
    # 1. Увеличиваем количество предметов
    num_items = random.randint(40, 120)
    total_chaos_value = 0
    reward_text = f"Ваш улов из экспедиции \\({num_items} шт\\.\\):\n"
    
    for _ in range(num_items):
        # 2. Улов теперь только из высокоуровневых тиров с весами
        # Шансы: 20% на T3, 60% на T4, 20% на T5
        tier = random.choices(['tier3', 'tier4', 'tier5'], weights=[0.2, 0.6, 0.2], k=1)[0]
        
        # 3. Повышаем шанс на более редкую рыбу
        # Шансы: 20% на common, 50% на uncommon, 30% на rare
        rarity = random.choices(['common', 'uncommon', 'rare'], weights=[0.2, 0.5, 0.3], k=1)[0]
        
        item = random.choice(FISHING_LOOT_TABLE[tier][rarity])
        
        # 4. Вес остается в прежнем диапазоне, но ценность рыбы теперь намного выше
        weight = random.uniform(2.0, 8.0)
        price = math.ceil(item['base_price'] * weight)
        total_chaos_value += price
        # Убираем отображение индивидуальной цены, чтобы не было путаницы
        reward_text += f"• *{escape_markdown(item['name'])}*\n"
    
    # Гарантируем минимальную награду в 20,000
    total_chaos_value = max(total_chaos_value, 20000)
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
        
    stats['chaos_orbs'] += total_chaos_value
    db.update_fishing_stats(user_id, stats)
    
    reward_text += f"\nИтоговая выручка: *{total_chaos_value}* 🟢"
    return "Экспедиция завершена", reward_text


FISHING_PERK_RESET_COST = 100000 # Стоимость сброса

def reset_perk_points(user_id):
    """
    (ИСПРАВЛЕНО) Вызывает единую атомарную функцию в БД для сброса перков.
    """
    # Вся логика (проверка баланса, списание, возврат) теперь происходит внутри одной функции БД
    success, message = db.reset_and_refund_fishing_perks(user_id)
    return success, message
