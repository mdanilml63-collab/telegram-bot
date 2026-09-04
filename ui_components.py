# ui_components.py
import random
import json
import database as db
import fishing_manager
import quest_manager
import time
import datetime
import pytz
import calendar
import world_boss_manager as wbm
import rhoa_race_manager
import event_manager as em
from game_content import FISHING_RODS, FISHING_XP_PER_LEVEL
# --- НАЧАЛО ИЗМЕНЕНИЙ ---
# Добавляем CONTENT в этот импорт
from game_content import (EVENT_TYPES, CURRENCY, SHOP_PRICES, SMITH_COSTS, 
                          HEALER_PRICES, ITEM_SETS, HARVEST_SEEDS, HARVEST_PLANTS, 
                          HARVEST_FERTILIZERS, HARVEST_BED_UPGRADES, HARVEST_CRAFTING_CONFIG, RHOA_NAMES, CONTENT, CLASS_DATA)
# --- КОНЕЦ ИЗМЕНЕНИЙ ---
from event_manager import SHRINE_BUFFS
from utils import escape_markdown
from telegram import InlineKeyboardButton
from game_content import DIVINATION_CARDS
from game_content import ASCENDANCY_PASSIVES
import leaderboard_manager

STAT_DISPLAY_MAP = {
    'attack': '⚔️ Атака',
    'defense': '🧱 Защита',
    'dodge_chance': '💨 Уворот',
    'crit_chance': '🎯 Шанс крита',
    'crit_multiplier': '💫 Крит множитель',
    'block_chance': '✋ Шанс блока',
    'defense_penetration': '🗡️ Пробитие Защиты',
    'block_penetration': '🛡️ Пробитие блока',
    'double_damage_chance': '🔥 Двойной урон',
    'accuracy': '👁️ Точность',
    'lifesteal': '🩸 Вампиризм',
    'es_leech_rate': '🔮 Вампиризм щита',
    'crit_damage_reduction': '🛡️ Защита от крита',
    'magic_find': '🍀 Поиск предметов',
    # Системные статы, которые не отображаются в общем списке, но важны для карты
    'health': '❤️ Здоровье', 
    'max_health': '❤️ Здоровье',
    'energy_shield': '💙 Энергощит',
    'max_energy_shield': '💙 Энергощит',
}
STAT_CAPS = {
    'dodge_chance': 75,
    'block_chance': 75,
    'defense': 75,
    'defense_penetration': 75 # Базовый предел, может быть изменен предметами
}
PERMANENT_DEBUFF_DESCRIPTIONS = {
    'block_chance': "Ваша способность блокировать удары ослаблена.",
    'max_health': "Ваша жизненная сила иссушена.",
    'defense': "Ваша броня стала менее эффективной.",
    'attack': "Ваши атаки стали слабее.",
    'crit_chance': "Ваша удача отвернулась от вас.",
    'dodge_chance': "Ваши движения стали неуклюжими."
}
# --- НАЧАЛО НОВОГО БЛОКА: Иконки уникальных свойств для боя ---
STATUS_ICONS = {
    'cannot_be_blocked': '🚫✋',
    'cannot_be_dodged': '🚫💨',
    'cannot_be_crit': '🛡️💫',
    'immune_to_double_damage': '🛡️🔥',
    'es_bypass_immunity': '🛡️🔮',
    'always_be_critted': '❗🎯',
    'reflect_damage_25': '🌵',
    'dodge_chance_override_zero': '⛓️💨', # Нельзя уворачиваться
    'crit_chance_override_zero': '⛓️💫',  # Нельзя наносить криты
    'double_damage_chance_override_zero': '⛓️🔥' # Нельзя наносить двойной урон
}

def _get_status_icons_string(effective_stats):
    """(НОВОЕ) Собирает строку иконок уникальных свойств для отображения в бою."""
    icons = []
    
    # Сначала проверяем комбинированное свойство, чтобы избежать дублирования иконок
    if effective_stats.get('cannot_be_dodged_and_blocked'):
        icons.append(STATUS_ICONS['cannot_be_blocked'])
        icons.append(STATUS_ICONS['cannot_be_dodged'])
    else:
        # Если его нет, проверяем по отдельности
        if effective_stats.get('cannot_be_blocked'):
            icons.append(STATUS_ICONS['cannot_be_blocked'])
        if effective_stats.get('cannot_be_dodged'):
            icons.append(STATUS_ICONS['cannot_be_dodged'])

    # Проверяем остальные свойства
    if effective_stats.get('cannot_be_crit'):
        icons.append(STATUS_ICONS['cannot_be_crit'])
    if effective_stats.get('immune_to_double_damage'):
        icons.append(STATUS_ICONS['immune_to_double_damage'])
    if effective_stats.get('es_bypass_immunity'):
        icons.append(STATUS_ICONS['es_bypass_immunity'])
    if effective_stats.get('always_be_critted'):
        icons.append(STATUS_ICONS['always_be_critted'])
    if effective_stats.get('reflect_damage_25'):
        icons.append(STATUS_ICONS['reflect_damage_25'])
        
    # Проверяем ограничения (оверрайды)
    if effective_stats.get('dodge_chance_override') == 0:
        icons.append(STATUS_ICONS['dodge_chance_override_zero'])
    if effective_stats.get('crit_chance_override') == 0:
        icons.append(STATUS_ICONS['crit_chance_override_zero'])
    if effective_stats.get('double_damage_chance_override') == 0:
        icons.append(STATUS_ICONS['double_damage_chance_override_zero'])

    if not icons:
        return ""
    
    # Форматируем строку: "✨ Свойства: 🚫✋ 🛡️💫 ❗🎯"
    return f"\n✨ *Свойства:* {', '.join(icons)}"
# --- КОНЕЦ НОВОГО БЛОКА ---

def generate_hp_display(current, maximum, symbol='❤️', empty_symbol='🖤'):
    if maximum <= 0: return ""
    current = max(0, current)
    hp_percent = current / maximum
    filled_hearts = round(hp_percent * 10)
    empty_hearts = 10 - filled_hearts
    display_str = (symbol * filled_hearts) + (empty_symbol * empty_hearts)
    return f"{display_str} \\({current}/{maximum}\\)"

def get_entity_stats_string(stats, is_item_bonus=False, exclude_stats=None, is_class_display=False):
    """
    Универсальная функция для создания отформатированной строки характеристик
    с возможностью исключения определенных статов.
    """
    if exclude_stats is None:
        exclude_stats = []
        
    stat_lines = []
    # Статы, которые не нужно отображать как проценты
    flat_stats = ['attack', 'health', 'max_health', 'energy_shield', 'max_energy_shield', 'accuracy']

    # --- ИЗМЕНЕНИЕ: Добавляем логику для отображения классов ---
    if is_class_display:
        # Убираем дубли, так как health/max_health имеют одно имя
        exclude_stats.extend(['health', 'energy_shield'])

    for stat_key, display_name in STAT_DISPLAY_MAP.items():
        if stat_key in exclude_stats:
            continue

        value = stats.get(stat_key)
        if value or (is_item_bonus and value is not None):
            # --- НАЧАЛО ИЗМЕНЕНИЙ: Исправление логики отображения предела ---
            if stat_key in STAT_CAPS and not is_item_bonus:
                # Устанавливаем предел по умолчанию
                cap = STAT_CAPS[stat_key]
                # Для пробития защиты проверяем, есть ли в статах персонажа переопределенное значение
                if stat_key == 'defense_penetration':
                    cap = stats.get('penetration_cap', cap)
                
                displayed_value = min(value, cap)
                
                if value > cap:
                    stat_lines.append(f"{display_name}: `{displayed_value}% ({value}%)`")
                else:
                    stat_lines.append(f"{display_name}: `{value}%`")
            # --- КОНЕЦ ИЗМЕНЕНИЙ ---
            else:
                prefix = "+" if is_item_bonus and value > 0 else ""
                suffix = "" if stat_key in flat_stats else "%"
                
                if is_class_display and not value and stat_key not in ['max_health', 'max_energy_shield']:
                    continue

                stat_lines.append(f"{display_name}: `{prefix}{value}{suffix}`")
            # --- КОНЕЦ ИЗМЕНЕНИЯ ---
            
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Отображение особых свойств класса ---
    if is_class_display:
        special_features = []
        if stats.get('es_bypass_immunity'):
            special_features.append("Иммунитет к пробитию энергощита")
        if stats.get('cannot_be_crit'):
            special_features.append("Иммунитет к критическим ударам")
        if stats.get('immune_to_double_damage'):
            special_features.append("Иммунитет к двойному урону")
        if stats.get('crit_pen'):
            special_features.append(f"\\+{stats['crit_pen']}% к пробитию защиты при крит ударе")
        if stats.get('cannot_be_dodged'):
            special_features.append("Ваши атаки не могут быть уклонены")
        if stats.get('cannot_be_blocked'):
            special_features.append("Ваши атаки не могут быть заблокированы")
        if stats.get('damage_split_mom'):
            special_features.append(f"{int(stats['damage_split_mom']*100)}% урона по здоровью перенаправляется в энергощит")
        if stats.get('arcane_substitution'):
            special_features.append("50% здоровья конвертируется в энергощит")
        
        if special_features:
            stat_lines.append(f"✨ *Особенность:* {', '.join(special_features)}")
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
            
    return "\n".join(stat_lines)



def get_item_description_string(item):
    """
    (ИСПРАВЛЕНО) Создает полное, отформатированное описание предмета, включая ВСЕ особые механики.
    """
    if not item:
        return "_Слот пуст_"

    # Получаем базовые, уже отформатированные статы
    # Исключаем "служебные" статы, которые опишем отдельно
    exclude_list = ['cannot_be_dodged', 'cannot_be_blocked', 'cannot_be_crit', 
                    'increased_damage_taken', 'attack_mult', 'defense_mult',
                    'crit_chance_cap', 'dodge_chance_override', 'crit_chance_override',
                    'double_damage_chance_override', 'penetration_cap_override']
    base_stats_text = get_entity_stats_string(item.get('stats', {}), is_item_bonus=True, exclude_stats=exclude_list)
    
    plain_effects = []
    item_stats = item.get('stats', {})
    if 'lifespan' in item and isinstance(item['lifespan'], list) and len(item['lifespan']) == 2:
        plain_effects.append(f"⏳ Оставшийся срок службы: {item['lifespan'][0]}/{item['lifespan'][1]} боёв")
    
    if 'charges' in item and isinstance(item['charges'], list) and len(item['charges']) == 2:
        plain_effects.append(f"⚡️ Зарядов осталось: {item['charges'][0]}/{item['charges'][1]}")
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Добавляем описания для ВСЕХ новых механик ---

    # 1. Обработка 'special_mechanic'
    if 'special_mechanic' in item:
        mechanic = item['special_mechanic']
        if mechanic == 'healing_overflow_to_es': plain_effects.append("Избыточное лечение здоровья восстанавливает энергощит")
        if mechanic == 'always_be_critted': plain_effects.append("Вы всегда получаете критические удары")
        if mechanic == 'crit_costs_hp_for_damage': plain_effects.append("Крит удары наносят на 50% больше урона, но стоят 10% текущего здоровья")
        if mechanic == 'debuff_attack_on_first_block': plain_effects.append("Первый блок за бой снижает атаку врага на 25%")
        if mechanic == 'transmute_on_pickup_chance': plain_effects.append("10% шанс улучшить редкость подобранного предмета")
        if mechanic == 'random_base_attack_per_fight': plain_effects.append("Ваша базовая атака становится случайной (От 1 до 100) в начале каждого боя")
        if mechanic == 'leech_per_corrupted_item': plain_effects.append("Дает +2% вампиризма здоровья и энергощита за каждый оскверненный предмет")
        if mechanic == 'attack_scaling_on_missing_health': plain_effects.append("Увеличивает атаку на 1% за каждый 1% недостающего здоровья")
        if mechanic == 'random_teleport_on_win': plain_effects.append("После победы перемещает вас в случайную комнату случайного этажа")
        if mechanic == 'health_degen_on_turn_start': plain_effects.append("Вы теряете 10% здоровья в начале вашего хода")
        if mechanic == 'balance_dodge_block': plain_effects.append("Ваши шансы уворота и блока становятся равны наивысшему из них")
        if mechanic == 'shield_only_build': plain_effects.append("Удваивает бонусы от щита, но запрещает использовать оружие")
        if mechanic == 'lifesteal_leeches_es_instead': plain_effects.append("100% вампиризма здоровья применяется к энергощиту")
        if mechanic == 'defense_from_es': plain_effects.append("Защита рассчитывается от 50% макс энергощита")
        if mechanic == 'healing_damages_you': plain_effects.append("Любое лечение (кроме вампиризма) наносит вам урон")
        if mechanic == 'dodge_to_crit_conversion': plain_effects.append("100% шанса уворота конвертируется в шанс крит. удара")
        if mechanic == 'amplify_set_bonuses': plain_effects.append("Увеличивает эффект от бонусов комплектов на 50%")
        if mechanic == 'bonus_per_corrupted_item': plain_effects.append("Дает +10 к атаке и +1% к криту за каждый оскверненный предмет")
        if mechanic == 'split_health_es_pool': plain_effects.append("Объединяет здоровье и щит, разделяя их 50/50, и дает +5% вампиризма обоим")
        if mechanic == 'death_defiance_once': plain_effects.append("Один раз за бой спасает от смерти, оставляя 1 ХП, даруя неуязвимость на 1 ход")
        if mechanic == 'attack_to_health_conversion': plain_effects.append("50% вашей атаки конвертируется в макс. здоровье")
        if mechanic == 'forgiving_set_bonus': plain_effects.append("Вы получаете бонусы от комплектов, даже если не хватает одной части")
        if mechanic == 'es_to_health_no_es': plain_effects.append("50% макс энергощита конвертируется в здоровье, обнуляя щит")
        if mechanic == 'es_to_health_conversion': plain_effects.append("Ваш энергощит добавляется к здоровью, но становится равен 0")
        if mechanic == 'full_es_to_health': plain_effects.append("Ваш энергощит добавляется к здоровью, но становится равен 1")
        if mechanic == 'reflect_damage_25': plain_effects.append("Отражает 25% от полученного урона обратно в атакующего")
        if mechanic == 'bonus_per_empty_slot': plain_effects.append("Дает бонусы за каждый пустой слот экипировки")
        if mechanic == 'cannot_be_dodged_and_blocked': plain_effects.append("Ваши атаки не могут быть уклонены или заблокированы")
        if mechanic == 'bypass_es_50_percent': plain_effects.append("50% вашего урона игнорирует энергощит и наносится напрямую по здоровью")
        if mechanic == 'anti_leech_on_crit': plain_effects.append("Критические удары накладывают на врага дебафф, запрещающий любой вампиризм на 2 хода")
        # --- НОВОЕ ОПИСАНИЕ ---
        if mechanic == 'es_bypass_immunity': plain_effects.append("Вы невосприимчивы к эффектам, пробивающим энергощит")

    # 2. Обработка триггеров on_..._effect
    if item.get('on_dodge_effect', {}).get('guaranteed_crit_next_hit'): plain_effects.append("После уворота ваша следующая атака гарантированно будет критической")
    if item.get('on_dodge_effect', {}).get('heal_percent_on_dodge'): plain_effects.append(f"Восстанавливает {item['on_dodge_effect']['heal_percent_on_dodge']}% здоровья при увороте")
    if item.get('on_block_effect', {}).get('heal_percent'): plain_effects.append(f"Восстанавливает {item['on_block_effect']['heal_percent']}% здоровья при блоке")
    if item.get('on_block_effect', {}).get('es_heal_percent'): plain_effects.append(f"Восстанавливает {item['on_block_effect']['es_heal_percent']}% энергощита при блоке")
    if item.get('on_attack_effect', {}).get('self_damage_percent'): plain_effects.append(f"Каждая атака отнимает у вас {item['on_attack_effect']['self_damage_percent']}% здоровья")
    if item.get('on_attack_effect', {}).get('self_es_damage_percent'): plain_effects.append(f"Атаки поглощают {item['on_attack_effect']['self_es_damage_percent']}% энергощита от вашей атаки для доп. урона")
    if item.get('on_crit_taken_effect', {}).get('add_attack_next_hit'): plain_effects.append(f"При получении крит. удара ваша след. атака усилена на {item['on_crit_taken_effect']['add_attack_next_hit']}")
    if item.get('on_crit_effect', {}).get('defense_penetration'): plain_effects.append(f"Крит. удары получают +{item['on_crit_effect']['defense_penetration']}% к пробитию защиты")
    if item.get('on_hit_taken_effect', {}).get('add_defense_temp'): plain_effects.append(f"При получении удара вы получаете +{item['on_hit_taken_effect']['add_defense_temp']}% к защите на 1 ход")

    # 3. Обработка прочих уникальных статов
    if item_stats.get('increased_damage_taken'): plain_effects.append(f"Вы получаете на {int(item_stats['increased_damage_taken']*100)}% больше урона")
    if item_stats.get('attack_mult'): plain_effects.append(f"Вы наносите на {int(item_stats['attack_mult']*100)}% больше урона")
    if item_stats.get('defense_mult'): plain_effects.append(f"Вы получаете на {int(abs(item_stats['defense_mult'])*100)}% меньше защиты")
    if item_stats.get('crit_chance_cap'): plain_effects.append(f"Ваш шанс крит. удара не может быть выше {item_stats['crit_chance_cap']}%")
    if item_stats.get('dodge_chance_override') == 0: plain_effects.append("Вы не можете уворачиваться от атак")
    if item_stats.get('crit_chance_override') == 0: plain_effects.append("Вы не можете наносить критические удары")
    if item_stats.get('double_damage_chance_override') == 0: plain_effects.append("Вы не можете наносить двойной урон")
    if item_stats.get('penetration_cap_override'): plain_effects.append(f"Предел пробития защиты увеличен до {item_stats['penetration_cap_override']}%")
    
    # 4. Обработка стандартных "cannot" статов
    if item_stats.get('cannot_be_blocked'): plain_effects.append("Ваши атаки не могут быть заблокированы")
    if item_stats.get('cannot_be_dodged'): plain_effects.append("Ваши атаки не могут быть уклонены")
    if item_stats.get('cannot_be_crit'): plain_effects.append("По вам нельзя нанести критический удар")
    
    # 5. Обработка scaling_stats
    if 'scaling_stats' in item:
        for target_stat, scale_data in item['scaling_stats'].items():
            source_stat_name = STAT_DISPLAY_MAP.get(scale_data['source'], scale_data['source']).split(' ', 1)[-1]
            target_stat_name = STAT_DISPLAY_MAP.get(target_stat, target_stat).split(' ', 1)[-1]
            ratio = scale_data['ratio']
            plain_effects.append(f"Дает +{ratio} к '{target_stat_name}' за каждую 1 ед. '{source_stat_name}'")

    # 6. Обработка conditional_stats
    if 'conditional_stats' in item:
        for target_stat, cond_data in item['conditional_stats'].items():
            condition_text = ""
            if cond_data['condition'] == 'offhand_empty': condition_text = "если левая рука пуста"
            elif cond_data['condition'] == 'health_below_50': condition_text = "когда здоровье ниже 50%"
            elif cond_data['condition'] == 'health_below_30': condition_text = "когда здоровье ниже 30%"
            elif cond_data['condition'] == 'not_hit_last_turn': condition_text = "если вас не ранили в прошлом ходу"
            elif cond_data['condition'] == 'enemy_full_health': condition_text = "по врагам с полным здоровьем"
            
            value = cond_data['value']
            target_stat_name = STAT_DISPLAY_MAP.get(target_stat, target_stat).split(' ', 1)[-1]
            
            if target_stat.endswith("_mult"):
                target_stat_name = "Урон"
                plain_effects.append(f"Дает +{int(value * 100)}% к '{target_stat_name}', {condition_text}")
            else:
                 plain_effects.append(f"Дает +{value} к '{target_stat_name}', {condition_text}")

    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    if not plain_effects:
        return base_stats_text
    else:
        # Форматируем все собранные описания
        formatted_effects = [f"✨ _{escape_markdown(effect)}_" for effect in plain_effects]
        effects_text = "\n" + "\n".join(formatted_effects)
        
        if not base_stats_text:
            return effects_text.strip()
        return base_stats_text + "\n" + effects_text.strip()

def create_ring_slot_choice_ui(item_index, character):
    """
    Создает умный UI для выбора слота кольца, который адаптируется
    в зависимости от того, заняты ли слоты, и показывает статы.
    """
    ring1 = character['equipment'].get('ring1')
    ring2 = character['equipment'].get('ring2')
    buttons = []
    rarity_colors = {'magic': '🟦', 'rare': '🟨', 'unique': '🟧', 'legendary': '🟪'}

    # --- НАЧАЛО ИЗМЕНЕНИЙ: Формируем подробный текст с описанием колец ---
    text = "Вы подобрали новое кольцо\\. Ваши действия:\n"

    # Блок для Кольца 1
    text += "\n\\-\\-\\- *Слот 1* \\-\\-\\-\n"
    if ring1:
        color = rarity_colors.get(ring1.get('rarity'), '⬜️')
        stats_string = get_item_description_string(ring1)
        text += f"{color} *{escape_markdown(ring1['name'])}*\n{stats_string}\n"
    else:
        text += "_Слот пуст_\n"

    # Блок для Кольца 2
    text += "\n\\-\\-\\- *Слот 2* \\-\\-\\-\n"
    if ring2:
        color = rarity_colors.get(ring2.get('rarity'), '⬜️')
        stats_string = get_item_description_string(ring2)
        text += f"{color} *{escape_markdown(ring2['name'])}*\n{stats_string}\n"
    else:
        text += "_Слот пуст_\n"
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    # Логика кнопок остается прежней, текст в них простой и безопасный
    if ring1:
        button_text = "Заменить Кольцо 1"
        callback_data = f'ring_choice:ring1:{item_index}'
    else:
        button_text = "Надеть в Слот 1"
        callback_data = f'equip_confirm:{item_index}:ring1'
    buttons.append([{'text': button_text, 'callback_data': callback_data}])

    if ring2:
        button_text = "Заменить Кольцо 2"
        callback_data = f'ring_choice:ring2:{item_index}'
    else:
        button_text = "Надеть в Слот 2"
        callback_data = f'equip_confirm:{item_index}:ring2'
    buttons.append([{'text': button_text, 'callback_data': callback_data}])

    buttons.append([{'text': '◀️ Назад к выбору лута', 'callback_data': 'back_to_loot_choice'}])
    
    return {'text': text, 'buttons': buttons}


def get_effective_stats(entity):
    """
    (ИСПРАВЛЕНО) Рассчитывает итоговые характеристики с учетом всех динамических эффектов.
    """
    effective_stats = entity['stats'].copy()
    
    for buff in entity.get('buffs', []):
        for stat, value in buff['effect'].items():
            if stat == 'max_health':
                effective_stats['max_health'] += value
                effective_stats['health'] += value 
            elif stat == 'max_energy_shield':
                effective_stats.setdefault('max_energy_shield', 0)
                effective_stats.setdefault('energy_shield', 0)
                effective_stats['max_energy_shield'] += value
                effective_stats['energy_shield'] += value
            else:
                effective_stats[stat] = effective_stats.get(stat, 0) + value
    
    if 'class_id' in entity and 'chosen_ascendancy_passives' in entity:
        asc_passives = ASCENDANCY_PASSIVES.get(entity['class_id'], {})
        for passive_id in entity['chosen_ascendancy_passives']:
            passive_effects = asc_passives.get(passive_id, {}).get('effects', {})
            # --- НАЧАЛО ИСПРАВЛЕНИЯ ---
            for stat, value in passive_effects.items():
                 # --- НАЧАЛО КЛЮЧЕВОГО ИСПРАВЛЕНИЯ ---
                # Игнорируем специальные накопительные бонусы.
                # Их обработкой занимается исключительно функция _handle_victory.
                if stat.startswith('perm_') and stat.endswith('_on_boss'):
                    continue # Переходим к следующему эффекту, не применяя этот
                # --- КОНЕЦ КЛЮЧЕВОГО ИСПРАВЛЕНИЯ ---
                # Обрабатываем особый случай условного уворота
                if stat == 'conditional_dodge':
                    if not (entity.get('combat') or {}).get('player_damaged_last_turn', True):
                        effective_stats['dodge_chance'] = effective_stats.get('dodge_chance', 0) + value
                # Все остальные пассивные эффекты (включая heal_on_block_percent) применяем напрямую
                else:
                    effective_stats[stat] = effective_stats.get(stat, 0) + value
            # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

    if 'equipment' in entity:
        for item in entity['equipment'].values():
            if not item: continue

            # --- НАЧАЛО ИЗМЕНЕНИЙ: Новые динамические и условные механики ---
            if item.get('special_mechanic') == 'attack_scaling_on_missing_health':
                missing_health_percent = 1 - (effective_stats.get('health', 0) / effective_stats.get('max_health', 1))
                attack_bonus = effective_stats.get('attack', 0) * missing_health_percent
                effective_stats['attack'] += attack_bonus

            if 'conditional_stats' in item:
                for target_stat, cond_data in item['conditional_stats'].items():
                    is_condition_met = False
                    condition = cond_data['condition']
                    value = cond_data['value']
                    
                    if condition == 'offhand_empty' and not entity['equipment'].get('weapon2'):
                        is_condition_met = True
                    elif condition == 'health_below_50' and (effective_stats['health'] / effective_stats.get('max_health', 1)) < 0.5:
                        is_condition_met = True
                    elif condition == 'health_below_30' and (effective_stats['health'] / effective_stats.get('max_health', 1)) < 0.3:
                        is_condition_met = True
                    # Этот флаг устанавливается в combat_manager
                    elif condition == 'not_hit_last_turn' and not (entity.get('combat') or {}).get('player_damaged_last_turn', True):
                        is_condition_met = True

                    if is_condition_met:
                        if target_stat.endswith('_mult'):
                            base_stat = target_stat.replace('_mult', '')
                            effective_stats[base_stat] = effective_stats.get(base_stat, 0) * (1 + value)
                        else:
                            effective_stats[target_stat] = effective_stats.get(target_stat, 0) + value
            # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    # --- НАЧАЛО ИЗМЕНЕНИЯ: Копируем флаги и механики в итоговые статы ---
    if 'special_flags' in entity:
        for flag, value in entity['special_flags'].items():
            effective_stats[flag] = value
            
    if 'equipment' in entity:
        for item in entity['equipment'].values():
            if item and 'special_mechanic' in item:
                # Добавляем флаг для каждой найденной уникальной механики
                effective_stats[item['special_mechanic']] = True
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---    
    if 'equipment' in entity:
        for item in entity['equipment'].values():
            if not item: continue
            
            # Ограничение шанса крита
            if item.get('stats', {}).get('crit_chance_cap'):
                cap = item['stats']['crit_chance_cap']
                effective_stats['crit_chance'] = min(effective_stats.get('crit_chance', 0), cap)
    for stat, value in effective_stats.items():
        if isinstance(value, float):
            effective_stats[stat] = round(value)
    effective_stats['health'] = min(effective_stats.get('health', 1), effective_stats.get('max_health', 1))
    effective_stats['energy_shield'] = min(effective_stats.get('energy_shield', 0), effective_stats.get('max_energy_shield', 0))

    return effective_stats

def get_player_stats_string(character_state, title="👤 *Ваш персонаж*", show_equipment=True):
    # --- НАЧАЛО ИЗМЕНЕНИЯ ---
    class_id = character_state.get('class_id')
    class_name = CLASS_DATA.get(class_id, {}).get('name', 'Неизвестный класс')
    
    # Добавляем класс в заголовок
    header = f"{title} \\({escape_markdown(class_name.split(' ')[0])}\\)\n\n"
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---
    base_stats = character_state['stats']
    effective_stats = get_effective_stats(character_state)
    c, e, buffs, perm_bonuses = character_state.get('currency', {}), character_state.get('equipment', {}), character_state.get('buffs', []), character_state.get('permanent_bonuses', {})
    header = f"{title}\n\n"
    hp_bar = generate_hp_display(base_stats.get('health', 0), effective_stats.get('max_health', 1))
    es_bar = generate_hp_display(base_stats.get('energy_shield', 0), effective_stats.get('max_energy_shield', 0), '💙', '🖤')
    main_stats_header = f"❤️ Здоровье: {hp_bar}\n" + (f"💙 Энергощит: {es_bar}\n" if effective_stats.get('max_energy_shield', 0) > 0 else "") + "\n"
    
    stats_to_exclude = ['health', 'max_health', 'energy_shield', 'max_energy_shield']
    main_stats_values = get_entity_stats_string(effective_stats, exclude_stats=stats_to_exclude)

    effect_info = ""
     # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    # Добавляем отображение бонуса скалирования
    if character_state.get('run_type') == 'endless' and character_state.get('endless_scaling_stacks', 0) > 0:
        stacks = character_state['endless_scaling_stacks']
        scaling_bonus = stacks * 5
        effect_info += f"\n\n♾️ *Скалирование Бесконечности*: `+{scaling_bonus}%` к ❤️, 💙 и ⚔️"
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    if buffs:
        buff_lines = [f"✨ *{escape_markdown(b['name'])}*: _{escape_markdown(b['desc'])}_" for b in buffs]
        effect_info += "\n\n*Временные эффекты:*\n" + "\n".join(buff_lines)
    if character_state.get('active_set_bonuses'):
        set_bonus_lines = [f"✅ *{escape_markdown(s['name'])}* \\({s['pieces']}/{s['pieces']}\\): _{escape_markdown(s['bonus']['desc'])}_" for s in character_state['active_set_bonuses']]
        effect_info += "\n\n*Бонусы комплектов:*\n" + "\n".join(set_bonus_lines)

    # --- НАЧАЛО ИЗМЕНЕНИЙ: Улучшенный блок для постоянных эффектов ---
    if perm_bonuses:
        bonus_lines = []
        debuff_lines = []
        
        # Разделяем бонусы и проклятия
        for stat, value in perm_bonuses.items():
            if value > 0:
                display_name = STAT_DISPLAY_MAP.get(stat, stat)
                # Убираем "базовый" из описания для краткости
                display_name = display_name.replace('Базовое ', '').replace('базовому ', '')
                suffix = '%' if stat not in ['max_health', 'attack', 'max_energy_shield', 'accuracy'] else ''
                bonus_lines.append(f"🏆 *{escape_markdown(display_name)}*: `+{value}{suffix}`")
            elif value < 0:
                # Используем словарь с описаниями для негативных эффектов
                description = PERMANENT_DEBUFF_DESCRIPTIONS.get(stat, f"Характеристика '{stat}' снижена\\.")
                debuff_lines.append(f"🩸 *Жертва*: _{escape_markdown(description)}_ `({value})`")
        
        if bonus_lines:
            effect_info += "\n\n*Бонусы от Испытаний:*\n" + "\n".join(bonus_lines)
        if debuff_lines:
            effect_info += "\n\n*Эффекты от Событий:*\n" + "\n".join(debuff_lines)
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
            
    equipment_info = ""
    if show_equipment and e:
        equipment_info = "\n\n*Экипировка:*\n"
        slot_map = {'weapon1': 'Оружие', 'weapon2': 'Офф\\-хенд', 'helmet': 'Шлем', 'body_armour': 'Броня', 'gloves': 'Перчатки', 'boots': 'Ботинки', 'ring1': 'Кольцо 1', 'ring2': 'Кольцо 2', 'amulet': 'Амулет', 'belt': 'Пояс'}
        for slot, display_name in slot_map.items():
            item = e.get(slot)
            item_name = "_пусто_" if not item else f"`{escape_markdown(item['name'])}{' 🔥' if item.get('corrupted') else ''}`"
            equipment_info += f"{display_name}: {item_name}\n"
            
    currency_info = f"\n💰 *Сокровища:*\n{CURRENCY['золото']['name']}: `{c.get('gold', 0)}`" if c.get('gold', 0) > 0 else ""
    return header + main_stats_header + main_stats_values + effect_info + equipment_info + currency_info

def create_equipped_items_ui(character, back_callback_data='show_char_stats'):
    text, buttons = "📜 *Ваша экипировка*\n", [[{'text': '⬅️ Назад', 'callback_data': back_callback_data}]]
    rarity_colors = {'magic': '🟦', 'rare': '🟨', 'unique': '🟧', 'legendary': '🟪'}
    slot_map = {'weapon1': 'Оружие', 'weapon2': 'Офф\\-хенд', 'helmet': 'Шлем', 'body_armour': 'Броня', 'gloves': 'Перчатки', 'boots': 'Ботинки', 'ring1': 'Кольцо 1', 'ring2': 'Кольцо 2', 'amulet': 'Амулет', 'belt': 'Пояс'}
    has_items = any(character['equipment'].get(slot) for slot in slot_map)
    if not has_items:
        text += "\n_У вас нет надетых предметов\\._"
    else:
        for slot, display_name in slot_map.items():
            item = character['equipment'].get(slot)
            if item:
                color = rarity_colors.get(item.get('rarity'), '⬜️')
                item_full_description = get_item_description_string(item)
                
                text += f"\n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\n*{display_name}:* {color} *{escape_markdown(item['name'])}*\n{item_full_description}\n"
                
                if 'set_id' in item and item['set_id'] in ITEM_SETS:
                    set_info = ITEM_SETS[item['set_id']]
                    text += f"*{escape_markdown(set_info['name'])}* \\(Требуется: {set_info['pieces']}\\)\n" # ИСПРАВЛЕНО
                if 'implicit' in item: text += f"✨ *Скрытое свойство:* {escape_markdown(item['implicit']['name'])} \\({escape_markdown(item['implicit']['desc'])}\\)\n" # ИСПРАВЛЕНО
                if item.get('corrupted'): text += "🔥 *Состояние: Осквернено*\n"
    return {'text': text, 'buttons': buttons}

def generate_event_choices(run_state):
    char = run_state['character']
    choices = char['current_events']
    buttons = [{'text': event['name'], 'callback_data': f"event_{event['id']}"} for event in choices]
    button_rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    bottom_buttons = [{'text': '👤 Мой персонаж', 'callback_data': 'show_char_stats'}]
    
    # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    run_type = char.get('run_type')
    if run_type in ['pvp', 'hc_pvp']:
        bottom_buttons.append({'text': '👹 Текущий Босс', 'callback_data': 'view_pvp_boss'})
    button_rows.append(bottom_buttons)
    
    mode_text = ""
    if run_type == 'pvp':
        mode_text = "*\\(PVP РЕЖИМ\\)*"
    elif run_type == 'hc_pvp':
        mode_text = "*\\(ХАРДКОР PVP\\)*"
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
        
    return {'text': f"📍 *Этаж {run_state['floor']}, комната {run_state['event_num'] + 1}/15* {mode_text}\n\nВы стоите на перепутье\\. Куда вы направитесь?", 'buttons': button_rows}

def create_pvp_boss_view_ui(boss_data, view_mode='stats'):
    # --- НАЧАЛО ИЗМЕНЕНИЯ ---
    class_id = boss_data.get('class_id')
    class_name = CLASS_DATA.get(class_id, {}).get('name', 'Неизвестный класс')
    
    # Добавляем класс в заголовок
    title = f"👹 *Противник на этом этаже: {escape_markdown(boss_data['name'])}* \\({escape_markdown(class_name.split(' ')[0])}\\)"
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---
    boss_char_state = {'stats': boss_data['stats'], 'equipment': boss_data.get('equipment', {}), 'buffs': []}
    title = f"👹 *Противник на этом этаже: {escape_markdown(boss_data['name'])}*"
    
    if view_mode == 'stats':
        # --- НАЧАЛО ИСПРАВЛЕНИЯ ---
        # Теперь мы строим текст вручную, чтобы избежать лишней информации
        
        # Получаем эффективные статы босса
        effective_stats = get_effective_stats(boss_char_state)
        
        # Генерируем полоски здоровья и энергощита
        hp_bar = generate_hp_display(effective_stats.get('health', 0), effective_stats.get('max_health', 1))
        es_bar = generate_hp_display(effective_stats.get('energy_shield', 0), effective_stats.get('max_energy_shield', 0), '💙', '🖤')
        
        # Формируем основной блок с ХП/Щитом
        main_stats_header = f"❤️ Здоровье: {hp_bar}\n"
        if effective_stats.get('max_energy_shield', 0) > 0:
            main_stats_header += f"💙 Энергощит: {es_bar}\n"
        main_stats_header += "\n"

        # Получаем ТОЛЬКО числовые характеристики, без описаний сетов и механик
        stats_to_exclude = ['health', 'max_health', 'energy_shield', 'max_energy_shield']
        main_stats_values = get_entity_stats_string(effective_stats, exclude_stats=stats_to_exclude)
        
        # Собираем финальный текст
        final_text = title + "\n\n" + main_stats_header + main_stats_values
        
        buttons = [
            [{'text': '🎒 Посмотреть экипировку', 'callback_data': 'view_boss_equipment'}],
            [{'text': '⬅️ Назад к выбору пути', 'callback_data': 'continue_run'}]
        ]
        return {'text': final_text, 'buttons': buttons}
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

    elif view_mode == 'equipment':
        # Эта часть остается без изменений, она использует правильную функцию
        result = create_equipped_items_ui(boss_char_state, back_callback_data='view_boss_stats')
        result['text'] = f"{title}\n\n" + result['text']
        return result


def create_shop_ui(run_state):
    character = run_state['character']
    shop_inventory = character.get('shop_inventory', [])
    
    current_gold = character.get('currency', {}).get('gold', 0)
    
    text = (
        "Вы встречаете торговца\\. «Не желаешь взглянуть на мои товары, изгнанник?»\n\n"
        f"💰 *Ваш баланс:* `{current_gold}` 🪙\n\n"
    )

    buttons = []
    if not shop_inventory: 
        text += "_Полки магазина пусты\\._"
        
    rarity_colors = {'magic': '🟦', 'rare': '🟨', 'unique': '🟧', 'legendary': '🟪'}
    
    for i, item in enumerate(shop_inventory):
        rarity = item.get('rarity', 'magic')
        color = rarity_colors.get(rarity, '⬜️')
        price = SHOP_PRICES.get(rarity, 9999)
        
        # --- НАЧАЛО ИЗМЕНЕНИЯ: Используем правильную функцию для описания ---
        item_full_description = get_item_description_string(item)
        
        text += f"\\-\\-\\- Товар {i+1} \\-\\-\\-\n{color} *{escape_markdown(item['name'])}* \\({escape_markdown(item['type'])}\\)\n{item_full_description}\n"
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---
        
        if 'set_id' in item and item['set_id'] in ITEM_SETS:
            set_info = ITEM_SETS[item['set_id']]
            text += f"*{escape_markdown(set_info['name'])}* \\(1/{set_info['pieces']}\\)\n"
            
        buttons.append([{'text': f'Купить Товар {i+1} за {price} 🪙', 'callback_data': f'shop_buy_{i}'}])
        
    buttons.append([{'text': '🎒 Мои Предметы', 'callback_data': 'shop_view_items'}])
    buttons.append([{'text': 'Уйти', 'callback_data': 'continue_run'}])
    
    return {'text': text, 'buttons': buttons}

def create_corruption_altar_ui(character):
    # ИСПРАВЛЕНИЕ: Экранированы точки.
    text = "🔥 Перед вами Алтарь Порчи\\. Вы можете осквернить один из своих предметов\\. Результат непредсказуем\\. Выберите предмет:"
    buttons = []
    equipped_items = {slot: item for slot, item in character['equipment'].items() if item and not item.get('corrupted')}
    if not equipped_items:
        # ИСПРАВЛЕНИЕ: Экранирована точка.
        return {'text': "Вам нечего осквернять\\.", 'buttons': [[{'text': 'Уйти', 'callback_data': 'continue_run'}]]}
    for slot, item in equipped_items.items(): buttons.append([{'text': f"{item['name']}", 'callback_data': f'corrupt_item_{slot}'}])
    buttons.append([{'text': '🎒 Мои Предметы', 'callback_data': 'corruption_view_items'}])
    buttons.append([{'text': 'Не рисковать и уйти', 'callback_data': 'continue_run'}])
    return {'text': text, 'buttons': buttons}

def create_trial_ui(trials):
    # ИСПРАВЛЕНИЕ: Экранирована точка.
    text = "🏆 Вы в зале Испытаний\\. Перед вами три пути, каждый требует мастерства\\. Выберите свой путь:"
    buttons = [[{'text': f"{trial['text']} ({STAT_DISPLAY_MAP.get(trial['stat'], trial['stat'])}: {trial['req']})", 'callback_data': f"trial_choice_{trial['id']}"}] for trial in trials]
    return {'text': text, 'buttons': buttons}

def create_cadiro_offer_ui(item, price):
    rarity_colors = {'magic': '🟦', 'rare': '🟨', 'unique': '🟧', 'legendary': '🟪'}
    rarity = item.get('rarity', 'magic') # <--- ДОБАВЛЕНО
    color = rarity_colors.get(rarity, '⬜️') # <--- ИЗМЕНЕНО
    
    # --- НАЧАЛО ИЗМЕНЕНИЯ: Используем правильную универсальную функцию ---
    item_full_description = get_item_description_string(item)
    
    text = (
        f"💰 Вы видите Кадиро\\! «Здравствуй, изгнанник\\! У меня есть нечто особенное для тебя\\.\\.\\.»\\.\n\n"
        f"\\-\\-\\- Предложение Кадиро \\-\\-\\-\n"
        f"{color} *{escape_markdown(item['name'])}* \\({escape_markdown(item['type'])}\\)\n"
        f"{item_full_description}\n\n"
        f"Цена: *{price}* 🪙 золота\\."
    )
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    buttons = [
        [{'text': f'Купить за {price} 🪙', 'callback_data': 'cadiro_deal_accept'}],
        [{'text': 'Отказаться', 'callback_data': 'cadiro_deal_decline'}]
    ]
    return {'text': text, 'buttons': buttons}

def create_quests_ui(user_id):
    """Создает UI для меню ежедневных заданий."""
    quests_data, reset_time = quest_manager.get_player_quests(user_id)
    
    time_left = reset_time - int(time.time())
    hours, remainder = divmod(time_left, 3600)
    minutes, _ = divmod(remainder, 60)
    
    text = f"🎯 *Ежедневные задания*\n\nНовые задания появятся через: *{hours} ч {minutes} мин*\n\n"
    buttons = []
    
    for i, quest in enumerate(quests_data):
        progress = quest['progress']
        target = quest['target']
        
        if quest['reward_claimed']:
            status_icon = "✅"
            progress_text = "(Награда получена)"
            buttons.append([{'text': f"{status_icon} {escape_markdown(quest['desc'])}", 'callback_data': f'quest_claimed_{i}'}])
        elif progress >= target:
            status_icon = "💎"
            progress_text = "(Готово к сдаче\\!)"
            buttons.append([{'text': f"{status_icon} {escape_markdown(quest['desc'])}", 'callback_data': f'claim_quest_{i}'}])
        else:
            status_icon = "⌛"
            progress_text = f"({progress}/{target})"
            buttons.append([{'text': f"{status_icon} {escape_markdown(quest['desc'])} {progress_text}", 'callback_data': f'quest_inprogress_{i}'}])
    from quest_manager import REROLL_COST
    buttons.append([{'text': f"🔄 Сменить задания за {REROLL_COST} 🟢", 'callback_data': 'reroll_quests'}])
    buttons.append([{'text': '⬅️ В главное меню', 'callback_data': 'back_to_main_menu'}])
    
    return {'text': text, 'buttons': buttons}

def create_blacksmith_ui(run_state):
    character = run_state['character']
    current_gold = character.get('currency', {}).get('gold', 0)
    floor = run_state['floor']

    # ИЗМЕНЕНИЕ: Динамический расчет стоимости с учетом скидки для отображения
    effective_stats = get_effective_stats(character)
    discount = effective_stats.get('service_discount', 0)

    cost_simple_base = int(SMITH_COSTS['simple_upgrade'] * (1 + 0.25 * (floor - 1)))
    cost_blessing_base = int(SMITH_COSTS['blessing'] * (1 + 0.25 * (floor - 1)))
    cost_tier_up_base = int(SMITH_COSTS['tier_up'] * (1 + 0.25 * (floor - 1)))
    
    cost_simple = int(cost_simple_base * (1 - discount / 100.0))
    cost_blessing = int(cost_blessing_base * (1 - discount / 100.0))
    cost_tier_up = int(cost_tier_up_base * (1 - discount / 100.0))
    
    text = (
        "У наковальни стоит могучий кузнец\\. «Хочешь закалить свою сталь, приступай»\n\n"
        f"💰 *Ваш баланс:* `{current_gold}` 🪙"
    )

    buttons = [
        [{'text': f"Простое усиление ({cost_simple} 🪙)", 'callback_data': 'smith_simple'}],
        [{'text': f"Благословение предмета ({cost_blessing} 🪙)", 'callback_data': 'smith_blessing'}],
        [{'text': f"Повышение редкости ({cost_tier_up} 🪙)", 'callback_data': 'smith_tier_up'}],
        [{'text': '🎒 Мои Предметы', 'callback_data': 'smith_view_items'}],
        [{'text': 'Уйти', 'callback_data': 'continue_run'}]
    ]
    return {'text': text, 'buttons': buttons}


def create_smith_item_choice_ui(character, mode):
    cost = SMITH_COSTS.get(mode, 0)
    # ИСПРАВЛЕНИЕ: Экранирована точка.
    text = f"Какой из своих предметов ты доверишь моей наковальне? Это будет стоить {cost} 🪙\\."
    buttons, equipped_items = [], {slot: item for slot, item in character['equipment'].items() if item}
    if not equipped_items:
        # ИСПРАВЛЕНИЕ: Экранирована точка.
        return {'text': "Тебе нечего улучшать\\.", 'buttons': [[{'text': 'Назад', 'callback_data': 'back_to_smith'}]]}
    for slot, item in equipped_items.items(): buttons.append([{'text': f"{item['name']}", 'callback_data': f'smith_select:{mode}:{slot}'}])
    buttons.append([{'text': 'Назад', 'callback_data': 'back_to_smith'}])
    return {'text': text, 'buttons': buttons}

def create_fight_ui(character_state):
    player_base_stats, player_effective_stats = character_state['stats'], get_effective_stats(character_state)
    monster = character_state['combat']['monster']
    monster_effective_stats = get_effective_stats(monster)
    # --- ИЗМЕНЕНИЕ: Исключаем дублирующую информацию ---
    stats_to_exclude = ['health', 'max_health', 'energy_shield', 'max_energy_shield']
    
    # --- НАЧАЛО ИЗМЕНЕНИЯ: Объединяем логику класса и иконок ---
    
    # 1. Генерируем строку с классом для монстра
    monster_class_id = monster.get('class_id')
    monster_class_name = ""
    if monster_class_id:
        monster_class_name = f" \\({escape_markdown(CLASS_DATA.get(monster_class_id, {}).get('name', '').split(' ')[0])}\\)"
    
    # 2. Генерируем строку с иконками для монстра
    monster_properties = _get_status_icons_string(monster_effective_stats)
    
    # 3. Собираем инфо-блок для монстра
    monster_hp_bar = generate_hp_display(monster['stats']['health'], monster_effective_stats['max_health'])
    monster_es_bar = generate_hp_display(monster['stats'].get('energy_shield', 0), monster_effective_stats.get('max_energy_shield', 0), '💙', '🖤')
    monster_stats_str = get_entity_stats_string(monster_effective_stats, exclude_stats=stats_to_exclude)
    monster_info = f"👹 *{escape_markdown(monster['name'])}*{monster_class_name}\n❤️ {monster_hp_bar}\n" + (f"💙 {monster_es_bar}\n" if monster_effective_stats.get('max_energy_shield', 0) > 0 else "") + (f"{monster_stats_str}{monster_properties}\n" if monster_stats_str or monster_properties else "")

    # 4. Генерируем строку с классом для игрока
    player_class_id = character_state.get('class_id')
    player_class_name = ""
    if player_class_id:
        player_class_name = f" \\({escape_markdown(CLASS_DATA.get(player_class_id, {}).get('name', '').split(' ')[0])}\\)"

    # 5. Генерируем строку с иконками для игрока
    player_properties = _get_status_icons_string(player_effective_stats)

    # 6. Собираем инфо-блок для игрока
    player_hp_bar = generate_hp_display(player_base_stats['health'], player_effective_stats['max_health'])
    player_es_bar = generate_hp_display(player_base_stats['energy_shield'], player_effective_stats['max_energy_shield'], '💙', '🖤')
    player_stats_str = get_entity_stats_string(player_effective_stats, exclude_stats=stats_to_exclude)
    player_info = f"👤 *Игрок*{player_class_name}\n❤️ {player_hp_bar}\n" + (f"💙 {player_es_bar}\n" if player_effective_stats.get('max_energy_shield', 0) > 0 else "") + (f"{player_stats_str}{player_properties}\n" if player_stats_str or player_properties else "")
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    log_messages = ""
    last_turn_log = character_state['combat'].get('last_turn_log', {})
    player_log = last_turn_log.get('player', [])
    monster_log = last_turn_log.get('monster', [])

    if player_log:
        log_messages += "\\-\\-\\- *Ваш Ход* \\-\\-\\-\n"
        log_messages += "\n".join([f"`{msg}`" for msg in player_log])

    if monster_log:
        if player_log: log_messages += "\n\n"
        log_messages += "\\-\\-\\- *Ход Противника* \\-\\-\\- \n"
        log_messages += "\n".join([f"`{msg}`" for msg in monster_log])
    
    if not log_messages:
        log_messages = character_state['combat']['log'][0]

    text = (f"{monster_info}\n"
            f"\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\n\n"
            f"{player_info}\n"
            f"📜 *Лог боя:*\n{log_messages}")
            
    is_world_boss = character_state.get('combat', {}).get('is_world_boss', False)
    attack_callback = 'wb_combat_attack' if is_world_boss else 'combat_attack'

    return {'text': text, 'buttons': [[{'text': '⚔️ Атаковать', 'callback_data': attack_callback}]]}

def create_healer_ui(run_state):
    character = run_state['character']
    current_gold = character.get('currency', {}).get('gold', 0)
    floor = run_state['floor']
    
    # ИЗМЕНЕНИЕ: Расчет стоимости с учетом скидки для отображения
    effective_stats = get_effective_stats(character)
    discount = effective_stats.get('service_discount', 0)
    
    cost_50_perc_base = int(HEALER_PRICES['half'] * (1 + 0.25 * (floor - 1)))
    cost_100_perc_base = int(HEALER_PRICES['full'] * (1 + 0.25 * (floor - 1)))
    
    cost_50_perc = int(cost_50_perc_base * (1 - discount / 100.0))
    cost_100_perc = int(cost_100_perc_base * (1 - discount / 100.0))

    current_hp = character['stats']['health']
    max_hp = effective_stats['max_health']
    
    text = (
        "💖 Вы встречаете странствующего лекаря\\. «Чем могу помочь, путник?»\n\n"
        f"❤️ *Ваше здоровье:* `{current_hp}/{max_hp}`\n"
        f"💰 *Ваш баланс:* `{current_gold}` 🪙"
    )

    buttons = [
        [{'text': f"Восстановить 25% ❤️ \\(Бесплатно\\)", 'callback_data': 'healer_free'}],
        [{'text': f"Восстановить 50% ❤️ \\({cost_50_perc} 🪙\\)", 'callback_data': 'healer_half'}],
        [{'text': f"Восстановить 100% ❤️ \\({cost_100_perc} 🪙\\)", 'callback_data': 'healer_full'}],
        [{'text': 'Нет, спасибо', 'callback_data': 'continue_run'}]
    ]
    return {'text': text, 'buttons': buttons}

def create_loot_choice_ui(run_state):
    loot = run_state['character'].get('pending_loot', [])
    if not loot:
        return {'text': "Вы ничего не нашли\\.", 'buttons': [[{'text': '▶️ Продолжить', 'callback_data': 'continue_run'}]]}
    
    text, buttons, rarity_colors = "Вы видите несколько предметов\\. Что вы возьмете?\n", [], {'magic': '🟦', 'rare': '🟨', 'unique': '🟧', 'legendary': '🟪'}
    for i, item in enumerate(loot):
        color = rarity_colors.get(item.get('rarity'), '⬜️')
        item_full_description = get_item_description_string(item)
        
        # ИСПРАВЛЕНО
        text += f"\n\\-\\-\\- Вариант {i+1} \\-\\-\\-\n{color} *{escape_markdown(item['name'])}* \\({escape_markdown(item['type'])}\\)\n{item_full_description}\n"
        
        if 'set_id' in item and item['set_id'] in ITEM_SETS:
            set_info = ITEM_SETS[item['set_id']]
            text += f"*{escape_markdown(set_info['name'])}* \\(1/{set_info['pieces']}\\)\n" # ИСПРАВЛЕНО
            
        buttons.append([{'text': f'Взять "{item["name"]}"', 'callback_data': f'loot_choice_{i}'}])
        
    # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
    buttons.append([{'text': 'Ничего не брать +40 🪙', 'callback_data': 'loot_choice_skip'}])
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    return {'text': text, 'buttons': buttons}

def create_item_comparison_ui(character, new_item, old_item, target_slot, item_index):
    """
    Создает UI для сравнения нового предмета с надетым.
    """
    rarity_colors = {'magic': '🟦', 'rare': '🟨', 'unique': '🟧', 'legendary': '🟪'}
    new_color = rarity_colors.get(new_item.get('rarity'), '⬜️')
    # --- ИЗМЕНЕНИЕ: Используем новую функцию для полного описания ---
    new_item_text = f"*{escape_markdown(new_item['name'])}* \\({escape_markdown(new_item['type'])}\\)\n{get_item_description_string(new_item)}"
    
    if old_item:
        old_color = rarity_colors.get(old_item.get('rarity'), '⬜️')
        old_item_text = f"*{escape_markdown(old_item['name'])}* \\({escape_markdown(old_item['type'])}\\)\n{get_item_description_string(old_item)}"
    else:
        old_color = "⬛️"
        old_item_text = "_Слот пуст_"
        
    warning_text = f"Вы уверены, что хотите заменить {old_color} *{escape_markdown(old_item['name']) if old_item else 'пустой слот'}* на {new_color} *{escape_markdown(new_item['name'])}*?"
    full_text = f"*ЗАМЕНА ПРЕДМЕТА*\n\n▶️ *НОВЫЙ:*\n{new_color} {new_item_text}\n\n◀️ *НАДЕТЫЙ:*\n{old_color} {old_item_text}\n\n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\n{warning_text}"
    
    callback_data_equip = f'equip_confirm:{item_index}:{target_slot}'
    back_callback = 'back_to_loot_choice'

    buttons = [
        [{'text': '✅ Заменить', 'callback_data': callback_data_equip}],
        [{'text': '◀️ Назад', 'callback_data': back_callback}]
    ]
    return {'text': full_text, 'buttons': buttons}

def create_class_selection_ui(run_type):
    """Создает UI для выбора класса перед началом забега."""
    from game_content import CLASS_DATA # Локальный импорт
    
    text = "Выберите свой класс для этого забега\\.\n\n"
    buttons = []
    
    for class_id, data in CLASS_DATA.items():
        text += f"*{escape_markdown(data['name'])}*\n"
        text += f"_{escape_markdown(data['desc'])}_\n"
        stats_text = get_entity_stats_string(data['stats'], is_class_display=True)
        if stats_text:
            text += f"{stats_text}\n\n"
        else:
            text += "\n"
        
        buttons.append([
            InlineKeyboardButton(f"Выбрать {data['name'].split(' ')[0]}", callback_data=f'class_select:{run_type}:{class_id}')
        ])

    buttons.append([InlineKeyboardButton("⬅️ Назад в главное меню", callback_data='back_to_main_menu')])
    return {'text': text, 'buttons': buttons}

def create_passive_skill_tree_ui(user_id, branch=None, sub_branch=None):
    """Создает UI для дерева пассивных умений с разделением на под-ветви."""
    from game_content import PASSIVE_SKILL_TREE
    
    player_info = db.get_player_info(user_id)
    skill_points = player_info.get('skill_points', 0)
    learned_skills = db.get_player_skills(user_id)
    learned_skills.update(['str_start', 'dex_start', 'int_start', 'com_start', 'asc_start'])

    # --- Главное меню дерева ---
    if branch is None:
        text = (f"🌳 *Дерево Пассивных Умений*\n\n"
                f"Вложите очки умений, чтобы навсегда усилить своего персонажа\\.\n\n"
                f"Доступно очков: *{skill_points}*\n\n"
                f"Выберите ветвь для изучения:")
        buttons = [
            [InlineKeyboardButton("🔴 Путь Силы", callback_data='skill_tree_branch:str')],
            [InlineKeyboardButton("🟢 Путь Ловкости", callback_data='skill_tree_branch:dex')],
            [InlineKeyboardButton("🔵 Путь Интеллекта", callback_data='skill_tree_branch:int')],
            [InlineKeyboardButton("⚪ Путь Командира (Универсал)", callback_data='skill_tree_branch:com')],
            [InlineKeyboardButton("⭐ Путь Странника (Гибрид)", callback_data='skill_tree_branch:asc')],
            [InlineKeyboardButton("🔄 Сбросить все умения (2 💎)", callback_data='reset_skills_confirm')],
            [InlineKeyboardButton("⬅️ Назад", callback_data='menu_upgrades_exchange')]
        ]
        return {'text': text, 'buttons': buttons}

    branch_names = {
        'str': "🔴 Путь Силы", 'dex': "🟢 Путь Ловкости", 'int': "🔵 Путь Интеллекта",
        'com': "⚪ Путь Командира", 'asc': "⭐ Путь Странника"
    }
    sub_branch_names = {
        'str': {'core': 'Базовые навыки Воина', 'block': '🛡️ Путь Стража', 'damage': '⚔️ Путь Разрушителя'},
        'dex': {'core': 'Базовые навыки Охотника', 'dd': '🔪 Путь Ассасина', 'crit': '🎯 Путь Снайпера'},
        'int': {'core': 'Базовые навыки Мудреца', 'es': '🔮 Путь Оккультиста', 'crit': '⚡ Путь Адепта'},
        'com': {'core': 'Базовые навыки Командира', 'tactician': '📈 Путь Тактика', 'survivor': '🛡️ Путь Выжившего'},
        'asc': {'core': 'Базовые навыки Странника', 'seeker': '💰 Путь Искателя', 'gambler': '🎲 Путь Авантюриста'}
    }

    # --- Меню выбора под-ветви ---
    if sub_branch is None:
        text = (f"{branch_names[branch]}\n\n"
                f"Доступно очков: *{skill_points}*\n\n"
                "Выберите под\\-ветвь для просмотра:")
        buttons = []
        for sb_id, sb_name in sub_branch_names[branch].items():
            buttons.append([InlineKeyboardButton(sb_name, callback_data=f'skill_tree_sub_branch:{branch}:{sb_id}')])
        buttons.append([InlineKeyboardButton("⬅️ Назад к ветвям", callback_data='menu_skill_tree')])
        return {'text': text, 'buttons': buttons}
        
    # --- Меню отображения конкретной под-ветви ---
    else:
        text = (f"{branch_names[branch]} \\> {escape_markdown(sub_branch_names[branch][sub_branch])}\n\n"
                f"Доступно очков: *{skill_points}*\n")
        buttons = []
        
        sub_branch_skills = {
            sid: sdata for sid, sdata in PASSIVE_SKILL_TREE.items() 
            if sdata.get('branch') == branch and sdata.get('sub_branch') == sub_branch
        }

        skill_chain_map = {sdata.get('requires'): sid for sid, sdata in sub_branch_skills.items()}

        start_node_id = None
        for sid, sdata in sub_branch_skills.items():
            required_skill = sdata.get('requires')
            if required_skill and PASSIVE_SKILL_TREE.get(required_skill, {}).get('sub_branch') != sub_branch:
                start_node_id = sid
                break
        
        ordered_skill_ids = []
        current_node_id = start_node_id
        while current_node_id:
            ordered_skill_ids.append(current_node_id)
            current_node_id = skill_chain_map.get(current_node_id)

        if not ordered_skill_ids:
            text += "\n_В этой ветке пока нет умений\\._"
        else:
            for skill_id in ordered_skill_ids:
                skill_data = PASSIVE_SKILL_TREE[skill_id]
                is_learned = skill_id in learned_skills
                can_learn = skill_data.get('requires') in learned_skills and not is_learned
                
                status_icon = "✅" if is_learned else "➡️" if can_learn else "🔒"
                text += f"\n{status_icon} *{escape_markdown(skill_data['name'])}*\n"
                text += f"   _{escape_markdown(skill_data['desc'])}_\n"

                if not is_learned and not can_learn:
                    required_skill_name = PASSIVE_SKILL_TREE.get(skill_data.get('requires'), {}).get('name', '')
                    text += f"   _Требует: {escape_markdown(required_skill_name)}_\n"

                if can_learn and skill_points > 0:
                    buttons.append([InlineKeyboardButton(f"Изучить '{skill_data['name']}' (1 очко)", callback_data=f'learn_skill_confirm:{skill_id}')])
        
        buttons.append([InlineKeyboardButton("⬅️ Назад к под-ветвям", callback_data=f'skill_tree_branch:{branch}')])
        return {'text': text, 'buttons': buttons}

def create_perks_main_menu_ui(user_id):
    """Создает главное меню выбора типа улучшений."""
    text = "Выберите, за какую валюту вы хотите приобрести постоянные улучшения для своего аккаунта\\."
    buttons = [
        [InlineKeyboardButton("💎 Улучшения за Divine", callback_data='perks_menu_divine')],
        [InlineKeyboardButton("🪞 Улучшения за Mirror", callback_data='perks_menu_mirror')],
        [InlineKeyboardButton("⬅️ Назад в главное меню", callback_data='back_to_main_menu')]
    ]
    return {'text': text, 'buttons': buttons}

def create_perk_purchase_ui(user_id, currency_type):
    """Создает UI для покупки перков за определенную валюту."""
    from perk_manager import PERK_CATALOG, MIRROR_PERK_CATALOG, get_player_perks

    player_info = db.get_player_info(user_id)
    if not player_info:
        return {'text': "❌ *Ошибка: не удалось найти данные вашего профиля\\.*", 'buttons': [[{'text': '⬅️ В главное меню', 'callback_data': 'back_to_main_menu'}]]}

    if currency_type == 'divine':
        title = "Улучшения за Divine Orbs"
        balance = player_info.get('divine_orbs', 0)
        symbol = '💎'
        catalog = PERK_CATALOG
        back_button = 'menu_perks'
    else: # mirror
        title = "Улучшения за Mirror of Kalandra"
        balance = player_info.get('mirrors', 0)
        symbol = '🪞'
        catalog = MIRROR_PERK_CATALOG
        back_button = 'menu_perks'

    player_perks = get_player_perks(user_id)
    
    text = (f"🛠️ *{title}*\n\n"
            f"Ваш баланс: *{balance}* {symbol}\n\n"
            "\\-\\-\\- *Текущие бонусы от всех перков* \\-\\-\\-\n")

    # Формируем строку с бонусами
    perk_lines = []
    for stat, display_name in STAT_DISPLAY_MAP.items():
        value = player_perks.get(stat, 0)
        if value > 0:
            suffix = '%' if stat not in ['attack', 'max_health', 'max_energy_shield', 'health'] else ''
            perk_lines.append(f"{display_name}: `+{value}{suffix}`")
    
    if not perk_lines:
        text += "_У вас пока нет постоянных бонусов_\n"
    else:
        text += "\n".join(perk_lines) + "\n"

    text += "\n\\-\\-\\- *Доступные улучшения* \\-\\-\\-"
    
    buttons = [[{'text': f"{perk_data['name']} ({perk_data['cost']} {symbol})", 'callback_data': f'buy_perk_{perk_id}'}] for perk_id, perk_data in catalog.items()]
    buttons.append([{'text': '⬅️ Назад', 'callback_data': back_button}])
    
    return {'text': text, 'buttons': buttons}

# --- Fishing UI ---

def create_fishing_main_ui(user_id):
    """Создает главное меню рыбалки."""
    text = (
        "🎣 *Рыбалка*\n\n"
        "Вы находитесь в тихом уголке, где можно отдохнуть от вечных сражений и попытать удачу в рыбной ловле\\.\n\n"
        "Здесь вас ждет торговец *Криллсон*, готовый купить ваш улов и продать лучшие снасти\\."
    )
    buttons = [
        [{'text': "🧔‍♂️ Торговец Криллсон", 'callback_data': 'krillson_shop'}],
        [{'text': "🏞️ К Озеру", 'callback_data': 'go_to_lake'}],
        [{'text': "⬅️ В главное меню", 'callback_data': 'back_to_main_menu'}],
    ]
    return {'text': text, 'buttons': buttons}

def create_krillson_shop_ui(user_id):
    """Создает меню магазина Криллсона."""
    stats = db.get_fishing_stats(user_id)
    text = f"🧔‍♂️ *Криллсон*\n\n«Привет, изгнанник\\! Ищешь снасти получше или хочешь продать рыбешку?»\n\nВаш баланс: `{stats.get('chaos_orbs', 0)}` 🟢 Хаос Орбов"
    buttons = [
        [{'text': "Купить Удочку", 'callback_data': 'buy_rod_shop'}],
        # --- НАЧАЛО ИЗМЕНЕНИЙ ---
        [{'text': "Купить Наживку", 'callback_data': 'bait_shop_ui'}],
        [{'text': "Продать Улов", 'callback_data': 'sell_catch_ui'}],
        [{'text': "💪 Улучшить Характеристики (за очки)", 'callback_data': 'fishing_perks_ui'}],
        [{'text': "✨ Обмен Осколков", 'callback_data': 'shard_exchange_ui'}],
        [{'text': "🗺️ Рыболовная Экспедиция", 'callback_data': 'fishing_expedition_ui'}], # << НОВАЯ КНОПКА
        # --- КОНЕЦ ИЗМЕНЕНИЙ ---
        [{'text': "⬅️ Назад", 'callback_data': 'menu_fishing'}],
    ]
    return {'text': text, 'buttons': buttons}

def create_rod_shop_ui(user_id):
    """Создает интерфейс магазина удочек."""
    stats = db.get_fishing_stats(user_id)
    text = "Выбирай с умом, хорошая удочка \\- залог успеха\\.\n\n"
    buttons = []

    available_rods = sorted(
        [rod_id for rod_id, data in FISHING_RODS.items() if rod_id not in stats['unlocked_rods']],
        key=lambda r: FISHING_RODS[r]['level_req']
    )

    if not available_rods:
        text += "_Вы скупили все удочки\\!_"
    else:
        for rod_id in available_rods:
            rod = FISHING_RODS[rod_id]
            is_affordable = stats['chaos_orbs'] >= rod['cost']
            is_level_ok = stats['level'] >= rod['level_req']
            
            status_emoji = "✅" if is_affordable and is_level_ok else "❌"
            cost_text = "Бесплатно" if rod['cost'] == 0 else f"{rod['cost']} 🟢"
            
            # ИСПРАВЛЕНИЕ: Заменены \- на \\-
            text += (f"\\-\\-\\-\\-\n*{escape_markdown(rod['name'])}* {status_emoji}\n"
                     f"Требуемый уровень: `{rod['level_req']}` \\(Ваш: `{stats['level']}`\\)\n"
                     f"Цена: `{cost_text}`\n"
                     f"🎣 Шанс улова: `{rod['stats']['catch_chance']}%`\n"
                     f"💎 Ценный улов: `{rod['stats']['valuable_catch_chance']}%`\n"
                     f"🏋️ Крупный улов: `{rod['stats']['big_catch_chance']}%`\n")
            
            if is_affordable and is_level_ok:
                buttons.append([{'text': f"Купить {rod['name']}", 'callback_data': f'buy_rod:{rod_id}'}])

    buttons.append([{'text': '⬅️ Назад к Криллсону', 'callback_data': 'krillson_shop'}])
    return {'text': text, 'buttons': buttons}
    
def create_sell_catch_ui(user_id):
    """Создает UI для продажи улова."""
    stats = db.get_fishing_stats(user_id)
    inventory = stats.get('inventory', [])
    text = "Вот что ты наловил:\n\n"
    buttons = []

    if not inventory:
        text += "_Ваша сумка пуста\\._"
    else:
        fish_counts = {}
        for fish in inventory:
            name = fish['name']
            if name not in fish_counts:
                fish_counts[name] = {'count': 0, 'total_weight': 0.0}
            fish_counts[name]['count'] += 1
            fish_counts[name]['total_weight'] += fish['weight']
        
        for name, data in fish_counts.items():
            # ИСПРАВЛЕНИЕ: Экранируем вес, который является float
            escaped_weight = escape_markdown(f"{data['total_weight']:.2f}")
            text += f"\\- *{escape_markdown(name)}* x{data['count']} \\(общий вес: {escaped_weight} кг\\)\n"
        
        buttons.append([{'text': '💰 Продать всё', 'callback_data': 'sell_all_catch'}])

    buttons.append([{'text': '⬅️ Назад к Криллсону', 'callback_data': 'krillson_shop'}])
    return {'text': text, 'buttons': buttons}

def create_fishing_perks_ui(user_id):
    """Создает UI для вложения очков перков рыбалки."""
    from game_content import FISHING_STAT_PERKS
    from perk_manager import get_player_perks
    
    fishing_stats = db.get_fishing_stats(user_id)
    player_perks = get_player_perks(user_id) # Получаем общие перки
    
    points = fishing_stats.get('unspent_perk_points', 0)
    
    text = (f"💪 *Улучшения за Уровень Рыбалки*\n\n"
            f"Вкладывайте очки, полученные за повышение уровня, в постоянные бонусы для ваших забегов\\.\n\n"
            f"Доступно очков: *{points}*\n\n"
            # ИСПРАВЛЕНИЕ БЫЛО ЗДЕСЬ: \- заменено на \\-
            "\\-\\-\\- *Текущие бонусы от рыбалки* \\-\\-\\-\n")

    # Отображаем только те бонусы, которые можно получить от рыбалки
    perk_lines = []
    for perk_id, perk_data in FISHING_STAT_PERKS.items():
        stat_key = perk_data['stat'].replace('perm_', '').replace('_bonus', '')
        # Переводим системные ключи в отображаемые
        display_key_map = {'health': 'max_health', 'es': 'max_energy_shield'}
        lookup_key = display_key_map.get(stat_key, stat_key)
        
        value = player_perks.get(lookup_key, 0)
        if value > 0:
             display_name = STAT_DISPLAY_MAP.get(lookup_key, stat_key)
             suffix = '%' if lookup_key not in ['attack', 'max_health', 'max_energy_shield'] else ''
             perk_lines.append(f"{display_name}: `+{value}{suffix}`")
    
    if not perk_lines:
        text += "_Бонусы еще не вложены_\\.\n"
    else:
        text += "\n".join(perk_lines) + "\n"

    text += "\n\\-\\-\\- *Доступные улучшения* \\-\\-\\"
    
    buttons = []
    for perk_id, perk_data in FISHING_STAT_PERKS.items():
        if points >= perk_data['cost']:
             buttons.append([
                {'text': f"{perk_data['name']} ({perk_data['cost']} очко)", 'callback_data': f'spend_fishing_perk:{perk_id}'}
             ])
    buttons.append([{'text': f"🔄 Сбросить улучшения ({fishing_manager.FISHING_PERK_RESET_COST} 🟢)", 'callback_data': 'reset_fishing_perks_confirm'}])         
    buttons.append([{'text': '⬅️ Назад к Криллсону', 'callback_data': 'krillson_shop'}])
    return {'text': text, 'buttons': buttons}

def create_bait_shop_ui(user_id):
    """Создает UI магазина наживок с описаниями."""
    from game_content import FISHING_BAITS
    stats = db.get_fishing_stats(user_id)
    active_baits = stats.get('active_baits', {})

    active_baits_text = "*Активные наживки:*\n"
    if not active_baits:
        active_baits_text += "_Нет активных наживок_\\.\n"
    else:
        for bait_id, data in active_baits.items():
            bait_name = FISHING_BAITS[bait_id]['name']
            active_baits_text += f" • *{escape_markdown(bait_name)}* \\- осталось: `{data['casts']}` забросов\n"

    # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    # Мы будем строить текст и кнопки одновременно в цикле

    text = (f"Здесь можно купить наживку для улучшения улова\\.\n\n"
            f"Ваш баланс: `{stats.get('chaos_orbs', 0)}` 🟢\n\n"
            f"{active_baits_text}\n"
            "\\-\\-\\- *Ассортимент* \\-\\-\\-")

    buttons = []
    for bait_id, bait_data in FISHING_BAITS.items():
        # Добавляем подробное описание для каждого товара в основной текст
        text += (
            f"\n\n*{escape_markdown(bait_data['name'])}*\n"
            f"_{escape_markdown(bait_data['effect_desc'])}_\n"
            f"Действует на: `{bait_data['casts']}` забросов"
        )
        # Кнопка покупки остается такой же
        buttons.append([
            {'text': f"Купить {bait_data['name']} ({bait_data['cost']} 🟢)", 'callback_data': f'buy_bait:{bait_id}'}
        ])
    
    buttons.append([{'text': '⬅️ Назад к Криллсону', 'callback_data': 'krillson_shop'}])
    
    return {'text': text, 'buttons': buttons}


def create_lake_ui(user_id, last_action_message=None):
    """Создает UI для локации 'Озеро' с возможностью показать сообщение о последнем действии."""
    # Импортируем контент прямо здесь, чтобы функция была самодостаточной
    from game_content import FISHING_XP_PER_LEVEL, FISHING_BAITS
    
    stats = db.get_fishing_stats(user_id)
    level = stats['level']
    xp = stats['xp']
    
    max_level = len(FISHING_XP_PER_LEVEL) - 1
    xp_needed = FISHING_XP_PER_LEVEL[level] if level < max_level else 'МАКС'
    
    active_rod = fishing_manager.get_player_active_rod(stats)
    rod_name = active_rod['name'] if active_rod else "Нет удочки"

    # --- НАЧАЛО ИЗМЕНЕНИЙ: Формируем блок с активными наживками ---
    active_baits = stats.get('active_baits', {})
    active_baits_text = "\n*Активные наживки:*\n"
    if not active_baits:
        active_baits_text += "_Нет активных наживок_\\.\n"
    else:
        for bait_id, data in active_baits.items():
            bait_name = FISHING_BAITS[bait_id]['name']
            casts_left = data['casts']
            active_baits_text += f" • *{escape_markdown(bait_name)}* \\- осталось: `{casts_left}` забросов\n"
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    action_text = ""
    if last_action_message:
        action_text = f"{last_action_message}\n\n"

    # --- НАЧАЛО ИЗМЕНЕНИЙ: Добавляем блок с наживками в основной текст ---
    base_text = (
        f"🏞️ *Озеро*\n\n"
        f"Тихая гладь воды манит своей загадочностью\n\n"
        f"Уровень рыбалки: *{level}*\n"
        f"Опыт: `{xp} / {xp_needed}`\n"
        f"Активная удочка: *{escape_markdown(rod_name)}*\n"
        f"{active_baits_text}"  # <-- Вот здесь мы вставили новый блок
    )
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    
    text = action_text + base_text

    buttons = [
        [{'text': "🎣 Рыбачить", 'callback_data': 'start_fishing'}],
        [{'text': "⬅️ Назад", 'callback_data': 'menu_fishing'}],
    ]
    return {'text': text, 'buttons': buttons}



def create_world_boss_main_ui(user_id):
    """Создает UI для главного экрана Мирового Босса."""
    status = wbm.get_boss_status(user_id)
    boss = status['boss']
    player = status['player']
    
    if not boss:
        return {'text': 'Не удалось загрузить информацию о боссе\\.', 'buttons': [[{'text': '⬅️ Назад', 'callback_data': 'menu_events'}]]}

    text = ""
    buttons = []
    
    # --- Сценарий 1: Босс Активен ---
    if boss['is_active']:
        text += f"👹 *{escape_markdown(boss['name'])}* 👹\n\n"
        hp_bar = generate_hp_display(boss['current_hp'], boss['stats']['max_health'])
        text += f"Здоровье: {hp_bar}\n"
        
        time_left = boss['end_time'] - int(time.time())
        hours, rem = divmod(time_left, 3600)
        minutes, _ = divmod(rem, 60)
        text += f"Событие закончится через: *{int(hours)} ч {int(minutes)} мин*\n\n"

        if player and player['damage_dealt'] > 0:
            text += f"Ваш вклад \\(урон\\): *{player['damage_dealt']}*\n"
        
        if status['cooldown_left'] > 0:
            cd_hours, cd_rem = divmod(status['cooldown_left'], 3600)
            cd_minutes, _ = divmod(cd_rem, 60)
            text += f"Вы ранены\\. Следующая атака возможна через: *{int(cd_hours)} ч {int(cd_minutes)} мин*"
            buttons.append([{'text': '🔄 Обновить', 'callback_data': 'menu_world_boss'}])
        else:
            buttons.append([{'text': '⚔️ Атаковать Босса', 'callback_data': 'wb_attack'}])
    
    # --- Сценарий 2: Босс Побежден или Время вышло ---
    else:
        if boss['is_defeated']:
            text += f"👑 *{escape_markdown(boss['name'])} ПОБЕЖДЕН\\!* 👑\n\n"
        else:
            text += f"⌛️ *Событие завершено\\!* ⌛️\n\n"
        text += "Общими усилиями вы одолели зло\\! Вот список самых отважных воинов:\n\n"
        
        # Отображение лидерборда
        leaderboard = status['leaderboard']
        if not leaderboard:
            text += "_Никто не нанес урона\\._\n"
        else:
            for i, (p_id, name, dmg) in enumerate(leaderboard[:10]):
                rank_icon = {1: '🥇', 2: '🥈', 3: '🥉'}.get(i + 1, f'*{i + 1}*\\.')
                text += f"{rank_icon} {escape_markdown(name)} \\- урон: *{dmg}*\n"

        # Кнопка награды
        if player and player['damage_dealt'] > 0 and not player['reward_claimed']:
            buttons.append([{'text': '💎 Забрать Награду', 'callback_data': 'wb_claim_reward'}])
        elif player and player['reward_claimed']:
            text += "\n_Вы уже получили свою награду\\._\n"
            
        # Таймер до нового босса
        next_spawn_time_ts = wbm.get_next_spawn_timestamp() # Используем новую функцию
        time_to_spawn = next_spawn_time_ts - time.time()
        
        if time_to_spawn > 0:
            hours, rem = divmod(time_to_spawn, 3600)
            minutes, _ = divmod(rem, 60)
            text += f"\nНовый босс появится через: *{int(hours)} ч {int(minutes)} мин*"

    buttons.append([{'text': '⬅️ Назад в Ивенты', 'callback_data': 'menu_events'}])
    return {'text': text, 'buttons': buttons}

def create_shard_exchange_ui(user_id):
    """Создает UI для обмена Divine Shards."""
    stats = db.get_fishing_stats(user_id)
    shard_balance = stats.get('divine_shards', 0)
    
    text = (
        "✨ *Обмен Осколков Божественности*\n\n"
        "Здесь ты можешь обменять накопленные осколки на цельный Divine Orb\\.\n\n"
        f"Курс обмена: *10* Осколков ➡️ *1* 💎 Divine Orb\n\n"
        f"У вас в наличии: *{shard_balance}* Осколков"
    )
    
    buttons = []
    if shard_balance >= 10:
        buttons.append([{'text': "Обменять 10 Осколков", 'callback_data': 'exchange_shards_confirm'}])
    
    buttons.append([{'text': '⬅️ Назад к Криллсону', 'callback_data': 'krillson_shop'}])
    
    return {'text': text, 'buttons': buttons}

# --- Harvest UI Components ---

def create_harvest_main_ui(user_id):
    """Создает главный UI Харвеста."""
    from harvest_manager import get_harvest_level_info
    stats = db.get_harvest_stats(user_id)
    level, xp, xp_needed = get_harvest_level_info(stats['xp'])
    
    text = (
       "🌿 *Священная Роща \\(Харвест\\)*\n\n"
        "Здесь воздух пропитан магией жизни\\. Вы можете выращивать семена, чтобы получить ценные ресурсы\\.\n\n"
        f"Уровень: *{level}*\n"
        f"Опыт: `{xp} / {xp_needed}`\n"
        f"Жизненная Сила: `{stats.get('lifeforce', 0)}` 🟢\n"
        f"Кристаллическая Сила: `{stats.get('crystalline_lifeforce', 0)}` 💎"
    )
    buttons = [
        [{'text': "🌱 Грядки", 'callback_data': 'harvest_beds'}],
        [{'text': "👩‍🌾 Ошаби", 'callback_data': 'harvest_oshabi'}],
        [{'text': "❓ Помощь", 'callback_data': 'harvest_help'}],
        [{'text': "⬅️ В главное меню", 'callback_data': 'back_to_main_menu'}]
    ]
    return {'text': text, 'buttons': buttons}

def create_harvest_help_ui():
    """UI с описанием механик Харвеста."""
    text = (
        "❓ *Помощь по Харвесту*\n\n"
        "*1\\. Семена*\n"
        "Семена можно получить с небольшим шансом после победы над любым монстром в PVE или PVP забеге\\. Чем выше ваш уровень Харвеста, тем более высокого тира семена могут вам выпасть\\.\n\n"
        "*2\\. Выращивание*\n"
        "Посадите семена на свободной грядке\\. Семена 1\\-го тира не требуют ничего, но для посадки семян 2\\-го тира и выше вам понадобится *удобрение* соответствующего тира, которое можно купить у Ошаби\\. Каждое семя имеет свое время роста\\. Вы можете ускорить его, купив улучшения в Жизненном Алтаре\\.\n\n"
        "*3\\. Урожай и Валюта*\n"
        "Когда растение созреет, соберите его\\. Вы получите растение, которое можно обменять у Ошаби на валюту:\n"
        # ИСПРАВЛЕНИЕ: Экранированы скобки
        "• *Жизненная Сила* \\(🟢\\): Основная валюта\\. Получается за обмен растений 1\\-4 тиров\\. Тратится на удобрения и улучшения грядок\\.\n"
        "• *Кристаллическая Сила* \\(💎\\): Редкая валюта\\. Получается за обмен растений 5\\-го \\(высшего\\) тира\\. Тратится на самые мощные функции в Жизненном Алтаре: казино и создание собственных предметов\\.\n\n"
        "*4\\. Создание Предметов*\n"
        "Это самая мощная функция Харвеста\\. Она позволяет вам создать полностью кастомный предмет, выбрав его редкость, слот и распределив очки характеристик\\. После создания ваш предмет будет добавлен в общую базу данных и сможет выпасть *любому игроку* в любом забеге, навсегда оставив ваш след в мире игры\\."
    )
    buttons = [[{'text': "⬅️ Назад", 'callback_data': 'menu_harvest'}]]
    return {'text': text, 'buttons': buttons}

def create_oshabi_shop_ui(user_id):
    """UI для меню Ошаби."""
    stats = db.get_harvest_stats(user_id)
    text = (
        "👩‍🌾 *Ошаби, Хранительница Рощи*\n\n"
        "«Чувствуешь, как жизнь пульсирует в этом месте? Что тебе нужно, дитя Рэкласта?»\n\n"
        f"Жизненная Сила: `{stats.get('lifeforce', 0)}` 🟢\n"
        f"Кристаллическая Сила: `{stats.get('crystalline_lifeforce', 0)}` 💎"
    )
    buttons = [
        [{'text': "Купить удобрения", 'callback_data': 'harvest_buy_fertilizer_ui'}],
        [{'text': "Обмен растений", 'callback_data': 'harvest_exchange_plants_ui'}],
        [{'text': "🔮 Жизненный Алтарь", 'callback_data': 'harvest_altar_ui'}],
        [{'text': "⬅️ Назад", 'callback_data': 'menu_harvest'}]
    ]
    return {'text': text, 'buttons': buttons}

def create_beds_ui(user_id):
    """UI для отображения грядок с улучшенным форматированием."""
    stats = db.get_harvest_stats(user_id)
    level = stats['level']
    
    unlocked_beds = 2
    if level >= 10: unlocked_beds = 3 
    if level >= 20: unlocked_beds = 4
    if level >= 30: unlocked_beds = 5
    if level >= 50: unlocked_beds = 6

    text = "🌱 *Ваши грядки*\n"
    buttons = []
    
    for i in range(6):
        text += f"\n\n*Грядка {i+1}*"
        
        if i < unlocked_beds:
            bed = stats['beds'][i]
            if bed is None:
                text += "\nСтатус: 🟫 Свободна\n_Готова к посадке семян_"
                buttons.append([{'text': f"Посадить на грядку {i+1}", 'callback_data': f'harvest_plant_ui:{i}'}])
            else:
                time_left = (bed['plant_time'] + bed['growth_duration']) - int(time.time())
                if time_left > 0:
                    hours, rem = divmod(time_left, 3600)
                    minutes, _ = divmod(rem, 60)
                    text += (f"\nСтатус: ⏳ Растет\n"
                             f"Растение: *{escape_markdown(HARVEST_SEEDS[bed['seed_id']]['name'])}*\n"
                             f"Готовность через: *{int(hours)}ч {int(minutes)}м*")
                else:
                    plant_name = HARVEST_PLANTS[HARVEST_SEEDS[bed['seed_id']]['produces']]['name']
                    text += (f"\nСтатус: ✨ Урожай созрел\\!\n"
                             f"Растение: *{escape_markdown(plant_name)}*")
                    buttons.append([{'text': f"Собрать урожай с грядки {i+1}", 'callback_data': f'harvest_collect:{i}'}])
        else:
            unlock_req = {2: 10, 3: 20, 4: 30, 5: 50}.get(i)
            text += (f"\nСтатус: 🔒 Закрыто\n"
                     f"_Требуется {unlock_req} уровень Харвеста_")

    buttons.append([{'text': "⬅️ Назад", 'callback_data': 'menu_harvest'}])
    return {'text': text, 'buttons': buttons}

def create_seed_planting_ui(user_id, bed_index):
    """UI для выбора семени для посадки."""
    stats = db.get_harvest_stats(user_id)
    text = f"Выберите семя для посадки на грядку {bed_index + 1}:\n"
    buttons = []
    
    has_seeds = False
    for seed_id, count in stats['seeds'].items():
        if count > 0:
            has_seeds = True
            seed_info = HARVEST_SEEDS[seed_id]
            buttons.append([{'text': f"{seed_info['name']} (x{count})", 'callback_data': f'harvest_plant_confirm:{bed_index}:{seed_id}'}])
            
    if not has_seeds:
        text += "\n_У вас нет семян для посадки\\._"
        
    buttons.append([{'text': "⬅️ Назад к грядкам", 'callback_data': 'harvest_beds'}])
    return {'text': text, 'buttons': buttons}

def create_fertilizer_shop_ui(user_id):
    """UI для покупки удобрений."""
    stats = db.get_harvest_stats(user_id)
    
    # --- Блок отображения инвентаря ---
    inventory_text = "*Ваши удобрения:*\n"
    owned_fertilizers = {fid: count for fid, count in stats.get('fertilizers', {}).items() if count > 0}
    if not owned_fertilizers:
        inventory_text += "_У вас нет удобрений\\._\n\n"
    else:
        for fert_id, count in owned_fertilizers.items():
            fert_name = HARVEST_FERTILIZERS[fert_id]['name']
            inventory_text += f"• {escape_markdown(fert_name)}: `{count}` шт\\.\n"
        inventory_text += "\n"

    # --- Основной текст магазина ---
    text = (
        f"Выберите удобрение для покупки\\. Они нужны для посадки семян Т2 и выше\\.\n\n"
        f"Ваша Жизненная Сила: `{stats['lifeforce']}` 🟢\n\n"
        f"{inventory_text}"
    )
    
    buttons = []
    for fert_id, fert_info in HARVEST_FERTILIZERS.items():
        cost_x1 = fert_info['cost']
        cost_x5 = cost_x1 * 5
        
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Сокращаем название для компактности кнопок (например, "Удобрение Т2" -> "Т2")
        short_name = fert_info['name'].replace('Удобрение ', '')
        
        # Создаем ряд из двух кнопок для каждого удобрения с понятным названием
        buttons.append([
            InlineKeyboardButton(f"Купить {short_name} x1 ({cost_x1} 🟢)", callback_data=f'harvest_buy_fertilizer:{fert_id}:1'),
            InlineKeyboardButton(f"Купить {short_name} x5 ({cost_x5} 🟢)", callback_data=f'harvest_buy_fertilizer:{fert_id}:5')
        ])
        
    buttons.append([InlineKeyboardButton("⬅️ Назад к Ошаби", callback_data='harvest_oshabi')])
    return {'text': text, 'buttons': buttons}

def create_plant_exchange_ui(user_id):
    """UI для обмена растений."""
    stats = db.get_harvest_stats(user_id)
    text = "Ваши собранные растения:\n\n"
    buttons = []
    
    has_plants = False
    for plant_id, count in stats['plants'].items():
        if count > 0:
            has_plants = True
            plant_info = HARVEST_PLANTS[plant_id]
            currency_symbol = "🟢" if plant_info['currency'] == 'lifeforce' else "💎"
            # ИСПРАВЛЕНИЕ: Экранированы скобки
            text += f"• *{escape_markdown(plant_info['name'])}* x{count} \\(обмен на {plant_info['value'] * count} {currency_symbol}\\)\n"
            
    if has_plants:
        buttons.append([{'text': "🔄 Обменять всё", 'callback_data': 'harvest_exchange_all'}])
    else:
        text += "_У вас нет растений для обмена\\._"
        
    buttons.append([{'text': "⬅️ Назад к Ошаби", 'callback_data': 'harvest_oshabi'}])
    return {'text': text, 'buttons': buttons}

def create_lifeforce_altar_ui(user_id):
    """UI для Алтаря Жизни."""
    stats = db.get_harvest_stats(user_id)
    text = (
        "🔮 *Жизненный Алтарь*\n\n"
        "Это место великой силы\\. Здесь можно преобразовывать жизненную энергию в нечто большее\\.\n\n"
        f"Жизненная Сила: `{stats.get('lifeforce', 0)}` 🟢\n"
        f"Кристаллическая Сила: `{stats.get('crystalline_lifeforce', 0)}` 💎"
    )
    buttons = [
        [{'text': "Улучшения грядок", 'callback_data': 'harvest_bed_upgrades_ui'}],
        [{'text': "🎰 Казино Удачи", 'callback_data': 'harvest_casino_ui'}],
        [{'text': "🛠️ Создание Предметов", 'callback_data': 'harvest_craft_rarity'}],
        [{'text': "⬅️ Назад к Ошаби", 'callback_data': 'harvest_oshabi'}]
    ]
    return {'text': text, 'buttons': buttons}

def create_bed_upgrade_ui(user_id):
    """UI для покупки улучшений грядок."""
    stats = db.get_harvest_stats(user_id)
    current_bonus = stats.get('growth_speed_bonus', 0)
    text = f"Текущий бонус к скорости роста: *{int(current_bonus * 100)}%*\n\nВыберите улучшение:\n"
    buttons = []
    for up_id, up_info in HARVEST_BED_UPGRADES.items():
        if current_bonus < up_info['bonus']:
             buttons.append([{'text': f"{up_info['name']} ({up_info['cost']} 🟢)", 'callback_data': f'harvest_buy_upgrade:{up_id}'}])
    if not buttons:
        text += "\n_Вы уже купили все доступные улучшения\\!_"
    buttons.append([{'text': "⬅️ Назад к Алтарю", 'callback_data': 'harvest_altar_ui'}])
    return {'text': text, 'buttons': buttons}

def create_casino_ui(user_id, last_bet_result=None):
    """UI для казино с отображением результата последней ставки."""
    stats = db.get_harvest_stats(user_id)
    player_info = db.get_player_info(user_id)
    
    result_message = ""
    if last_bet_result:
        if last_bet_result['status'] == 'win':
            result_message = (f"🎉 *ПОБЕДА\\!* 🎉\nВы выиграли "
                              f"*{last_bet_result['winnings']}* {last_bet_result['currency_name']}\\!\n\n")
        elif last_bet_result['status'] == 'loss':
            result_message = (f"💀 *Увы, неудача\\!* 💀\nВы проиграли "
                              f"*{last_bet_result['lost_amount']}* {last_bet_result['currency_name']}\\.\n\n")

    text = (
        f"{result_message}"
        "🎰 *Казино Удачи*\n\n"
        "Рискнешь своей удачей, изгнанник? Шанс 50/50 удвоить ставку или потерять всё\\.\n"
        "*Каждая ставка стоит 1 💎 Кристаллическую Силу\\.*\n\n"
        f"Ваш баланс:\n`{player_info.get('divine_orbs', 0)}` 💎 Divine Orb\n`{player_info.get('mirrors', 0)}` 🪞 Mirror\n"
        f"`{stats.get('crystalline_lifeforce', 0)}` 💎 Кристаллическая Сила"
    )
    buttons = [
        [
            {'text': "Ставка 1 💎", 'callback_data': 'harvest_casino_bet:divine_orbs:1'},
            {'text': "Ставка 5 💎", 'callback_data': 'harvest_casino_bet:divine_orbs:5'},
            {'text': "Ставка ВСЁ 💎", 'callback_data': 'harvest_casino_bet:divine_orbs:all'}
        ],
        [
            {'text': "Ставка 1 🪞", 'callback_data': 'harvest_casino_bet:mirrors:1'},
            {'text': "Ставка 5 🪞", 'callback_data': 'harvest_casino_bet:mirrors:5'},
            {'text': "Ставка ВСЁ 🪞", 'callback_data': 'harvest_casino_bet:mirrors:all'}
        ],
        [{'text': "⬅️ Назад к Алтарю", 'callback_data': 'harvest_altar_ui'}]
    ]
    return {'text': text, 'buttons': buttons}

def create_item_crafting_ui(session):
    """Динамический UI для процесса создания предмета (безопасная версия)."""
    rarity_map = {'magic': 'Магический', 'rare': 'Редкий', 'unique': 'Уникальный', 'legendary': 'Легендарный'}
    
    # Используем `моноширинный` шрифт (`) для всех динамических данных.
    # Это предотвращает ошибки парсинга, если в данных есть спецсимволы.
    rarity_text = f"`{rarity_map.get(session['rarity'])}`"
    slot_text = f"`{session['slot'] or 'Не выбран'}`"
    name_text = f"`{escape_markdown(session['name']) if session['name'] else 'Не задано'}`"
    points_text = f"`{session['points']} / {session['max_points']}`"

    text = (
        f"🛠️ *Создание предмета*\n\n"
        f"*Редкость:* {rarity_text}\n"
        f"*Слот:* {slot_text}\n"
        f"*Название:* {name_text}\n\n"
        f"*Осталось очков:* {points_text}\n\n"
        f"*Текущие свойства:*\n"
    )
    
    if not session['stats']:
        text += "_Нет_\n"
    else:
        for stat_id, value in session['stats'].items():
            stat_info = HARVEST_CRAFTING_CONFIG['stat_costs'][stat_id]
            base_name = stat_info['name'].split(' ', 2)[-1] 
            text += f"• \\+`{value}` {base_name}\n"
            
    text += "\n*Добавьте свойства:*"
    
    buttons = []
    row = []
    stat_buttons = HARVEST_CRAFTING_CONFIG['stat_costs']
    for stat_id, stat_info in stat_buttons.items():
        row.append({'text': f"{stat_info['name']} ({stat_info['cost']})", 'callback_data': f'harvest_craft_add_stat:{stat_id}'})
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
        
    buttons.append([
        {'text': "🔄 Сбросить", 'callback_data': 'harvest_craft_reset_stats'},
        {'text': "✅ Готово", 'callback_data': 'harvest_craft_confirm'}
    ])
    buttons.append([{'text': "❌ Отмена", 'callback_data': 'harvest_altar_ui'}])
    
    return {'text': text, 'buttons': buttons}

def create_upgrades_exchange_menu_ui(user_id):
    """Создает меню выбора между прокачкой и обменом."""
    # ИСПРАВЛЕНИЕ: Экранирована точка в конце предложения.
    text = "Выберите, что вы хотите сделать\\."
    buttons = [
        [InlineKeyboardButton("🛠️ Прокачка Персонажа", callback_data='menu_perks')],
        [InlineKeyboardButton("🎴 Обменять Гадальные Карты", callback_data='divination_card_exchange_ui')],
        [InlineKeyboardButton("⬅️ Назад в главное меню", callback_data='back_to_main_menu')]
    ]
    return {'text': text, 'buttons': buttons}

def create_divination_card_ui(user_id):
    """Создает UI для просмотра и обмена гадальных карт."""
    player_cards = db.get_player_cards(user_id)
    # ИСПРАВЛЕНИЕ: Экранирована точка в конце предложения.
    text = "🎴 *Обмен Гадальных Карт*\n\nСоберите полный сет одинаковых карт, чтобы обменять их на ценную награду\\.\n\n"
    buttons = []

    # Сортируем карты по весу, чтобы самые редкие были в конце
    sorted_cards = sorted(DIVINATION_CARDS.items(), key=lambda item: item[1]['weight'], reverse=True)

    for card_id, card_info in sorted_cards:
        current_amount = player_cards.get(card_id, 0)
        required_amount = card_info['stack_size']
        
        # --- НАЧАЛО ИЗМЕНЕНИЙ ---
        reward_text = ""
        reward_type = card_info['reward_type']
        reward_value = card_info['reward_value']
        
        if reward_type == 'divine_shards':
            reward_text = f"{reward_value} Осколков Божественности"
        elif reward_type == 'divine_orbs':
            reward_text = f"{reward_value} 💎 Divine Orbs"
        elif reward_type == 'mirrors':
            reward_text = f"{reward_value} 🪞 Mirror of Kalandra"
        
        text += f"*{escape_markdown(card_info['name'])}* \\({current_amount}/{required_amount}\\) \\- _{escape_markdown(reward_text)}_\n"
        # --- КОНЕЦ ИЗМЕНЕНИЙ ---
        
        if current_amount >= required_amount:
            buttons.append(
                [{'text': f"Обменять сет '{card_info['name']}'", 'callback_data': f'exchange_card_set_{card_id}'}]
            )
            
    if not buttons:
        # ИСПРАВЛЕНИЕ: Экранирована точка в конце предложения.
        text += "\n_У вас пока нет полных сетов для обмена\\._"

    buttons.append([{'text': '⬅️ Назад', 'callback_data': 'menu_upgrades_exchange'}])
    return {'text': text, 'buttons': buttons}


def create_chest_choice_ui():
    """(НОВОЕ) Создает UI для выбора типа сундука."""
    text = (
        "Вы видите два сундука\\. Один выглядит старым и потрепанным, другой \\- "
        "опутан темными цепями и зловеще гудит\\.\n\n"
        "Какой вы решите открыть?"
    )
    buttons = [
        [{'text': "📦 Открыть обычный сундук", 'callback_data': 'chest_choice:plain'}],
        [{'text': "💀 Открыть проклятый сундук (Бой!)", 'callback_data': 'chest_choice:cursed'}],
        [{'text': "Уйти", 'callback_data': 'continue_run'}]
    ]
    return {'text': text, 'buttons': buttons}

def create_sacrifice_ui(health_cost):
    """(НОВОЕ) Создает UI для алтаря жертвоприношения."""
    text = (
        "🩸 Перед вами окровавленный алтарь\\. Древний голос предлагает вам сделку:\n\n"
        "«Пожертвуй частью своей жизненной сути, и я вознагражу тебя силой, "
        "недоступной простым смертным»\\.\n\n"
        f"Вы можете *навсегда* пожертвовать `{health_cost}` максимального здоровья, "
        "чтобы получить взамен *уникальный* или *легендарный* предмет\\."
    )
    buttons = [
        [{'text': f"Пожертвовать {health_cost} ❤️", 'callback_data': 'mystery_sacrifice_confirm'}],
        [{'text': "Отказаться от жертвы", 'callback_data': 'mystery_decline'}]
    ]
    return {'text': text, 'buttons': buttons}

def create_pact_ui(buff, debuff):
    """(НОВОЕ) Создает UI для заключения пакта."""
    text = (
        "😈 Из тени появляется сущность и предлагает сделку:\n\n"
        "«Я дарую тебе силу, но взамен заберу толику твоей удачи»\\.\n\n"
        f"*Вы получите:* {escape_markdown(buff['desc'])}\n"
        f"*Вы потеряете:* {escape_markdown(debuff['desc'])}\n\n"
        "Оба эффекта будут действовать до конца забега\\. Вы согласны?"
    )
    buttons = [
        [{'text': "✅ Принять пакт", 'callback_data': 'mystery_pact_accept'}],
        [{'text': "❌ Отказаться", 'callback_data': 'mystery_pact_decline'}]
    ]
    return {'text': text, 'buttons': buttons}

def create_chest_choice_ui():
    """(НОВОЕ) Создает UI для выбора типа сундука."""
    text = (
        "Вы видите два сундука\\. Один выглядит старым и потрепанным, другой \\- "
        "опутан темными цепями и зловеще гудит\\.\n\n"
        "Какой вы решите открыть?"
    )
    buttons = [
        [{'text': "📦 Открыть обычный сундук", 'callback_data': 'chest_choice:plain'}],
        [{'text': "💀 Открыть проклятый сундук (Бой!)", 'callback_data': 'chest_choice:cursed'}],
        [{'text': "Уйти", 'callback_data': 'continue_run'}]
    ]
    return {'text': text, 'buttons': buttons}

def create_kalandra_touch_ui(character):
    """(НОВОЕ) Создает UI для выбора предмета для трансформации."""
    text = (
        "🪞 Вы находите мерцающую, жидкую поверхность — Прикосновение Каландры\\. "
        "Она предлагает преобразить один из ваших предметов в другой, той же редкости, "
        "но навсегда заберет оригинал\\.\n\n"
        "Выберите предмет для трансформации:"
    )
    buttons = []
    
    equipped_items = {slot: item for slot, item in character['equipment'].items() if item}
    
    if not equipped_items:
        return {'text': "Вы смотрите на поверхность, но вам нечего ей предложить\\.", 'buttons': [[{'text': 'Уйти', 'callback_data': 'continue_run'}]]}

    # --- НАЧАЛО ИЗМЕНЕНИЙ: Добавляем иконки редкости на кнопки ---
    rarity_colors = {'magic': '🟦', 'rare': '🟨', 'unique': '🟧', 'legendary': '🟪'}
    for slot, item in equipped_items.items():
        rarity = item.get('rarity', 'magic')
        color_icon = rarity_colors.get(rarity, '⬜️')
        buttons.append([{'text': f"{color_icon} {item['name']}", 'callback_data': f'mystery_kalandra_touch:{slot}'}])
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
        
    buttons.append([{'text': 'Не рисковать и уйти', 'callback_data': 'mystery_decline'}])
    return {'text': text, 'buttons': buttons}

def create_expedition_ui(user_id):
    """Создает UI для рыболовной экспедиции."""
    from game_content import EXPEDITION_CONFIG 
    stats = db.get_fishing_stats(user_id)
    expedition_end_time = stats.get('expedition_end_time', 0)
    
    buttons = []
    
    if expedition_end_time > time.time():
        # Экспедиция активна
        time_left = expedition_end_time - int(time.time())
        hours, rem = divmod(time_left, 3600)
        minutes, _ = divmod(rem, 60)
        text = (
            "🗺️ *Вы в экспедиции* 🗺️\n\n"
            "Ваш рыбак вернется с богатым уловом\\. Не мешайте ему\\.\n\n"
            f"Осталось времени: *{int(hours)} ч {int(minutes)} мин*"
        )
        buttons.append([{'text': '⬅️ Назад к Криллсону', 'callback_data': 'krillson_shop'}])

    elif expedition_end_time != 0 and expedition_end_time <= time.time():
        # Экспедиция завершена, можно забрать награду
        text = (
            "🎉 *Экспедиция завершена\\!* 🎉\n\n"
            "Ваш рыбак вернулся\\! Нажмите, чтобы забрать свой улов\\."
        )
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---
        buttons.append([{'text': '🏆 Забрать награду', 'callback_data': 'claim_expedition_reward'}])
        buttons.append([{'text': '⬅️ Назад к Криллсону', 'callback_data': 'krillson_shop'}])
        
    else:
        # Экспедиция не начата
        cost = EXPEDITION_CONFIG['cost']
        duration_hours = EXPEDITION_CONFIG['duration_hours']
        
        text = (
            "🗺️ *Рыболовная Экспедиция* 🗺️\n\n"
            "Отправьте своего рыбака в долгую экспедицию, чтобы получить гарантированный, но случайный улов\\. "
            "Вы не сможете рыбачить или начинать новую экспедицию, пока она не завершится\\.\n\n"
            f"Стоимость: *{cost}* 🟢\n"
            f"Длительность: *{int(duration_hours)} часа*"
        )
        buttons.append([{'text': f'Начать экспедицию за {cost} 🟢', 'callback_data': 'start_expedition'}])
        buttons.append([{'text': '⬅️ Назад к Криллсону', 'callback_data': 'krillson_shop'}])
        
    return {'text': text, 'buttons': buttons}

def create_fishing_perk_reset_confirmation_ui():
    """Создает UI для подтверждения сброса перков рыбалки."""
    cost = fishing_manager.FISHING_PERK_RESET_COST
    text = (
        f"⚠️ *Подтверждение Сброса* ⚠️\n\n"
        f"Вы уверены, что хотите сбросить все улучшения, купленные за очки рыбалки, за *{cost}* 🟢 Хаос Орбов?\n\n"
        "Все потраченные очки будут возвращены\\. Это действие необратимо\\."
    )
    buttons = [
        [InlineKeyboardButton("✅ Да, сбросить", callback_data='reset_fishing_perks_do')],
        [InlineKeyboardButton("❌ Нет, отмена", callback_data='fishing_perks_ui')]
    ]
    return {'text': text, 'buttons': buttons}

def create_monthly_rewards_ui(user_id):
    """Создает UI для экрана ежемесячных наград."""
    now = datetime.datetime.now(pytz.utc)
    
    # Расчет времени до конца текущего месяца
    _, last_day = calendar.monthrange(now.year, now.month)
    end_of_month = now.replace(day=last_day, hour=23, minute=59, second=59)
    time_left = end_of_month - now
    
    days = time_left.days
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    text = (
        "🏆 *Ежемесячные Награды Лидербордов* 🏆\n\n"
        "В конце каждого месяца лучшие игроки в каждой категории получают ценные награды\\.\n\n"
        f"До окончания текущего сезона осталось: *{days} дн {hours} ч {minutes} мин*\n\n"
        "✨ *Награды:*\n"
        "🥇 Топ 1: *25* 🪞\n"
        "🥈 Топ 2: *15* 🪞\n"
        "🥉 Топ 3: *10* 🪞\n"
        "🏅 Топ 4\\-10: *5* 🪞\n"
    )
    
    buttons = []
    # Кнопка появляется, если сейчас начало нового месяца (например, первые 5 дней)
    if now.day <= 5:
        month_to_claim_str = leaderboard_manager.get_reward_period()
        text += f"\n*Доступны награды за {month_to_claim_str} месяц*"
        buttons.append([InlineKeyboardButton("💎 Забрать награды за прошлый месяц", callback_data='claim_monthly_rewards')])

    buttons.append([InlineKeyboardButton("⬅️ Назад к таблицам", callback_data='menu_leaderboard')])
    
    return {'text': text, 'buttons': buttons}

def create_referral_program_ui(user_id, bot_username):
    """Создает UI для реферальной программы."""
    from referral_manager import TARGET_LEVEL, REWARD_AMOUNT
    
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = (
        f"🤝 *Реферальная программа*\n\n"
        f"Пригласите друга в игру, и как только он достигнет *{TARGET_LEVEL}* уровня, вы получите награду: *{REWARD_AMOUNT}* 💎 Divine Orbs\n\n"
        f"🔗 *Ваша ссылка для приглашения:*\n`{escape_markdown(referral_link)}`\n\n"
        f"\\-\\-\\- *Ваши приглашенные* \\-\\-\\-\n"
    )
    
    all_referrals = db.get_all_referrals_with_levels(user_id)
    
    if not all_referrals:
        text += "_У вас пока нет приглашенных игроков_"
    else:
        for _, username, level in all_referrals:
            status_icon = "✅" if level >= TARGET_LEVEL else "⏳"
            text += f"• {escape_markdown(username)} \\- Уровень: *{level}/{TARGET_LEVEL}* {status_icon}\n"
            
    buttons = []
    unclaimed_rewards = db.get_unclaimed_referrals(user_id, TARGET_LEVEL)
    if unclaimed_rewards:
        count = len(unclaimed_rewards)
        buttons.append([InlineKeyboardButton(f"🎁 Забрать награду \\({count}\\)", callback_data='claim_referral_reward_all')])
        
    buttons.append([InlineKeyboardButton("⬅️ Назад в главное меню", callback_data='back_to_main_menu')])
    
    return {'text': text, 'buttons': buttons}

def create_ascendancy_choice_ui(run_state):
    """Создает UI для выбора пассивного умения Восхождения после победы над боссом."""
    char = run_state['character']
    class_id = char.get('class_id')
    points = char.get('ascendancy_points', 0)
    chosen_passives = char.get('chosen_ascendancy_passives', [])
    
    text = (
        f"✨ *Вы чувствуете прилив сил после победы над боссом\\!* ✨\n\n"
        f"Вы получили *1* очко Восхождения\\. Выберите новое умение, чтобы усилить себя до конца этого забега\\.\n\n"
        f"Очков для распределения: *{points}*\n"
    )
    
    buttons = []
    
    if not class_id or class_id not in ASCENDANCY_PASSIVES:
        text += "\n\n_Ошибка: не найдены умения для вашего класса\\._"
        buttons.append([{'text': '▶️ Пропустить и перейти к добыче', 'callback_data': 'ascendancy_skip'}])
    else:
        available_passives = {
            pid: pdata for pid, pdata in ASCENDANCY_PASSIVES[class_id].items()
            if pid not in chosen_passives
        }
        
        if not available_passives:
            text += "\n\n_Вы уже изучили все доступные умения\\._"
            buttons.append([{'text': '▶️ К добыче', 'callback_data': 'ascendancy_skip'}])
        else:
            # --- НАЧАЛО ИЗМЕНЕНИЙ ---
            text += "\n\\-\\-\\- *Доступные умения* \\-\\-\\-\n"
            
            for passive_id, passive_data in available_passives.items():
                # Добавляем описание в основной текст
                text += f"\n*{escape_markdown(passive_data['name'])}*\n_{escape_markdown(passive_data['desc'])}_\n"
                
                # На кнопку выносим только название
                button_text = f"Выбрать «{passive_data['name']}»"
                buttons.append([{'text': button_text, 'callback_data': f'ascendancy_choice:{passive_id}'}])
            # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    return {'text': text, 'buttons': buttons}

def create_rhoa_race_ui(user_id, context): # <--- Добавляем context
    """Создает главный UI для ивента 'Гонка Роа'."""
    status = rhoa_race_manager.get_race_status(user_id)
    player_info = db.get_player_info(user_id)
    
    last_finished_race_id, last_race_bets = db.get_last_race_results_for_player(user_id)
    
    # --- ИЗМЕНЕНИЕ: Проверяем флаг в context.user_data ---
    viewed_race_id = context.user_data.get('viewed_race_id', -1)

    if last_finished_race_id and last_finished_race_id > viewed_race_id:
        results_text = rhoa_race_manager.get_last_race_results_text(last_finished_race_id, last_race_bets)
        return {
            'text': results_text,
            'buttons': [[{'text': '✅ Понятно, к новому забегу', 'callback_data': 'rhoa_race_show_new'}]] # <--- Новая кнопка
        }
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    # Если результаты показывать не нужно, показываем обычное лобби
    text = f"🏁 *Гонка Роа \\(Забег \\#{status['race_id']}\\)*\n\n"
    text += "Делайте ставки на одного из шести могучих Роа\\! Как только 4 игрока сделают ставки, начнется забег\\. Победитель получает свою ставку в тройном размере\\!\n\n"
    text += f"Ваш баланс:\n`{player_info.get('divine_orbs', 0)}` 💎 Divine Orbs\n`{player_info.get('mirrors', 0)}` 🪞 Mirrors\n\n"
    
    text += f"*Участники в текущем забеге: {len(status['current_bets'])}/{rhoa_race_manager.RACE_CAPACITY}*\n"
    if status['current_bets']:
        for _, username, rhoa_id, _, _ in status['current_bets']:
            text += f"\\- `{escape_markdown(username)}` поставил на Роа \\#{rhoa_id}\n"
            
    buttons = []
    if status['player_in_current_race']:
        text += "\n_Вы уже сделали ставку\\. Ожидаем других участников\\._"
        buttons.append([{'text': '🔄 Обновить', 'callback_data': 'menu_rhoa_race'}])
    elif status['is_full']:
        text += "\n_Забег заполнен и вот-вот начнется\\! Нажмите 'Обновить'\\._"
        buttons.append([{'text': '🔄 Обновить', 'callback_data': 'menu_rhoa_race'}])
    else:
        text += "\n*Выберите Роа для ставки:*\n"
        for rhoa_id, rhoa_name in RHOA_NAMES.items():
            buttons.append([{'text': f"#{rhoa_id} - {rhoa_name}", 'callback_data': f'rhoa_race_bet_ui:{rhoa_id}'}])

    buttons.append([{'text': '⬅️ Назад в Ивенты', 'callback_data': 'menu_events'}])
    return {'text': text, 'buttons': buttons}


def create_rhoa_bet_ui(user_id, rhoa_id):
    """Создает UI для выбора суммы ставки."""
    player_info = db.get_player_info(user_id)
    rhoa_name = RHOA_NAMES.get(rhoa_id, "Неизвестный Роа")
    
    text = (
        f"Вы выбрали: *{escape_markdown(rhoa_name)}* \\(Роа \\#{rhoa_id}\\)\n\n"
        "Выберите валюту и сумму ставки:\n\n"
        f"Ваш баланс:\n`{player_info.get('divine_orbs', 0)}` 💎 Divine Orbs\n`{player_info.get('mirrors', 0)}` 🪞 Mirrors"
    )
    
    buttons = [
        [
            {'text': "1 💎", 'callback_data': f'rhoa_race_place_bet:{rhoa_id}:1:divine_orbs'},
            {'text': "5 💎", 'callback_data': f'rhoa_race_place_bet:{rhoa_id}:5:divine_orbs'},
            {'text': "10 💎", 'callback_data': f'rhoa_race_place_bet:{rhoa_id}:10:divine_orbs'}
        ],
        [
            {'text': "1 🪞", 'callback_data': f'rhoa_race_place_bet:{rhoa_id}:1:mirrors'},
            {'text': "5 🪞", 'callback_data': f'rhoa_race_place_bet:{rhoa_id}:5:mirrors'},
            {'text': "10 🪞", 'callback_data': f'rhoa_race_place_bet:{rhoa_id}:10:mirrors'}
        ],
        [{'text': '⬅️ Назад к выбору Роа', 'callback_data': 'menu_rhoa_race'}]
    ]
    return {'text': text, 'buttons': buttons}

def create_post_boss_endless_ui(run_state):
    """(НОВОЕ) Создает UI после победы над боссом в Бесконечном режиме (этаж 4+)."""
    char = run_state['character']
    class_id = char.get('class_id')
    
    # Считаем, сколько всего пассивок доступно для класса
    total_passives = len(ASCENDANCY_PASSIVES.get(class_id, {}))
    chosen_passives_count = len(char.get('chosen_ascendancy_passives', []))
    
    # Получаем текст о победе, который мы сохранили ранее
    victory_text = char.get('pending_victory_message', "Вы победили босса\\!")
    gold = char.get('currency', {}).get('gold', 0)
    
    text = (
        f"{victory_text}\n\n"
        "Вы находитесь в затишье после битвы\\. Связь с Древом Возвышения ослабла, но вы можете "
        "усилить ее с помощью накопленных сокровищ\\.\n\n"
        f"Ваше золото: `{gold}` 🪙"
    )
    
    buttons = []
    
    # Показываем кнопку, только если есть что изучать
    if chosen_passives_count < total_passives:
        buttons.append([{'text': 'Купить Возвышение (1000 🪙)', 'callback_data': 'buy_ascendancy'}])
        
    buttons.append([{'text': '▶️ К добыче', 'callback_data': 'show_post_boss_loot'}])
    
    return {'text': text, 'buttons': buttons}

# --- НАЧАЛО ИЗМЕНЕНИЙ: Новый UI и правки старых ---

def create_crucible_post_boss_ui(run_state):
    """Создает стартовый UI для Кузницы Горнила после победы над боссом."""
    char = run_state['character']
    victory_text = char.get('pending_victory_message', "Вы победили босса\\!")
    gold = char.get('currency', {}).get('gold', 0)

    text = (
        f"{victory_text}\n\n"
        "Вместо обычной награды, перед вами открывается проход в *Кузницу Горнила* — место, где можно выковать судьбу\\.\n\n"
        f"За *{em.CRUCIBLE_FORGE_COST}* 🪙 золота вы можете создать любой предмет на свой выбор\\. "
        "Или вы можете пропустить эту возможность и забрать обычную добычу с босса\\.\n\n"
        f"Ваше золото: `{gold}` 🪙"
    )
    buttons = [
        [{'text': '🔥 Войти в Кузницу', 'callback_data': 'crucible_start'}],
        [{'text': '▶️ Пропустить (к добыче)', 'callback_data': 'show_post_boss_loot'}]
    ]
    return {'text': text, 'buttons': buttons}

def create_crucible_floor_choice_ui():
    """Шаг 1: Выбор этажа для пула предметов."""
    text = (
        f"🔥 *Кузница Горнила*\n\n"
        f"За *{escape_markdown(str(em.CRUCIBLE_FORGE_COST))}* 🪙 вы можете выковать любой существующий предмет\\.\n\n"
        "Сначала выберите, из пула предметов какого этажа вы хотите создать артефакт:"
    )
    buttons = [
        [{'text': "Этаж 1", 'callback_data': 'crucible_select_floor:1'}, {'text': "Этаж 2", 'callback_data': 'crucible_select_floor:2'}],
        [{'text': "Этаж 3", 'callback_data': 'crucible_select_floor:3'}, {'text': "Этаж 4", 'callback_data': 'crucible_select_floor:4'}],
        # Кнопка "Отмена" теперь ведет к обычному экрану добычи
        [{'text': "❌ Отмена (к добыче)", 'callback_data': 'show_post_boss_loot'}]
    ]
    return {'text': text, 'buttons': buttons}

def create_crucible_type_choice_ui(context):
    """Шаг 2: Выбор типа предмета."""
    session = context.user_data.get('crucible_session', {})
    text = f"Вы выбрали этаж *{session.get('floor')}*\\. Теперь выберите тип предмета:"
    
    type_map = {
        "Оружие": ['weapon1', 'weapon2'], "Шлем": ['helmet'], "Броня": ['body_armour'],
        "Перчатки": ['gloves'], "Ботинки": ['boots'], "Кольцо": ['ring'],
        "Амулет": ['amulet'], "Пояс": ['belt']
    }
    
    buttons = []
    row = []
    for type_name in type_map.keys():
        row.append({'text': type_name, 'callback_data': f'crucible_select_type:{type_name}'})
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
        
    # Кнопка "Назад" теперь ведет на стартовый экран Кузницы
    buttons.append([{'text': "⬅️ Назад к выбору этажа", 'callback_data': 'crucible_start'}])
    return {'text': text, 'buttons': buttons}

def create_crucible_rarity_choice_ui(context):
    """Шаг 3: Выбор редкости предмета."""
    session = context.user_data.get('crucible_session', {})
    text = f"Этаж: *{session.get('floor')}*, Тип: *{escape_markdown(session.get('type'))}*\\.\n\nТеперь выберите редкость:"
    buttons = [
        [{'text': "🟦 Магический", 'callback_data': 'crucible_select_rarity:magic'}],
        [{'text': "🟨 Редкий", 'callback_data': 'crucible_select_rarity:rare'}],
        [{'text': "🟧 Уникальный", 'callback_data': 'crucible_select_rarity:unique'}],
        [{'text': "🟪 Легендарный", 'callback_data': 'crucible_select_rarity:legendary'}],
        [{'text': "⬅️ Назад к выбору типа", 'callback_data': f"crucible_select_floor:{session.get('floor')}"}]
    ]
    return {'text': text, 'buttons': buttons}

def _get_crucible_item_pool(context):
    """Вспомогательная функция для получения отфильтрованного пула предметов."""
    session = context.user_data.get('crucible_session', {})
    floor = session.get('floor')
    item_type_name = session.get('type')
    rarity = session.get('rarity')

    if not all([floor, item_type_name, rarity]):
        return []

    # Получаем стандартные и кастомные предметы
    floor_items = CONTENT[f"floor_{floor}"]['items']
    all_custom_items = db.get_all_custom_items()
    floor_custom_items = [item for item in all_custom_items if item.get('floor') == floor]

    # Собираем общий пул для нужной редкости
    combined_pool = floor_items.get(rarity, []) + [item for item in floor_custom_items if item.get('rarity') == rarity]

    # Фильтруем по типу
    type_map = {
        "Оружие": ['weapon1', 'weapon2'], "Шлем": ['helmet'], "Броня": ['body_armour'],
        "Перчатки": ['gloves'], "Ботинки": ['boots'], "Кольцо": ['ring', 'ring1', 'ring2'],
        "Амулет": ['amulet'], "Пояс": ['belt']
    }
    target_slots = type_map.get(item_type_name, [])
    
    filtered_items = [item for item in combined_pool if item.get('slot') in target_slots]
    
    # Убираем дубликаты по имени
    unique_items = []
    seen_names = set()
    for item in filtered_items:
        if item['name'] not in seen_names:
            unique_items.append(item)
            seen_names.add(item['name'])
            
    return sorted(unique_items, key=lambda x: x['name'])

def create_crucible_item_choice_ui(context):
    """Шаг 4: Финальный выбор предмета из списка."""
    session = context.user_data.get('crucible_session', {})
    item_pool = _get_crucible_item_pool(context)
    
    text = f"Этаж: *{session.get('floor')}*, Тип: *{escape_markdown(session.get('type'))}*, Редкость: *{escape_markdown(session.get('rarity'))}*\\.\n\nВыберите предмет для создания:"
    buttons = []

    if not item_pool:
        text += "\n\n_В этой категории нет доступных предметов\\._"
    else:
        for i, item in enumerate(item_pool):
            buttons.append([{'text': item['name'], 'callback_data': f'crucible_select_item:{i}'}])

    buttons.append([{'text': "⬅️ Назад к выбору редкости", 'callback_data': f"crucible_select_type:{session.get('type')}"}])
    return {'text': text, 'buttons': buttons}

# --- КОНЕЦ ИЗМЕНЕНИЙ ---