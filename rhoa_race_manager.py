# rhoa_race_manager.py
import random
import database as db
from utils import escape_markdown
from game_content import RHOA_NAMES

RACE_CAPACITY = 4
WIN_MULTIPLIER = 4 # Множитель выигрыша

def _format_race_results(race_id, bets, winning_rhoa_id):
    """Форматирует текстовое представление результатов гонки."""
    winning_rhoa_name = RHOA_NAMES[winning_rhoa_id]
    
    results_text = f"🏁 *Забег Роа \\#{race_id} завершен\\!* 🏁\n\nПобедитель: 🏆 *{escape_markdown(winning_rhoa_name)}* \\(Роа \\#{winning_rhoa_id}\\)\n\n"
    results_text += "*Результаты игроков:*\n"

    for user_id, username, rhoa_id, bet_amount, currency_type in bets:
        currency_symbol = "💎" if currency_type == 'divine_orbs' else "🪞"
        if rhoa_id == winning_rhoa_id:
            winnings = bet_amount * WIN_MULTIPLIER
            results_text += f"✅ {escape_markdown(username)} поставил на победителя и выиграл *{winnings}* {currency_symbol}\\!\n"
        else:
            results_text += f"❌ {escape_markdown(username)} поставил на Роа \\#{rhoa_id} и проиграл *{bet_amount}* {currency_symbol}\\.\n"
    
    return results_text

def get_race_status(user_id):
    """Собирает всю информацию о текущем состоянии гонок для UI."""
    race_id, current_bets = db.get_current_race_bets()
    player_in_current_race = any(user_id == bet[0] for bet in current_bets)
    
    return {
        'race_id': race_id,
        'current_bets': current_bets,
        'player_in_current_race': player_in_current_race,
        'is_full': len(current_bets) >= RACE_CAPACITY
    }

def place_bet(user_id, username, rhoa_id, amount, currency):
    """Обрабатывает ставку игрока."""
    player_info = db.get_player_info(user_id)
    if not player_info or player_info.get(currency, 0) < amount:
        return False, f"Недостаточно средств для ставки!"

    status = get_race_status(user_id)
    if status['player_in_current_race']:
        return False, "Вы уже сделали ставку в этом забеге."
    if status['is_full']:
        return False, "Этот забег уже заполнен, обновите меню."

    db.add_rewards(user_id, divines=-amount if currency == 'divine_orbs' else 0, mirrors=-amount if currency == 'mirrors' else 0)
    db.add_bet_to_race(status['race_id'], user_id, username, rhoa_id, amount, currency)
    
    # Обновляем статус после нашей ставки
    current_bets_after_bet = status['current_bets'] + [(user_id, username, rhoa_id, amount, currency)]
    
    if len(current_bets_after_bet) >= RACE_CAPACITY:
        return True, finalize_race(status['race_id'], current_bets_after_bet)
    
    return True, "Ваша ставка принята! Ожидаем других игроков."

def finalize_race(race_id, bets):
    """Завершает гонку, определяет победителя и начисляет награды."""
    winning_rhoa_id = random.randint(1, 6)
    
    # Начисляем награды победителям
    for user_id, _, rhoa_id, bet_amount, currency_type in bets:
        if rhoa_id == winning_rhoa_id:
            winnings = bet_amount * WIN_MULTIPLIER
            db.add_rewards(user_id, divines=winnings if currency_type == 'divine_orbs' else 0, mirrors=winnings if currency_type == 'mirrors' else 0)
            
    db.finish_race(race_id)
    
    # Возвращаем отформатированный текст с результатами
    return _format_race_results(race_id, bets, winning_rhoa_id)

def get_last_race_results_text(race_id, bets):
    """Получает результаты завершенной гонки для отображения."""
    # Победителя нужно определить детерминированно, чтобы он был одинаков для всех
    # Используем ID гонки как "сид" для генератора случайных чисел
    random.seed(race_id)
    winning_rhoa_id = random.randint(1, 6)
    random.seed() # Сбрасываем сид, чтобы не влиять на другие случайности в боте
    
    return _format_race_results(race_id, bets, winning_rhoa_id)