# mtx_manager.py
import database as db
from utils import escape_markdown

# --- Каталог всех доступных MTX ---
# ID предмета - ключ. Это позволяет легко добавлять новые предметы.
MTX_CATALOG = {
    # Divine Orb Tier
    'title_ascended': {'name': "Титул 'Вознесшийся'", 'cost': 5, 'currency': 'divine_orbs', 'type': 'title', 'value': '*Вознесшийся*'},
    'suffix_spark':   {'name': "Эмодзи суффикс 'Искра'", 'cost': 10, 'currency': 'divine_orbs', 'type': 'suffix', 'value': '✨'},
    'highlight_italic':{'name': 'Выделение в Лидерборде', 'cost': 15, 'currency': 'divine_orbs', 'type': 'highlight', 'value': 'italic'},

    # Mirror Tier
    'prefix_crown':   {'name': 'Королевский Префикс', 'cost': 3, 'currency': 'mirrors', 'type': 'prefix', 'value': '👑'},
    'color_azure':    {'name': "Симуляция цвета 'Лазурит'", 'cost': 8, 'currency': 'mirrors', 'type': 'color', 'value': '🟦'},
    'greeting_legend':{'name': 'Персональное приветствие', 'cost': 15, 'currency': 'mirrors', 'type': 'greeting', 'value': True},
    'announce_fame':  {'name': "Анонс в 'Зале Славы'", 'cost': 25, 'currency': 'mirrors', 'type': 'announce', 'value': True},
}

def get_player_mtx_effects(user_id):
    """Получает из БД купленные MTX и возвращает словарь с активными эффектами."""
    player_info = db.get_player_info(user_id)
    if not player_info:
        return {}
        
    unlocked_ids = player_info.get('unlocked_mtx', [])
    effects = {}
    for mtx_id in unlocked_ids:
        if mtx_id in MTX_CATALOG:
            mtx_data = MTX_CATALOG[mtx_id]
            effects[mtx_data['type']] = mtx_data['value']
    return effects

def format_username(user_id, username):
    """Форматирует имя пользователя на основе его купленных MTX."""
    effects = get_player_mtx_effects(user_id)
    safe_username = escape_markdown(username)
    
    if 'title' in effects:
        safe_username = f"{effects['title']} {safe_username}"
    if 'suffix' in effects:
        safe_username = f"{safe_username} {effects['suffix']}"
    if 'prefix' in effects:
        safe_username = f"{effects['prefix']} {safe_username}"
    if 'color' in effects:
        safe_username = f"{effects['color']} {safe_username} {effects['color']}"
        
    return safe_username

def format_leaderboard_entry(formatted_name, wins, user_id):
    effects = get_player_mtx_effects(user_id)
    name_part = f"`{formatted_name}`"
    if effects.get('highlight') == 'italic':
        name_part = f"_{formatted_name}_" # Курсив для MarkdownV2 это _текст_
    return f"{name_part} \\- {wins} побед" # ИСПРАВЛЕНО