import requests

headers = {
    'accept': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3N1ZWRfYXQiOjE3MDg3NjU5NDMsImV4cGlyZXNfYXQiOjE3MDk0NTcxNDMsInN1YiI6ImQ2MzM0ODY0LWZiNzMtNDc0OC04ZDMwLTRlMzlhMThkNmNiMyIsInJlZnJlc2giOmZhbHNlfQ.9w88eFTrveMe0tJrWpp-AxhbkajyGsiip5OQwSjCwH8',
    'Content-Type': 'application/json',
}

json_data1 = {
    'amount': 250000000,
}

json_data2 = {
    'amount': 100000000,
    'address': "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
}

for i in range(100):
    response1 = requests.post('http://127.0.0.1:8000/internal-transaction/create-inbound', headers=headers, json=json_data1)
    response2 = requests.post('http://127.0.0.1:8000/internal-transaction/create-outbound', headers=headers, json=json_data2)
    print(response1.text, response2.text)
