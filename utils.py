# utils.py

def escape_markdown(text: str) -> str:
    """
    Экранирует специальные символы для Telegram MarkdownV2.
    ВАЖНО: Использовать ParseMode.MARKDOWN_V2 для сообщений с этим текстом.
    """
    if not isinstance(text, str):
        text = str(text)
        
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    # Обратите внимание на \\ - мы экранируем сам \
    return "".join(f'\\{char}' if char in escape_chars else char for char in text)