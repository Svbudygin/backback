import requests

headers = {
    'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3N1ZWRfYXQiOjE3MDg3NjU5NDMsImV4cGlyZXNfYXQiOjE3MDk0NTcxNDMsInN1YiI6ImQ2MzM0ODY0LWZiNzMtNDc0OC04ZDMwLTRlMzlhMThkNmNiMyIsInJlZnJlc2giOmZhbHNlfQ.9w88eFTrveMe0tJrWpp-AxhbkajyGsiip5OQwSjCwH8',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'http://127.0.0.1:8000',
    'Referer': 'http://127.0.0.1:8000/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
    'accept': 'application/json',
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
}

json_data = [
    
    {
        'name': 'KIM IVAN DMITRIEVICH',
        'bank': 'SBER',
        'type': 'MASTERCARD',
        'currency': 'YOAN',
        'number': '2200284937449487',
        'is_active': True,
        'amount_limit': 1000000,
        'device_hash': '0xeiuye',
        'comment': 'string',
    },
    {
        'name': 'Alexandr Viktorovich Plokhikh',
        'bank': 'SBER',
        'type': 'MIR',
        'currency': 'EUR',
        'number': '21022849364789487',
        'is_active': False,
        'amount_limit': 10000,
        'device_hash': '0xeiuye',
        'comment': 'string',
    },
    {
        'name': 'Dao Yuong Peter',
        'bank': 'ALFABANK',
        'type': 'SBP',
        'currency': 'RUB',
        'number': '89111153748',
        'is_active': True,
        'amount_limit': 9800111,
        'device_hash': '0xeiuye',
        'comment': 'string',
    },
    {
        'name': 'Gorkunov Mikhail Petrovich',
        'bank': 'TINKOFF',
        'type': 'VISA',
        'currency': 'RUB',
        'number': '2200284937449487',
        'is_active': True,
        'amount_limit': 100000,
        'device_hash': '0xeiuye',
        'comment': 'string',
    }

]

for i in range(100):
    response = requests.post('http://127.0.0.1:8000/bank_detail/create', headers=headers, json=json_data[i % 4])

# Note: json_data will not be serialized by requests
# exactly as it was in the original request.
# data = '{\n  "name": "KIM IVAN DMITRIEVICH",\n  "bank": "SBER",\n  "type": "MIR",\n  "currency": "RUB",\n  "number": "2200284937449487",\n  "is_active": true,\n  "amount_limit": 1000000,\n  "device_hash": "0xeiuye",\n  "comment": "string"\n}'
# response = requests.post('http://127.0.0.1:8000/bank_detail/create', headers=headers, data=data)
