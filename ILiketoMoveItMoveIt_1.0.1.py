import os
import shutil
import webbrowser
import traceback
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request

app = Flask(__name__)
app.jinja_env.cache = {}

# ---------------------- HTML TEMPLATE ----------------------
FORM_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MoveIt Form</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            font-size: 2em;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background: #f5f5f5;
        }
        form {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            width: 2000px;
            position: relative;
        }
        input[type="text"], input[type="date"] {
            font-size: 1em;
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            box-sizing: border-box;
        }
        input[type="submit"] {
            font-size: 1.5em;
            padding: 20px;
            width: 100%;
            background-color: rgb(0, 150, 155);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: rgb(4, 69, 71);
        }
        label {
            margin-bottom: 5px;
            display: block;
        }
        .message {
            background-color: #e0ffe0;
            color: #2e7d32;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #c8e6c9;
            position: relative;
        }
        .message .close {
            position: absolute;
            top: 8px;
            right: 12px;
            font-size: 1.2em;
            color: #2e7d32;
            cursor: pointer;
        }
        .error {
            background-color: #ffe0e0;
            color: #b71c1c;
            border-color: #f5c6cb;
        }
    </style>
</head>
<body>
    <form id="moveForm" method="POST">
        {% if message %}
        <div class="message {{ 'error' if error else '' }}" id="resultMessage">
            <span class="close" onclick="document.getElementById('resultMessage').remove();">&times;</span>
            {{ message }}
        </div>
        {% endif %}
        
        <label>From Directory:</label>
        <input type="text" name="from_dir" placeholder="e.g. K:\FLOWCAL\Coterra_Prod_Arc\zProcessedFilesArchive\cfx\..." required>

        <label>To Directory:</label>
        <input type="text" name="to_dir" placeholder="e.g. K:\FLOWCAL\Coterra_Prod_Import\cfx\..." required>

        <label>Date Modified Start Date:</label>
        <input type="date" name="start_date" required>

        <label>Date Modified End Date:</label>
        <input type="date" name="end_date" required>

        <label>Old Extension (e.g. .cf_R_bLAhbLAhbLAh):</label>
        <input type="text" name="old_ext" placeholder=".cf_R_...">

        <label>New Extension (e.g. .csv):</label>
        <input type="text" name="new_ext" placeholder=".cfx">

        <input type="submit" value="Move it!">
    </form>

    <script>
        // Reset form after slight delay to allow message to appear
        document.getElementById('moveForm').addEventListener('submit', function () {
            setTimeout(() => this.reset(), 100);
        });
    </script>
</body>
</html>
'''

# ---------------------- LOGGING FUNCTION ----------------------
def log_action(message, moved_files=None, is_error=False):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_filename = 'moveit.log'
    with open(log_filename, 'a', encoding='utf-8') as log:
        log.write(f"[{timestamp}] {'ERROR' if is_error else 'INFO'}: {message}\n")
        if moved_files:
            for f in moved_files:
                log.write(f"    - {f}\n")
        log.write("\n")

# ---------------------- FILE MOVER FUNCTION ----------------------
def move_files(from_dir, to_dir, start_date, end_date, old_ext, new_ext):
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

    os.makedirs(to_dir, exist_ok=True)

    moved_files = []

    for file in os.listdir(from_dir):
        full_path = os.path.join(from_dir, file)
        if os.path.isfile(full_path):
            mod_time = datetime.fromtimestamp(os.path.getmtime(full_path))
            if start_date <= mod_time < end_date and (not old_ext or old_ext in file):
                new_name = os.path.splitext(file)[0] + new_ext
                shutil.move(full_path, os.path.join(to_dir, new_name))
                moved_files.append(file)

    return moved_files

# ---------------------- FLASK WEB ROUTE ----------------------
@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        try:
            from_dir = request.form.get('from_dir')
            to_dir = request.form.get('to_dir')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            old_ext = request.form.get('old_ext')
            new_ext = request.form.get('new_ext')

            # ✅ Validate input before proceeding
            if not os.path.isdir(from_dir):
                raise Exception(f"❌ Source directory does not exist: {from_dir}")

            moved_files = move_files(from_dir, to_dir, start_date, end_date, old_ext, new_ext)
            moved_count = len(moved_files)
            message = f'✅ {moved_count} file(s) moved'

            log_action(
                f"{moved_count} file(s) moved from '{from_dir}' to '{to_dir}'",
                moved_files=moved_files
            )

            return render_template_string(FORM_HTML, message=message, error=False)

        except Exception as e:
            error_msg = f"{str(e)}"
            log_action(error_msg + "\n" + traceback.format_exc(), is_error=True)
            return render_template_string(FORM_HTML, message=error_msg, error=True)

    return render_template_string(FORM_HTML)

# ---------------------- RUN APP ----------------------
if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000")
    app.run(port=5000)
