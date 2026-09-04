# telegram_handler.py
import json
import logging
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest, RetryAfter # <-- ИЗМЕНЕНИЕ: Импортируем RetryAfter
from utils import escape_markdown

import database as db
import game_manager as gm
import combat_manager as cm
import ui_components as ui
import item_manager as im
import event_manager as em
import pvp_manager as pvp_m
import mtx_manager as mtx_m
import perk_manager as perk_m 
import rhoa_race_manager
import fishing_manager
import quest_manager
import harvest_manager
import leaderboard_manager
import referral_manager
import world_boss_manager as wbm
import divination_card_manager as dcm
from game_content import CURRENCY, HARVEST_CRAFTING_CONFIG, PASSIVE_SKILL_TREE, PLAYER_XP_PER_LEVEL, ASCENDANCY_PASSIVES
from shared_data import USER_ACTION_LOCK 


logger = logging.getLogger(__name__)

def generate_main_menu_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("⚔️ PVE Режим", callback_data='menu_pve'), InlineKeyboardButton("🛡️ PVP Режим", callback_data='menu_pvp')],
        [InlineKeyboardButton("☠️ Хардкор PVP", callback_data='menu_hc_pvp')],
        [InlineKeyboardButton("🏆 Таблицы Лидеров", callback_data='menu_leaderboard'), InlineKeyboardButton("📊 Моя статистика", callback_data='menu_my_stats')],
        [InlineKeyboardButton("🎯 Ежедневные Задания", callback_data='menu_quests'), InlineKeyboardButton("👹 Ивенты", callback_data='menu_events')],
        # ИЗМЕНЕНИЕ ЗДЕСЬ
        [InlineKeyboardButton("🛠️ Прокачка и Обмен", callback_data='menu_upgrades_exchange')],
        [InlineKeyboardButton("🤝 Пригласить друга", callback_data='menu_referral')], 
        [InlineKeyboardButton("💎 Магазин MTX", callback_data='menu_mtx_shop')],
        [InlineKeyboardButton("❓ Помощь", callback_data='menu_help')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_buy_perk(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    from perk_manager import PERK_CATALOG
    user_id = query.from_user.id
    perk_id = query.data.replace('buy_perk_', '')
    
    success, message = perk_m.purchase_perk(user_id, perk_id)
    await query.answer(escape_markdown(message), show_alert=True)
    
    if success:
        currency_type = 'divine' if perk_id in PERK_CATALOG else 'mirror'
        result = ui.create_perk_purchase_ui(user_id, currency_type)
        await query.edit_message_text(text=result['text'], reply_markup=InlineKeyboardMarkup(result['buttons']), parse_mode=ParseMode.MARKDOWN_V2)

def generate_leaderboard_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏆 Ежемесячные Награды", callback_data='monthly_rewards_menu')],
        [InlineKeyboardButton("PVE Лидеры", callback_data='leaderboard_pve'), InlineKeyboardButton("PVP Лидеры", callback_data='leaderboard_pvp')],
        [InlineKeyboardButton("☠️ ХК PVP Лидеры", callback_data='leaderboard_hc_pvp')],
        [InlineKeyboardButton("👑 Чемпионы", callback_data='leaderboard_champions'), InlineKeyboardButton("⭐ Лидеры по Уровню", callback_data='leaderboard_level')],
        [InlineKeyboardButton("♾️ Бесконечный Забег", callback_data='leaderboard_endless')],
        [InlineKeyboardButton("🎣 Лидеры Рыбалки", callback_data='leaderboard_fishing'), InlineKeyboardButton("🌿 Садоводы", callback_data='leaderboard_harvest')],
        [InlineKeyboardButton("⬅️ Назад в меню", callback_data='back_to_main_menu')]
    ])

def format_leaderboard(board_data, title):
    if not board_data: return f"🏆 *{escape_markdown(title)}* 🏆\n\n_Пока здесь пусто\\._"
    header = f"🏆 *__{escape_markdown(title)}__* 🏆\n\n"
    lines = [f"{'🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else f'*{i}*\\.'} {mtx_m.format_leaderboard_entry(mtx_m.format_username(user_id, name), wins, user_id)}" for i, (user_id, name, wins) in enumerate(board_data, 1)] # ИСПРАВЛЕНО
    return header + "\n".join(lines)

def format_endless_leaderboard(board_data, title):
    """Форматирует таблицу лидеров для Бесконечного Забега."""
    if not board_data:
        return f"♾️ *{escape_markdown(title)}* ♾️\n\n_Пока никто не осмелился бросить вызов бесконечности\\._"
    header = f"♾️ *__{escape_markdown(title)}__* ♾️\n\n"
    lines = [f"{'🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else f'*{i}*\\.'} {escape_markdown(name)} — этаж: *{floor}*"
             for i, (_, name, floor) in enumerate(board_data, 1)]
    return header + "\n".join(lines)

def format_fishing_leaderboard(board_data, title):
    if not board_data:
        return f"🎣 *{escape_markdown(title)}* 🎣\n\n_Пока здесь пусто\\._"
    header = f"🎣 *__{escape_markdown(title)}__* 🎣\n\n"
    lines = [f"{'🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else f'*{i}*\\.'} {escape_markdown(name)} — уровень: *{level}*"
             for i, (_, name, level) in enumerate(board_data, 1)]
    return header + "\n".join(lines)

def format_harvest_leaderboard(board_data, title):
    if not board_data:
        return f"🌿 *{escape_markdown(title)}* 🌿\n\n_Пока здесь пусто\\._"
    header = f"🌿 *__{escape_markdown(title)}__* 🌿\n\n"
    lines = [f"{'🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else f'*{i}*\\.'} {escape_markdown(name)} — уровень: *{level}*"
             for i, (_, name, level) in enumerate(board_data, 1)]
    return header + "\n".join(lines)

def format_champions_list(champions_data):
    if not champions_data: return "👑 *Текущие Чемпионы* 👑\n\n_Трон пустует\\._"
    header = "👑 *Текущие Чемпионы* 👑\n\n"
    lines = [f"✨ {mtx_m.format_username(player_id, name)} \\- пассивных побед: *{wins}*" for player_id, name, wins in champions_data]
    return header + "\n".join(lines)

def format_level_leaderboard(board_data, title):
    """Форматирует таблицу лидеров по уровню персонажа."""
    if not board_data:
        return f"👑 *{escape_markdown(title)}* 👑\n\n_Пока никто не покинул первый уровень\\._"
    header = f"👑 *__{escape_markdown(title)}__* 👑\n\n"
    lines = [f"{'🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else f'*{i}*\\.'} {escape_markdown(name)} — уровень: *{level}*"
             for i, (_, name, level) in enumerate(board_data, 1)]
    return header + "\n".join(lines)

async def show_main_menu(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    user_id = query.from_user.id
    effects = mtx_m.get_player_mtx_effects(user_id)
    
    text = "Вы вернулись в главное меню\\."
    
    if effects.get('greeting') and (player_info := db.get_player_info(user_id)):
        text = f"Куда отправимся дальше, Легенда {mtx_m.format_username(user_id, player_info['username'])}?"

    await query.edit_message_text(
        text=text, 
        reply_markup=generate_main_menu_keyboard(user_id), 
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def show_mtx_shop(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE, section='main'):
    user_id = query.from_user.id
    player_info = db.get_player_info(user_id)
    if not player_info:
        await query.edit_message_text("Не удалось найти данные профиля\\.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main_menu')]]))
        return
    unlocked_mtx = player_info.get('unlocked_mtx', [])
    shop_text = f"💎 *Магазин MTX*\n\nПриобретите косметику для статуса\\.\n\n\\-\\-\\- *Ваш баланс* \\-\\-\\-\n{CURRENCY['divine_orb']['name']}: *{player_info.get('divine_orbs', 0)}*\n{CURRENCY['mirror']['name']}: *{player_info.get('mirrors', 0)}*\n"
    keyboard_buttons = []
    if section == 'main':
        keyboard_buttons = [[InlineKeyboardButton("✨ Обитель Вознесшихся (Divine)", callback_data='mtx_section_divine')], [InlineKeyboardButton("👑 Пантеон Богов (Mirror)", callback_data='mtx_section_mirror')], [InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main_menu')]]
    else:
        currency_filter, currency_symbol = ('divine_orbs', '💎') if section == 'divine' else ('mirrors', '🪞')
        for mtx_id, mtx in mtx_m.MTX_CATALOG.items():
            if mtx['currency'] == currency_filter:
                is_owned = mtx_id in unlocked_mtx
                button_text = f"✅ {mtx['name']}" if is_owned else f"Купить {mtx['name']} ({mtx['cost']} {currency_symbol})"
                keyboard_buttons.append([InlineKeyboardButton(button_text, callback_data="mtx_already_owned" if is_owned else f'buy_mtx_{mtx_id}')])
        keyboard_buttons.append([InlineKeyboardButton("⬅️ Назад в магазин", callback_data='menu_mtx_shop')])
    await query.edit_message_text(text=shop_text, reply_markup=InlineKeyboardMarkup(keyboard_buttons), parse_mode=ParseMode.MARKDOWN_V2)

async def handle_buy_mtx(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    user_id = query.from_user.id
    mtx_id = query.data.replace('buy_mtx_', '')
    mtx_data = mtx_m.MTX_CATALOG.get(mtx_id)
    if not mtx_data:
        await query.answer("Ошибка: предмет не найден\\.", show_alert=True)
        return
    success = db.purchase_mtx(user_id, mtx_id, mtx_data['cost'], mtx_data['currency'])
    await query.answer(escape_markdown(f"✅ Поздравляем\\! Вы приобрели: {mtx_data['name']}." if success else "❌ Недостаточно средств или предмет уже куплен\\!"), show_alert=True)
    await show_mtx_shop(query, context, section='divine' if mtx_data['currency'] == 'divine_orbs' else 'mirror')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, user_id = update.effective_user, update.effective_user.id
    db.add_or_update_player(user_id, user.username or user.first_name)

    # --- НАЧАЛО ИЗМЕНЕНИЙ: Обработка реферальной ссылки ---
    if context.args and context.args[0].startswith('ref_'):
        try:
            referrer_id = int(context.args[0].split('_')[1])
            if referrer_id != user_id:
                # Проверяем, существует ли пригласивший игрок
                if db.get_player_info(referrer_id):
                    db.add_referral(referrer_id, user_id)
                    logger.info(f"User {user_id} was referred by {referrer_id}")
        except (ValueError, IndexError):
            logger.warning(f"Invalid referral code received: {context.args[0]}")
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    if context.user_data.get('wb_char_state'):
        db.set_player_boss_cooldown(user_id)
        del context.user_data['wb_char_state']
        await update.message.reply_markdown_v2(
            text="Вы покинули поле боя с Мировым Боссом до его завершения\\.\n\n"
                 "Ваша атака прервана, и вы получаете штрафное время восстановления \\(4 часа\\)\\.",
            reply_markup=generate_main_menu_keyboard(user_id)
        )
        return

    effects = mtx_m.get_player_mtx_effects(user_id)
    greeting = f"Привет, Изгнанник {user.mention_markdown_v2()}\\!\n\n"
    greeting += f"Чат для общения: [Игровой Чат](https://t.me/poegamechat)\\.\n\n"
    if effects.get('greeting') and (player_info := db.get_player_info(user_id)):
        greeting = f"С возвращением, Легенда {mtx_m.format_username(user_id, player_info['username'])}\\!"
    await update.message.reply_markdown_v2(greeting, reply_markup=generate_main_menu_keyboard(user_id))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    db.add_or_update_player(user_id, query.from_user.username or query.from_user.first_name)
    data = query.data
    if data is None:
        logger.error(f"CallbackQuery data is None for user {user_id}")
        await query.answer("Ошибка: некорректный запрос.", show_alert=True)
        return
    current_time, last_action_time, COOLDOWN = time.time(), USER_ACTION_LOCK.get(user_id, 0), 1.5
    if current_time - last_action_time < COOLDOWN:
        try: await query.answer()
        except BadRequest: pass
        return
    USER_ACTION_LOCK[user_id] = current_time
    
    try: await query.answer()
    except BadRequest as e:
        if "Query is too old" in str(e): logger.warning(f"Query is too old for user {user_id}, data: '{data}'. Ignoring."); return
        else: raise e 
    
    logger.info(f"--- CB: '{data}' from {user_id} ---")

    RUN_DEPENDENT_CALLBACKS = (
        'show_char_stats', 'show_my_items', 'continue_run', 
        # --- ДОБАВЛЕНЫ НОВЫЕ КОЛБЭКИ ---
        'view_pvp_boss', 'view_boss_stats', 'view_boss_equipment', 
        # --- НАЧАЛО ИЗМЕНЕНИЙ ---
        'force_crucible_forge', # Добавляем отладочную команду в список
        # --- КОНЕЦ ИЗМЕНЕНИЙ ---
        'crucible_start',
          # --- НАЧАЛО ИЗМЕНЕНИЙ: Добавляем все шаги Кузницы ---
        'crucible_select_floor:',
        'crucible_select_type:',
        'crucible_select_rarity:',
        'crucible_select_item:',
        # --- КОНЕЦ ИЗМЕНЕНИЙ ---
        'pvp_challenge_champion', 'shop_', 'back_to_shop', 'back_to_smith', 'smith_', 
        'event_', 'healer_', 'combat_', 'loot_choice_', 'equip_confirm:', 
        'back_to_loot_choice', 'corrupt_item_', 'trial_choice_', 'chest_choice:',
        'mysterious_room_trigger', 'cadiro_deal_', 'mystery_sacrifice_confirm',
        'mystery_kalandra_touch:', 'mystery_pact_accept', 'mystery_pact_decline',
        'ring_choice:', 'loot_choice_skip', 'corruption_view_items', 'smith_view_items',
        'leave_run', 'show_post_boss_loot', 'mystery_decline', 'ascendancy_skip', 'ascendancy_choice:', 'buy_ascendancy'
    )


    run_state = None
    if any(data.startswith(prefix) for prefix in RUN_DEPENDENT_CALLBACKS):
        run_state = db.get_pve_run_state(user_id)
        if not run_state and data not in ['leave_run', 'back_to_main_menu']:
            await query.edit_message_text(text="❌ *Действие отменено*\n\nВаш предыдущий забег уже завершен\\.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ В главное меню", callback_data='back_to_main_menu')]]), parse_mode=ParseMode.MARKDOWN_V2)
            return

    result = None
    try:
        # --- Меню и Навигация ---
        if data == 'back_to_main_menu': await show_main_menu(query, context)
        elif data == 'menu_pve': result = gm.start_pve_run(user_id)
        elif data == 'menu_pvp': result = gm.start_pvp_run(user_id)
        elif data == 'menu_leaderboard': await query.edit_message_text(text="🏆 *Таблицы Лидеров*", reply_markup=generate_leaderboard_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
        elif data == 'leaderboard_pve': result = {'text': format_leaderboard(db.get_pve_leaderboard_with_ids(), "Топ PVE Игроков"), 'buttons': generate_leaderboard_keyboard().inline_keyboard}
        elif data == 'leaderboard_pvp': result = {'text': format_leaderboard(db.get_pvp_leaderboard_with_ids(), "Топ PVP Игроков"), 'buttons': generate_leaderboard_keyboard().inline_keyboard}
        elif data == 'leaderboard_champions': result = {'text': format_champions_list(db.get_champions_list_with_ids()), 'buttons': generate_leaderboard_keyboard().inline_keyboard}
        elif data == 'menu_hc_pvp': result = gm.start_hc_pvp_run(user_id)
        elif data == 'leaderboard_hc_pvp': result = {'text': format_leaderboard(db.get_hc_pvp_leaderboard_with_ids(), "Топ Хардкор PVP Игроков"), 'buttons': generate_leaderboard_keyboard().inline_keyboard}
        elif data == 'leaderboard_level':
            board = leaderboard_manager.get_level_leaderboard()
            text = format_level_leaderboard(board, "Топ 10 по Уровню Персонажа")
            await query.edit_message_text(text=text, reply_markup=generate_leaderboard_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
        elif data == 'menu_endless_run': result = gm.start_endless_run(user_id)
        elif data == 'leaderboard_endless':
            board = leaderboard_manager.get_endless_leaderboard()
            text = format_endless_leaderboard(board, "Лучшие Покорители Бесконечности")
            await query.edit_message_text(text=text, reply_markup=generate_leaderboard_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
        elif data == 'menu_quests': result = ui.create_quests_ui(user_id)
        elif data == 'menu_events':
            event_menu_text = "Выберите ивент, в котором хотите поучаствовать\\."
            event_menu_buttons = [
                [InlineKeyboardButton("♾️ Бесконечный Забег", callback_data='menu_endless_run')],
                [InlineKeyboardButton("👹 Мировой Босс", callback_data='menu_world_boss')],
                [InlineKeyboardButton("🎣 Рыбалка", callback_data='menu_fishing')],
                [InlineKeyboardButton("🌿 Харвест", callback_data='menu_harvest')],
                [InlineKeyboardButton("🏁 Гонка Роа", callback_data='menu_rhoa_race')],
                [InlineKeyboardButton("⬅️ В главное меню", callback_data='back_to_main_menu')]
            ]
            result = {'text': event_menu_text, 'buttons': event_menu_buttons}
        
        elif data == 'menu_fishing': result = ui.create_fishing_main_ui(user_id)
        elif data == 'menu_harvest': db.get_harvest_stats(user_id); result = ui.create_harvest_main_ui(user_id)
        elif data == 'krillson_shop': result = ui.create_krillson_shop_ui(user_id)
        elif data == 'buy_rod_shop': result = ui.create_rod_shop_ui(user_id)
        elif data.startswith('buy_rod:'):
            rod_id = data.split(':')[1]
            success, message = fishing_manager.buy_rod(user_id, rod_id)
            await query.answer(message, show_alert=True)
            if success: result = ui.create_rod_shop_ui(user_id)
        elif data == 'sell_catch_ui': result = ui.create_sell_catch_ui(user_id)
        elif data == 'leaderboard_fishing':
            board = leaderboard_manager.get_fishing_leaderboard()
            text = format_fishing_leaderboard(board, "Топ 10 по уровню рыбалки")
            await query.edit_message_text(text=text, reply_markup=generate_leaderboard_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
        elif data == 'leaderboard_harvest':
            board = leaderboard_manager.get_harvest_leaderboard()
            text = format_harvest_leaderboard(board, "Топ 10 Садоводов")
            await query.edit_message_text(text=text, reply_markup=generate_leaderboard_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
        elif data == 'sell_all_catch':
            items_sold, chaos_earned = fishing_manager.sell_all_catch(user_id)
            if items_sold == 0: await query.answer("Вам нечего продавать\\.", show_alert=True)
            else:
                await query.answer(f"Вы продали {items_sold} предмет(ов) и заработали {chaos_earned} 🟢 Хаос Орбов\\!", show_alert=True)
                result = ui.create_sell_catch_ui(user_id)
        elif data == 'fishing_upgrades_ui': result = ui.create_fishing_upgrades_ui(user_id)
        elif data.startswith('buy_fish_upgrade:'):
            upgrade_id = data.split(':')[1]
            success, message = fishing_manager.buy_fishing_upgrade(user_id, upgrade_id)
            await query.answer(escape_markdown(str(message)), show_alert=True)
            result = ui.create_fishing_upgrades_ui(user_id)
        elif data == 'go_to_lake': result = ui.create_lake_ui(user_id)
        elif data == 'buy_ascendancy':
            char = run_state['character']
            cost = 1000
            
            # Проверка, может ли игрок вообще изучать пассивки
            class_id = char.get('class_id')
            total_passives = len(ASCENDANCY_PASSIVES.get(class_id, {}))
            chosen_passives_count = len(char.get('chosen_ascendancy_passives', []))

            if chosen_passives_count >= total_passives:
                await query.answer("Вы уже изучили все доступные умения Восхождения!", show_alert=True)
                return # Прерываем выполнение

            if char.get('currency', {}).get('gold', 0) < cost:
                await query.answer(f"Недостаточно золота! Нужно {cost} 🪙.", show_alert=True)
                return # Прерываем выполнение

            # Если все проверки пройдены
            char['currency']['gold'] -= cost
            char['ascendancy_points'] = char.get('ascendancy_points', 0) + 1
            
            # Извлекаем сообщение о победе, чтобы оно не потерялось
            victory_message = char.pop('pending_victory_message', None)
            
            db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
            
            # Показываем стандартный UI выбора умения
            result = ui.create_ascendancy_choice_ui(run_state)
            
            # Добавляем сообщение о победе к тексту UI
            if victory_message:
                result['text'] = victory_message + "\n\n" + result['text']
        elif data == 'monthly_rewards_menu':
            result = ui.create_monthly_rewards_ui(user_id)

        elif data == 'claim_monthly_rewards':
            message = leaderboard_manager.claim_all_monthly_rewards(user_id)
            await query.answer(escape_markdown(message), show_alert=True)
            # Обновляем UI, чтобы кнопка могла исчезнуть, если награды забраны
            result = ui.create_monthly_rewards_ui(user_id)
        elif data == 'menu_referral':
            bot_username = context.bot.username
            result = ui.create_referral_program_ui(user_id, bot_username)

        elif data == 'claim_referral_reward_all':
            message = referral_manager.claim_all_rewards(user_id)
            await query.answer(escape_markdown(message), show_alert=True)
            # Обновляем UI, чтобы кнопка исчезла
            bot_username = context.bot.username
            result = ui.create_referral_program_ui(user_id, bot_username)
        elif data == 'shard_exchange_ui': result = ui.create_shard_exchange_ui(user_id)
        elif data == 'menu_rhoa_race':
            # Просто вызываем обновление UI без сброса состояния
            result = ui.create_rhoa_race_ui(user_id, context)
            
        elif data == 'rhoa_race_show_new':
            # --- НОВАЯ КНОПКА: Помечаем результаты как просмотренные и обновляем UI ---
            status = rhoa_race_manager.get_race_status(user_id)
            context.user_data['viewed_race_id'] = status['race_id'] - 1
            result = ui.create_rhoa_race_ui(user_id, context)

        elif data.startswith('rhoa_race_bet_ui:'):
            rhoa_id = int(data.split(':')[1])
            result = ui.create_rhoa_bet_ui(user_id, rhoa_id)
            
        elif data.startswith('rhoa_race_place_bet:'):
            _, rhoa_id_str, amount_str, currency = data.split(':')
            rhoa_id = int(rhoa_id_str)
            amount = int(amount_str)
            username = query.from_user.username or query.from_user.first_name
            
            success, message = rhoa_race_manager.place_bet(user_id, username, rhoa_id, amount, currency)
            
            if not success:
                await query.answer(escape_markdown(message), show_alert=True)
            else:
                if "Забег Роа" in message:
                    result = {'text': message, 'buttons': [[{'text': '✅ Отлично!', 'callback_data': 'menu_rhoa_race'}]]}
                else:
                    await query.answer(escape_markdown(message), show_alert=True)
                    # --- ИСПРАВЛЕНО: Добавляем context ---
                    result = ui.create_rhoa_race_ui(user_id, context)
        elif data == 'exchange_shards_confirm':
            success, message = db.exchange_divine_shards(user_id)
            await query.answer(message, show_alert=True)
            if success: result = ui.create_shard_exchange_ui(user_id)
        elif data == 'start_fishing':
            fishing_result = fishing_manager.start_fishing(user_id)
            if fishing_result['status'] == 'cooldown':
                await query.answer(f"Еще слишком рано! Попробуйте снова через {fishing_result.get('wait_time', 10)} сек.", show_alert=True)
            
            # --- НАЧАЛО ИЗМЕНЕНИЙ: ОБРАБОТКА НОВОГО СТАТУСА ---
            elif fishing_result['status'] == 'on_expedition':
                # Получаем актуальные данные, чтобы рассчитать время
                stats = db.get_fishing_stats(user_id)
                expedition_end_time = stats.get('expedition_end_time', 0)
                
                # Рассчитываем оставшееся время
                time_left = expedition_end_time - int(time.time())
                hours, rem = divmod(time_left, 3600)
                minutes, _ = divmod(rem, 60)
                
                # Формируем сообщение, которое будет вставлено в основной текст
                message = (f"❗ Вы не можете рыбачить, пока находитесь в экспедиции\\.\n\n"
                           f"Осталось времени: *{int(hours)} ч {int(minutes)} мин*")
                
                # Пересобираем UI озера с этим сообщением
                result = ui.create_lake_ui(user_id, last_action_message=message)

            elif fishing_result['status'] == 'no_rod':
                await query.answer("У вас нет удочки! Купите её у Криллсона.", show_alert=True)
            else:
                last_action_msg = ""
                if fishing_result['status'] == 'fail':
                    last_action_msg = "💦 Ничего не клюнуло, рыба сорвалась с крючка\\!"
                elif fishing_result['status'] == 'success':
                    res = fishing_result
                    escaped_weight = escape_markdown(str(res['item_weight']))
                    last_action_msg = f"🎉 *Улов\\!* Вы поймали: *{escape_markdown(res['item_name'])}* \\(вес: {escaped_weight} кг\\)\\.\nВы получили *{res['xp_gained']}* опыта\\."
                    if res.get('dropped_seed_name'):
                        last_action_msg += f"\n\n🌿 *Бонус\\!* Вместе с рыбой вы выловили семя: *{escape_markdown(res['dropped_seed_name'])}*\\!"
                    if res['leveled_up']:
                        last_action_msg += f"\n\n✨ *ПОЗДРАВЛЯЕМ\\!* Вы достигли *{res['new_level']}* уровня рыбалки\\!"
                elif fishing_result['status'] == 'success_special':
                    res = fishing_result
                    last_action_msg = (f"🎉 *Невероятная удача\\!* 🎉\n"
                                       f"Вы выловили *{escape_markdown(res['item_name'])}*\\!\n\n"
                                       f"Внутри вы нашли *1 Осколок Божественности*\\. "
                                       f"Теперь у вас *{res['new_shard_balance']}* осколков\\.")
                last_action_msg += f"\n\nПодождите *{fishing_manager.FISHING_COOLDOWN}* секунд до следующей попытки\\."
                result = ui.create_lake_ui(user_id, last_action_message=last_action_msg)
        
        elif data.startswith('claim_quest_'):
            quest_index = int(data.split('_')[-1])
            success, message = quest_manager.claim_reward(user_id, quest_index)
            await query.answer(escape_markdown(message), show_alert=True)
            if success: result = ui.create_quests_ui(user_id)
        elif data.startswith('ascendancy_choice:'):
            passive_id = data.split(':')[1]
            result = gm.process_ascendancy_choice(user_id, run_state, passive_id)
        
        elif data == 'ascendancy_skip':
            # Если игрок пропускает выбор (например, из-за ошибки), просто переходим к добыче
            result = ui.create_loot_choice_ui(run_state)
        elif data.startswith('quest_claimed_'): await query.answer("Награда за это задание уже получена.", show_alert=False)
        elif data.startswith('quest_inprogress_'): await query.answer("Задание еще в процессе выполнения.", show_alert=False)
        elif data == 'menu_my_stats':
            player_info = db.get_player_info(user_id)
            if not player_info:
                result = {'text': "❌ *Профиль не найден\\.*\n\nПожалуйста, начните с команды /start, чтобы создать свой профиль\\.", 'buttons': [[InlineKeyboardButton("⬅️ В главное меню", callback_data='back_to_main_menu')]]}
            else:
                level = player_info.get('level', 1)
                xp = player_info.get('xp', 0)
                xp_needed = PLAYER_XP_PER_LEVEL[level] if level < 100 else "МАКС"
                
                # --- ИЗМЕНЕНИЯ ЗДЕСЬ ---
                champions_list = db.get_player_champions_info(user_id)
                hc_champions_list = db.get_player_hc_champions_info(user_id)
                # --- КОНЕЦ ИЗМЕНЕНИЙ ---

                stats_text = (f"📊 *Статистика игрока {mtx_m.format_username(user_id, player_info['username'])}*\n\n"
                              f"⭐ Уровень: *{level}* \\(`{xp}/{xp_needed}`\\)\n"
                              f"⚔️ PVE побед: *{player_info.get('pve_wins', 0)}*\n"
                              f"🛡️ PVP побед: *{player_info.get('pvp_wins', 0)}*\n"
                              f"☠️ ХК PVP побед: *{player_info.get('hc_pvp_wins', 0)}*\n\n" # <-- Новая строка
                              f"\\-\\-\\- *Валюта* \\-\\-\\-\n{CURRENCY['divine_orb']['name']}: *{player_info.get('divine_orbs', 0)}*\n{CURRENCY['mirror']['name']}: *{player_info.get('mirrors', 0)}*\n")
                
                # --- ИЗМЕНЕНИЯ ЗДЕСЬ ---
                if champions_list:
                    stats_text += f"\n\\-\\-\\- *Ваши Чемпионы* \\({len(champions_list)} шт\\.\\) \\-\\-\\-\n"
                    total_passive_wins = sum(c[1] for c in champions_list)
                    stats_text += f"🏆 Суммарно пассивных побед: *{total_passive_wins}*\n"

                if hc_champions_list:
                    stats_text += f"\n\\-\\-\\- *Ваши Хардкорные Чемпионы* \\({len(hc_champions_list)} шт\\.\\) \\-\\-\\-\n"
                    total_hc_passive_wins = sum(c[1] for c in hc_champions_list)
                    stats_text += f"🏆 Суммарно пассивных побед: *{total_hc_passive_wins}*\n"
                # --- КОНЕЦ ИЗМЕНЕНИЙ ---

                result = {'text': stats_text, 'buttons': [[InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main_menu')]]}
        elif data == 'menu_help':
            help_text = (
                "❓ *Краткое Руководство*\n\n"
                "Подробности всех механик и предметов доступны на [игровой Википедии](https://tgpoegamebot.fandom.com/ru/wiki/Предметы)\\.\n\n"
                "Для общения переходите в наш [игровой Чат](https://t.me/poegamechat)\\.\n\n"
                "🏆 *Цель*: Пройти 4 этажа по 15 комнат, побеждая боссов\\. Полная победа приносит `1 💎 Divine Orb`\\.\n\n"
                "⚔️ *Режимы Игры*\n"
                "• *PVE*: Классический режим против монстров\\.\n"
                "• *PVP*: Открывается после первой PVE победы\\. Сражайся с призраками игроков, стань Чемпионом и получай `🪞 Mirror` за пассивные защиты\\.\n"
                "• *Бесконечный Забег*: Монстры постоянно усиливаются\\. Награда за рекорды этажей\\.\n\n"
                "💎 *Валюта*\n"
                "• `🪙 Золото`: Временная валюта, только на 1 забег\\.\n"
                "• `💎 Divine Orb` и `🪞 Mirror`: Постоянные валюты для покупки *Перков* \\(глобальных улучшений\\) и MTX\\.\n"
                "• `🟢 Хаос Орбы` и `✨ Осколки`: Добываются на *Рыбалке* для покупки удочек и особых перков\\.\n"
                "• `🟢/💎 Сила \\(Харвест\\)`: Добывается в *Харвесте* для создания собственных предметов\\.\n\n"
                "🎯 *Механики в Забеге*\n"
                "• *Святилища*: Временные баффы на несколько боев\\.\n"
                "• *Алтари Порчи*: Рискованное улучшение/уничтожение предмета\\.\n"
                "• *Испытания*: Проверка характеристик за *постоянный* бонус к статам\\.\n"
                "• *Загадочные комнаты*: Случайные события с уникальными наградами и рисками\\.\n"
                "• *Сеты Предметов*: Несколько частей одного комплекта дают мощный дополнительный бонус\\.\n\n"
                "👹 *Глобальные Активности*\n"
                "• *Мировой Босс*: Ежедневный ивент, где все игроки бьют одного босса за топ награды, включая `Mirrors`\\.\n"
                "• *Ежедневные Задания*: Стабильный источник `Divine Orbs`\\.\n"
                "• *Рыбалка*: Мини\\-игра для фарма `Хаос Орбов` и `Осколков`\\.\n"
                "• *Харвест*: Выращивание растений для крафта *собственных уникальных предметов*, которые попадут в общую игру\\.\n"
                "• *Гадальные Карты*: Собери сет и обменяй на ценную валюту в меню *Прокачка \\| Обмен*\\."
            )
            result = {'text': help_text, 'buttons': [[InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main_menu')]]}
        elif data == 'menu_upgrades_exchange':
            text = "Выберите, что вы хотите сделать\\."
            buttons = [
                [InlineKeyboardButton("🛠️ Прокачка Персонажа (Валюта)", callback_data='menu_perks')],
                [InlineKeyboardButton("🌳 Дерево Умений (Уровень)", callback_data='menu_skill_tree')],
                [InlineKeyboardButton("🎴 Обменять Гадальные Карты", callback_data='divination_card_exchange_ui')],
                [InlineKeyboardButton("⬅️ Назад в главное меню", callback_data='back_to_main_menu')]
            ]
            result = {'text': text, 'buttons': buttons}
        elif data == 'divination_card_exchange_ui': result = ui.create_divination_card_ui(user_id)
        elif data.startswith('exchange_card_set_'):
            card_id = data.replace('exchange_card_set_', '')
            success, message = dcm.exchange_card_set(user_id, card_id)
            await query.answer(message, show_alert=True)
            if success: result = ui.create_divination_card_ui(user_id)
        elif data == 'menu_skill_tree':
            result = ui.create_passive_skill_tree_ui(user_id)
            
        elif data.startswith('skill_tree_branch:'):
            branch_id = data.split(':')[1]
            result = ui.create_passive_skill_tree_ui(user_id, branch=branch_id)

        elif data.startswith('skill_tree_sub_branch:'):
            _, branch_id, sub_branch_id = data.split(':')
            result = ui.create_passive_skill_tree_ui(user_id, branch=branch_id, sub_branch=sub_branch_id)
        elif data == 'fishing_perks_ui':
            result = ui.create_fishing_perks_ui(user_id)
        elif data.startswith('spend_fishing_perk:'):
            perk_id = data.split(':')[1]
            success, message = fishing_manager.spend_perk_point(user_id, perk_id)
            await query.answer(message, show_alert=True)
            if success:
                result = ui.create_fishing_perks_ui(user_id)
        elif data == 'reset_fishing_perks_confirm':
            result = ui.create_fishing_perk_reset_confirmation_ui()

        elif data == 'reset_fishing_perks_do':
            success, message = fishing_manager.reset_perk_points(user_id)
            await query.answer(escape_markdown(message), show_alert=True)
            if success:
                result = ui.create_fishing_perks_ui(user_id)
        elif data == 'bait_shop_ui':
            result = ui.create_bait_shop_ui(user_id)
        elif data.startswith('buy_bait:'):
            bait_id = data.split(':')[1]
            success, message = fishing_manager.buy_bait(user_id, bait_id)
            await query.answer(message, show_alert=True)
            if success:
                result = ui.create_bait_shop_ui(user_id)
        elif data == 'reroll_quests':
            success, message = quest_manager.reroll_quests(user_id)
            await query.answer(message, show_alert=True)
            if success:
                result = ui.create_quests_ui(user_id)
        elif data == 'fishing_expedition_ui':
            result = ui.create_expedition_ui(user_id)
            
        elif data == 'start_expedition':
            
            result = None # Инициализируем result как None
            try:
                success, message = fishing_manager.start_expedition(user_id)
                # Всегда пересобираем UI, чтобы он отражал актуальное состояние из БД
                result = ui.create_expedition_ui(user_id)

                if not success:
                    # Если была ошибка, добавляем ее в начало текста
                    error_text = f"❌ *Ошибка*\n_{escape_markdown(message)}_\n\n"
                    result['text'] = error_text + result['text']
                
                # На этом этапе переменная 'result' полностью готова к отправке

            except Exception as e:
                # В случае непредвиденной ошибки, создаем сообщение для пользователя
                result = {'text': 'Произошла внутренняя ошибка при обработке экспедиции', 'buttons': [[{'text': '⬅️ Назад', 'callback_data': 'krillson_shop'}]]}
                
        elif data == 'claim_expedition_reward':
            title, reward_text = fishing_manager.claim_expedition_reward(user_id)
            if title:
                # Сначала показываем короткое уведомление
                await query.answer(escape_markdown(title), show_alert=True)
                # Затем редактируем сообщение, чтобы показать полный улов
                result = {
                    'text': reward_text, 
                    'buttons': [[{'text': '⬅️ Назад к Криллсону', 'callback_data': 'krillson_shop'}]]
                }
            else:
                # Если награды нет (например, время не вышло), просто покажем уведомление
                await query.answer(escape_markdown(reward_text), show_alert=True)
        elif data.startswith('learn_skill_confirm:'):
            skill_id = data.split(':')[1]
            skill_data = PASSIVE_SKILL_TREE[skill_id]
            
            # Входные узлы теперь не должны быть доступны для изучения
            if skill_data.get('requires') is None:
                await query.answer("Этот узел уже изучен по умолчанию.", show_alert=True)
                return

            text = (f"Вы уверены, что хотите изучить умение *{escape_markdown(skill_data['name'])}* за 1 очко?\n\n"
                    f"_{escape_markdown(skill_data['desc'])}_\n\n"
                    "Это действие необратимо\\!")
            buttons = [
                [InlineKeyboardButton("✅ Да, изучить", callback_data=f'learn_skill_do:{skill_id}')],
                [InlineKeyboardButton("❌ Нет, назад", callback_data=f'skill_tree_sub_branch:{skill_data["branch"]}:{skill_data["sub_branch"]}')]
            ]
            result = {'text': text, 'buttons': buttons}
            
        elif data.startswith('learn_skill_do:'):
            skill_id = data.split(':')[1]
            success, message = db.spend_skill_point(user_id, skill_id)
            await query.answer(message, show_alert=True)
            if success:
                skill_data = PASSIVE_SKILL_TREE[skill_id]
                # Возвращаем пользователя в ту же под-ветвь, где он был
                result = ui.create_passive_skill_tree_ui(user_id, branch=skill_data["branch"], sub_branch=skill_data["sub_branch"])
        elif data == 'reset_skills_confirm':
            text = (
                "⚠️ *Подтверждение Сброса* ⚠️\n\n"
                "Вы уверены, что хотите сбросить все изученные пассивные умения за *10 💎 Divine Orbs*?\n\n"
                "Все ваши очки умений будут возвращены\\. Это действие необратимо\\."
            )
            buttons = [
                [InlineKeyboardButton("✅ Да, сбросить", callback_data='reset_skills_do')],
                [InlineKeyboardButton("❌ Нет, отмена", callback_data='menu_skill_tree')]
            ]
            result = {'text': text, 'buttons': buttons}
            
        elif data == 'reset_skills_do':
            player_info = db.get_player_info(user_id)
            cost = 2
            if player_info.get('divine_orbs', 0) < cost:
                await query.answer("❌ Недостаточно Divine Orbs!", show_alert=True)
                result = ui.create_passive_skill_tree_ui(user_id)
            else:
                # Списываем валюту, сбрасываем умения, возвращаем очки
                db.add_rewards(user_id, divines=-cost, mirrors=0)
                db.reset_all_passive_skills(user_id)
                db.refund_skill_points(user_id)
                await query.answer("✅ Все ваши пассивные умения были успешно сброшены!", show_alert=True)
                result = ui.create_passive_skill_tree_ui(user_id)
        elif data == 'menu_perks': result = ui.create_perks_main_menu_ui(user_id)
        elif data == 'perks_menu_divine': result = ui.create_perk_purchase_ui(user_id, 'divine')
        elif data == 'perks_menu_mirror': result = ui.create_perk_purchase_ui(user_id, 'mirror')
        elif data.startswith('buy_perk_'): await handle_buy_perk(query, context)
        elif data == 'leave_run': db.end_pve_run(user_id, is_win=False); await show_main_menu(query, context)
        elif data == 'menu_mtx_shop': await show_mtx_shop(query, context, section='main')
        elif data.startswith('mtx_section_'): await show_mtx_shop(query, context, section=data.replace('mtx_section_', ''))
        elif data.startswith('buy_mtx_'): await handle_buy_mtx(query, context)
        elif data == "mtx_already_owned": await query.answer("✅ У вас уже есть этот предмет\\.", show_alert=False)
        elif data.startswith('class_select:'):
            _, run_type, class_id = data.split(':')
            result = gm.start_run_with_class(user_id, run_type, class_id)
        elif data == 'show_char_stats': result = {'text': ui.get_player_stats_string(run_state['character']), 'buttons': [[{'text': '🎒 Мои Предметы', 'callback_data': 'show_my_items'}], [{'text': '⬅️ Назад к выбору пути', 'callback_data': 'continue_run'}]]}
        elif data == 'show_my_items': result = ui.create_equipped_items_ui(run_state['character'])
        elif data == 'continue_run': result = gm.continue_run(user_id)
        elif data == 'view_pvp_boss':
            boss_data = run_state['floor_bosses'][str(run_state['floor'])]
            result = ui.create_pvp_boss_view_ui(boss_data, view_mode='stats')

        # --- ДОБАВИТЬ ЭТИ ДВА ОБРАБОТЧИКА ---
        elif data == 'view_boss_stats':
            boss_data = run_state['floor_bosses'][str(run_state['floor'])]
            result = ui.create_pvp_boss_view_ui(boss_data, view_mode='stats')

        elif data == 'view_boss_equipment':
            boss_data = run_state['floor_bosses'][str(run_state['floor'])]
            result = ui.create_pvp_boss_view_ui(boss_data, view_mode='equipment')
        # --- КОНЕЦ НОВОГО БЛОКА ---

        elif data == 'pvp_challenge_champion': result = pvp_m.initiate_champion_fight(user_id, run_state)
        elif data == 'shop_view_items': result = ui.create_equipped_items_ui(run_state['character'], back_callback_data='back_to_shop')
        elif data == 'back_to_shop': result = ui.create_shop_ui(run_state)
        elif data == 'corruption_view_items': result = ui.create_equipped_items_ui(run_state['character'], back_callback_data='event_алтарь_порчи')
        elif data == 'smith_view_items': result = ui.create_equipped_items_ui(run_state['character'], back_callback_data='event_кузнец')
        elif data.startswith('shop_buy_'): result = gm.process_shop_purchase(user_id, int(data.split('_')[-1]))
        elif data == 'back_to_smith': result = ui.create_blacksmith_ui(run_state)
        elif data == 'smith_simple' or data == 'smith_blessing': result = ui.create_smith_item_choice_ui(run_state['character'], 'simple_upgrade' if data == 'smith_simple' else 'blessing')
        elif data == 'smith_tier_up': result = gm.process_smith_action(user_id, 'tier_up')
        elif data.startswith('smith_select:'): _, mode, slot = data.split(':'); result = gm.process_smith_action(user_id, mode, slot)
        
        # --- НАЧАЛО ИЗМЕНЕНИЙ: Обработчики для Кузницы Горнила ---
        elif data.startswith('smith_select:'): _, mode, slot = data.split(':'); result = gm.process_smith_action(user_id, mode, slot)
        
        # --- НАЧАЛО ИЗМЕНЕНИЙ: Обработчики для Кузницы Горнила ---
        elif data == 'crucible_start':
            # Эта кнопка ведет со стартового экрана Кузницы
            character = run_state['character']
            if character.get('currency', {}).get('gold', 0) < em.CRUCIBLE_FORGE_COST:
                await query.answer(f"Недостаточно золота! Нужно {em.CRUCIBLE_FORGE_COST} 🪙", show_alert=True)
                # Не выходим, просто показываем уведомление
            else:
                result = ui.create_crucible_floor_choice_ui()

        elif data.startswith('crucible_select_floor:'):
            floor = int(data.split(':')[1])
            context.user_data['crucible_session'] = {'floor': floor}
            result = ui.create_crucible_type_choice_ui(context)

        elif data.startswith('crucible_select_type:'):
            item_type = data.split(':', 1)[1]
            if 'crucible_session' in context.user_data:
                context.user_data['crucible_session']['type'] = item_type
                result = ui.create_crucible_rarity_choice_ui(context)
            else: # Если сессия потеряна
                result = em.handle_crucible_forge(user_id, run_state)

        elif data.startswith('crucible_select_rarity:'):
            rarity = data.split(':', 1)[1]
            if 'crucible_session' in context.user_data:
                context.user_data['crucible_session']['rarity'] = rarity
                result = ui.create_crucible_item_choice_ui(context)
            else:
                result = em.handle_crucible_forge(user_id, run_state)

        elif data.startswith('crucible_select_item:'):
            item_index = int(data.split(':')[1])
            if 'crucible_session' in context.user_data:
                result = em.process_crucible_item_selection(user_id, run_state, item_index, context)
            else:
                result = em.handle_crucible_forge(user_id, run_state)
        # --- КОНЕЦ ИЗМЕНЕНИЙ ---

        elif data.startswith('event_'):
            action_value = data.split('_', 1)[1]
            result = gm.handle_event(user_id, action_value)
        elif data.startswith('healer_'):
            action_value = data.split('_', 1)[1]
            result = gm.process_healer_choice(user_id, action_value)
        elif data.startswith('chest_choice:'):
            action_value = data.split(':', 1)[1]
            result = em.handle_chest_choice(user_id, run_state, action_value)
        elif data.startswith('combat_'):
            action_value = data.split('_', 1)[1]
            combat_state = run_state.get('character', {}).get('combat')
            if combat_state and not combat_state.get('is_world_boss', False):
                result = cm.process_combat_turn(user_id, action_value, run_state, context, telegram_user=query.from_user)

        elif data.startswith('mystery_'):
            if data == 'mystery_decline':
                result = em.handle_mystery_decline(user_id, run_state)
            if data == 'mystery_sacrifice_confirm': result = em.process_sacrifice(user_id, run_state)
            elif data.startswith('mystery_kalandra_touch:'):
                slot = data.split(':', 1)[1]
                result = em.process_kalandra_touch(user_id, run_state, slot)
            elif data == 'mystery_pact_accept': result = em.process_pact(user_id, run_state, accepted=True)
            elif data == 'mystery_pact_decline': result = em.process_pact(user_id, run_state, accepted=False)
        
        elif data == 'loot_choice_skip':
            char = run_state['character']
            # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
            char['currency']['gold'] += 40
            # --- КОНЕЦ ИЗМЕНЕНИЯ ---
            char['pending_loot'] = []
            db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
            result = gm.continue_run(user_id)
        elif data.startswith('loot_choice_'):
            item_index = int(data.split('_')[-1])
            pending_loot = run_state.get('character', {}).get('pending_loot', [])

            # --- НАЧАЛО ИЗМЕНЕНИЙ: Защита от двойного нажатия ---
            if not pending_loot or item_index >= len(pending_loot):
                await query.answer("Вы уже сделали свой выбор.", show_alert=True)
                result = gm.continue_run(user_id)
            else:
                # Если проверка пройдена, выполняем основную логику
                new_item = pending_loot[item_index]
                if new_item['slot'] in ['ring', 'ring1', 'ring2']:
                    result = ui.create_ring_slot_choice_ui(item_index, run_state['character'])
                else:
                    slot = new_item['slot']
                    old_item = run_state['character']['equipment'].get(slot)
                    result = ui.create_item_comparison_ui(run_state['character'], new_item, old_item, target_slot=slot, item_index=item_index)
        elif data.startswith('ring_choice:'):
            _, target_slot, item_index_str = data.split(':'); item_index = int(item_index_str)
            new_item = run_state['character']['pending_loot'][item_index]
            old_item = run_state['character']['equipment'].get(target_slot)
            result = ui.create_item_comparison_ui(run_state['character'], new_item, old_item, target_slot=target_slot, item_index=item_index)
        elif data.startswith('equip_confirm:'):
            _, item_index_str, target_slot = data.split(':')
            item_index = int(item_index_str)
            
            # --- НАЧАЛО ИЗМЕНЕНИЙ: Логика "Камня Алхимика" ---
            char = run_state['character']
            item_to_equip = char['pending_loot'][item_index]
            
            # Пытаемся трансмутировать предмет
            new_item, transmute_message = im.handle_transmutation(char, item_to_equip, run_state['floor'])
            
            # Если предмет изменился, обновляем его в списке добычи
            if transmute_message:
                char['pending_loot'][item_index] = new_item
                # Обновляем состояние в БД, чтобы equip_item нашел правильный предмет
                db.update_pve_run_state(user_id, run_state['floor'], run_state['event_num'], char, run_state['floor_bosses'])
            # --- КОНЕЦ ИЗМЕНЕНИЙ ---

            updated_run_state = im.equip_item(user_id, item_index, target_slot=target_slot)
            if not updated_run_state:
                result = {'text': "❌ *Действие отменено*\\.\n\nНе удалось найти предмет или забег уже завершен\\.", 'buttons': [[InlineKeyboardButton("⬅️ В главное меню", callback_data='back_to_main_menu')]]}
            else:
                item_name = updated_run_state['character']['equipment'][target_slot]['name']
                next_step = gm.continue_run(user_id)
                
                # Добавляем сообщение о трансмутации, если оно было
                final_text = f"✅ Предмет *{escape_markdown(item_name)}* надет\\!\n\n"
                if transmute_message:
                    final_text = transmute_message + "\n\n" + final_text
                
                result = {'text': final_text + next_step['text'], 'buttons': next_step['buttons']}
        elif data == 'back_to_loot_choice': result = ui.create_loot_choice_ui(run_state)
        elif data == 'show_post_boss_loot':
            result = ui.create_loot_choice_ui(run_state)
        elif data.startswith('corrupt_item_'):
            slot_to_corrupt = data.replace('corrupt_item_', '')
            result = em.process_corruption(user_id, run_state, slot_to_corrupt)
        elif data.startswith('trial_choice_'): result = em.process_trial_choice(user_id, run_state, data.split('_')[-1])
        elif data.startswith('cadiro_deal_'): result = em.process_cadiro_deal(user_id, run_state, accept=(data.split('_')[-1] == 'accept'))
        
        elif data == 'menu_world_boss': result = ui.create_world_boss_main_ui(user_id)
        elif data == 'wb_attack':
            initial_result = wbm.start_boss_fight(user_id)
            if 'character' in initial_result: context.user_data['wb_char_state'] = initial_result.pop('character')
            result = initial_result
        elif data == 'wb_combat_attack':
            char_state = context.user_data.get('wb_char_state')
            if not char_state:
                result = {'text': "❌ *Ошибка боя*\\n\nСостояние боя с мировым боссом было утеряно\\. Пожалуйста, вернитесь в меню ивента\\.", 'buttons': [[InlineKeyboardButton("⬅️ Назад", callback_data='menu_world_boss')]]}
            else:
                combat_result = wbm.process_boss_combat_turn(user_id, char_state)
                if combat_result.get('status') == 'ongoing':
                    context.user_data['wb_char_state'] = combat_result['char_state']
                else:
                    if 'wb_char_state' in context.user_data: del context.user_data['wb_char_state']
                result = combat_result['ui']
        elif data == 'wb_claim_reward':
            reward_message = wbm.claim_reward(user_id)
            await query.answer(escape_markdown(reward_message), show_alert=True)
            result = ui.create_world_boss_main_ui(user_id)

        elif data.startswith('harvest_'):
            if data == 'harvest_beds': result = ui.create_beds_ui(user_id)
            elif data == 'harvest_oshabi': result = ui.create_oshabi_shop_ui(user_id)
            elif data == 'harvest_help': result = ui.create_harvest_help_ui()
            elif data.startswith('harvest_plant_ui:'):
                bed_index = int(data.split(':')[1])
                result = ui.create_seed_planting_ui(user_id, bed_index)
            elif data.startswith('harvest_plant_confirm:'):
                _, bed_index_str, seed_id = data.split(':')
                success, message = harvest_manager.plant_seed(user_id, int(bed_index_str), seed_id)
                await query.answer(escape_markdown(message), show_alert=True)
                if success: result = ui.create_beds_ui(user_id)
            elif data.startswith('harvest_collect:'):
                bed_index = int(data.split(':')[1])
                success, message = harvest_manager.harvest_plant(user_id, bed_index)
                await query.answer(escape_markdown(message), show_alert=True)
                if success: result = ui.create_beds_ui(user_id)
            elif data == 'harvest_buy_fertilizer_ui': result = ui.create_fertilizer_shop_ui(user_id)
            elif data.startswith('harvest_buy_fertilizer:'):
                parts = data.split(':')
                fert_id = parts[1]
                amount = int(parts[2])
                success, message = harvest_manager.buy_fertilizer(user_id, fert_id, amount=amount)
                await query.answer(escape_markdown(message), show_alert=True)
                if success: result = ui.create_fertilizer_shop_ui(user_id)
            elif data == 'harvest_exchange_plants_ui': result = ui.create_plant_exchange_ui(user_id)
            elif data == 'harvest_exchange_all':
                items, lf, cf = harvest_manager.exchange_all_plants(user_id)
                if items == 0: await query.answer("Нечего обменивать\\.", show_alert=True)
                else: await query.answer(f"Вы обменяли {items} растений и получили {lf} 🟢 и {cf} 💎\\.", show_alert=True)
                result = ui.create_plant_exchange_ui(user_id)
            elif data == 'harvest_altar_ui': result = ui.create_lifeforce_altar_ui(user_id)
            elif data == 'harvest_bed_upgrades_ui': result = ui.create_bed_upgrade_ui(user_id)
            elif data.startswith('harvest_buy_upgrade:'):
                up_id = data.split(':')[1]
                success, message = harvest_manager.buy_bed_upgrade(user_id, up_id)
                await query.answer(escape_markdown(message), show_alert=True)
                if success: result = ui.create_bed_upgrade_ui(user_id)
            elif data == 'harvest_casino_ui': result = ui.create_casino_ui(user_id)
            elif data.startswith('harvest_casino_bet:'):
                _, currency, amount = data.split(':')
                bet_result = await harvest_manager.process_casino_bet(user_id, currency, amount)
                if isinstance(bet_result, str):
                    await query.answer(escape_markdown(bet_result), show_alert=True)
                    result = ui.create_casino_ui(user_id)
                else:
                    result = ui.create_casino_ui(user_id, last_bet_result=bet_result)
            elif data == 'harvest_craft_rarity':
                stats = db.get_harvest_stats(user_id)
                text = f"Выберите редкость предмета для создания\\.\n\nВаша Кристаллическая Сила: `{stats.get('crystalline_lifeforce', 0)}` 💎"
                rarity_map = {'magic': 'Магический', 'rare': 'Редкий', 'unique': 'Уникальный', 'legendary': 'Легендарный'}
                buttons = [[{'text': f"{rarity_map.get(r, r.capitalize())} ({c['cost']} 💎)", 'callback_data': f'harvest_craft_start:{r}'}] for r, c in HARVEST_CRAFTING_CONFIG['rarity_config'].items()]
                buttons.append([{'text': "⬅️ Назад к Алтарю", 'callback_data': 'harvest_altar_ui'}])
                result = {'text': text, 'buttons': buttons}
            elif data.startswith('harvest_craft_start:'):
                rarity = data.split(':')[1]
                success, message = await harvest_manager.start_item_craft(user_id, context, rarity)
                if not success: await query.answer(escape_markdown(message), show_alert=True)
                else:
                    floor_buttons = [[{'text': f"Этаж {i}", 'callback_data': f'harvest_craft_set_floor:{i}'} for i in range(1, 3)], [{'text': f"Этаж {i}", 'callback_data': f'harvest_craft_set_floor:{i}'} for i in range(3, 5)], [{'text': "❌ Отмена", 'callback_data': 'harvest_altar_ui'}]]
                    result = {'text': message, 'buttons': floor_buttons}
            elif data.startswith('harvest_craft_set_floor:'):
                floor = int(data.split(':')[1])
                success, message = await harvest_manager.set_craft_floor_and_start(user_id, context, floor)
                if not success:
                    await query.answer(escape_markdown(message), show_alert=True)
                    result = {'text': "Произошла ошибка, попробуйте снова\\.", 'buttons': [[{'text': "⬅️ Назад к Алтарю", 'callback_data': 'harvest_altar_ui'}]]}
                else:
                    slots = ['weapon1', 'weapon2', 'helmet', 'body_armour', 'gloves', 'boots', 'ring1', 'ring2', 'amulet', 'belt']
                    slot_buttons = [[{'text': s, 'callback_data': f'harvest_craft_set_slot:{s}'}] for s in slots]
                    slot_buttons.append([{'text': "❌ Отмена", 'callback_data': 'harvest_altar_ui'}])
                    result = {'text': message, 'buttons': slot_buttons}
            elif data.startswith('harvest_craft_set_slot:'):
                slot = data.split(':', 1)[1]
                if 'item_craft_session' in context.user_data:
                    context.user_data['item_craft_session']['slot'] = slot
                    await query.edit_message_text("Теперь введите уникальное название для вашего предмета в чат. (макс. 30 символов)")
                    context.user_data['awaiting_item_name'] = True
                else:
                    await query.answer("Сессия крафта истекла\\.", show_alert=True)
            elif data.startswith('harvest_craft_add_stat:'):
                stat_id = data.split(':', 1)[1]
                success, message = await harvest_manager.add_stat_to_custom_item(user_id, context, stat_id)
                if not success: await query.answer(escape_markdown(message), show_alert=True)
                result = ui.create_item_crafting_ui(context.user_data['item_craft_session'])
            elif data == 'harvest_craft_reset_stats':
                session = context.user_data.get('item_craft_session')
                if session:
                    session['points'] = session['max_points']
                    session['stats'] = {}
                    result = ui.create_item_crafting_ui(session)
            elif data == 'harvest_craft_confirm':
                session = context.user_data.get('item_craft_session')
                if session and session.get('name') and session.get('slot'):
                    result = {'text': "Вы уверены, что хотите создать этот предмет? Это действие необратимо\\.", 'buttons': [[{'text': "✅ Да, создать!", 'callback_data': 'harvest_craft_finalize'}], [{'text': "⬅️ Нет, назад к редактированию", 'callback_data': 'harvest_craft_back_to_edit'}]]}
                else: await query.answer("Сначала выберите слот и задайте имя\\.", show_alert=True)
            elif data == 'harvest_craft_back_to_edit': result = ui.create_item_crafting_ui(context.user_data['item_craft_session'])
            elif data == 'harvest_craft_finalize':
                success, message = await harvest_manager.finalize_custom_item(user_id, context)
                if success: result = {'text': f"🏆 *Предмет создан\\!* 🏆\n\n{message}", 'buttons': [[{'text': "✅ Отлично!", 'callback_data': 'harvest_altar_ui'}]]}
                else:
                    await query.answer(escape_markdown(message), show_alert=True)
                    result = ui.create_lifeforce_altar_ui(user_id)
        
        # --- НАЧАЛО ИЗМЕНЕНИЙ: Основной блок обработки ---
        if result and isinstance(result, dict) and 'text' in result and 'buttons' in result:
            try:
                await query.edit_message_text(text=result['text'], reply_markup=InlineKeyboardMarkup(result['buttons']), parse_mode=ParseMode.MARKDOWN_V2)
            except BadRequest as e:
                if "Message to edit not found" in str(e):
                    logger.warning(f"Message to edit not found for data '{data}'. Sending new message instead.")
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=result['text'],
                        reply_markup=InlineKeyboardMarkup(result['buttons']),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                else:
                    raise  # Перебрасываем другие ошибки BadRequest
        elif result is not None:
            logger.warning(f"Result for data '{data}' is not a dict with 'text' and 'buttons': {result}")
        # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    except RetryAfter as e:
        logger.warning(f"Flood control exceeded for user {user_id}. Retry in {e.retry_after}s.")
        await query.answer(f"Telegram попросил нас притормозить! Попробуйте снова через {e.retry_after} сек.", show_alert=True)
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"A BadRequest (likely formatting) occurred for data '{data}'", exc_info=True)
            try:
                error_text = "Произошла ошибка при отображении\\.\nВозможно, в названии предмета или монстра есть несовместимый символ\\. Ваш прогресс сохранен\\."
                error_buttons = [[InlineKeyboardButton("🔄 Попробовать продолжить", callback_data='continue_run')], [InlineKeyboardButton("⬅️ В главное меню (завершить забег)", callback_data='leave_run')]]
                # --- ИЗМЕНЕНИЕ: Отправляем новое сообщение в случае ошибки, а не редактируем
                await context.bot.send_message(chat_id=user_id, text=error_text, reply_markup=InlineKeyboardMarkup(error_buttons), parse_mode=ParseMode.MARKDOWN_V2)
            except Exception as inner_e:
                logger.error(f"Could not send the SAFE error message to the user: {inner_e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in button_callback for data '{data}'", exc_info=True)
        try:
            error_text = "🤖 Произошла непредвиденная ошибка в логике игры\\.\nВаш прогресс в этом забеге сохранен\\."
            error_buttons = [[InlineKeyboardButton("🔄 Попробовать продолжить", callback_data='continue_run')], [InlineKeyboardButton("⬅️ В главное меню (завершить забег)", callback_data='leave_run')]]
            # --- ИЗМЕНЕНИЕ: Отправляем новое сообщение в случае ошибки, а не редактируем
            await context.bot.send_message(chat_id=user_id, text=error_text, reply_markup=InlineKeyboardMarkup(error_buttons), parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as inner_e:
            logger.error(f"Could not send the SAFE error message to the user: {inner_e}")


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if context.user_data.get('awaiting_item_name'):
        item_name = update.message.text
        if len(item_name) > 30:
            await update.message.reply_markdown_v2("Название слишком длинное\\. Попробуйте еще раз \\(макс\\. 30 символов\\)\\.")
            return
        
        session = context.user_data.get('item_craft_session')
        if session:
            session['name'] = item_name
            context.user_data['awaiting_item_name'] = False # Снимаем флаг
        
            # Показываем UI для распределения статов
            result = ui.create_item_crafting_ui(session)
            await context.bot.send_message(
                chat_id=user_id,
                text=result['text'],
                reply_markup=InlineKeyboardMarkup(result['buttons']),
                parse_mode=ParseMode.MARKDOWN_V2
            )

