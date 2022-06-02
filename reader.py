#!/usr/bin/env python3
import socket
import os
import sys
import signal

def READ(dict):
    #kontrola hodnot from a to 


    try:
            with open(f'data/{dict["File"]}', 'r') as file:
                fileContent = file.readlines()
                lines = len(fileContent)

            if(int(dict["From"]) < 0 ) or (int(dict["To"]) < 0 ) or (int(dict["To"]) < int(dict["From"])):
                return '','',200,'Bad request'
            if(int(dict["To"]) > (lines - 1)):
                return '','',201,'Bad line number'

    except FileNotFoundError:
        return '','',202,'No such file'
    except OSError:
        return '','',203,'Read error'
    except KeyError:
        return '','',200,'Bad request'

    headerReply = f'Lines:{int(dict["To"]) - int(dict["From"])}\n'
    contentReply = [fileContent[i] for i in range(int(dict["From"]), int(dict["To"]))]
    contentReply = ''.join(contentReply)

    return headerReply, contentReply, 100, 'OK'


def LS(dict):
    files = os.listdir('data')

    headerReply = f'Lines:{len(files)}\n'
    contentReply = '\n'.join(files) + '\n'

    return headerReply, contentReply, 100, 'OK'

def LENGTH(dict):


    try:
            if (dict["File"].find('/') != -1):
                return '','', 200, "Bad request"

            with open(f'data/{dict["File"]}', 'r') as file:
                fileContent = file.readlines()
                lines = len(fileContent)

    except FileNotFoundError:
        return '','',202,'No such file'
    except OSError:
        return '','',203,'Read error'
    except KeyError:
        return '','',200,'Bad request'

    headerReply = f'Lines:1\n'
    contentReply = f'{lines}' + '\n'

    return headerReply, contentReply, 100, 'OK'

def SEARCH(dict):
    try:
        searchedWord = dict["String"]

        if not (searchedWord.startswith('"') and searchedWord.endswith('"')):
            return '', '', 200, 'Bad request'
        searchedWord = searchedWord[1:-1]
        files = os.listdir('data')
        foundFiles = []

        for fileName in files:
            try:
                with open(f'data/{fileName}', 'r') as file: # otvorenie suborov
                    fileContent = file.readlines() # precitanie riadkov

                for line in fileContent:
                    if searchedWord in line:
                        foundFiles.append(fileName)
                        break

            except OSError:
                continue


    except KeyError:
        return '','',200,'Bad request'

    headerReply = f'Lines:{len(foundFiles)}\n' # pocet najdenych suborov
    contentReply = '\n'.join(foundFiles) + '\n' # nazvy najdenych suborov

    return headerReply, contentReply, 100, 'OK'

def SELECT(dict):
    try:
        searchedWord = dict["String"]

        if not (searchedWord.startswith('"') and searchedWord.endswith('"')):
            return '', '', 200, 'Bad request'
        searchedWord = searchedWord[1:-1]

        if (dict["File"].find('/') != -1):
            return '','', 200, "Bad request"

        with open(f'data/{dict["File"]}', 'r') as file: # otvorenie suboru
            fileContent = file.readlines() # precitaju vsetky riadky
                
            foundLines = []
            
            foundLines = [line for line in fileContent if searchedWord in line]


    except FileNotFoundError:
        return '','',202,'No such file'
    except OSError:
        return '','',203,'Read error'
    except KeyError:
        return '','',200,'Bad request'

    headerReply = f'Lines:{len(foundLines)}\n' # pocet najdenych riadkov
    contentReply = '\n'.join(foundLines) + '\n' # vypisanie najdenych riadkov

    return headerReply, contentReply, 100, 'OK'

def SPLITHEADER(line):
    line = line.strip() # odstranenie medzier (na konci/ na zaciatku)
    line=line.split(':') #rozdelenie na identifikator a hodnotu
    if(len(line) != 2):
        return '', ''
    if not line[0].isascii(): #kontroler ascii znakov
        return '', ''
    for char in line[0]:
        if(char.isspace()): #kontrola bielych znakov
            return '', ''
    if(line[0].find(':') != -1): # nesmie obsahovat dvojbodku
        return '', ''


    return line[0], line[1]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 9999))
signal.signal(signal.SIGCHLD, signal.SIG_IGN)
s.listen(5)

while True:
    connectedSocket, address = s.accept()
    print(f'connection from adress: {address}')
    pid_chld = os.fork()
    if pid_chld == 0:
        s.close()
        f = connectedSocket.makefile(mode='rw', encoding='utf-8')

        while True:
            headers = {}
            method = f.readline().strip()
            if not method:
                break

            data = f.readline()

            while data != "\n":
              identifier, value = SPLITHEADER(data) # rozdelenie hlavicky
              headers[identifier] = value
              data = f.readline()

            statusCode, statusMsg = (100, 'OK')

            if method == 'READ':
            	headerReply, contentReply, statusCode, statusMsg = READ(headers)

            elif method == 'LS':
                headerReply, contentReply, statusCode, statusMsg = LS(headers)

            elif method == 'LENGTH':
                headerReply, contentReply, statusCode, statusMsg = LENGTH(headers)

            elif method == 'SEARCH':
                headerReply, contentReply, statusCode, statusMsg = SEARCH(headers)

            elif method == 'SELECT':
                headerReply, contentReply, statusCode, statusMsg = SELECT(headers)

            else:
                statusCode, statusMsg = (204, 'Unknown method')

                f.write(f'{statusCode} {statusMsg}\n')
                f.write('\n')
                f.flush()
                sys.exit(0)

            f.write(f'{statusCode} {statusMsg}\n')
            f.write(headerReply)
            f.write('\n')
            f.write(contentReply)
            f.flush()
        print(f'{address} disconnected')
        sys.exit(0)
    else:
        connectedSocket.close()
