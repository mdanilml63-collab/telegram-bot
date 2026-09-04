# item_manager.py

import random
import copy
import database as db
import perk_manager as perk_m
from game_content import CONTENT, BASE_STATS, SMITH_SIMPLE_UPGRADES, SMITH_BLESSINGS_POOL, ITEM_SETS
import ui_components as ui
import quest_manager
from utils import escape_markdown
from game_content import ASCENDANCY_PASSIVES

def get_base_stats_with_perks(user_id, base_stats=None):
    """
    (ИЗМЕНЕНО) Рассчитывает статы с учетом Базы класса и Глобальных перков.
    """
    from game_content import BASE_STATS

    if base_stats is None:
        stats = copy.deepcopy(BASE_STATS)
    else:
        stats = copy.deepcopy(base_stats)
    
    # Применяем перки за валюту (Divine/Mirror)
    player_perks = perk_m.get_player_perks(user_id)
    if player_perks:
        for stat, value in player_perks.items():
            if stat == 'max_health':
                stats['max_health'] += value
            elif stat == 'max_energy_shield':
                stats.setdefault('max_energy_shield', 0)
                stats['max_energy_shield'] += value
            else:
                stats[stat] = stats.get(stat, 0) + value
            
    # Синхронизируем текущие ХП и Щит с максимальными
    stats['health'] = stats['max_health']
    if 'max_energy_shield' in stats:
        stats.setdefault('energy_shield', 0)
        stats['energy_shield'] = stats['max_energy_shield']
            
    return stats


def _get_rarity(character_state, monster_type):
    base_chances = {
        'бой_обычный': {'magic': 0.65, 'rare': 0.3, 'unique': 0.05}, 'бой_редкий': {'magic': 0.25, 'rare': 0.60, 'unique': 0.10, 'legendary': 0.05},
        'лутгоблин': {'rare': 0.65, 'unique': 0.25, 'legendary': 0.1}, 'босс': {'rare': 0.0, 'unique': 0.6, 'legendary': 0.4},
        'изгнанник': {'magic': 0.1, 'rare': 0.6, 'unique': 0.25, 'legendary': 0.05},
        'сундук': {'rare': 0.75, 'unique': 0.20, 'legendary': 0.05}
    }
    chances = copy.deepcopy(base_chances.get(monster_type, {'magic': 1.0}))
    magic_find_mult = 1.0 + (ui.get_effective_stats(character_state).get('magic_find', 0) / 100.0)
    if 'rare' in chances: chances['rare'] *= magic_find_mult
    if 'unique' in chances: chances['unique'] *= magic_find_mult
    if 'legendary' in chances: chances['legendary'] *= magic_find_mult
    total_chance = sum(chances.values())
    if total_chance > 0:
        for rarity in chances: chances[rarity] /= total_chance
    rarities = list(chances.keys())
    weights = list(chances.values())
    # ИСПРАВЛЕНИЕ: Добавлен [0] для извлечения строки из списка.
    return random.choices(rarities, weights, k=1)[0]

def generate_loot(floor_num, character_state, monster_type):
    content_floor_num = floor_num
    if character_state.get('run_type') == 'endless' and floor_num > 4:
        content_floor_num = 4

    loot_choices = []
    chosen_item_names = set()
    floor_items = CONTENT[f"floor_{content_floor_num}"]['items']
    user_id = character_state['user_id']

    all_custom_items = db.get_all_custom_items()
    floor_custom_items = [item for item in all_custom_items if item.get('floor') == floor_num]

    # ИЗМЕНЕНИЕ: Учитываем Keystone на доп. предмет
    effective_stats = ui.get_effective_stats(character_state)
    num_items_to_generate = 3 + effective_stats.get('extra_loot_choice', 0)
    if monster_type == 'босс' and effective_stats.get('extra_loot_choice_on_boss'):
        num_items_to_generate += effective_stats['extra_loot_choice_on_boss']

    rarities_to_generate = [_get_rarity(character_state, monster_type) for _ in range(num_items_to_generate)]

    for rarity in rarities_to_generate:
        candidate_pool = []
        candidate_pool.extend(floor_items.get(rarity, []))
        candidate_pool.extend([item for item in floor_custom_items if item.get('rarity') == rarity])

        available_candidates = [item for item in candidate_pool if item['name'] not in chosen_item_names]

        if available_candidates:
            chosen_item = random.choice(available_candidates)
            item_to_add = copy.deepcopy(chosen_item)
            
            item_to_add['rarity'] = rarity
            
            loot_choices.append(item_to_add)
            chosen_item_names.add(chosen_item['name'])

            if rarity == 'rare':
                quest_manager.update_quest_progress(user_id, 'pve_find_rare_item')
            elif rarity == 'unique':
                quest_manager.update_quest_progress(user_id, 'pve_find_unique_item')
        
    return loot_choices

def recalculate_stats(user_id, character):
    from game_content import CLASS_DATA, ASCENDANCY_PASSIVES, PASSIVE_SKILL_TREE

    old_max_health = ui.get_effective_stats(character).get('max_health', 1)
    current_health = character['stats'].get('health', 1)
    old_max_es = ui.get_effective_stats(character).get('max_energy_shield', 0)
    current_es = character['stats'].get('energy_shield', 0)

    # --- Шаг 1: Фундамент (База + Перки) ---
    class_id = character.get('class_id')
    base_class_stats = CLASS_DATA.get(class_id, {}).get('stats')
    run_type = character.get('run_type')
    new_stats = {}

    if run_type == 'hc_pvp':
        if base_class_stats: new_stats = copy.deepcopy(base_class_stats)
        else: new_stats = copy.deepcopy(BASE_STATS)
        new_stats['health'] = new_stats['max_health']
        new_stats['energy_shield'] = new_stats.get('max_energy_shield', 0)
    else:
        new_stats = get_base_stats_with_perks(user_id, base_stats=base_class_stats)
    
    perm_bonuses = character.get('permanent_bonuses', {})
    for stat, value in perm_bonuses.items():
        if stat == 'max_health': new_stats['max_health'] += value
        elif stat == 'max_energy_shield': new_stats['max_energy_shield'] += value
        else: new_stats[stat] = new_stats.get(stat, 0) + value

    # --- Шаг 2 и 3: Экипировка и Сеты ---
    equipped_items = [item for item in character['equipment'].values() if item]
    equipped_sets, overrides_and_caps = {}, {}
    scholar_set_active = False
    
    # Собираем все уникальные механики в один список для последующей обработки
    active_mechanics = [item.get('special_mechanic') for item in equipped_items if item and item.get('special_mechanic')]

    for item in equipped_items:
        for stat, value in item.get('stats', {}).items():
            if stat.endswith(('_override', '_cap')):
                overrides_and_caps[stat] = value
                continue
            if stat == 'health': new_stats['max_health'] += value
            elif stat == 'energy_shield': new_stats['max_energy_shield'] += value
            else: new_stats[stat] = new_stats.get(stat, 0) + value
        if 'implicit' in item:
            for stat, value in item['implicit']['effect'].items():
                if isinstance(value, (int, float)):
                    if stat == 'health': new_stats['max_health'] += int(value)
                    elif stat == 'energy_shield': new_stats['max_energy_shield'] += int(value)
                    else: new_stats[stat] = new_stats.get(stat, 0) + int(value)
        if 'set_id' in item:
            equipped_sets[item['set_id']] = equipped_sets.get(item['set_id'], 0) + 1

    # --- НАЧАЛО ИСПРАВЛЕНИЯ: Единственный, корректный блок обработки сетов ---
    character['active_set_bonuses'] = []
    unity_ring_equipped = 'forgiving_set_bonus' in active_mechanics

    for set_id, count in equipped_sets.items():
        set_info = ITEM_SETS.get(set_id)
        if set_info and (count >= set_info['pieces'] or (unity_ring_equipped and count >= set_info['pieces'] - 1)):
            character['active_set_bonuses'].append(set_info)
            if set_id == 'scholar':
                scholar_set_active = True
            
            if 'special_mechanic' in set_info['bonus']:
                active_mechanics.append(set_info['bonus']['special_mechanic'])
            
            if 'effect' in set_info['bonus']:
                for stat, value in set_info['bonus']['effect'].items():
                    if stat == 'health': new_stats['max_health'] += int(value)
                    elif stat == 'energy_shield': new_stats['max_energy_shield'] += int(value)
                    else: new_stats[stat] = new_stats.get(stat, 0) + int(value)
    # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

    # Проверяем наличие "Искаженной души" и считаем оскверненные предметы
    if 'leech_per_corrupted_item' in active_mechanics:
        corrupted_count = sum(1 for item in equipped_items if item.get('corrupted'))
        if corrupted_count > 0:
            leech_bonus = corrupted_count * 2 # +2% за каждый предмет
            new_stats['lifesteal'] = new_stats.get('lifesteal', 0) + leech_bonus
            new_stats['es_leech_rate'] = new_stats.get('es_leech_rate', 0) + leech_bonus
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Логика для новых и переработанных сетов ---
    if 'bonus_per_corrupted_item_set' in active_mechanics:
        corrupted_count = sum(1 for item in equipped_items if item.get('corrupted'))
        if corrupted_count > 0:
            bonus = 5 * corrupted_count
            core_stats = ['attack', 'defense', 'dodge_chance', 'block_chance', 'crit_chance']
            for stat in core_stats:
                new_stats[stat] = new_stats.get(stat, 0) + bonus

    if 'defense_to_crit_conversion' in active_mechanics:
        crit_bonus = int(new_stats.get('defense', 0) * 0.5)
        new_stats['crit_chance'] = new_stats.get('crit_chance', 0) + crit_bonus
        
    if 'attack_scaling_from_gold' in active_mechanics:
        gold = character.get('currency', {}).get('gold', 0)
        attack_bonus = min(25, gold // 200)
        new_stats['attack'] = new_stats.get('attack', 0) + attack_bonus
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    if run_type != 'hc_pvp':
        learned_skills = db.get_player_skills(user_id)
        multipliers = {}
        for skill_id in learned_skills:
            skill_data = PASSIVE_SKILL_TREE.get(skill_id)
            if not skill_data or not skill_data.get('effects'): continue
            for effect, value in skill_data['effects'].items():
                if effect.endswith('_override'):
                    overrides_and_caps[effect] = value
                    continue
                if effect.endswith('_mult'):
                    multipliers[effect.replace('_mult', '')] = multipliers.get(effect.replace('_mult', ''), 0) + value
                elif effect.endswith('_override'):
                    new_stats[effect.replace('_override', '')] = value
                elif effect == 'lifesteal_to_es':
                    if new_stats.get('lifesteal', 0) > 0:
                        new_stats['es_leech_rate'] = new_stats.get('es_leech_rate', 0) + new_stats['lifesteal']
                        new_stats['lifesteal'] = 0
                else:
                    if effect == 'max_health': new_stats['max_health'] += value
                    elif effect == 'max_energy_shield': new_stats.setdefault('max_energy_shield', 0); new_stats['max_energy_shield'] += value
                    else: new_stats[effect] = new_stats.get(effect, 0) + value
        
        for stat, total_mult in multipliers.items():
            if stat in new_stats:
                new_stats[stat] = int(new_stats[stat] * (1 + total_mult))

    # --- НАЧАЛО ИСПРАВЛЕНИЯ: ПЕРЕМЕЩЕНИЕ И ОБЪЕДИНЕНИЕ ЛОГИКИ ---
    # Шаг 1: Применяем особенность Ведьмы до всех конвертаций
    if new_stats.get('arcane_substitution'):
        current_max_health = new_stats.get('max_health', 0)
        health_to_convert = int(current_max_health * 0.5)
        new_stats['max_health'] -= health_to_convert
        new_stats.setdefault('max_energy_shield', 0)
        new_stats['max_energy_shield'] += health_to_convert
        # Удаляем флаг, чтобы он не применился снова
        del new_stats['arcane_substitution']

    # Шаг 2: Применяем Возвышение, включая новое для Ведьмы
    chosen_passives = character.get('chosen_ascendancy_passives', [])
    if class_id and chosen_passives:
        for passive_id in chosen_passives:
            passive_data = ASCENDANCY_PASSIVES.get(class_id, {}).get(passive_id)
            if passive_data and 'effects' in passive_data:
                for stat, value in passive_data['effects'].items():
                    if stat == 'attack_scaling_from_es': # <-- НОВАЯ ПРОВЕРКА
                        bonus_attack = int(new_stats.get('max_energy_shield', 0) * value)
                        new_stats['attack'] = new_stats.get('attack', 0) + bonus_attack
                    elif stat == 'max_health': new_stats['max_health'] += value
                    elif stat == 'max_energy_shield': new_stats.setdefault('max_energy_shield', 0); new_stats['max_energy_shield'] += value
                    elif stat.endswith('_mult'):
                        base_stat = stat.replace('_mult', '')
                        new_stats[base_stat] = int(new_stats.get(base_stat, 0) * (1 + value))
                    else:
                        new_stats[stat] = new_stats.get(stat, 0) + value
    # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

    # --- Шаг 5: Масштабирующиеся механики (Scaling) ---
    for item in equipped_items:
        if 'scaling_stats' in item:
            for target_stat, scale_data in item['scaling_stats'].items():
                if target_stat == 'attack_from_health_override':
                    source_value = new_stats.get(scale_data['source'], 0)
                    new_stats['attack'] = int(source_value * scale_data['ratio'])
                    continue 
                source_value = new_stats.get(scale_data['source'], 0)
                bonus = source_value * scale_data['ratio']
                if target_stat == 'max_health': new_stats['max_health'] += int(bonus)
                elif target_stat == 'max_energy_shield': new_stats['max_energy_shield'] += int(bonus)
                else: new_stats[target_stat] = new_stats.get(target_stat, 0) + int(bonus)
    if 'defense_from_es' in active_mechanics:
        new_stats['defense'] = new_stats.get('defense', 0) + int(new_stats.get('max_energy_shield', 0) * 0.5)

    if 'balance_dodge_block' in active_mechanics:
        max_val = max(new_stats.get('dodge_chance', 0), new_stats.get('block_chance', 0))
        new_stats['dodge_chance'], new_stats['block_chance'] = max_val, max_val
    if 'dodge_to_crit_conversion' in active_mechanics:
        new_stats['crit_chance'] = new_stats.get('crit_chance', 0) + new_stats.get('dodge_chance', 0)
        new_stats['dodge_chance'] = 0
    if 'attack_to_health_conversion' in active_mechanics:
        new_stats['max_health'] += int(new_stats.get('attack', 0) * 0.5)
    if 'es_to_health_no_es' in active_mechanics:
        new_stats['max_health'] += int(new_stats.get('max_energy_shield', 0) * 0.5)
        new_stats['max_energy_shield'] = 0
    if 'es_to_health_conversion' in active_mechanics:
        new_stats['max_health'] += new_stats.get('max_energy_shield', 0)
        new_stats['max_energy_shield'] = 0
    if 'full_es_to_health' in active_mechanics:
        new_stats['max_health'] += new_stats.get('max_energy_shield', 0)
        new_stats['max_energy_shield'] = 1
    if 'split_health_es_pool' in active_mechanics:
        total_pool = new_stats['max_health'] + new_stats.get('max_energy_shield', 0)
        new_stats['max_health'] = int(total_pool * 0.5)
        new_stats['max_energy_shield'] = int(total_pool * 0.5)
        new_stats['lifesteal'] = new_stats.get('lifesteal', 0) + 5
        new_stats['es_leech_rate'] = new_stats.get('es_leech_rate', 0) + 5
        # --- НАЧАЛО ИЗМЕНЕНИЙ: Логика для "Покрова Тени" ---
    if 'es_leech_to_lifesteal_conversion' in active_mechanics:
        if new_stats.get('es_leech_rate', 0) > 0:
            es_leech_amount = new_stats['es_leech_rate']
            new_stats['lifesteal'] = new_stats.get('lifesteal', 0) + es_leech_amount
            new_stats['es_leech_rate'] = 0
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Добавляем недостающие механики сюда ---
    if 'attack_scaling_from_block_chance' in active_mechanics:
        bonus_attack = int(new_stats.get('block_chance', 0) * 0.5)
        new_stats['attack'] = new_stats.get('attack', 0) + bonus_attack

    if 'attack_scaling_from_accuracy' in active_mechanics:
        bonus_attack = new_stats.get('accuracy', 0) // 10
        new_stats['attack'] = new_stats.get('attack', 0) + bonus_attack
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    if 'berserker_on_low_life' in active_mechanics:
        # Проверяем условие низкого здоровья на основе ТЕКУЩЕГО здоровья, а не максимального
        if character['stats'].get('health', 1) / new_stats.get('max_health', 1) < 0.5:
            new_stats['lifesteal'] = new_stats.get('lifesteal', 0) + 10
            # Применяем мультипликатор к атаке
            new_stats['attack'] = int(new_stats.get('attack', 0) * 1.20)
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    if scholar_set_active:
        set_info = ITEM_SETS['scholar']
        bonus_effect = set_info['bonus']['effect']
        if 'attack_from_es_percent' in bonus_effect:
            ratio = bonus_effect['attack_from_es_percent']
            bonus_attack = int(new_stats.get('max_energy_shield', 0) * ratio)
            new_stats['attack'] = new_stats.get('attack', 0) + bonus_attack
    
    if character.get('run_type') == 'endless':
        scaling_stacks = character.get('endless_scaling_stacks', 0)
        if scaling_stacks > 0:
            multiplier = 1.0 + (scaling_stacks * 0.02)
            new_stats['max_health'] = int(new_stats.get('max_health', 0) * multiplier)
            new_stats['max_energy_shield'] = int(new_stats.get('max_energy_shield', 0) * multiplier)
            new_stats['attack'] = int(new_stats.get('attack', 0) * multiplier)

    # --- НАЧАЛО ИЗМЕНЕНИЙ: Добавление всех новых механик в special_flags ---
    character['special_flags'] = {
        'healing_damages_you': 'healing_damages_you' in active_mechanics,
        'lifesteal_leeches_es_instead': 'lifesteal_leeches_es_instead' in active_mechanics,
        'health_degen_on_turn_start': 'health_degen_on_turn_start' in active_mechanics,
        'always_be_critted': 'always_be_critted' in active_mechanics,
        'healing_overflow_to_es': 'healing_overflow_to_es' in active_mechanics,
        'crit_costs_hp_for_damage': 'crit_costs_hp_for_damage' in active_mechanics,
        'cannot_be_dodged_and_blocked': 'cannot_be_dodged_and_blocked' in active_mechanics,
        'bypass_es_50_percent': 'bypass_es_50_percent' in active_mechanics,
        'anti_leech_on_crit': 'anti_leech_on_crit' in active_mechanics,
        'es_bypass_immunity': 'es_bypass_immunity' in active_mechanics or new_stats.get('es_bypass_immunity', False),
        'crit_consumes_es_for_mult': 'crit_consumes_es_for_mult' in active_mechanics
    }
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    for key, value in overrides_and_caps.items():
        if key.endswith('_override'):
            base_stat = key.replace('_override', '')
            new_stats[base_stat] = value
        elif key.endswith('_cap'):
            base_stat = key.replace('_cap', '')
            if base_stat in new_stats and new_stats[base_stat] > value:
                new_stats[base_stat] = value

    character['stats'] = new_stats
    final_max_stats = ui.get_effective_stats(character)
    
    health_change = final_max_stats.get('max_health', old_max_health) - old_max_health
    es_change = final_max_stats.get('max_energy_shield', old_max_es) - old_max_es
    
    new_health = current_health + health_change
    character['stats']['health'] = min(new_health, final_max_stats.get('max_health', new_health))
    
    if character['stats'].get('max_energy_shield', 0) > 0:
        new_es = current_es + es_change
        character['stats']['energy_shield'] = min(new_es, final_max_stats.get('max_energy_shield', new_es))
    else:
        character['stats']['energy_shield'] = 0
        
    return character

def handle_transmutation(character, chosen_item, floor_num):
    """
    Проверяет наличие "Камня Алхимика" и пытается улучшить редкость предмета.
    Возвращает (возможно измененный) предмет и сообщение для лога.
    """
    if not any(item.get('special_mechanic') == 'transmute_on_pickup_chance' for item in character.get('equipment', {}).values() if item):
        return chosen_item, None

    if random.random() > 0.10: # 10% шанс
        return chosen_item, None
        
    current_rarity = chosen_item.get('rarity')
    rarity_map = ['magic', 'rare', 'unique']
    if current_rarity not in rarity_map:
        return chosen_item, None # Нельзя улучшить легендарки или другие типы

    current_index = rarity_map.index(current_rarity)
    if current_index + 1 >= len(rarity_map):
        return chosen_item, None # Уже максимальная улучшаемая редкость

    new_rarity = rarity_map[current_index + 1]
    
    content_floor_num = floor_num
    if character.get('run_type') == 'endless' and floor_num > 4:
        content_floor_num = 4
    
    item_pool = CONTENT[f"floor_{content_floor_num}"]['items'].get(new_rarity, [])
    if not item_pool:
        return chosen_item, None

    new_item = copy.deepcopy(random.choice(item_pool))
    new_item['rarity'] = new_rarity
    
    message = f"💎 *Камень Алхимика сработал\\!* Ваш предмет *{escape_markdown(chosen_item['name'])}* трансмутировал в *{escape_markdown(new_item['name'])}*\\!"
    return new_item, message

def equip_item(user_id, item_index, target_slot=None):
    """
    Атомарно обрабатывает надевание предмета: находит его по индексу в pending_loot,
    надевает в нужный слот и очищает pending_loot.
    """
    run_state = db.get_pve_run_state(user_id)
    if not run_state or not run_state.get('character'):
        # Проверка на случай, если состояние забега или персонажа повреждено
        return None
        
    char = run_state['character']
    
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Защита от двойного нажатия ---
    # Проверка, что pending_loot существует и индекс в его пределах
    if 'pending_loot' not in char or not isinstance(char['pending_loot'], list) or item_index >= len(char['pending_loot']):
        return None # Невозможно найти предмет (уже взят), выходим
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    item_to_equip = char['pending_loot'][item_index]

    # Используем target_slot, если он передан (для колец), иначе используем slot предмета.
    final_slot = target_slot if target_slot else item_to_equip.get('slot')
    if not final_slot:
        return None # У предмета нет слота

    char['equipment'][final_slot] = item_to_equip
    char['pending_loot'] = []  # Очищаем список ожидания здесь
    
    char = recalculate_stats(user_id, char)
    
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    
    return db.get_pve_run_state(user_id) # Возвращаем самое свежее состояние

def perform_simple_upgrade(user_id, character, slot):
    item = character['equipment'].get(slot)
    if not item: return character, "Ошибка: в этом слоте нет предмета."
    item_type = 'weapon' if 'weapon' in slot else ('armour' if slot in ['helmet', 'body_armour', 'gloves', 'boots'] else 'accessory')
    upgrade_pool = SMITH_SIMPLE_UPGRADES[item_type]
    stat_to_upgrade, value_to_add = random.choice(list(upgrade_pool.items()))
    item['stats'][stat_to_upgrade] = item['stats'].get(stat_to_upgrade, 0) + value_to_add
    item['name'] += "+"
    character['equipment'][slot] = item
    character = recalculate_stats(user_id, character) # Передаем user_id
    # ИСПРАВЛЕНИЕ: Экранирован восклицательный знак '!' для MarkdownV2.
    return character, f"Предмет *{escape_markdown(item['name'])}* улучшен\\! Получен бонус: `{escape_markdown(stat_to_upgrade)}: +{value_to_add}`"

def perform_blessing(user_id, character, slot):
    item = character['equipment'].get(slot)
    if not item: return character, "Ошибка: в этом слоте нет предмета\\."
    num_blessings = random.randint(1, 3)
    applied_blessings = []
    for _ in range(num_blessings):
        blessing = copy.deepcopy(random.choice(SMITH_BLESSINGS_POOL))
        # ИСПРАВЛЕНИЕ: Сначала извлекаем единственный кортеж (ключ, значение) из списка,
        # а затем распаковываем его в две переменные.
        stat, value = list(blessing.items())[0]
        item['stats'][stat] = item['stats'].get(stat, 0) + value
        applied_blessings.append(f"`{escape_markdown(stat)}: +{value}`")
    if not item['name'].startswith("✨"):
        item['name'] = "✨" + item['name']
    character['equipment'][slot] = item
    character = recalculate_stats(user_id, character) # Передаем user_id
    blessings_str = ", ".join(applied_blessings)
    return character, f"Предмет *{escape_markdown(item['name'])}* получил {num_blessings} благословения: {blessings_str}"

def perform_tier_up(character, floor_num):
    equipped_items = [item for item in character['equipment'].values() if item]
    if not equipped_items: return character, None, "У вас нет надетых предметов для улучшения\\."
    
    item_to_upgrade = random.choice(equipped_items)
    current_rarity = item_to_upgrade.get('rarity', 'magic')
    
    if current_rarity == 'magic': new_rarity = 'rare'
    elif current_rarity == 'rare': new_rarity = 'unique'
    elif current_rarity == 'unique': new_rarity = 'legendary'
    else: return character, None, "Легендарные предметы являются вершиной мастерства и не могут быть улучшены дальше\\."
    
    # --- НАЧАЛО ИЗМЕНЕНИЯ: Исправление для Бесконечного режима ---
    # Определяем, из какого этажа брать пул предметов.
    content_floor_num = floor_num
    if character.get('run_type') == 'endless' and floor_num > 4:
        content_floor_num = 4
    
    # Используем безопасный номер этажа для доступа к контенту.
    item_pool = CONTENT[f"floor_{content_floor_num}"]['items'].get(new_rarity, [])
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    if not item_pool: return character, None, "Не удалось создать предмет более высокой редкости для этого этажа\\."
    
    new_item = copy.deepcopy(random.choice(item_pool))
    new_item['rarity'] = new_rarity
    character['pending_loot'] = [new_item]
    
    return character, new_item, None