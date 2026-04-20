from flask import Flask, render_template, request, jsonify, session
import random
import string

app = Flask(__name__)
app.secret_key = 'rps-secret-key-change-me'

MOVES = ['rock', 'paper', 'scissors']

# Stores room data - NOT persistent, for demo purposes only
INVITE_ROOMS = {}  # room_id: {'players': [...], 'history': [...], 'mode': 'bot' or 'friend'}

def decide_winner(p1, p2):
    if p1 == p2:
        return "It's a tie!"
    if (p1 == 'rock' and p2 == 'scissors') or \
       (p1 == 'scissors' and p2 == 'paper') or \
       (p1 == 'paper' and p2 == 'rock'):
        return "Player 1 wins!"
    else:
        return "Player 2 wins!"

def random_id(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/create_room', methods=['POST'])
def create_room():
    mode = request.json.get('mode', 'bot')
    room_id = random_id()
    session['room_id'] = room_id
    INVITE_ROOMS[room_id] = {
        'players': [None, None],
        'history': [],
        'mode': mode
    }
    return jsonify({'room_id': room_id})

@app.route('/join_room', methods=['POST'])
def join_room():
    room_id = request.json.get('room_id')
    if room_id in INVITE_ROOMS:
        session['room_id'] = room_id
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Room not found'})

@app.route('/play', methods=['POST'])
def play():
    move = request.json['move']
    room_id = session.get('room_id')
    mode = INVITE_ROOMS.get(room_id, {}).get('mode', 'bot')
    history = INVITE_ROOMS.get(room_id, {}).get('history', [])
    player_num = int(request.json.get('player_num', 1))
    
    if mode == 'bot':
        computer_move = random.choice(MOVES)
        result = decide_winner(move, computer_move)
        history.append({'player1': move, 'player2': computer_move, 'result': result})
        return jsonify({'player': move, 'opponent': computer_move, 'result': result, 'history': history})
    else:
        players = INVITE_ROOMS[room_id]['players']
        if player_num == 1:
            if players[0] is None:
                players[0] = move
                return jsonify({'waiting': True, 'msg': 'Waiting for friend...', 'history': history})
            else:
                return jsonify({'waiting': True, 'msg': 'Waiting for friend...', 'history': history})
        elif player_num == 2:
            if players[0] is not None and players[1] is None:
                players[1] = move
                p1 = players[0]
                p2 = move
                result = decide_winner(p1, p2)
                history.append({'player1': p1, 'player2': p2, 'result': result})
                INVITE_ROOMS[room_id]['players'] = [None, None]
                return jsonify({'player': p1, 'opponent': p2, 'result': result, 'history': history})
            elif players[1] is None:
                # Don't allow Player 2 to move first
                return jsonify({'waiting': True, 'msg': 'Waiting for Player 1 to play...', 'history': history})
            else:
                return jsonify({'waiting': True, 'msg': 'Waiting for next round...', 'history': history})

@app.route('/reset', methods=['POST'])
def reset():
    room_id = session.get('room_id')
    if room_id and room_id in INVITE_ROOMS:
        INVITE_ROOMS[room_id]['history'].clear()
        INVITE_ROOMS[room_id]['players'] = [None, None]
    return jsonify({'success': True})

@app.route('/status')
def status():
    room_id = session.get('room_id')
    mode = INVITE_ROOMS.get(room_id, {}).get('mode', 'bot')
    history = INVITE_ROOMS.get(room_id, {}).get('history', [])
    players = INVITE_ROOMS.get(room_id, {}).get('players', [None, None])
    waiting = False
    msg = ""
    # Report 'waiting' if (friend mode) only first player has moved
    if mode == 'friend' and players[0] is not None and players[1] is None:
        waiting = True
        msg = "Waiting for friend..."
    elif mode == 'friend' and players[0] is None and players[1] is None and len(history) > 0:
        waiting = False
        msg = ""
    return jsonify({
        'waiting': waiting,
        'msg': msg,
        'history': history,
        'players': players
    })

if __name__ == '__main__':
    app.run(debug=True)
