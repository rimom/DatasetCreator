import os
import sys
import json
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from io import BytesIO
import threading
import webview

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key'

def get_data_dir():
    """Return the appropriate directory for storing user data."""
    if getattr(sys, 'frozen', False):
        # The application is frozen (packaged)
        if sys.platform == "darwin":
            # macOS
            return os.path.expanduser('~/Library/Application Support/DatasetCreator')
        elif sys.platform.startswith('win'):
            # Windows
            return os.path.join(os.environ['APPDATA'], 'DatasetCreator')
        else:
            # Linux and other Unix-like systems
            return os.path.expanduser('~/.DatasetCreator')
    else:
        # The application is running in a normal Python environment
        return os.path.dirname(os.path.abspath(__file__))

DATA_DIR = get_data_dir()
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DATA_FILE = os.path.join(DATA_DIR, 'conversations.jsonl')

conversations = []

def load_conversations():
    global conversations
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                conversations = [json.loads(line) for line in f if line.strip()]
        except Exception as e:
            print(f"Error loading conversations: {e}")
            conversations = []
    else:
        conversations = []

def save_conversations():
    global conversations
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            for conv in conversations:
                json.dump(conv, f, ensure_ascii=False)
                f.write('\n')  # Ensure each conversation is on a new line (JSONL format)
    except Exception as e:
        print(f"Error saving conversations: {e}")

# Load conversations on app start
load_conversations()

@app.route('/', methods=['GET', 'POST'])
def index():
    global conversations
    if request.method == 'POST':
        # Handle form submission to add a conversation
        data = request.form
        system_message = data.get('system_message', 'You are a helpful assistant.').strip()
        persist = data.get('persist', 'off') == 'on'

        # Extract message pairs
        user_messages = data.getlist('user_message')
        assistant_messages = data.getlist('assistant_message')

        weights = []
        for i in range(len(user_messages)):
            weight_value = data.get(f'weight_{i}')
            if weight_value == 'on':
                weights.append(1)
            else:
                weights.append(0)

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})

        for user, assistant, weight in zip(user_messages, assistant_messages, weights):
            user = user.strip()
            assistant = assistant.strip()
            weight = int(weight)
            if not user or not assistant:
                flash("User and Assistant messages cannot be empty.", "danger")
                return redirect(url_for('index'))
            messages.append({"role": "user", "content": user})
            assistant_msg = {"role": "assistant", "content": assistant, "weight": weight}
            messages.append(assistant_msg)

        conversation = {"messages": messages}
        conversations.append(conversation)
        flash("Conversation added successfully!", "success")

        # Handle persist
        if persist:
            session['persist'] = True
            session['system_message'] = system_message
        else:
            session['persist'] = False
            session['system_message'] = "You are a helpful assistant."

        # Save to file
        save_conversations()

        return redirect(url_for('index'))

    # On GET, get system_message and persist from session
    system_message = session.get('system_message', "You are a helpful assistant.")
    persist = session.get('persist', False)

    return render_template('index.html', conversations=conversations, system_message=system_message, persist=persist)

@app.route('/export', methods=['GET'])
def export():
    if not conversations:
        flash("No conversations to export.", "warning")
        return redirect(url_for('index'))

    # Create a virtual binary file for JSONL
    vbf = ""
    for conv in conversations:
        vbf += json.dumps(conv, ensure_ascii=False) + '\n'

    bytes_io = BytesIO(vbf.encode('utf-8'))
    bytes_io.seek(0)

    return send_file(
        bytes_io,
        mimetype='application/json',
        as_attachment=True,
        download_name='dataset.jsonl'
    )

@app.route('/clear', methods=['POST'])
def clear():
    global conversations
    conversations = []
    save_conversations()
    # Reset session
    session['persist'] = False
    session['system_message'] = "You are a helpful assistant."
    flash("All conversations have been cleared.", "info")
    return redirect(url_for('index'))

@app.route('/edit/<int:conv_id>', methods=['GET', 'POST'])
def edit(conv_id):
    global conversations
    if conv_id < 0 or conv_id >= len(conversations):
        flash("Invalid conversation ID.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Handle form submission to update the conversation
        data = request.form
        system_message = data.get('system_message', 'You are a helpful assistant.').strip()
        persist = data.get('persist', 'off') == 'on'

        # Extract message pairs
        user_messages = data.getlist('user_message')
        assistant_messages = data.getlist('assistant_message')

        weights = []
        for i in range(len(user_messages)):
            weight_value = data.get(f'weight_{i}')
            if weight_value == 'on':
                weights.append(1)
            else:
                weights.append(0)

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})

        for user, assistant, weight in zip(user_messages, assistant_messages, weights):
            user = user.strip()
            assistant = assistant.strip()
            weight = int(weight)
            if not user or not assistant:
                flash("User and Assistant messages cannot be empty.", "danger")
                return redirect(url_for('edit', conv_id=conv_id))
            messages.append({"role": "user", "content": user})
            assistant_msg = {"role": "assistant", "content": assistant, "weight": weight}
            messages.append(assistant_msg)

        conversation = {"messages": messages}
        conversations[conv_id] = conversation
        flash("Conversation updated successfully!", "success")

        # Handle persist
        if persist:
            session['persist'] = True
            session['system_message'] = system_message
        else:
            session['persist'] = False
            session['system_message'] = "You are a helpful assistant."

        # Save to file
        save_conversations()

        return redirect(url_for('index'))

    # GET request: Render the form with existing conversation data
    conversation = conversations[conv_id]
    system_message = ""
    message_pairs = []
    i = 0

    for msg in conversation.get('messages', []):
        if msg['role'] == 'system':
            system_message = msg['content']
        elif msg['role'] == 'user':
            user_content = msg['content']
        elif msg['role'] == 'assistant':
            assistant_content = msg['content']
            weight = msg.get('weight', 1)
            message_pairs.append({
                'user_message': user_content,
                'assistant_message': assistant_content,
                'weight': weight
            })
            i += 1

    # Determine persist based on system_message
    persist = system_message != "You are a helpful assistant."
    # Update session based on edit
    if persist:
        session['persist'] = True
        session['system_message'] = system_message
    else:
        session['persist'] = False
        session['system_message'] = "You are a helpful assistant."

    return render_template('edit.html', conv_id=conv_id, system_message=system_message, message_pairs=message_pairs, persist=persist)

@app.route('/delete/<int:conv_id>', methods=['POST'])
def delete(conv_id):
    global conversations
    if conv_id < 0 or conv_id >= len(conversations):
        flash("Invalid conversation ID.", "danger")
        return redirect(url_for('index'))

    # Remove the conversation
    del conversations[conv_id]
    flash(f"Conversation {conv_id + 1} has been deleted.", "success")

    # Save to file
    save_conversations()

    return redirect(url_for('index'))

class API:
    def export_jsonl(self):
        if not conversations:
            return {'success': False, 'message': 'No conversations to export.'}

        # Create the JSONL content
        vbf = ""
        for conv in conversations:
            vbf += json.dumps(conv, ensure_ascii=False) + '\n'

        # Open a save file dialog
        save_path = webview.windows[0].create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename='dataset.jsonl'
        )

        print(f"save_path: {save_path}")  # Debugging line to check the value of save_path

        if save_path:
            try:
                # Check if save_path is a directory
                if os.path.isdir(save_path):
                    return {'success': False, 'message': 'Cannot save to a directory. Please select a file.'}

                # Use save_path directly, no need to index [0]
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(vbf)

                return {'success': True, 'message': f'File saved successfully at {save_path}.'}
            except Exception as e:
                return {'success': False, 'message': f'Error saving file: {str(e)}'}
        else:
            return {'success': False, 'message': 'Save canceled.'}



def run_app():
    app.run(port=5005, use_reloader=False)

if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        # We are running in a packaged app
        flask_thread = threading.Thread(target=run_app)
        flask_thread.daemon = True
        flask_thread.start()
        # Create an instance of the API class
        api = API()
        # Open the pywebview window with the API
        window = webview.create_window('Dataset Creator', 'http://127.0.0.1:5005', width=1200, height=1200, resizable=True, js_api=api)
        webview.start()
    else:
        # We are running directly with python app.py
        app.run(port=5000)