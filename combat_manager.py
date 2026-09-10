# combat_manager.py
import random
import copy
import database as db
import ui_components as ui
import game_manager as gm
from telegram import Update
from game_content import CONTENT, BASE_STATS, HARVEST_SEEDS
import item_manager as im
from ui_components import get_effective_stats
import pvp_manager as pvp_m
import quest_manager
import harvest_manager
from utils import escape_markdown
import divination_card_manager as dcm

def _get_monster_item_count(player_level, monster_type):
    """Определяет, сколько предметов должен надеть монстр в зависимости от уровня игрока."""
    # Базовое количество предметов для монстров, если уровень игрока 5+
    base_counts = {
        'бой_обычный': 1, 
        'бой_редкий': 3, 
        'лутгоблин': 4, 
        'изгнанник': 5, 
        'сундук': 6  # Специальный тип для монстра из сундука
    }
    # Уровни, на которых количество предметов увеличивается на 1
    tiers = [10, 15, 25, 35, 45, 55, 65, 75, 85, 95]

    if player_level < 5:
        return 0
    
    item_count = base_counts.get(monster_type, 0)
    
    # Добавляем +1 предмет за каждый достигнутый порог уровня
    for tier in tiers:
        if player_level >= tier:
            item_count += 1
    
    return item_count

def _equip_monster_with_random_items(monster_data, num_items, floor_content):
    """Надевает на монстра случайные предметы и обновляет его статы."""
    if num_items <= 0:
        return monster_data

    monster_stats = monster_data['stats']
    
    # --- НАЧАЛО ИЗМЕНЕНИЯ: Фильтруем пул предметов ---
    # Собираем пул всех доступных предметов, ИСКЛЮЧАЯ предметы с механикой зарядов или срока службы.
    item_pool = [
        item for rarity in ['magic', 'rare', 'unique', 'legendary']
        for item in floor_content['items'].get(rarity, [])
        # Вот сам фильтр:
        if 'lifespan' not in item and 'charges' not in item
    ]
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---
    
    if not item_pool:
        return monster_data

    # Определяем доступные слоты
    available_slots = ['weapon1', 'weapon2', 'helmet', 'body_armour', 'gloves', 'boots', 'ring1', 'amulet', 'belt']
    random.shuffle(available_slots)

    equipped_count = 0
    while equipped_count < num_items and available_slots and item_pool:
        chosen_item = copy.deepcopy(random.choice(item_pool))
        slot = chosen_item['slot']

        # Обрабатываем слоты (кольца, двуручное оружие)
        slot_to_equip = None
        if slot == 'ring' and 'ring1' in available_slots:
            slot_to_equip = 'ring1'
        elif slot in available_slots:
            slot_to_equip = slot
        else:
            continue # Не можем надеть этот предмет, ищем другой

        # Применяем статы предмета к монстру
        for stat, value in chosen_item.get('stats', {}).items():
            if stat in ['health', 'max_health']:
                monster_stats['max_health'] = monster_stats.get('max_health', monster_stats.get('health', 0)) + value
                monster_stats['health'] = monster_stats.get('health', 0) + value
            elif stat in ['energy_shield', 'max_energy_shield']:
                monster_stats.setdefault('max_energy_shield', 0)
                monster_stats.setdefault('energy_shield', 0)
                monster_stats['max_energy_shield'] += value
                monster_stats['energy_shield'] += value
            else:
                monster_stats[stat] = monster_stats.get(stat, 0) + value
        
        # Убираем использованные слоты
        available_slots.remove(slot_to_equip)
        if chosen_item.get('type') in ['Лук', 'Двуручный меч', 'Двуручный топор', 'Посох'] and 'weapon2' in available_slots:
            available_slots.remove('weapon2')
        
        equipped_count += 1
        
    # После надевания всех предметов, синхронизируем текущие значения с максимальными
    if 'max_health' in monster_stats:
        monster_stats['health'] = monster_stats['max_health']
    if 'max_energy_shield' in monster_stats:
        monster_stats['energy_shield'] = monster_stats['max_energy_shield']
        
    monster_data['stats'] = monster_stats
    return monster_data

def _process_post_combat_item_effects(character):
    """
    Обрабатывает эффекты предметов, срабатывающие после боя (победа или поражение).
    Уменьшает срок службы и заряды, уничтожает предметы при их окончании.
    Возвращает обновленный объект персонажа и список сообщений для лога.
    """
    log_messages = []
    # Создаем копию, чтобы безопасно удалять предметы во время итерации
    equipment = character.get('equipment', {}).copy()
    
    for slot, item in equipment.items():
        if not item:
            continue
            
        item_destroyed = False
        
        # Уменьшаем срок службы (Нейтронная Звезда)
        if 'lifespan' in item and isinstance(item['lifespan'], list):
            item['lifespan'][0] -= 1
            if item['lifespan'][0] <= 0:
                log_messages.append(f"💥 Предмет *{escape_markdown(item['name'])}* исчерпал свой срок службы и рассыпался в прах\\!")
                character['equipment'][slot] = None
                item_destroyed = True

        # Уменьшаем заряды (Мечта Фликера)
        if not item_destroyed and 'charges' in item and isinstance(item['charges'], list):
            item['charges'][0] -= 1
            if item['charges'][0] <= 0:
                log_messages.append(f"💨 Предмет *{escape_markdown(item['name'])}* исчерпал все заряды и исчез\\!")
                character['equipment'][slot] = None
                
    return character, log_messages

def _apply_on_hit_taken_effects(victim, attacker, damage, turn_log, original_damage_log):
    """
    УНИВЕРСАЛЬНАЯ ФУНКЦИЯ
    Применяет все эффекты, которые срабатывают при получении урона, к цели (victim).
    Это может быть как игрок, так и монстр.
    """
    if 'equipment' in victim:
        for item in victim['equipment'].values():
            if not item: continue

            # 1. Отражение урона (например, Доспех из шипов)
            if item.get('special_mechanic') == 'reflect_damage_25':
                reflected_damage = int(damage * 0.25)
                if reflected_damage > 0:
                    attacker['stats'] = _apply_damage(attacker, reflected_damage)['stats']
                    turn_log.append(f"🛡️ {escape_markdown(item['name'])} отражает {reflected_damage} урона обратно в {escape_markdown(attacker['name'])}\\!")

            # 2. Бонусы при получении удара (например, Оплот горы)
            if item.get('on_hit_taken_effect', {}).get('add_defense_temp'):
                buff_name = 'Оплот горы'
                if not any(b['name'] == buff_name for b in victim.get('buffs', [])):
                    buff = {'name': buff_name, 'effect': {'defense': item['on_hit_taken_effect']['add_defense_temp']}, 'duration': 2, 'desc': "+25% к защите на 1 ход"}
                    victim.setdefault('buffs', []).append(buff)

            # 3. Бонусы при получении критического удара (например, Корона мщения)
            if "\\(КРИТ\\!" in original_damage_log:
                if item.get('on_crit_taken_effect', {}).get('add_attack_next_hit'):
                    buff_name = 'Корона мщения'
                    
                    # ИСПРАВЛЕНИЕ: Мы удаляем старый бафф, если он есть, чтобы избежать стака значений.
                    victim['buffs'] = [b for b in victim.get('buffs', []) if b.get('name') != buff_name]
                    
                    # А затем добавляем новый, "чистый" бафф с правильным значением.
                    buff = {
                        'name': buff_name, 
                        'effect': {'attack': item['on_crit_taken_effect']['add_attack_next_hit']}, 
                        'duration': 2, 
                        'desc': "Следующая атака усилена"
                    }
                    victim.setdefault('buffs', []).append(buff)
    
    return victim, attacker


def _calculate_damage(attacker, defender):
    attacker_stats = get_effective_stats(attacker)
    defender_stats = get_effective_stats(defender)
    
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Улучшенная проверка флагов ---
    cannot_be_dodged = attacker_stats.get('cannot_be_dodged', False)
    cannot_be_blocked = attacker_stats.get('cannot_be_blocked', False)
    
    # Проверяем новый флаг от "Приговора Грешника"
    if attacker.get('special_flags', {}).get('cannot_be_dodged_and_blocked'):
        cannot_be_dodged = True
        cannot_be_blocked = True
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    # Этот блок все еще нужен для старых предметов с таким свойством, но основная проверка уже выше
    if 'equipment' in attacker:
        for item in attacker['equipment'].values():
            if item:
                if item.get('stats', {}).get('cannot_be_dodged'): cannot_be_dodged = True
                if item.get('stats', {}).get('cannot_be_blocked'): cannot_be_blocked = True
                if item.get('implicit', {}).get('effect', {}).get('cannot_be_dodged'): cannot_be_dodged = True
                if item.get('implicit', {}).get('effect', {}).get('cannot_be_blocked'): cannot_be_blocked = True

    # --- НАЧАЛО ИЗМЕНЕНИЯ: Новая логика уворота и точности ---
    
    # 1. Рассчитываем пробитие уворота из точности. Формула: Точность / 500 (или Точность * 0.002)
    dodge_penetration_from_accuracy = attacker_stats.get('accuracy', 0) / 500.0
    
    # 2. Уменьшаем шанс уворота защитника на процент пробития
    effective_dodge_chance = defender_stats.get('dodge_chance', 0) * (1 - dodge_penetration_from_accuracy)
    
    # 3. Применяем жесткий предел (кап) в 75%
    capped_dodge_chance = min(effective_dodge_chance, 75)

    if not cannot_be_dodged and random.random() < (capped_dodge_chance / 100.0):
        return 0, f"💨 {escape_markdown(defender['name'])} увернулся от атаки\\!", False, 0, 0

    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

     # --- НАЧАЛО ИЗМЕНЕНИЯ: Новая логика пробития блока ---

    # 1. Берем пробитие блока атакующего как процент
    block_penetration_percent = attacker_stats.get('block_penetration', 0)
    
    # 2. Уменьшаем шанс блока защитника на процент пробития
    effective_block_chance = defender_stats.get('block_chance', 0) * (1 - block_penetration_percent / 100.0)

    # 3. Применяем жесткий предел (кап) в 75%
    capped_block_chance = min(effective_block_chance, 75)

    if not cannot_be_blocked and random.random() < (capped_block_chance / 100.0):
        heal_amount = 0
        es_heal_amount = 0
        
        if defender_stats.get('heal_on_block_percent'):
            heal_amount += int(defender_stats['max_health'] * (defender_stats['heal_on_block_percent'] / 100.0))

        if 'equipment' in defender:
            for item in defender['equipment'].values():
                if item:
                    if item.get('on_block_effect', {}).get('heal_percent'):
                        heal_amount += int(defender_stats['max_health'] * (item['on_block_effect']['heal_percent'] / 100.0))
                    if item.get('on_block_effect', {}).get('es_heal_percent'):
                        es_heal_amount += int(defender_stats['max_energy_shield'] * (item['on_block_effect']['es_heal_percent'] / 100.0))
                        
        return 0, f"🛡️ {escape_markdown(defender['name'])} заблокировал атаку\\!", False, heal_amount, es_heal_amount

    # --- КОНЕЦ ИЗМЕНЕНИЯ ---
    
    base_damage = attacker_stats.get('attack', 5)
    is_crit = False
    
    can_be_crit = not defender_stats.get('cannot_be_crit', False)

     # --- НАЧАЛО ИЗМЕНЕНИЙ: Исправление логики крита ---
    can_be_crit = not defender_stats.get('cannot_be_crit', False)
    
    # Проверяем, может ли цель вообще получать криты
    if can_be_crit:
        # Если да, то проверяем остальные условия
        if defender_stats.get('always_be_critted'):
            is_crit = True
        elif attacker.get('guaranteed_crit_next_hit'):
            is_crit = True
            attacker['guaranteed_crit_next_hit'] = False
        elif random.random() < (attacker_stats.get('crit_chance', 0) / 100.0):
            is_crit = True
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    
    if is_crit:
        crit_multiplier = 2.0 + (attacker_stats.get('crit_multiplier', 0) / 100.0)
        
        if attacker_stats.get('crit_mult_override'):
            crit_multiplier = attacker_stats.get('crit_mult_override')

        if 'equipment' in attacker:
            for item in attacker['equipment'].values():
                if item and 'conditional_stats' in item:
                    cond_stats = item['conditional_stats']
                    if 'crit_multiplier' in cond_stats and cond_stats['crit_multiplier']['condition'] == 'enemy_full_health':
                        if defender['stats']['health'] >= defender['stats']['max_health']:
                            crit_multiplier += cond_stats['crit_multiplier']['value'] / 100.0
        
        crit_reduction_percent = defender_stats.get('crit_damage_reduction', 0)
        if crit_reduction_percent > 0:
            extra_damage_multiplier = crit_multiplier - 1.0
            reduction_factor = 1.0 - (crit_reduction_percent / 100.0)
            reduced_extra_damage = extra_damage_multiplier * reduction_factor
            crit_multiplier = 1.0 + reduced_extra_damage
        
        crit_multiplier = max(1.0, crit_multiplier)
        base_damage = int(base_damage * crit_multiplier)

    defense_perc = min(defender_stats.get('defense', 0), 75)
    penetration_perc = attacker_stats.get('defense_penetration', 0)
    
    if is_crit:
        penetration_perc += attacker_stats.get('crit_pen', 0)
        if 'equipment' in attacker:
            for item in attacker['equipment'].values():
                if item and item.get('on_crit_effect', {}).get('defense_penetration'):
                    penetration_perc += item['on_crit_effect']['defense_penetration']

    # --- НАЧАЛО ИЗМЕНЕНИЙ: Исправление для "Предвестника Заката" ---
    # Получаем предел из итоговых статов, а не ищем ключ с _override
    penetration_cap = attacker_stats.get('penetration_cap', 75)
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    penetration_perc = min(penetration_perc, penetration_cap)

    effective_defense_perc = defense_perc * (1 - penetration_perc / 100.0)
    final_damage = max(1, int(base_damage * (1 - effective_defense_perc / 100.0)))

    attack_multiplier = 1.0 + attacker_stats.get('attack_mult', 0)
    final_damage = int(final_damage * attack_multiplier)

    is_double_damage = False
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Исправление для "Предвестника Заката" ---
    # Проверяем и иммунитет защитника, и запрет у атакующего
    if not defender_stats.get('immune_to_double_damage', False) and attacker_stats.get('double_damage_chance_override', 100) != 0:
        double_damage_chance = attacker_stats.get('double_damage_chance', 0)
        
        if is_crit and attacker_stats.get('temp_dd_on_crit'):
            double_damage_chance += attacker_stats.get('temp_dd_on_crit')

        if attacker.get('guaranteed_dd_next_hit'):
            is_double_damage = True
            attacker['guaranteed_dd_next_hit'] = False 
        elif random.random() < (double_damage_chance / 100.0):
            is_double_damage = True

        if is_double_damage:
            final_damage *= 2
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    log_message = f"💥 {escape_markdown(attacker['name'])} наносит {final_damage} урона"

    if is_crit: log_message += " \\(КРИТ\\! 💫\\)"
    if is_double_damage: log_message += " \\(ДВОЙНОЙ УРОН\\! 🔥\\)"
    return final_damage, log_message, True, 0, 0




def _apply_damage(character, damage, attacker_flags=None):
    from ui_components import get_effective_stats # Локальный импорт
    
    if attacker_flags is None:
        attacker_flags = {}
        
    char_stats = character.get('stats', {})
    char_stats.setdefault('energy_shield', 0)
    char_stats.setdefault('health', 0)
    
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Новая логика для "Разум превыше Материи" и "Разрыва Завесы" ---
    effective_stats = get_effective_stats(character)
    mom_ratio = effective_stats.get('damage_split_mom', 0)
    
    # Проверяем, есть ли эффект обхода энергощита у атакующего и нет ли иммунитета у защищающегося
    has_bypass = attacker_flags.get('bypass_es_50_percent', False)
    has_immunity = character.get('special_flags', {}).get('es_bypass_immunity', False)

    if has_bypass and not has_immunity:
        damage_to_es = int(damage * 0.5)
        damage_to_health_direct = damage - damage_to_es
        
        # 50% урона идет в энергощит как обычно
        es_damage = min(char_stats.get('energy_shield', 0), damage_to_es)
        char_stats['energy_shield'] -= es_damage
        
        # Оставшиеся 50% идут напрямую в здоровье, игнорируя все
        char_stats['health'] -= damage_to_health_direct
        
    else: # Стандартная логика, если нет обхода или есть иммунитет
        # Сначала урон проходит через обычный энергощит
        es_damage = min(char_stats.get('energy_shield', 0), damage)
        char_stats['energy_shield'] -= es_damage
        damage_to_health = damage - es_damage

        # Если остался урон, который должен пойти в здоровье, и есть эффект МоМ
        if damage_to_health > 0 and mom_ratio > 0:
            # Часть этого урона снова пытается отняться от энергощита
            damage_redirected_to_es = int(damage_to_health * mom_ratio)
            final_es_damage = min(char_stats.get('energy_shield', 0), damage_redirected_to_es)
            
            char_stats['energy_shield'] -= final_es_damage
            # Оставшийся урон идет в здоровье
            char_stats['health'] -= (damage_to_health - final_es_damage)
        else:
            # Если МоМ нет, весь оставшийся урон идет в здоровье
            char_stats['health'] -= damage_to_health
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    
    character['stats'] = char_stats
    return character



def _apply_healing(character, heal_amount):
    """
    УНИВЕРСАЛЬНАЯ ФУНКЦИЯ
    Применяет лечение, учитывая 'healing_damages_you' и 'healing_overflow_to_es'.
    """
    from ui_components import get_effective_stats
    effective_stats = get_effective_stats(character)
    char_stats = character.get('stats', {})
    
    if effective_stats.get('special_flags', {}).get('healing_damages_you'):
        character = _apply_damage(character, heal_amount)
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Логика "Эгиды Святого" ---
    elif effective_stats.get('special_flags', {}).get('healing_overflow_to_es'):
        max_health = effective_stats.get('max_health', 1)
        current_health = char_stats.get('health', 0)
        
        if current_health >= max_health:
            # Если здоровье полное, лечим энергощит
            max_es = effective_stats.get('max_energy_shield', 0)
            char_stats['energy_shield'] = min(max_es, char_stats.get('energy_shield', 0) + heal_amount)
        else:
            # Иначе, лечим здоровье как обычно
            char_stats['health'] = min(max_health, current_health + heal_amount)
        character['stats'] = char_stats
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    else:
        max_health = effective_stats.get('max_health', 1)
        char_stats['health'] = min(max_health, char_stats.get('health', 0) + heal_amount)
        character['stats'] = char_stats
        
    return character

def create_fight_event(user_id, run_state, fight_type, custom_monster_data=None):
    char = run_state['character']
    floor = run_state['floor']
    
    # --- ИЗМЕНЕНИЕ: Временный фикс удален. Вместо него просто вызываем правильный recalculate_stats. ---
    # Это гарантирует, что все динамические эффекты (например, бонусы за низкое ХП)
    # будут актуальны на момент начала боя.
    im.recalculate_stats(user_id, char)
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Логика для "Сосуда Нестабильности" ---
    effective_char_stats = get_effective_stats(char)
    if any(item.get('special_mechanic') == 'random_base_attack_per_fight' for item in char.get('equipment', {}).values() if item):
        random_attack = random.randint(1, 100)
        buff_name = 'Хаотичная Энергия'
        # Удаляем старый бафф, если он есть
        char['buffs'] = [b for b in char.get('buffs', []) if b.get('name') != buff_name]
        # Добавляем новый
        buff = {'name': buff_name, 'effect': {'attack': random_attack - effective_char_stats.get('attack', 0)}, 'duration': 2, 'desc': f"Ваша атака в этом бою: {random_attack}"}
        char.setdefault('buffs', []).append(buff)
    content_floor_number = floor
    if char.get('run_type') == 'endless' and floor > 4:
        content_floor_number = 4
    
    floor_key = f"floor_{content_floor_number}"
    floor_content = CONTENT[floor_key]
    
    monster_data = None
    if custom_monster_data:
        monster_data = custom_monster_data
    # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
    elif fight_type == 'босс' and char.get('run_type') in ['pvp', 'hc_pvp']:
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---
        boss_player_data = run_state['floor_bosses'][str(floor)]
        prefix = "ХК Призрак" if char.get('run_type') == 'hc_pvp' else "Призрак игрока"
        monster_data = {'name': f"{prefix} {boss_player_data['name']}", 'type': 'босс', 'stats': boss_player_data['stats'], 'equipment': boss_player_data.get('equipment', {})}
    else:
        monster_type_map = {'бой_обычный': 'common', 'бой_редкий': 'rare', 'лутгоблин': 'lootgoblins'}
        if fight_type in monster_type_map:
            monster_data = copy.deepcopy(random.choice(floor_content['monsters'][monster_type_map[fight_type]]))
        elif fight_type == 'босс':
            boss_name_or_data = run_state['floor_bosses'][str(floor)]
            boss_pool = floor_content['monsters']['bosses']
            if isinstance(boss_name_or_data, str):
                monster_data = copy.deepcopy(next((b for b in boss_pool if b['name'] == boss_name_or_data), random.choice(boss_pool)))
            else:
                monster_data = copy.deepcopy(random.choice(boss_pool))

    # --- НАЧАЛО НОВЫХ ИЗМЕНЕНИЙ: Система экипировки монстров ---
    run_type = char.get('run_type')

    # Отключаем скейлинг монстров для Хардкорного режима
    if run_type != 'hc_pvp':
        player_info = db.get_player_info(user_id)
        player_level = player_info.get('level', 1) if player_info else 1
        
        # Определяем тип монстра для системы экипировки
        monster_type_for_equip = custom_monster_data.get('type') if custom_monster_data else fight_type
        
        num_items_to_equip = _get_monster_item_count(player_level, monster_type_for_equip)
        
        if num_items_to_equip > 0 and monster_data:
            monster_data = _equip_monster_with_random_items(monster_data, num_items_to_equip, floor_content)
    # --- КОНЕЦ НОВЫХ ИЗМЕНЕНИЙ ---

    if char.get('run_type') == 'endless' and floor > 4:
        # --- НАЧАЛО ИЗМЕНЕНИЯ: Экипировка боссов на высоких этажах ---
        if fight_type == 'босс':
            # Рассчитываем, сколько предметов должен надеть босс. 1 предмет каждые 30 этажей.
            num_items_to_equip = floor // 30
            
            if num_items_to_equip > 0:
                # Используем существующую функцию для надевания предметов
                monster_data = _equip_monster_with_random_items(monster_data, num_items_to_equip, floor_content)
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---
        scaling_levels = floor - 4
        health_multiplier = 1.0 + (0.20 * scaling_levels)
        attack_multiplier = 1.0 + (0.20 * scaling_levels)
        
        stats = monster_data['stats']
        stats['health'] = int(stats['health'] * health_multiplier)
        if 'max_health' in stats:
            stats['max_health'] = int(stats['max_health'] * health_multiplier)
        else:
            stats['max_health'] = stats['health']

        if stats.get('energy_shield', 0) > 0:
            stats['energy_shield'] = int(stats['energy_shield'] * health_multiplier)
            if 'max_energy_shield' in stats:
                stats['max_energy_shield'] = int(stats['max_energy_shield'] * health_multiplier)
            else:
                stats['max_energy_shield'] = stats['energy_shield']

        stats['attack'] = int(stats['attack'] * attack_multiplier)

        flat_stat_bonus = 1 * scaling_levels
        stats['dodge_chance'] = stats.get('dodge_chance', 0) + flat_stat_bonus
        stats['block_chance'] = stats.get('block_chance', 0) + flat_stat_bonus
        stats['crit_chance'] = stats.get('crit_chance', 0) + flat_stat_bonus
        neww_flat_bonus = 4 * scaling_levels
        stats['defense'] = stats.get('defense', 0) + neww_flat_bonus
        new_flat_bonus = 8 * scaling_levels
        stats['accuracy'] = stats.get('accuracy', 0) + new_flat_bonus
        stats['defense_penetration'] = stats.get('defense_penetration', 0) + new_flat_bonus
        stats['block_penetration'] = stats.get('block_penetration', 0) + (3 * scaling_levels)

    monster_data['stats'].setdefault('max_health', monster_data['stats']['health'])
    monster_data['stats'].setdefault('max_energy_shield', monster_data['stats'].get('energy_shield', 0))

    char['combat'] = {
        'monster': {'name': monster_data['name'], 'type': fight_type, 'stats': monster_data['stats'], 'equipment': monster_data.get('equipment', {})},
        'log': ['Бой начинается\\!'],
        'last_turn_log': {},
        'is_world_boss': False
    }
    if monster_data.get('log_message'):
         char['combat']['log'] = [monster_data['log_message']]

    char['combat']['player_damaged_last_turn'] = True
    db.update_pve_run_state(user_id, floor, run_state['event_num'], char, run_state['floor_bosses'])
    return ui.create_fight_ui(char)

def process_combat_turn(user_id, action, run_state, context=None, telegram_user=None):
    char = run_state['character']
    if not char.get('combat'): return gm.continue_run(user_id)
    
    # --- ИЗМЕНЕНИЕ: Сбрасываем флаг урона в начале хода игрока ---
    char['combat']['player_damaged_last_turn'] = False
    
    monster_obj = char['combat']['monster']
    monster_obj['name'] = char['combat']['monster']['name'] 
    
    player_obj = copy.deepcopy(char)
    player_obj['name'] = 'Игрок'

    last_turn_log = {'player': [], 'monster': []}

    # --- ИЗМЕНЕНИЕ: Механика "Клятва Азири" (дегенерация в начале хода) ---
    if 'special_flags' in player_obj and player_obj['special_flags'].get('health_degen_on_turn_start'):
        degen_damage = int(player_obj['stats']['max_health'] * 0.10)
        if degen_damage > 0:
            player_obj = _apply_damage(player_obj, degen_damage)
            last_turn_log['player'].append(f"🩸 Клятва Азири отнимает у вас {degen_damage} здоровья\\.")

    if action == 'attack':
        damage, log, hit_landed, heal_on_block, es_heal_on_block = _calculate_damage(player_obj, monster_obj)
        last_turn_log['player'].append(log)
        
        if hit_landed:
            if damage > 0:
                player_effective_stats = get_effective_stats(player_obj)
                
                # --- НАЧАЛО ИЗМЕНЕНИЙ: Логика для "Наряда Тайного Ткача" ---
                if "\\(КРИТ\\!" in log and player_effective_stats.get('crit_consumes_es_for_mult'):
                    es_cost = int(player_obj['stats'].get('max_energy_shield', 0) * 0.05)
                    if player_obj['stats'].get('energy_shield', 0) >= es_cost:
                        player_obj['stats']['energy_shield'] -= es_cost
                        # Увеличиваем урон на 100% от базового урона этого крита
                        # (эквивалентно добавлению 100% к множителю)
                        damage *= 2 
                        last_turn_log['player'].append(f"🔮 Ткач поглощает {es_cost} энергощита, чтобы усилить крит\\!")
                # --- КОНЕЦ ИЗМЕНЕНИЙ ---

                if "\\(КРИТ\\!" in log and player_effective_stats.get('special_flags', {}).get('crit_costs_hp_for_damage'):
                    hp_cost = int(player_obj['stats']['health'] * 0.10)
                    if hp_cost > 0:
                        player_obj['stats']['health'] -= hp_cost
                        last_turn_log['player'].append(f"🩸 Клинок поглощает {hp_cost} здоровья, чтобы усилить удар")
                        damage = int(damage * 1.5)

                es_cost_damage = 0
                if 'equipment' in player_obj:
                    for item in player_obj['equipment'].values():
                        if item and item.get('on_attack_effect', {}).get('self_es_damage_percent'):
                            es_cost = int(player_obj['stats']['energy_shield'] * (item['on_attack_effect']['self_es_damage_percent'] / 100.0))
                            if es_cost > 0:
                                player_obj['stats']['energy_shield'] -= es_cost
                                es_cost_damage = int(es_cost * item['on_attack_effect']['add_damage_from_es_cost'])
                                last_turn_log['player'].append(f"🔮 Жертвенный Клинок поглощает {es_cost} энергощита, чтобы усилить удар\\!")
                
                final_damage = damage + es_cost_damage
                # --- ИЗМЕНЕНИЕ: Передаем флаги атакующего ---
                monster_obj = _apply_damage(monster_obj, final_damage, attacker_flags=player_obj.get('special_flags', {}))
                monster_obj, player_obj = _apply_on_hit_taken_effects(monster_obj, player_obj, final_damage, last_turn_log['player'], log)

                # --- НАЧАЛО ИЗМЕНЕНИЙ: Механика "Хватка Паучихи" ---
                if "\\(КРИТ\\!" in log and player_obj.get('special_flags', {}).get('anti_leech_on_crit'):
                    # Накладываем дебафф на монстра
                    debuff_name = 'Паучья Отрава'
                    if not any(b.get('name') == debuff_name for b in monster_obj.get('buffs', [])):
                        debuff = {'name': debuff_name, 'effect': {'lifesteal': -100, 'es_leech_rate': -100}, 'duration': 3, 'desc': "Вампиризм не работает"}
                        monster_obj.setdefault('buffs', []).append(debuff)
                        last_turn_log['player'].append(f"🕷️ Ваш критический удар отравляет {escape_markdown(monster_obj['name'])}, блокируя вампиризм\\!")
                # --- КОНЕЦ ИЗМЕНЕНИЙ ---

                # --- ИЗМЕНЕНИЕ: Механика "Грань Пустоты" и "Призрачный Жнец" ---
                effective_player_stats = get_effective_stats(player_obj)
                lifesteal_percent = effective_player_stats.get('lifesteal', 0)
                es_leech_percent = effective_player_stats.get('es_leech_rate', 0)

                if player_obj.get('special_flags', {}).get('lifesteal_leeches_es_instead'):
                    es_leech_percent += lifesteal_percent
                    lifesteal_percent = 0

                leech_messages = []
                if lifesteal_percent > 0:
                    healed_amount = int(final_damage * (lifesteal_percent / 100.0))
                    if healed_amount > 0:
                        player_obj['stats']['health'] = min(player_obj['stats']['max_health'], player_obj['stats']['health'] + healed_amount)
                        leech_messages.append(f"🩸 +{healed_amount} здоровья")
                if es_leech_percent > 0:
                    leeched_amount = int(final_damage * (es_leech_percent / 100.0))
                    if leeched_amount > 0:
                        player_obj['stats']['energy_shield'] = min(player_obj['stats']['max_energy_shield'], player_obj['stats']['energy_shield'] + leeched_amount)
                        leech_messages.append(f"🔮 +{leeched_amount} энергощита")
                if leech_messages:
                    last_turn_log['player'].append("✨ Вампиризм: " + ", ".join(leech_messages) + "\\.")
        
        else: # Уворот или блок
            if heal_on_block > 0:
                monster_obj['stats']['health'] = min(monster_obj['stats']['max_health'], monster_obj['stats']['health'] + heal_on_block)
                last_turn_log['player'].append(f"✨ {escape_markdown(monster_obj['name'])} восстанавливает {heal_on_block} здоровья от блока\\!")
            if es_heal_on_block > 0:
                monster_obj['stats']['energy_shield'] = min(monster_obj['stats']['max_energy_shield'], monster_obj['stats']['energy_shield'] + es_heal_on_block)
                last_turn_log['player'].append(f"✨ {escape_markdown(monster_obj['name'])} восстанавливает {es_heal_on_block} энергощита от блока\\!")

        if 'equipment' in player_obj:
            for item in player_obj['equipment'].values():
                if item and item.get('on_attack_effect', {}).get('self_damage_percent'):
                    self_dmg = int(player_obj['stats']['max_health'] * (item['on_attack_effect']['self_damage_percent'] / 100.0))
                    player_obj = _apply_damage(player_obj, self_dmg)
                    last_turn_log['player'].append(f"🔥 {escape_markdown(item['name'])} наносит вам {self_dmg} урона в ответ\\!")

        if monster_obj['stats']['health'] <= 0:
            char.update(player_obj)
            char['combat']['last_turn_log'] = last_turn_log
            return _handle_victory(user_id, run_state, telegram_user, context)
    
    damage, log, hit_landed, heal_on_block, es_heal_on_block = _calculate_damage(monster_obj, player_obj)
    last_turn_log['monster'].append(log)

    if hit_landed:
        char['combat']['player_damaged_last_turn'] = True # Устанавливаем флаг
        
        # --- ИЗМЕНЕНИЕ: Механика "Эгида Бессмертия" (Death Defiance) ---
        if 'equipment' in player_obj:
            has_death_defiance = any(item.get('special_mechanic') == 'death_defiance_once' for item in player_obj['equipment'].values() if item)
            if has_death_defiance and not player_obj['combat'].get('death_defiance_used'):
                if player_obj['stats']['health'] - damage <= 0:
                    damage = player_obj['stats']['health'] - 1 # Оставляем 1 ХП
                    player_obj['combat']['death_defiance_used'] = True
                    # Добавляем бафф неуязвимости
                    buff = {'name': "Бессмертие", 'effect': {'defense': 9999}, 'duration': 2, 'desc': "Вы неуязвимы"}
                    player_obj.setdefault('buffs', []).append(buff)
                    last_turn_log['monster'].append(f"🛡️ Эгида Бессмертия спасает вас от гибели\\!")
        player_effective_stats = get_effective_stats(player_obj)
        if player_effective_stats.get('increased_damage_taken'):
            damage = int(damage * (1 + player_effective_stats['increased_damage_taken']))
        
        # --- НАЧАЛО ИЗМЕНЕНИЙ: Новая логика для "Эгиды Бессмертия" ---
        # Сначала применяем урон
        monster_flags = get_effective_stats(monster_obj).get('special_flags', {})
        player_obj_after_damage = _apply_damage(player_obj, damage, attacker_flags=monster_flags)
        
        # Теперь проверяем, умер ли игрок
        if player_obj_after_damage['stats']['health'] <= 0:
            # Если игрок должен умереть, проверяем, есть ли у него "Эгида" и не была ли она использована
            has_death_defiance = any(item.get('special_mechanic') == 'death_defiance_once' for item in player_obj_after_damage.get('equipment', {}).values() if item)
            
            if has_death_defiance and not player_obj_after_damage['combat'].get('death_defiance_used'):
                # Спасаем игрока
                player_obj_after_damage['stats']['health'] = 1 # Оставляем 1 ХП
                player_obj_after_damage['combat']['death_defiance_used'] = True
                
                # Добавляем бафф неуязвимости
                buff = {'name': "Бессмертие", 'effect': {'defense': 9999}, 'duration': 2, 'desc': "Вы неуязвимы"}
                player_obj_after_damage.setdefault('buffs', []).append(buff)
                last_turn_log['monster'].append(f"🛡️ Эгида Бессмертия спасает вас от гибели\\!")
            
        # Обновляем объект игрока в любом случае
        player_obj = player_obj_after_damage
        # --- КОНЕЦ ИЗМЕНЕНИЙ ---
        player_obj, monster_obj = _apply_on_hit_taken_effects(player_obj, monster_obj, damage, last_turn_log['monster'], log)

        if damage > 0:
            monster_lifesteal = get_effective_stats(monster_obj).get('lifesteal', 0)
            if monster_lifesteal > 0:
                healed_amount = int(damage * (monster_lifesteal / 100.0))
                if healed_amount > 0:
                    monster_obj['stats']['health'] = min(monster_obj['stats']['max_health'], monster_obj['stats']['health'] + healed_amount)
                    last_turn_log['monster'].append(f"✨ Вампиризм: 🩸 +{healed_amount} здоровья\\.")

    else: # Игрок увернулся или заблокировал
        if heal_on_block > 0:
            player_obj = _apply_healing(player_obj, heal_on_block)
            last_turn_log['monster'].append(f"✨ Вы получили {heal_on_block} здоровья от блока\\!")
        if es_heal_on_block > 0:
            player_obj['stats']['energy_shield'] = min(player_obj['stats']['max_energy_shield'], player_obj['stats']['energy_shield'] + es_heal_on_block)
            last_turn_log['monster'].append(f"✨ Вы восстанавливаете {es_heal_on_block} энергощита от блока\\!")
        
        if "заблокировал" in log:
            player_effective_stats = get_effective_stats(player_obj)
            if any(item.get('special_mechanic') == 'debuff_attack_on_first_block' for item in player_obj.get('equipment', {}).values() if item) and not monster_obj.get('debuffs', {}).get('attack_reduced_by_hope'):
                monster_obj['stats']['attack'] = int(monster_obj['stats']['attack'] * 0.75)
                monster_obj.setdefault('debuffs', {})['attack_reduced_by_hope'] = True
                last_turn_log['monster'].append(f"✨ Ваш щит вспыхивает светом, ослабляя атаку {escape_markdown(monster_obj['name'])} на 25%\\!")
            if player_effective_stats.get('dd_on_block'):
                player_obj['guaranteed_dd_next_hit'] = True # Устанавливаем флаг
                last_turn_log['monster'].append("🛡️ Ваша следующая атака нанесет двойной урон благодаря блоку\\!")
        if "увернулся" in log:
            if 'equipment' in player_obj:
                for item in player_obj['equipment'].values():
                    if item:
                        if item.get('on_dodge_effect', {}).get('guaranteed_crit_next_hit'):
                            player_obj['guaranteed_crit_next_hit'] = True
                            last_turn_log['monster'].append("🎯 Поступь Фантома гарантирует критический удар для вашей следующей атаки\\!")
                        if item.get('on_dodge_effect', {}).get('heal_percent_on_dodge'):
                            heal_val = int(player_obj['stats']['max_health'] * (item['on_dodge_effect']['heal_percent_on_dodge'] / 100.0))
                            player_obj = _apply_healing(player_obj, heal_val)
                            last_turn_log['monster'].append(f"💃 Призрачные Танцоры дали вам {heal_val} здоровья за уворот\\!")
    
    char.update(player_obj)
    char['combat']['monster'].update(monster_obj)
    
    if char.get('buffs'):
        for buff in char.get('buffs', []):
            # --- ИЗМЕНЕНИЕ ЗДЕСЬ: Добавляем 'Источник Жизни' в исключения ---
            if 'duration' in buff and 'Святилище' not in buff.get('name', '') and 'Источник Жизни' not in buff.get('name', ''):
                buff['duration'] -= 1
        char['buffs'] = [b for b in char.get('buffs', []) if b.get('duration', 0) > 0]

    # --- НАЧАЛО ИЗМЕНЕНИЙ: Уменьшаем длительность дебаффов на монстре ---
    if char['combat']['monster'].get('buffs'):
        for buff in char['combat']['monster'].get('buffs', []):
            if 'duration' in buff:
                buff['duration'] -= 1
        char['combat']['monster']['buffs'] = [b for b in char['combat']['monster'].get('buffs', []) if b.get('duration', 0) > 0]
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    char['combat']['last_turn_log'] = last_turn_log
    full_turn_log = last_turn_log['player'] + last_turn_log['monster']
    char['combat']['log'].extend(full_turn_log)

    if char['stats']['health'] <= 0:
        if char['combat']['monster'].get('type') == 'чемпион':
            return pvp_m.process_champion_fight_result(
                challenger_id=user_id, challenger_char_state=char, 
                champion_owner_id=char['combat']['monster']['owner_id'], 
                champion_id_in_fight=char['combat']['monster']['champion_id'],
                is_challenger_win=False, context=context
            )
        # --- ДОБАВИТЬ ЭТОТ БЛОК ---
        elif char['combat']['monster'].get('type') == 'hc_champion':
             return pvp_m.process_champion_fight_result(
                challenger_id=user_id, challenger_char_state=char, 
                champion_owner_id=char['combat']['monster']['owner_id'], 
                champion_id_in_fight=char['combat']['monster']['champion_id'],
                is_challenger_win=False, context=context
            )
        # --- КОНЕЦ БЛОКА ---
        db.end_pve_run(user_id, is_win=False)
        return {'text': f"💀 *Вы были повержены\\!* 💀\n\n_{escape_markdown(char['combat']['monster']['name'])} оказался сильнее\\._", 'buttons': [[{'text': 'В главное меню', 'callback_data': 'back_to_main_menu'}]]}

    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    return ui.create_fight_ui(char)



def _handle_victory(user_id, run_state, telegram_user: Update.effective_user, context=None):
    char = run_state['character']
    char, post_combat_logs = _process_post_combat_item_effects(char)
    im.recalculate_stats(user_id, char)
    
    monster = char['combat']['monster']
    monster_type = monster['type']
    
    if monster_type == 'чемпион':
        return pvp_m.process_champion_fight_result(
            challenger_id=user_id, challenger_char_state=char,
            champion_owner_id=monster['owner_id'], 
            champion_id_in_fight=monster['champion_id'],
            is_challenger_win=True, context=context
        )
    # --- ДОБАВИТЬ ЭТОТ БЛОК ---
    elif monster_type == 'hc_champion':
        return pvp_m.process_champion_fight_result(
            challenger_id=user_id, challenger_char_state=char,
            champion_owner_id=monster['owner_id'], 
            champion_id_in_fight=monster['champion_id'],
            is_challenger_win=True, context=context
        )
        
    if monster_type == 'бой_обычный': quest_manager.update_quest_progress(user_id, 'pve_kill_common')
    elif monster_type == 'бой_редкий': quest_manager.update_quest_progress(user_id, 'pve_kill_rare')
    elif monster_type == 'босс':
        quest_manager.update_quest_progress(user_id, 'pve_kill_boss')
        quest_manager.update_quest_progress(user_id, 'pve_complete_floor')
        if char.get('run_type') == 'pvp':
            quest_manager.update_quest_progress(user_id, 'pvp_ghost_wins')
    elif monster_type == 'изгнанник': quest_manager.update_quest_progress(user_id, 'pve_defeat_exile')
    
    is_boss_fight = monster['type'] == 'босс'
    effective_stats = get_effective_stats(char)
    
    if is_boss_fight:
        # --- НАЧАЛО ИЗМЕНЕНИЯ: Добавляем обработку новых перков Возвышения ---
        # Старые перки
        if effective_stats.get('health_regen_on_boss'):
            heal_percent = effective_stats['health_regen_on_boss']
            heal_amount = int(effective_stats['max_health'] * (heal_percent / 100.0))
            char['stats']['health'] = min(effective_stats['max_health'], char['stats']['health'] + heal_amount)
        if effective_stats.get('es_regen_on_boss'):
            char['stats']['energy_shield'] = min(effective_stats['max_energy_shield'], char['stats']['energy_shield'] + effective_stats['es_regen_on_boss'])
        
        # Новые суммирующиеся перки
        char.setdefault('permanent_bonuses', {})
        if effective_stats.get('perm_hp_on_boss'):
            char['permanent_bonuses']['max_health'] = char['permanent_bonuses'].get('max_health', 0) + effective_stats['perm_hp_on_boss']
        if effective_stats.get('perm_es_on_boss'):
            char['permanent_bonuses']['max_energy_shield'] = char['permanent_bonuses'].get('max_energy_shield', 0) + effective_stats['perm_es_on_boss']
        if effective_stats.get('perm_def_on_boss'):
            char['permanent_bonuses']['defense'] = char['permanent_bonuses'].get('defense', 0) + effective_stats['perm_def_on_boss']
        if effective_stats.get('perm_dodge_on_boss'):
            char['permanent_bonuses']['dodge_chance'] = char['permanent_bonuses'].get('dodge_chance', 0) + effective_stats['perm_dodge_on_boss']
        if effective_stats.get('perm_block_on_boss'):
            char['permanent_bonuses']['block_chance'] = char['permanent_bonuses'].get('block_chance', 0) + effective_stats['perm_block_on_boss']
        if effective_stats.get('perm_all_def_on_boss'):
            bonus_value = effective_stats['perm_all_def_on_boss']
            char['permanent_bonuses']['block_chance'] = char['permanent_bonuses'].get('block_chance', 0) + bonus_value
            char['permanent_bonuses']['dodge_chance'] = char['permanent_bonuses'].get('dodge_chance', 0) + bonus_value
            char['permanent_bonuses']['defense'] = char['permanent_bonuses'].get('defense', 0) + bonus_value
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    if effective_stats.get('health_regen', 0) > 0:
        heal_amount = int(effective_stats['max_health'] * (effective_stats['health_regen'] / 100.0))
        char['stats']['health'] = min(effective_stats['max_health'], char['stats']['health'] + heal_amount)

    loot_type_map = {'бой_обычный': 1, 'бой_редкий': 3, 'лутгоблин': 5, 'босс': 10, 'изгнанник': 8, 'сундук': 6}
    loot_multiplier = loot_type_map.get(monster['type'], 1)
    gold_bonus_mult = 1.0 + (effective_stats.get('gold_find', 0) / 100.0)
    gold = int(random.randint(5 * loot_multiplier, 15 * loot_multiplier) * gold_bonus_mult)
    char['currency']['gold'] += gold
    
    victory_text = f"🎉 *Вы победили {escape_markdown(monster['name'])}\\!*\n\nВы получили *{gold}* 🪙 золота\\."
    
    run_type = char.get('run_type')
    current_floor = run_state['floor']
    
    if is_boss_fight and run_type is None:
        pve_xp_rewards = {1: 100, 2: 150, 3: 250}
        if current_floor in pve_xp_rewards:
            xp_reward = pve_xp_rewards[current_floor]
            level_up_msg = db.add_xp_and_level_up(user_id, xp_reward)
            victory_text += f"\n\nВы получили *{xp_reward}* опыта за победу над боссом этажа\\."
            if level_up_msg: victory_text += f"\n\n{level_up_msg}"

    if is_boss_fight and run_type == 'endless':
        max_floor_record = db.get_endless_max_floor(user_id)
        if current_floor > max_floor_record:
            db.add_rewards(user_id, divines=2, mirrors=0)
            victory_text += "\n\n✨ *Новый рекорд\\!* За первое прохождение этого этажа вы получаете *2 💎 Divine Orbs*\\!"
        
        # --- НАЧАЛО ИЗМЕНЕНИЙ ---
        if current_floor > 4:
            # Увеличиваем счетчик скалирования персонажа
            char.setdefault('endless_scaling_stacks', 0)
            char['endless_scaling_stacks'] += 1
        # --- КОНЕЦ ИЗМЕНЕНИЙ ---
            
        xp_reward = 100 + (current_floor * 100)
        level_up_msg = db.handle_endless_victory_updates(user_id, run_state, xp_reward)
        victory_text += f"\n\nВы получили *{xp_reward}* опыта\\."
        if level_up_msg: victory_text += f"\n\n{level_up_msg}"

    loot = []
    if char.get('pending_chest_reward') == 'cursed':
        victory_text += "\n\n🎁 *Сундук открывается, изливая на вас двойную порцию сокровищ\\!*"
        loot1 = im.generate_loot(run_state['floor'], char, 'сундук')
        loot2 = im.generate_loot(run_state['floor'], char, 'сундук')
        loot = loot1 + loot2
        char.pop('pending_chest_reward')
    else:
        loot = im.generate_loot(run_state['floor'], char, monster['type'])
    char['pending_loot'] = loot

    harvest_stats = db.get_harvest_stats(user_id)
    harvest_level = harvest_stats.get('level', 1)
    for seed_id, chance in {'seed_t1': 0.05, 'seed_t2': 0.04 if harvest_level >= 5 else 0, 'seed_t3': 0.03 if harvest_level >= 10 else 0, 'seed_t4': 0.02 if harvest_level >= 20 else 0, 'seed_t5': 0.01 if harvest_level >= 25 else 0}.items():
        if random.random() < chance:
            harvest_manager.add_seed(user_id, seed_id)
            victory_text += f"\n🌿 Выпало семя: *{escape_markdown(HARVEST_SEEDS[seed_id]['name'])}*\\!"
            
    dropped_card_name = dcm.handle_card_drop(user_id, monster_type)
    if dropped_card_name:
        victory_text += f"\n\n🎴 Вы нашли гадальную карту: *{escape_markdown(dropped_card_name)}*\\!"
        
    char['combat'] = None
    char['current_events'] = []
    if char.get('buffs'):
        for buff in char.get('buffs', []):
            # Убедитесь, что "Источник Жизни" здесь в условии
            if 'duration' in buff and ('Святилище' in buff.get('name', '') or 'Источник Жизни' in buff.get('name', '')):
                buff['duration'] -= 1
        char['buffs'] = [b for b in char.get('buffs', []) if b.get('duration', 0) > 0]
    
    if is_boss_fight:
        char['boss_defeated_flag'] = True
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        if run_type in ['pvp', 'hc_pvp']: 
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---
            return pvp_m.handle_pvp_victory(user_id, run_state, telegram_user)
        if run_type is None:
            char_snapshot = copy.deepcopy(char)
            char_snapshot['stats']['health'] = char_snapshot['stats']['max_health']
            char_snapshot['stats']['energy_shield'] = char_snapshot['stats']['max_energy_shield']
            db.save_character_for_pvp(user_id, run_state['floor'], char_snapshot, telegram_user)
    
    im.recalculate_stats(user_id, char)
    
    char['just_won_fight'] = True

    # --- НАЧАЛО ИЗМЕНЕНИЙ: Логика Кузницы Горнила ---
    is_endless_run = char.get('run_type') == 'endless'
    current_floor = run_state['floor']

    # --- НАЧАЛО ИЗМЕНЕНИЯ: Новая объединенная логика для Бесконечного режима ---
    if is_boss_fight and is_endless_run and current_floor >= 4:
        # Проверяем условия для разных событий
        is_crucible_floor = current_floor >= 5 and (current_floor - 5) % 10 == 0
        is_even_floor = current_floor % 2 == 0

        # Сохраняем сообщение о победе, оно будет использовано в любом из следующих UI
        char['pending_victory_message'] = victory_text
        db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])

        if is_crucible_floor:
            # Приоритет №1: Если это этаж Кузницы (5, 15, 25...), показываем ее UI
            return ui.create_crucible_post_boss_ui(run_state)
        elif is_even_floor:
            # Приоритет №2: Если это чётный этаж (4, 6, 8...), показываем UI покупки Возвышения
            return ui.create_post_boss_endless_ui(run_state)
        # Если этаж нечётный и не является этажом Кузницы (7, 9, 11...),
        # этот блок ничего не делает, и код переходит к стандартному экрану добычи.
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    if is_boss_fight and run_state['floor'] in [1, 2, 3]:
        # --- НАЧАЛО ИЗМЕНЕНИЯ: Добавляем проверку на лимит умений ---
        # Проверяем, сколько умений Восхождения игрок УЖЕ выбрал в этом забеге.
        if len(char.get('chosen_ascendancy_passives', [])) < 3:
            # Если выбрано меньше трех, начисляем очко как обычно.
            char.setdefault('ascendancy_points', 0)
            char['ascendancy_points'] += 1
            char.setdefault('chosen_ascendancy_passives', [])
            char['pending_victory_message'] = victory_text
            db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
            return ui.create_ascendancy_choice_ui(run_state)
        else:
            # Если лимит в 3 умения уже достигнут, очко не начисляется.
            # Игрок просто переходит к экрану с добычей.
            # Сообщение о победе будет показано на следующем экране.
            pass # Просто позволяем коду продолжиться до стандартного экрана победы над боссом
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    
    if is_boss_fight:
        return {'text': victory_text, 'buttons': [[{'text': '▶️ К добыче', 'callback_data': 'show_post_boss_loot'}]]}
    else:
        loot_ui = ui.create_loot_choice_ui(run_state)
        if post_combat_logs:
            victory_text += "\n\n" + "\n".join(post_combat_logs)
        loot_ui['text'] = victory_text + "\n\n" + loot_ui['text']
        return loot_ui
