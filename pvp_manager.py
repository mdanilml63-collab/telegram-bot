# pvp_manager.py
import random
import copy
import database as db
import ui_components as ui
import game_manager as gm
import combat_manager as cm
import quest_manager
from telegram import Update
import perk_manager as perk_m 
import item_manager as im
from game_content import BASE_STATS, CONTENT
from utils import escape_markdown

def check_pvp_eligibility(user_id):
    """Проверяет, может ли игрок участвовать в PVP (нужна хотя бы 1 PVE победа)."""
    player_stats = db.get_player_info(user_id)
    return player_stats and player_stats['pve_wins'] > 0

# --- ИЗМЕНЕНИЕ: Логика победы в PVP и вызова чемпиона полностью переписана ---
def handle_pvp_victory(user_id, run_state, telegram_user: Update.effective_user):
    """
    Обрабатывает победу над боссом-игроком.
    """
    char = run_state['character']
    floor = run_state['floor']
    run_type = char.get('run_type') # <-- Получаем тип забега

    char_snapshot = copy.deepcopy(char)
    char_snapshot['stats']['health'] = char_snapshot['stats']['max_health']
    char_snapshot['stats']['energy_shield'] = char_snapshot['stats'].get('max_energy_shield', 0)
    
    # --- ИЗМЕНЕНИЕ: Сохраняем персонажа в правильный пул ---
    if run_type == 'hc_pvp':
        db.save_character_for_hc_pvp(user_id, floor, char_snapshot, telegram_user)
    else: # Обычный PVP
        db.save_character_for_pvp(user_id, floor, char_snapshot, telegram_user)
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---
    
    if floor < 4:
        pvp_xp_rewards = {1: 300, 2: 350, 3: 400}
        xp_reward = pvp_xp_rewards.get(floor, 0)
        
        victory_message = f"🎉 Вы одолели призрака игрока\\!"
        
        if xp_reward > 0:
            level_up_msg = db.add_xp_and_level_up(user_id, xp_reward)
            victory_message += f"\n\nВы получили *{xp_reward}* опыта за победу над боссом этажа\\."
            if level_up_msg:
                victory_message += f"\n\n{level_up_msg}"
        
        char['boss_defeated_flag'] = True
        loot = im.generate_loot(floor, char, 'босс')
        char['pending_loot'] = loot
        
        char.setdefault('ascendancy_points', 0)
        char['ascendancy_points'] += 1
        char.setdefault('chosen_ascendancy_passives', [])
        char['pending_victory_message'] = victory_message
        
        db.update_pve_run_state(user_id, floor, run_state['event_num'], char, run_state['floor_bosses'])
        
        return ui.create_ascendancy_choice_ui(run_state)

    else: # Победа на 4-м этаже
        char['stats']['health'] = char['stats']['max_health']
        char['stats']['energy_shield'] = char['stats'].get('max_energy_shield', 0)
        
        # --- ИЗМЕНЕНИЕ: Выбираем чемпиона из правильного пула ---
        champion = None
        if run_type == 'hc_pvp':
            quest_manager.update_quest_progress(user_id, 'pvp_full_run_win') # Можно использовать тот же квест
            champion = db.get_random_hc_champion(exclude_user_id=user_id)
            if not champion: champion = db.get_random_hc_champion()
        else:
            quest_manager.update_quest_progress(user_id, 'pvp_full_run_win')
            champion = db.get_random_champion(exclude_user_id=user_id)
            if not champion: champion = db.get_random_champion()
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---

        if not champion:
            # --- ИЗМЕНЕНИЕ: Добавляем в правильный пул ---
            if run_type == 'hc_pvp':
                db.add_new_hc_champion(user_id, char)
                db.increment_pvp_wins(user_id) # Используем старый счетчик побед для квестов
            else:
                db.add_new_champion(user_id, char)
                db.increment_pvp_wins(user_id)
            # --- КОНЕЦ ИЗМЕНЕНИЯ ---
            
            db.delete_pve_run(user_id)
            champion_title = "ПЕРВЫЙ ХАРДКОРНЫЙ ЧЕМПИОН" if run_type == 'hc_pvp' else "ПЕРВЫЙ ЧЕМПИОН"
            return {
                'text': f"🏆 *ВЫ {champion_title}\\!* 🏆\n\nВы прошли все испытания и заняли пустующий трон\\!",
                'buttons': [[{'text': 'В главное меню', 'callback_data': 'back_to_main_menu'}]]
            }
        else:
            run_state['floor_bosses']['champion_opponent'] = champion
            db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
            champion_title = "ХАРДКОРНОМУ ЧЕМПИОНУ" if run_type == 'hc_pvp' else "ЧЕМПИОНУ"
            return {
                'text': (f"👑 *ВЫЗОВ {champion_title}* 👑\n\nВы одолели последнего стража и восстановили силы\\! Перед вами \\- трон, который занимает "
                         f"чемпион `{escape_markdown(champion['username'])}`\\. Вы готовы бросить ему вызов?"),
                'buttons': [[{'text': f'⚔️ Бросить вызов', 'callback_data': 'pvp_challenge_champion'}]]
            }


def initiate_champion_fight(user_id, run_state):
    """Создает бой с текущим чемпионом (обычным или хардкорным)."""
    quest_manager.update_quest_progress(user_id, 'pvp_challenge_champion')
    champion_opponent = run_state['floor_bosses'].get('champion_opponent')
    run_type = run_state['character'].get('run_type')

    if not champion_opponent:
        return {'text': "Ошибка: не найден чемпион для боя\\.", 'buttons': [[{'text': 'В главное меню', 'callback_data': 'back_to_main_menu'}]]}

    # --- ИЗМЕНЕНИЕ: Определяем тип чемпиона ---
    monster_type = 'hc_champion' if run_type == 'hc_pvp' else 'чемпион'
    monster_name_prefix = "ХК Чемпион" if run_type == 'hc_pvp' else "Чемпион"
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    monster_data = {
        'name': f"{monster_name_prefix} {champion_opponent['username']}",
        'type': monster_type,
        'stats': champion_opponent['character']['stats'],
        'equipment': champion_opponent['character']['equipment'],
        'owner_id': champion_opponent['player_id'],
        'champion_id': champion_opponent['champion_id']
    }

    run_state['character']['combat'] = {
        'monster': monster_data,
        'log': ['Бой за звание чемпиона начинается\\!']
    }
    
    db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], run_state['character'], run_state['floor_bosses'])
    return ui.create_fight_ui(run_state['character'])

# --- ИЗМЕНЕНИЕ: Логика обработки результата боя полностью переписана ---
def process_champion_fight_result(challenger_id, challenger_char_state, champion_owner_id, champion_id_in_fight, is_challenger_win, context):
    """Обрабатывает результат боя за чемпионство и отправляет анонс, если нужно."""
    # --- ИЗМЕНЕНИЕ: Определяем тип чемпиона по состоянию персонажа претендента ---
    monster_type_in_combat = challenger_char_state['combat']['monster']['type']
    is_hc_fight = monster_type_in_combat == 'hc_champion'
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---
    
    message_to_challenger = ""

    if is_challenger_win:
        quest_manager.update_quest_progress(challenger_id, 'pvp_become_champion')
        
        champion_snapshot = copy.deepcopy(challenger_char_state)
        champion_snapshot['stats']['health'] = champion_snapshot['stats']['max_health']
        champion_snapshot['stats']['energy_shield'] = champion_snapshot['stats'].get('max_energy_shield', 0)

        # --- ИЗМЕНЕНИЕ: Разная логика для ХК и обычного режима ---
        if is_hc_fight:
            db.add_new_hc_champion(challenger_id, champion_snapshot)
            db.delete_hc_champion(champion_id_in_fight)
            db.increment_pvp_wins(challenger_id, 1) # Общий счетчик для квестов
            message_to_challenger = "🏆 *НОВЫЙ ХАРДКОРНЫЙ ЧЕМПИОН\\!* 🏆\n\nВы одолели сильнейшего и заняли трон\\!"
        else:
            message_to_challenger = "🏆 *НОВЫЙ ЧЕМПИОН ДОБАВЛЕН\\!* 🏆\n\nВы победили и еще один ваш могущественный призрак занял место в пантеоне чемпионов\\!"
            db.handle_champion_victory_updates(
                challenger_id=challenger_id,
                champion_snapshot=champion_snapshot,
                defeated_champion_id=champion_id_in_fight,
                xp_reward=1000 # Опыт дается только за обычного чемпиона
            )
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---

        db.delete_pve_run(challenger_id)
        
    else: # Претендент проиграл
        if challenger_id != champion_owner_id:
            quest_manager.update_quest_progress(champion_owner_id, 'pvp_defend_champion')
            # --- ИЗМЕНЕНИЕ: Разная награда за защиту ---
            if is_hc_fight:
                db.increment_hc_champion_passive_win(champion_id_in_fight, champion_owner_id)
            else:
                db.increment_champion_passive_win(champion_id_in_fight, champion_owner_id)
            # --- КОНЕЦ ИЗМЕНЕНИЯ ---
            
        champion_title = "Действующий Хардкорный Чемпион" if is_hc_fight else "Действующий Чемпион"
        message_to_challenger = f"💀 *ВЫ ПРОИГРАЛИ* 💀\n\n{champion_title} оказался сильнее\\. Возможно, в другой раз удача улыбнется вам\\."
        db.delete_pve_run(challenger_id)

    return {
        'text': message_to_challenger,
        'buttons': [[{'text': 'В главное меню', 'callback_data': 'back_to_main_menu'}]]
    }

