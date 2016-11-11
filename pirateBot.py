from random import randint
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
                if getSpotAt("".join(board), spotCoords) != '.':
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

def getSpotAt(line, cords):
    n = boardSize[0]
    boardMap = [line[i * n:i * n+n] for i,b in enumerate(line[::n])]
    character = boardMap[cords[1]-1][cords[0]-1]
    # print("Spot {} has a {}".format(cords, character))
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
def selectShot():
    board = {}
    openSpots = 0

    ret = {};
    ret["cords"] = ""
    ret["player"] = ""


    #Select board
    for player, state in players.items():
        if player == NAME: continue
        if state['board'].count(".") > openSpots:
            board = state['board']
            ret["player"] = player
            openSpots = board.count(".")

    #select cords
    while True:
        ret['cords'] = (randint(1, boardSize[0]), randint(1, boardSize[1]))
        if getSpotAt(board, ret['cords']) == ".": break;

    return ret


def storeBoard(data):
    global players
    playerName = data[1]
    players[playerName] = {}
    players[playerName]['board'] = data[3]
    players[playerName]['score'] = int(data[4]) if len(data[4]) else 0

def takeTurn():
    target = selectShot()

    message = 'S|{}|{}|{}\n'.format(target['player'], target['cords'][0], target['cords'][1])
    sock.sendall(message.encode())
    print('Fire cannons at {}, {}:{}'.format(target['player'], target['cords'][0], target['cords'][1]));
    

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
