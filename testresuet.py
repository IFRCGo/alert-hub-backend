import requests
import json

url = "http://127.0.0.1:8000/alerts/summary/"
csrf_token = 'your_csrf_token_here'

data = {
    'alert_ids': json.dumps([38540, 38541]),
    'csrfmiddlewaretoken': csrf_token
}

response = requests.post(url, data=data)
print("Status Code", response.status_code)
print("JSON Response ", response.text)