from tkinter import *;
from tkinter import ttk;
from PIL import Image,ImageTk
from tkinter.messagebox import askyesno
import math
import time
import threading
import random
from socket import *

LADDERS = [(3,22),(5,8),(11,26),(20,29)]
SNAKES = [(17,4),(19,7),(21,9),(27,1)]

class GameWindow(Frame):
    def __init__(self,root:Tk):
        self.master = root

        self.diceLbl = Label()
        self.diceLbl.pack()

        self.configWindow(root)
        self.load_images(root)
        self.setupCanvas(root)

        self.isConnected = False
        self.show_connection_status()
        self.isServer= self.ask_is_server()
        if(self.isServer):
            threading.Thread(target=self.startServer).start()
        else:
            threading.Thread(target=self.startClient).start()

        

    def configWindow(self,master):
        master.title("Ladder and Snake")
        master.geometry('800x700')
        master.resizable(0,0)

    def ask_is_server(self):
        return  askyesno("Establish Connection","Serve or Connect ?\nTo Serve press Yes")
    
    def show_connection_status(self):

        if(hasattr(self,'connectionLbl')):
            self.connectionLbl.destroy()

        if (self.isConnected):
            if(self.isServer):
                self.btn['state']= 'normal'
                role = "Client"
                self.master.title("Ladder and Snake : Server")
            else:
                role = "Server"
                self.master.title("Ladder and Snake : Client")
            self.connectionLbl = Label(self.master,text="Connected to "+role,fg='green')
        else:
            self.btn['state']= 'disabled'
            self.connectionLbl = Label(self.master,text="Not Connected",fg="red")

        self.connectionLbl.pack(side=BOTTOM)

    def startServer(self):
        host = '127.0.0.1'
        port = 20499
        serverSocket = socket(AddressFamily.AF_INET,SocketKind.SOCK_STREAM)
        serverSocket.bind((host,port))
        serverSocket.listen(1)
        client,address = serverSocket.accept()
        self.client = client
        self.isConnected= True
        self.show_connection_status()
        threading.Thread(target=self.revc_from_client).start()
        
    
    def send_to_server(self,msg:str):
        self.server.send(msg.encode())
        
    def revc_from_server(self):
        while True:
            msg = self.server.recv(1024).decode()
            if(msg=="restart"):
                self.resart_game()
            else:
                movement = int(msg)
                self.show_dice(movement)
                self.move_player_1(movement)
                self.btn['state']= 'normal'

    def send_to_client(self,msg:str):
        self.client.send(msg.encode())

    def revc_from_client(self):
        while True:
            msg = self.client.recv(1024).decode()
            if(msg=="restart"):
                self.resart_game()
            else:
                movement = int(msg)
                self.show_dice(movement)
                self.move_player_2(movement)
                self.btn['state']= 'normal'
                

    
    def startClient(self):
        host = '127.0.0.1'
        port = 20499
        clientSocket = socket(AddressFamily.AF_INET,SocketKind.SOCK_STREAM)
        clientSocket.connect((host,port))
        self.server = clientSocket
        self.isConnected= True
        self.show_connection_status()
        threading.Thread(target=self.revc_from_server).start()

    def load_images(self,master):
        #Load an image in the script
        master.backgroundImg = Image.open("background.png").resize((800,500),Image.LANCZOS)
        master.backgroundPhotoImg= ImageTk.PhotoImage(image=master.backgroundImg)

        master.p1Img = Image.open("p1.png").resize((100,100),Image.LANCZOS)
        master.p1PhotoImg= ImageTk.PhotoImage(image=master.p1Img)

        master.p2Img = Image.open("p2.png").resize((100,100),Image.LANCZOS)
        master.p2PhotoImg= ImageTk.PhotoImage(image=master.p2Img)
        master.diceIMGs = []
        master.dicePhotoIMGs = []
        for i in range(6):
            master.diceIMGs.append(Image.open(f"d{i+1}.png").resize((100,100),Image.LANCZOS)) 
            master.dicePhotoIMGs.append(ImageTk.PhotoImage(image=master.diceIMGs[len(master.diceIMGs)-1])) 

    def setupCanvas(self,master):
        #Create a canvas
        self.canvas= Canvas(master, width= 800, height= 500)
        self.canvas.pack()
        
        self.btn = ttk.Button(master,text="Move",command=self.move_func)
        self.btn.pack(pady=20)
        
        #Add image to the Canvas Items
        self.canvas.create_image(0,0,anchor=NW,image=master.backgroundPhotoImg)
        (x1,y1)= self.get_pixels(1)
        self.show_dice(1)

        self.p1Pos = 1
        self.p2Pos = 1

        master.p1 = self.canvas.create_image(x1,y1,anchor=NW,image=master.p1PhotoImg)
        master.p2 =self.canvas.create_image(x1,y1,anchor=NW,image=master.p2PhotoImg)

    def roll_dice(self):
        movement  = random.randint(1,6)
        self.show_dice(movement)
        return movement
    
    def show_dice(self,num):
        self.diceLbl.destroy()
        self.diceLbl = Label(image=self.master.dicePhotoIMGs[num-1])
        self.diceLbl.pack()

    def move_func(self):

        movement  = self.roll_dice()
        if(self.isServer):
            threading.Thread(target=self.move_player_1, args=(movement,)).start()
            self.send_to_client(str(movement))
        else:
            threading.Thread(target=self.move_player_2, args=(movement,)).start()
            self.send_to_server(str(movement))
        
    def move_player(self,movment,currentPos,player):
        self.btn['state']= 'disabled'
        wantedPos = movment + currentPos
        if(wantedPos>30):
            return currentPos

        while(currentPos != wantedPos ):
            if(currentPos < wantedPos):
                currentPos+=1
            else:
                currentPos-=1
            (x,y) = self.get_pixels(currentPos)
            self.canvas.moveto(player,x,y)
            time.sleep(0.5)

        for ladder in LADDERS:
            if(currentPos == ladder[0]):
                currentPos = ladder[1]
                break
        
        for snake in SNAKES:
            if(currentPos == snake[0]):
                currentPos = snake[1]
                break

        (x,y) = self.get_pixels(currentPos)
        self.canvas.moveto(player,x,y)
        return currentPos
        

    def move_player_1(self,movement):
        self.p1Pos = self.move_player(movement,self.p1Pos,self.master.p1)

        if(self.p1Pos == 30 ):
            self.player_win("Player 1")
            
    def move_player_2(self,movement):
        self.p2Pos = self.move_player(movement,self.p2Pos,self.master.p2)
        if(self.p2Pos == 30 ):
            self.player_win("Player 2")
    
    def player_win(self,player):
        answer = askyesno("Game Over",f"{player} won ! \nRestart Game ?")
        if (answer):

            self.resart_game()

            if(self.isServer):
                self.send_to_client('restart')
            else:
                self.send_to_server('restart')

        else:
            self.btn.configure(command=lambda : self.player_win(player))

    def resart_game(self):

        self.canvas.destroy()
        self.btn.destroy()
        self.diceLbl.destroy()
        self.setupCanvas(self.master)

    def get_pixels(self,pos):
        x= 40 
        row  = math.ceil(pos / 6) - 1
        y = 400 - (row  * 100)

        col = pos % 6 
        if col == 0: col = 6

        if(row == 1 or row == 3 ):
            col = 7 - col 
        
        col = col - 1
        x = 20 + (col * 130)

        return (x,y)       
        
    
if __name__ == '__main__' :
    root = Tk()
    GameWindow(root)
    root.mainloop()