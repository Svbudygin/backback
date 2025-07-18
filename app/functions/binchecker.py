from app.core.constants import Banks
from app.core.session import async_session
from app.core import config, redis
import aiohttp
import json
import asyncio
from app.models import ExternalTransactionModel


ASSOCIATE_BANK_AND_BIN = {
    "SBERBANK OF RUSSIA": Banks.SBER.name,
    "VTB BANK PJSC": Banks.VTB.name,
    "PUBLIC JOINT STOCK COMPANY PROMSVYAZBANK": Banks.PSB.name,
    "JOINT STOCK COMPANY ALFA-BANK": Banks.ALFABANK.name,
    "VTB BANK (PUBLIC JOINT-STOCK COMPANY)": Banks.VTB.name,
    "TINKOFF BANK": Banks.TBANK.name,
    "PJSC MTS BANK": Banks.MTS.name,
    "JOINT STOCK COMPANY OTP BANK": Banks.OTPBANK.name,
    "ALIF BANK OJSC": Banks.ALIF.name,
    "AO RAIFFEISENBANK": Banks.RAIFFEISEN.name,
    "BANK SAINT PETERSBURG PUBLIC JOINT-STOCK COMPANY": "Банк Санкт-Петербург",
    "CJSC DUSHANBE CITY BANK": Banks.DUSHANBE.name,
    "CJSC INTERNATIONAL BANK OF TAJIKISTAN": "Международный банк Таджикистана",
    "CJSC SPITAMEN BANK": Banks.SPITAMEN.name,
    "CJSC THE FIRST MICROFINANCE BANK": "Первый микрофинансовый банк",
    "CLOSED JOINT STOCK COMPANY MICROCREDIT DEPOSIT ORGANIZATION HUMO": Banks.HUMO.name,
    "COMMERCIAL BANK KHLYNOV JOINT STOCK COMPANY": "Банк Хлынов",
    "COMMERCIAL BANK RENAISSANCE CREDIT (LIMITED LIABILITY COMPANY)": Banks.RENESSANS.name,
    "CREDIT BANK OF MOSCOW": Banks.MKB.name,
    "CREDIT BANK OF MOSCOW (MKB BANK)": Banks.MKB.name,
    "CREDIT UNION PAYMENT CENTER (LIMITED LIABILITY COMPANY)": 'РНКО "Платежный Центр"',
    "DALNEVOSTOCHNIY BANK": "Дальневосточный банк",
    "GAZPROMBANK (JOINT STOCK COMPANY)": Banks.GAZPROM.name,
    "GAZPROMBANK (JOINT-STOCK COMPANY)": Banks.GAZPROM.name,
    "JOINT STOCK COMMERCIAL BANK AK BARS": Banks.AKBB.name,
    "JOINT STOCK COMPANY RUSSIAN AGRICULTURAL BANK": Banks.RSHB.name,
    "JOINT STOCK COMPANY RUSSIAN AGRICULTURAL BANK JSC ROSSELKHOZBANK": Banks.RSHB.name,
    "JOINT-STOCK COMPANY RUSSIAN REGIONAL DEVELOPMENT BANK (RRDB)": "Всероссийский банк развития регионов",
    "JOINT STOCK COMPANY RUSSIAN STANDARD BANK": Banks.RUSSIANSTANDARDBANK.name,
    "JOINT-STOCK BANK ALMAZERGIENBANK": "Алмазэргиэнбанк",
    "JSCB FORA BANK": Banks.FORABANK.name,
    "JSCB NOVIKOMBANK": "Новиком Банк",
    "LLC ECOM BANK": "Еком Банк",
    "OJSC BANK ESKHATA": Banks.ESKHATA.name,
    "OJSC CB SOLIDARNOST": Banks.SOLIDARNOST.name,
    "OJSC ORIENBANK": "Ориёнбанк",
    "PJSC BANK URALSIB": Banks.URALSIB.name,
    "PJSC SOVCOMBANK": Banks.SOVCOMBANK.name,
    "PUBLIC JOINT-STOCK COMPANY SOVCOMBANK": Banks.SOVCOMBANK.name,
    "PJSC ROSBANK": Banks.ROSBANK.name,
    "PJSC METKOMBANK": "Меткомбанк",
    "PJSC CB CENTER-INVEST BANK": 'Банк "Центр-Инвест"',
    "PUBLIC JOINT STOCK COMPANY BANK URALSIB": Banks.URALSIB.name,
    "PUBLIC JOINT-STOCK COMPANY BANK OTKRITIE FINANCIAL CORPORATION": 'Банк "Финансовая Корпорация Открытие"',
    "RNKB BANK (PJSC)": Banks.RNKB.name,
    "YANDEX BANK": Banks.YANDEX.name,
    '"YOOMONEY, NBCO LLC"': Banks.YOOMONEY.name,
    "YOOMONEY, NBCO LLC": Banks.YOOMONEY.name,
    "AUTOTORGBANK LIMITED COMPANY": "Автоторгбанк",
    "BANK LEVOBEREZHNY PUBLIC JOINT-STOCK COMPANY": Banks.LEVOBEREZH.name,
    "BANK OF AFRICA": "Bank of Africa(BMCE Bank)",
    "BANK OF GUIYANG CO., LTD.": "Bank of Guiyang",
    "BANK ZENIT": Banks.ZENIT.name,
    "CB CENTER-INVEST": 'Банк "Центр-Инвест"',
    "CB MOLDOVA-AGROINDBANK, S.A.": "Moldova Agroindbank (MAIB)",
    "CJSC ACTIVBANK": "АктивБанк",
    "CJSC MICROCREDIT DEPOSIT-TAKING ORGANIZATION IMON INTERNATIONAL": "Микрокредитная депозитная организация Имон Интернешнл",
    "COMMERCIAL BANK EXPOBANK": "Экспобанк",
    "FISERV SOLUTIONS, LLC": "Fiserv",
    "INTERPROGRESSBANK (CJSC)": "Интерпрогрессбанк",
    "JOINT STOCK COMMERCIAL BANK AVANGARD": "Банк Авангард",
    "JOINT STOCK COMMERCIAL BANK MOLDINDCONBANK, S.A.": "Moldindconbank",
    "JOINT-STOCK COMMERCIAL BANK PRIMORYE": 'Банк "Приморье"',
    "JOINT STOCK COMPANY ASIAN-PACIFIC BANK": "Азиатско-Тихоокеанский банк",
    "JOINT STOCK COMPANY BANK DOM.RF": Banks.DOMRF.name,
    "JOINT STOCK COMPANY DATABANK": "Датабанк",
    "JOINT STOCK COMPANY SURGUTNEFTEGASBANK": "Сургутнефтегазбанк",
    "JSB TATSOTSBANK": "Татсоцбанк",
    "LLC NATIONAL STANDARD CB": "Банк Национальный стандарт",
    "LOCAL GOVERNMENT FEDERAL CREDIT UNION": "Local Government Federal Credit Union",
    "MUFG BANK LTD PRIMARY NY BRANCH": "MUFG Bank (NY Branch)",
    "OPEN JOINT-STOCK COMPANY JOINT-STOCK BANK ROSSIYA": Banks.ABR.name,
    "PNC BANK, NATIONAL ASSOCIATION": "PNC Bank",
    "POCHTA BANK": Banks.POCHTABANK.name,
    "PUBLIC JOINT-STOCK COMPANY THE URAL BANK FOR RECONSTRUCTION &": Banks.UBRR.name,
    "REAP TECHNOLOGIES, LTD.": "Reap technologies",
    "THE STATE SAVINGS BANK OF THE REPUBLIC OF TAJIKISTAN (AMONATBONK": Banks.AMONAT.name,
    "URAL BANK FOR RECONSTRUCTION AND DEVELOPMENT JSC": Banks.UBRR.name,
    "UZBEK INDUSTRIAL AND CONSTRUCTION BANK JSCB": "УЗПРОМСТРОЙБАНК",
    "Wildberries (Вайлдберриз Банк)": Banks.WILDBERRIES.name,
    "NOVIKOMBANK": "Новиком Банк",
    "LIMITED OZON BANK": Banks.OZON.name
}


async def set_bank(transaction_id: str, number: str):
    from app.functions.external_transaction import _find_external_transaction_by_id
    redis_key = f"bank_info:{number}"
    bank_info = await redis.rediss.get(redis_key)

    if bank_info:
        bank_name = bank_info.decode('utf-8')
    else:
        async with aiohttp.ClientSession() as session:
            headers = {
                'Content-Type': 'application/json',
                'x-rapidapi-host': 'bin-ip-checker.p.rapidapi.com',
                'x-rapidapi-key': config.settings.X_RAPIDAPI_KEY
            }
            async with session.post(
                url=f"https://bin-ip-checker.p.rapidapi.com/?bin={number}",
                headers=headers
            ) as response:
                if response.status != 200:
                    return
                data = await response.json()

        #print("[API RESPONSE]:")
        #print(json.dumps(data, indent=2, ensure_ascii=False))

        if not data.get("success") or "BIN" not in data or "issuer" not in data["BIN"]:
            return

        bank_name = data["BIN"]["issuer"].get("name", "UNKNOWN")
        if bank_name != "UNKNOWN":
            await redis.rediss.set(redis_key, bank_name)
    #print(bank_name)
    bank_name = ASSOCIATE_BANK_AND_BIN.get(bank_name[:64], bank_name[:64])
    #print(bank_name)
    if bank_name:
        async with async_session() as bd_session:
            transaction_model: ExternalTransactionModel = await _find_external_transaction_by_id(
                transaction_id=transaction_id,
                session=bd_session,
            )
            transaction_model.bank_detail_bank = bank_name
            await bd_session.commit()

async def main():
    await set_bank("1765b96b-4aa8-4eba-94e9-36483b5c25da", "427638")
    await redis.rediss.close()

if __name__ == "__main__":
    asyncio.run(main())
