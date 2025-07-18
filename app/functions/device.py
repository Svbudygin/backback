import re
from typing import Tuple
import json

from app import exceptions
from app.core.constants import DECIMALS, Banks, Bank, Type


def preprocess_message(message: str) -> str:
    while True:
        new_message = message.replace('  ', '')
        if len(new_message) == len(message):
            break
        message = new_message
    msg_array = message.split('сообщений | ')
    if len(msg_array) == 2:
        message = msg_array[1]
    else:
        message = msg_array[0]

    msg_array = message.split('сообщения | ')
    if len(msg_array) == 2:
        message = msg_array[1]
    else:
        message = msg_array[0]

    msg_array = message.split('сообщение | ')
    if len(msg_array) == 2:
        message = msg_array[1]
    else:
        message = msg_array[0]
    return message


def get_card_last_digits(sms: str) -> str | None:
    result = re.search(r'(karta|сч|карта|счет|счёт|schet|visa|mastercard|мир|mir)(\D|){4}[0-9]{4}', sms)
    if result is None:
        return None
    return result[0][-4:]


def try_get_card_last_digits(header):
    if header is None:
        return None
    result = re.search(r'(сч|karta|карт|счет|счёт|schet|visa|mastercard|мир|ecmc|mc|mir|ecmc|·)\D{0,4}[0-9]{4}', header)
    if result is None:
        return None
    return result[0][-4:]


def replace_inr(s: str):
    for i in range(len(s) - 1):
        if s[i] == 'r' and s[i + 1] == 's':
            t = ''
            g = ''
            t += s[i]
            t += s[i + 1]
            ind = i + 2
            while ind < len(s) and s[ind] in '0123456789., ':
                g += s[ind]
                ind += 1
            if len(g.replace(' ', '')) > 0:
                return s[0:i] + g + t.replace('rs', 'rub ') + s[ind:]

    return s


def add_r_after_numbers(text: str) -> str:
    # Добавляем "р" после чисел (включая десятичные), но только если "р" не стоит уже сразу после
    return re.sub(r'(?<!\d)(\d+(?:\.\d+)?)(?!р)', r'\1р', text)


def parse_message(sms: str, header: str, bank: str | None = None, recursion: int = 0) -> Tuple[int | None, str | None, str | None]:
    if recursion > 1:
        return None, None, None

    #name_pattern = r'[А-Я][а-я]* [А-Я]\.'
    #hasName = re.search(name_pattern, header)
    #if hasName:
    #    return None, None, None
    sms = header.lower() + " " + sms.lower()
    if bank == 'alfabusiness':
        sms = add_r_after_numbers(sms)
    if 'заблокирован' in sms or 'отказ' in sms or 'компрометаци' in sms or 'не поступил' in sms or 'заблокировали' in sms:
        raise exceptions.BlockedCardException()
    result = re.findall(r'зачислено [^A-Za-z\u0400-\u04FF]+ rur', sms)
    if result is not None and len(result) > 0:
        sms = result[-1] + sms
    pattern = r'(?<!\w)(mir|сч|мир|ecmc|mc|visa|mastercard|счёт|счет)(?!\w)'
    if (
            re.search(pattern, sms)
            and ' от ' not in sms
            and 'получен ' not in sms
            and 'перевод' in sms
    ):  # sber pay out
        return None, None, None
    sms = ' ^ ' + sms + ' ^'
    header = header.lower()
    sms = sms.replace('*', '·')
    sms = sms.replace(' ', ' ')
    new_amount = None
    if 'tjs' in sms:
        sms = re.sub(r'karta \d{12}(\d{4})', r'visa\1', sms)

        if 'summa' in sms and 'zachislenie' in sms and 'komis' in sms:
            new_amount, _, _ = parse_message(
                re.sub(r'komis .* tjs', r'', re.sub(r'summa .* tjs', r'', sms))
                , header, bank, 1)
            print(re.sub(r'komis .* tjs', r'', re.sub(r'summa .* tjs', r'', sms)))

    if 'kzt' in sms:
        sms = re.sub(r'\*(\d{4})', lambda match: f"{match.group(0)}#", sms)
    if bank == "sber":
        pattern1 = r"перевод.*\b(от|из)\b"
        pattern2 = r'(?<!["])\bзачисление\b(?!["])'
        if not re.search(pattern1, sms) and not re.search(pattern2, sms):
            return None, None, None
        if 'мир' not in sms and 'счёт' not in sms and 'mir' not in sms and 'ecmc' not in sms and 'visa' not in sms:
            return None, None, None
        if 'баланс' not in sms:
            return None, None, None
    #if bank == "vtb":
    #    pattern = r'\bпоступление\b'
    #    if not re.search(pattern, sms):
    #        return None, None, None
    if bank == "ozon":
        if "перевод через" in sms:
            return None, None, None
    if bank == "yoomoney":
        if "деньги получит" in sms:
            return None, None, None
    if len(sms) > 350 or len(sms) < 15:
        return None, None, None
    if 'операция' in sms and 'uzs' in sms:
        return None, None, None
    if 'оплата' in sms and 'uzs' in sms:
        return None, None, None
    if 'отклон' in sms or 'отмен' in sms or 'выдач' in sms or 'наличн' in sms or 'снят' in sms or 'вывод' in sms:
        return None, None, None
    if 'запрос ' in sms or 'расход ' in sms:
        return None, None, None
    if ('c2c psb m f' in sms and bank != "vtb") or 'отмена' in sms or 'otmena' in sms or 'otpravlen perevod' in sms or 'карта пэй' in sms or ' код' in sms or 'списано' in sms or 'списан' in sms \
            or 'списание' in sms or 'spisanie' in sms or 'течение 24ч выберите' in sms or 'текстовое сообщение: ' in sms + header or 'снятие' in sms \
            or 'успешно завершен' in sms or (
            'перевод' in sms and (
            'исполнен' in sms or 'выполнен' in sms or 'не прошел' in sms)) or 'otklone' in sms or 'отклоне' in sms or 'покупка' in sms or 'выдача' in sms \
            or ('платеж' in sms and bank != "yoomoney") or ('перевод сбп' in sms and ' для ' in sms and ' в ' in sms) or 'код!' in sms \
            or ("перевод с карты" in sms and "mtsb" in sms) or 'nikomu ne soobshhajte' in sms \
            or 'spisano ' in sms or 'p2p mkb-mobile' in sms or 'q.tb.ru' in sms or 'запрашивает' in sms:
        return None, None, None
    ss = r"(кошелёк пополнен на\s+)(\d+[.,]?\d*)"
    sms = re.sub(ss, r"\1\2rub", sms)
    ss = r"(сумма:\s+)(\d+[.,]?\d*)"
    sms = re.sub(ss, r"\1\2rub", sms)
    pattern = r"отправитель:\s*\d+[*·]+\d+"
    sms = re.sub(pattern, "отправитель", sms)
    card_end = try_get_card_last_digits(sms)
    if card_end is not None:
        if bank == "solidarnost":
            if re.search(r'сч\s\d{5}\.\.\.\d{3}', sms):
                card_end = None
        if card_end is not None:
            sms = sms.replace(card_end, f"{card_end}|")

    if bank == "yoomoney":
        match = re.search(r'кошельке\s+(\d+)', sms)
        if match:
            wallet_number = match.group(1)
            last_4_digits = wallet_number[-4:]
            card_end = last_4_digits

    sms = sms.replace('postuplenie', '|postuplenie')
    if bank == "pochtabank":
        sms = sms.replace('popolnenie', '|popolnenie')
    sms = replace_inr(sms)
    sms = sms.replace(' сом', 'rub')
    sms = sms.replace('₸', 'rub')
    sms = sms.replace('azn', 'rub')
    sms = sms.replace('kgs', 'rub')
    sms = sms.replace('uzs', 'rub')
    sms = sms.replace('rur', 'rub')
    sms = sms.replace('tjs', 'rub')
    sms = sms.replace('rub', 'р ')
    sms = sms.replace('kzt', 'р ')
    sms = sms.replace(' ₽', 'р ')
    sms = sms.replace(' руб', 'р ')
    sms.replace(' rub', 'р ')
    sms = sms.replace('r', 'р')
    sms = sms.replace('p', 'р')
    sms = sms.replace('₽', 'р')
    sms = sms.replace('р ', 'rub')
    sms = sms.replace('р.', 'rub')
    sms = sms.replace(' р', 'rub')
    sms = sms.replace(' р', 'rub')
    sms = sms.replace('р\n', 'rub')
    sms_ = []

    for i in range(len(sms)):
        if sms[i] in 'абвгдеёжзиклмнопрстфхцчшщъыьэюя':
            sms_.append('a')
        else:
            sms_.append(sms[i])
    sms = ''.join(sms_)
    sms = sms.encode('ascii', 'ignore').decode('utf-8')
    sms = sms.replace('rub', 'р ')
    sms = '^' + sms + '^'
    numbers = []
    if 'менее' in sms or 'пополните' in sms:
        sms = ''
    for i in range(len(sms) - 1):
        if sms[i] == 'р' and sms[i + 1] not in 'абвгдеёжзиклмнопрстфхцчшщъыьэюяabcdefghijklmnopqrstuvwxyz':
            res = ''
            j = i - 1
            while str(sms[j]) in ' 0123456789.,':
                res += sms[j].replace(' ', '')
                j -= 1
            d = 0
            while len(res) + d > 0 and res[d - 1] not in '0123456789':
                d -= 1
            if d < 0:
                res = res[:d]
            if len(res) > 0:
                if len(res) >= 4 and res[0] not in '.,' and res[1] not in '.,' and res[2] not in '.,':
                    res = res.replace(',', '').replace('.', '')
                try:
                    numbers.append(res[::-1].replace(',', '.'))
                except TypeError:
                    pass
    if len(numbers) > 0 and numbers[0].count('.') > 1:
        numbers[0] = numbers[0].replace('.', '', numbers[0].count('.') - 1)
    return round(float(numbers[0]) * DECIMALS) if len(numbers) > 0 else None, card_end, new_amount


def get_bank_by_sender(msg: str, text: str, package_name: str | None) -> str | None:
    msg = str(msg).lower()
    if package_name is not None:
        package_name = str(package_name).lower()
    if package_name is not None and 'messag' not in package_name:
        check_bank = package_name
    else:
        check_bank = msg

    for bank in vars(Banks).values():
        if isinstance(bank, Bank):
            if any(package in check_bank for package in [p.lower() for p in bank.package_names]):
                return bank.name
    return None


if __name__ == '__main__':
    #print(parse_message("""Zachislenie\nSumma 50.00 TJS\nKomis 0.00 TJS\nZachislenie 50.00 TJS\nData 10:25 02.03.25\nOtpravitel ::992937480022\nKod 8856165539\nKarta 9762000163153504\nBalans 2 098.21 TJS""", "Eskh.Online"))
    #print(get_bank_by_sender('dc_next_bot', 'Zachislenie\nSumma 50.00 TJS\nKomis 0.00 TJS\nZachislenie 50.00 TJS\nData 10:25 02.03.25\nOtpravitel ::992937480022\nKod 8856165539\nKarta 9762000163153504\nBalans 2 098.21 TJS', 'com.google.android.apps.messaging'))
    print(parse_message("""СБП.Счет *0095 Перевод 300 р. от Максим Сергеевич Т,АО "ТБанк" """, "", Banks.DOLINSK.name))