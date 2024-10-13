from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
import json
import os
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key'

# Path to store conversations persistently as JSONL
DATA_FILE = 'conversations.jsonl'

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
        weights = data.getlist('weight')
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        for user, assistant, weight in zip(user_messages, assistant_messages, weights):
            user = user.strip()
            assistant = assistant.strip()
            weight = int(weight) if weight.isdigit() else 1
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
        weights = data.getlist('weight')
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        for user, assistant, weight in zip(user_messages, assistant_messages, weights):
            user = user.strip()
            assistant = assistant.strip()
            weight = int(weight) if weight.isdigit() else 1
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

if __name__ == '__main__':
    app.run(debug=True)
