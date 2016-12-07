from random import randint
from random import randrange
import socket
import sys

DATA = ""
GAMEON = True
HOST = 'localhost'
NAME = 'Cap\'n Rob'
PORT = 7948
boardSize = (0,0)
players = {}

# check for passed in args
for i, arg in enumerate(sys.argv):
    if arg == '-p': PORT = int(sys.argv[i+1])
    if arg == '-h': HOST = sys.argv[i+1]

# digest message and respond
def digestMessage(mess):
    data = mess.split("|")
    # print('-->', mess )

    if mess.startswith('G'): joinGame(data)
    if mess.startswith('B'): storeBoard(data)
    if (mess.startswith('N')) and (NAME in mess): takeTurn()
    if mess.startswith('F'): endGame()

def endGame():
    global GAMEON
    global players
    iWin = True
    for player,state in players.items():
        if state['score'] > players[NAME]['score']: iWin = False

    if iWin:
        print('YAR! Vitory be mine! They be sleepin with yonder fishies!')
    else:
        print('Arg... I put up good fight, but they proved to be too much for Cap\'n Rob-bot')

    GAMEON = False

# create your board
def generateBoard(data):
    board = []

    for x in range(boardSize[1]):
        board.append("." * boardSize[0])

    for boat in data[11:]:
        character = boat[0]
        length = int(boat[1])
        horizontal = randint(0,1) == 0
        validSpot = False

        while not validSpot:
            validPlacement = True
            coords = [randint(1, boardSize[0]), randint(1, boardSize[1])]
            if horizontal and coords[0] > boardSize[0] - length:
                coords[0] = boardSize[0] - length
            elif not horizontal and coords[1] > boardSize[1] - length:
                coords[1] = boardSize[1] - length

            for i in range(length):
                spotCoords = coords[:]
                if horizontal: spotCoords[0] += i
                else: spotCoords[1] += i
                if getSpotAt(board, spotCoords) != '.':
                    validPlacement = False
                    break

            validSpot = validPlacement

        for i in range(length):
            spotCoords = coords[:]
            if horizontal: spotCoords[0] += i
            else: spotCoords[1] += i
            row = list(board[spotCoords[1]-1])
            row[spotCoords[0]-1] = character
            board[spotCoords[1]-1] = "".join(row)

    print("Here be the plans:")
    for line in board:
        print(line)

    return ''.join(board)

def getSpotAt(board, coords):
    global boardSize

    if coords[0] < 1 or coords[0] > boardSize[0] or coords[1] < 1 or coords[1] > boardSize[1]:
        return None

    character = board[coords[1]-1][coords[0]-1]
    # print("Spot {} has a {}".format(coords, character))
    return character


# join the game
def joinGame(data):
    global boardSize
    boardSize = (int(data[8]), int(data[9]))
    message = 'J|{}|{}\n'.format(NAME, generateBoard(data))
    sock.sendall(message.encode())
    print('We be join\'n this here game');

# selectShot
# this is where the logic and fun is going to go.
# right now, it will shoot randomly at the board with the most "."s
# needs to return an object with a player string and a coords tuple (x,y)
def selectShot():
    board = {}
    openTargets = []
    openSpots = 0

    ret = {};
    ret["coords"] = ""
    ret["player"] = ""

    #Select board
    for player, state in players.items():
        if player == NAME: continue
        if len(openTargets) > 0 and len(state['openTargets']) > len(openTargets) or len(openTargets) == 0 and state['board'].count(".") > openSpots:
            board = state['boardmap']
            ret["player"] = player
            openSpots = board.count(".")
            openTargets = state['openTargets']

    if len(openTargets) > 0:
        #destory mode
        coords = openTargets[0]
        if getSpotAt(board, (coords[0], coords[1]-1)) == ".": ret['coords'] = (coords[0], coords[1]-1)
        elif getSpotAt(board, (coords[0], coords[1]+1)) == ".": ret['coords'] = (coords[0], coords[1]+1)
        elif getSpotAt(board, (coords[0]-1, coords[1])) == ".": ret['coords'] = (coords[0]-1, coords[1])
        else: ret['coords'] = (coords[0]+1, coords[1])

    else:
        #search mode
        while True:
            x = randint(1, boardSize[0])
            y = randrange(1, boardSize[1], 2) if x%2==0 else randrange(2, boardSize[1]+1, 2)
            ret['coords'] = (x,y)
            if getSpotAt(board, ret['coords']) == ".": break;

    return ret

def isTargetOpen(board, coords):
    ret = (
        getSpotAt(board, coords) == "X" and (
        getSpotAt(board, (coords[0], coords[1]-1)) == "." or
        getSpotAt(board, (coords[0], coords[1]+1)) == "." or
        getSpotAt(board, (coords[0]+1, coords[1])) == "." or
        getSpotAt(board, (coords[0]-1, coords[1])) == "."
    ))
    return ret

def storeBoard(data):
    global players
    n = boardSize[0]
    playerName = data[1]
    players[playerName] = {}
    players[playerName]['board'] = data[3]
    players[playerName]['score'] = int(data[4]) if len(data[4]) else 0
    players[playerName]['boardmap'] = [data[3][i * n:i * n+n] for i,b in enumerate(data[3][::n])]
    players[playerName]['openTargets'] = []

    # get open Targets
    for row, rowval in enumerate(players[playerName]['boardmap']):
        for col, colval in enumerate(rowval):
            if isTargetOpen(players[playerName]['boardmap'], (col+1, row+1)):
                players[playerName]['openTargets'].append((col+1, row+1))

def takeTurn():
    target = selectShot()

    message = 'S|{}|{}|{}\n'.format(target['player'], target['coords'][0], target['coords'][1])
    sock.sendall(message.encode())
    print('Fire cannons at {}, {}:{}'.format(target['player'], target['coords'][0], target['coords'][1]));
    

#create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#bind the socket ( server and host will be params )
sock.connect((HOST, PORT))
print('Arg! connection secure on {}:{}'.format(HOST, PORT))

while GAMEON: 
  data = sock.recv(1024)
  DATA += data.decode("utf-8")

  if "\n" in DATA: 
    messages = DATA.split('\n')
    DATA = ""
    for message in messages: 
        if len(message): digestMessage(message)
