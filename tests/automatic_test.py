import pytest
from anyio import value

from app.functions.device import *

dict_for_test_amount_card_RUB = {
    (
        "Karta MIR *0017. Postuplenie na schet: +20.00 RUB SBP credit operation 17.08.2024 14:52. Dostupno: -72.62 RUB. rsb.ru/balance Russian Standard Bank",
        ""): [20000000, "0017"],
    (
        "Karta MIR *0017.Spisanie: -10.00 RUB SBP debet operations 17.08.2024 15:03. Dostupno: 297.38 RUB. rsb.ru/balance Russian Standard Bank",
        ""): [None, None],
    ("Karta MIR *0017. Postuplenie na schet: +20.00 RUB SBOL 17.08.2024 15:05. Dostupno: 317.38 RUB. rsb.ru/ balance",
     ""): [20000000, "0017"],
    ("Пополнение, счет RUB. 1 RUB. Кирилл К. Доступно 53 RUB", ""): [1000000, None],
    ("Перевод на 10 ₽, счет RUB. Кирилл К. Баланс 23 ₽", ""): [None, None],
    (
        "19.08 15:19. Карта *5676 зачисление на сумму 1000р. OTP_FPS. Доступно 12425.14р.       Карта *5676 зачисление на сумму 3000р. ",
        ""): [1000000000, "5676"],
    ("Карта *6690 списание -301р. Доступно 63.52р. otpbank.ru/tr", ""): [None, None],
    (
        "2024.08.19 19:03:36. Счет ****. Перевод через СБП на сумму 15000.00RUB. в АО \"АЛЬФА-БАНК\" успешно завершен. Получатель: Никита Дмитриевич Д.",
        ""): [None, None],
    (
        "СБП. Получен перевод 02.09.2024 22:48 (мск). Счет 0239. Зачислено 10.00 RUB. от Иван Сергеевич Д Баланс 52.30 RUB 0.00 USD 0.00 EUR",
        ""): [10000000, "0239"],
    ("Карта 4007:02.09.2024 22:48, пополнение 10.00 RUB, SBOL RUS VISA DIRECT. Баланс 62.30 RUB 0.00 USD 0.00 EUR",
     ""): [10000000, "4007"],
    (
        "СБП. Исполнен перевод 02.09.2024 22:53 (мск). Счет 0239. Списано 10.00 RUB. Иван Сергеевич Д. Платеж СБП N В4246195302140040000110011331101. Без налога (НДС). Баланс 52.30 RUB 0.00 USD 0.00 EUR",
        ""): [None, None],
    ("Spisanie po perevodu s karty na kartu karta: 7522 summa: 101.50 RUR balans: 8.50 RUR. MP2P4OUT 24-09-13 11:42:30",
     ""): [None, None],
    ("Перевод по СБП 10.00 RUR с карты/счёта 7522 в Т-Банк 13.09.2024 Код: 449221", ""): [None, None],
    (
        "Зачисление 10.00 руб. по переводу с карты на карту в 24-09-13 00:07:16. Карта *7522. Tinkoff Card2Card. Баланс 30.00 руб.",
        ""): [10000000, "7522"],
    (
        "Schet *0383 Zachislen perevod SBP summa 10.00 RUR ot Maksim Sergeevich B tel +79870642848 iz Tinkoff Bank 24-09-13 11:37:52 balans: 10.00 RUR. Operatsiya zavershena uspeshno",
        ""): [10000000, "0383"],
    ("Карта Пэй Перевод 10.00 RUB. Александр Михайлович С. 17.09.2024 15:04. Доступно 10.00 RUB", "Карта Пэй"): [None,
                                                                                                                 None],
    ("Входящий перевод Пополнение на 10.00 RUB. 17.09.2024 15:01. Доступно 20.00 RUB", "Входящий перевод"): [10000000,
                                                                                                             None],
    ("Входящий перевод Пополнение на 10.00 RUB. Александр Михайлович С. 17.09.2024 14:53. Доступно 10.00 RUB",
     "Входящий перевод"): [10000000, None],
    ("СБП Зачислено 3000.0 р из Сбербанк, Булат Рашидович У", ""): [3000000000, None],
    ("Солидарность СБП Списано 55.0 р в Сбербанк,Булат Рашидович У", "Солидарность"): [None, None],
    ("ABR Direct МИР5695 Пополнение 10p", "ABR Direct"): [10000000, "5695"],
    ("ABR Direct 18:33 04.10.2024 Зачисление СБП 10р на сч*0707 от Кирилл Сергеевич Л. из Т-Банк Доступно 20р",
     "ABR Direct"): [10000000, "0707"],
    ("Перевод на карту 33,00 P Перевод на карту 2200-XXXX-XXXX-3474 Исполнен Доступно 27.0 p 19:12 04.10.2024",
     "ABR Direct"): [None, None],
    ("Перевод СБП 10,00 Р Кирилл Сергеевич Л исполнен Доступно 10.0 p 19:00 04.10.2024", "ABR Direct"): [None, None],
    ("Karta *8944. 04.10.24 20:29. Postuplenie 1008.00 RUB. Tinkoff Card2Card. Balans 8937.00 RUB", "Уралсиб"): [
        1008000000, '8944']
}

dict_for_test_amount_card_UZS = {

}

dict_for_test_amount_card_AZN = {

}

dict_for_test_amount_card_KZT = {

}

dict_for_test_amount_card_TJS = {

}

dict_for_test_amount_card_KGS = {

}


def raize_exceptions():
    raise exceptions.AutomaticTestError()


def test_automatic_RUB_test():
    for key, value in dict_for_test_amount_card_RUB.items():
        message = key[0]
        header_from_message = key[1]
        amount, card, _ = parse_message(sms=message, header=header_from_message)
        assert amount == value[0], raize_exceptions()
        assert card == value[1], raize_exceptions()


def test_automatic_UZS_test():
    for key, value in dict_for_test_amount_card_UZS.items():
        message = key[0]
        header_from_message = key[1]
        amount, card, _ = parse_message(sms=message, header=header_from_message)
        assert amount == value[0], raize_exceptions()
        assert card == value[1], raize_exceptions()


def test_automatic_AZN_test():
    for key, value in dict_for_test_amount_card_AZN.items():
        message = key[0]
        header_from_message = key[1]
        amount, card, _ = parse_message(sms=message, header=header_from_message)
        assert amount == value[0], raize_exceptions()
        assert card == value[1], raize_exceptions()


def test_automatic_TJS_test():
    for key, value in dict_for_test_amount_card_TJS.items():
        message = key[0]
        header_from_message = key[1]
        amount, card, _ = parse_message(sms=message, header=header_from_message)
        assert amount == value[0], raize_exceptions()
        assert card == value[1], raize_exceptions()


def test_automatic_KGS_test():
    for key, value in dict_for_test_amount_card_KGS.items():
        message = key[0]
        header_from_message = key[1]
        amount, card, _ = parse_message(sms=message, header=header_from_message)
        assert amount == value[0], raize_exceptions()
        assert card == value[1], raize_exceptions()
