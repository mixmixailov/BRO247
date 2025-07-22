import re
import datetime
from typing import Tuple

# RU
R_MIN_RU = re.compile(r"через\s+(\d+)\s*мин(?:ут[ыу]?)?\s+(.*)", re.I)
R_HR_RU = re.compile(r"через\s+(\d+)\s*час(?:а|ов)?\s+(.*)", re.I)
# EN
R_MIN_EN = re.compile(r"in\s+(\d+)\s*min(?:s|utes)?\s+(.*)", re.I)
R_HR_EN = re.compile(r"in\s+(\d+)\s*hour(?:s)?\s+(.*)", re.I)
# DateTime универсально (21.07.2025 18:00 или 21/07/2025 18:00)
R_DATE_TIME = re.compile(r"(\d{2})[./](\d{2})[./](\d{4})\s+(\d{2}):(\d{2})\s+(.*)")

def parse_delay(text: str, lang: str) -> Tuple[int | datetime.datetime, str] | None:
    """
    Парсит напоминание:
    - через 10мин ... / через 2 часа ... (RU)
    - in 10min ... / in 2 hours ... (EN)
    - 21.07.2025 18:00 ... (RU/EN)
    Возвращает (минуты, текст) или (datetime, текст) либо None.
    """
    # Пробуем дату (универсально для RU/EN)
    m = R_DATE_TIME.match(text.strip())
    if m:
        try:
            dt = datetime.datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)), int(m.group(4)), int(m.group(5)))
            msg = m.group(6).strip() or ("Без текста" if lang == "RU" else "No text")
            return dt, msg
        except Exception:
            return None

    # Интервалы по языку
    if lang == "RU":
        m = R_MIN_RU.match(text)
        if m:
            minutes = int(m.group(1))
            msg = m.group(2).strip() or "Без текста"
            return minutes, msg
        m = R_HR_RU.match(text)
        if m:
            hours = int(m.group(1))
            msg = m.group(2).strip() or "Без текста"
            return hours * 60, msg
    else:
        m = R_MIN_EN.match(text)
        if m:
            minutes = int(m.group(1))
            msg = m.group(2).strip() or "No text"
            return minutes, msg
        m = R_HR_EN.match(text)
        if m:
            hours = int(m.group(1))
            msg = m.group(2).strip() or "No text"
            return hours * 60, msg

    # Если ничего не нашли
    return None

