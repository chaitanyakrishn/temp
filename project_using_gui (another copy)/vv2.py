import os
import subprocess
from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app)

class SteganographyApp:
    def __init__(self):
        self.output_message = ""

    def run_encryption(self, input_audio, file_to_hide, password):
        try:
            subprocess.run(['sox', input_audio, 'output_audio.wav'], stderr=subprocess.DEVNULL, check=True)
            subprocess.run(['openssl', 'enc', '-aes-256-cbc', '-pbkdf2', '-in', file_to_hide,
                            '-out', 'encrypted_file.enc', '-k', password], stderr=subprocess.DEVNULL, check=True)
            subprocess.run(['steghide', 'embed', '-cf', 'output_audio.wav', '-ef', 'encrypted_file.enc',
                            '-sf', 'steghide_data', '-p', password], stderr=subprocess.DEVNULL, check=True)

            self.output_message = "Encryption successful."
        except subprocess.CalledProcessError as e:
            self.output_message = f"Error occurred during encryption: {e}"

    def run_decryption(self, input_audio, encrypted_file, password):
        extracted_encrypted_file = "extracted_encrypted_file.txt"

        try:
            subprocess.run(['steghide', 'extract', '-sf', 'steghide_data', '-xf', extracted_encrypted_file,
                            '-p', password], stderr=subprocess.PIPE, check=True)
            subprocess.run(['openssl', 'enc', '-d', '-aes-256-cbc', '-pbkdf2', '-in', extracted_encrypted_file,
                            '-out', 'decrypted_file.txt', '-k', password], stderr=subprocess.DEVNULL, check=True)

            self.output_message = "Decryption successful."
        except subprocess.CalledProcessError as e:
            self.output_message = f"Error occurred during decryption: {e}"
        finally:
            if os.path.exists(extracted_encrypted_file):
                os.remove(extracted_encrypted_file)

    def send_email_after_delay(self, subject, message, to_email, attachment_path_1, attachment_path_2):
        time.sleep(5)
        from_email = "cckkaa1236@gmail.com"  
        password = "jmnh aglp bwfr amrm"     

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        body = MIMEText(message)
        msg.attach(body)

        # Attach the first file
        with open(attachment_path_1, 'rb') as file_1:
            attachment_1 = MIMEApplication(file_1.read(), _subtype="txt")
            attachment_1.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path_1))
            msg.attach(attachment_1)

        # Attach the second file
        with open(attachment_path_2, 'rb') as file_2:
            attachment_2 = MIMEApplication(file_2.read(), _subtype="txt")
            attachment_2.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path_2))
            msg.attach(attachment_2)

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(from_email, password)
                server.sendmail(from_email, to_email, msg.as_string())
            self.output_message = "Email sent successfully."
        except smtplib.SMTPException as e:
            self.output_message = f"Error sending email: {e}"

# Create an instance of SteganographyApp
steganography_app = SteganographyApp()

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(".", filename)

@socketio.on('encrypt')
def encrypt(message):
    input_audio = message['input_audio']
    file_to_hide = message['file_to_hide']
    password = message['password']
    email = message['emailID']

    steganography_app.run_encryption(input_audio, file_to_hide, password)
    socketio.emit('output', {'message': steganography_app.output_message})

    # Send email after encryption
    subject = "Encryption Result"
    to_email = email  # Replace with the recipient's email address
    attachment_path_1 = '/home/chaitanya/Desktop/project_using_gui (another copy)/encrypted_file.enc'  
    attachment_path_2 = '/home/chaitanya/Desktop/project_using_gui (another copy)/output_audio.wav'  

    # Start a new thread to handle the email sending
    threading.Thread(target=steganography_app.send_email_after_delay, args=(subject, steganography_app.output_message, to_email, attachment_path_1, attachment_path_2)).start()

@socketio.on('decrypt')
def decrypt(message):
    input_audio = message['input_audio']
    encrypted_file = message['encrypted_file']
    password = message['password']
    email = message['emailID']

    steganography_app.run_decryption(input_audio, encrypted_file, password)
    socketio.emit('output', {'message': steganography_app.output_message})

    # Send email after decryption
    subject = "Decryption Result"
    to_email = email  # Replace with the recipient's email address
    attachment_path_1 = '/home/chaitanya/Desktop/project_using_gui (another copy)/decrypted_file.txt'  
    attachment_path_2 = '/home/chaitanya/Desktop/project_using_gui (another copy)/output_audio.wav'  

    # Start a new thread to handle the email sending
    threading.Thread(target=steganography_app.send_email_after_delay, args=(subject, steganography_app.output_message, to_email, attachment_path_1, attachment_path_2)).start()

if __name__ == "__main__":
    socketio.run(app, debug=True)

