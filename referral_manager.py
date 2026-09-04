# referral_manager.py
import database as db
from utils import escape_markdown

TARGET_LEVEL = 7
REWARD_AMOUNT = 5  # Количество Divine Orbs за одного друга

def claim_all_rewards(user_id):
    """
    Начисляет награды за всех приглашенных, достигших целевого уровня.
    """
    unclaimed_referrals = db.get_unclaimed_referrals(user_id, TARGET_LEVEL)
    
    if not unclaimed_referrals:
        return "У вас нет доступных наград для получения\\."

    total_reward = 0
    claimed_friends = []

    for ref_id, friend_username, _ in unclaimed_referrals:
        db.mark_referral_as_claimed(user_id, ref_id)
        total_reward += REWARD_AMOUNT
        claimed_friends.append(friend_username)

    if total_reward > 0:
        db.add_rewards(user_id, divines=total_reward, mirrors=0)
        friends_list_str = ", ".join([f"*{escape_markdown(name)}*" for name in claimed_friends])
        return (f"🎉 Поздравляем\\! Вы получили награду за следующих друзей: {friends_list_str}\\. "
                f"Ваш баланс пополнен на *{total_reward}* 💎 Divine Orbs")
    
    return "Произошла ошибка при начислении наград"