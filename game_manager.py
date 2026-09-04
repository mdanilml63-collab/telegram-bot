# game_manager.py
import random
import copy
import database as db
import combat_manager as cm
import ui_components as ui
from ui_components import generate_event_choices
import item_manager as im
import event_manager as em
import perk_manager as perk_m
import pvp_manager as pvp_m
import quest_manager
from game_content import CONTENT, BASE_STATS, EVENT_TYPES, SHOP_PRICES, SMITH_COSTS, HEALER_PRICES
from utils import escape_markdown

def start_run_with_class(user_id, run_type, class_id):
    """Финализирует начало забега с выбранным классом."""
    from game_content import CLASS_DATA # Локальный импорт
    
    class_base_stats = CLASS_DATA[class_id]['stats']
    initial_character_stats = {}

    if run_type == 'hc_pvp':
        initial_character_stats = copy.deepcopy(class_base_stats)
    else:
        initial_character_stats = im.get_base_stats_with_perks(user_id, base_stats=class_base_stats)

    initial_character = {
        'user_id': user_id, 'stats': initial_character_stats,
        'class_id': class_id,
        'equipment': {'weapon1': None, 'weapon2': None, 'helmet': None, 'body_armour': None, 'gloves': None, 'boots': None, 'ring1': None, 'ring2': None, 'amulet': None, 'belt': None},
        'currency': {'gold': 0, 'exalted_orb': 0, 'divine_orb': 0, 'mirror': 0},
        'combat': None, 'pending_loot': [], 'current_events': [], 'buffs': [],
        'permanent_bonuses': {}, 'boss_defeated_flag': False,
        'run_type': run_type if run_type != 'pve' else None,
        # --- НАЧАЛО ИЗМЕНЕНИЙ ---
        'endless_scaling_stacks': 0 # Добавляем счетчик для скалирования
        # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    }
    
    floor_bosses = {}
    
    if run_type == 'pvp':
        for floor_num in range(1, 5):
            opponent_data = db.get_random_pvp_opponent(floor_num, user_id)
            if opponent_data:
                floor_bosses[str(floor_num)] = opponent_data
            else:
                floor_bosses[str(floor_num)] = {'name': f"Призрак Этажа {floor_num}", 'stats': {'health': 500 * floor_num, 'attack': 20 * floor_num, 'defense': 10 * floor_num}, 'equipment': {}}
    # --- НОВЫЙ БЛОК ДЛЯ ХАРДКОРА ---
    elif run_type == 'hc_pvp':
        for floor_num in range(1, 5):
            opponent_data = db.get_random_hc_pvp_opponent(floor_num, user_id)
            if opponent_data:
                floor_bosses[str(floor_num)] = opponent_data
            else:
                # Запасной вариант, если в пуле нет противников
                floor_bosses[str(floor_num)] = {'name': f"Хардкорный Призрак {floor_num}", 'stats': {'health': 500 * floor_num, 'attack': 20 * floor_num, 'defense': 10 * floor_num}, 'equipment': {}}
    # --- КОНЕЦ НОВОГО БЛОКА ---
    else: # PVE и Endless
        boss_floors = list(CONTENT.values())[:4] if run_type == 'endless' else CONTENT.values()
        floor_bosses = {str(floor_num): random.choice(data['monsters']['bosses'])['name'] for floor_num, data in enumerate(boss_floors, 1)}

    db.start_new_pve_run(user_id, initial_character, floor_bosses)
    return continue_run(user_id)


def start_pve_run(user_id):
    """Инициирует выбор класса для PVE забега."""
    return ui.create_class_selection_ui(run_type='pve')


def start_endless_run(user_id):
    """Инициирует выбор класса для Бесконечного Забега."""
    return ui.create_class_selection_ui(run_type='endless')

def start_pvp_run(user_id):
    """Инициирует выбор класса для PVP забега."""
    if not pvp_m.check_pvp_eligibility(user_id):
        return {'text': "🛡️ *Доступ закрыт\\!*\\n\\nЧтобы войти в режим PVP, вы должны сначала одержать победу в PVE\\-режиме\\.", 'buttons': [[{'text': '⬅️ В главное меню', 'callback_data': 'back_to_main_menu'}]]}
    return ui.create_class_selection_ui(run_type='pvp')

def start_hc_pvp_run(user_id):
    """Инициирует выбор класса для Хардкорного PVP забега."""
    # Хардкор доступен сразу, проверка на PVE победу не нужна.
    return ui.create_class_selection_ui(run_type='hc_pvp')

def process_smith_action(user_id, mode, slot=None):
    run_state = db.get_pve_run_state(user_id)
    char = run_state['character']
    
    # ИЗМЕНЕНИЕ: Динамический расчет стоимости с учетом скидки
    base_cost = SMITH_COSTS.get(mode, 9999)
    floor_cost = int(base_cost * (1 + 0.25 * (run_state['floor'] - 1)))
    discount = ui.get_effective_stats(char).get('service_discount', 0)
    cost = int(floor_cost * (1 - discount / 100.0))

    if char['currency']['gold'] < cost:
        response = ui.create_blacksmith_ui(run_state)
        response['text'] = f"❌ Недостаточно золота\\! Нужно {cost} 🪙\\.\\\n\n" + response['text']
        return response
    char['currency']['gold'] -= cost
    if mode == 'simple_upgrade':
        char, message = im.perform_simple_upgrade(user_id, char, slot)
    elif mode == 'blessing':
        char, message = im.perform_blessing(user_id, char, slot)
    elif mode == 'tier_up':
        char, new_item, error_message = im.perform_tier_up(char, run_state['floor'])
        if error_message:
            char['currency']['gold'] += cost
            db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
            response = ui.create_blacksmith_ui(run_state)
            response['text'] = f"⚠️ {error_message}\n\n" + response['text']
            return response
        db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
        response = ui.create_loot_choice_ui(run_state)
        response['text'] = f"Кузнец протягивает вам новый предмет\\.\\.\\.\n\n" + response['text']
        return response
    run_state['event_num'] += 1
    char['current_events'] = []
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    next_step = continue_run(user_id)
    return {'text': f"✨ {message}\n\n" + next_step['text'], 'buttons': next_step['buttons']}

# НОВЫЙ КОД: Функция для обработки выбора умения Восхождения
def process_ascendancy_choice(user_id, run_state, passive_id):
    """Применяет выбранное умение Восхождения и переходит к экрану добычи."""
    char = run_state['character']
    
    if char.get('ascendancy_points', 0) < 1:
        loot_ui = ui.create_loot_choice_ui(run_state)
        loot_ui['text'] = "❌ У вас нет очков для изучения\\.\n\n" + loot_ui['text']
        return loot_ui

    # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    # 1. Извлекаем сохраненное сообщение о победе и СРАЗУ удаляем его из состояния
    victory_message = char.pop('pending_victory_message', None)
    
    # 2. Применяем умение
    char['ascendancy_points'] -= 1
    char.setdefault('chosen_ascendancy_passives', []).append(passive_id)
    
    im.recalculate_stats(user_id, char)
    
    # 3. Сохраняем обновленное состояние (уже без pending_victory_message)
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    
    # 4. Генерируем UI с лутом
    loot_ui = ui.create_loot_choice_ui(run_state)
    
    # 5. Формируем все части текста
    from game_content import ASCENDANCY_PASSIVES
    passive_name = ASCENDANCY_PASSIVES[char['class_id']][passive_id]['name']
    confirmation_text = f"✅ *Умение «{escape_markdown(passive_name)}» изучено\\!*"
    
    final_text = ""
    if victory_message:
        final_text += victory_message + "\n\n" # Сначала текст о победе, золоте и опыте
    
    final_text += confirmation_text + "\n\n" # Затем текст об изучении умения
    final_text += loot_ui['text'] # В конце - сам UI выбора лута
    
    loot_ui['text'] = final_text
    
    return loot_ui



def handle_event(user_id, event_type):
    run_state = db.get_pve_run_state(user_id)
    if not run_state: return {'text': "❌ Ошибка: не найдено активного прохождения\\.", 'buttons': [[{'text': 'В главное меню', 'callback_data': 'back_to_main_menu'}]]}
    
    char = run_state['character']

    # --- НАЧАЛО КЛЮЧЕВОГО ИСПРАВЛЕНИЯ ---
    # ПРОВЕРКА №1: Есть ли у игрока ожидающая добыча?
    # Если да, то это действие имеет наивысший приоритет.
    if char.get('pending_loot'):
        # Игнорируем запрошенное событие (event_type) и показываем экран выбора добычи.
        return ui.create_loot_choice_ui(run_state)
    # --- КОНЕЦ КЛЮЧЕВОГО ИСПРАВЛЕНИЯ ---

    user_id = char['user_id']
    effective_stats = ui.get_effective_stats(char) 
    char['stats']['energy_shield'] = effective_stats['max_energy_shield'] 
    char['current_events'] = []
    
    is_fight = event_type in ['бой_обычный', 'бой_редкий', 'лутгоблин']
    is_boss_fight = (event_type == 'boss_fight' and run_state['event_num'] >= 15)
    
    if is_fight or is_boss_fight:
        fight_type = 'босс' if is_boss_fight else event_type
        run_state['event_num'] += 1
        db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
        return cm.create_fight_event(user_id, run_state, fight_type)

    if event_type == 'сундук':
        quest_manager.update_quest_progress(user_id, 'pve_open_chests')
        return em.handle_chest_event(user_id, run_state)
    
    if event_type == 'загадочная_комната':
        return em.handle_mysterious_room(user_id, run_state)

    if event_type == 'святилище': 
        quest_manager.update_quest_progress(user_id, 'pve_use_shrines')
        return em.handle_shrine_event(user_id, run_state)
    if event_type == 'встреча_с_изгнанником': return em.create_exile_encounter(user_id, run_state)
    if event_type == 'алтарь_порчи': 
        return em.handle_corruption_altar(user_id, run_state)
    if event_type == 'испытание_возвышения': return em.handle_ascendancy_trial(user_id, run_state)
    
    if event_type == 'магазин':
        if 'shop_inventory' not in char or not char.get('shop_inventory'):
            floor_num = run_state['floor']
            
            content_floor_num = floor_num
            if char.get('run_type') == 'endless' and floor_num > 4:
                content_floor_num = 4

            standard_items = CONTENT[f"floor_{content_floor_num}"]['items']
            all_custom_items = db.get_all_custom_items()
            floor_custom_items = [item for item in all_custom_items if item.get('floor') == floor_num]

            combined_item_pool = {}
            for rarity in ['magic', 'rare', 'unique', 'legendary']:
                combined_item_pool[rarity] = standard_items.get(rarity, []) + \
                                            [item for item in floor_custom_items if item.get('rarity') == rarity]

            rarities, weights = zip(*{'magic': 0.40, 'rare': 0.30, 'unique': 0.20, 'legendary': 0.10}.items())
            shop_inventory = []
            for _ in range(6):
                rarity = random.choices(rarities, weights, k=1)[0]
                if rarity in combined_item_pool and combined_item_pool[rarity]:
                    item = copy.deepcopy(random.choice(combined_item_pool[rarity]))
                    item['rarity'] = rarity
                    shop_inventory.append(item)
            
            char['shop_inventory'] = shop_inventory
            db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
        return ui.create_shop_ui(run_state)

    if event_type == 'кузнец':
        quest_manager.update_quest_progress(user_id, 'pve_visit_smith')
        return ui.create_blacksmith_ui(run_state)
        
    if event_type == 'лекарь': 
        quest_manager.update_quest_progress(user_id, 'pve_visit_healer')
        return ui.create_healer_ui(run_state)
    
    run_state['event_num'] += 1
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    next_step = continue_run(user_id)
    return {'text': f"Обработчик для '{escape_markdown(str(event_type))}' не реализован\\. Переход к следующей комнате\\." + "\n\n" + next_step['text'], 'buttons': next_step['buttons']}
def process_healer_choice(user_id, heal_type):
    run_state = db.get_pve_run_state(user_id)
    char, stats = run_state['character'], run_state['character']['stats']
    effective_char_stats = ui.get_effective_stats(char)
    max_health = effective_char_stats['max_health']
    cost, heal_amount = 0, 0
    
    # Динамический расчет стоимости с учетом скидки
    discount = effective_char_stats.get('service_discount', 0)
    
    if heal_type == 'free': 
        heal_amount = int(max_health * 0.25)
    elif heal_type == 'half': 
        base_cost = HEALER_PRICES['half']
        floor_cost = int(base_cost * (1 + 0.25 * (run_state['floor'] - 1)))
        cost = int(floor_cost * (1 - discount / 100.0))
        heal_amount = int(max_health * 0.50)
    elif heal_type == 'full': 
        base_cost = HEALER_PRICES['full']
        floor_cost = int(base_cost * (1 + 0.25 * (run_state['floor'] - 1)))
        cost = int(floor_cost * (1 - discount / 100.0))
        heal_amount = max_health

    if char['currency']['gold'] < cost:
        response = ui.create_healer_ui(run_state)
        response['text'] = f"❌ Недостаточно золота\\! Требуется {cost} 🪙, у вас {char['currency']['gold']} 🪙\\.\n\n" + response['text']
        return response
        
    # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    char['currency']['gold'] -= cost
    
    # Рассчитываем, сколько здоровья действительно нужно восстановить
    health_to_reach = min(max_health, stats['health'] + heal_amount)
    actual_heal_amount = health_to_reach - stats['health']
    
    # Применяем лечение через универсальную функцию, которая учтет "Кровавый Ритуал"
    char = cm._apply_healing(char, actual_heal_amount)
    
    # Сообщение теперь нейтральное, так как результат может быть разным
    success_text = f"💖 Вы получили *{actual_heal_amount}* здоровья" + (f"\\. Потрачено *{cost}* 🪙 золота\\." if cost > 0 else "\\.")
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    
    run_state['event_num'] += 1
    char['current_events'] = []
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    
    next_step = continue_run(user_id)
    return {'text': success_text + "\n\n" + next_step['text'], 'buttons': next_step['buttons']}



def process_shop_purchase(user_id, item_index):
    run_state = db.get_pve_run_state(user_id)
    char = run_state['character']
    item_to_buy = char['shop_inventory'][item_index]
    
    # ИЗМЕНЕНИЕ: Расчет цены с учетом скидки
    base_price = SHOP_PRICES.get(item_to_buy.get('rarity'), 9999)
    discount = ui.get_effective_stats(char).get('service_discount', 0)
    price = int(base_price * (1 - discount / 100.0))
    
    quest_manager.update_quest_progress(user_id, 'pve_spend_gold', value=price)
    
    if char['currency']['gold'] < price:
        response = ui.create_shop_ui(run_state)
        response['text'] = f"❌ Недостаточно золота\\! Нужно {price} 🪙\\.\n\n" + response['text']
        return response
        
    char['currency']['gold'] -= price
    char['shop_inventory'].pop(item_index)
    char['pending_loot'] = [item_to_buy]

    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])

    if item_to_buy['slot'] == 'ring':
        return ui.create_ring_slot_choice_ui(0, char)
    else:
        slot = item_to_buy['slot']
        old_item = char['equipment'].get(slot)
        return ui.create_item_comparison_ui(char, item_to_buy, old_item, target_slot=slot, item_index=0)

def continue_run(user_id):
    run_state = db.get_pve_run_state(user_id)
    if not run_state: return {'text': "❌ Нет активного забега\\.", 'buttons': [[{'text': 'В главное меню', 'callback_data': 'back_to_main_menu'}]]}
    
    char = run_state['character']
    
    # --- НАЧАЛО ИСПРАВЛЕНИЯ: Меняем порядок блоков ---

    # Шаг 1: Проверяем, нужно ли перейти на следующий этаж
    if char.pop('boss_defeated_flag', False): # Используем .pop() чтобы флаг сработал только один раз
        is_endless_run = char.get('run_type') == 'endless'
        
        if run_state['floor'] == 4 and not is_endless_run:
            db.end_pve_run(user_id, is_win=True, xp_reward=500)
            return {'text': "🏆 *ПОЗДРАВЛЯЕМ\\!* Вы прошли все этажи и одержали великую победу\\! В качестве награды вы получаете *2 💎 Divine Orb* и *500* опыта\\.", 'buttons': [[{'text': 'В главное меню', 'callback_data': 'back_to_main_menu'}]]}
        else:
            run_state['floor'] += 1
            if is_endless_run and run_state['floor'] > 4:
                run_state['floor_bosses'][str(run_state['floor'])] = random.choice(CONTENT['floor_4']['monsters']['bosses'])['name']
            run_state['event_num'] = 0
            db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
            return continue_run(user_id)

    # Шаг 2: Если перехода не было, проверяем, нужно ли телепортироваться
    if char.pop('just_won_fight', False):
        teleported = False
        for item in char.get('equipment', {}).values():
            if item and item.get('special_mechanic') == 'random_teleport_on_win':
                if item.get('charges', [0, 0])[0] > 0:
                    run_state['floor'] = random.randint(1, 4)
                    run_state['event_num'] = random.randint(0, 13)
                    char['current_events'] = []
                    teleported = True
                    break 
        
        db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])

    # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

    if 'pending_loot' in char and char['pending_loot']: return ui.create_loot_choice_ui(run_state)
    if 'shop_inventory' in char: char.pop('shop_inventory', None)
    
    if char.get('run_type') == 'endless' and run_state['floor'] > 4:
        run_state['floor_content_key'] = 4
    else:
        run_state['floor_content_key'] = run_state['floor']
        
    if run_state['event_num'] >= 15:
        floor_key = str(run_state['floor'])
        if floor_key not in run_state['floor_bosses'] and char.get('run_type') == 'endless' and run_state['floor'] > 4:
            run_state['floor_bosses'][floor_key] = random.choice(CONTENT['floor_4']['monsters']['bosses'])['name']
            db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])

        if floor_key not in run_state['floor_bosses']:
            db.end_pve_run(user_id, is_win=False)
            return {'text': ("❌ *Критическая ошибка забега\\!*\\n\\n"
                         "Не удалось найти данные о боссе для текущего этажа\\. "
                         "Забег был безопасно завершен\\."),
                'buttons': [[{'text': 'В главное меню', 'callback_data': 'back_to_main_menu'}]]}
    
        boss_name_or_data = run_state['floor_bosses'][floor_key]
        boss_display_name = boss_name_or_data if isinstance(boss_name_or_data, str) else boss_name_or_data.get('name', 'Неизвестный противник')
        return {'text': f"Вы прошли 15 комнат\\.\\.\\. За дверью вас ждет босс этажа: *{escape_markdown(boss_display_name)}*\\!", 'buttons': [[{'text': '⚔️ Сразиться с боссом', 'callback_data': 'event_boss_fight'}]]}

    if not char.get('current_events'):
        choices = []
        if run_state['event_num'] < 3:
            common_fight_event = next(e for e in EVENT_TYPES if e['id'] == 'бой_обычный')
            other_events = [e for e in EVENT_TYPES if e['id'] != 'бой_обычный']
            random_choices = random.sample(other_events, 2)
            choices = [common_fight_event] + random_choices
            random.shuffle(choices)
        elif run_state['event_num'] == 14:
            other_events = [e for e in EVENT_TYPES if e['id'] != 'лекарь']
            choices = random.sample(other_events, 2)
            healer_event = next((e for e in EVENT_TYPES if e['id'] == 'лекарь'), None)
            if healer_event:
                choices.append(healer_event)
            random.shuffle(choices)
        else:
            choices = random.sample(EVENT_TYPES, 3)

        char['current_events'] = choices 
        db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
        
    return generate_event_choices(run_state)
