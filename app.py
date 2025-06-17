import os
from flask import Flask, render_template, request, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import PyPDF2
from docx import Document
import markdown2
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

# Login manager setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    reports = db.relationship('Report', backref='owner', lazy=True)

# Report model
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    evaluation = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.template_filter('nl2br')
def nl2br(value):
    if not value:
        return ""
    # Convert markdown to HTML
    html = markdown2.markdown(value, extras=["fenced-code-blocks", "tables"])
    return html

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def evaluate_report(text):
    client = genai.Client(api_key=os.getenv("API"))
    
    
    prompt = f"""Lütfen aşağıdaki TÜBİTAK 2204-A raporunu değerlendirin ve 100 üzerinden puanlayıp Türkçe cevap verin.
    Ayrıca raporun geliştirilmesi için öneriler sunun.
    
    Rapor:
    {text}
    
    Lütfen şu formatta yanıt verin:
    Puan: [0-100]
    Öneriler:
    - [öneri 1]
    - [öneri 2]
    - [öneri 3]
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction="Sen Tübitak 2204-A raporları değerlendiren ve sadece Türkçe cevap veren birisin."),
        contents=prompt
    )

    
    
    return response.text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Kullanıcı adı veya şifre hatalı.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Şifreler eşleşmiyor.', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten alınmış.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Bu e-posta adresi zaten kullanılıyor.', 'error')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Hesabınız başarıyla oluşturuldu! Giriş yapabilirsiniz.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        reports = Report.query.order_by(Report.id.desc()).all()
    else:
        reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.id.desc()).all()
    return render_template('dashboard.html', reports=reports)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('Dosya seçilmedi', 'error')
        return redirect(url_for('dashboard'))
    file = request.files['file']
    if file.filename == '':
        flash('Dosya seçilmedi', 'error')
        return redirect(url_for('dashboard'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # Extract text based on file type
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        else:
            text = extract_text_from_docx(file_path)
        # Evaluate the report
        evaluation = evaluate_report(text)
        # Save to DB
        report = Report(filename=filename, content=text, evaluation=evaluation, user_id=current_user.id)
        db.session.add(report)
        db.session.commit()
        os.remove(file_path)
        flash('Rapor başarıyla yüklendi ve değerlendirildi.', 'success')
        return redirect(url_for('dashboard'))
    flash('Geçersiz dosya formatı. Sadece PDF ve DOCX dosyaları kabul edilir.', 'error')
    return redirect(url_for('dashboard'))

@app.route('/report/<int:report_id>')
@login_required
def report_detail(report_id):
    report = Report.query.get_or_404(report_id)
    if not (current_user.is_admin or report.user_id == current_user.id):
        flash('Bu raporu görüntüleme yetkiniz yok.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('result.html', evaluation=report.evaluation, report=report)

if __name__ == '__main__':
    app.run(port=5000,debug=False) 