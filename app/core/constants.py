from enum import Enum, EnumMeta
from datetime import datetime
from typing import Optional, List
from app.enums import TransactionFinalStatusEnum

DECIMALS = 1_000_000
AUTO_CLOSE_EXTERNAL_TRANSACTIONS_S = 900
AUTO_CLOSE_INTERNAL_TRANSACTIONS_S = 60 * 60
BEFORE_CLOSE_OUT_EXTERNAL_TRANSACTIONS_S = 10 * 60
CACHE_TIMEOUT_SMALL_S = 9
MIN_TRUST_BALANCE = -1000_000_000
ONE_MILLION = 1000000
FUTURE_DATE = datetime(3000, 1, 1)

REPLICATION_LAG_S: int = 1

class Bank:
    def __init__(self, name: str, currency: str, display_name: Optional[str] = None, schema: Optional[str] = None, package_names: Optional[List[str]] = None, merchants_names: Optional[List[str]] = None):
        self.name = name
        self.display_name = display_name
        self.currency = currency
        self.schema = schema
        self.package_names = package_names or []
        self.merchants_names = merchants_names or []

class Banks:
    # RUB
    KAZAN = Bank(
        name="bank-kazani",
        display_name="Банк Казани",
        currency="RUB",
        schema="100000000191",
        package_names=["kazan", "казан"]
    )

    SBER = Bank(
        name="sber",
        display_name="Сбербанк",
        currency="RUB",
        schema="100000000111",
        package_names=["900", "sber", "sberbankonline", "sberbankmobile"],
        merchants_names=["SBER", "Сбербанк", "Сбер", "SBERBANK OF RUSSIA", "sber"]
    )

    ALFABANK = Bank(
        name="alfabank",
        display_name="Альфа Банк",
        currency="RUB",
        schema="100000000008",
        package_names=["ru.alfabank.mobile"],
        merchants_names=["Альфа Банк", "ALFA-BANK", "alfabank"]
    )

    ALFABUSINESS = Bank(
        name="alfabusiness",
        display_name="Альфа-Бизнес",
        currency="RUB",
        schema=None,
        package_names=["ru.alfabank.oavdo.amc"]
    )

    RAIFFEISEN = Bank(
        name="raiffeissen",
        display_name="Райффайзен Банк",
        currency="RUB",
        schema="100000000007",
        package_names=["raiffeisen", "райф"],
        merchants_names=["AO RAIFFEISENBANK", "Райффайзен Банк", "RAIFFEISENBANK"]
    )

    VTB = Bank(
        name="vtb",
        display_name="ВТБ",
        currency="RUB",
        schema="100000000005",
        package_names=["vtb", "втб"],
        merchants_names=["ВТБ", "vtb", "BANK VTB"]
    )

    URALSIB = Bank(
        name="uralsib",
        display_name="БАНК УРАЛСИБ",
        currency="RUB",
        schema="100000000026",
        package_names=["uralsib", "уралсиб"],
        merchants_names=["БАНК УРАЛСИБ"]
    )

    GAZPROM = Bank(
        name="gazprom",
        display_name="Газпромбанк",
        currency="RUB",
        schema="100000000001",
        package_names=["gazprom"],
        merchants_names=["Газпромбанк", "gazprom"]
    )

    RSHB = Bank(
        name="rshb",
        display_name="Россельхозбанк",
        currency="RUB",
        schema="100000000020",
        package_names=["ru.rshb.dbo", "rshb", "рсхб"],
        merchants_names=["Россельхозбанк"]
    )

    RENESSANS = Bank(
        name="renessans",
        display_name="Ренессанс Кредит",
        currency="RUB",
        schema="100000000032",
        package_names=["rencredit"],
        merchants_names=["Ренессанс Кредит"]
    )

    SOVCOMBANK = Bank(
        name="sovcombank",
        display_name="Совкомбанк",
        currency="RUB",
        schema="100000000013",
        package_names=["sovcombank", "совком"],
        merchants_names=["Совкомбанк", "SOVCOMBANK", "sovcombank"]
    )

    OTPBANK = Bank(
        name="otp-bank",
        display_name="ОТП Банк",
        currency="RUB",
        schema="100000000018",
        package_names=["otp", "отп"],
        merchants_names=["ОТП Банк", "otp-bank"]
    )

    RUSSIANSTANDARDBANK = Bank(
        name="russian-standard-bank",
        display_name="Банк Русский Стандарт",
        currency="RUB",
        schema="100000000014",
        package_names=[],
        merchants_names=["Банк Русский Стандарт"]
    )

    TBANK = Bank(
        name="t-bank",
        display_name="Т-банк",
        currency="RUB",
        schema="100000000004",
        package_names=["t-bank", "tinkoff"],
        merchants_names=["Т-банк", "Тинькофф", "t-bank", "TINKOFF BANK"]
    )

    CIFRABANK = Bank(
        name="cifra-bank",
        display_name="Цифра банк",
        currency="RUB",
        schema="100000000265",
        package_names=["cifra", "цифра"]
    )

    RNKB = Bank(
        name="rnkb",
        display_name="РНКБ Банк",
        currency="RUB",
        schema="100000000011",
        package_names=["rnkb", "rncb", "рнкб"],
        merchants_names=["РНКБ Банк"]
    )

    YANDEX = Bank(
        name="yandex-pay",
        display_name="Яндекс Банк",
        currency="RUB",
        schema="100000000150",
        package_names=["yandex-pay", "яндекс пэй", "com.yandex.bank"],
        merchants_names=["YANDEX BANK", "Яндекс Банк", "yandex-pay"]
    )

    SOLIDARNOST = Bank(
        name="solidarnost",
        display_name="КБ Солидарность",
        currency="RUB",
        schema="100000000121",
        package_names=["solidarnost", "солидарность"],
        merchants_names=["КБ Солидарность"]
    )

    PSB = Bank(
        name="psb",
        display_name="Промсвязьбанк",
        currency="RUB",
        schema="100000000010",
        package_names=["psb", "псб", "logo.com.mbanking"],
        merchants_names=["Промсвязьбанк", "PROMSVYAZBANK"]
    )

    ABR = Bank(
        name="abr",
        display_name="АБ РОССИЯ",
        currency="RUB",
        schema="100000000095",
        package_names=["abr", "абр", "ru.artsofte.russiafl"],
        merchants_names=["АБ РОССИЯ", "BANK ROSSIYA"]
    )

    CEB = Bank(
        name="credit-europe-bank",
        display_name="Кредит Европа Банк (Россия)",
        currency="RUB",
        schema="100000000027",
        package_names=["credit-europe-bank", "кредит европа банк"],
        merchants_names=["Кредит Европа Банк (Россия)"]
    )

    AKBB = Bank(
        name="ak-bars-bank",
        display_name="Ак Барс Банк",
        currency="RUB",
        schema="100000000006",
        package_names=["ak-bars-bank", "ак барс банк"]
    )

    VOLOG = Bank(
        name="vologzhanin",
        display_name="Банк Вологжанин",
        currency="RUB",
        schema=None,
        package_names=["vologzhanin", "вологжанин"],
        merchants_names=["Ак Барс Банк"]
    )

    UBRR = Bank(
        name="ubrr",
        display_name="УБРиР",
        currency="RUB",
        schema="100000000031",
        package_names=["ubrr", "убрр"],
        merchants_names=["УБРиР"]
    )

    SINARA = Bank(
        name="sinara",
        display_name="Банк Синара",
        currency="RUB",
        schema="100000000003",
        package_names=["синара", "sinara", "ru.skbbank.ib"],
        merchants_names=["Банк Синара"]
    )

    LEVOBEREZH = Bank(
        name="levoberezhnyy",
        display_name="Банк Левобережный",
        currency="RUB",
        schema="100000000052",
        package_names=["bl-online", "ru.ftc.faktura.nskbl"],
        merchants_names=["Банк Левобережный"]
    )

    ROSBANK = Bank(
        name="rosbank",
        display_name="Росбанк",
        currency="RUB",
        schema="100000000012",
        package_names=["rosbank"],
        merchants_names=["Росбанк"]
    )

    WILDBERRIES = Bank(
        name="wildberries",
        display_name="Wildberries (Вайлдберриз Банк)",
        currency="RUB",
        schema="100000000259",
        package_names=["wildberries"],
        merchants_names=["Wildberries (Вайлдберриз Банк)", "WBBANK"]
    )

    INGOBANK = Bank(
        name="ingobank",
        display_name="Ингосстрах Банк",
        currency="RUB",
        schema="100000000078",
        package_names=["ingobank"],
        merchants_names=["Ингосстрах Банк"]
    )

    ZENIT = Bank(
        name="zenit",
        display_name="Банк Зенит",
        currency="RUB",
        schema="100000000045",
        package_names=["bankzenit"],
        merchants_names=["Банк Зенит"]
    )

    MTS = Bank(
        name="mts-dengi",
        display_name="МТС Деньги",
        currency="RUB",
        schema="100000000017",
        package_names=["ru.lewis.dbo", "mts.dengi", "мтс деньги"],
        merchants_names=["МТС Деньги", "mts-dengi"]
    )

    DOMRF = Bank(
        name="dom-rf",
        display_name="ДОМ.РФ",
        currency="RUB",
        schema="100000000082",
        package_names=["dom.rf", "com.bank.domrf.v2"],
        merchants_names=["ДОМ.РФ"]
    )

    RESOBANK = Bank(
        name="resobank",
        display_name="Банк РЕСО Кредит",
        currency="RUB",
        schema="100000000187",
        package_names=["resobank"]
    )

    FORABANK = Bank(
        name="forabank",
        display_name="ФОРА-БАНК",
        currency="RUB",
        schema="100000000217",
        package_names=["fora-bank"],
        merchants_names=["ФОРА-БАНК", "forabank"]
    )

    TKB = Bank(
        name="tkb",
        display_name="ТРАНСКАПИТАЛБАНК",
        currency="RUB",
        schema=None,
        package_names=["tkb"]
    )

    SVOIBANK = Bank(
        name="svoibank",
        display_name="Свой Банк",
        currency="RUB",
        schema=None,
        package_names=["svoibank"]
    )

    BCS = Bank(
        name="bcs",
        display_name="БКС Банк",
        currency="RUB",
        schema=None,
        package_names=["ru.bcs.bcsbank"]
    )

    MKB = Bank(
        name="mkb",
        display_name="МКБ (Московский кредитный банк)",
        currency="RUB",
        schema=None,
        package_names=["ru.mkb.mobile"],
        merchants_names=["МКБ (Московский кредитный банк)"]
    )

    OZON = Bank(
        name="ozon",
        display_name="Озон Банк",
        currency="RUB",
        schema="100000000273",
        package_names=["ozon", "LIMITED OZON BANK"]
    )

    POCHTABANK = Bank(
        name="pochtabank",
        display_name="Почта банк",
        currency="RUB",
        schema=None,
        package_names=["prometheus", "pochtabank"]
    )

    CREDITURALBANK = Bank(
        name="credituralbank",
        display_name="Кредит Урал Банк",
        currency="RUB",
        schema=None,
        package_names=["credituralbank"]
    )

    HMBANK = Bank(
        name="hmbank",
        display_name="Хакасский Муниципальный Банк",
        currency="RUB",
        schema=None,
        package_names=["hmbinfo"]
    )

    YOOMONEY = Bank(
        name="yoomoney",
        display_name="ЮМани",
        currency="RUB",
        schema=None,
        package_names=["ru.yoo.money", "yoomoney"]
    )

    BANKSPB = Bank(
        name="bankspb",
        display_name="Банк Санкт-Петербург",
        currency="RUB",
        schema=None,
        package_names=["bankspb"]
    )

    DOLINSK = Bank(
        name="dolinsk",
        display_name="Долинск Банк",
        currency="RUB",
        schema=None,
        package_names=["ru.ftc.faktura.dolinsk"]
    )

    OPTIMA2 = Bank(
        name="optima",
        display_name="Оптима Банк",
        currency="RUB",
        schema=None,
        package_names=["optimabank.optima24"]
    )

    DUSHANBE2 = Bank(
        name="dushanbe",
        display_name="Душанбе Сити",
        currency="RUB",
        schema="10002",
        package_names=["dc_next_bot"],
        merchants_names=["Душанбе Сити"]
    )

    BAKAI2 = Bank(
        name="bakai",
        display_name=None,
        currency="RUB",
        schema=None,
        package_names=[]
    )

    DEMIR2 = Bank(
        name="demir",
        display_name="Демир",
        currency="RUB",
        schema=None,
        package_names=['demir']
    )

    MBANK2 = Bank(
        name="mbank",
        display_name=None,
        currency="RUB",
        schema=None,
        package_names=["com.maanavan.mb_kyrgyzstan"]
    )

    KOMPANION2 = Bank(
        name="kompanion",
        display_name="Банк Компаньон",
        currency="RUB",
        schema=None,
        package_names=["kompanion"]
    )

    # AZN
    EMANAT = Bank(
        name="emanat",
        display_name=None,
        currency="AZN",
        schema=None,
        package_names=[]
    )

    KAPITAL = Bank(
        name="kapital",
        display_name=None,
        currency="AZN",
        schema=None,
        package_names=["kapital", "kapitalbank"]
    )

    LEOBANK = Bank(
        name="leobank",
        display_name=None,
        currency="AZN",
        schema=None,
        package_names=[]
    )

    M10 = Bank(
        name="m10",
        display_name=None,
        currency="AZN",
        schema=None,
        package_names=["m10"]
    )

    # KGS
    BAKAI = Bank(
        name="bakai",
        display_name=None,
        currency="KGS",
        schema=None,
        package_names=[]
    )

    DEMIR = Bank(
        name="demir",
        display_name="Демир",
        currency="KGS",
        schema=None,
        package_names=['demir']
    )

    MBANK = Bank(
        name="mbank",
        display_name=None,
        currency="KGS",
        schema=None,
        package_names=["com.maanavan.mb_kyrgyzstan"]
    )

    OPTIMA = Bank(
        name="optima",
        display_name="Оптима Банк",
        currency="KGS",
        schema=None,
        package_names=["optimabank.optima24"]
    )

    KOMPANION = Bank(
        name="kompanion",
        display_name="Банк Компаньон",
        currency="KGS",
        schema=None,
        package_names=["kompanion"]
    )

    # UZS
    ANORBANK = Bank(
        name="anorbank",
        display_name=None,
        currency="UZS",
        schema=None,
        package_names=[]
    )

    HUMO = Bank(
        name="humo",
        display_name=None,
        currency="UZS",
        schema=None,
        package_names=["humocardbot"],
        merchants_names=["Humo"]
    )

    IPAKYULI = Bank(
        name="ipakyuli",
        display_name=None,
        currency="UZS",
        schema=None,
        package_names=[]
    )

    UZKARD = Bank(
        name="uzcard",
        display_name=None,
        currency="UZS",
        schema=None,
        package_names=["cardxabarbot"]
    )

    PAYME = Bank(
        name="payme",
        display_name=None,
        currency="UZS",
        schema=None,
        package_names=[]
    )

    CLICKUP = Bank(
        name="click-up",
        display_name=None,
        currency="UZS",
        schema=None,
        package_names=[]
    )

    # KZT
    BCC = Bank(
        name="bcc",
        display_name=None,
        currency="KZT",
        schema=None,
        package_names=[]
    )

    BEREKE = Bank(
        name="bereke",
        display_name=None,
        currency="KZT",
        schema=None,
        package_names=["berekebank"]
    )

    FREEDOM = Bank(
        name="freedom",
        display_name=None,
        currency="KZT",
        schema=None,
        package_names=[]
    )

    KASPI = Bank(
        name="kaspi",
        display_name=None,
        currency="KZT",
        schema=None,
        package_names=["kz.kaspi.mobile"]
    )

    FORTE = Bank(
        name="forte",
        display_name=None,
        currency="KZT",
        schema=None,
        package_names=[]
    )

    JUSAN = Bank(
        name="jusan",
        display_name=None,
        currency="KZT",
        schema=None,
        package_names=[]
    )

    HALK = Bank(
        name="halk",
        display_name=None,
        currency="KZT",
        schema=None,
        package_names=[]
    )

    HOME = Bank(
        name="home",
        display_name=None,
        currency="KZT",
        schema=None,
        package_names=["kz.kkb.homebank"]
    )

    # TJS
    ALIF = Bank(
        name="alif",
        display_name="Алиф Банк",
        currency="TJS",
        schema=None,
        package_names=["tj.alif.mobi", 'alif'],
        merchants_names=["ALIF BANK OJSC", "Алиф Банк"]
    )

    AMONAT = Bank(
        name="amonat",
        display_name="Амонат Банк",
        currency="TJS",
        schema=None,
        package_names=['amonat']
    )

    DUSHANBE = Bank(
        name="dushanbe",
        display_name="Душанбе Сити",
        currency="TJS",
        schema="10002",
        package_names=["dc_next_bot"],
        merchants_names=["Душанбе Сити"]
    )

    ESKHATA = Bank(
        name="eskhata",
        display_name="Банк Эсхата",
        currency="TJS",
        schema=None,
        package_names=['eskhata', 'Eskh.Online'],
        merchants_names=["Банк Эсхата"]
    )

    SPITAMEN = Bank(
        name="spitamen",
        display_name="Спитамен",
        currency="TJS",
        schema=None,
        package_names=['spitamen'],
        merchants_names=["Спитамен"]
    )

    # TRY
    ISBANK = Bank(
        name="isbank",
        display_name=None,
        currency="TRY",
        schema=None,
        package_names=[]
    )

    VAKIFBANK = Bank(
        name="vakifbank",
        display_name=None,
        currency="TRY",
        schema=None,
        package_names=[]
    )

    AKBANK = Bank(
        name="akbank",
        display_name=None,
        currency="TRY",
        schema=None,
        package_names=[]
    )

    YAPIKREDI = Bank(
        name="yapi-kredi",
        display_name=None,
        currency="TRY",
        schema=None,
        package_names=[]
    )

    ZIRAATBANK = Bank(
        name="ziraat-bank",
        display_name=None,
        currency="TRY",
        schema=None,
        package_names=[]
    )

    TEBBANK = Bank(
        name="teb-bank",
        display_name=None,
        currency="TRY",
        schema=None,
        package_names=[]
    )

    HALKBANK = Bank(
        name="halkbank",
        display_name=None,
        currency="TRY",
        schema=None,
        package_names=[]
    )

    KUVEYTTURK = Bank(
        name="kuveyt-turk",
        display_name=None,
        currency="TRY",
        schema=None,
        package_names=[]
    )

    VAKIFKATILIM = Bank(
        name="vakif-katilim",
        display_name=None,
        currency="TRY",
        schema=None,
        package_names=[]
    )

    ALBARAKA = Bank(
        name="albaraka",
        display_name=None,
        currency="TRY",
        schema=None,
        package_names=[]
    )

    TURKIYEFINANS = Bank(
        name="turkiye-finans",
        display_name=None,
        currency="TRY",
        schema=None,
        package_names=[]
    )

    ING = Bank(
        name="ing",
        display_name=None,
        currency="TRY",
        schema=None,
        package_names=[]
    )

    PAPARA = Bank(
        name="papara",
        display_name=None,
        currency="TRY",
        schema=None,
        package_names=[]
    )

    # INR

    #ARS
    CLAROPAY = Bank(
        name="claropay",
        display_name="Claro Pay",
        currency="ARS",
        schema=None,
        package_names=[]
    )

    RIPIO = Bank(
        name="ripio",
        display_name="Ripio",
        currency="ARS",
        schema=None,
        package_names=[]
    )

    LEMONCASH = Bank(
        name="lemoncash",
        display_name="Lemon Cash",
        currency="ARS",
        schema=None,
        package_names=[]
    )

    BRUBANK = Bank(
        name="brubank",
        display_name="Brubank",
        currency="ARS",
        schema=None,
        package_names=[]
    )


class Currency:
    RUB = "RUB"
    AZN = "AZN"
    USD = "USD"
    EUR = "EUR"
    KZT = "KZT"
    UZS = "UZS"
    KGS = 'KGS'
    ARS = "ARS"


class Type:
    UPI = "upi"
    IBAN = "iban"
    PHONE = "phone"
    CARD = "card"
    ACCOUNT = "account"
    CB_PHONE = "cross-border-phone"
    CVU = "cvu"
    CBU = "cbu"

class PaymentSystem:
    VISA = 'visa'
    MASTERCARD = 'mastercard'
    MIR = 'mir'
    KORTIMILLI = 'kortimilli'
    ELCART = 'elcart'
    PAYME = 'payme'


def create_associate_bank_dict():
    associate_bank = {}
    for bank in vars(Banks).values():
        if isinstance(bank, Bank) and bank.display_name is not None:
            associate_bank[bank.name] = bank.display_name
    return associate_bank


def create_associate_merchant_bank_dict():
    associate_merchant_bank = {}
    for bank in vars(Banks).values():
        if isinstance(bank, Bank) and bank.merchants_names is not None:
            for merch_name in bank.merchants_names:
                associate_merchant_bank[merch_name] = bank.name
    return associate_merchant_bank

def create_bank_schema_dict():
    bank_schema = {}
    for bank in vars(Banks).values():
        if isinstance(bank, Bank) and bank.schema is not None:
            bank_schema[bank.name] = bank.schema
    return bank_schema

ASSOCIATE_BANK = create_associate_bank_dict()
ASSOCIATE_MERCHANT_BANK = create_associate_merchant_bank_dict()
BANK_SCHEMAS = create_bank_schema_dict()

def get_list_banks(currency: str):
    return [bank.name for bank in vars(Banks).values() if isinstance(bank, Bank) and bank.currency == currency]


SUPPORT_OUTBOUND_CATEGORIES = [
    [
        {
            "title": "Pending",
            "code": "pending"
        },
        {
            "title": "In process",
            "code": "processing"
        },
        {
            "title": "Accept",
            "code": "accept"
        },
        {
            "title": "Close",
            "code": "close"
        },
        {
            "title": "All",
            "code": "all"
        }
    ]
]

TEAM_OUTBOUND_CATEGORIES = [
    [
        {
            "title": "Ожидание",
            "code": "pending"
        },
        {
            "title": "В обработке",
            "code": "processing"
        },
        {
            "title": "Успешно",
            "code": "accept"
        },
        {
            "title": "Отменено",
            "code": "close"
        },
        {
            "title": "Все",
            "code": "all"
        }
    ]
]

TRANSACTION_FINAL_STATUS_TITLES = {
    TransactionFinalStatusEnum.AUTO: {
        "en": "Auto",
        "ru": "Auto"
    },
    TransactionFinalStatusEnum.ACCEPT: {
        "en": "Accept",
        "ru": "Accept"
    },
    TransactionFinalStatusEnum.APPEAL: {
        "en": "Appeal",
        "ru": "Appeal"
    },
    TransactionFinalStatusEnum.RECALC: {
        "en": "Recalc",
        "ru": "Recalc"
    },
    TransactionFinalStatusEnum.TIMEOUT: {
        "en": "Timeout",
        "ru": "Timeout"
    },
    TransactionFinalStatusEnum.CANCEL: {
        "en": "Cancel",
        "ru": "Cancel"
    }
}


USUAL_TYPES_INFO = {
    Type.UPI: {"title": "UPI ID", "code": Type.UPI},
    Type.IBAN: {"title": "IBAN", "code": Type.IBAN},
    Type.PHONE: {"title": "Телефон", "code": Type.PHONE},
    Type.CARD: {"title": "Карта", "code": Type.CARD},
    Type.ACCOUNT: {"title": "Счет", "code": Type.ACCOUNT},
    Type.CB_PHONE: {"title": "Трансгр. телефон", "code": Type.CB_PHONE},
    Type.CVU: {"title": "CVU", "code": Type.CVU},
    Type.CBU: {"title": "CBU", "code": Type.CBU}
}


SUPPORT_TYPES_INFO = {
    Type.UPI: {"title": "UPI ID", "code": Type.UPI},
    Type.IBAN: {"title": "IBAN", "code": Type.IBAN},
    Type.PHONE: {"title": "Phone", "code": Type.PHONE},
    Type.CARD: {"title": "Card", "code": Type.CARD},
    Type.ACCOUNT: {"title": "Account", "code": Type.ACCOUNT},
    Type.CB_PHONE: {"title": "CB Phone", "code": Type.CB_PHONE},
    Type.CVU: {"title": "CVU", "code": Type.CVU},
    Type.CBU: {"title": "CBU", "code": Type.CBU}
}


DETAILS_INFO = {
    'RUB': {
        'banks': get_list_banks("RUB"),
        'types': [
            Type.CARD,
            Type.PHONE,
            Type.ACCOUNT,
            Type.CB_PHONE
        ],
        'payment_systems': []
    },
    'AZN': {
        'banks': get_list_banks("AZN"),
        'types': [
            Type.CARD,
            Type.PHONE
        ],
        'payment_systems': []
    },
    'KGS': {
        'banks': get_list_banks("KGS"),
        'types': [
            Type.CARD,
            Type.PHONE
        ],
        'payment_systems': [
            PaymentSystem.VISA,
            PaymentSystem.ELCART,
            PaymentSystem.MASTERCARD
        ]
    },
    'UZS': {
        'banks': get_list_banks("UZS"),
        'types': [
            Type.CARD,
            Type.PHONE
        ],
        'payment_systems': [
            PaymentSystem.PAYME
        ]
    },
    'KZT': {
        'banks': get_list_banks("KZT"),
        'types': [
            Type.CARD,
            Type.PHONE
        ],
        'payment_systems': []
    },
    'TJS': {
        'banks': get_list_banks("TJS"),
        'types': [
            Type.CARD,
            Type.PHONE
        ],
        'payment_systems': [
            PaymentSystem.VISA,
            PaymentSystem.KORTIMILLI,
            PaymentSystem.MASTERCARD
        ]
    },
    'TRY': {
        'banks': get_list_banks("TRY"),
        'types': [
            Type.IBAN,
            Type.CARD,
            Type.PHONE
        ],
        'payment_systems': []
    },
    'INR': {
        'banks': get_list_banks("INR"),
        'types': [
            Type.UPI
        ],
        'payment_systems': []
    },
    'ARS': {
        'banks': get_list_banks("ARS"),
        'types': [
            Type.CBU,
            Type.CVU
        ],
        'payment_systems': []
    }
}


class Role:
    ROOT = "root"
    AGENT = "agent"
    ADMIN = "admin"
    TEAM = "team"
    MERCHANT = "merchant"
    SUPPORT = "support"
    C_WORKER = "c_worker"
    B_WORKER = "b_worker"
    TV_WORKER = "tv_worker"
    TC_WORKER = "tc_worker"
    TG_APPEAL_WORKER = "tg_appeal_worker"


class EconomicModel:
    FIAT = "fiat"
    FIAT_CRYPTO_PROFIT = "fiat_crypto_profit"
    CRYPTO = "crypto"
    CRYPTO_FIAT_PROFIT = "crypto_fiat_profit"


class Limit:
    MAX_OUTBOUND_PENDING_PER_TOKEN = 10
    MESSAGE_BACK_TIME_S = 60 * 60
    INTERNAL_INBOUND_BACK_TIME_S = 80 * 60
    MAX_ITEMS_PER_QUERY = 2 ** 8
    MAX_STRING_LENGTH_SMALL = 2 ** 6
    MAX_STRING_LENGTH_BIG = 2 ** 10
    MAX_INT = 2 ** 63 - 1
    MIN_INT = -(2 ** 63) + 1
    MIN_INTERNAL_OUTBOUND_AMOUNT = 1 * DECIMALS
    MAX_TIMESTAMP = 20419782716
    MIN_TIMESTAMP = 0
    FRAUD_MAX_PENDING = 8
    MIN_OFFSET_ID = 0
    MIN_PRIORITY = -94608000000
    STANDART_LIMIT = 50


class Direction:
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CacheNamespace:
    LIST = "list"


class Status:
    OPEN = "open"
    PENDING = "pending"
    ACCEPT = "accept"
    CLOSE = "close"
    PROCESSING = "processing"


class StatusEnum(str, Enum):
    OPEN = "open"
    PENDING = "pending"
    ACCEPT = "accept"
    CLOSE = "close"
    PROCESSING = "processing"


class BalanceStatsPeriodName(str, Enum):
    hour = "hour"
    last_hour = "last_hour"
    day = "day"
    last_day = "last_day"
    all_time = "all_time"


class TrafficStatsPeriodName(str, Enum):
    hour = "hour"
    day = "24h"
    minutes = "15 min"


class ReasonName(str, Enum):
    wrong_details = "wrong_details"
    high_risk_details = "high_risk_details"


translations_reason = {
    "RUB": {
        "wrong_details": "Неверные данные",
        "high_risk_details": "Красный риск"
    },
    "support": {
        "wrong_details": "Wrong detail",
        "high_risk_details": "High risk detail"
    }
}


class Params:
    AUTO_CLOSE_TRANSACTIONS_S = 30 * 60
    AUTO_GET_BACK_TRANSACTIONS_S = 60 * 60 * 4
    AUTO_CLOSE_TRANSACTIONS_INTERVAL_S = 1 * 60
    CHECK_DISABLED_DEVICES_INTERVAL_S = 3 * 60
    AUTO_GET_BACK_TRANSACTIONS_INTERVAL_S = 5 * 60
    DISABLED_DEVICE_PING_DELAY_S = 10 * 60
    AUTO_UNBIND_VIP_NO_TRX_S = 30 * 60
    REMOVE_TRANSFER_ASSOCIATION_INTERVAL_S = 3 * 60
    AUTO_ACCEPT_APPEALS_INTERVAL_S = 3 * 60
    AUTO_CLOSE_PAYOUTS_INTERVAL_S = 60
    DISABLED_REQS_AUTO_CONFIRM_NOT_WORKING_INTERVAL_S = 30
    


class MetaEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True


class BaseEnum(Enum, metaclass=MetaEnum):
    pass


def get_class_fields(cls):
    return [attr for key, attr in cls.__dict__.items()
            if not key.startswith('__')]
