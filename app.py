from flask import Flask, render_template, session, redirect, request, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
import flask_socketio
import random as r
import json
import os

app = Flask(__name__)
app.secret_key = os.urandom(32) # clears all sessions


socketio = SocketIO(app, cors_allowed_origins='*')
rooms = {'NEEHOMA':{'owner':'aarav', 'users':['aarav'], 'started':False}}
# rooms = {}

with open('logs\\log.txt', "w+") as f:
    f.seek(0)
    f.truncate(0)
    f.seek(0)

def log(msg):
    with open('logs\\log.txt', "a") as f:
        f.write(msg+'\n')


def plainTextPage(text:str, link, linkText):    
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Artzle</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .container {
                text-align: center;
            }
            h1 {
                color: #333;
                font-size: 36px;
                margin-bottom: 20px;
            }
            p {
                color: #666;
                font-size: 18px;
            }
        </style>
        <style>
            .link {
                color: #93a782; /* Link color */
                text-decoration:none; /* Underline to mimic link */
                cursor: pointer; /* Change cursor to pointer on hover */
                font-size: 20px;
                margin-top: 40px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>''' + text + '''</h1>
            <div class="link" onclick="window.location.href=\''''+link+'''\'">'''+linkText+'''</div>
        </div>
    </body>
    </html>
    '''

def removeUserFromRoom(username, room):
    if username in rooms[room]['users']:
        rooms[room]['users'].remove(username)

####################### routes

@app.route('/')
def homePage():
    if session.get('room'):   
        if session['room'] in rooms:
            log(f'{session['username']} left room {session['room']}')
            removeUserFromRoom(session['username'], session['room'])
            if rooms[session['room']]['owner'] == session['username']:
                if rooms[session['room']]['users']:
                    rooms[session['room']]['owner'] = r.choice(rooms[session['room']]['users'])
                    log(f'Room {session['room']} transferred owner to {rooms[session['room']]['owner']}')
            if not rooms[session['room']]['users']:
                log(f'Room {session['room']} was deleted due to lack of any users')
                del rooms[session['room']]
    session['username'] = None
    session['inRoom'] = False
    session['room'] = ''
    return send_file("home.html")

@app.route("/drawing")
def drawingTurn():
    return render_template("drawing.html")

@app.route("/guessing")
def guessingTurn():
    return render_template("guessing.html")

@app.route("/getValidRoomCode")
def getValidRoomCode():
    def generateRandomRoomCode():
        chars = 'QWERTYUIOPASDFGHJKLZXCVBNM1234567890'
        code = ''
        for _ in range(6):
            code += r.choice(chars)
        return code
    
    roomCode = generateRandomRoomCode()
    while roomCode in rooms.keys():
        roomCode = generateRandomRoomCode()
    return roomCode


@app.route("/processJoinRoom", methods=['POST'])
def processJoinRoom():
    if session.get('room'):   
        if session['room'] in rooms:
            log(f'{session['username']} left room {session['room']}')
            removeUserFromRoom(session['username'], session['room'])
            if rooms[session['room']]['owner'] == session['username']:
                if rooms[session['room']]['users']:
                    rooms[session['room']]['owner'] = r.choice(rooms[session['room']]['users'])
                    log(f'Room {session['room']} transferred owner to {rooms[session['room']]['owner']}')
            if not rooms[session['room']]['users']:
                log(f'Room {session['room']} was deleted due to lack of any users')
                del rooms[session['room']]

    session['username'] = None
    session['inRoom'] = False
    session['room'] = ''
    room = request.form['joinRoomName']
    username = request.form['username'].strip()
    
    if room in rooms:
        if username in rooms[room]['users']:
            return plainTextPage('Username already in room', '/', 'Try another?')
        
        session['username'] = username
        session['inRoom'] = True
        session['room'] = room
        # join_room(room)
        rooms[room]['users'].append(username)
        log(f'{username} joined room {room}')
        # emit('userJoinedRoom', {'username': username, 'room': room, 'owner':rooms[room]['owner']}, room=room)
        return redirect(f'/room?room={room}')
    else:
        return plainTextPage('Room does not exist', '/', 'Try another?')
    
@app.route("/processCreateRoom", methods=['POST'])
def processCreateRoom():
    if session.get('room'):   
        if session['room'] in rooms:
            log(f'{session['username']} left room {session['room']}')
            removeUserFromRoom(session['username'], session['room'])
            if rooms[session['room']]['owner'] == session['username']:
                if rooms[session['room']]['users']:
                    rooms[session['room']]['owner'] = r.choice(rooms[session['room']]['users'])
                    log(f'Room {session['room']} transferred owner to {rooms[session['room']]['owner']}')
            if not rooms[session['room']]['users']:
                log(f'Room {session['room']} was deleted due to lack of any users')
                del rooms[session['room']]
    session['username'] = None
    session['inRoom'] = False
    session['room'] = ''
    room = request.form['createRoomName']
    username = request.form['username'].strip()
    
    if room not in rooms:
        session['username'] = username
        session['inRoom'] = True
        session['room'] = room
        rooms[room] = {'owner':username, 'users': [username], 'started': False}
        log(f'{username} created room {room} (owner)')
        return redirect(f'/room?room={room}')
    else:
        return plainTextPage('Room already exists', '/', 'Try another?')

@app.route("/room")
def lobbyForRoom():
    # ! delete this:
    if not session.get('username'):
        session['username'] = 'aarav'
        session['inRoom'] = True
        session['room'] = 'NEEHOMA'

    room = request.args.get('room')
    if room not in rooms.keys():
        return plainTextPage("Room doesn't exist", '/', 'Make one?')
    elif not room:
        return plainTextPage("Link invalid", '/', 'Try again?')
    elif not session.get('inRoom'):
        return plainTextPage("You are not in the room yet", '/', 'Enter it?')
    
    

    username = session.get('username')
    roomOwner = rooms[room]['owner']
    log(f'{username} waiting in lobby {room}')
    return render_template('lobby.html', room=room, roomOwner=roomOwner, users=rooms[room]['users'], userIsOwner=(username==roomOwner), username=username)      

# @socketio.on('my event', namespace='/processRemoveUserFromRoom')
@app.route('/processRemoveUserFromRoom', methods=['POST'])
def processRemoveUserFromRoom():
    data = request.get_json(force=True)
    log(f'{data['username']} left room {data['room']} client side, requesting an *WH update to graphics on others')
    socketio.emit('removeUserFromVisualLobbyList', data, namespace='/')

    return '', 204  # 204 No Content status

####################### drawing 

@socketio.on('connect')
def handleConnect():
    print('User Connected')
    emit('giveNewClientImage', broadcast=True)

@socketio.on('fullImage')
def sendFullImage(image):
    print("Sending full image")
    emit('fullImage', image, broadcast=True)

@socketio.on('newPacket')
def sendPacket(packet):
    emit('guessingClientsNewPacket', packet, broadcast=True)

####################### lobby (rooms) 

@socketio.on('lobbyConnect')
def handleLobbyConnect(data):
    log(f'*WH {data['username']} joined lobby {data['room']}, requesting update to graphics of others')
    emit('addUserToVisualLobbyList', data, broadcast=True)

####################### rooms
# @socketio.on('createRoom')
# def handleCreateRoom(data):
#     room = data['room']
#     username = data['username']
#     if room not in rooms:
#         rooms[room] = {'owner':username, 'users': [], 'started': False}
#         emit('roomCreated', {'room':room, 'owner':username})
#     else:
#         emit('roomError', {'error': 'Room Already Exists!'})

# @socketio.on('joinRoom')
# def handleJoinRoom(data):
#     room = data['room']
#     username = data['username']
#     if room in rooms:
#         join_room(room)
#         rooms[room]['users'].append(username)
#         emit('userJoinedRoom', {'username': username, 'room': room, 'owner':rooms[room]['owner']}, room=room)
#     else:
#         emit('roomError', {'error': "Room Doesn't Exist!"})
        
# @socketio.on('startRoom')
# def handleStartRoom(data):
#     room = data['room']
#     username = data['username']
#     if room in rooms and not rooms[room]['started'] and username == rooms[room]['owner']:
#         rooms[room]['started'] = True
#         emit('roomStarted', {'room': room}, room=room)
#         roomLogic(room)
#     else:
#         emit('room_error', {'error': 'Room already started or does not exist'})

# def roomLogic(room):
#     actions = ['action1', 'action2', 'action3']
#     for action in actions:
#         emit('roomAction', {'action':action}, room=room)
#         socketio.sleep(2)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000, allow_unsafe_werkzeug=True, debug=False)   