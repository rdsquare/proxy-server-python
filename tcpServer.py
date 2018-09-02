import socket
from threading import Thread
import re
import requests
import ssl

print('''
    Proxy Server in Python  Copyright (C) 2018  Rahul Dangi
    This program comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions
''')

serverSocket = socket.socket()   #creating socket object
localHostIp = "0.0.0.0" # Work for all ips of the server computer
print("application bind with ", localHostIp)
port = 10000
serverSocket.bind((localHostIp, port))      #Reserving port for the tcpServer.py program
serverSocket.listen(10) # Listening for max 10 client connections in a queue or waiting for the client connection over port
#serverSocket.setblocking(False)
allThreads = set() #Store records of all threads for joining them
buffer = 1024 #Buffer size of tcpServer is 1kb or 1024 bytes

def handleClientConnection(clientSocket, clientAddr):
    'This will handle all the client connections'
    clientHeader = ""
    listHeader = []
    #print("Recieving request from client ", clientAddr)
    while True:
        rawData = clientSocket.recv(buffer) #recieving request from client
        try:
            clientHeader += rawData.decode("utf-8")
        except UnicodeDecodeError:
            break
        if len(rawData) < buffer:
            break
    listHeader = list(map(str, clientHeader.strip().split("\r\n")))
    

    if list(map(str, listHeader[0].split(" ")))[0].strip() == "GET":
        handleHttpRequest(clientSocket, listHeader)
    else :
        print("Recieved request: ", listHeader[0])
        handleHttpsRequest(clientSocket, clientHeader,listHeader)

def handleHttpRequest(clientSocket, listHeader):
    'This will handle http requests from the clients'
    webRequest = requests.get(list(map(str, listHeader[0].split(" ")))[1])
    if webRequest.status_code == 200:
        response = "HTTP/1.1 200 OK\r\nProxy-Agent: tcpServer\r\n\r\n"
        clientSocket.send(response.encode("utf-8"))
        clientSocket.sendall(webRequest.text.encode("utf-8"))
    else:
        response = "HTTP/1.1 404 Not Found\r\nProxy-Agent: tcpServer\r\n\r\nYour Website not Found\r\n"
        clientSocket.send(response.encode("utf-8"))

def handleHttpsRequest(clientSocket, clientHeader,listHeader):
    'This will handle https requests from the clients'
    webServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        webHost = list(map(str, listHeader[0].split(" ")))[1]
        webHost = list(map(str, webHost.split(":")))[0]
    except IndexError:
        print("Index error while fatching https request")
        return
    webhostip = ""
    try:
        webhostip = socket.gethostbyname(webHost)
    except socket.gaierror:
        print("Unknown host error while fatching https request")
        return
    webServerSocket.connect((webhostip, 443))
    response = "HTTP/1.1 200 Connection Established\r\nProxy-Agent: tcpServer\r\n\r\n"
    clientSocket.send(response.encode("utf-8"))
    
    transferThread = Thread(target = clientToServerTransfer, args=(clientSocket, webServerSocket))
    transferThread.setDaemon(True)
    transferThread.start()
    
    while True:
        serverData = webServerSocket.recv(buffer)
        clientSocket.send(serverData)
        if len(serverData) < 1:
            break
        
def clientToServerTransfer(clientSocket, webServerSocket):
    'This will handle asynchronous data transfer from client to server'
    while True:
        clientData = clientSocket.recv(buffer)
        webServerSocket.send(clientData)
        if len(clientData) < 1:
            break
 

while True:
    print("\tWaiting for client connection...")
    clientSocket, clientAddr = serverSocket.accept()  #Establish connection with client
    #Creating new thread and then handling client connection to accept another client connection as well
    print("Connection accepted from ", clientAddr)
    thread = Thread(target = handleClientConnection, args=(clientSocket, clientAddr))
    allThreads.add(thread) #adding thread to allThreads set
    thread.start()
