# divination_card_manager.py
import random
import database as db
from game_content import DIVINATION_CARDS
from utils import escape_markdown

def handle_card_drop(user_id, monster_type):
    """
    Обрабатывает шанс выпадения и выбор гадальной карты после победы.
    Возвращает имя выпавшей карты или None.
    """
    drop_chance_map = {
        'бой_обычный': 0.04,  # 4%
        'бой_редкий': 0.06,   # 6%
        'лутгоблин': 0.07,    # 7%
        'изгнанник': 0.07,     # 7%
        'босс': 0.20,          # 20%
    }
    
    # Шаг 1: Проверяем, выпала ли карта вообще
    chance = drop_chance_map.get(monster_type, 0)
    if random.random() > chance:
        return None

    # Шаг 2: Если карта выпала, определяем, какая именно, на основе веса
    cards = list(DIVINATION_CARDS.keys())
    weights = [DIVINATION_CARDS[card_id]['weight'] for card_id in cards]
    
    # random.choices возвращает список, поэтому берем первый элемент [0]
    chosen_card_id = random.choices(cards, weights, k=1)[0]
    
    # Добавляем карту в инвентарь игрока
    db.add_divination_card(user_id, chosen_card_id)
    
    return DIVINATION_CARDS[chosen_card_id]['name']

def exchange_card_set(user_id, card_id):
    """
    Обрабатывает обмен полного сета карт на награду.
    """
    player_cards = db.get_player_cards(user_id)
    card_info = DIVINATION_CARDS[card_id]
    
    current_amount = player_cards.get(card_id, 0)
    required_amount = card_info['stack_size']

    if current_amount < required_amount:
        return False, "У вас недостаточно карт для обмена\\."

    # Забираем карты
    db.remove_card_stack(user_id, card_id, required_amount)
    
    # Выдаем награду
    reward_type = card_info['reward_type']
    reward_value = card_info['reward_value']

    if reward_type == 'divine_shards':
        stats = db.get_fishing_stats(user_id)
        stats['divine_shards'] = stats.get('divine_shards', 0) + reward_value
        db.update_fishing_stats(user_id, stats)
        reward_text = f"{reward_value} Осколков Божественности"
    elif reward_type == 'divine_orbs':
        db.add_rewards(user_id, divines=reward_value, mirrors=0)
        reward_text = f"{reward_value} 💎 Divine Orbs"
    elif reward_type == 'mirrors':
        db.add_rewards(user_id, divines=0, mirrors=reward_value)
        reward_text = f"{reward_value} 🪞 Mirror of Kalandra"
    else:
        return False, "Неизвестный тип награды\\."

    return True, f"Вы обменяли сет '{escape_markdown(card_info['name'])}' и получили: {reward_text}\\!"