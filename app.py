from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import subprocess
import sys
import os
import threading

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key_here'

# Функция для выполнения кода с таймаутом
def run_code_with_timeout(code, input_data, timeout=2):
    def target():
        try:
            # Создаем временный файл с кодом
            with open('temp_code.py', 'w', encoding='utf-8') as f:
                f.write(code)

            # Выполняем код
            result = subprocess.run(
                [sys.executable, 'temp_code.py'],
                input=input_data,
                text=True,
                capture_output=True,
                timeout=timeout,
                encoding='utf-8',  # Указываем кодировку
                errors='replace'   # Заменяем некорректные символы
            )
            output = result.stdout
            error = result.stderr
        except subprocess.TimeoutExpired:
            output = ""
            error = "Execution timed out"
        except Exception as e:
            output = ""
            error = str(e)
        finally:
            # Удаляем временный файл
            if os.path.exists('temp_code.py'):
                os.remove('temp_code.py')

        return output, error

    # Создаем поток для выполнения кода
    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout=timeout)  # Ждем завершения потока с таймаутом

    if thread.is_alive():
        # Если поток все еще выполняется после таймаута, завершаем его
        try:
            subprocess.run(['taskkill', '/f', '/im', 'python.exe'], check=True)
        except subprocess.CalledProcessError:
            pass
        return "", "Execution timed out"

    return target()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_code():
    try:
        # Получаем данные из запроса
        data = request.get_json()
        code = data['code']
        input_data = data.get('input', '')

        # Выполняем код с таймаутом
        output, error = run_code_with_timeout(code, input_data)

        # Возвращаем результат
        return jsonify({
            'output': output,
            'error': error
        })
    except Exception as e:
        return jsonify({
            'output': '',
            'error': f"Server error: {str(e)}"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)