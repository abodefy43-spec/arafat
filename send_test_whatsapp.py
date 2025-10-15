"""
send_test_whatsapp.py
Simple script to send a WhatsApp text message through AiSensy using environment variables.
Usage:
  export AISENSY_API_KEY='your_key'
  export AISENSY_API_URL='https://api.aisensy.com/v1/message'
  python3 send_test_whatsapp.py '+971501234567' 'Test message'
"""
import os
import sys
import requests

AISENSY_API_URL = os.getenv('AISENSY_API_URL', 'https://api.aisensy.com/v1/message')
AISENSY_API_KEY = os.getenv('AISENSY_API_KEY')


def main():
    if not AISENSY_API_KEY:
        print('ERROR: AISENSY_API_KEY is not set in environment')
        sys.exit(2)

    if len(sys.argv) < 3:
        print('Usage: python3 send_test_whatsapp.py <PHONE_NUMBER> "Message text"')
        sys.exit(2)

    number = sys.argv[1]
    message = sys.argv[2]

    headers = {
        'Authorization': f'Bearer {AISENSY_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'to': number,
        'type': 'text',
        'text': {'body': message}
    }

    try:
        resp = requests.post(AISENSY_API_URL, json=data, headers=headers, timeout=10)
        print('STATUS:', resp.status_code)
        print('BODY:', resp.text)
        if 200 <= resp.status_code < 300:
            print('Send successful')
            sys.exit(0)
        else:
            print('Send failed')
            sys.exit(1)
    except Exception as e:
        print('Exception while sending:', e)
        sys.exit(3)


if __name__ == '__main__':
    main()
"""
Simple test script to send a message through AiSensy using environment variables.
Run:

export AISENSY_API_KEY='your_key'
export AISENSY_API_URL='https://api.aisensy.com/v1/message'
python3 send_test_whatsapp.py +971XXXXXXXXX "Test message"

"""
import os
import sys
import requests

AISENSY_API_URL = os.getenv('AISENSY_API_URL', 'https://api.aisensy.com/v1/message')
AISENSY_API_KEY = os.getenv('AISENSY_API_KEY')

if __name__ == '__main__':
    if not AISENSY_API_KEY:
        print('ERROR: AISENSY_API_KEY is not set in environment')
        sys.exit(2)
    if len(sys.argv) < 3:
        print('Usage: python3 send_test_whatsapp.py <PHONE_NUMBER> "Message text"')
        sys.exit(2)

    number = sys.argv[1]
    message = sys.argv[2]

    headers = {
        'Authorization': f'Bearer {AISENSY_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'to': number,
        'type': 'text',
        'text': {'body': message}
    }

    try:
        resp = requests.post(AISENSY_API_URL, json=payload, headers=headers, timeout=10)
        print('STATUS:', resp.status_code)
        print('BODY:', resp.text)
        if 200 <= resp.status_code < 300:
            print('Send successful')
            sys.exit(0)
        else:
            print('Send failed')
            sys.exit(1)
    except Exception as e:
        print('Exception while sending:', e)
        sys.exit(3)
