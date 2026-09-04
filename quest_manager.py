# quest_manager.py
import random
import time
import json
import database as db
from utils import escape_markdown

# Пул всех возможных заданий
REROLL_COST = 10000

QUEST_POOL = {
    'pve': [
        {'id': 'pve_kill_common', 'desc': 'Победить 50 обычных монстров', 'target': 50},
        {'id': 'pve_kill_rare', 'desc': 'Одолеть 25 элитных монстров', 'target': 25},
        {'id': 'pve_kill_boss', 'desc': 'Победить 10 боссов этажа', 'target': 10},
        {'id': 'pve_open_chests', 'desc': 'Открыть 25 сундуков', 'target': 25},
        {'id': 'pve_use_shrines', 'desc': 'Активировать 25 святилищ', 'target': 25},
        {'id': 'pve_corrupt_item', 'desc': 'Осквернить предмет у Алтаря', 'target': 10},
        {'id': 'pve_win_trial', 'desc': 'Успешно пройти Испытание Возвышения', 'target': 10},
        {'id': 'pve_visit_smith', 'desc': 'Воспользоваться услугами кузнеца', 'target': 25},
        {'id': 'pve_visit_healer', 'desc': 'Восстановить здоровье у лекаря', 'target': 30},
        {'id': 'pve_find_rare_item', 'desc': 'Найти редкий предмет (желтый)', 'target': 100},
        {'id': 'pve_find_unique_item', 'desc': 'Найти уникальный предмет (оранжевый)', 'target': 50},
        {'id': 'pve_defeat_exile', 'desc': 'Победить Загадочного Изгнанника', 'target': 20},
        {'id': 'pve_complete_floor', 'desc': 'Завершить этаж (победить босса)', 'target': 10},
        {'id': 'pve_full_run_win', 'desc': 'Завершить полный PVE забег', 'target': 3},
        {'id': 'pve_spend_gold', 'desc': 'Потратить 1000 золота за забег', 'target': 1000},
    ],
    'pvp': [
        {'id': 'pvp_ghost_wins', 'desc': 'Победить 10 призраков игроков', 'target': 10},
        {'id': 'pvp_full_run_win', 'desc': 'Выиграть полный PVP забег (дойти до Чемпиона)', 'target': 3},
        {'id': 'pvp_challenge_champion', 'desc': 'Бросить вызов Чемпиону', 'target': 2},
        {'id': 'pvp_become_champion', 'desc': 'Стать новым Чемпионом', 'target': 1},
        {'id': 'pvp_defend_champion', 'desc': 'Успешно защитить титул Чемпиона (пассивно)', 'target': 1},
    ],
    'fishing': [
        {'id': 'fish_any', 'desc': 'Поймать 50 рыб', 'target': 50},
        {'id': 'fish_rare', 'desc': 'Поймать 25 редких рыб', 'target': 25},
        {'id': 'fish_heavy', 'desc': 'Поймать рыбу весом более 7 кг', 'target': 10},
        {'id': 'fish_sell_chaos', 'desc': 'Заработать 10000 Хаос Орбов на продаже рыбы', 'target': 10000},
        {'id': 'fish_level_up', 'desc': 'Получить уровень рыбалки', 'target': 5},
    ]
}

def _generate_new_quests(user_id):
    """Генерирует 5 случайных квестов для игрока и сохраняет их."""
    full_pool = QUEST_POOL['pve'] + QUEST_POOL['pvp'] + QUEST_POOL['fishing']
    chosen_quests_templates = random.sample(full_pool, 5)
    
    quests_data = []
    for template in chosen_quests_templates:
        quests_data.append({
            'id': template['id'],
            'desc': template['desc'],
            'progress': 0,
            'target': template['target'],
            'reward_claimed': False
        })
        
    reset_time = int(time.time()) + 24 * 60 * 60  # Сброс через 24 часа
    
    with db.sqlite3.connect(db.DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO daily_quests (user_id, quests_data, reset_time) VALUES (?, ?, ?)",
            (user_id, json.dumps(quests_data), reset_time)
        )
    
    return quests_data, reset_time

def get_player_quests(user_id):
    """Получает квесты игрока. Если их нет или они устарели - генерирует новые."""
    with db.sqlite3.connect(db.DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT quests_data, reset_time FROM daily_quests WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

    if not row or time.time() > row[1]:
        # Если записей нет или время сброса прошло, генерируем новые
        quests_data, reset_time = _generate_new_quests(user_id)
        return json.loads(json.dumps(quests_data)), reset_time # Возвращаем свежие данные
    
    return json.loads(row[0]), row[1]


def update_quest_progress(user_id, quest_id_to_update, value=1):
    """Обновляет прогресс для всех активных квестов с указанным ID."""
    quests_data, reset_time = get_player_quests(user_id)
    
    updated = False
    for quest in quests_data:
        # Обновляем все квесты, которые соответствуют ID и еще не выполнены
        if quest['id'] == quest_id_to_update and quest['progress'] < quest['target']:
            quest['progress'] += value
            # Убедимся, что прогресс не превышает цель
            quest['progress'] = min(quest['progress'], quest['target'])
            updated = True
            
    if updated:
        with db.sqlite3.connect(db.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE daily_quests SET quests_data = ? WHERE user_id = ?",
                (json.dumps(quests_data), user_id)
            )

def claim_reward(user_id, quest_index):
    """Игрок забирает награду за выполненный квест."""
    quests_data, reset_time = get_player_quests(user_id)
    
    if quest_index >= len(quests_data):
        return False, "Ошибка: неверный индекс квеста\\."

    quest = quests_data[quest_index]

    if quest['progress'] < quest['target']:
        return False, "Квест еще не выполнен\\."
    
    if quest['reward_claimed']:
        return False, "Награда уже была получена\\."

    # Начисляем награду и помечаем квест как выполненный
    quest['reward_claimed'] = True
    
    with db.sqlite3.connect(db.DB_NAME) as conn:
        cursor = conn.cursor()
        # Начисляем награду
        cursor.execute("UPDATE players SET divine_orbs = divine_orbs + 1 WHERE user_id = ?", (user_id,))
        # Обновляем состояние квестов
        cursor.execute("UPDATE daily_quests SET quests_data = ? WHERE user_id = ?", (json.dumps(quests_data), user_id))
        conn.commit()

    return True, "Вы получили 1 💎 Divine Orb\\!"

def reroll_quests(user_id):
    """
    Меняет текущие квесты игрока на новые за хаос орбы.
    """
    fishing_stats = db.get_fishing_stats(user_id)
    
    if fishing_stats.get('chaos_orbs', 0) < REROLL_COST:
        return False, f"Недостаточно хаос орбов для смены заданий\\! Нужно {REROLL_COST} 🟢\\."
        
    # Списываем валюту
    fishing_stats['chaos_orbs'] -= REROLL_COST
    db.update_fishing_stats(user_id, fishing_stats)
    
    # Генерируем новые квесты
    _generate_new_quests(user_id)
    
    return True, "Ваши ежедневные задания были успешно обновлены\\!"