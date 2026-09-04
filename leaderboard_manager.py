import sqlite3
import datetime
import pytz
from database import DB_NAME, add_rewards, has_claimed_reward, mark_reward_as_claimed, get_pve_leaderboard, get_pvp_leaderboard

def get_fishing_leaderboard(limit=10):
    """Возвращает топ игроков по уровню рыбалки."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT fs.user_id, p.username, fs.level
            FROM fishing_stats fs
            JOIN players p ON fs.user_id = p.user_id
            ORDER BY fs.level DESC, fs.xp DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
def get_harvest_leaderboard(limit=10):
    """Возвращает топ игроков по уровню Харвеста."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT hs.user_id, p.username, hs.level
            FROM harvest_stats hs
            JOIN players p ON hs.user_id = p.user_id
            ORDER BY hs.level DESC, hs.xp DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
def get_endless_leaderboard(limit=10):
    """Возвращает топ игроков по максимальному этажу в Бесконечном Забеге."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT erl.user_id, p.username, erl.max_floor
            FROM endless_run_leaderboard erl
            JOIN players p ON erl.user_id = p.user_id
            WHERE erl.max_floor > 0
            ORDER BY erl.max_floor DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
def get_level_leaderboard(limit=10):
    """Возвращает топ игроков по уровню персонажа."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.user_id, p.username, p.level
            FROM players p
            WHERE p.level > 1
            ORDER BY p.level DESC, p.xp DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    

REWARDS = {
    1: 25,
    2: 15,
    3: 10,
    4: 5,
    5: 5,
    6: 5,
    7: 5,
    8: 5,
    9: 5,
    10: 5
}

def get_reward_period():
    """Определяет текущий и предыдущий месяц для наград."""
    now = datetime.datetime.now(pytz.utc)
    # Предыдущий месяц (за который выдаются награды)
    first_day_of_current_month = now.replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - datetime.timedelta(days=1)
    previous_month_str = last_day_of_previous_month.strftime('%Y-%m')
    
    return previous_month_str

def claim_all_monthly_rewards(user_id):
    """
    Проверяет все лидерборды за предыдущий месяц и начисляет награды, если они еще не были получены.
    """
    month_to_claim = get_reward_period()
    total_mirrors_earned = 0
    rewards_log = []

    leaderboard_functions = {
        'pve': get_pve_leaderboard,
        'pvp': get_pvp_leaderboard,
        'level': get_level_leaderboard,
        'endless': get_endless_leaderboard,
        'fishing': get_fishing_leaderboard,
        'harvest': get_harvest_leaderboard
    }
    
    leaderboard_names = {
        'pve': "PVE", 'pvp': "PVP", 'level': "Уровню", 'endless': "Бесконечному забегу",
        'fishing': "Рыбалке", 'harvest': "Харвесту"
    }

    for lb_type, lb_func in leaderboard_functions.items():
        if has_claimed_reward(user_id, month_to_claim, lb_type):
            continue

        board = lb_func()
        rank = -1
        for i, (p_id, _, _) in enumerate(board):
            if p_id == user_id:
                rank = i + 1
                break
        
        if 0 < rank <= 10:
            reward = REWARDS.get(rank, 0)
            if reward > 0:
                total_mirrors_earned += reward
                mark_reward_as_claimed(user_id, month_to_claim, lb_type)
                rewards_log.append(f"Топ-{rank} по {leaderboard_names[lb_type]}: +{reward} 🪞")

    if total_mirrors_earned > 0:
        add_rewards(user_id, divines=0, mirrors=total_mirrors_earned)
        summary = "\\n".join(rewards_log)
        return f"Вы получили награды за прошлый месяц:\\n\\n{summary}\\n\\nИтого: +{total_mirrors_earned} 🪞"
    else:
        return "Не найдено доступных наград для получения\\. Возможно, вы не попали в топ\\-10 или уже забрали награду\\."