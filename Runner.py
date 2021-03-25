#!/usr/bin/python3
""""
Welcome to the backbone of the vending machine as of the 3rd Trimester of the year 2021
Made by yours truly, Woldorf Spernancus. If you dont know who this is... Thats sad
Sad but understandable, I will graduate soon.

This was created as the 7th/8th graders can't be sold soda in school so the vending machine has just gone un used.
<<<<<<< HEAD
The google sheet is how this code knows who to allow access to which buttons.
This will NOT work on a normal computer, it MUST be run on a RasberriePi to work
=======
The google sheet is how this code knows who to allow access to which buttons. The link for that is down below.
>>>>>>> 884ce2f4fc4d9ed432f767c3a46cbe8c46f1368d
"""
import gspread, pygame, urllib.request, time, sys
import RPi.GPIO as GPIO # using RPi.GPIO
from oauth2client.service_account import ServiceAccountCredentials
from pygame.locals import *
from _thread import *

#disable the warnings displayed when activating the GPIO pins
GPIO.setwarnings(False) 

#Initialize pygame, the screen drawing library
pygame.init()
pygame.display.set_caption("Isaacs Very Nice Vending Machine")

#Create a window object
Window = pygame.display.set_mode((500,500))
#Make Window fullscreen
#pygame.display.toggle_fullscreen()

#Temporary screen variables
ScreenWidth = pygame.display.Info().current_w
ScreenHeight = pygame.display.Info().current_h

#Setup some fonts to use
FONT = pygame.font.Font("airstrike.ttf", 80)

#Setup the sheet data
Client = gspread.service_account()
Sheet = Client.open("Vending Machine Manager Settings")
#Important sheet variables
UserPage = Sheet.worksheet("Users")
MetricsPage = Sheet.worksheet("Data Metrics")
ProfilePage = Sheet.worksheet("Profiles")
SettingsPage = Sheet.worksheet("Settings")

#Colors available for drawing
NAVYBLUE  = ( 60,  60, 100)
WHITE     = (255, 255, 255)
RED       = (255,   0,   0)
GREEN     = (  0, 255,   0)
BLUE      = (  0,   0, 255)
YELLOW    = (255, 255,   0)
ORANGE    = (255, 128,   0)
PURPLE    = (255,   0, 255)
CYAN      = (  0, 255, 255)
BLACK     = (  0,   0,   0)
DARKGREEN = (  0, 155,   0)

#Set the pins as inputs or outputs
#Image for reference: https://i2.wp.com/randomnerdtutorials.com/wp-content/uploads/2018/01/RPi-Pinout.jpg?ssl=1
GPIO.setmode(GPIO.BOARD) #Set the scheme for refering to pins. Im using the method that refers to pin placements rather than names
PinsList = [38,37,36,35,32,33,31,29,26,23,24,21,22,19,18,15,16,13,12,11]
LEDPinList = [37,35,33,29,23,21,19,15,13,11]
SODAPinList = [38,36,32,31,26,24,22,18,16,12]
#Configure all pins to be output except 40
GPIO.setup(PinsList, GPIO.OUT) 
GPIO.setup(40,GPIO.IN) #Motion sensor input
#PinVariables 
Active = False
Inactive = True
#Set all pins off 
for pin in PinsList:
    GPIO.output(pin, Inactive)
    
global AfterHoursProfile, OVERRIDE, AfterHours
AfterHoursProfile = "7"

#Threaded function that just checkes the time
def ThreadedTimeChecker():
    global AfterHoursProfile, AfterHours
    while True:
        Row = 1
        Breaker = False
        AfterHours = False
        #Check the collum for the date
        for data in SettingsPage.col_values(1):
            if data == "OVERRIDE PROFILE": #Check if the override is active
                Collumn = 1
                for Profile in SettingsPage.row_values(Row)[1:]:
                    if Collumn == 1 and Profile:
                        OVERRIDE = True
                    else:
                        OVERRIDE = False

                    if Collumn == 3 and OVERRIDE:
                        AfterHoursProfile = Profile
                        
                    Collumn += 1

            elif data == time.strftime("%A"): #Check if the day matches
                Collumn = 1
                for setting in SettingsPage.row_values(Row)[1:]:      
                    if Collumn == 1:
                        TimeList = []
                        TimeSetting = ""
                        #Parse through each setting and get the individual times
                        for character in setting:
                            if character == ":":
                                TimeList.append(TimeSetting)
                                TimeSetting = ""
                            else:
                                TimeSetting += character
                    
                        TimeList.append(TimeSetting)
                            
                        #CHECK IF THE CURRENT TIME IS INBETWEEN THE SETTING IN GOOGLE SHEETS AND MIDNIGHT
                        #%H is the Hour
                        #%M is the Minute
                        #%p is the PM/AM indicator
                        print(time.strftime("%H"))
                        if (int(TimeList[0]) < int(time.strftime("%H"))):
                            AfterHours = True
                        elif (int(TimeList[0]) == int(time.strftime("%H"))):
                            if int(TimeList[1]) <= int(time.strftime("%M")):
                                AfterHours = True               
                        
                        else:
                            AfterHours = False
                            
                    elif Collumn == 3:
                        AfterHoursProfile = setting
                        
                    print(time.strftime("%H"),time.strftime("%M"))
                        
                    Collumn += 1
            Row += 1
            
            if Breaker:
                break
        
        time.sleep(60)

#Function to check internet connection by connecting to google.com
def ConnectionTest(host='http://google.com'):
    try:
        urllib.request.urlopen(host)
        return True
    except:
        return False

def DrawBeforeEnter(Angle = None):
    Window.fill(RED)
    Text = FONT.render("SCAN CARD",True,(BLUE))

    #Uncomment this line and the one in the while loop that runs everything to have the words onscreen rotate
    #Text = pygame.transform.rotate(Text,Angle)

    Window.blit(Text,((ScreenWidth/2 - Text.get_rect().width/2),(ScreenHeight/2 - Text.get_rect().height/2)))

def DrawSOSNoConnection():
    Window.fill(BLACK)
    Text = FONT.render("NO CONNECTION",True,RED)
    SubText = FONT.render("OUT OF ORDER",True,RED)

    #Cordinates for Text
    X = ((ScreenWidth/2) - (Text.get_rect().width/2))
    Y = (ScreenHeight/3) - (Text.get_rect().height/2)
    #Cordinates for SubText
    X2 = ((ScreenWidth/2) - (SubText.get_rect().width/2))
    Y2 = (ScreenHeight - (ScreenHeight/3) - (SubText.get_rect().height/2))

    #Draw the text to the screen
    Window.blit(Text,(X,Y))
    Window.blit(SubText,(X2,Y2))

    return ConnectionTest()
  
def DrawCardError():
    Window.fill(RED)
    Text = FONT.render("ERROR",True,BLUE)
    SubText = FONT.render("PLEASE SCAN AGAIN",True,BLUE)

    #Cordinates for Text
    X = ((ScreenWidth/2) - (Text.get_rect().width/2))
    Y = (ScreenHeight/3) - (Text.get_rect().height/2)
    #Cordinates for SubText
    X2 = ((ScreenWidth/2) - (SubText.get_rect().width/2))
    Y2 = (ScreenHeight - (ScreenHeight/3) - (SubText.get_rect().height/2))

    Window.blit(Text,(X,Y))
    Window.blit(SubText,(X2,Y2))

def main(StudentID):
    #Row and Collumn are variables used to designate the row and collumn the bot is currently on when doing its nested for loops
    StartTime = time.time() #Time from the moment the card was scanned. Will be used to have a delay the code X amount of time to allow people to input payment and make selection of soda
    print(StartTime,"CHECK 1")
    try:
        #Get the delay amount and the time until override time
        Row = 2
        for data in SettingsPage.col_values(1)[1:]:
            if data == "Profile Activation Timer": #Get the delay
                Collumn = 1
                for setting in SettingsPage.row_values(Row)[1:]:
                    if Collumn == 1:
                        Delay = int(setting) #You have to make sure this is an integer and not a string
                    else:
                        if setting == "minutes":
                            Delay = Delay * 60 #Multiply this to get the seconds count
                        elif setting == "hours":
                            Delay = Delay * 3600 #Multiply this to get the seconds count
                    Collumn += 1
            Row += 1
        
        Row = 2
        Breaker = False
        #Geth the user profile data NOT which buttons are allowed
        for value in UserPage.col_values(1)[1:]: #Only check the ID collumn
            if StudentID == value:
                Collumn = 1 #What Collumn the bot is on
                for Info in UserPage.row_values(Row)[1:]: #From collumn B onwards
                    #print(Info,Collumn)
                    if Collumn == 1:
                        UserName = Info
                    elif Collumn == 2 and not OVERRIDE: #Collumn 2 is where the profile data is
                        UserProfile = Info
                    elif Collumn == 3: #Collumn 4 is the persons amount of sodas ordered
                        ConfirmedOrders = {"Amount":int(Info),"Row":Row,"Collumn":Collumn + 1}
                    elif Collumn == 4: #Scans of the card
                        CardScans = {"Amount":int(Info),"Row":Row,"Collumn":Collumn + 1}
                        #Incriment the placements
                    Collumn += 1
                    Breaker = True
                    
            Row += 1
            
            if Breaker:
                break

        print(time.time(),"CHECK 2")

        #Get what buttons/LEDs are allowed based on the profile of the user ID AND set them
        Row = 2
        for Profile in ProfilePage.col_values(1)[1:]:
            if Profile == UserProfile:                 
                ButtonNumber = 0
                for Button in ProfilePage.row_values(Row)[1:]:
                    if Button: #If the button is cleared, turn on the LED and Button
                        GPIO.output(LEDPinList[ButtonNumber], Inactive)
                        GPIO.output(SODAPinList[ButtonNumber], Inactive)
                    else: #Otherwise, make sure they're off
                        GPIO.output(LEDPinList[ButtonNumber], Active)
                        GPIO.output(SODAPinList[ButtonNumber], Active)
                    ButtonNumber +=1
            Row += 1
        
        #Reset all pins/LEDs to off after a soda has been selected
        CurrentTime = time.time()
        while (CurrentTime - StartTime) < Delay: #Give time to pay machine and get soda
            CurrentTime = time.time()
            if GPIO.input(40):
                ConfirmedOrders["Amount"] += 1
                #Update the metrics page
                Placement = 1
                for data in MetricsPage.col_values(1): #data is not needed, when running "MetricsPade.col_count it gave me 25 for some reason so this is my workaround for that"
                    Placement += 1

                #The amount of collumns plus 1 to go down and put it one below the lowest data
                MetricsPage.update_cell(Placement, 1, StudentID) #Enter ID
                MetricsPage.update_cell(Placement, 2, UserName) #Enter the Name
                MetricsPage.update_cell(Placement, 3, time.asctime()) #Enter the time
                break
        
        #Set all pins to off
        for Button in PinsList:
            GPIO.output(Button, Inactive)

        #Update that the card was scanned:
        CardScans["Amount"] += 1
        UserPage.update_cell(ConfirmedOrders["Row"],ConfirmedOrders["Collumn"],ConfirmedOrders["Amount"])
        UserPage.update_cell(CardScans["Row"],CardScans["Collumn"],CardScans["Amount"])

        return ConnectionTest()
    except:
        return ConnectionTest()

#Some base variables before the loop begins
Connected = ConnectionTest() #Initial connection test
Angle = 0
StudentID = ""

start_new_thread(ThreadedTimeChecker,())

while True:
    #Connected = ConnectionTest()
    #print(time.strftime("%I")) Hour
    #print(time.strftime("%M")) Minutes

    if Connected:
        DrawBeforeEnter(Angle)
        #For every event that pygame detects:
        for event in pygame.event.get():
            if event.type == KEYDOWN: #If a key was pressed
                if event.key == K_RETURN: #If the key was ENTER
                    Connected = main(StudentID) #Take the StudentID to set buttons and such
                    print(StudentID)
                    StudentID = "" #Reset the Student ID as it was taken in by the main() function         
                else:
                    StudentID += (pygame.key.name(event.key)) #Add all other inputs to the StudentID
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
                
        #Uncomment these 2 lines and the one mentioned in the DrawBeforeEnter() function to have the start screen rotate cause I'm a weezord
        #Angle += 5
        #pygame.time.Clock().tick(15)

    else:
        DrawSOSNoConnection()

    pygame.display.flip()