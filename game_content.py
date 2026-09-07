# game_content.py

BASE_STATS = {
    'health': 100, 'max_health': 100, 'energy_shield': 20, 'max_energy_shield': 20,
    'attack': 12, 'crit_chance': 5, 'dodge_chance': 5, 'block_chance': 5, 'defense': 0,
    'accuracy': 0, 'defense_penetration': 0, 'block_penetration': 0, 'double_damage_chance': 0, 'magic_find': 0,
    'es_leech_rate': 0, # <--- ИЗМЕНЕНО ЗДЕСЬ
    'crit_damage_reduction': 0,
}

EVENT_TYPES = [
    {'id': 'бой_обычный', 'name': '⚔️ Обычный бой'},
    {'id': 'бой_редкий', 'name': '💀 Элитный бой'},
    {'id': 'лутгоблин', 'name': '💰 Гоблин с сокровищами'},
    {'id': 'магазин', 'name': '🛒 Магазин'},
    {'id': 'лекарь', 'name': '💖 Лекарь'},
    {'id': 'кузнец', 'name': '🛠️ Кузнец'},
    {'id': 'сундук', 'name': '📦 Сундук'},
    {'id': 'святилище', 'name': '✨ Святилище'},
    {'id': 'алтарь_порчи', 'name': '🔥 Алтарь Порчи'},
    {'id': 'встреча_с_изгнанником', 'name': '👤 Загадочный Изгнанник'},
    {'id': 'испытание_возвышения', 'name': '🏆 Испытание'},
    {'id': 'загадочная_комната', 'name': '❓ Загадочная Комната'}
]
EXPEDITION_CONFIG = {
    'cost': 20000,           # Стоимость в хаос орбах
    'duration_hours': 4     # Длительность в часах
}
CURRENCY = {
    'золото': {'name': '🪙 Золото'},
    'exalted_orb': {'name': '🔮 Exalted Orb'},
    'divine_orb': {'name': '💎 Divine Orb'},
    'mirror': {'name': '🪞 Mirror of Kalandra'}
}

HEALER_PRICES = {
    'half': 25,  # Цена за 50% лечения
    'full': 50   # Цена за 100% лечения
}

SHOP_PRICES = {
    'magic': 25,
    'rare': 70,
    'unique': 200,
    'legendary': 500
}

SMITH_COSTS = {
    'simple_upgrade': 50,
    'blessing': 150,
    'tier_up': 200
}

SMITH_SIMPLE_UPGRADES = {
    'weapon': {
        'attack': 3, 
        'crit_chance': 2,
        'accuracy': 8,
        'defense_penetration': 4,
        'double_damage_chance': 1,
    },
    'armour': {
        'defense': 3, 
        'health': 15,
        'energy_shield': 12,
        'crit_damage_reduction': 5,
        'dodge_chance': 1,
        'block_chance': 1,
    },
    'accessory': {
        'health': 20, 
        'energy_shield': 15,
        'magic_find': 10,
        'es_leech_rate': 1,
    }
}

# ИЗМЕНЕНО: Пул значительно расширен, добавлены новые и гибридные благословения.
SMITH_BLESSINGS_POOL = [
    # --- Обычные благословения (один стат) ---
    {'health': 30},
    {'energy_shield': 25},
    {'attack': 5},
    {'defense': 4},
    {'crit_chance': 3},
    {'dodge_chance': 3},
    {'block_chance': 3},
    {'accuracy': 12},
    {'defense_penetration': 6},
    {'double_damage_chance': 2},
    {'magic_find': 20},
    {'crit_damage_reduction': 8},

    # --- Гибридные благословения (два стата) ---
    # Атакующие
    {'attack': 3, 'crit_chance': 2},          # Благословение Безжалостности
    {'attack': 3, 'accuracy': 8},             # Благословение Точного Удара
    {'crit_chance': 2, 'accuracy': 8},        # Благословение Снайпера
    {'attack': 3, 'defense_penetration': 4},  # Благословение Прорыва
    
    # Защитные
    {'health': 20, 'defense': 2},             # Благословение Бастиона
    {'health': 20, 'block_chance': 2},        # Благословение Стража
    {'dodge_chance': 2, 'health': 15},        # Благословение Акробата
    {'energy_shield': 15, 'defense': 2},      # Благословение Эгиды
    {'defense': 2, 'crit_damage_reduction': 5},# Благословение Несокрушимости

    # Универсальные
    {'health': 15, 'attack': 3},              # Благословение Берсерка
    {'magic_find': 15, 'health': 10},         # Благословение Искателя
]

CLASS_DATA = {
    'marauder': {
        'name': "Мародер (Силач)",
        'desc': "Мастер грубой силы. Начинает с огромным запасом здоровья и повышенной атакой.",
        'stats': {
            'health': 150, 'max_health': 150, 'energy_shield': 10, 'max_energy_shield': 10,
            'attack': 15, 'crit_chance': 5, 'dodge_chance': 0, 'block_chance': 5, 'defense': 5,
            'accuracy': 0, 'defense_penetration': 0, 'block_penetration': 0, 'double_damage_chance': 0, 'magic_find': 0,
            'es_leech_rate': 0, 'crit_damage_reduction': 0,
            # --- НОВАЯ ОСОБЕННОСТЬ ---
            'cannot_be_crit': True
        }
    },
    'witch': {
        'name': "Ведьма (Интеллект)",
        'desc': "Повелительница магии и энергощита. Конвертирует часть своего здоровья в дополнительный энергощит.",
        'stats': {
            'health': 70, 'max_health': 70, 'energy_shield': 60, 'max_energy_shield': 60,
            'attack': 15, 'crit_chance': 10, 'dodge_chance': 5, 'block_chance': 0, 'defense': 0,
            'accuracy': 0, 'defense_penetration': 0, 'block_penetration': 0, 'double_damage_chance': 0, 'magic_find': 0,
            'es_leech_rate': 2, 'crit_damage_reduction': 0,
            # --- НОВАЯ ОСОБЕННОСТЬ ---
            'arcane_substitution': True  # <-- НОВЫЙ ФЛАГ
        }
    },
    'ranger': {
        'name': "Охотница (Ловкость)",
        'desc': "Неуловимый боец дальнего боя. Высокая точность и шанс уворота делают её сложной целью.",
        'stats': {
            'health': 90, 'max_health': 90, 'energy_shield': 15, 'max_energy_shield': 15,
            'attack': 12, 'crit_chance': 5, 'dodge_chance': 12, 'block_chance': 5, 'defense': 0,
            'accuracy': 30, 'defense_penetration': 0, 'block_penetration': 0, 'double_damage_chance': 0, 'magic_find': 0,
            'es_leech_rate': 0, 'crit_damage_reduction': 0,
            # --- НОВАЯ ОСОБЕННОСТЬ ---
            'cannot_be_dodged': True
            
        }
    },
    'duelist': {
        'name': "Дуэлянт (Сила/Ловкость)",
        'desc': "Искусный фехтовальщик, сочетающий атаку и защиту. Мастер блоков и вампиризма.",
        'stats': {
            'health': 100, 'max_health': 100, 'energy_shield': 5, 'max_energy_shield': 5,
            'attack': 12, 'crit_chance': 3, 'dodge_chance': 2, 'block_chance': 6, 'defense': 5,
            'accuracy': 5, 'defense_penetration': 0, 'block_penetration': 0, 'double_damage_chance': 0, 'magic_find': 0,
            'es_leech_rate': 0, 'lifesteal': 2, 'crit_damage_reduction': 0,
            # --- НОВАЯ ОСОБЕННОСТЬ ---
            'cannot_be_blocked': True
        }
    },
    'templar': {
        'name': "Храмовник (Сила/Интеллект)",
        'desc': "Святой воин, полагающийся на прочную броню и баланс между здоровьем и энергощитом.",
        'stats': {
            'health': 120, 'max_health': 120, 'energy_shield': 40, 'max_energy_shield': 40,
            'attack': 11, 'crit_chance': 5, 'dodge_chance': 0, 'block_chance': 5, 'defense': 8,
            'accuracy': 0, 'defense_penetration': 0, 'block_penetration': 0, 'double_damage_chance': 0, 'magic_find': 0,
            'es_leech_rate': 0, 'crit_damage_reduction': 20,
            # --- НАЧАЛО ИЗМЕНЕНИЙ ---
            'immune_to_double_damage': True
            # --- КОНЕЦ ИЗМЕНЕНИЙ ---
        }
    },
    'shadow': {
        'name': "Тень (Ловкость/Интеллект)",
        'desc': "Коварный убийца, наносящий огромный критический урон. Выживает за счет уклонения от ударов.",
        'stats': {
            'health': 100, 'max_health': 100, 'energy_shield': 35, 'max_energy_shield': 35,
            'attack': 15, 'crit_chance': 15, 'dodge_chance': 10, 'block_chance': 0, 'defense': 0,
            'accuracy': 15, 'defense_penetration': 5, 'block_penetration': 0, 'double_damage_chance': 3, 'magic_find': 50,
            'es_leech_rate': 5, 'crit_damage_reduction': 0,
            # --- НОВАЯ ОСОБЕННОСТЬ ---
            'crit_pen': 50
            
        }
    },
    'scion': {
        'name': "Дворянка (Все статы)",
        'desc': "Наследница падшей империи. Сбалансированный класс, способный адаптироваться к любому стилю игры.",
        'stats': {
            'health': 110, 'max_health': 110, 'energy_shield': 20, 'max_energy_shield': 20,
            'attack': 11, 'crit_chance': 6, 'dodge_chance': 6, 'block_chance': 6, 'defense': 3,
            'accuracy': 10, 'defense_penetration': 3, 'block_penetration': 3, 'double_damage_chance': 1, 'magic_find': 10,
            'es_leech_rate': 1, 'lifesteal': 1, 'crit_damage_reduction': 5,
            'es_bypass_immunity': True 
        }
    }
}
PLAYER_XP_PER_LEVEL = [0] + [int(300 * (1.18 ** i)) for i in range(1, 101)]
# =============================================================================
# НОВАЯ СИСТЕМА: ОПРЕДЕЛЕНИЕ КОМПЛЕКТОВ ПРЕДМЕТОВ (СЕТОВ)
# =============================================================================
ITEM_SETS = {
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Обновленные старые сеты ---
    'hyrri': {
        'name': "Наследие Хюрри", 'pieces': 2,
        'bonus': {'effect': {'dodge_chance': 20, 'accuracy': 70}, 'desc': "+20% к шансу уворота и +70 к точности"}
    },
    'brute': {
        'name': "Объятия Дикаря", 'pieces': 3,
        'bonus': {'effect': {'health': 120, 'attack': 20, 'defense_penetration': 25}, 'desc': "+120 к здоровью, +20 к атаке и +25% к пробитию защиты"}
    },
    'viper': {
        'name': "Поцелуй Гадюки", 'pieces': 2,
        'bonus': {'effect': {'crit_chance': 10, 'accuracy': 30, 'crit_multiplier': 40}, 'desc': "+10% к шансу крит. удара, +30 к точности и +40% к множителю крит. урона"}
    },
    'acolyte': {
        'name': "Решимость Послушника", 'pieces': 3,
        'bonus': {'desc': "Преобразует 50% от вашего общего процента Защиты в шанс критического удара.", 'special_mechanic': 'defense_to_crit_conversion'}
    },
    'gilded': {
        'name': "Позолоченный Клад", 'pieces': 2,
        'bonus': {'desc': "+120% к поиску магических предметов и +1 к атаке за каждые 200 золота (вплоть до +25).", 'special_mechanic': 'attack_scaling_from_gold'}
    },
    'bulwark': {
        'name': "Бастион Последнего Рубежа", 'pieces': 3,
        'bonus': {'effect': {'block_chance': 10, 'crit_damage_reduction': 50, 'heal_on_block_percent': 5}, 'desc': "+10% к блоку, +50% защиты от крита и восстанавливает 5% здоровья при блоке."}
    },
    # --- КОНЕЦ ИЗМЕНЕНИЙ: Обновленные старые сеты ---
    'stormrider': {
        'name': "Ярость Наездника на Буре", 'pieces': 2,
        'bonus': {'effect': {'double_damage_chance': 15}, 'desc': "+15% к шансу нанести двойной урон"}
    },
    'executioner': {
        'name': "Правосудие Палача", 'pieces': 3,
        'bonus': {'effect': {'defense_penetration': 55}, 'desc': "+55% к пробитию защиты"}
    },
    'scholar': {
        'name': "Путь Ученого", 'pieces': 2,
        'bonus': {'effect': {'attack_from_es_percent': 0.10}, 'desc': "Вы получаете бонус к атаке в размере 10% от вашего макс. энергощита"}
    },
    'shadow': {
        'name': "Покров Тени", 'pieces': 3,
        'bonus': {
            'desc': "Конвертирует 100% вампиризма энергощита в вампиризм здоровья и дает +12% к увороту.", 
            'special_mechanic': 'es_leech_to_lifesteal_conversion',
            'effect': {'dodge_chance': 12}
        }
    },
    # --- НАЧАЛО НОВЫХ СЕТОВ ---
    'retribution': {
        'name': "Авангард Возмездия", 'pieces': 2,
        'bonus': {'desc': "Ваша атака увеличивается на 50% от вашего шанса блока.", 'special_mechanic': 'attack_scaling_from_block_chance'}
    },
    'deadeye': {
        'name': "Незримый Путь", 'pieces': 3,
        'bonus': {'desc': "Вы получаете +1 к атаке за каждые 10 единиц точности.", 'special_mechanic': 'attack_scaling_from_accuracy'}
    },
    'void_touched': {
        'name': "Облачение Коснувшегося Бездны", 'pieces': 3,
        'bonus': {'desc': "+5% ко всем основным статам (Атака, Защита, Уворот, Блок, Крит) за каждый оскверненный предмет.", 'special_mechanic': 'bonus_per_corrupted_item_set'}
    },
    'crimson_pact': {
        'name': "Багровый Пакт", 'pieces': 2,
        'bonus': {'desc': "Когда ваше здоровье ниже 50%, вы получаете +10% к вампиризму и наносите на 20% больше урона.", 'special_mechanic': 'berserker_on_low_life'}
    },
    'arcane_weaver': {
        'name': "Наряд Тайного Ткача", 'pieces': 3,
        'bonus': {'desc': "Крит. удары тратят 5% энергощита для +100% к множителю крита.", 'special_mechanic': 'crit_consumes_es_for_mult'}
    }
    # --- КОНЕЦ НОВЫХ СЕТОВ ---
}

# =============================================================================
# НОВЫЕ ПРЕДМЕТЫ: СЕТЫ И РАСШИРЕНИЕ ЛУТ-ПУЛА
# =============================================================================
NEW_STRANGE_ITEMS = {
    'floor_3': {
        'unique': [
            # --- НАЧАЛО НОВЫХ ПРЕДМЕТОВ ДЛЯ СЕТОВ ---
            {'name': "Молот Правосудия", 'type': 'Одноручная булава', 'slot': 'weapon1', 'set_id': 'retribution', 
             'stats': {'attack': 28, 'block_chance': 5}},
            {'name': "Щит Возмездия", 'type': 'Щит', 'slot': 'weapon2', 'set_id': 'retribution', 
             'stats': {'block_chance': 14, 'health': 90}},
            {'name': "Взор Снайпера", 'type': 'Шлем', 'slot': 'helmet', 'set_id': 'deadeye', 
             'stats': {'accuracy': 60, 'crit_chance': 5}},
            {'name': "Пояс Энтропии", 'type': 'Пояс', 'slot': 'belt', 'set_id': 'void_touched', 
             'stats': {'health': 110, 'crit_damage_reduction': 20}},
            {'name': "Жало Отчаяния", 'type': 'Кинжал', 'slot': 'weapon1', 'set_id': 'crimson_pact', 
             'stats': {'attack': 25, 'lifesteal': 3}, 'conditional_stats': {'crit_chance': {'condition': 'health_below_50', 'value': 15}}},
            {'name': "Скипетр Разряда", 'type': 'Жезл', 'slot': 'weapon1', 'set_id': 'arcane_weaver', 
             'stats': {'attack': 20, 'energy_shield': 70}},
            # --- КОНЕЦ НОВЫХ ПРЕДМЕТОВ ДЛЯ СЕТОВ ---
            {'name': "Хрупкая Корона", 'type': 'Шлем', 'slot': 'helmet', 
             'stats': {'block_chance': 40}, 
             'special_mechanic': 'always_be_critted'},
            {'name': "Проблеск Надежды", 'type': 'Щит', 'slot': 'weapon2', 
             'stats': {'block_chance': 12, 'health': 130}, 
             'special_mechanic': 'debuff_attack_on_first_block'},
            {'name': "Сосуд Нестабильности", 'type': 'Пояс', 'slot': 'belt', 
             'stats': {'health': 100}, 
             'special_mechanic': 'random_base_attack_per_fight'},
            {'name': "Пояс Последний Вдох", 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 50}, 'special_mechanic': 'attack_scaling_on_missing_health'},
            {'name': "Корона Отчаяния", 'type': 'Шлем', 'slot': 'helmet', 'stats': {'dodge_chance_override': 0, 'block_chance': 25, 'health': 100}},
            {'name': "Клятва Азири", 'type': 'Амулет', 'slot': 'amulet', 'stats': {'double_damage_chance': 25}, 'special_mechanic': 'health_degen_on_turn_start'},
            {'name': "Печать Баланса", 'type': 'Кольцо', 'slot': 'ring', 'stats': {'crit_chance_override': 0}, 'special_mechanic': 'balance_dodge_block'},
            {'name': "Прикосновение Разлома", 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 10}, 'conditional_stats': {'attack_mult': {'condition': 'not_hit_last_turn', 'value': 0.25}}},
            {'name': "Поступь Фантома", 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 8}, 'on_dodge_effect': {'guaranteed_crit_next_hit': True}},
            {'name': "Зеркало Души", 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 10}, 'on_block_effect': {'es_heal_percent': 5}},
        ],
        'legendary': [
            {'name': "Грань Пустоты", 'type': 'Двуручный меч', 'slot': 'weapon1', 'stats': {'attack': 50, 'lifesteal': 5}, 'special_mechanic': 'lifesteal_leeches_es_instead'},
            {'name': "Наследие Вождя", 'type': 'Амулет', 'slot': 'amulet', 'stats': {'health': 80}, 'scaling_stats': {'attack': {'source': 'max_health', 'ratio': 0.05}}},
            {'name': "Кровавый Ритуал", 'type': 'Кольцо', 'slot': 'ring', 'stats': {'lifesteal': 15}, 'special_mechanic': 'healing_damages_you'},
            {'name': "Цепи Титана", 'type': 'Пояс', 'slot': 'belt', 'stats': {'crit_multiplier': 100, 'crit_chance_cap': 15}},
            {'name': "Ртутная Поступь", 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 25, 'defense_mult': -0.5}},
            {'name': "Жертвенный Клинок", 'type': 'Одноручный меч', 'slot': 'weapon1', 'stats': {'attack': 20}, 'on_attack_effect': {'self_es_damage_percent': 20, 'add_damage_from_es_cost': 1.0}},
        ]
    },
    'floor_4': {
        'unique': [
            # --- НАЧАЛО НОВЫХ ПРЕДМЕТОВ ДЛЯ СЕТОВ ---
            {'name': "Хватка Меткого", 'type': 'Перчатки', 'slot': 'gloves', 'set_id': 'deadeye', 
             'stats': {'accuracy': 70, 'attack': 10}},
            {'name': "Талисман Концентрации", 'type': 'Амулет', 'slot': 'amulet', 'set_id': 'deadeye', 
             'stats': {'accuracy': 50, 'cannot_be_dodged': True}},
            {'name': "Одеяние Искажения", 'type': 'Нательная броня', 'slot': 'body_armour', 'set_id': 'void_touched', 
             'stats': {'health': 120, 'energy_shield': 120, 'defense': 10}},
            {'name': "Кольцо Разлома", 'type': 'Кольцо', 'slot': 'ring', 'set_id': 'void_touched', 
             'stats': {'attack': 10, 'crit_chance': 5}},
            {'name': "Нагрудник Последнего Рубежа", 'type': 'Нательная броня', 'slot': 'body_armour', 'set_id': 'crimson_pact', 
             'stats': {'health': 150}, 'conditional_stats': {'defense': {'condition': 'health_below_50', 'value': 30}}},
            {'name': "Диадема Мыслителя", 'type': 'Шлем', 'slot': 'helmet', 'set_id': 'arcane_weaver', 
             'stats': {'energy_shield': 150, 'crit_chance': 4}},
            {'name': "Рукавицы Похитителя Сущности", 'type': 'Перчатки', 'slot': 'gloves', 'set_id': 'arcane_weaver', 
             'stats': {'energy_shield': 80, 'es_leech_rate': 3}},
            # --- КОНЕЦ НОВЫХ ПРЕДМЕТОВ ДЛЯ СЕТОВ ---
            {'name': "Око Истины", 'type': 'Амулет', 'slot': 'amulet', 'stats': {'dodge_chance': 5}, 'special_mechanic': 'dodge_to_crit_conversion'},
            {'name': "Последний довод Королей", 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 10, 'double_damage_chance': 20, 'crit_chance_override': 0}},
            {'name': "Корона Тирана", 'type': 'Шлем', 'slot': 'helmet', 'stats': {'health': 100}, 'special_mechanic': 'amplify_set_bonuses'},
            {'name': "Катализатор", 'type': 'Пояс', 'slot': 'belt', 'stats': {'increased_damage_taken': 0.25, 'attack_mult': 0.25}},
            {'name': "Хватка Агонии", 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 15}, 'conditional_stats': {'crit_multiplier': {'condition': 'enemy_full_health', 'value': 100}}},
            {'name': "Обреченность Ваал", 'type': 'Кольцо', 'slot': 'ring', 'stats': {}, 'special_mechanic': 'bonus_per_corrupted_item'},
            {'name': "Одеяние Схизмы", 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {}, 'special_mechanic': 'split_health_es_pool'},
        ],
        'legendary': [
            {'name': "Эгида Святого", 'type': 'Щит', 'slot': 'weapon2', 
             'stats': {'block_chance': 18, 'energy_shield': 120}, 
             'special_mechanic': 'healing_overflow_to_es'},
            {'name': "Кровью выкованный Клинок", 'type': 'Одноручный меч', 'slot': 'weapon1', 
             'stats': {'attack': 55, 'crit_chance': 8}, 
             'special_mechanic': 'crit_costs_hp_for_damage'},
            {'name': "Камень Алхимика", 'type': 'Кольцо', 'slot': 'ring', 
             'stats': {'magic_find': 25, 'health': 70}, 
             'special_mechanic': 'transmute_on_pickup_chance'},
            {'name': "Искаженная Душа", 'type': 'Амулет', 'slot': 'amulet', 
             'stats': {'health': 120, 'energy_shield': 120}, 
             'special_mechanic': 'leech_per_corrupted_item'},
             {'name': "Приговор Грешника", 'type': 'Амулет', 'slot': 'amulet', 
             'stats': {'attack': -20, 'accuracy': 100}, 
             'special_mechanic': 'cannot_be_dodged_and_blocked'},
            {'name': "Разрыв Завесы", 'type': 'Кольцо', 'slot': 'ring', 
             'stats': {'attack': -10}, 
             'special_mechanic': 'bypass_es_50_percent'},
            {'name': "Хватка Паучихи", 'type': 'Перчатки', 'slot': 'gloves', 
             'stats': {'lifesteal': 5},
             'special_mechanic': 'anti_leech_on_crit'},
            {'name': "Предвестник Заката", 'type': 'Двуручный меч', 'slot': 'weapon1', 'stats': {'attack': 40, 'defense_penetration': 25, 'double_damage_chance_override': 0, 'penetration_cap_override': 1000}},
            {'name': "Эгида Бессмертия", 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 200}, 'special_mechanic': 'death_defiance_once'},
            {'name': "Взгляд Безумия", 'type': 'Шлем', 'slot': 'helmet', 'stats': {'accuracy': 100}, 'scaling_stats': {'double_damage_chance': {'source': 'accuracy', 'ratio': 0.25}}},
            {'name': "Единство", 'type': 'Кольцо', 'slot': 'ring', 'stats': {'health': 75}, 'special_mechanic': 'forgiving_set_bonus'},
            {'name': "Узы Крови", 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 400}, 'special_mechanic': 'es_to_health_no_es'},
            {'name': "Призрачные Танцоры", 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 20}, 'on_dodge_effect': {'heal_percent_on_dodge': 5}},
            {'name': "Воля Императора", 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 10, 'cannot_be_blocked': True}, 'scaling_stats': {'defense_penetration': {'source': 'block_chance', 'ratio': 0.5}}},
        ]
    }
}

NEW_MECHANIC_ITEMS = {
    'floor_1': {
        'unique': [
            {'name': "Железная хватка", 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'health': 10}, 'scaling_stats': {'max_health': {'source': 'defense', 'ratio': 2}}},
            {'name': "Одинокий волк", 'type': 'Одноручный меч', 'slot': 'weapon1', 'stats': {'attack': 5}, 'conditional_stats': {'crit_chance': {'condition': 'offhand_empty', 'value': 15}}},
            {'name': "Кровавая связь", 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 20}, 'conditional_stats': {'attack': {'condition': 'health_below_50', 'value': 20}}},
            {'name': "Хитрость Ондара", 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'cannot_be_dodged': True, 'crit_chance': -2}},
            {'name': "Красный сон", 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 10}, 'on_block_effect': {'heal_percent': 5}},
        ]
    },
    'floor_2': {
        'unique': [
            {'name': "Эгида возмездия", 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 10}, 'scaling_stats': {'attack': {'source': 'block_chance', 'ratio': 0.5}}},
            {'name': "Стеклянная пушка", 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'attack': 30, 'block_chance': -15, 'dodge_chance': -15}}, # -50 защиты = обнуление
            {'name': "Клинки танцора", 'type': 'Когти', 'slot': 'weapon1', 'stats': {'dodge_chance': 8}, 'scaling_stats': {'crit_chance': {'source': 'dodge_chance', 'ratio': 0.3}}},
            {'name': "Корона мщения", 'type': 'Шлем', 'slot': 'helmet', 'stats': {'health': 50}, 'on_crit_taken_effect': {'add_attack_next_hit': 30}},
            {'name': "Солнечный камень", 'type': 'Амулет', 'slot': 'amulet', 'stats': {}, 'special_mechanic': 'es_to_health_conversion'},
        ]
    },
    'floor_3': {
        'unique': [
            {'name': "Неостановимая сила", 'type': 'Одноручная булава', 'slot': 'weapon1', 'stats': {'attack': 15, 'cannot_be_blocked': True}},
            {'name': "Порочное сердце", 'type': 'Амулет', 'slot': 'amulet', 'stats': {'crit_chance': 5}, 'on_crit_effect': {'defense_penetration': 50}},
            {'name': "Оплот горы", 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 200}, 'on_hit_taken_effect': {'add_defense_temp': 25}},
            {'name': "Око снайпера", 'type': 'Щит', 'slot': 'weapon2', 'stats': {'accuracy': 20}, 'scaling_stats': {'crit_multiplier': {'source': 'accuracy', 'ratio': 0.5}}}, # +5% за 10 точности
        ],
        'legendary': [
            {'name': "Последний рубеж", 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 10}, 'conditional_stats': {'double_damage_chance': {'condition': 'health_below_30', 'value': 40}}},
        ]
    },
    'floor_4': {
        'legendary': [
            {'name': "Бесформенное пламя", 'type': 'Шлем', 'slot': 'helmet', 'stats': {'health': 120, 'cannot_be_crit': True}},
            {'name': "Доспех из шипов", 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'defense': 40}, 'special_mechanic': 'reflect_damage_25'},
            {'name': "Взгляд бездны", 'type': 'Двуручный меч', 'slot': 'weapon1', 'stats': {'attack': 60}, 'on_attack_effect': {'self_damage_percent': 5}},
            {'name': "Наследие аскета", 'type': 'Амулет', 'slot': 'amulet', 'set_id': 'hyrri', 'stats': {}, 'special_mechanic': 'bonus_per_empty_slot'},
            {'name': "Трансцендентный разум", 'type': 'Шлем', 'slot': 'helmet', 'stats': {'health': 300}, 'special_mechanic': 'full_es_to_health'},
        ]
    }
}

NEW_SET_AND_EXPANSION_ITEMS = {
    'floor_1': {
        'rare': [
            {'name': "Шлем Дикаря", 'type': 'Шлем', 'slot': 'helmet', 'set_id': 'brute', 'stats': {'health': 25, 'attack': 4}},
            {'name': "Кольчуга Хюрри", 'type': 'Нательная броня', 'slot': 'body_armour', 'set_id': 'hyrri', 'stats': {'dodge_chance': 5, 'health': 30}},
            {'name': 'Коготь Гадюки', 'type': 'Когти', 'slot': 'weapon1', 'set_id': 'viper', 'stats': {'crit_chance': 3, 'attack': 8}},
            {'name': 'Взгляд Ястреба', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'accuracy': 35, 'crit_chance': 2}}, # Новый предмет
        ],
        'unique': [
            {'name': "Ботинки Хюрри", 'type': 'Ботинки', 'slot': 'boots', 'set_id': 'hyrri', 'stats': {'dodge_chance': 6, 'health': 35}},
            {'name': 'Пояс Искателя', 'type': 'Пояс', 'slot': 'belt', 'set_id': 'gilded', 'stats': {'magic_find': 30, 'health': 25}},
        ]
    },
    'floor_2': {
        'rare': [
            {'name': "Рукавицы Дикаря", 'type': 'Перчатки', 'slot': 'gloves', 'set_id': 'brute', 'stats': {'health': 30, 'attack': 5}},
            {'name': "Одеяние Послушника", 'type': 'Нательная броня', 'slot': 'body_armour', 'set_id': 'acolyte', 'stats': {'energy_shield': 40, 'defense': 5}},
            {'name': "Щит Бастиона", 'type': 'Щит', 'slot': 'weapon2', 'set_id': 'bulwark', 'stats': {'block_chance': 6, 'defense': 10}},
            {'name': 'Прошитый Рунами Пояс', 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 45, 'energy_shield': 25}}, # Новый предмет
        ],
        'unique': [
            {'name': "Маска Гадюки", 'type': 'Шлем', 'slot': 'helmet', 'set_id': 'viper', 'stats': {'crit_chance': 4, 'accuracy': 30}},
            {'name': "Клинок Наездника на Буре", 'type': 'Одноручный меч', 'slot': 'weapon1', 'set_id': 'stormrider', 'stats': {'attack': 17, 'double_damage_chance': 4}},
            {'name': 'Око Грифона', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'magic_find': 50, 'crit_chance': 4}}, # Новый предмет
        ],
        'legendary': [
             {'name': "Перстень Удачи", 'type': 'Кольцо', 'slot': 'ring', 'set_id': 'gilded', 'stats': {'magic_find': 55, 'health': 20}},
        ]
    },
    'floor_3': {
        'rare': [
            {'name': "Наголенники Дикаря", 'type': 'Ботинки', 'slot': 'boots', 'set_id': 'brute', 'stats': {'health': 70, 'dodge_chance': -2}},
            {'name': "Перчатки Послушника", 'type': 'Перчатки', 'slot': 'gloves', 'set_id': 'acolyte', 'stats': {'energy_shield': 35, 'es_leech_rate': 1}},
            {'name': "Перчатки Палача", 'type': 'Перчатки', 'slot': 'gloves', 'set_id': 'executioner', 'stats': {'attack': 8, 'defense_penetration': 25}},
            {'name': "Кираса Бастиона", 'type': 'Нательная броня', 'slot': 'body_armour', 'set_id': 'bulwark', 'stats': {'health': 90, 'defense': 12}},
            {'name': "Плащ Тени", 'type': 'Нательная броня', 'slot': 'body_armour', 'set_id': 'shadow', 'stats': {'dodge_chance': 6, 'health': 60}},
            {'name': "Сфера Мыслителя", 'type': 'Жезл', 'slot': 'weapon1', 'set_id': 'scholar', 'stats': {'energy_shield': 40,  'attack': 10}},
            {'name': 'Кольцо Титана', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'health': 70, 'attack': 5}}, # Новый предмет
        ],
        'unique': [
            {'name': "Щит Наездника на Буре", 'type': 'Щит', 'slot': 'weapon2', 'set_id': 'stormrider', 'stats': {'block_chance': 7, 'double_damage_chance': 5}},
            {'name': "Сапоги Бастиона", 'type': 'Ботинки', 'slot': 'boots', 'set_id': 'bulwark', 'stats': {'health': 70, 'block_chance': 3}},
            {'name': "Маска Тени", 'type': 'Шлем', 'slot': 'helmet', 'set_id': 'shadow', 'stats': {'dodge_chance': 5, 'crit_damage_reduction': 25}},
        ],
        'legendary': [
            {'name': "Лик Палача", 'type': 'Шлем', 'slot': 'helmet', 'set_id': 'executioner', 'stats': {'attack': 14, 'defense_penetration': 15, 'crit_chance': 5}},
            {'name': 'Талисман Знаний', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'health': 80, 'energy_shield': 80, 'magic_find': -20}}, # Новый предмет
        ]
    },
    'floor_4': {
        'rare': [
            {'name': "Сапоги Послушника", 'type': 'Ботинки', 'slot': 'boots', 'set_id': 'acolyte', 'stats': {'energy_shield': 40, 'dodge_chance': 4}},
            {'name': "Ботинки Тени", 'type': 'Ботинки', 'slot': 'boots', 'set_id': 'shadow', 'stats': {'dodge_chance': 7, 'health': 50}},
            {'name': 'Бастион Мысли', 'type': 'Нательная броня', 'slot': 'body_armour', 
            'stats': {'energy_shield': 100, 'health': 70}, 
            'special_mechanic': 'es_bypass_immunity'},
            {'name': 'Клинок Неизбежности', 'type': 'Одноручный меч', 'slot': 'weapon1', 
            'stats': {'attack': 10, 'accuracy': 50}, 
            'special_mechanic': 'cannot_be_dodged_and_blocked'},
            {'name': 'Кольцо Верного Удара', 'type': 'Кольцо', 'slot': 'ring', 
            'stats': {'attack': 15, 'health': -400}, 
            'special_mechanic': 'cannot_be_dodged_and_blocked'},
            {'name': 'Коготь Разрыва Души', 'type': 'Когти', 'slot': 'weapon1', 
            'stats': {'attack': 32, 'crit_chance': 5}, 
            'special_mechanic': 'bypass_es_50_percent'},
            {'name': 'Амулет Разлома', 'type': 'Амулет', 'slot': 'amulet', 
            'stats': {'defense_penetration': 20, 'health': 50}, 
            'special_mechanic': 'bypass_es_50_percent'},
            {'name': 'Зазубренный Колчан', 'type': 'Колчан (Щит)', 'slot': 'weapon2', 
            'stats': {'crit_chance': 6, 'accuracy': 40}, 
            'special_mechanic': 'anti_leech_on_crit'},
        ],
        'unique': [
            {'name': "Диадема Ученого", 'type': 'Шлем', 'slot': 'helmet', 'set_id': 'scholar', 'stats': {'energy_shield': 65, 'crit_chance': 5}},
            {'name': "Гильотина Палача", 'type': 'Двуручный топор', 'slot': 'weapon1', 'set_id': 'executioner', 'stats': {'attack': 30, 'defense_penetration': 30}},
            {'name': "Хватка Тени", 'type': 'Перчатки', 'slot': 'gloves', 'set_id': 'shadow', 'stats': {'lifesteal': 5, 'attack': 10}},
            {'name': 'Взор Немигающего', 'type': 'Шлем', 'slot': 'helmet', 
            'stats': {'health': 200, 'dodge_chance': -25, 'block_chance': -25}, 
            'special_mechanic': 'cannot_be_dodged_and_blocked'},
            {'name': 'Молот-Миролом', 'type': 'Двуручная булава', 'slot': 'weapon1', 
            'stats': {'attack': 60, 'crit_chance_override': 0}, 
            'special_mechanic': 'cannot_be_dodged_and_blocked'},
            {'name': 'Перчатки Коснувшегося Бездны', 'type': 'Перчатки', 'slot': 'gloves', 
            'stats': {'attack': 40, 'max_energy_shield': -100, 'block_chance': -25}, 
            'special_mechanic': 'bypass_es_50_percent'},
            {'name': 'Сделка Паразита', 'type': 'Кольцо', 'slot': 'ring', 
            'stats': {'crit_chance': 15, 'lifesteal': -5, 'es_leech_rate': -5}, 
            'special_mechanic': 'anti_leech_on_crit'},
            {'name': 'Око Злобы', 'type': 'Амулет', 'slot': 'amulet', 
            'stats': {'crit_chance': 3, 'crit_multiplier': 30}, 
            'special_mechanic': 'anti_leech_on_crit'},
            {'name': 'Непоколебимая Воля', 'type': 'Амулет', 'slot': 'amulet', 
            'stats': {'energy_shield': 200, 'dodge_chance': -15}, 
            'special_mechanic': 'es_bypass_immunity'},
            {'name': 'Поступь Эфирного Ткача', 'type': 'Ботинки', 'slot': 'boots', 
            'stats': {'energy_shield': 50, 'es_leech_rate': 2}, 
            'special_mechanic': 'es_bypass_immunity'},
        ],
        'legendary': [
            {'name': "Шлем Бастиона", 'type': 'Шлем', 'slot': 'helmet', 'set_id': 'bulwark', 'stats': {'defense': 20, 'crit_damage_reduction': 30}},
            {'name': 'Пояс Неуязвимости', 'type': 'Пояс', 'slot': 'belt', 'stats': {'defense': 10, 'dodge_chance': 8, 'block_chance': 8, 'health': 120}}, # Новый предмет
            {'name': 'Эгида Вечного', 'type': 'Щит', 'slot': 'weapon2', 
            'stats': {'energy_shield': 150, 'block_chance': 15, 'crit_damage_reduction': 30}, 
            'special_mechanic': 'es_bypass_immunity'},
            {'name': 'Диадема Непроницаемости', 'type': 'Шлем', 'slot': 'helmet', 
            'stats': {'energy_shield': 200}, 
            'scaling_stats': {'crit_chance': {'source': 'max_energy_shield', 'ratio': 0.02}}, # +2% крита за 100 щита
            'special_mechanic': 'es_bypass_immunity'},
        ]
    }
}
# =============================================================================
# НОВЫЕ ПРЕДМЕТЫ С НОВЫМИ СТАТАМИ
# =============================================================================

# --- НОВЫЕ ПРЕДМЕТЫ ЭТАЖА 1 ---
FLOOR_1_NEW_ITEMS = {
    'magic': [
        {'name': 'Кольцо Точности', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'accuracy': 10, 'attack': 3}},
        {'name': 'Амулет Искателя', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'magic_find': 15, 'attack': 2}},
        {'name': 'Заостренный Топор', 'type': 'Одноручный топор', 'slot': 'weapon1', 'stats': {'attack': 4, 'defense_penetration': 10}},
        {'name': 'Ботинки Авантюриста', 'type': 'Ботинки', 'slot': 'boots', 'set_id': 'gilded', 'stats': {'magic_find': 10, 'dodge_chance': 3}},
        {'name': 'Шлем Пронзателя', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'magic_find': 15, 'defense_penetration': 15}},
        {'name': 'Перчатки Снайпера', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'accuracy': 8, 'attack': 3}},
        {'name': 'Пояс с Самоцветами', 'type': 'Пояс', 'slot': 'belt', 'stats': {'magic_find': 12, 'health': 12}},
        {'name': 'Скипетр Разрушителя', 'type': 'Одноручная булава', 'slot': 'weapon1', 'stats': {'double_damage_chance': 2, 'attack': 6}},
        {'name': 'Щит Стража', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'crit_damage_reduction': 10, 'energy_shield': 10}},
        {'name': 'Эфирный Щит', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'es_leech_rate': 2, 'energy_shield': 20}},
    ],
    'rare': [
        {'name': 'Хватка Убийцы', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'accuracy': 15, 'crit_chance': 3}},
        {'name': 'Поступь Призрака', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 3, 'magic_find': 25}},
        {'name': 'Взгляд Палача', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'defense_penetration': 15, 'attack': 4}},
        {'name': 'Кольцо Алчности', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'magic_find': 20, 'health': 15}},
        {'name': 'Амулет Удачи', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'magic_find': 25, 'crit_chance': 3}},
        {'name': 'Кровавый Тесак', 'type': 'Одноручный меч', 'slot': 'weapon1', 'stats': {'attack': 10, 'double_damage_chance': 2}},
        {'name': 'Оплот из Кости', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 5, 'crit_damage_reduction': 10}},
        {'name': 'Перевязь Искателя Сокровищ', 'type': 'Пояс', 'slot': 'belt', 'stats': {'magic_find': 18, 'health': 25}},
        {'name': 'Наручи Точного Удара', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'accuracy': 15, 'attack': 4}},
         {'name': 'Эгида Восстановления', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'es_leech_rate': 3, 'energy_shield': 25}},
    ],
    'unique': [
        {'name': "Ondar's Clasp", 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'accuracy': 30, 'dodge_chance': 5}},
        {'name': 'The Sadist Garb', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'double_damage_chance': 5, 'attack': 7}},
        {'name': 'Karui Ward', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'accuracy': 25, 'health': 25}},
        {'name': 'The Magnate', 'type': 'Пояс', 'slot': 'belt', 'stats': {'magic_find': 30, 'attack': 3, 'health': 30}},
        {'name': 'Aurseize', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'magic_find': 40, 'defense': 8}},
    ],
    'legendary': [
        {'name': "Lioneye's Glare", 'type': 'Лук', 'slot': 'weapon1', 'stats': {'attack': 14, 'cannot_be_dodged': True}},
        {'name': "Bisco's Collar", 'type': 'Амулет', 'slot': 'amulet', 'stats': {'magic_find': 85}},
        {'name': 'Terminus Est', 'type': 'Двуручный меч', 'slot': 'weapon1', 'stats': {'attack': 13, 'defense_penetration': 15, 'crit_chance': 4}},
        {'name': 'The Anvil', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'block_chance': 7, 'crit_damage_reduction': 25, 'health': 35}},
        {'name': "Greed's Embrace", 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'magic_find': 50, 'defense': 20}},
    ]
}

# --- НОВЫЕ ПРЕДМЕТЫ ЭТАЖА 2 ---
FLOOR_2_NEW_ITEMS = {
    'magic': [
        {'name': 'Кольцо Пробития', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'defense_penetration': 15, 'accuracy': 10, 'health': 10}},
        {'name': 'Амулет Двойного Удара', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'double_damage_chance': 5, 'crit_chance': 2}},
        {'name': 'Хорошо Смазанный Лук', 'type': 'Лук', 'slot': 'weapon1', 'stats': {'accuracy': 30, 'health': 12}},
        {'name': 'Сапоги Расхитителя', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'magic_find': 25, 'health': 20}},
        {'name': 'Маска Неотвратимости', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'accuracy': 15, 'energy_shield': 15}},
        {'name': 'Перчатки Палача', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'defense_penetration': 10, 'attack': 5}},
        {'name': 'Пояс Коллекционера', 'type': 'Пояс', 'slot': 'belt', 'stats': {'magic_find': 25, 'health': 20}},
        {'name': 'Молот Удачи', 'type': 'Одноручная булава', 'slot': 'weapon1', 'stats': {'double_damage_chance': 2, 'attack': 11}},
        {'name': 'Бастион из Стали', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'crit_damage_reduction': 25, 'defense': 5}},
        {'name': 'Кристальный Щит', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'es_leech_rate': 3, 'energy_shield': 20}},
    ],
    'rare': [
        {'name': 'Хватка Тирана', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'defense_penetration': 15, 'attack': 10}},
        {'name': 'Походка Расхитителя Гробниц', 'type': 'Ботинки', 'slot': 'boots', 'set_id': 'gilded', 'stats': {'magic_find': 35, 'dodge_chance': 4, 'health': 12}},
        {'name': 'Лик Завоевателя', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'accuracy': 25, 'health': 35}},
        {'name': 'Кольцо Драконьего Богатства', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'magic_find': 30, 'attack': 5, 'health': 8}},
        {'name': 'Сердце Льва', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'crit_damage_reduction': 25, 'health': 45}},
        {'name': 'Клинок Неминуемой Гибели', 'type': 'Одноручный меч', 'slot': 'weapon1', 'stats': {'attack': 14, 'double_damage_chance': 4, 'crit_chance': 3}},
        {'name': 'Стена Несокрушимости', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 8, 'crit_damage_reduction': 20}},
        {'name': 'Ремень Охотника за Реликвиями', 'type': 'Пояс', 'slot': 'belt', 'stats': {'magic_find': 28, 'defense': 5, 'health': 15}},
        {'name': 'Броня Эфирного Потока', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'es_leech_rate': 5, 'energy_shield': 20, 'health': 25}},
        {'name': 'Взор Сокола', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'accuracy': 30, 'crit_chance': 4, 'health': 10}},
    ],
    'unique': [
        {'name': 'Blackgleam', 'type': 'Колчан (Щит)', 'slot': 'weapon2', 'stats': {'accuracy': 35, 'attack': 8, 'crit_chance': 3}},
        {'name': 'The Peregrine', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'accuracy': 30, 'magic_find': 20, 'crit_chance': 4}},
        {'name': 'Hrimsorrow', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'defense_penetration': 20, 'health': 50}},
        {'name': "Thief's Torment", 'type': 'Кольцо', 'slot': 'ring', 'stats': {'magic_find': 45, 'health': 40}},
        {'name': 'Wideswing', 'type': 'Двуручный топор', 'slot': 'weapon1', 'stats': {'attack': 22, 'double_damage_chance': 4}},
    ],
    'legendary': [
        {'name': "Marylene's Fallacy", 'type': 'Амулет', 'slot': 'amulet', 'stats': {'crit_damage_reduction': 60, 'attack': 13}},
        {'name': 'The Bringer of Rain', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'attack': 12, 'health': 80, 'block_chance': 5, 'defense_penetration': 20}}, # Изменено
        {'name': 'Divination Distillate', 'type': 'Пояс', 'slot': 'belt', 'set_id': 'gilded', 'stats': {'magic_find': 100, 'es_leech_rate': 3}},
        {'name': "Kondo's Pride", 'type': 'Двуручный меч', 'slot': 'weapon1', 'stats': {'attack': 28, 'defense_penetration': 20, 'crit_chance': 2}}, # Изменено
        {'name': 'Aegis Aurora', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 9, 'defense': 5, 'energy_shield': 45, 'es_leech_rate': 5}}, # Изменено
    ]
}

# --- НОВЫЕ ПРЕДМЕТЫ ЭТАЖА 3 ---
FLOOR_3_NEW_ITEMS = {
    'magic': [
        {'name': 'Кольцо Беспощадности', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'double_damage_chance': 8}},
        {'name': 'Амулет Истребления', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'defense_penetration': 20, 'health': 30}},
        {'name': 'Длинный Лук Снайпера', 'type': 'Лук', 'slot': 'weapon1', 'stats': {'accuracy': 25, 'health': 15, 'attack': 24}},
        {'name': 'Сапоги Золотоискателя', 'type': 'Ботинки', 'slot': 'boots', 'set_id': 'gilded', 'stats': {'magic_find': 50, 'attack': 6}},
        {'name': 'Великий Шлем Непогрешимости', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'accuracy': 20, 'energy_shield': 20}},
        {'name': 'Рукавицы Разлома', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'defense_penetration': 20, 'attack': 8}},
        {'name': 'Кушак Кладоискателя', 'type': 'Пояс', 'slot': 'belt', 'stats': {'magic_find': 35, 'health': 50, 'attack': 2}},
        {'name': 'Скипетр Двойной Угрозы', 'type': 'Одноручная булава', 'slot': 'weapon1', 'stats': {'double_damage_chance': 4, 'attack': 21}},
        {'name': 'Непробиваемая Эгида', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'crit_damage_reduction': 40, 'block_chance': 4}},
        {'name': 'Щит Вечной Подпитки', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'es_leech_rate': 4, 'energy_shield': 40}},
    ],
    'rare': [
        {'name': 'Хватка Погибели', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'double_damage_chance': 5, 'attack': 10, 'crit_chance': 3}},
        {'name': 'Следы Древнего Исследователя', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'magic_find': 50, 'dodge_chance': 3, 'health': 40}},
        {'name': 'Корона Абсолютной Точности', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'accuracy': 45, 'health': 50}},
        {'name': 'Печатка Невероятной Удачи', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'magic_find': 45, 'crit_chance': 5}},
        {'name': 'Амулет Несокрушимой Воли', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'crit_damage_reduction': 35, 'health': 60, 'defense': 5}},
        {'name': 'Разрушитель Миров', 'type': 'Двуручный топор', 'slot': 'weapon1', 'stats': {'attack': 26, 'defense_penetration': 25}},
        {'name': 'Щит из Драконьей Чешуи', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 8, 'crit_damage_reduction': 30, 'defense': 8}},
        {'name': 'Пояс Короля Пиратов', 'type': 'Пояс', 'slot': 'belt', 'stats': {'magic_find': 40, 'health': 55, 'attack': 3}},
        {'name': 'Броня Вечного Восстановления', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'es_leech_rate': 3, 'energy_shield': 40, 'defense': 20}},
        {'name': 'Клинок-Бритва', 'type': 'Одноручный меч', 'slot': 'weapon1', 'stats': {'attack': 25, 'accuracy': 20, 'defense_penetration': 15}},
    ],
    'unique': [
        {'name': "Starkonja's Head", 'type': 'Шлем', 'slot': 'helmet', 'stats': {'accuracy': 30, 'dodge_chance': 7, 'health': 70}},
        {'name': 'The Ascetic', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'magic_find': 80, 'attack': 8}},
        {'name': "Abberath's Hooves", 'type': 'Ботинки', 'slot': 'boots', 'stats': {'magic_find': 30, 'double_damage_chance': 5, 'health': 50}},
        {'name': "Kongor's Undying Rage", 'type': 'Двуручный топор', 'slot': 'weapon1', 'stats': {'attack': 35, 'double_damage_chance': 5, 'accuracy': 10}},
        {'name': "Sentari's Answer", 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 9, 'crit_damage_reduction': 45, 'energy_shield': 15}},
    ],
    'legendary': [
        {'name': 'Starforge', 'type': 'Двуручный меч', 'slot': 'weapon1', 'stats': {'attack': 40, 'health': 100, 'defense_penetration': 25}}, # Изменено
        {'name': "The Poet's Pen", 'type': 'Жезл', 'slot': 'weapon1', 'stats': {'attack': 10, 'double_damage_chance': 25}},
        {'name': "Shaper's Touch", 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'accuracy': 50, 'energy_shield': 100, 'health': 100}},
        {'name': 'Eye of Chayula', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'health': 120, 'crit_damage_reduction': 50}},
        {'name': 'Soul Taker', 'type': 'Одноручный топор', 'slot': 'weapon1', 'stats': {'attack': 32, 'defense_penetration': 30, 'es_leech_rate': 4}},
    ]
}

# --- НОВЫЕ ПРЕДМЕТЫ ЭТАЖА 4 ---
FLOOR_4_NEW_ITEMS = {
    'magic': [
        {'name': 'Кольцо Уничтожения', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'defense_penetration': 25, 'health': 80}},
        {'name': 'Амулет Погибели', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'double_damage_chance': 7}},
        {'name': 'Лук Создателя', 'type': 'Лук', 'slot': 'weapon1', 'set_id': 'viper', 'stats': {'accuracy': 50, 'attack': 30}},
        {'name': 'Сапоги Атласа', 'type': 'Ботинки', 'slot': 'boots', 'set_id': 'stormrider', 'stats': {'magic_find': 50, 'crit_chance': 5}},
        {'name': 'Корона Истинного Зрения', 'type': 'Шлем', 'slot': 'helmet', 'set_id': 'viper', 'stats': {'accuracy': 40, 'crit_chance': 6}},
        {'name': 'Перчатки Пустоты', 'type': 'Перчатки', 'slot': 'gloves', 'set_id': 'executioner', 'stats': {'defense_penetration': 20, 'attack': 35}},
        {'name': 'Пояс Древних', 'type': 'Пояс', 'slot': 'belt', 'stats': {'magic_find': 45, 'health': 100}},
        {'name': 'Булава Двойного Рока', 'type': 'Одноручная булава', 'slot': 'weapon1', 'stats': {'double_damage_chance': 6, 'attack': 34}},
        {'name': 'Щит Невозмутимости', 'type': 'Щит', 'slot': 'weapon2', 'set_id': 'stormrider', 'stats': {'crit_damage_reduction': 40, 'defense': 30}},
        {'name': 'Призматический Щит', 'type': 'Щит', 'slot': 'weapon2', 'set_id': 'acolyte', 'stats': {'es_leech_rate': 4, 'energy_shield': 90}},
    ],
    'rare': [
        {'name': 'Хватка Создателя Миров', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 13, 'defense_penetration': 25, 'accuracy': 30}},
        {'name': 'Поступь Забвения', 'type': 'Ботинки', 'slot': 'boots', 'set_id': 'hyrri', 'stats': {'magic_find': 60, 'dodge_chance': 5, 'health': 80}},
        {'name': 'Венец Космического Порядка', 'type': 'Шлем', 'slot': 'helmet', 'set_id': 'scholar', 'stats': {'accuracy': 40, 'crit_damage_reduction': 25, 'energy_shield': 40}},
        {'name': 'Кольцо Всевидящего Ока', 'type': 'Кольцо', 'slot': 'ring', 'set_id': 'executioner', 'stats': {'magic_find': 50, 'accuracy': 40, 'attack': 10}},
        {'name': 'Талисман Предвестника', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'double_damage_chance': 7, 'defense_penetration': 20, 'attack': 8}},
        {'name': 'Секира Бесконечной Скорби', 'type': 'Двуручный топор', 'slot': 'weapon1', 'set_id': 'brute', 'stats': {'attack': 35, 'double_damage_chance': 5}},
        {'name': 'Оплот Звездного Странника', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 10, 'crit_damage_reduction': 35, 'es_leech_rate': 5}},
        {'name': 'Ремень Искателя Галактик', 'type': 'Пояс', 'slot': 'belt', 'stats': {'magic_find': 55, 'health': 100, 'defense': 10}},
        {'name': 'Броня Закаленного в Боях', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'crit_damage_reduction': 40, 'health': 180, 'defense': 10}},
        {'name': 'Клинок, Пронзающий Завесу', 'type': 'Одноручный меч', 'slot': 'weapon1', 'set_id': 'viper', 'stats': {'attack': 33, 'accuracy': 40, 'defense_penetration': 20}},
    ],
    'unique': [
        {'name': 'The Tempestuous Steel', 'type': 'Одноручный меч', 'slot': 'weapon1', 'stats': {'attack': 40, 'double_damage_chance': 6}},
        {'name': 'The Scourge', 'type': 'Когти', 'slot': 'weapon1', 'set_id': 'stormrider', 'stats': {'attack': 35, 'double_damage_chance': 7, 'accuracy': 40}},
        {'name': 'Lycosidae', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 15, 'health': 80, 'cannot_be_dodged': True}},
        {'name': 'Goldwyrm', 'type': 'Ботинки', 'slot': 'boots', 'set_id': 'shadow', 'stats': {'magic_find': 100, 'dodge_chance': 9}},
        {'name': 'The Pariah', 'type': 'Кольцо', 'slot': 'ring', 'set_id': 'gilded', 'stats': {'accuracy': 100, 'magic_find': 50}},
    ],
    'legendary': [
        {'name': 'Headhunter', 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 290, 'attack': 28, 'magic_find': 50}}, # Изменено
        {'name': 'Mageblood', 'type': 'Пояс', 'slot': 'belt', 'stats': {'defense': 30, 'dodge_chance': 15, 'crit_damage_reduction': 40}}, # Изменено
        {'name': "Atziri's Acuity", 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'crit_chance': 12, 'attack': 15, 'energy_shield': 100, 'defense_penetration': 20}}, # Изменено
        {'name': 'Voidforge', 'type': 'Двуручный меч', 'slot': 'weapon1', 'stats': {'attack': 60, 'double_damage_chance': 10}}, # Изменено
        {'name': 'The Squire', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'attack': 12, 'block_chance': 22, 'double_damage_chance': 5}}, # Изменено
        {'name': "The Iron Fortress", 'type': 'Нательная броня', 'slot': 'body_armour', 
         'stats': {'defense': 20, 'health': 100},
         'scaling_stats': {'attack': {'source': 'defense', 'ratio': 0.8}}}, # Дает +0.8 к атаке за каждый 1% защиты
        {'name': "Redblade Banner", 'type': 'Щит', 'slot': 'weapon2', 'set_id': 'bulwark', 
         'stats': {'block_chance': 10, 'health': 150},
         'scaling_stats': {'crit_chance': {'source': 'block_chance', 'ratio': 0.5}}}, # Дает +0.5% крит. шанса за каждый 1% блока ,
    ]
}

NEW_RARE_ITEMS_F4 = [
    # Оружие
    {'name': 'Rift Slicer Vaal Blade', 'type': 'Одноручный меч', 'slot': 'weapon1', 'set_id': 'executioner', 'stats': {'attack': 30, 'crit_chance': 5, 'accuracy': 40, 'block_penetration': 10}},
    {'name': 'Soul Carver Royal Axe', 'type': 'Одноручный топор', 'slot': 'weapon1', 'stats': {'attack': 25, 'double_damage_chance': 4, 'health': 350}},
    {'name': 'Void Goad Spiraled Wand', 'type': 'Жезл', 'slot': 'weapon1', 'set_id': 'acolyte', 'stats': {'attack': 18, 'energy_shield': 400, 'crit_chance': 4}},
    {'name': 'Oblivion Strike Harbinger Bow', 'type': 'Лук', 'slot': 'weapon1', 'set_id': 'viper', 'stats': {'attack': 26, 'crit_chance': 7, 'accuracy': 50, 'block_penetration': 15}},
    {'name': 'Doom Gavel Karui Maul', 'type': 'Двуручная булава', 'slot': 'weapon1', 'stats': {'attack': 34, 'health': 180, 'defense_penetration': 15}},
    # Броня
    {'name': 'Glyph Mark Vaal Mask', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'health': 80, 'energy_shield': 60, 'defense': 10, 'block_penetration': 3}},
    {'name': 'Behemoth Pelt Crusader Plate', 'type': 'Нательная броня', 'slot': 'body_armour', 'set_id': 'bulwark', 'stats': {'health': 200, 'defense': 12, 'block_chance': 8}},
    {'name': 'Cataclysm Grip Titan Gauntlets', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 12, 'health': 90, 'accuracy': 30, 'block_penetration': 10}},
    {'name': 'Storm Walk Sorcerer Boots', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 6, 'energy_shield': 80, 'health': 60}},
    {'name': 'Aegis of Annihilation Pinnacle Tower Shield', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 17, 'health': 110, 'defense': 18}},
    # Аксессуары
    {'name': 'Pain Clasp Steel Ring', 'type': 'Кольцо', 'slot': 'ring', 'set_id': 'executioner', 'stats': {'attack': 15, 'health': 100, 'crit_chance': 3}},
    {'name': 'Dragon Heart Onyx Amulet', 'type': 'Амулет', 'slot': 'amulet', 'set_id': 'scholar', 'stats': {'health': 100, 'attack': 10, 'energy_shield': 100, 'block_penetration': 4}},
    {'name': 'Wraith Cinch Crystal Belt', 'type': 'Пояс', 'slot': 'belt', 'stats': {'energy_shield': 120, 'health': 90, 'defense': 5}},
    {'name': 'Blight Coil Ruby Ring', 'type': 'Кольцо', 'slot': 'ring', 'set_id': 'shadow', 'stats': {'attack': 12, 'lifesteal': 2, 'health': 60, 'block_penetration': 4}},
    {'name': 'Gale Eye Jade Amulet', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'dodge_chance': 7, 'attack': 19, 'crit_chance': 4}},
    # Еще предметы
    {'name': 'Corpse Rend Fleshripper', 'type': 'Двуручный топор', 'slot': 'weapon1', 'stats': {'attack': 40, 'lifesteal': 5, 'defense_penetration': 25}},
    {'name': 'Miracle Guard Archon Shield', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 20, 'crit_damage_reduction': 30, 'health': 60}},
    {'name': 'Havoc Crest Nightmare Bascinet', 'type': 'Шлем', 'slot': 'helmet', 'set_id': 'brute', 'stats': {'crit_chance': 6, 'attack': 10, 'health': 135}},
    {'name': 'Woe Stride Goliath Greaves', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'health': 140, 'defense': 10, 'dodge_chance': 5}},
    {'name': 'Viper Fangs Spiked Gloves', 'type': 'Перчатки', 'slot': 'gloves', 'set_id': 'stormrider', 'stats': {'attack': 14, 'crit_chance': 4, 'double_damage_chance': 3, 'block_penetration': 5}},
    {'name': 'Armageddon Harness Heavy Belt', 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 140, 'defense': 7, 'block_penetration': 6}},
    {'name': 'Rune Loop Moonstone Ring', 'type': 'Кольцо', 'slot': 'ring', 'set_id': 'acolyte', 'stats': {'energy_shield': 100, 'crit_chance': 4, 'attack': 5, 'block_penetration': 4}},
    {'name': 'Pandemonium Charm Lapis Amulet', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'energy_shield': 110, 'attack': 8, 'es_leech_rate': 2, 'block_penetration': 5}},
    {'name': 'Demonhide Tunic Assassin\'s Garb', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'dodge_chance': 10, 'health': 170, 'crit_chance': 5}},
    {'name': 'Eclipse Staff Maelström Staff', 'type': 'Посох', 'slot': 'weapon1', 'stats': {'attack': 35, 'block_chance': 10, 'energy_shield': 150}},
]

# --- 25 НОВЫХ УНИКАЛЬНЫХ ПРЕДМЕТОВ ---
NEW_UNIQUE_ITEMS_F4 = [
    # Оружие
    {'name': 'Oni-Goroshi', 'type': 'Одноручный меч', 'slot': 'weapon1', 'stats': {'attack': 60, 'crit_chance': 10, 'lifesteal': 4, 'health': -300}},
    {'name': 'Nebuloch', 'type': 'Одноручная булава', 'slot': 'weapon1', 'stats': {'attack': 40, 'defense': 20, 'health': 140}},
    {'name': 'Hopeshredder', 'type': 'Лук', 'slot': 'weapon1', 'stats': {'attack': 52, 'dodge_chance': 12, 'health': -100}},
    {'name': 'The Poet\'s Pen', 'type': 'Жезл', 'slot': 'weapon1', 'stats': {'attack': 25, 'double_damage_chance': 15, 'block_penetration': 40}},
    {'name': 'Atziri\'s Disfavour', 'type': 'Двуручный топор', 'slot': 'weapon1', 'stats': {'attack': 45, 'lifesteal': 4, 'defense': -25, 'block_penetration': 14}},
    {'name': 'Cospri\'s Malice', 'type': 'Одноручный меч', 'slot': 'weapon1', 'stats': {'attack': 25, 'crit_chance': 8, 'defense_penetration': 30}},
    # Броня
    {'name': 'Lightpoacher', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'health': 100, 'attack': 15, 'defense_penetration': 15, 'block_penetration': 8}},
    {'name': 'Tinkerskin', 'type': 'Нательная броня', 'slot': 'body_armour', 'set_id': 'hyrri', 'stats': {'health': 130, 'dodge_chance': 12, 'energy_shield': 100}},
    {'name': 'Bubonic Trail', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'health': 120, 'attack': 10, 'dodge_chance': 7}},
    {'name': 'Fleshcrafter', 'type': 'Нательная броня', 'slot': 'body_armour', 'set_id': 'scholar', 'stats': {'energy_shield': 250, 'attack': 20, 'health': -250}},
    {'name': 'The Rat Cage', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'attack': 25, 'crit_damage_reduction': 50, 'dodge_chance': -10}},
    {'name': 'Command of the Pit', 'type': 'Перчатки', 'slot': 'gloves', 'set_id': 'executioner', 'stats': {'crit_chance': 8, 'attack': 12, 'accuracy': 50, 'block_penetration': 6}},
    {'name': 'The Devouring Diadem', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'energy_shield': 200, 'es_leech_rate': 3, 'defense': 15}},
    # Аксессуары
    {'name': 'Yoke of Suffering', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'health': 120, 'crit_chance': 7, 'attack': 10, 'block_penetration': 4}},
    {'name': 'Mark of the Shaper', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'energy_shield': 100, 'attack': 15, 'block_penetration': 7}},
    {'name': 'Perseverance', 'type': 'Пояс', 'slot': 'belt', 'set_id': 'bulwark', 'stats': {'health': 100, 'defense': 15, 'attack': 15}},
    {'name': 'The Nomad', 'type': 'Пояс', 'slot': 'belt', 'set_id': 'hyrri', 'stats': {'health': 120, 'dodge_chance': 8, 'magic_find': 30, 'block_penetration': 4}},
    {'name': 'Mindfang', 'type': 'Когти', 'slot': 'weapon1', 'set_id': 'stormrider', 'stats': {'attack': 39, 'lifesteal': 4, 'crit_chance': 8}},
    {'name': 'The Primordial Chain', 'type': 'Амулет', 'slot': 'amulet', 'set_id': 'shadow', 'stats': {'attack': 25, 'health': -250, 'block_penetration': 25}},
    {'name': 'Praxis', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'energy_shield': 120, 'health': 80, 'block_penetration': 10}},
    # Щиты
    {'name': 'The Surrender', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 18, 'health': 170, 'defense': 10}},
    {'name': 'Titucius\' Span', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 15, 'crit_damage_reduction': 40, 'defense': 12}},
    {'name': 'Lycosidae', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 10, 'health': 100, 'cannot_be_dodged': True}},
    {'name': 'Ahn\'s Heritage', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 14, 'dodge_chance': -10, 'attack': 15, 'block_penetration': 20}},
    {'name': 'The Vigil', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'defense': 50, 'health': 130}},
]

# --- 15 НОВЫХ ЛЕГЕНДАРНЫХ ПРЕДМЕТОВ ---
NEW_LEGENDARY_ITEMS_F4 = [
    {'name': 'The Saviour', 'type': 'Одноручный меч', 'slot': 'weapon1', 'stats': {'attack': -45, 'dodge_chance': 30, 'block_chance': 30}},
    {'name': 'Crown of the Inward Eye', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'health': 150, 'energy_shield': 150, 'attack': 15, 'defense': 15, 'block_penetration':3}},
    {'name': 'The Eternity Shroud', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'energy_shield': 330, 'defense_penetration': 20, 'crit_chance': 5}},
    {'name': 'Aul\'s Uprising', 'type': 'Амулет', 'slot': 'amulet', 'set_id': 'executioner', 'stats': {'health': 120, 'defense': 25, 'block_chance': 8}},
    {'name': 'Flicker Coil', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'dodge_chance': 14, 'health': 130, 'attack': 20}},
    {'name': 'Grelwood Shank', 'type': 'Одноручный меч', 'slot': 'weapon1', 'stats': {'attack': 47, 'block_chance': 10, 'double_damage_chance': 7, 'block_penetration': 5}},
    {'name': 'Chains of Command', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'attack': 25, 'health': 200, 'defense_penetration': 15}},
    {'name': 'The Crimson Storm', 'type': 'Лук', 'slot': 'weapon1', 'set_id': 'shadow', 'stats': {'attack': 48, 'lifesteal': 5, 'double_damage_chance': 5}},
    {'name': 'Hyrri\'s Ire', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'dodge_chance': 20, 'attack': 22, 'health': 100, 'defense': 10}},
    {'name': 'Scold\'s Bridle', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'attack': 40, 'energy_shield': 180, 'health': -200}},
    {'name': 'Victario\'s Acuity', 'type': 'Амулет', 'slot': 'amulet', 'set_id': 'viper', 'stats': {'crit_chance': 12, 'accuracy': 100, 'attack': 15}},
    {'name': 'Doryani\'s Prototype', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'attack': 40, 'lifesteal': 5, 'defense': -25}},
    {'name': 'Forbidden Shako', 'type': 'Шлем', 'slot': 'helmet', 'set_id': 'gilded', 'stats': {'attack': 20, 'crit_chance': 10, 'magic_find': 50, 'lifesteal': 3}},
    {'name': 'Coward\'s Legacy', 'type': 'Пояс', 'slot': 'belt', 'stats': {'attack': 30, 'crit_chance': 10, 'dodge_chance': 6, 'health': -200, 'block_penetration': 8}},
    {'name': 'Solstice Vigil', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'energy_shield': 150, 'crit_damage_reduction': 80, 'es_leech_rate': 3, 'block_penetration': 6}},
]
# --- НАЧАЛО НОВОГО БЛОКА: Предметы со скалированием от защиты (Этаж 4) ---
NEW_SCALING_ITEMS_F4 = {
    'rare': [
        {'name': 'Ремень Кровавого Договора', 'type': 'Пояс', 'slot': 'belt', 
         'stats': {'health': 100}, 
         'scaling_stats': {'attack': {'source': 'max_health', 'ratio': 0.02}}}, # +1 атаки за 50 здоровья

        {'name': 'Бастион из Слоновой Кости', 'type': 'Щит', 'slot': 'weapon2', 
         'stats': {'block_chance': 12, 'health': 80}, 
         'scaling_stats': {'crit_chance': {'source': 'defense', 'ratio': 0.1}}}, # +1% крита за 10% защиты

        {'name': 'Поступь Голема', 'type': 'Ботинки', 'slot': 'boots', 
         'stats': {'health': 120, 'dodge_chance': -5}, 
         'scaling_stats': {'crit_damage_reduction': {'source': 'max_health', 'ratio': 0.0125}}}, # +1% защиты от крита за 80 здоровья
    ],
    'unique': [
        {'name': 'Сердце Горы', 'type': 'Нательная броня', 'slot': 'body_armour', 
         'stats': {'health': 250, 'crit_chance': -10}, 
         'scaling_stats': {'double_damage_chance': {'source': 'max_health', 'ratio': 0.0066}}}, # ~+1% двойного урона за 150 здоровья

        {'name': 'Несокрушимая Эгида', 'type': 'Шлем', 'slot': 'helmet', 
         'stats': {'defense': 15, 'health': 100}, 
         'scaling_stats': {'es_leech_rate': {'source': 'defense', 'ratio': 0.066}}}, # ~+1% вампиризма щита за 15% защиты

        {'name': 'Обет Стойкости', 'type': 'Амулет', 'slot': 'amulet', 
         'stats': {'health': 80}, 
         'scaling_stats': {'accuracy': {'source': 'max_health', 'ratio': 0.04}}}, # +1 точности за 25 здоровья
    ],
    'legendary': [
        {'name': 'Воплощение Титана', 'type': 'Двуручная булава', 'slot': 'weapon1', 
         'stats': {'defense': 15, 'cannot_be_crit': True}, 
         'scaling_stats': {'attack_from_health_override': {'source': 'max_health', 'ratio': 0.15}}}, # Атака = 15% от макс. здоровья

        {'name': 'Последний Бастион Империи', 'type': 'Нательная броня', 'slot': 'body_armour', 
         'stats': {'health': 200}, 
         'scaling_stats': {'block_chance': {'source': 'defense', 'ratio': 0.125}}}, # +1% блока за 8% защиты

        {'name': 'Зеркало Крови', 'type': 'Амулет', 'slot': 'amulet', 
         'stats': {'lifesteal': 5}, 
         'scaling_stats': {'defense_penetration': {'source': 'max_health', 'ratio': 0.0083}}}, # ~+1% пробития за 120 здоровья
    ]
}
# --- КОНЕЦ НОВОГО БЛОКА ---
# =============================================================================
# ЭТАЖ 1: ПОБЕРЕЖЬЕ (THE COAST - ACT 1-2)
FLOOR_1_CONTENT = {
    'monsters': {
        'common': [{'name': 'Risen Dead', 'stats': {'health': 85, 'attack': 8, 'defense': 5}}, {'name': 'Starved Husk', 'stats': {'health': 55, 'attack': 10, 'defense': 2}}, {'name': 'Rhoa', 'stats': {'health': 100, 'attack': 7, 'defense': 8, 'block_chance': 5}}, {'name': 'Cave Crustacean', 'stats': {'health': 90, 'attack': 5, 'defense': 25}}, {'name': 'Carrion Swarmer', 'stats': {'health': 45, 'attack': 5, 'dodge_chance': 15}}, {'name': 'Skeletal Archer', 'stats': {'health': 75, 'attack': 10, 'defense': 0}}, {'name': 'Water Elemental', 'stats': {'health': 70, 'energy_shield': 20, 'attack': 6, 'defense': 5}}],
        'rare': [{'name': 'Gnarled Trickster', 'stats': {'health': 90, 'energy_shield': 25, 'attack': 10, 'defense': 8, 'dodge_chance': 15}}, {'name': 'Corrupted Rhoa', 'stats': {'health': 130, 'attack': 12, 'defense': 10, 'crit_chance': 10, 'block_penetration': 10}}, {'name': 'Vaal Smasher', 'stats': {'health': 150, 'attack': 12, 'defense': 12, 'block_chance': 10}}, {'name': 'Salt-lashed Warrior', 'stats': {'health': 100, 'attack': 11, 'defense': 8, 'crit_chance': 35, 'block_penetration': 8}}, {'name': 'Enslaved Hellion', 'stats': {'health': 95, 'attack': 16, 'defense': 30}}],
        'lootgoblins': [{'name': 'Pilfering Imp', 'stats': {'health': 105, 'attack': 9, 'defense': 25, 'dodge_chance': 40, 'block_penetration': 15}}, {'name': 'Covetous Spirit', 'stats': {'health': 60, 'energy_shield': 80, 'attack': 8, 'defense': 20, 'dodge_chance': 20}}, {'name': 'Hoarding Vaal Construct', 'stats': {'health': 200, 'attack': 7, 'defense': 20, 'dodge_chance': 10}}],
        'bosses': [{'name': 'Brutus, Lord of the Damned', 'stats': {'health': 250, 'attack': 25, 'defense': 20, 'block_chance': 20, 'accuracy': 500, 'double_damage_chance': 5, 'defense_penetration': 25, 'block_penetration': 8}}, {'name': 'Merveil, the Siren', 'stats': {'health': 10, 'energy_shield': 250, 'attack': 20, 'defense': 8, 'dodge_chance': 20, 'accuracy': 20, 'defense_penetration': 15, 'block_penetration': 5}}, {'name': 'The Crier', 'stats': {'health': 400, 'attack': 10, 'defense': 15, 'crit_chance': 5, 'accuracy': 18, 'defense_penetration': 20, 'block_penetration': 6}}, {'name': 'Oozeback', 'stats': {'health': 240, 'attack': 25, 'defense': 5, 'dodge_chance': 35, 'accuracy': 25, 'defense_penetration': 14, 'block_penetration': 4}}]
    },
    'items': {
        'magic': [{'name': 'Serrated Wand of Sparks', 'type': 'Жезл', 'slot': 'weapon1', 'stats': {'attack': 5}}, {'name': 'Leather Cap of Warding', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'defense': 8}}, {'name': 'Driftwood Club of Bashing', 'type': 'Одноручная булава', 'slot': 'weapon1', 'stats': {'attack': 6}}, {'name': 'Rusted Gauntlets of Protection', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'defense': 7}}, {'name': 'Wool Shoes of Swiftness', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 3}}, {'name': 'Simple Buckler of Deflection', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 4}}, {'name': 'Iron Ring of Striking', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'attack': 4}}, {'name': 'Paua Amulet of Health', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'health': 20}}, {'name': 'Coral Ring of Life', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'health': 18}}, {'name': 'Goathide Boots of Speed', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 3}}, {'name': 'Spiked Shield of Blocking', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 5}}, {'name': 'Carved Wand of Damage', 'type': 'Жезл', 'slot': 'weapon1', 'stats': {'attack': 5, 'crit_chance': 1}}, {'name': 'Iron Hat of Defense', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'defense': 8}}, {'name': 'Studded Belt of Vigor', 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 15}}, {'name': 'Jade Amulet of Dodging', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'dodge_chance': 3}}, {'name': 'Crude Bow of Firing', 'type': 'Лук', 'slot': 'weapon1', 'stats': {'attack': 6, 'health': 10}}, {'name': 'Chainmail Vest of the Wall', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'defense': 5, 'health': 10}}, {'name': 'Iron Greaves of Stability', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'defense': 4, 'block_chance': 2}}, {'name': 'Sapphire Ring of Shielding', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'energy_shield': 8}}, {'name': 'Lapis Amulet of Power', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'energy_shield': 13}}] + FLOOR_1_NEW_ITEMS['magic'],
        'rare': [{'name': 'Havoc Grip Iron Gauntlets', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 4, 'crit_chance': 2}}, {'name': 'Ghoul Hide Studded Belt', 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 20, 'defense': 4}}, {'name': 'Wraith Stride Wool Shoes', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 2, 'health': 20}}, {'name': 'Blood Crest Rusted Helm', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'attack': 3, 'health': 13}}, {'name': 'Victory Shelter Spiked Shield', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 6, 'defense': 5}}, {'name': 'Rift Heart Paua Amulet', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'health': 20, 'energy_shield': 10}}, {'name': 'Pain Grasp Coral Ring', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'attack': 3, 'health': 10}}, {'name': 'Eagle Flight Crude Bow', 'type': 'Лук', 'slot': 'weapon1', 'stats': {'attack': 8, 'crit_chance': 3}}, {'name': 'Beast Hide Chainmail', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 25, 'defense': 6}}, {'name': 'Sorrow Step Goathide Boots', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 2, 'health': 20}}, {'name': 'Stone Grip Rawhide Gloves', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 3, 'defense': 9}}, {'name': 'Oblivion Horn Iron Hat', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'defense': 5, 'energy_shield': 12}}, {'name': 'Demon Song Carved Wand', 'type': 'Жезл', 'slot': 'weapon1', 'stats': {'attack': 5, 'energy_shield': 11}}, {'name': 'Cataclysm Buckler of the Titan', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 5, 'health': 20}}, {'name': 'Corpse Harness Leather Tunic', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 20, 'dodge_chance': 3}}] + FLOOR_1_NEW_ITEMS['rare'] + NEW_SET_AND_EXPANSION_ITEMS['floor_1'].get('rare', []),
        'unique': [{'name': 'Goldrim', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'defense': 10, 'energy_shield': 20}}, {'name': 'The Last Resort', 'type': 'Одноручный топор', 'slot': 'weapon1', 'stats': {'attack': 12, 'dodge_chance': 2}}, {'name': 'Lifesprig', 'type': 'Жезл', 'slot': 'weapon1', 'stats': {'attack': 4, 'health': 25, 'energy_shield': 15}}, {'name': 'Redbeak', 'type': 'Одноручный меч', 'slot': 'weapon1', 'stats': {'attack': 11, 'health': 12}}, {'name': 'Wondertrap', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 3, 'defense': 5, 'health': 15}}, {'name': 'The Ignomon', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'crit_chance': 4, 'defense': 8, 'health': 10}}, {'name': 'Blackheart', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'attack': 4, 'block_chance': 3, 'health': 20}}, {'name': 'Silverbranch', 'type': 'Лук', 'slot': 'weapon1', 'stats': {'attack': 13, 'crit_chance': 2}}, {'name': 'Lochtonial Caress', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 4, 'block_chance': 4}}, {'name': 'Perandus Blazon', 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 35, 'defense': 5}}] + FLOOR_1_NEW_ITEMS['unique'] + NEW_SET_AND_EXPANSION_ITEMS['floor_1'].get('unique', []) + NEW_MECHANIC_ITEMS['floor_1']['unique'],
        'legendary': [{'name': 'Wanderlust', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 3, 'health': 30, 'defense': 5}}, {'name': "Нейтронная Звезда", 'type': 'Двуручный клинок', 'slot': 'weapon1', 
             'stats': {'attack': 100, 'double_damage_chance': 5, 'crit_chance': 5}, 
             'lifespan': [5, 5]}, # [текущее, максимальное]
            {'name': "Мечта Фликера", 'type': 'Одноручный меч', 'slot': 'weapon1', 
             'stats': {'attack': 50, 'dodge_chance': 10}, 
             'charges': [5, 5], # [текущее, максимальное]
             'special_mechanic': 'random_teleport_on_win'}, {'name': 'Tabula Rasa', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 25, 'energy_shield': 15, 'attack': 5, 'crit_chance': 2}}, {'name': 'Shiversting', 'type': 'Двуручный меч', 'slot': 'weapon1', 'stats': {'attack': 15, 'crit_chance': 4}}, {'name': 'Limbsplit', 'type': 'Двуручный топор', 'slot': 'weapon1', 'stats': {'attack': 14, 'health': 20}}, {'name': 'The Goddess Scorned', 'type': 'Одноручный меч', 'slot': 'weapon1', 'stats': {'attack': 5, 'crit_chance': 10, 'block_chance': 5}}] + FLOOR_1_NEW_ITEMS['legendary'] + NEW_SET_AND_EXPANSION_ITEMS['floor_1'].get('legendary', [])
    }
}
# ЭТАЖ 2: ГОРОД САРН (THE CITY OF SARN - ACT 3-4)
FLOOR_2_CONTENT = {
    'monsters': {
        'common': [{'name': 'Undying Guard', 'stats': {'health': 130, 'attack': 12, 'defense': 12, 'block_chance': 10}}, {'name': 'Gemling Legionnaire', 'stats': {'health': 120, 'energy_shield': 50, 'attack': 13, 'defense': 10}}, {'name': 'Sarn Guard', 'stats': {'health': 130, 'attack': 16, 'defense': 15}}, {'name': 'Blackguard Mage', 'stats': {'health': 80, 'energy_shield': 60, 'attack': 16, 'defense': 5}}, {'name': 'Vaal Construct', 'stats': {'health': 210, 'attack': 10, 'defense': 20, 'block_chance': 5}}, {'name': 'Ribbon Sentinel', 'stats': {'health': 130, 'attack': 11, 'defense': 8, 'dodge_chance': 25}}],
        'rare': [{'name': 'Eternal Mercenary', 'stats': {'health': 250, 'attack': 18, 'defense': 15, 'crit_chance': 10}}, {'name': 'Armoured Bonestalker', 'stats': {'health': 330, 'attack': 13, 'defense': 25, 'block_penetration': 10}}, {'name': 'Corrupted Sentinel', 'stats': {'health': 20, 'energy_shield': 240, 'attack': 20, 'defense': 10}}, {'name': 'Anomalous Vaal Construct', 'stats': {'health': 280, 'attack': 17, 'defense': 22, 'block_chance': 15, 'block_penetration': 11}}, {'name': 'Imperial Legionary', 'stats': {'health': 200, 'attack': 20, 'defense': 20, 'crit_chance': 50}}],
        'lootgoblins': [{'name': 'Wealthy Noble', 'stats': {'health': 290, 'attack': 15, 'defense': 25, 'dodge_chance': 20, 'block_penetration': 10}}, {'name': 'Gem-hoarding Construct', 'stats': {'health': 145, 'attack': 28, 'defense': 15, 'dodge_chance': 15}}, {'name': 'Opulent Brute', 'stats': {'health': 220, 'attack': 11, 'defense': 20, 'dodge_chance': 30, 'block_penetration': 7}}],
        'bosses': [{'name': 'Vaal Oversoul', 'stats': {'health': 400, 'energy_shield': 400, 'attack': 25, 'defense': 20, 'crit_chance': 50, 'accuracy': 30, 'defense_penetration': 20, 'block_penetration': 10}}, {'name': 'Piety of Theopolis', 'stats': {'health': 350, 'energy_shield': 350, 'attack': 30, 'defense': 15, 'dodge_chance': 15, 'accuracy': 25, 'double_damage_chance': 25, 'defense_penetration': 15, 'block_penetration': 8}}, {'name': 'General Gravicius', 'stats': {'health': 400, 'attack': 35, 'defense': 35, 'block_chance': 20, 'accuracy': 35, 'double_damage_chance': 10, 'defense_penetration': 20, 'block_penetration': 7}}, {'name': 'Dominus, Ascendant', 'stats': {'health': 100, 'energy_shield': 350, 'attack': 45, 'defense': 18, 'crit_chance': 25, 'accuracy': 10, 'defense_penetration': 10, 'block_penetration': 7}}]
    },
    'items': {
        'magic': [{'name': 'Engraved Wand of Force', 'type': 'Жезл', 'slot': 'weapon1', 'stats': {'attack': 13}}, {'name': 'Full Helm of Fortification', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'defense': 15, 'health': 20}}, {'name': 'Jade Chopper of Cleaving', 'type': 'Двуручный топор', 'slot': 'weapon1', 'stats': {'attack': 11, 'health': 15}}, {'name': 'Plated Gauntlets of the Sentinel', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'defense': 5, 'dodge_chance': 5}}, {'name': 'Shagreen Boots of Evasion', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 4, 'health': 20}}, {'name': 'Tower Shield of Impenetrability', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 6, 'health': 15}}, {'name': 'Topaz Ring of Power', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'energy_shield': 15, 'attack': 5}}, {'name': 'Heavy Belt of the Giant', 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 50}}, {'name': 'Amber Amulet of Strength', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'health': 25, 'attack': 3}}, {'name': 'War Hammer of Crushing', 'type': 'Одноручная булава', 'slot': 'weapon1', 'stats': {'attack': 10, 'energy_shield': 20}}, {'name': 'Bronze Gauntlets of Might', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 4, 'defense': 6}}, {'name': 'Legion Boots of Endurance', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'health': 35, 'defense': 5}}, {'name': 'Gilded Sallet of Command', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'defense': 10, 'energy_shield': 10}}, {'name': 'Spine Bow of the Ranger', 'type': 'Лук', 'slot': 'weapon1', 'stats': {'attack': 7, 'crit_chance': 4, 'energy_shield': 10}}, {'name': 'Bronze Plate of the Bear', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 40, 'defense': 5}}, {'name': 'Ruby Ring of Flames', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'attack': 4, 'energy_shield': 10}}, {'name': 'Onyx Amulet of Balance', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'health': 25, 'energy_shield': 10}}, {'name': 'Warlord Buckler of Defense', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 7, 'defense': 5}}, {'name': 'Slink Gloves of Dexterity', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'dodge_chance': 3, 'attack': 4}}, {'name': 'Velvet Mask of Shadows', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'crit_chance': 4, 'dodge_chance': 3}}] + FLOOR_2_NEW_ITEMS['magic'],
        'rare': [{'name': 'Gale Grip Plated Gauntlets', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 7, 'crit_chance': 3}}, {'name': 'Sorrow Clasp Heavy Belt', 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 50, 'defense': 5}}, {'name': 'Wraith March Shagreen Boots', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 3, 'health': 45}}, {'name': 'Dread Visage Full Helm', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'attack': 4, 'defense': 7, 'health': 20}}, {'name': 'Phoenix Shelter Tower Shield', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 5, 'health': 35, 'defense': 5}}, {'name': 'Grim Heart Amber Amulet', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'attack': 5, 'health': 35}}, {'name': 'Havoc Coil Topaz Ring', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'attack': 1, 'crit_chance': 5, 'energy_shield': 10}}, {'name': 'Death Shot Spine Bow', 'type': 'Лук', 'slot': 'weapon1', 'stats': {'attack': 13, 'crit_chance': 5}}, {'name': 'Dragonscale Bronze Plate', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 50, 'defense': 8, 'block_chance': 4}}, {'name': 'Rune Stride Legion Boots', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 2, 'energy_shield': 20, 'health': 20}}, {'name': 'Blood Fist Bronze Gauntlets', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 6, 'health': 25, 'defense': 5}}, {'name': 'Hypnotic Horns Gilded Sallet', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'defense': 10, 'crit_chance': 4}}, {'name': 'Maelstrom Carver Jade Chopper', 'type': 'Двуручный топор', 'slot': 'weapon1', 'stats': {'attack': 15, 'dodge_chance': 3}}, {'name': 'Kraken Guard Warlord Buckler', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 9, 'defense': 9}}, {'name': 'Shadow Weave Velvet Mask', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'crit_chance': 5, 'dodge_chance': 3, 'energy_shield': 15}}] + FLOOR_2_NEW_ITEMS['rare'] + NEW_SET_AND_EXPANSION_ITEMS['floor_2'].get('rare', []),
        'unique': [{'name': 'Geofri\'s Crest', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'defense': 10, 'energy_shield': 30}}, {'name': 'Belt of the Deceiver', 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 10, 'attack': 10, 'defense': 3}}, {'name': 'Aurumvorax', 'type': 'Одноручный меч', 'slot': 'weapon1', 'stats': {'attack': 24, 'defense': 10}}, {'name': 'The Screaming Eagle', 'type': 'Одноручный топор', 'slot': 'weapon1', 'stats': {'attack': 22, 'dodge_chance': 4}}, {'name': 'Fairgraves\' Tricorne', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'dodge_chance': 5, 'attack': 10, 'defense': 5}}, {'name': 'Crest of Perandus', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 8, 'defense': 8, 'health': 70}}, {'name': 'Brightbeak', 'type': 'Одноручная булава', 'slot': 'weapon1', 'stats': {'attack': 25, 'crit_chance': 1}}, {'name': 'Reverberation Rod', 'type': 'Жезл', 'slot': 'weapon1', 'stats': {'attack': 20, 'energy_shield': 25}}, {'name': 'Meginord\'s Girdle', 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 70, 'attack': 7}}, {'name': 'Prism Guardian', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 10, 'energy_shield': 20, 'health': 50}}] + FLOOR_2_NEW_ITEMS['unique'] + NEW_SET_AND_EXPANSION_ITEMS['floor_2'].get('unique', []) + NEW_MECHANIC_ITEMS['floor_2']['unique'],
        'legendary': [{'name': 'Maligaro\'s Virtuosity', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'crit_chance': 10, 'attack': 10, 'dodge_chance': 5}}, {'name': 'The Searing Touch', 'type': 'Посох', 'slot': 'weapon1', 'stats': {'attack': 29, 'energy_shield': 20}}, {'name': 'Doedre\'s Damning', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'attack': 10, 'crit_chance': 5, 'energy_shield': 20}}] + FLOOR_2_NEW_ITEMS['legendary'] + NEW_SET_AND_EXPANSION_ITEMS['floor_2'].get('legendary', [])
    }
}
# ЭТАЖ 3: ГОРЫ И ХРАМЫ (HIGHSPIRE & TEMPLES - ACT 5-7)
FLOOR_3_CONTENT = {
    'monsters': {
        'common': [{'name': 'Goatman Shaman', 'stats': {'health': 240, 'energy_shield': 80, 'attack': 28, 'defense': 15}}, {'name': 'Tukohama Warrior', 'stats': {'health': 300, 'attack': 39, 'defense': 20, 'block_chance': 15}}, {'name': 'Kitava Cultist', 'stats': {'health': 400, 'attack': 20, 'defense': 12, 'crit_chance': 10}}, {'name': 'Heretical Guardian', 'stats': {'health': 350, 'energy_shield': 130, 'attack': 25, 'defense': 25}}, {'name': 'Host Cobra', 'stats': {'health': 200, 'attack': 32, 'defense': 10, 'dodge_chance': 25}}, {'name': 'Stygian Revenant', 'stats': {'health': 280, 'energy_shield': 150, 'attack': 36, 'defense': 18, 'crit_chance': 15}}],
        'rare': [{'name': 'Tukohama\'s Vanguard', 'stats': {'health': 550, 'attack': 40, 'defense': 30, 'block_chance': 25, 'accuracy': 25}}, {'name': 'Innocence-touched Crusader', 'stats': {'health': 500, 'energy_shield': 250, 'attack': 38, 'defense': 25, 'accuracy': 20}}, {'name': 'Kitava\'s Herald', 'stats': {'health': 400, 'attack': 45, 'defense': 20, 'crit_chance': 40, 'accuracy': 30, 'block_penetration': 15}}, {'name': 'Empowered Golem', 'stats': {'health': 750, 'attack': 33, 'defense': 35, 'block_chance': 10, 'accuracy': 35}}, {'name': 'Nightmarish Rider', 'stats': {'health': 420, 'attack': 45, 'defense': 18, 'dodge_chance': 30, 'accuracy': 40}}],
        'lootgoblins': [{'name': 'Treasure-laden Goatman', 'stats': {'health': 330, 'attack': 40, 'defense': 10, 'dodge_chance': 40, 'accuracy': 25, 'block_penetration': 50}}, {'name': 'Heretical Hoarder', 'stats': {'health': 1, 'energy_shield': 660, 'attack': 45, 'defense': 5, 'dodge_chance': 10, 'accuracy': 30}}, {'name': 'Abyssal Scavenger', 'stats': {'health': 10, 'attack': 85, 'defense': 15, 'dodge_chance': 60, 'accuracy': 35}}],
        'bosses': [{'name': 'Malachai, The Nightmare', 'stats': {'health': 1000, 'energy_shield': 200, 'attack': 60, 'defense': 25, 'accuracy': 50, 'double_damage_chance': 15, 'defense_penetration': 40, 'block_penetration': 12}}, {'name': 'Avarius, Reassembled', 'stats': {'health': 1000, 'energy_shield': 300, 'attack': 55, 'defense': 30, 'accuracy': 40, 'double_damage_chance': 18, 'defense_penetration': 20, 'block_penetration': 10}}, {'name': 'Tukohama, Karui God of War', 'stats': {'health': 1100, 'attack': 62, 'defense': 28, 'block_chance': 30, 'accuracy': 30, 'defense_penetration': 20, 'block_penetration': 9}}, {'name': 'Kitava, the Insatiable', 'stats': {'health': 1150, 'attack': 40, 'defense': 22, 'crit_chance': 60, 'accuracy': 25, 'defense_penetration': 15, 'block_penetration': 14}}]
    },
    'items': {
        'magic': [{'name': 'Prophecy Wand of Destruction', 'type': 'Жезл', 'slot': 'weapon1', 'stats': {'attack': 25}}, {'name': 'Archon Hat of the Colossus', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'defense': 20, 'health': 50}}, {'name': 'Karui Chopper of Carnage', 'type': 'Двуручный топор', 'slot': 'weapon1', 'stats': {'attack': 23, 'health': 40}}, {'name': 'Titan Gauntlets of the Juggernaut', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'defense': 15, 'health': 35}}, {'name': 'Stealth Boots of the Phantom', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 7, 'health': 20}}, {'name': 'Archon Kite Shield of Aegis', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 9, 'health': 30}}, {'name': 'Moonstone Ring of Power', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'energy_shield': 30, 'health': 25}}, {'name': 'Vanguard Belt of the Titan', 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 100}}, {'name': 'Agate Amulet of Fortitude', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'health': 70, 'attack': 9}}, {'name': 'Judgement Staff of Domination', 'type': 'Посох', 'slot': 'weapon1', 'stats': {'attack': 23, 'block_chance': 5}}, {'name': 'Ezomyte Burgonet of Stone', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'defense': 20, 'health': 15}}, {'name': 'Murder Mitts of Slaying', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 10, 'crit_chance': 4}}, {'name': 'Goliath Greaves of Stability', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'health': 60, 'defense': 8}}, {'name': 'Recurve Bow of the Storm', 'type': 'Лук', 'slot': 'weapon1', 'stats': {'attack': 22, 'crit_chance': 6}}, {'name': 'Glorious Plate of the Leviathan', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 120, 'defense': 10}}, {'name': 'Prismatic Ring of All', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'health': 25, 'energy_shield': 25, 'attack': 2}}, {'name': 'Turquoise Amulet of the Wind', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'dodge_chance': 4, 'attack': 7}}, {'name': 'Champion Kite Shield of Victory', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 9, 'defense': 9}}, {'name': 'Sorcerer Gloves of the Archmage', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'energy_shield': 45, 'crit_chance': 3}}, {'name': 'Hubris Circlet of the Mind', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'energy_shield': 65}}] + FLOOR_3_NEW_ITEMS['magic'],
        'rare': [{'name': 'Storm Fist Titan Gauntlets', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 10, 'crit_chance': 5, 'health': 45}}, {'name': 'Dire Lock Vanguard Belt', 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 150, 'defense': 8}}, {'name': 'Miracle Stride Stealth Boots', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 8, 'health': 75}}, {'name': 'Behemoth Crest Ezomyte Burgonet', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'attack': 15, 'defense': 10, 'health': 20}}, {'name': 'Aegis of the Last Stand Archon Shield', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 10, 'defense': 15, 'health': 100}}, {'name': 'Rage Talisman Agate Amulet', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'attack': 13, 'health': 60}}, {'name': 'Oblivion Loop Moonstone Ring', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'energy_shield': 30, 'crit_chance': 5, 'attack': 5}}, {'name': 'Tempest Song Recurve Bow', 'type': 'Лук', 'slot': 'weapon1', 'stats': {'attack': 26, 'crit_chance': 8}}, {'name': 'Kaom\'s Guard Glorious Plate', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 150, 'defense': 10, 'block_chance': 6}}, {'name': 'Gale Pace Goliath Greaves', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 6, 'health': 90, 'defense': 5}}, {'name': 'Apocalypse Grip Murder Mitts', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 10, 'crit_chance': 5, 'energy_shield': 35}}, {'name': 'Mind Cage Hubris Circlet', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'energy_shield': 85, 'defense': 10, 'crit_chance': 2}}, {'name': 'Maelstrom Spire Judgement Staff', 'type': 'Посох', 'slot': 'weapon1', 'stats': {'attack': 26, 'block_chance': 5, 'energy_shield': 20}}, {'name': 'Unwavering Guard Champion Shield', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 15, 'defense': 10, 'energy_shield': 15}}, {'name': 'Whispering Hand Sorcerer Gloves', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'crit_chance': 5, 'energy_shield': 100}}] + FLOOR_3_NEW_ITEMS['rare'] + NEW_SET_AND_EXPANSION_ITEMS['floor_3'].get('rare', []),
        'unique': [{'name': 'Belly of the Beast', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 300, 'defense': 10}}, {'name': 'Abyssus', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'crit_chance': 5, 'attack': 25, 'defense': 5}}, {'name': 'Death\'s Opus', 'type': 'Лук', 'slot': 'weapon1', 'stats': {'attack': 15, 'crit_chance': 30}}, {'name': 'Rat\'s Nest', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'crit_chance': 11, 'dodge_chance': 11}}, {'name': 'The Surrender', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 15, 'health': 250, 'defense': 20}}, {'name': 'Doedre\'s Skin', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'energy_shield': 150, 'attack': 5, 'health': 50}}, {'name': 'Marohi Erqi', 'type': 'Двуручная булава', 'slot': 'weapon1', 'stats': {'attack': 42, 'defense': 10}}, {'name': 'Lightning Coil', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 150, 'defense': 20, 'attack': 12}}, {'name': 'Devoto\'s Devotion', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'dodge_chance': 11, 'attack': 12, 'defense': 10}}] + FLOOR_3_NEW_ITEMS['unique'] + NEW_SET_AND_EXPANSION_ITEMS['floor_3'].get('unique', []) + NEW_MECHANIC_ITEMS['floor_3']['unique'] + NEW_STRANGE_ITEMS['floor_3']['unique'],
        'legendary': [{'name': 'Kaom\'s Heart', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 500}}, {'name': 'Shavronne\'s Wrappings', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'energy_shield': 280, 'defense': 10}}] + FLOOR_3_NEW_ITEMS['legendary'] + NEW_SET_AND_EXPANSION_ITEMS['floor_3'].get('legendary', []) + NEW_MECHANIC_ITEMS['floor_3']['legendary'] + NEW_STRANGE_ITEMS['floor_3']['legendary']
    }
}
# ЭТАЖ 4: АТЛАС МИРОВ (THE ATLAS OF WORLDS - ENDGAME)
FLOOR_4_CONTENT = {
    'monsters': {
        'common': [{'name': 'Hydra Guardian Minion', 'stats': {'health': 600, 'attack': 55, 'defense': 25, 'dodge_chance': 20}}, {'name': 'Phoenix Guardian Minion', 'stats': {'health': 550, 'attack': 60, 'defense': 20, 'crit_chance': 15}}, {'name': 'Chimera Guardian Minion', 'stats': {'health': 600, 'attack': 58, 'defense': 30, 'block_chance': 15}}, {'name': 'Minotaur Guardian Minion', 'stats': {'health': 700, 'attack': 60, 'defense': 35}}, {'name': 'Syndicate Operative', 'stats': {'health': 400, 'energy_shield': 200, 'attack': 65, 'defense': 22, 'crit_chance': 35}}, {'name': 'Elder Tentacle', 'stats': {'health': 840, 'attack': 52, 'defense': 28}}, {'name': 'Shaper\'s Follower', 'stats': {'health': 550, 'energy_shield': 300, 'attack': 64, 'defense': 25, 'dodge_chance': 15}}],
        'rare': [{'name': 'Constrictor Guardian', 'stats': {'health': 1100, 'attack': 75, 'defense': 30, 'crit_chance': 15}}, {'name': 'Purifier Guardian', 'stats': {'health': 900, 'energy_shield': 450, 'attack': 80, 'defense': 28, 'block_penetration': 15}}, {'name': 'Enslaver Guardian', 'stats': {'health': 1250, 'attack': 73, 'defense': 35, 'block_chance': 20}}, {'name': 'Eradicator Guardian', 'stats': {'health': 950, 'energy_shield': 350, 'attack': 74, 'defense': 25, 'dodge_chance': 25}}, {'name': 'Syndicate Mastermind', 'stats': {'health': 1000, 'energy_shield': 700, 'attack': 80, 'defense': 30, 'crit_chance': 25}}],
        'lootgoblins': [{'name': 'Shaper-touched Hoarder', 'stats': {'health': 1, 'energy_shield': 1400, 'attack': 69, 'defense': 15, 'dodge_chance': 20}}, {'name': 'Elder\'s Covetous Creation', 'stats': {'health': 950, 'attack': 65, 'defense': 30, 'dodge_chance': 33, 'block_penetration': 40}}, {'name': 'Atlas Fugitive', 'stats': {'health': 500, 'attack': 100, 'defense': 20, 'dodge_chance': 30}}],
        'bosses': [
    # Создатель - его космические атаки невозможно избежать
    {'name': 'The Shaper', 'stats': {'health': 800, 'energy_shield': 2000, 'attack': 100, 'defense': 35, 'accuracy': 45, 'double_damage_chance': 25, 'defense_penetration': 30, 'block_penetration': 15, 'cannot_be_dodged': True}},
    # Древний - его сокрушительные удары нельзя заблокировать
    {'name': 'The Elder', 'stats': {'health': 2400, 'attack': 95, 'defense': 40, 'block_chance': 20, 'accuracy': 50, 'double_damage_chance': 20, 'defense_penetration': 22, 'block_penetration': 14, 'cannot_be_blocked': True}},
    # Сирус - мастер боя, не оставляющий уязвимых мест для критов
    {'name': 'Sirus, Awakener of Worlds', 'stats': {'health': 1300, 'energy_shield': 1200, 'attack': 110, 'defense': 30, 'crit_chance': 15, 'accuracy': 30, 'defense_penetration': 19, 'block_penetration': 15, 'cannot_be_crit': True}},
    # Мейвен - наблюдательница, иммунная к "удаче" двойного урона
    {'name': 'The Maven', 'stats': {'health': 500, 'max_health': 500, 'energy_shield': 3000, 'max_energy_shield': 3000, 'attack': 70, 'defense': 30, 'dodge_chance': 20, 'accuracy': 35, 'double_damage_chance': 15, 'defense_penetration': 20, 'block_penetration': 13, 'immune_to_double_damage': True}}]
    },
    'items': {
        'magic': [{'name': 'Void Wand of the Void', 'type': 'Жезл', 'slot': 'weapon1', 'stats': {'attack': 34}}, {'name': 'Regicide Mask of the God', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'defense': 25, 'health': 80}}, {'name': 'Vaal Axe of Annihilation', 'type': 'Двуручный топор', 'slot': 'weapon1', 'stats': {'attack': 30, 'health': 70}}, {'name': 'Colossal Gauntlets of the Titan', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'defense': 30, 'energy_shield': 35}}, {'name': 'Sorcerer Boots of the Void', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 10, 'energy_shield': 60}}, {'name': 'Pinnacle Tower Shield of Supremacy', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 17}}, {'name': 'Diamond Ring of Criticals', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'crit_chance': 10}}, {'name': 'Crystal Belt of the Colossus', 'type': 'Пояс', 'slot': 'belt', 'stats': {'energy_shield': 80, 'health': 120}}, {'name': 'Marble Amulet of Power', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'health': 120, 'attack': 12}}, {'name': 'Void Sceptre of Nothingness', 'type': 'Одноручная булава', 'slot': 'weapon1', 'stats': {'attack': 32, 'energy_shield': 60}}, {'name': 'Harbinger Bow of the End', 'type': 'Лук', 'slot': 'weapon1', 'stats': {'attack': 30, 'crit_chance': 10}}, {'name': 'Vaal Regalia of the Master', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'energy_shield': 250}}, {'name': 'Titan Greaves of the Behemoth', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'health': 140, 'defense': 15}}, {'name': 'Spiked Gloves of the Assassin', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 20, 'crit_chance': 2}}, {'name': 'Eternal Burgonet of the Warlord', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'defense': 26, 'block_chance': 5}}, {'name': 'Steel Ring of the Elder', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'attack': 20}}, {'name': 'Blue Pearl Amulet of the Shaper', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'energy_shield': 120, 'crit_chance': 2}}, {'name': 'Crusader Buckler of Faith', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 15, 'defense': 15}}, {'name': 'Fingerless Silk Gloves of the Exile', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'crit_chance': 8, 'attack': 12, 'energy_shield': 40}}, {'name': 'Nightmare Bascinet of Terror', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'crit_chance': 5, 'defense': 20, 'attack': 14}}] + FLOOR_4_NEW_ITEMS['magic'],
        'rare': [{'name': 'Rift Grasp Colossal Gauntlets', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 18, 'crit_chance': 4, 'health': 120}}, {'name': 'Hypnotic Coil Crystal Belt', 'type': 'Пояс', 'slot': 'belt', 'stats': {'health': 130, 'energy_shield': 140}}, {'name': 'Apocalypse Stride Sorcerer Boots', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 11, 'health': 110, 'energy_shield': 55}}, {'name': 'Blight Horn Eternal Burgonet', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'attack': 15, 'defense': 25, 'health': 100}}, {'name': 'Unthinkable Fate Pinnacle Shield', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 12, 'defense': 20, 'health': 115}}, {'name': 'Pandemonium Eye Marble Amulet', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'attack': 15, 'health': 150, 'crit_chance': 5}}, {'name': 'Pain Twirl Diamond Ring', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'attack': 6, 'crit_chance': 8, 'health': 80}}, {'name': 'Wraith Song Harbinger Bow', 'type': 'Лук', 'slot': 'weapon1', 'stats': {'attack': 40, 'crit_chance': 10}}, {'name': 'Cathedral of Stars Vaal Regalia', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'energy_shield': 200, 'defense': 25, 'health': 80}}, {'name': 'Armageddon March Titan Greaves', 'type': 'Ботинки', 'slot': 'boots', 'stats': {'dodge_chance': 8, 'health': 180, 'defense': 18}}, {'name': 'Ghoul Touch Spiked Gloves', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 8, 'crit_chance': 7, 'health': 90}}, {'name': 'Sorrow Crest Nightmare Bascinet', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'crit_chance': 3, 'attack': 17, 'defense': 22, 'energy_shield': 100}}, {'name': 'Cosmic Pillar Void Sceptre', 'type': 'Одноручная булава', 'slot': 'weapon1', 'stats': {'attack': 35, 'energy_shield': 150, 'crit_chance': 4}}, {'name': 'Elder\'s Bastion Crusader Buckler', 'type': 'Щит', 'slot': 'weapon2', 'stats': {'block_chance': 13, 'defense': 18, 'energy_shield': 90, 'health': 70}}, {'name': 'Mortal Urge Fingerless Silk Gloves', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'crit_chance': 6, 'attack': 18, 'energy_shield': 100}}] + FLOOR_4_NEW_ITEMS['rare'] + NEW_SET_AND_EXPANSION_ITEMS['floor_4'].get('rare', []) + NEW_RARE_ITEMS_F4 + NEW_SCALING_ITEMS_F4['rare'],
        'unique': [{'name': 'Carcass Jack', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 230, 'defense': 20, 'attack': 25}}, {'name': 'Void Battery', 'type': 'Жезл', 'slot': 'weapon1', 'stats': {'attack': 5, 'crit_chance': 40, 'energy_shield': 150}}, {'name': 'Tombfist', 'type': 'Перчатки', 'slot': 'gloves', 'stats': {'attack': 15, 'health': 230}}, {'name': 'Inpulsa\'s Broken Heart', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 220, 'attack': 10, 'crit_chance': 10}}, {'name': 'Farrul\'s Fur', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 120, 'dodge_chance': 20, 'crit_chance': 10}}, {'name': 'The Pandemonius', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'attack': 25, 'dodge_chance': 6, 'health': 150}}, {'name': 'Circle of Fear', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'attack': 30, 'defense': 5, 'energy_shield': 10}}, {'name': 'Watcher\'s Eye', 'type': 'Амулет', 'slot': 'amulet', 'stats': {'health': 200, 'energy_shield': 200, 'attack': 10, 'crit_chance': 5}}, {'name': 'Kalandra\'s Touch', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'health': 50, 'energy_shield': 50, 'attack': 10, 'defense': 5, 'crit_chance': 5, 'dodge_chance': 5, 'block_chance': 5}}, {'name': 'Indigon', 'type': 'Шлем', 'slot': 'helmet', 'stats': {'energy_shield': 350, 'attack': 10, 'defense': 10}}] + FLOOR_4_NEW_ITEMS['unique'] + NEW_SET_AND_EXPANSION_ITEMS['floor_4'].get('unique', []) + NEW_UNIQUE_ITEMS_F4 + NEW_STRANGE_ITEMS['floor_4']['unique'] + NEW_SCALING_ITEMS_F4['unique'],
        'legendary': [{'name': 'Original Sin', 'type': 'Кольцо', 'slot': 'ring', 'stats': {'attack': 65}}, {'name': 'Replica Farrul\'s Fur', 'type': 'Нательная броня', 'slot': 'body_armour', 'stats': {'health': 200, 'block_chance': 20, 'attack': 20, 'defense': 15}}] + FLOOR_4_NEW_ITEMS['legendary'] + NEW_SET_AND_EXPANSION_ITEMS['floor_4'].get('legendary', []) + NEW_MECHANIC_ITEMS['floor_4']['legendary'] + NEW_LEGENDARY_ITEMS_F4 + NEW_STRANGE_ITEMS['floor_4']['legendary'] + NEW_SCALING_ITEMS_F4['legendary']
    }
}
# ОБЪЕДИНЕННЫЙ СЛОВАРЬ КОНТЕНТА
CONTENT = {
    'floor_1': FLOOR_1_CONTENT,
    'floor_2': FLOOR_2_CONTENT,
    'floor_3': FLOOR_3_CONTENT,
    'floor_4': FLOOR_4_CONTENT,
}

FISHING_XP_PER_LEVEL = [0] + [int(100 * (1.12 ** i)) for i in range(1, 201)]

FISHING_RODS = {
    'rod_01': {'name': "Ветвь с Побережья", 'level_req': 1, 'cost': 0, 'stats': {'catch_chance': 30, 'valuable_catch_chance': 1, 'big_catch_chance': 1}},
    'rod_02': {'name': "Удочка из Костяного Шипа", 'level_req': 5, 'cost': 100, 'stats': {'catch_chance': 45, 'valuable_catch_chance': 8, 'big_catch_chance': 5}},
    'rod_03': {'name': "Коралловая Удочка Ваал", 'level_req': 10, 'cost': 650, 'stats': {'catch_chance': 55, 'valuable_catch_chance': 12, 'big_catch_chance': 8}},
    'rod_04': {'name': "Посох Вечного Рыбака", 'level_req': 20, 'cost': 1300, 'stats': {'catch_chance': 60, 'valuable_catch_chance': 15, 'big_catch_chance': 10}},
    'rod_05': {'name': "Кармическая Удочка Азори", 'level_req': 30, 'cost': 2500, 'stats': {'catch_chance': 65, 'valuable_catch_chance': 18, 'big_catch_chance': 15}},
    'rod_06': {'name': "Хребет Тукохамы", 'level_req': 45, 'cost': 4500, 'stats': {'catch_chance': 70, 'valuable_catch_chance': 22, 'big_catch_chance': 20}},
    'rod_07': {'name': "Оскверненное Удилище Китавы", 'level_req': 55, 'cost': 10000, 'stats': {'catch_chance': 75, 'valuable_catch_chance': 26, 'big_catch_chance': 35}},
    'rod_08': {'name': "Эфирная Леска Создателя", 'level_req': 70, 'cost': 30000, 'stats': {'catch_chance': 80, 'valuable_catch_chance': 30, 'big_catch_chance': 30}},
    'rod_09': {'name': "Щупальце Древнего", 'level_req': 80, 'cost': 60000, 'stats': {'catch_chance': 85, 'valuable_catch_chance': 40, 'big_catch_chance': 35}},
    'rod_10': {'name': "Отражение Каландры", 'level_req': 90, 'cost': 125000, 'stats': {'catch_chance': 100, 'valuable_catch_chance': 50, 'big_catch_chance': 45}},
    'rod_11': {'name': "Удочка из Пустоты", 'level_req': 100, 'cost': 250000, 'stats': {'catch_chance': 100, 'valuable_catch_chance': 70, 'big_catch_chance': 70}}
}

FISHING_STAT_PERKS = {
    'f_atk_1': {'name': "+1 к Атаке", 'cost': 4, 'stat': 'perm_attack_bonus', 'value': 1},
    'f_hp_5':  {'name': "+5 к Здоровью", 'cost': 3, 'stat': 'perm_health_bonus', 'value': 5},
    'f_crit_1': {'name': "+1% к Крит. шансу", 'cost': 10, 'stat': 'perm_crit_chance_bonus', 'value': 1},
    'f_dodge_1':{'name': "+1% к Увороту", 'cost': 15, 'stat': 'perm_dodge_chance_bonus', 'value': 1},
    'f_def_1':  {'name': "+1% к Защите", 'cost': 8, 'stat': 'perm_defense_bonus', 'value': 1},
    'f_mf_2': {'name': "+2% к Поиску Предметов", 'cost': 3, 'stat': 'perm_magic_find_bonus', 'value': 2}
}

# Новый функционал: наживка
FISHING_BAITS = {
    'bait_common': {'name': "Простая наживка", 'cost': 1500, 'casts': 10, 'effect_desc': "+10% к шансу поймать Uncommon рыбу", 'effect': {'type': 'rarity_boost', 'rarity': 'uncommon', 'bonus': 10}},
    'bait_rare': {'name': "Редкая наживка", 'cost': 5000, 'casts': 10, 'effect_desc': "+15% к шансу поймать Rare рыбу", 'effect': {'type': 'rarity_boost', 'rarity': 'rare', 'bonus': 15}},
    'bait_heavy': {'name': "Утяжеленная наживка", 'cost': 10000, 'casts': 15, 'effect_desc': "+25% к весу улова", 'effect': {'type': 'weight_boost', 'bonus': 0.25}},
    'bait_lucky': {'name': "Счастливая наживка", 'cost': 20000, 'casts': 5, 'effect_desc': "Увеличивает шанс найти Затонувший сундук в 3 раза", 'effect': {'type': 'chest_boost', 'multiplier': 3}},
    'bait_xp': {'name': "Мудрая наживка", 'cost': 25000, 'casts': 20, 'effect_desc': "+20% к получаемому опыту с рыбалки", 'effect': {'type': 'xp_boost', 'bonus': 0.20}},
    'bait_quality': {'name': "Качественная наживка", 'cost': 35000, 'casts': 10, 'effect_desc': "Повышает минимальный вес рыбы", 'effect': {'type': 'min_weight_boost', 'bonus': 4.0}},
    'bait_seed': {'name': "Наживка Садовода", 'cost': 50000, 'casts': 10, 'effect_desc': "+25% к шансу найти семя Харвеста", 'effect': {'type': 'seed_chance_boost', 'bonus': 0.25}},
}

FISHING_LOOT_TABLE = {
    'tier1': { # Уровень 0+
        'common': [ # 60% шанс
            {'name': 'Грязный ботинок', 'base_xp': 30, 'base_price': 1},
            {'name': 'Ржавая жестянка', 'base_xp': 30, 'base_price': 1},
            {'name': 'Морской слизень', 'base_xp': 40, 'base_price': 1}, # было 2
        ],
        'uncommon': [ # 25% шанс
            {'name': 'Прибрежный бычок', 'base_xp': 50, 'base_price': 2}, # было 3
            {'name': 'Пещерный рак', 'base_xp': 55, 'base_price': 2}, # было 4
        ],
        'rare': [ # 15% шанс
            {'name': 'Карп Роа', 'base_xp': 120, 'base_price': 3}, # было 5
            {'name': 'Призрачная креветка', 'base_xp': 150, 'base_price': 4}, # было 6
        ]
    },
    'tier2': { # Уровень 20+
        'common': [
            {'name': 'Сарнская плотва', 'base_xp': 150, 'base_price': 3}, # было 5
            {'name': 'Канальный сом', 'base_xp': 170, 'base_price': 3}, # было 5
        ],
        'uncommon': [
            {'name': 'Черный страж', 'base_xp': 240, 'base_price': 6}, # было 8
            {'name': 'Самоцветный окунь', 'base_xp': 260, 'base_price': 6}, # было 9
        ],
        'rare': [
            {'name': 'Vaal-овый угорь', 'base_xp': 600, 'base_price': 15}, # было 20
            {'name': 'Солнечный лещ', 'base_xp': 580, 'base_price': 20}, # было 35
        ]
    },
    'tier3': { # Уровень 40+
        'common': [
            {'name': 'Горный голец', 'base_xp': 610, 'base_price': 12}, # было 20
            {'name': 'Каменный краб', 'base_xp': 660, 'base_price': 12}, # было 20
        ],
        'uncommon': [
            {'name': 'Боевая рыба Тукохамы', 'base_xp': 920, 'base_price': 20}, # было 30
            {'name': 'Кровавый карп Китавы', 'base_xp': 1020, 'base_price': 20}, # было 30
        ],
        'rare': [
            {'name': 'Огненный лосось Невинности', 'base_xp': 1800, 'base_price': 35}, # было 50
            {'name': 'Сумрачный тунец', 'base_xp': 1950, 'base_price': 35}, # было 50
        ]
    },
    'tier4': { # Уровень 60+
        'common': [
            {'name': 'Атласная треска', 'base_xp': 1300, 'base_price': 30},
            {'name': 'Пустотная пикша', 'base_xp': 1400, 'base_price': 30},
            {'name': 'Глубинная камбала', 'base_xp': 1350, 'base_price': 32},
            {'name': 'Темный палтус', 'base_xp': 1450, 'base_price': 33},
            {'name': 'Холодный морской окунь', 'base_xp': 1380, 'base_price': 31},
            {'name': 'Ледяная треска', 'base_xp': 1420, 'base_price': 32},
            {'name': 'Полярная пикша', 'base_xp': 1500, 'base_price': 35},
        ],
        'uncommon': [
            {'name': 'Рыба-гидра', 'base_xp': 1500, 'base_price': 50},
            {'name': 'Феникс-рыба', 'base_xp': 1620, 'base_price': 50},
            {'name': 'Теневой лосось', 'base_xp': 1550, 'base_price': 55},
            {'name': 'Кровавый тунец', 'base_xp': 1600, 'base_price': 52},
            {'name': 'Эфирный скат', 'base_xp': 1650, 'base_price': 58},
            {'name': 'Астральный окунь', 'base_xp': 1580, 'base_price': 53},
            {'name': 'Древний осетр', 'base_xp': 1700, 'base_price': 60},
        ],
        'rare': [
            {'name': 'Рыба-химера', 'base_xp': 2020, 'base_price': 80},
            {'name': 'Рыба-минотавр', 'base_xp': 2040, 'base_price': 80},
            {'name': 'Грифон-рыба', 'base_xp': 2100, 'base_price': 85},
            {'name': 'Кракен-младший', 'base_xp': 2150, 'base_price': 90},
            {'name': 'Василиск-рыба', 'base_xp': 2080, 'base_price': 82},
            {'name': 'Феникс-акула', 'base_xp': 2200, 'base_price': 95},
            {'name': 'Легендарный морской змей', 'base_xp': 2250, 'base_price': 100},
        ],
        'special': [
            {'name': 'Затонувший сундук', 'type': 'treasure_chest'}
        ]
    },
    'tier5': { # Уровень 80+
        'common': [
            {'name': 'Осколок грез', 'base_xp': 1850, 'base_price': 60}, # было 100
            {'name': 'Эхо бездны', 'base_xp': 1900, 'base_price': 70}, # было 120
        ],
        'uncommon': [
            {'name': 'Космический скат Создателя', 'base_xp': 950, 'base_price': 120}, # было 200
            {'name': 'Кристалл Древнего', 'base_xp': 3000, 'base_price': 120}, # было 200
        ],
        'rare': [
            {'name': 'Сердце Пробудителя', 'base_xp': 4000, 'base_price': 250}, # было 400
            {'name': 'Слеза Мейвен', 'base_xp': 4000, 'base_price': 300}, # было 500
        ]
    }
}

# =============================================================================
# НОВЫЙ РАЗДЕЛ: КОНТЕНТ ДЛЯ ХАРВЕСТА
# =============================================================================

HARVEST_XP_PER_LEVEL = [0] + [int(250 * (1.15 ** i)) for i in range(1, 101)]

HARVEST_SEEDS = {
    'seed_t1': {'name': "Семя Дикого Зерна", 'tier': 1, 'growth_time': 300, 'produces': 'plant_t1'}, # 5 мин
    'seed_t2': {'name': "Семя Первобытного Шипа", 'tier': 2, 'growth_time': 600, 'produces': 'plant_t2'}, # 10 мин
    'seed_t3': {'name': "Семя Яркого Цветка", 'tier': 3, 'growth_time': 1200, 'produces': 'plant_t3'}, # 20 мин
    'seed_t4': {'name': "Семя Жуткой Лозы", 'tier': 4, 'growth_time': 1800, 'produces': 'plant_t4'}, # 30 мин
    'seed_t5': {'name': "Семя Священной Рощи", 'tier': 5, 'growth_time': 3200, 'produces': 'plant_t5'} # 1 час
}

HARVEST_PLANTS = {
    'plant_t1': {'name': "Зрелое Дикое Зерно", 'tier': 1, 'xp': 70, 'currency': 'lifeforce', 'value': 20},
    'plant_t2': {'name': "Зрелый Первобытный Шип", 'tier': 2, 'xp': 160, 'currency': 'lifeforce', 'value': 100},
    'plant_t3': {'name': "Зрелый Яркий Цветок", 'tier': 3, 'xp': 300, 'currency': 'lifeforce', 'value': 300},
    'plant_t4': {'name': "Зрелая Жуткая Лоза", 'tier': 4, 'xp': 600, 'currency': 'lifeforce', 'value': 600},
    'plant_t5': {'name': "Плод Священной Рощи", 'tier': 5, 'xp': 1200, 'currency': 'crystalline', 'value': 1}
}

HARVEST_FERTILIZERS = {
    'fertilizer_t2': {'name': "Удобрение Т2", 'cost': 50},
    'fertilizer_t3': {'name': "Удобрение Т3", 'cost': 150},
    'fertilizer_t4': {'name': "Удобрение Т4", 'cost': 300},
    'fertilizer_t5': {'name': "Удобрение Т5", 'cost': 1000}
}

HARVEST_BED_UPGRADES = {
    'speed_1': {'name': "Ускорение роста (10%)", 'cost': 500, 'bonus': 0.1},
    'speed_2': {'name': "Ускорение роста (20%)", 'cost': 1500, 'bonus': 0.2},
    'speed_3': {'name': "Ускорение роста (30%)", 'cost': 4000, 'bonus': 0.3},
    'speed_4': {'name': "Ускорение роста (40%)", 'cost': 10000, 'bonus': 0.4},
    'speed_5': {'name': "Ускорение роста (50%)", 'cost': 25000, 'bonus': 0.5},
}

HARVEST_CRAFTING_CONFIG = {
    # ИЗМЕНЕНИЕ: Стоимость теперь зависит только от редкости
    'rarity_config': {
        'magic': {'cost': 2},
        'rare': {'cost': 4},
        'unique': {'cost': 8},
        'legendary': {'cost': 15}
    },
    # ИЗМЕНЕНИЕ: Очки теперь зависят от этажа и редкости
    'floor_points': {
        '1': {'magic': 5, 'rare': 10, 'unique': 15, 'legendary': 20},
        '2': {'magic': 10, 'rare': 15, 'unique': 20, 'legendary': 25},
        '3': {'magic': 15, 'rare': 20, 'unique': 25, 'legendary': 30},
        '4': {'magic': 25, 'rare': 30, 'unique': 40, 'legendary': 50}
    },
    'stat_costs': {
        'attack': {'name': "+2 Атаки", 'cost': 1, 'value': 2},
        'dodge_chance': {'name': "+2% Уворота", 'cost': 3, 'value': 2},
        'energy_shield': {'name': "+5 Энергощита", 'cost': 1, 'value': 5},
        'defense': {'name': "+1% Защиты", 'cost': 1, 'value': 1},
        'crit_chance': {'name': "+1% Крит. шанса", 'cost': 1, 'value': 1},
        'block_chance': {'name': "+2% Шанса блока", 'cost': 3, 'value': 2},
        'health': {'name': "+5 Здоровья", 'cost': 1, 'value': 5},
        'accuracy': {'name': "+5 Точности", 'cost': 2, 'value': 5},
        'double_damage_chance': {'name': "+1% Двойного урона", 'cost': 2, 'value': 1},
        'defense_penetration': {'name': "+1% Пробития", 'cost': 1, 'value': 2},
    }
}

# =============================================================================
# НОВЫЙ РАЗДЕЛ: ГАДАЛЬНЫЕ КАРТЫ
# =============================================================================

DIVINATION_CARDS = {
    # card_id: {name, stack_size, reward_type, reward_value, weight}
    'the_hoarder': {
        'name': "The Hoarder",
        'stack_size': 4,
        'reward_type': 'divine_shards',
        'reward_value': 2,
        'weight': 30
    },
    'the_seeker': {
        'name': "The Seeker",
        'stack_size': 5,
        'reward_type': 'divine_shards',
        'reward_value': 5,
        'weight': 25
    },
    'the_saints_treasure': {
        'name': "The Saint's Treasure",
        'stack_size': 6,
        'reward_type': 'divine_orbs',
        'reward_value': 1,
        'weight': 20
    },
    'the_enlightened': {
        'name': "The Enlightened",
        'stack_size': 8,
        'reward_type': 'divine_orbs',
        'reward_value': 3,
        'weight': 15
    },
    'the_immortal': {
        'name': "The Immortal",
        'stack_size': 10,
        'reward_type': 'divine_orbs',
        'reward_value': 10,
        'weight': 5
    },
    'house_of_mirrors': {
        'name': "House of Mirrors",
        'stack_size': 5,
        'reward_type': 'mirrors',
        'reward_value': 1,
        'weight': 5
    }
}

PASSIVE_SKILL_TREE = {
    # --------------------------- ВЕТВЬ СИЛЫ (43) ---------------------------
    'str_start': {'name': "Начало Пути Воина", 'desc': "Первый шаг к несокрушимой мощи.", 'branch': "str", 'sub_branch': None, 'effects': {}, 'requires': None},
    'str_hp1': {'name': "Живучесть", 'desc': "+15 к макс. здоровью.", 'branch': "str", 'sub_branch': 'core', 'effects': {'max_health': 15}, 'requires': 'str_start'},
    'str_atk1': {'name': "Тяжелые замахи", 'desc': "+4 к атаке.", 'branch': "str", 'sub_branch': 'core', 'effects': {'attack': 4}, 'requires': 'str_hp1'},
    'str_def1': {'name': "Железная кожа", 'desc': "+3% к защите.", 'branch': "str", 'sub_branch': 'core', 'effects': {'defense': 3}, 'requires': 'str_atk1'},
    'str_hp2': {'name': "Крепость плоти", 'desc': "+25 к макс. здоровью.", 'branch': "str", 'sub_branch': 'core', 'effects': {'max_health': 25}, 'requires': 'str_def1'},
    
    # --- Под-ветвь Брони и Блока ---
    'str_path_block_entry': {'name': "Путь Стража", 'desc': "+1% к шансу блока, +1% к защите.", 'branch': "str", 'sub_branch': 'block', 'effects': {'block_chance': 1, 'defense': 1}, 'requires': 'str_hp2'},
    'str_b_hp1': {'name': "Стойкость", 'desc': "+20 к здоровью.", 'branch': "str", 'sub_branch': 'block', 'effects': {'max_health': 20}, 'requires': 'str_path_block_entry'},
    'str_b_block1': {'name': "Реакция", 'desc': "+1% к шансу блока.", 'branch': "str", 'sub_branch': 'block', 'effects': {'block_chance': 1}, 'requires': 'str_b_hp1'},
    'str_b_def1': {'name': "Неподвижность", 'desc': "+3% к защите.", 'branch': "str", 'sub_branch': 'block', 'effects': {'defense': 3}, 'requires': 'str_b_block1'},
    'str_b_hp2': {'name': "Гора", 'desc': "+30 к здоровью.", 'branch': "str", 'sub_branch': 'block', 'effects': {'max_health': 30}, 'requires': 'str_b_def1'},
    'str_b_crit_reduc1': {'name': "Закалка", 'desc': "+10% к защите от крит. урона.", 'branch': "str", 'sub_branch': 'block', 'effects': {'crit_damage_reduction': 10}, 'requires': 'str_b_hp2'},
    'str_b_block2': {'name': "Идеальная стойка", 'desc': "+2% к шансу блока.", 'branch': "str", 'sub_branch': 'block', 'effects': {'block_chance': 2}, 'requires': 'str_b_crit_reduc1'},
    'str_b_def2': {'name': "Костяная броня", 'desc': "+5% к защите.", 'branch': "str", 'sub_branch': 'block', 'effects': {'defense': 5}, 'requires': 'str_b_block2'},
    'str_b_hp3': {'name': "Кровь гигантов", 'desc': "+50 к здоровью.", 'branch': "str", 'sub_branch': 'block', 'effects': {'max_health': 50}, 'requires': 'str_b_def2'},
    'str_b_block3': {'name': "Бастион", 'desc': "+3% к шансу блока.", 'branch': "str", 'sub_branch': 'block', 'effects': {'block_chance': 3}, 'requires': 'str_b_hp3'},
    'str_b_crit_reduc2': {'name': "Несокрушимость", 'desc': "+15% к защите от крит. урона.", 'branch': "str", 'sub_branch': 'block', 'effects': {'crit_damage_reduction': 15}, 'requires': 'str_b_block3'},
    'str_keystone_unwavering': {'name': "Непоколебимая Стойка (Ключевое)", 'desc': "От вас нельзя увернуться, но и вы не можете уворачиваться (шанс уворота = 0).", 'branch': "str", 'sub_branch': 'block', 'effects': {'cannot_be_dodged': True, 'dodge_chance_override': 0}, 'requires': 'str_b_crit_reduc2'},
    'str_b_def3': {'name': "Джуггернаут", 'desc': "+10% к защите.", 'branch': "str", 'sub_branch': 'block', 'effects': {'defense': 10}, 'requires': 'str_keystone_unwavering'},
    'str_b_hp4': {'name': "Воля к жизни", 'desc': "+15% к макс. здоровью.", 'branch': "str", 'sub_branch': 'block', 'effects': {'max_health_mult': 0.15}, 'requires': 'str_b_def3'},

    # --- Под-ветвь Урона и Здоровья ---
    'str_path_damage_entry': {'name': "Путь Разрушителя", 'desc': "+3 к атаке.", 'branch': "str", 'sub_branch': 'damage', 'effects': {'attack': 3}, 'requires': 'str_hp2'},
    'str_d_atk1': {'name': "Точность удара", 'desc': "+2 к атаке, +5 к точности.", 'branch': "str", 'sub_branch': 'damage', 'effects': {'attack': 2, 'accuracy': 5}, 'requires': 'str_path_damage_entry'},
    'str_d_hp1': {'name': "Запас сил", 'desc': "+20 к здоровью.", 'branch': "str", 'sub_branch': 'damage', 'effects': {'max_health': 20}, 'requires': 'str_d_atk1'},
    'str_d_pen1': {'name': "Пролом брони", 'desc': "+5% к пробитию защиты.", 'branch': "str", 'sub_branch': 'damage', 'effects': {'defense_penetration': 5}, 'requires': 'str_d_hp1'},
    'str_d_atk2': {'name': "Сила", 'desc': "+4 к атаке.", 'branch': "str", 'sub_branch': 'damage', 'effects': {'attack': 4}, 'requires': 'str_d_pen1'},
    'str_d_hp2': {'name': "Сердце воина", 'desc': "+30 к здоровью.", 'branch': "str", 'sub_branch': 'damage', 'effects': {'max_health': 30}, 'requires': 'str_d_atk2'},
    'str_d_atk3': {'name': "Ярость берсерка", 'desc': "+5 к атаке.", 'branch': "str", 'sub_branch': 'damage', 'effects': {'attack': 5}, 'requires': 'str_d_hp2'},
    'str_d_pen2': {'name': "Раскалыватель", 'desc': "+8% к пробитию защиты.", 'branch': "str", 'sub_branch': 'damage', 'effects': {'defense_penetration': 8}, 'requires': 'str_d_atk3'},
    'str_d_hp3': {'name': "Кровь предков", 'desc': "+40 к здоровью.", 'branch': "str", 'sub_branch': 'damage', 'effects': {'max_health': 40}, 'requires': 'str_d_pen2'},
    'str_d_atk4': {'name': "Безжалостность", 'desc': "+6% к атаке.", 'branch': "str", 'sub_branch': 'damage', 'effects': {'attack_mult': 0.06}, 'requires': 'str_d_hp3'},
    'str_d_pen3': {'name': "Аннигиляция", 'desc': "+10% к пробитию защиты.", 'branch': "str", 'sub_branch': 'damage', 'effects': {'defense_penetration': 10}, 'requires': 'str_d_atk4'},
    'str_keystone_blood_magic': {'name': "Кровная Магия (Ключевое)", 'desc': "+300 к макс. здоровью, но ваш энергощит становится равен 1.", 'branch': "str", 'sub_branch': 'damage', 'effects': {'max_health': 300, 'max_energy_shield_override': 1}, 'requires': 'str_d_pen3'},
    'str_d_hp4': {'name': "Кровавый обряд", 'desc': "+80 к здоровью.", 'branch': "str", 'sub_branch': 'damage', 'effects': {'max_health': 80}, 'requires': 'str_keystone_blood_magic'},
    'str_d_ls1': {'name': "Жажда битвы", 'desc': "+3% к вампиризму.", 'branch': "str", 'sub_branch': 'damage', 'effects': {'lifesteal': 3}, 'requires': 'str_d_hp4'},
    
    # --------------------------- ВЕТВЬ ЛОВКОСТИ (43) ---------------------------
    'dex_start': {'name': "Начало Пути Охотника", 'desc': "Шаг к становлению неуловимой тенью.", 'branch': "dex", 'sub_branch': None, 'effects': {}, 'requires': None},
    'dex_dodge1': {'name': "Легкость", 'desc': "+1% к шансу уворота.", 'branch': "dex", 'sub_branch': 'core', 'effects': {'dodge_chance': 1}, 'requires': 'dex_start'},
    'dex_acc1': {'name': "Острый глаз", 'desc': "+10 к точности.", 'branch': "dex", 'sub_branch': 'core', 'effects': {'accuracy': 10}, 'requires': 'dex_dodge1'},
    'dex_crit1': {'name': "Слабое место", 'desc': "+2% к шансу крит. удара.", 'branch': "dex", 'sub_branch': 'core', 'effects': {'crit_chance': 2}, 'requires': 'dex_acc1'},
    'dex_dodge2': {'name': "Быстрые рефлексы", 'desc': "+2% к шансу уворота.", 'branch': "dex", 'sub_branch': 'core', 'effects': {'dodge_chance': 2}, 'requires': 'dex_crit1'},

    # --- Под-ветвь Двойного Урона и Вампиризма ---
    'dex_path_dd_entry': {'name': "Путь Ассасина", 'desc': "+1% к шансу двойного урона.", 'branch': "dex", 'sub_branch': 'dd', 'effects': {'double_damage_chance': 1}, 'requires': 'dex_dodge2'},
    'dex_dd_atk1': {'name': "Парные клинки", 'desc': "+3 к атаке, +1% двойного урона.", 'branch': "dex", 'sub_branch': 'dd', 'effects': {'attack': 3, 'double_damage_chance': 1}, 'requires': 'dex_path_dd_entry'},
    'dex_dd_ls1': {'name': "Кровопийца", 'desc': "+1% к вампиризму.", 'branch': "dex", 'sub_branch': 'dd', 'effects': {'lifesteal': 1}, 'requires': 'dex_dd_atk1'},
    'dex_dd_dodge1': {'name': "Подвижность", 'desc': "+2% к увороту.", 'branch': "dex", 'sub_branch': 'dd', 'effects': {'dodge_chance': 2}, 'requires': 'dex_dd_ls1'},
    'dex_dd_dd1': {'name': "Амбидекстрия", 'desc': "+2% к шансу двойного урона.", 'branch': "dex", 'sub_branch': 'dd', 'effects': {'double_damage_chance': 2}, 'requires': 'dex_dd_dodge1'},
    'dex_dd_ls2': {'name': "Ненасытный голод", 'desc': "+2% к вампиризму.", 'branch': "dex", 'sub_branch': 'dd', 'effects': {'lifesteal': 2}, 'requires': 'dex_dd_dd1'},
    'dex_dd_atk2': {'name': "Точные выпады", 'desc': "+5 к атаке.", 'branch': "dex", 'sub_branch': 'dd', 'effects': {'attack': 5}, 'requires': 'dex_dd_ls2'},
    'dex_dd_dodge2': {'name': "Призрачный шаг", 'desc': "+3% к увороту.", 'branch': "dex", 'sub_branch': 'dd', 'effects': {'dodge_chance': 3}, 'requires': 'dex_dd_atk2'},
    'dex_dd_dd2': {'name': "Танец смерти", 'desc': "+3% к шансу двойного урона.", 'branch': "dex", 'sub_branch': 'dd', 'effects': {'double_damage_chance': 3}, 'requires': 'dex_dd_dodge2'},
    'dex_dd_hp1': {'name': "Выносливость", 'desc': "+30 к здоровью.", 'branch': "dex", 'sub_branch': 'dd', 'effects': {'max_health': 30}, 'requires': 'dex_dd_dd2'},
    'dex_dd_ls3': {'name': "Пир плоти", 'desc': "+3% к вампиризму.", 'branch': "dex", 'sub_branch': 'dd', 'effects': {'lifesteal': 3}, 'requires': 'dex_dd_hp1'},
    'dex_keystone_glass_cannon': {'name': "Стеклянная Пушка (Ключевое)", 'desc': "+10% к шансу крит. удара и +5% двойного урона, но -30% от макс. здоровья.", 'branch': "dex", 'sub_branch': 'dd', 'effects': {'crit_chance': 10, 'double_damage_chance': 5, 'max_health_mult': -0.30}, 'requires': 'dex_dd_ls3'},
    'dex_dd_atk3': {'name': "Смертельный танец", 'desc': "+10 к атаке.", 'branch': "dex", 'sub_branch': 'dd', 'effects': {'attack': 10}, 'requires': 'dex_keystone_glass_cannon'},
    'dex_dd_dd3': {'name': "Шквал клинков", 'desc': "+5% к шансу двойного урона.", 'branch': "dex", 'sub_branch': 'dd', 'effects': {'double_damage_chance': 5}, 'requires': 'dex_dd_atk3'},

    # --- Под-ветвь Критов и Точности ---
    'dex_path_crit_entry': {'name': "Путь Снайпера", 'desc': "+5 к точности.", 'branch': "dex", 'sub_branch': 'crit', 'effects': {'accuracy': 5}, 'requires': 'dex_dodge2'},
    'dex_c_acc1': {'name': "Интуиция", 'desc': "+8 к точности.", 'branch': "dex", 'sub_branch': 'crit', 'effects': {'accuracy': 8}, 'requires': 'dex_path_crit_entry'},
    'dex_c_crit1': {'name': "Смертоносность", 'desc': "+1% к шансу крит. удара.", 'branch': "dex", 'sub_branch': 'crit', 'effects': {'crit_chance': 1}, 'requires': 'dex_c_acc1'},
    'dex_c_dodge1': {'name': "Акробатика", 'desc': "+2% к увороту.", 'branch': "dex", 'sub_branch': 'crit', 'effects': {'dodge_chance': 2}, 'requires': 'dex_c_crit1'},
    'dex_c_acc2': {'name': "Безупречная техника", 'desc': "+10 к точности.", 'branch': "dex", 'sub_branch': 'crit', 'effects': {'accuracy': 10}, 'requires': 'dex_c_dodge1'},
    'dex_c_crit2': {'name': "Хладнокровие", 'desc': "+2% к шансу крит. удара.", 'branch': "dex", 'sub_branch': 'crit', 'effects': {'crit_chance': 2}, 'requires': 'dex_c_acc2'},
    'dex_c_mf1': {'name': "Интуиция охотника", 'desc': "+15% к поиску предметов.", 'branch': "dex", 'sub_branch': 'crit', 'effects': {'magic_find': 15}, 'requires': 'dex_c_crit2'},
    'dex_c_acc3': {'name': "Око орла", 'desc': "+20 к точности.", 'branch': "dex", 'sub_branch': 'crit', 'effects': {'accuracy': 20}, 'requires': 'dex_c_mf1'},
    'dex_c_crit3': {'name': "Убийственное намерение", 'desc': "+25% к множителю крит. урона.", 'branch': "dex", 'sub_branch': 'crit', 'effects': {'crit_multiplier': 25}, 'requires': 'dex_c_acc3'},
    'dex_c_dodge2': {'name': "Грация", 'desc': "+4% к увороту.", 'branch': "dex", 'sub_branch': 'crit', 'effects': {'dodge_chance': 4}, 'requires': 'dex_c_crit3'},
    'dex_c_crit4': {'name': "Безжалостный удар", 'desc': "+4% к шансу крит. удара.", 'branch': "dex", 'sub_branch': 'crit', 'effects': {'crit_chance': 4}, 'requires': 'dex_c_dodge2'},
    'dex_keystone_perfect_agony': {'name': "Идеальная Агония (Ключевое)", 'desc': "Крит. удары получают +50% к пробитию защиты, но наносят на 25% меньше урона.", 'branch': "dex", 'sub_branch': 'crit', 'effects': {'crit_pen': 50, 'attack_mult': -0.25}, 'requires': 'dex_c_crit4'},
    'dex_c_acc4': {'name': "Предвидение", 'desc': "+30 к точности.", 'branch': "dex", 'sub_branch': 'crit', 'effects': {'accuracy': 30}, 'requires': 'dex_keystone_perfect_agony'},
    'dex_c_crit5': {'name': "Апогей мощи", 'desc': "+40% к множителю крит. урона.", 'branch': "dex", 'sub_branch': 'crit', 'effects': {'crit_multiplier': 40}, 'requires': 'dex_c_acc4'},

    # --------------------------- ВЕТВЬ ИНТЕЛЛЕКТА (ИСПРАВЛЕНО) ---------------------------
    'int_start': {'name': "Начало Пути Мудреца", 'desc': "Первый шаг к овладению тайными знаниями.", 'branch': "int", 'sub_branch': None, 'effects': {}, 'requires': None},
    'int_es1': {'name': "Мысленный барьер", 'desc': "+15 к макс. энергощиту.", 'branch': "int", 'sub_branch': 'core', 'effects': {'max_energy_shield': 15}, 'requires': 'int_start'},
    'int_crit1': {'name': "Фокус", 'desc': "+2% к шансу крит. удара.", 'branch': "int", 'sub_branch': 'core', 'effects': {'crit_chance': 2}, 'requires': 'int_es1'},
    'int_es_leech1': {'name': "Поглощение души", 'desc': "+1% к вампиризму энергощита.", 'branch': "int", 'sub_branch': 'core', 'effects': {'es_leech_rate': 1}, 'requires': 'int_crit1'},
    'int_es2': {'name': "Концентрация", 'desc': "+20 к макс. энергощиту.", 'branch': "int", 'sub_branch': 'core', 'effects': {'max_energy_shield': 20}, 'requires': 'int_es_leech1'},
    'int_path_es_entry': {'name': "Путь Оккультиста", 'desc': "+10 к энергощиту.", 'branch': "int", 'sub_branch': 'es', 'effects': {'max_energy_shield': 10}, 'requires': 'int_es2'},
    'int_es_hp1': {'name': "Закалка духа", 'desc': "+10 к здоровью, +10 к энергощиту.", 'branch': "int", 'sub_branch': 'es', 'effects': {'max_health': 10, 'max_energy_shield': 10}, 'requires': 'int_path_es_entry'},
    'int_es_def1': {'name': "Руническая защита", 'desc': "+2% к защите.", 'branch': "int", 'sub_branch': 'es', 'effects': {'defense': 2}, 'requires': 'int_es_hp1'},
    'int_es_es1': {'name': "Дисциплина", 'desc': "+50 к энергощиту.", 'branch': "int", 'sub_branch': 'es', 'effects': {'max_energy_shield': 50}, 'requires': 'int_es_def1'},
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Переименованы ID, чтобы избежать дублирования ---
    'int_es_leech2': {'name': "Ненасытность", 'desc': "+1% к вампиризму энергощита.", 'branch': "int", 'sub_branch': 'es', 'effects': {'es_leech_rate': 1}, 'requires': 'int_es_es1'},
    'int_es_es2': {'name': "Сила духа", 'desc': "+5% к макс. энергощиту.", 'branch': "int", 'sub_branch': 'es', 'effects': {'max_energy_shield_mult': 0.05}, 'requires': 'int_es_leech2'},
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    'int_es_hp2': {'name': "Баланс", 'desc': "+25 к здоровью, +15 к энергощиту.", 'branch': "int", 'sub_branch': 'es', 'effects': {'max_health': 25, 'max_energy_shield': 15}, 'requires': 'int_es_es2'},
    'int_es_def2': {'name': "Эгида", 'desc': "+4% к защите.", 'branch': "int", 'sub_branch': 'es', 'effects': {'defense': 4}, 'requires': 'int_es_hp2'},
    'int_es_es3': {'name': "Призматический барьер", 'desc': "+40 к энергощиту.", 'branch': "int", 'sub_branch': 'es', 'effects': {'max_energy_shield': 40}, 'requires': 'int_es_def2'},
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Переименованы ID ---
    'int_es_leech3': {'name': "Вечный голод", 'desc': "+2% к вампиризму энергощита.", 'branch': "int", 'sub_branch': 'es', 'effects': {'es_leech_rate': 2}, 'requires': 'int_es_es3'},
    'int_es_es4': {'name': "Безграничный разум", 'desc': "+10% к макс. энергощиту.", 'branch': "int", 'sub_branch': 'es', 'effects': {'max_energy_shield_mult': 0.10}, 'requires': 'int_es_leech3'},
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    'int_keystone_ghost_reaver': {'name': "Призрачный Жнец (Ключевое)", 'desc': "Весь ваш вампиризм здоровья применяется к энергощиту вместо здоровья.", 'branch': "int", 'sub_branch': 'es', 'effects': {'lifesteal_to_es': True}, 'requires': 'int_es_es4'},
    'int_es_es5': {'name': "Незримый покров", 'desc': "+80 к энергощиту.", 'branch': "int", 'sub_branch': 'es', 'effects': {'max_energy_shield': 80}, 'requires': 'int_keystone_ghost_reaver'},
    # --- НАЧАЛО ИЗМЕНЕНИЙ: Переименованы ID ---
    'int_es_leech4': {'name': "Эссенция пустоты", 'desc': "+3% к вампиризму энергощита.", 'branch': "int", 'sub_branch': 'es', 'effects': {'es_leech_rate': 3}, 'requires': 'int_es_es5'},
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
    'int_path_crit_entry': {'name': "Путь Адепта", 'desc': "+1% к шансу крит. удара.", 'branch': "int", 'sub_branch': 'crit', 'effects': {'crit_chance': 1}, 'requires': 'int_es2'},
    'int_c_crit1': {'name': "Точность мысли", 'desc': "+2% к шансу крит. удара.", 'branch': "int", 'sub_branch': 'crit', 'effects': {'crit_chance': 2}, 'requires': 'int_path_crit_entry'},
    'int_c_pen1': {'name': "Разрушение барьеров", 'desc': "+8% к пробитию защиты.", 'branch': "int", 'sub_branch': 'crit', 'effects': {'defense_penetration': 8}, 'requires': 'int_c_crit1'},
    'int_c_atk1': {'name': "Магическая мощь", 'desc': "+3 к атаке.", 'branch': "int", 'sub_branch': 'crit', 'effects': {'attack': 3}, 'requires': 'int_c_pen1'},
    'int_c_crit2': {'name': "Смертельный холод", 'desc': "+15% к множителю крит. урона.", 'branch': "int", 'sub_branch': 'crit', 'effects': {'crit_multiplier': 15}, 'requires': 'int_c_atk1'},
    'int_c_pen2': {'name': "Энтропия", 'desc': "+10% к пробитию защиты.", 'branch': "int", 'sub_branch': 'crit', 'effects': {'defense_penetration': 10}, 'requires': 'int_c_crit2'},
    'int_c_crit3': {'name': "Глубокий фокус", 'desc': "+3% к шансу крит. удара.", 'branch': "int", 'sub_branch': 'crit', 'effects': {'crit_chance': 3}, 'requires': 'int_c_pen2'},
    'int_c_atk2': {'name': "Сила разума", 'desc': "+4 к атаке.", 'branch': "int", 'sub_branch': 'crit', 'effects': {'attack': 4}, 'requires': 'int_c_crit3'},
    'int_c_pen3': {'name': "Неизбежность", 'desc': "+12% к пробитию защиты.", 'branch': "int", 'sub_branch': 'crit', 'effects': {'defense_penetration': 12}, 'requires': 'int_c_atk2'},
    'int_c_crit4': {'name': "Ледяное сердце", 'desc': "+30% к множителю крит. урона.", 'branch': "int", 'sub_branch': 'crit', 'effects': {'crit_multiplier': 30}, 'requires': 'int_c_pen3'},
    'int_c_atk3': {'name': "Воплощение мощи", 'desc': "+10% к атаке.", 'branch': "int", 'sub_branch': 'crit', 'effects': {'attack_mult': 0.10}, 'requires': 'int_c_crit4'},
    'int_keystone_mind_over_matter': {'name': "Разум превыше Материи (Ключевое)", 'desc': "50% урона, который должен был быть получен здоровьем, вместо этого отнимается от энергощита.", 'branch': "int", 'sub_branch': 'crit', 'effects': {'damage_split_mom': 0.50}, 'requires': 'int_c_atk3'},
    'int_c_es1': {'name': "Эфирный барьер", 'desc': "+50 к энергощиту.", 'branch': "int", 'sub_branch': 'crit', 'effects': {'max_energy_shield': 50}, 'requires': 'int_keystone_mind_over_matter'},
    'int_c_crit5': {'name': "Заряд пустоты", 'desc': "+4% к шансу крит. удара.", 'branch': "int", 'sub_branch': 'crit', 'effects': {'crit_chance': 4}, 'requires': 'int_c_es1'},

    # --------------------------- ВЕТВЬ КОМАНДИРА (УНИВЕРСАЛЬНАЯ) ---------------------------
    'com_start': {'name': "Начало Пути Командира", 'desc': "Первый шаг к тактическому превосходству.", 'branch': "com", 'sub_branch': None, 'effects': {}, 'requires': None},
    'com_hp1': {'name': "Основы выживания", 'desc': "+20 к макс. здоровью.", 'branch': "com", 'sub_branch': 'core', 'effects': {'max_health': 20}, 'requires': 'com_start'},
    'com_atk1': {'name': "Основы боя", 'desc': "+3 к атаке.", 'branch': "com", 'sub_branch': 'core', 'effects': {'attack': 3}, 'requires': 'com_hp1'},
    'com_def1': {'name': "Основы защиты", 'desc': "+2% к защите.", 'branch': "com", 'sub_branch': 'core', 'effects': {'defense': 2}, 'requires': 'com_atk1'},
    'com_all_stats1': {'name': "Всесторонняя подготовка", 'desc': "+5 к здоровью, +5 к энергощиту, +1 к атаке.", 'branch': "com", 'sub_branch': 'core', 'effects': {'max_health': 5, 'max_energy_shield': 5, 'attack': 1}, 'requires': 'com_def1'},

    # --- Под-ветвь Тактика (Экономика и Утилити) ---
    'com_path_tactician_entry': {'name': "Путь Тактика", 'desc': "Услуги торговцев, лекарей и кузнецов на 5% дешевле.", 'branch': "com", 'sub_branch': 'tactician', 'effects': {'service_discount': 5}, 'requires': 'com_all_stats1'},
    'com_t_gold1': {'name': "Делец", 'desc': "+10% к поиску золота.", 'branch': "com", 'sub_branch': 'tactician', 'effects': {'gold_find': 10}, 'requires': 'com_path_tactician_entry'},
    'com_t_shrinedur1': {'name': "Связь с богами", 'desc': "Длительность эффектов Святилищ увеличена на 1 бой.", 'branch': "com", 'sub_branch': 'tactician', 'effects': {'shrine_duration': 1}, 'requires': 'com_t_gold1'},
    'com_t_discount1': {'name': "Опытный торговец", 'desc': "Услуги торговцев, лекарей и кузнецов еще на 5% дешевле.", 'branch': "com", 'sub_branch': 'tactician', 'effects': {'service_discount': 5}, 'requires': 'com_t_shrinedur1'},
    'com_t_gold2': {'name': "Золотая лихорадка", 'desc': "+15% к поиску золота.", 'branch': "com", 'sub_branch': 'tactician', 'effects': {'gold_find': 15}, 'requires': 'com_t_discount1'},
    'com_t_shrinedur2': {'name': "Божественное покровительство", 'desc': "Длительность эффектов Святилищ увеличена еще на 1 бой.", 'branch': "com", 'sub_branch': 'tactician', 'effects': {'shrine_duration': 1}, 'requires': 'com_t_gold2'},
    'com_t_discount2': {'name': "Мастер переговоров", 'desc': "Услуги торговцев, лекарей и кузнецов еще на 10% дешевле.", 'branch': "com", 'sub_branch': 'tactician', 'effects': {'service_discount': 10}, 'requires': 'com_t_shrinedur2'},
    'com_t_gold3': {'name': "Сокровище дракона", 'desc': "+25% к поиску золота.", 'branch': "com", 'sub_branch': 'tactician', 'effects': {'gold_find': 25}, 'requires': 'com_t_discount2'},
    'com_keystone_resolute_technique': {'name': "Точные Удары (Ключевое)", 'desc': "Ваши атаки не могут быть уклонены, но вы не можете наносить критические удары.", 'branch': "com", 'sub_branch': 'tactician', 'effects': {'cannot_be_dodged': True, 'crit_chance_override': 0}, 'requires': 'com_t_gold3'},

    # --- Под-ветвь Выжившего (Защита и Регенерация) ---
    'com_path_survivor_entry': {'name': "Путь Выжившего", 'desc': "+15 к здоровью, +10 к энергощиту.", 'branch': "com", 'sub_branch': 'survivor', 'effects': {'max_health': 15, 'max_energy_shield': 10}, 'requires': 'com_all_stats1'},
    'com_s_regen1': {'name': "Восстановление", 'desc': "Восстанавливает 1% здоровья после каждой победы.", 'branch': "com", 'sub_branch': 'survivor', 'effects': {'health_regen': 1}, 'requires': 'com_path_survivor_entry'},
    'com_s_crit_reduc1': {'name': "Толстая кожа", 'desc': "+8% к защите от крит. урона.", 'branch': "com", 'sub_branch': 'survivor', 'effects': {'crit_damage_reduction': 8}, 'requires': 'com_s_regen1'},
    'com_s_es_regen1': {'name': "Подпитка духа", 'desc': "+15 к макс. энергощиту.", 'branch': "com", 'sub_branch': 'survivor', 'effects': {'max_energy_shield': 15}, 'requires': 'com_s_crit_reduc1'},
    'com_s_hp1': {'name': "Крепкое телосложение", 'desc': "+40 к здоровью.", 'branch': "com", 'sub_branch': 'survivor', 'effects': {'max_health': 40}, 'requires': 'com_s_es_regen1'},
    'com_s_regen2': {'name': "Быстрая регенерация", 'desc': "Восстанавливает еще 1% здоровья после каждой победы.", 'branch': "com", 'sub_branch': 'survivor', 'effects': {'health_regen': 1}, 'requires': 'com_s_hp1'},
    'com_s_crit_reduc2': {'name': "Стальная воля", 'desc': "+12% к защите от крит. урона.", 'branch': "com", 'sub_branch': 'survivor', 'effects': {'crit_damage_reduction': 12}, 'requires': 'com_s_regen2'},
    'com_s_es_regen2': {'name': "Духовный бастион", 'desc': "+20 к макс. энергощиту.", 'branch': "com", 'sub_branch': 'survivor', 'effects': {'max_energy_shield': 20}, 'requires': 'com_s_crit_reduc2'},
    'com_s_hp2': {'name': "Неутомимость", 'desc': "+60 к здоровью.", 'branch': "com", 'sub_branch': 'survivor', 'effects': {'max_health': 60}, 'requires': 'com_s_es_regen2'},
    'com_keystone_divine_shield': {'name': "Изобилие (Ключевое)", 'desc': "После победы над монстрами вы всегда получаете 4 предмета на выбор вместо 3.", 'branch': "com", 'sub_branch': 'survivor', 'effects': {'extra_loot_choice': 1}, 'requires': 'com_s_hp2'},

    # --------------------------- ВЕТВЬ СТРАННИКА (ГИБРИДНАЯ) ---------------------------
    'asc_start': {'name': "Начало Пути Странника", 'desc': "Шаг навстречу неизведанному.", 'branch': "asc", 'sub_branch': None, 'effects': {}, 'requires': None},
    'asc_hybrid1': {'name': "Равновесие", 'desc': "+10 к здоровью, +10 к энергощиту.", 'branch': "asc", 'sub_branch': 'core', 'effects': {'max_health': 10, 'max_energy_shield': 10}, 'requires': 'asc_start'},
    'asc_hybrid2': {'name': "Смертоносная точность", 'desc': "+2 к атаке, +2% к шансу крит. удара.", 'branch': "asc", 'sub_branch': 'core', 'effects': {'attack': 2, 'crit_chance': 2}, 'requires': 'asc_hybrid1'},
    'asc_hybrid3': {'name': "Гибкая защита", 'desc': "+1% к увороту, +1% к блоку.", 'branch': "asc", 'sub_branch': 'core', 'effects': {'dodge_chance': 1, 'block_chance': 1}, 'requires': 'asc_hybrid2'},
    'asc_hybrid4': {'name': "Проницательность", 'desc': "+4% к пробитию, +8 к точности.", 'branch': "asc", 'sub_branch': 'core', 'effects': {'defense_penetration': 4, 'accuracy': 8}, 'requires': 'asc_hybrid3'},

    # --- Под-ветвь Искателя (Удача и Предметы) ---
    'asc_path_seeker_entry': {'name': "Путь Искателя", 'desc': "+10% к поиску магических предметов.", 'branch': "asc", 'sub_branch': 'seeker', 'effects': {'magic_find': 10}, 'requires': 'asc_hybrid4'},
    'asc_s_mf1': {'name': "Интуиция кладоискателя", 'desc': "+15% к поиску магических предметов.", 'branch': "asc", 'sub_branch': 'seeker', 'effects': {'magic_find': 15}, 'requires': 'asc_path_seeker_entry'},
    'asc_s_gold1': {'name': "Алчность", 'desc': "+15% к поиску золота.", 'branch': "asc", 'sub_branch': 'seeker', 'effects': {'gold_find': 15}, 'requires': 'asc_s_mf1'},
    'asc_s_mf2': {'name': "Глаз Грифона", 'desc': "+20% к поиску магических предметов.", 'branch': "asc", 'sub_branch': 'seeker', 'effects': {'magic_find': 20}, 'requires': 'asc_s_gold1'},
    'asc_s_gold2': {'name': "Прикосновение Мидаса", 'desc': "+20% к поиску золота.", 'branch': "asc", 'sub_branch': 'seeker', 'effects': {'gold_find': 20}, 'requires': 'asc_s_mf2'},
    'asc_s_mf3': {'name': "Наследие Перандусов", 'desc': "+25% к поиску магических предметов.", 'branch': "asc", 'sub_branch': 'seeker', 'effects': {'magic_find': 25}, 'requires': 'asc_s_gold2'},
    'asc_keystone_ancestral_bond': {'name': "Связь с Предками (Ключевое)", 'desc': "Вы получаете +100% к поиску золота и предметов, но теряете 25% от макс. здоровья и энергощита.", 'branch': "asc", 'sub_branch': 'seeker', 'effects': {'magic_find': 100, 'gold_find': 100, 'max_health_mult': -0.25, 'max_energy_shield_mult': -0.25}, 'requires': 'asc_s_mf3'},

    # --- Под-ветвь Авантюриста (Риск и Награда) ---
    'asc_path_gambler_entry': {'name': "Путь Авантюриста", 'desc': "+1% к шансу двойного урона.", 'branch': "asc", 'sub_branch': 'gambler', 'effects': {'double_damage_chance': 1}, 'requires': 'asc_hybrid4'},
    'asc_g_dd1': {'name': "Двойной или ничего", 'desc': "+1% к шансу двойного урона.", 'branch': "asc", 'sub_branch': 'gambler', 'effects': {'double_damage_chance': 1}, 'requires': 'asc_path_gambler_entry'},
    'asc_g_crit1': {'name': "Рискованный удар", 'desc': "+2% к шансу крит. удара.", 'branch': "asc", 'sub_branch': 'gambler', 'effects': {'crit_chance': 2}, 'requires': 'asc_g_dd1'},
    'asc_g_dd2': {'name': "Игра в кости", 'desc': "+2% к шансу двойного урона.", 'branch': "asc", 'sub_branch': 'gambler', 'effects': {'double_damage_chance': 2}, 'requires': 'asc_g_crit1'},
    'asc_g_crit2': {'name': "Ставка на всё", 'desc': "+3% к шансу крит. удара.", 'branch': "asc", 'sub_branch': 'gambler', 'effects': {'crit_chance': 3}, 'requires': 'asc_g_dd2'},
    'asc_g_dd3': {'name': "Фортуна", 'desc': "+2% к шансу двойного урона.", 'branch': "asc", 'sub_branch': 'gambler', 'effects': {'double_damage_chance': 2}, 'requires': 'asc_g_crit2'},
    'asc_g_crit3': {'name': "Сердце колоды", 'desc': "+4% к шансу крит. удара.", 'branch': "asc", 'sub_branch': 'gambler', 'effects': {'crit_chance': 4}, 'requires': 'asc_g_dd3'},
    'asc_keystone_elemental_overload': {'name': "Перегрузка Стихиями (Ключевое)", 'desc': "Ваши крит. удары имеют множитель x1.5, но дают +50% к шансу двойного урона", 'branch': "asc", 'sub_branch': 'gambler', 'effects': {'crit_mult_override': 1.5, 'temp_dd_on_crit': 50}, 'requires': 'asc_g_crit3'},
}

ASCENDANCY_PASSIVES = {
    'marauder': {
        'unstoppable': {'name': "Неудержимость", 'desc': "Ваши атаки не могут быть заблокированы.", 'effects': {'cannot_be_blocked': True}},
        'blood_of_the_karui': {'name': "Кровь Каруи", 'desc': "+150 к максимальному здоровью.", 'effects': {'max_health': 150}},
        'juggernaut': {'name': "Джаггернаут", 'desc': "+15% к защите и +15% к защите от крит. урона.", 'effects': {'defense': 15, 'crit_damage_reduction': 15}},
        'overwhelm': {'name': "Подавление", 'desc': "+20% к пробитию защиты.", 'effects': {'defense_penetration': 20}},
        'resilience': {'name': "Несокрушимая воля", 'desc': "После победы над боссом вы получаете +50 к максимальному здоровью. Этот бонус сохраняется до конца забега и суммируется.", 'effects': {'perm_hp_on_boss': 50}},
        'undeniable': {'name': "Неоспоримость", 'desc': "+50 к точности и +10 к атаке.", 'effects': {'accuracy': 50, 'attack': 10}},
        'bone_breaker': {'name': "Костолом", 'desc': "+30% к множителю критического урона.", 'effects': {'crit_multiplier': 30}},
        'aspect_of_carnage': {'name': "Аспект Резни", 'desc': "Вы наносите на 20% больше урона, но и получаете на 10% больше урона.", 'effects': {'attack_mult': 0.20, 'increased_damage_taken': 0.10}},
    },
    'ranger': {
        'rapid_assault': {'name': "Стремительный Натиск", 'desc': "+8% к шансу двойного урона.", 'effects': {'double_damage_chance': 8}},
        'acrobatics': {'name': "Акробатика", 'desc': "+13% к шансу уворота.", 'effects': {'dodge_chance': 13}},
        'ricochet': {'name': "Смертоносный прицел", 'desc': "После победы над боссом вы получаете +10 к точности. Этот бонус сохраняется до конца забега и суммируется.", 'effects': {'perm_acc_on_boss': 10}},
        'farsight': {'name': "Дальнозоркость", 'desc': "+7% к шансу крит. удара и +50 к точности.", 'effects': {'crit_chance': 7, 'accuracy': 50}},
        'nature_s_bounty': {'name': "Дар Природы", 'desc': "После победы над боссом вы получаете дополнительный выбор из 2 предметов.", 'effects': {'extra_loot_choice_on_boss': 2}},
        'wind_dancer': {'name': "Танцующая с ветром", 'desc': "Если вас не ранили в прошлом ходу, вы получаете +20% к увороту.", 'effects': {'conditional_dodge': 20}},
        'focal_point': {'name': "Точка Фокусировки", 'desc': "Увеличивает эффект бонусов от комплектов на 50%.", 'effects': {'amplify_set_bonuses': 1.5}},
        'endless_quiver': {'name': "Бесконечный Колчан", 'desc': "+15 к атаке и +3% к вампиризму.", 'effects': {'attack': 15, 'lifesteal': 3}},
    },
    'witch': {
        'wicked_ward': {'name': "Греховный оберег", 'desc': "+3% к вампиризму энергощита.", 'effects': {'es_leech_rate': 3}},
        'arcane_surge': {'name': "Мистический всплеск", 'desc': "+15% к пробитию защиты и +4% к шансу крит. удара.", 'effects': {'defense_penetration': 15, 'crit_chance': 4}},
        'profane_bloom': {'name': "Поглощение знаний", 'desc': "После победы над боссом вы получаете +40 к максимальному энергощиту. Этот бонус сохраняется до конца забега и суммируется.", 'effects': {'perm_es_on_boss': 40}},
        'harness_the_void': {'name': "Обуздание Бездны", 'desc': "+8% к шансу двойного урона.", 'effects': {'double_damage_chance': 8}},
        'forbidden_power': {'name': "Запретная сила", 'desc': "+10 к атаке за каждые 100 макс. энергощита.", 'effects': {'attack_scaling_from_es': 0.1}},
        'occultist_s_dominion': {'name': "Владычество Оккультиста", 'desc': "+2% к вампиризму энергощита и +15 к атаке.", 'effects': {'es_leech_rate': 2, 'attack': 15}},
        'mastermind_of_discord': {'name': "Гений Диссонанса", 'desc': "+50% к множителю критического урона.", 'effects': {'crit_multiplier': 50}},
        'essence_drain': {'name': "Похищение сущности", 'desc': "+4% ко всем основным защитным характеристикам (блок, уворот, защита).", 'effects': {'block_chance': 4, 'dodge_chance': 4, 'defense': 4}}
    },
    'duelist': {
        'versatile_combatant': {'name': "Универсальный боец", 'desc': "Восстанавливает 5% от максимального здоровья при успешном блоке.", 'effects': {'heal_on_block_percent': 5}},
        'outmatch_and_outlast': {'name': "Превзойти и пережить", 'desc': "+8% к шансу блока и +2% к вампиризму.", 'effects': {'block_chance': 8, 'lifesteal': 2}},
        'gladiator_s_fortitude': {'name': "Стойкость Гладиатора", 'desc': "+80 к здоровью и +10% к защите.", 'effects': {'max_health': 80, 'defense': 10}},
        'arena_champion': {'name': "Чемпион Арены", 'desc': "+15 к атаке и +10% к защите от крит. урона.", 'effects': {'attack': 15, 'crit_damage_reduction': 10}},
        'violent_retaliation': {'name': "Жестокое возмездие", 'desc': "После блока ваша следующая атака наносит двойной урон.", 'effects': {'dd_on_block': True}},
        'blood_in_the_eyes': {'name': "Кровь в глазах", 'desc': "+15% к пробитию блока и +30 к точности.", 'effects': {'block_penetration': 15, 'accuracy': 30}},
        'challenger_s_might': {'name': "Мощь претендента", 'desc': "+10% к атаке.", 'effects': {'attack_mult': 0.10}},
        'master_of_the_arena': {'name': "Искусство блокирования", 'desc': "После победы над боссом вы получаете +4% к шансу блока. Этот бонус сохраняется до конца забега и суммируется.", 'effects': {'perm_block_on_boss': 4}},
    },
    'templar': {
        'divine_guidance': {'name': "Божественное укрепление", 'desc': "+50 к здоровью и +50 к энергощиту.", 'effects': {'max_health': 50, 'max_energy_shield': 50}},
        'instruments_of_virtue': {'name': "Орудия добродетели", 'desc': "+15 к атаке и +10% к пробитию защиты.", 'effects': {'attack': 15, 'defense_penetration': 10}},
        'guardian_s_prayer': {'name': "Молитва Хранителя", 'desc': "После победы над боссом вы получаете +4% к защите. Этот бонус сохраняется до конца забега и суммируется.", 'effects': {'perm_def_on_boss': 4}},
        'righteous_providence': {'name': "Праведное провидение", 'desc': "+7% к шансу крит. удара.", 'effects': {'crit_chance': 7}},
        'bastion_of_hope': {'name': "Бастион надежды", 'desc': "+8% к шансу блока и +5% к защите.", 'effects': {'block_chance': 8, 'defense': 5}},
        'illuminated_devotion': {'name': "Освященная преданность", 'desc': "+3% к вампиризму энергощита и +10 к атаке.", 'effects': {'es_leech_rate': 3, 'attack': 10}},
        'sign_of_purpose': {'name': "Знак предназначения", 'desc': "+20% к защите от крит. урона.", 'effects': {'crit_damage_reduction': 20}},
        'unwavering_crusade': {'name': "Непоколебимый крестовый поход", 'desc': "+8% к шансу двойного урона.", 'effects': {'double_damage_chance': 8}},
    },
    'shadow': {
        'ghost_dance': {'name': "Танец призрака", 'desc': "+12% к шансу уворота.", 'effects': {'dodge_chance': 12}},
        'assassin_s_mark': {'name': "Метка убийцы", 'desc': "+6% к шансу крит. удара и +25% к множителю крит. урона.", 'effects': {'crit_chance': 6, 'crit_multiplier': 25}},
        'walk_the_aether': {'name': "Прогулка по эфиру", 'desc': "Ваши атаки не могут быть уклонены.", 'effects': {'cannot_be_dodged': True}},
        'prolonged_pain': {'name': "Продленная боль", 'desc': "+6% к шансу двойного урона.", 'effects': {'double_damage_chance': 6}},
        'swift_killer': {'name': "Быстрый убийца", 'desc': "+15 к атаке и +2% к вампиризму.", 'effects': {'attack': 15, 'lifesteal': 2}},
        'mistwalker': {'name': "Ходящий в тумане", 'desc': "После победы над боссом вы получаете +4% к увороту до конца забега.", 'effects': {'perm_dodge_on_boss': 4}},
        'unstable_infusion': {'name': "Нестабильное насыщение", 'desc': "+70 к здоровью и +40 к энергощиту.", 'effects': {'max_health': 70, 'max_energy_shield': 40}},
        'deadly_infusion': {'name': "Смертельное насыщение", 'desc': "Крит. удары получают +25% к пробитию защиты.", 'effects': {'crit_pen': 25}},
    },
    'scion': {
        'path_of_the_warrior': {'name': "Путь Воина", 'desc': "+50 к здоровью и +8 к атаке.", 'effects': {'max_health': 50, 'attack': 8}},
        'path_of_the_ranger': {'name': "Путь Охотницы", 'desc': "+6% к увороту и +30 к точности.", 'effects': {'dodge_chance': 6, 'accuracy': 30}},
        'path_of_the_witch': {'name': "Путь Ведьмы", 'desc': "+80 к энергощиту и +4% к шансу крит. удара.", 'effects': {'max_energy_shield': 80, 'crit_chance': 4}},
        'ascendant_s_might': {'name': "Опыт странствий", 'desc': "После победы над боссом вы получаете +1% ко всем основным защитным характеристикам (блок, уворот, защита). Этот бонус сохраняется до конца забега и суммируется.", 'effects': {'perm_all_def_on_boss': 1}},
        'endless_inspiration': {'name': "Бесконечное вдохновение", 'desc': "Длительность эффектов Святилищ увеличена на 2 боя.", 'effects': {'shrine_duration': 2}},
        'master_of_all': {'name': "Мастер на все руки", 'desc': "+2% ко всем видам вампиризма (здоровье и энергощит).", 'effects': {'lifesteal': 2, 'es_leech_rate': 2}},
        'elemental_aegis': {'name': "Стихийная эгида", 'desc': "+25% к защите от крит. урона.", 'effects': {'crit_damage_reduction': 25}},
        'opportunist': {'name': "Оппортунист", 'desc': "+7% к шансу двойного урона.", 'effects': {'double_damage_chance': 7}},
    }
}

RHOA_NAMES = {
    1: "Быстроногий Боб",
    2: "Каменный Лоб",
    3: "Пернатый Ураган",
    4: "Грязный Гарри",
    5: "Костяная Погремушка",
    6: "Чемпион с Побережья"
}