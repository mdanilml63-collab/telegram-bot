# world_boss_manager.py
import random
import time
import json
import datetime
import pytz
import copy
import database as db
import item_manager as im
import ui_components as ui
from utils import escape_markdown

# --- Конфигурация Боссов ---
BOSS_TEMPLATES = [
    {
        'name': "Пожиратель Миров",
        'stats': {'health': 8500, 'max_health': 8500, 'attack': 45, 'defense': 25, 'block_chance': 10, 'dodge_chance': 10, 'crit_chance': 10}
    },
    {
        'name': "Древний Ужас из Глубин",
        'stats': {'health': 9000, 'max_health': 9000, 'attack': 40, 'defense': 25, 'block_chance': 15, 'dodge_chance': 5, 'crit_chance': 10}
    },
    {
        'name': "Пылающий Колосс",
        'stats': {'health': 8000, 'max_health': 8000, 'attack': 50, 'defense': 25, 'block_chance': 5, 'dodge_chance': 10, 'crit_chance': 15}
    }
]

BOSS_EVENT_DURATION = 24 * 60 * 60  # 24 часа в секундах
PLAYER_COOLDOWN = 4 * 60 * 60     # 4 часа в секундах
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

def get_boss_status(user_id):
    """
    Получает текущее состояние Мирового Босса и информацию об игроке.
    Автоматически завершает старые ивенты и начинает новые по расписанию.
    Возвращает словарь со всеми необходимыми данными для UI.
    """
    boss_data = db.get_world_boss()
    now_ts = int(time.time())

    # Шаг 1: Если босс существует и его время вышло, деактивируем его.
    if boss_data and boss_data['is_active'] and now_ts > boss_data['end_time']:
        boss_data['is_active'] = False
        db.update_world_boss(boss_data)
        print(f"Ивент босса '{boss_data['name']}' завершен по времени.")

    # Шаг 2: Проверяем, нужно ли спавнить нового босса.
    if not boss_data or not boss_data['is_active']:
        # Вычисляем время спавна СЕГОДНЯ в 20:00 по МСК
        now_moscow = datetime.datetime.now(MOSCOW_TZ)
        todays_spawn_time_moscow = now_moscow.replace(hour=20, minute=0, second=0, microsecond=0)
        todays_spawn_ts = int(todays_spawn_time_moscow.astimezone(pytz.utc).timestamp())

        # Условие для спавна:
        # 1. Текущее время больше или равно времени спавна сегодня.
        # 2. ИЛИ босса нет, ИЛИ время спавна последнего босса было ДО сегодняшнего спавна.
        should_spawn = (now_ts >= todays_spawn_ts) and (not boss_data or boss_data['spawn_time'] < todays_spawn_ts)
        
        if should_spawn:
            spawn_new_boss()
            boss_data = db.get_world_boss()  # Перезагружаем данные, так как появился новый босс.

    # Шаг 3: Собираем информацию для UI с актуальными данными.
    player_data = db.get_player_boss_damage(user_id)
    
    status = {
        'boss': boss_data,
        'player': player_data,
        'leaderboard': None,
        'cooldown_left': 0
    }
    
    if player_data:
        cooldown_end_time = player_data['last_attack_time'] + PLAYER_COOLDOWN
        if time.time() < cooldown_end_time:
            status['cooldown_left'] = cooldown_end_time - time.time()

    if boss_data and not boss_data['is_active']:
        status['leaderboard'] = db.get_world_boss_leaderboard()

    return status

def spawn_new_boss():
    """
    Создает нового босса для самого последнего временного окна (20:00 МСК).
    """
    now_moscow = datetime.datetime.now(MOSCOW_TZ)
    
    # Определяем правильную дату спавна. Если сейчас раньше 20:00, то последний спавн был вчера.
    spawn_date_moscow = now_moscow.replace(hour=20, minute=0, second=0, microsecond=0)
    if now_moscow < spawn_date_moscow:
        spawn_date_moscow -= datetime.timedelta(days=1)
        
    spawn_ts = int(spawn_date_moscow.astimezone(pytz.utc).timestamp())

    boss_template = copy.deepcopy(random.choice(BOSS_TEMPLATES))
    
    new_boss = {
        'boss_id': 1,
        'name': boss_template['name'],
        'stats': boss_template['stats'],
        'current_hp': boss_template['stats']['max_health'],
        'spawn_time': spawn_ts,
        'end_time': spawn_ts + BOSS_EVENT_DURATION,
        'is_active': True,
        'is_defeated': False
    }

    db.update_world_boss(new_boss)
    db.reset_world_boss_participants()
    print(f"Новый мировой босс '{new_boss['name']}' был создан для ивента, начавшегося в {spawn_date_moscow.strftime('%Y-%m-%d %H:%M:%S')} МСК.")


def start_boss_fight(user_id):
    """
    Инициирует бой игрока с мировым боссом.
    """
    boss_status = get_boss_status(user_id)

    if not boss_status['boss'] or not boss_status['boss']['is_active']:
        return {'text': "Битва с боссом сейчас неактивна\\.", 'buttons': [[{'text': '⬅️ Назад', 'callback_data': 'menu_world_boss'}]]}

    if boss_status['cooldown_left'] > 0:
        return {'text': "Вы ранены и не можете атаковать босса\\.", 'buttons': [[{'text': '⬅️ Назад', 'callback_data': 'menu_world_boss'}]]}

    player_stats = im.get_base_stats_with_perks(user_id)
    char_for_combat = {
        'user_id': user_id, 'name': 'Игрок', 'stats': player_stats,
        'equipment': {}, 'buffs': [], 'permanent_bonuses': {}
    }

    boss_stats_for_fight = boss_status['boss']['stats'].copy()
    boss_stats_for_fight['health'] = boss_status['boss']['current_hp']

    monster_object_for_combat = {
        'name': boss_status['boss']['name'], 'stats': boss_stats_for_fight,
        'equipment': {}, 'type': 'world_boss'
    }
    
    char_for_combat['combat'] = {
        'monster': monster_object_for_combat,
        'log': [f'Вы вступаете в бой с могущественным {escape_markdown(boss_status["boss"]["name"])}\\!'],
        'last_turn_log': {}, 'is_world_boss': True
    }
    
    # Возвращаем и UI, и состояние персонажа
    result_ui = ui.create_fight_ui(char_for_combat)
    result_ui['character'] = char_for_combat
    return result_ui


def process_boss_combat_turn(user_id, char_state):
    """
    Обрабатывает один ход боя с Мировым Боссом.
    """
    from combat_manager import _calculate_damage, _apply_damage
    
    boss = db.get_world_boss()
    if not boss or not boss['is_active']:
        return {'ui': {'text': "Битва с боссом окончена\\.", 'buttons': [[{'text': '⬅️ Назад', 'callback_data': 'menu_world_boss'}]]}, 'status': 'defeat'}

    monster_obj = {'name': boss['name'], 'stats': boss['stats'], 'equipment': {}}
    player_obj = {'name': 'Игрок', **char_state}
    
    last_turn_log = {'player': [], 'monster': []}
    
    # Ход игрока
    # --- ИСПРАВЛЕНИЕ ЗДЕСЬ: Принимаем 5 значений вместо 4 ---
    damage_dealt, player_log, _, _, _ = _calculate_damage(player_obj, monster_obj)
    last_turn_log['player'].append(player_log)
    
    total_damage_dealt = 0
    if damage_dealt > 0:
        total_damage_dealt += damage_dealt
        boss['current_hp'] = max(0, boss['current_hp'] - damage_dealt)
        db.update_world_boss(boss)
        db.update_player_boss_damage(user_id, damage_dealt)

    if boss['current_hp'] <= 0:
        boss['is_defeated'] = True
        boss['is_active'] = False
        db.update_world_boss(boss)
        return {
            'ui': {
                'text': f"💥 Вы нанесли сокрушительный удар на *{total_damage_dealt}* урона\\!\n\n"
                        f"👑 *ПОБЕДА\\!* 👑\n\nОбщими усилиями вы одолели *{escape_markdown(boss['name'])}*\\! "
                        "Возвращайтесь в меню ивента, чтобы увидеть свой вклад и забрать награду\\.",
                'buttons': [[{'text': '🏆 К итогам', 'callback_data': 'menu_world_boss'}]]
            },
            'status': 'victory'
        }

    # Ход босса
    # --- ИСПРАВЛЕНИЕ ЗДЕСЬ: Принимаем 5 значений вместо 4 ---
    damage_taken, monster_log, _, _, _ = _calculate_damage(monster_obj, player_obj)
    last_turn_log['monster'].append(monster_log)
    char_state['stats'] = _apply_damage(char_state, damage_taken)['stats']

    if char_state['stats']['health'] <= 0:
        db.set_player_boss_cooldown(user_id)
        return {
            'ui': {
                'text': f"💥 Вы успели нанести *{total_damage_dealt}* урона, но босс оказался сильнее\\.\n\n"
                        f"💀 *Вы повержены\\!* 💀\n\nВы сможете снова атаковать босса через 4 часа\\. "
                        "Ваш вклад в битву засчитан\\.",
                'buttons': [[{'text': '⬅️ Назад', 'callback_data': 'menu_world_boss'}]]
            },
            'status': 'defeat'
        }
    
    char_state['combat']['monster']['stats']['health'] = boss['current_hp']
    char_state['combat']['last_turn_log'] = last_turn_log
    
    return {
        'ui': ui.create_fight_ui(char_state),
        'char_state': char_state,
        'status': 'ongoing'
    }



def claim_reward(user_id):
    """
    Выдает награду игроку в зависимости от его места в топе урона.
    """
    boss_status = get_boss_status(user_id)
    
    if not boss_status['boss'] or boss_status['boss']['is_active']:
        return "Награду можно забрать только после завершения события\\."
        
    if boss_status['player'] and boss_status['player']['reward_claimed']:
        return "Вы уже получили свою награду за этого босса\\."
        
    if not boss_status['player'] or boss_status['player']['damage_dealt'] == 0:
        return "Вы не участвовали в битве и не можете получить награду\\."

    leaderboard = db.get_world_boss_leaderboard()
    player_rank = -1
    for i, (p_id, _, _) in enumerate(leaderboard):
        if p_id == user_id:
            player_rank = i + 1
            break
            
    if player_rank == -1:
        return "Ошибка: не удалось найти вас в рейтинге участников\\."

    divine_reward = 0
    mirror_reward = 0
    
    if player_rank == 1:
        divine_reward = 10
        mirror_reward = 1
    elif player_rank in [2, 3]:
        divine_reward = 5
    elif 4 <= player_rank <= 10:
        divine_reward = 3
    else: # Награда за участие
        # Дадим немного хаосов из рыбалки в качестве утешительного приза
        chaos_reward = random.randint(500, 1500)
        db.add_fishing_chaos(user_id, chaos_reward)
        db.set_player_reward_claimed(user_id)
        return f"Спасибо за участие\\! Ваша награда: {chaos_reward} 🟢 Хаос Орбов\\."

    db.add_rewards(user_id, divine_reward, mirror_reward)
    db.set_player_reward_claimed(user_id)

    reward_text = f"Ваша награда за {player_rank} место:\n"
    if divine_reward > 0:
        reward_text += f"💎 *{divine_reward}* Divine Orb{'s' if divine_reward > 1 else ''}\n"
    if mirror_reward > 0:
        reward_text += f"🪞 *{mirror_reward}* Mirror of Kalandra"
        
    return reward_text

def get_next_spawn_timestamp():
    """Просто рассчитывает и возвращает временную метку следующего спавна босса."""
    now_utc = datetime.datetime.now(pytz.utc)
    now_moscow = now_utc.astimezone(MOSCOW_TZ)
    
    spawn_time_moscow = now_moscow.replace(hour=20, minute=0, second=0, microsecond=0)
    if now_moscow >= spawn_time_moscow:
        spawn_time_moscow += datetime.timedelta(days=1)
        
    return int(spawn_time_moscow.astimezone(pytz.utc).timestamp())