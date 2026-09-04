# event_manager.py
import random
import copy
import database as db
import ui_components as ui
import item_manager as im
import quest_manager
from game_content import CONTENT, BASE_STATS
from utils import escape_markdown
import combat_manager as cm

CRUCIBLE_FORGE_COST = 2000

# --- НАЧАЛО ИЗМЕНЕНИЙ: Добавьте эти две функции ---

def handle_crucible_forge(user_id, run_state):
    """Начинает событие 'Кузница Горнила', предлагая выбрать этаж."""
    character = run_state['character']
    if character.get('currency', {}).get('gold', 0) < CRUCIBLE_FORGE_COST:
        return {
            'text': f"🔥 Вы нашли Кузницу Горнила, но у вас недостаточно золота, чтобы ее активировать\\. Требуется *{CRUCIBLE_FORGE_COST}* 🪙\\.",
            'buttons': [[{'text': 'Уйти', 'callback_data': 'continue_run'}]]
        }
    return ui.create_crucible_floor_choice_ui()

def process_crucible_item_selection(user_id, run_state, item_index, context):
    """Обрабатывает финальный выбор предмета в кузнице."""
    from game_manager import continue_run
    char = run_state['character']
    
    if char.get('currency', {}).get('gold', 0) < CRUCIBLE_FORGE_COST:
        return {'text': "Ошибка: недостаточно золота\\.", 'buttons': [[{'text': 'В главное меню', 'callback_data': 'back_to_main_menu'}]]}

    # Получаем тот же пул предметов, который был показан пользователю
    item_pool = ui._get_crucible_item_pool(context)
    if item_index >= len(item_pool):
        return {'text': "Ошибка: неверный индекс предмета\\.", 'buttons': [[{'text': 'В главное меню', 'callback_data': 'back_to_main_menu'}]]}

    chosen_item = copy.deepcopy(item_pool[item_index])
    
    # Списываем золото и даем предмет
    char['currency']['gold'] -= CRUCIBLE_FORGE_COST
    char['pending_loot'] = [chosen_item]
    
    message = f"🔥 Кузница с ревом принимает ваше золото и выковывает для вас *{escape_markdown(chosen_item['name'])}*\\!"
    
    # Завершаем событие
    run_state['event_num'] += 1
    char['current_events'] = []
    del context.user_data['crucible_session'] # Очищаем сессию
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    
    loot_ui = ui.create_loot_choice_ui(run_state)
    loot_ui['text'] = message + "\n\n" + loot_ui['text']
    return loot_ui

# --- КОНЕЦ ИЗМЕНЕНИЙ ---

# --- 1. Святилище (Shrine) ---

SHRINE_BUFFS = [
    {'name': "Святилище Скорости", 'effect': {'dodge_chance': 10}, 'duration': 6, 'desc': "+10% к шансу уворота на 6 боёв."},
    {'name': "Святилище Защиты", 'effect': {'defense': 15}, 'duration': 5, 'desc': "+15% к защите на 5 боёв."},
    {'name': "Святилище Резонанса", 'effect': {'crit_chance': 7}, 'duration': 5, 'desc': "+7% к шансу крит. удара на 5 боёв."},
    {'name': "Святилище Титана", 'effect': {'max_health': 30}, 'duration': 5, 'desc': "+30 к макс. здоровью на 5 боёв."},
    {'name': "Святилище Непробиваемости", 'effect': {'block_chance': 10}, 'duration': 6, 'desc': "+10% к шансу блока на 6 боёв."},
    {'name': "Святилище Точности", 'effect': {'attack': 7}, 'duration': 7, 'desc': "+7 к атаке на 7 боёв."},
    {'name': "Святилище Мощи", 'effect': {'crit_multiplier': 50}, 'duration': 3, 'desc': "Крит. удары наносят на 50% больше урона (x2.5) в течение 3 боёв."},
    {'name': "Святилище Стойкости", 'effect': {'health_regen': 20}, 'duration': 5, 'desc': "Восстанавливает 20% здоровья после каждой победы в течение 5 боёв."},
    {'name': "Святилище Эгиды", 'effect': {'max_energy_shield': 25}, 'duration': 6, 'desc': "+25 к макс. энергощиту на 6 боёв."},
    {'name': "Святилище Удачи", 'effect': {'gold_find': 100}, 'duration': 3, 'desc': "На 100% больше золота с монстров в течение 3 боёв."}
]

def handle_shrine_event(user_id, run_state):
    from game_manager import continue_run
    char = run_state['character']
    
    shrine_duration_bonus = ui.get_effective_stats(char).get('shrine_duration', 0)
    
    buff_template = copy.deepcopy(random.choice(SHRINE_BUFFS))
    buff_template['duration'] += shrine_duration_bonus
    
    existing_buff = next((b for b in char.get('buffs', []) if b['name'] == buff_template['name']), None)
    if existing_buff:
        existing_buff['duration'] = max(existing_buff['duration'], buff_template['duration'])
        message = f"✨ Вы снова прикоснулись к святилищу *{escape_markdown(buff_template['name'])}*\\! Его действие обновлено\\.\n\n_{escape_markdown(buff_template['desc'])}_"
    else:
        char.setdefault('buffs', []).append(buff_template)
        message = f"✨ Вы прикоснулись к святилищу и получили благословение:\n\n>>> *{escape_markdown(buff_template['name'])}* <<<\n\n_{escape_markdown(buff_template['desc'])}_"
    
    # Теперь эта функция сама правильно восстановит здоровье до нового максимума
    im.recalculate_stats(user_id, char) 
    
    run_state['event_num'] += 1
    char['current_events'] = []
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    next_step = continue_run(user_id)
    return {'text': message + "\n\n" + next_step['text'], 'buttons': next_step['buttons']}

def create_exile_encounter(user_id, run_state):
    import combat_manager as cm
    from game_content import CLASS_DATA # Импортируем данные о классах
    floor_num = run_state['floor']
    char = run_state['character']

    content_floor_num = floor_num
    if char.get('run_type') == 'endless' and floor_num > 4:
        content_floor_num = 4
    
    exile_stats = copy.deepcopy(BASE_STATS)
    
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Усиление базовых статов Изгнанника ---
    exile_stats['health'] += 100 * (floor_num)
    exile_stats['attack'] += 20 * (floor_num)
    exile_stats['defense'] += 5 * (floor_num)
    exile_stats['max_health'] = exile_stats['health']
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    # --- НАЧАЛО ИЗМЕНЕНИЯ: Присваиваем случайный класс ---
    random_class_id = random.choice(list(CLASS_DATA.keys()))
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---
    monster_data = {
        'name': "Загадочный Изгнанник",
        'type': 'изгнанник',
        'stats': exile_stats,
        'log_message': 'Вы наткнулись на другого изгнанника\\! Он не выглядит дружелюбно\\. Бой начинается\\!'
    }
    
    # --- ИЗМЕНЕНИЕ: Передаем монстра в центральную функцию ---
    run_state['event_num'] += 1
    char['current_events'] = []
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    return cm.create_fight_event(user_id, run_state, 'изгнанник', custom_monster_data=monster_data)


# --- 3. Алтарь Порчи ---

CORRUPTION_IMPLICITS = {
    'weapon': [
        {'name': "Неумолимость", 'effect': {'cannot_be_blocked': True}, 'desc': "Атаки этим оружием не могут быть заблокированы."},
        {'name': "Сглаз", 'effect': {'cannot_be_dodged': True}, 'desc': "Атаки этим оружием не могут быть уклонены."},
        {'name': "Приговор", 'effect': {'defense_penetration': 25}, 'desc': "+25% к пробитию защиты этим оружием."}
    ],
    'armour': [ 
        {'name': "Бастион", 'effect': {'defense': 15}, 'desc': "+15% к защите."},
        {'name': "Живучесть", 'effect': {'health': 80}, 'desc': "+80 к здоровью."},
        {'name': "Несокрушимость", 'effect': {'crit_damage_reduction': 25}, 'desc': "Получаемый критический урон снижен на 25%."}
    ],
    'accessory': [ 
        {'name': "Вампиризм", 'effect': {'lifesteal': 10}, 'desc': "Вы восстанавливаете 10% от нанесенного урона в виде здоровья."},
        {'name': "Эгида порчи", 'effect': {'es_leech_rate': 4}, 'desc': "+4% к вампиризму энергощита."},
        {'name': "Алчность", 'effect': {'magic_find': 35}, 'desc': "+35% к поиску магических предметов."}
    ]
}

def handle_corruption_altar(user_id, run_state):
    return ui.create_corruption_altar_ui(run_state['character'])

def process_corruption(user_id, run_state, slot_to_corrupt):
    """Обрабатывает осквернение выбранного предмета."""
    from game_manager import continue_run
    char = run_state['character']
    item = char['equipment'].get(slot_to_corrupt)

    if not item:
        next_step = continue_run(user_id)
        return {'text': "Ошибка: предмет не найден\\.", 'buttons': next_step['buttons']}

    item['corrupted'] = True
    original_name = item['name']
    
    roll = random.randint(1, 100)
    message = ""
    proceed_to_loot_ui = False

    if roll <= 40:
        message = f"🔮 Алтарь гудит, но ничего не происходит\\. Предмет *{escape_markdown(original_name)}* сопротивляется порче\\."
    
    elif roll <= 65:
        message = f"💥 Со вспышкой темной энергии ваш предмет *{escape_markdown(original_name)}* рассыпается в прах\\!"
        char['equipment'][slot_to_corrupt] = None
    
    elif roll <= 90:
        item['corrupted'] = True
        
        item_slot = item.get('slot')
        item_type = 'accessory'
        if 'weapon' in item_slot:
            item_type = 'weapon'
        elif item_slot in ['helmet', 'body_armour', 'gloves', 'boots']:
            item_type = 'armour'

        implicit = copy.deepcopy(random.choice(CORRUPTION_IMPLICITS[item_type]))
        item['implicit'] = implicit
        message = (f"✨ Ваш предмет *{escape_markdown(original_name)}* пропитывается силой\\! Он получает новое свойство:\n\n"
                   f"*{escape_markdown(implicit['name'])}*: _{escape_markdown(implicit['desc'])}_")

    else: # 10% шанс - улучшение редкости
        item['corrupted'] = True
        new_rarity = None
        if item.get('rarity') == 'magic':
            new_rarity = 'rare'
        elif item.get('rarity') == 'rare':
            new_rarity = 'unique'
        
        if new_rarity:
            # --- НАЧАЛО ИЗМЕНЕНИЙ: Надежное определение этажа для контента ---
            content_floor_num = run_state['floor']
            if char.get('run_type') == 'endless' and run_state['floor'] > 4:
                content_floor_num = 4
            
            floor_items = CONTENT[f"floor_{content_floor_num}"]['items']
            # --- КОНЕЦ ИЗМЕНЕНИЙ ---

            item_pool = [i for i in floor_items.get(new_rarity, []) if i['slot'] == item['slot']]
            if item_pool:
                new_item = copy.deepcopy(random.choice(item_pool))
                new_item['corrupted'] = True
                
                char['equipment'][slot_to_corrupt] = None
                char['pending_loot'] = [new_item]
                proceed_to_loot_ui = True
                message = f"💥 В ослепительной вспышке ваш предмет *{escape_markdown(original_name)}* перерождается в *{new_rarity}* предмет: *{escape_markdown(new_item['name'])}*\\!"
            else:
                message = "Алтарь пытался преобразить ваш предмет, но энергия иссякла\\. Ничего не произошло\\."
                item['corrupted'] = False
        else:
            message = "Алтарь пытался преобразить ваш предмет, но его сила слишком велика\\. Ничего не произошло\\."
            item['corrupted'] = False

    quest_manager.update_quest_progress(user_id, 'pve_corrupt_item')
    im.recalculate_stats(user_id, char)
    
    run_state['event_num'] += 1
    char['current_events'] = []
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])

    if proceed_to_loot_ui:
        loot_ui = ui.create_loot_choice_ui(run_state)
        loot_ui['text'] = message + "\n\n" + loot_ui['text']
        return loot_ui

    next_step = continue_run(user_id)
    final_text = message + "\n\n" + next_step['text']
    return {'text': final_text, 'buttons': next_step['buttons']}

# --- 4. Испытание Возвышения ---

TRIAL_REWARDS = [
    {'stat': 'attack', 'value': 5, 'desc': "+5 к базовой атаке"},
    {'stat': 'max_health', 'value': 25, 'desc': "+25 к базовому здоровью"},
    {'stat': 'max_energy_shield', 'value': 10, 'desc': "+10 к базовому энергощиту"},
    {'stat': 'defense', 'value': 4, 'desc': "+4% к базовой защите"},
    {'stat': 'crit_chance', 'value': 2, 'desc': "+2% к базовому шансу крит. удара"},
    {'stat': 'dodge_chance', 'value': 2, 'desc': "+2% к базовому шансу уворота"},
    {'stat': 'block_chance', 'value': 2, 'desc': "+2% к базовому шансу блока"},
    {'stat': 'gold_find', 'value': 20, 'desc': "+20% к поиску золота (постоянно)"},
    {'stat': 'accuracy', 'value': 6, 'desc': "+3 к базовой точности"},
    {'stat': 'defense_penetration', 'value': 5, 'desc': "+5% к пробитию защиты"},
    {'stat': 'double_damage_chance', 'value': 2, 'desc': "+2% к шансу двойного урона"},
    {'stat': 'crit_damage_reduction', 'value': 10, 'desc': "+10% к защите от крит. урона"},
    {'stat': 'es_leech_rate', 'value': 1, 'desc': "+1% к вампиризму энергощита"},
]

def handle_ascendancy_trial(user_id, run_state):
    floor = run_state['floor']
    trials = [
        {'id': 'dodge', 'stat': 'dodge_chance', 'req': 7 + floor * 3, 'text': "Проскользнуть"},
        {'id': 'attack', 'stat': 'attack', 'req': 15 + floor * 5, 'text': "Проломить стену"},
        {'id': 'es', 'stat': 'max_energy_shield', 'req': 30 + floor * 15, 'text': "Магический удар"},
        {'id': 'defense', 'stat': 'defense', 'req': 10 + floor * 4, 'text': "Огненные гейзеры"},
        {'id': 'crit', 'stat': 'crit_chance', 'req': 6 + floor * 4, 'text': "Древний механизм"},
        {'id': 'block', 'stat': 'block_chance', 'req': 8 + floor * 3, 'text': "Отбить щитом"},
        {'id': 'accuracy', 'stat': 'accuracy', 'req': 10 + floor * 8, 'text': "Попасть в цель"},
        {'id': 'pen', 'stat': 'defense_penetration', 'req': 6 + floor * 5, 'text': "Силовой барьер"},
        {'id': 'dd', 'stat': 'double_damage_chance', 'req': 4 + floor * 2, 'text': "Вызвать взрыв"},
        {'id': 'mf', 'stat': 'magic_find', 'req': 20 + floor * 10, 'text': "На Удачу"},
    ]
    chosen_trials = random.sample(trials, 3)
    return ui.create_trial_ui(chosen_trials)

def process_trial_choice(user_id, run_state, trial_id):
    from game_manager import continue_run
    char = run_state['character']
    floor = run_state['floor']
    
    trials = {
        'dodge': {'stat': 'dodge_chance', 'req': 7 + floor * 3},
        'attack': {'stat': 'attack', 'req': 15 + floor * 5},
        'es': {'stat': 'max_energy_shield', 'req': 30 + floor * 15},
        'defense': {'stat': 'defense', 'req': 10 + floor * 4},
        'crit': {'stat': 'crit_chance', 'req': 6 + floor * 4},
        'block': {'stat': 'block_chance', 'req': 8 + floor * 3},
        'accuracy': {'stat': 'accuracy', 'req': 10 + floor * 8},
        'pen': {'stat': 'defense_penetration', 'req': 6 + floor * 5},
        'dd': {'stat': 'double_damage_chance', 'req': 4 + floor * 2},
        'mf': {'stat': 'magic_find', 'req': 20 + floor * 10},
    }
    
    trial = trials[trial_id]
    player_stats = ui.get_effective_stats(char) 
    
    message = ""
    if player_stats.get(trial['stat'], 0) >= trial['req']:
        quest_manager.update_quest_progress(user_id, 'pve_win_trial')
        reward = copy.deepcopy(random.choice(TRIAL_REWARDS))
        char.setdefault('permanent_bonuses', {})
        char['permanent_bonuses'][reward['stat']] = char['permanent_bonuses'].get(reward['stat'], 0) + reward['value']
        message = f"✅ *Испытание пройдено\\!*\n\nВаша решимость вознаграждена\\. Вы получаете постоянный бонус: *{escape_markdown(reward['desc'])}*\\."
    else:
        damage = int(char['stats']['max_health'] * (0.10 + floor * 0.02)) 
        char['stats']['health'] -= damage
        message = f"❌ *Провал\\!*\n\nВы не смогли преодолеть ловушку и получаете *{damage}* урона\\."
        if char['stats']['health'] <= 0:
            db.end_pve_run(user_id, is_win=False)
            return {'text': message + "\n\n💀 *Вы погибли в ловушке\\!* Ваше путешествие окончено\\.", 'buttons': [[{'text': 'В главное меню', 'callback_data': 'back_to_main_menu'}]]}

    char = im.recalculate_stats(user_id, char)
    run_state['event_num'] += 1
    char['current_events'] = []
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    
    next_step = continue_run(user_id)
    final_text = message + "\n\n" + next_step['text']
    return {'text': final_text, 'buttons': next_step['buttons']}

# --- НАЧАЛО НОВОГО БЛОКА: ПЕРЕРАБОТАННЫЕ СОБЫТИЯ ---

def handle_chest_event(user_id, run_state):
    """(НОВОЕ) Инициирует событие 'Сундук' с выбором."""
    return ui.create_chest_choice_ui()

def handle_chest_choice(user_id, run_state, choice):
    """(ИЗМЕНЕНО) Обрабатывает выбор игрока у сундука с тремя исходами."""
    from game_manager import continue_run
    import combat_manager as cm
    char = run_state['character']

    if choice == 'plain':
        # Новая логика с тремя исходами: 35% золото, 35% предметы, 30% ловушка
        outcome = random.choices(['gold', 'items', 'trap'], weights=[0.35, 0.35, 0.30], k=1)[0]
        
        # --- Исход №1: Предметы ---
        if outcome == 'items':
            loot = im.generate_loot(run_state['floor'], char, 'бой_редкий')
            char['pending_loot'] = loot
            message = f"📦 Сундук со скрипом открывается, и вы видите внутри несколько предметов\\!"
            
            # Обновляем состояние и переходим к экрану выбора добычи
            run_state['event_num'] += 1
            char['current_events'] = []
            db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
            
            loot_ui = ui.create_loot_choice_ui(run_state)
            loot_ui['text'] = message + "\n\n" + loot_ui['text']
            return loot_ui

        # --- Исход №2: Золото ---
        elif outcome == 'gold':
            gold = random.randint(30, 80) * run_state['floor']
            char['currency']['gold'] += gold
            message = f"📦 Вы открыли обычный сундук и нашли *{gold}* 🪙 золота\\."
            
        # --- Исход №3: Ловушка ---
        else: # trap
            damage = int(char['stats']['max_health'] * 0.15)
            char['stats']['health'] -= damage
            message = f"❗ Это ловушка\\! Из сундука вырываются иглы, и вы получаете *{damage}* урона\\."
            if char['stats']['health'] <= 0:
                db.end_pve_run(user_id, is_win=False)
                return {'text': message + "\n\n💀 *Вы погибли от яда\\!*", 'buttons': [[{'text': 'В главное меню', 'callback_data': 'back_to_main_menu'}]]}

        # Общий код для исходов "золото" и "ловушка"
        run_state['event_num'] += 1
        char['current_events'] = []
        db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
        next_step = continue_run(user_id)
        return {'text': message + "\n\n" + next_step['text'], 'buttons': next_step['buttons']}

    elif choice == 'cursed':
        char['stats']['energy_shield'] = ui.get_effective_stats(char)['max_energy_shield']

        content_floor_num = run_state['floor']
        if char.get('run_type') == 'endless' and run_state['floor'] > 4:
            content_floor_num = 4
        
        floor_content = CONTENT[f"floor_{content_floor_num}"]
        
        monster_data = copy.deepcopy(random.choice(floor_content['monsters']['rare']))
        monster_data['name'] = f"Дух-хранитель сундука"
        
        monster_data['log_message'] = 'Вы потревожили проклятый сундук, и его усиленный экипировкой хранитель восстал из мертвых\\!'
        monster_data['type'] = 'сундук'
        
        char['pending_chest_reward'] = 'cursed'
        run_state['event_num'] += 1
        char['current_events'] = []
        db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
        
        return cm.create_fight_event(user_id, run_state, 'сундук', custom_monster_data=monster_data)

def handle_mysterious_room(user_id, run_state):
    """(ПЕРЕРАБОТАНО) Запускает случайное событие в загадочной комнате."""
    # --- НАЧАЛО ИЗМЕНЕНИЯ: Динамическое формирование пула событий ---
    char = run_state['character']
    
    # Составляем базовый список всех возможных событий
    event_functions = [
        _mystery_fountain_reworked,
        _mystery_sacrificial_altar,
        _mystery_pact_with_shadow,
        _mystery_touch_of_kalandra,
        _mystery_cadiro,
    ]
    
    # Проверяем, полное ли здоровье у игрока
    is_full_health = char['stats']['health'] >= ui.get_effective_stats(char)['max_health']
    
    # Если здоровье полное, удаляем фонтан из списка возможных событий
    if is_full_health:
        event_functions.remove(_mystery_fountain_reworked)
    
    # Выбираем случайное событие из отфильтрованного списка
    chosen_function = random.choice(event_functions)
    return chosen_function(user_id, run_state)
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

def _mystery_fountain_reworked(user_id, run_state):
    """
    (ИЗМЕНЕНО) Теперь эта функция вызывается только для раненых игроков
    и просто восстанавливает им здоровье до максимума.
    """
    from game_manager import continue_run
    char = run_state['character']
    
    # --- НАЧАЛО ИЗМЕНЕНИЯ: Упрощение логики ---
    # Так как эта функция теперь вызывается только если здоровье неполное,
    # нам больше не нужна проверка is_full_health.
    
    # Рассчитываем, сколько здоровья нужно восстановить
    heal_needed = ui.get_effective_stats(char)['max_health'] - char['stats']['health']
    
    # Применяем лечение
    char = cm._apply_healing(char, heal_needed)
    
    message = "💧 Вы пьете из фонтана, и его живительная вода полностью восстанавливает ваше здоровье\\!"
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    im.recalculate_stats(user_id, char)
    run_state['event_num'] += 1
    char['current_events'] = []
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    
    next_step = continue_run(user_id)
    return {'text': message + "\n\n" + next_step['text'], 'buttons': next_step['buttons']}

def _mystery_sacrificial_altar(user_id, run_state):
    floor = run_state['floor']
    if floor == 1:
        health_cost = 20
    elif floor == 2:
        health_cost = 30
    elif floor == 3:
        health_cost = 40
    else:  # Этаж 4 и выше
        health_cost = 50
        
    return ui.create_sacrifice_ui(health_cost)

def process_sacrifice(user_id, run_state):
    """(ИСПРАВЛЕНО) Обрабатывает жертвоприношение."""
    char = run_state['character']
    floor = run_state['floor']

    if floor == 1:
        health_cost = 20
    elif floor == 2:
        health_cost = 30
    elif floor == 3:
        health_cost = 40
    else:
        health_cost = 50
        
    if char['stats']['health'] <= health_cost:
        error_message = f"❌ *Недостаточно здоровья\\!* ❌\n\nДля ритуала требуется *{health_cost}* ❤️, а у вас всего *{char['stats']['health']}* ❤️\\.\n\n"
        ui_data = ui.create_sacrifice_ui(health_cost)
        ui_data['text'] = error_message + ui_data['text']
        return ui_data
    
    # Добавляем постоянный негативный бонус к максимальному здоровью.
    char.setdefault('permanent_bonuses', {})
    char['permanent_bonuses']['max_health'] = char['permanent_bonuses'].get('max_health', 0) - health_cost
    
    # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
    # Мы УБРАЛИ строку, которая отнимала здоровье от ТЕКУЩЕГО запаса.
    # Теперь функция recalculate_stats() сама корректно скорректирует
    # текущее здоровье, если оно вдруг окажется выше нового максимума.
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---
    
    content_floor_num = run_state['floor']
    if char.get('run_type') == 'endless' and run_state['floor'] > 4:
        content_floor_num = 4
    
    floor_items = CONTENT[f"floor_{content_floor_num}"]['items']
    item_pool = floor_items.get('unique', []) + floor_items.get('legendary', [])
    if not item_pool: item_pool = floor_items.get('rare', [])
        
    chosen_item_template = copy.deepcopy(random.choice(item_pool))
    rarity = chosen_item_template.get('rarity', 'unique' if not any(i.get('rarity') == 'legendary' for i in item_pool) else 'legendary')
    chosen_item_template['rarity'] = rarity
    char['pending_loot'] = [chosen_item_template]
        
    message = f"🩸 Вы приносите жертву\\! Ваше тело слабеет, теряя *{health_cost}* максимального здоровья, но взамен алтарь дарует вам могущественный артефакт\\!"
    
    im.recalculate_stats(user_id, char) # Эта функция теперь сделает всё правильно.
    run_state['event_num'] += 1
    char['current_events'] = []
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
        
    loot_ui = ui.create_loot_choice_ui(run_state)
    return {'text': message + "\n\n" + loot_ui['text'], 'buttons': loot_ui['buttons']}


def _mystery_pact_with_shadow(user_id, run_state):
    positive_stats = [
        {'stat': 'crit_chance', 'value': 10, 'desc': "+10% к шансу крит. удара"},
        {'stat': 'attack', 'value': 12, 'desc': "+12 к атаке"},
        {'stat': 'double_damage_chance', 'value': 7, 'desc': "+7% к шансу двойного урона"},
    ]
    negative_stats = [
        {'stat': 'block_chance', 'value': -10, 'desc': "-10% к шансу блока"},
        {'stat': 'max_health', 'value': -40, 'desc': "-40 к макс. здоровью"},
        {'stat': 'defense', 'value': -15, 'desc': "-15% к защите"},
    ]
    
    pact_buff = random.choice(positive_stats)
    pact_debuff = random.choice(negative_stats)
    
    run_state['character']['pending_pact'] = {'buff': pact_buff, 'debuff': pact_debuff}
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], run_state['character'], run_state['floor_bosses'])
    
    return ui.create_pact_ui(pact_buff, pact_debuff)

def process_pact(user_id, run_state, accepted):
    from game_manager import continue_run
    char = run_state['character']
    pact = char.pop('pending_pact', None)
    
    if not pact:
         next_step = continue_run(user_id)
         return {'text': "Ошибка: предложение сделки истекло\\.", 'buttons': next_step['buttons']}
    
    if accepted:
        char.setdefault('permanent_bonuses', {})
        buff_stat = pact['buff']['stat']
        char['permanent_bonuses'][buff_stat] = char['permanent_bonuses'].get(buff_stat, 0) + pact['buff']['value']
        debuff_stat = pact['debuff']['stat']
        char['permanent_bonuses'][debuff_stat] = char['permanent_bonuses'].get(debuff_stat, 0) + pact['debuff']['value']
        
        message = "😈 Сделка заключена\\! Вы чувствуете, как новая сила наполняет вас, но за все приходится платить\\."
        im.recalculate_stats(user_id, char)
    else:
        message = "Вы отказываетесь от сделки\\. Тень отступает, разочарованно шипя\\."
        
    run_state['event_num'] += 1
    char['current_events'] = []
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    next_step = continue_run(user_id)
    return {'text': message + "\n\n" + next_step['text'], 'buttons': next_step['buttons']}

def _mystery_touch_of_kalandra(user_id, run_state):
    """(НОВОЕ) Предлагает трансформировать предмет."""
    return ui.create_kalandra_touch_ui(run_state['character'])

def process_kalandra_touch(user_id, run_state, slot):
    """(НОВОЕ) Обрабатывает трансформацию предмета."""
    from game_manager import continue_run
    char = run_state['character']
    item_to_sacrifice = char['equipment'].get(slot)

    if not item_to_sacrifice:
        next_step = continue_run(user_id)
        return {'text': "Ошибка: предмет не найден\\.", 'buttons': next_step['buttons']}

    rarity = item_to_sacrifice.get('rarity')
    original_name = item_to_sacrifice['name']
    
    char['equipment'][slot] = None
    
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Исправление KeyError и присвоение редкости ---
    content_floor_num = run_state['floor']
    if char.get('run_type') == 'endless' and run_state['floor'] > 4:
        content_floor_num = 4
    
    floor_items = CONTENT[f"floor_{content_floor_num}"]['items']
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    
    item_pool = [item for item in floor_items.get(rarity, []) if item['name'] != original_name]
    
    if not item_pool:
        gold_compensation = random.randint(100, 200) * run_state['floor']
        char['currency']['gold'] += gold_compensation
        message = f"🪞 Вы кладете *{escape_markdown(original_name)}* на поверхность\\. Он растворяется, но ничего не появляется взамен\\. Кажется, для этого предмета нет достойной замены\\. В качестве компенсации вы получаете *{gold_compensation}* 🪙 золота\\."
    else:
        new_item = copy.deepcopy(random.choice(item_pool))
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ: Явно присваиваем редкость новому предмету ---
        new_item['rarity'] = rarity
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---
        char['pending_loot'] = [new_item]
        message = f"🪞 Вы кладете *{escape_markdown(original_name)}* на поверхность\\. Он растворяется в ряби и преобразуется в новый предмет: *{escape_markdown(new_item['name'])}*\\!"

    im.recalculate_stats(user_id, char)
    run_state['event_num'] += 1
    char['current_events'] = []
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    
    if char['pending_loot']:
        loot_ui = ui.create_loot_choice_ui(run_state)
        return {'text': message + "\n\n" + loot_ui['text'], 'buttons': loot_ui['buttons']}
    else:
        next_step = continue_run(user_id)
        return {'text': message + "\n\n" + next_step['text'], 'buttons': next_step['buttons']}

def _mystery_cadiro(user_id, run_state):
    """Генерирует предложение от Кадиро."""
    floor = run_state['floor']
    char = run_state['character'] # Получаем персонажа для проверки

    # --- НАЧАЛО ИЗМЕНЕНИЙ: Надежное определение этажа для контента ---
    content_floor_num = floor
    if char.get('run_type') == 'endless' and floor > 4:
        content_floor_num = 4
    
    floor_items = CONTENT[f"floor_{content_floor_num}"]['items']
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    possible_rarities = []
    if floor_items.get('legendary'):
        possible_rarities.append(('legendary', 0.4))
    if floor_items.get('unique'):
        possible_rarities.append(('unique', 0.6))
    
    if not possible_rarities:
        chosen_rarity = 'rare'
        item_pool = floor_items.get('rare', [])
    else:
        rarities, weights = zip(*possible_rarities)
        chosen_rarity = random.choices(rarities, weights, k=1)[0]
        item_pool = floor_items.get(chosen_rarity, [])

    if not item_pool:
         item_pool = floor_items.get('magic', [])
         chosen_rarity = 'magic'

    item = copy.deepcopy(random.choice(item_pool))
    item['rarity'] = chosen_rarity
    
    base_price = 100
    if item.get('rarity') == 'unique': base_price = 30 + floor * 50
    if item.get('rarity') == 'legendary': base_price = 80 + floor * 60
    
    price = random.randint(int(base_price * 0.8), int(base_price * 1.2))
    
    char['cadiro_offer'] = {'item': item, 'price': price}
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    
    return ui.create_cadiro_offer_ui(item, price)

def process_cadiro_deal(user_id, run_state, accept):
    from game_manager import continue_run
    char = run_state['character']
    offer = char.get('cadiro_offer')
    
    message = ""
    if accept:
        if char['currency']['gold'] >= offer['price']:
            char['currency']['gold'] -= offer['price']
            char['pending_loot'] = [offer['item']]
            message = f"💰 «Мудрый выбор, изгнанник\\!» \\- говорит Кадиро, протягивая вам *{escape_markdown(offer['item']['name'])}*\\."
            
            run_state['event_num'] += 1
            char['current_events'] = []
            char.pop('cadiro_offer', None)
            db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
            
            loot_ui = ui.create_loot_choice_ui(run_state)
            return {'text': message + "\n\n" + loot_ui['text'], 'buttons': loot_ui['buttons']}
        else:
            message = f"💰 «У тебя не хватает монет, друг мой», \\- добродушно говорит Кадиро\\."
            ui_data = ui.create_cadiro_offer_ui(offer['item'], offer['price'])
            ui_data['text'] = message + "\n\n" + ui_data['text']
            return ui_data
    else:
        message = "«Возможно, в следующий раз», \\- говорит Кадиро и исчезает в облаке дыма\\."

    run_state['event_num'] += 1
    char['current_events'] = []
    char.pop('cadiro_offer', None)
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    
    next_step = continue_run(user_id)
    return {'text': message + "\n\n" + next_step['text'], 'buttons': next_step['buttons']}

def handle_mystery_decline(user_id, run_state):
    """(НОВОЕ) Обрабатывает отказ от действия в загадочной комнате."""
    from game_manager import continue_run
    char = run_state['character']
    
    message = "Вы решаете не рисковать и отступаете\\. Загадочная энергия в комнате рассеивается\\."
    
    # Завершаем событие и обновляем состояние
    run_state['event_num'] += 1
    char['current_events'] = []
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
    
    # Переходим к следующему выбору
    next_step = continue_run(user_id)
    return {'text': message + "\n\n" + next_step['text'], 'buttons': next_step['buttons']}