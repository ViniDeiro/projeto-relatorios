from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from dotenv import load_dotenv
import pandas as pd
import os
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

app = Flask(__name__)

load_dotenv()
dotenv_path = os.path.join(os.path.dirname(__file__), 'secretkey.env')
load_dotenv(dotenv_path)

app.secret_key = os.getenv('SECRET_KEY')

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def plot_to_html(df):
    try:
        plt.figure(figsize=(10, 6))  # Define o tamanho da figura
        ax = df.plot(kind='bar')  # Supondo que df tenha colunas numéricas apropriadas para uma plotagem de barras
        ax.set_title('Comparação de Valores e Custos')
        ax.set_xlabel('Categorias')
        ax.set_ylabel('Valores')
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        plt.close()
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf-8')
        return f'<img src="data:image/png;base64,{plot_url}" />'
    except Exception as e:
        return f'Erro ao gerar gráfico: {e}'

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Nenhum arquivo enviado!', 'danger')
        return redirect(url_for('home'))

    file = request.files['file']
    if file.filename == '':
        flash('Nenhum arquivo selecionado!', 'warning')
        return redirect(url_for('home'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        flash('Arquivo enviado com sucesso!', 'success')
        return redirect(url_for('process_file', filename=filename))

    flash('Formato de arquivo inválido. Apenas arquivos CSV e XLSX são permitidos.', 'danger')
    return redirect(url_for('home'))

@app.route('/process/<filename>')
def process_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(filepath)
        summary = df.describe(include=[np.number]).to_html(classes='table table-striped')
        plot_html = plot_to_html(df)  # Gerar gráfico
        return render_template('report.html', summary=summary, plot_html=plot_html, filename=filename)
    except Exception as e:
        flash(f'Ocorreu um erro ao processar o arquivo: {e}', 'danger')
        return redirect(url_for('home'))

@app.route('/download/<filename>')
def download_report(filename):
    try:
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # Verifica se o arquivo CSV original existe antes de tentar processá-lo.
        if not os.path.exists(input_path):
            flash('Arquivo original não encontrado.', 'danger')
            return redirect(url_for('home'))

        df = pd.read_csv(input_path)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'relatorio.xlsx')
        df.to_excel(output_path, index=False)
        
        # Verifica se o arquivo Excel foi criado com sucesso.
        if os.path.exists(output_path):
            return send_file(output_path, as_attachment=True, download_name='relatorio.xlsx')
        else:
            flash('Falha ao criar o arquivo Excel.', 'danger')
            return redirect(url_for('home'))
    except Exception as e:
        flash(f'Ocorreu um erro ao gerar o relatório: {e}', 'danger')
        return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)

