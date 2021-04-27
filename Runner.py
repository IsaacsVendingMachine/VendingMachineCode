#!/usr/bin/python3
""""
Welcome to the backbone of the vending machine as of the 3rd Trimester of the year 2021
Made by yours truly, Woldorf Spernancus. If you dont know who this is... Thats sad
Sad but understandable, I will graduate soon.

This was created as the 7th/8th graders can't be sold soda in school so the vending machine has just gone un used.

The google sheet is how this code knows who to allow access to which buttons.
This will NOT work on a normal computer, it MUST be run on a RasberriePi to work

The google sheet is how this code knows who to allow access to which buttons. The link for that is down below.
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

#Screen variables
ScreenWidth = pygame.display.Info().current_w
ScreenHeight = pygame.display.Info().current_h

#Background variable:
Background = pygame.image.load("OriginalBackground.png")
Background = pygame.transform.scale(Background,(ScreenWidth,ScreenHeight))

#Setup some fonts to use
FONT = pygame.font.Font("airstrike.ttf", 300)
SMALLFONT = pygame.font.Font("airstrike.ttf",200)

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
    
global AfterHoursProfile, OVERRIDE, AfterHours, DefaultProfile
AfterHoursProfile = "7"
DefaultProfile = "Guest"


#Make a User class:
class UserClass():
    def __init__(self,Scans,Orders,FirstName,Profile,ID,FullName):
        self.scans = Scans
        self.orders = Orders
        self.firstname = FirstName
        self.fullname = FullName
        self.profile = Profile
        self.ID = ID
        self.buttonCount = 0
        self.buttonList = []

    def ScanUpdateSheet(self):
        UserPage.update_cell(self.scans["Row"],self.scans["Collumn"],(self.scans["Amount"] + 1))

    def OrderUpdateSheet(self):
        self.orders["Amount"] += 1
        #Update the metrics page
        Placement = 1
        for data in MetricsPage.col_values(1):
            Placement += 1
        #The amount of collumns plus 1 to go down and put it one below the lowest data
        MetricsPage.update_cell(Placement, 1, self.ID) #Enter ID
        MetricsPage.update_cell(Placement, 2, self.fullname) #Enter the Name
        MetricsPage.update_cell(Placement, 3, time.strftime("%x")) #Enter the date
        MetricsPage.update_cell(Placement, 4, time.strftime("%X")) #Enter the time
        
        UserPage.update_cell(self.orders["Row"],self.orders["Collumn"],self.orders["Amount"])
    
class DefaultUserClass():
    def __init__(self, DefaultProfile):
        self.profile = DefaultProfile
        self.buttonList = []
        self.buttonCount = 0

#Threaded function that just checkes the time
def ThreadedTimeChecker():
    global AfterHoursProfile, AfterHours, DefaultProfile, OVERRIDE
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
                        if (int(TimeList[0]) < int(time.strftime("%H"))):
                            AfterHours = True
                        elif (int(TimeList[0]) == int(time.strftime("%H"))):
                            if int(TimeList[1]) <= int(time.strftime("%M")):
                                AfterHours = True               
                        
                        else:
                            AfterHours = False
                            
                    elif Collumn == 3:
                        AfterHoursProfile = setting
                        
                    #print(time.strftime("%H"),time.strftime("%M"))
                        
                    Collumn += 1
                    
            elif data == "DEFAULT PROFILE":
               for setting in SettingsPage.row_values(Row)[1:]:
                   if setting != None:
                       DefaultProfile = setting
                    
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
    Window.blit(Background,(0,0))
    Text = FONT.render("SCAN CARD",True,(WHITE))
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
    Window.blit(Background,(0,0))
    Text = FONT.render("ERROR",True,WHITE)
    SubText = SMALLFONT.render("NOT RECOGNIZED",True,WHITE)

    #Cordinates for Text
    X = ((ScreenWidth/2) - (Text.get_rect().width/2))
    Y = (ScreenHeight/3) - (Text.get_rect().height/2)
    #Cordinates for SubText
    X2 = ((ScreenWidth/2) - (SubText.get_rect().width/2))
    Y2 = (ScreenHeight - (ScreenHeight/3) - (SubText.get_rect().height/2))

    Window.blit(Text,(X,Y))
    Window.blit(SubText,(X2,Y2))
    
def DrawWelcome(Name):    
    Window.blit(Background,(0,0))
    Text = FONT.render("SELECT SODA",True,WHITE)
    Welcome = SMALLFONT.render("WELCOME BACK",True,WHITE)
    Name = SMALLFONT.render(Name,True,WHITE)
    
    #Cordinates for Text
    X = ((ScreenWidth/2) - (Text.get_rect().width/2))
    Y = (ScreenHeight/3) - (Text.get_rect().height/2)
    #Cordinates for Welcome
    X2 = ((ScreenWidth/2) - (Welcome.get_rect().width/2))
    Y2 = (ScreenHeight - (ScreenHeight/3) - (Welcome.get_rect().height/2))
    #Cordinated for Name
    X3 = ((ScreenWidth/2) - (Name.get_rect().width/2))
    Y3 = (ScreenHeight - (ScreenHeight/5) - (Name.get_rect().height/2))
    
    Window.blit(Text,(X,Y))
    Window.blit(Welcome,(X2,Y2))
    Window.blit(Name,(X3,Y3))

def GetDefaultUser():
    #Make the Default User class to pass around:
    Default = DefaultUserClass(DefaultProfile)
    #Locate the data on the ProfileSetting page which matches the default user name:
    ProfileSetting = ProfilePage.find(Default.profile)

    for Info in ProfilePage.row_values(ProfileSetting.row)[1:]:
        Default.buttonList.append(Info)
        if Info:
            Default.buttonCount += 1
    return Default

def main(StudentID):
    global OVERRIDE
    #Row and Collumn are variables used to designate the row and collumn the bot is currently on when doing its nested for loops
    #Get the delay amount and the time until override time
    Settings = SettingsPage.find("Profile Activation Timer")

    #Get the delay
    Collumn = 1
    for setting in SettingsPage.row_values(Settings.row)[1:]:
        if Collumn == 1:
            Delay = int(setting) #You have to make sure this is an integer and not a string
        else:
            if setting == "minutes":
                Delay = Delay * 60 #Multiply this to get the seconds count
            elif setting == "hours":
                Delay = Delay * 3600 #Multiply this to get the seconds count
        Collumn += 1

    #Get the user data
    try:
        Profile = UserPage.find(StudentID)
        User = "Filler"
    except:
        User = None
    
    if User != None:    
        Collumn = 1
        for Info in UserPage.row_values(Profile.row)[1:]: #From collumn B onwards
            print(Info, Collumn)
            if Collumn == 1:
                LastName = Info
            elif Collumn == 2:
                FirstName = Info
            elif Collumn == 3 and not OVERRIDE: #Collumn 2 is where the profile data is
                UserProfile = Info
            elif Collumn == 4: #Collumn 4 is the persons amount of sodas ordered
                ConfirmedOrders = {"Amount":int(Info),"Row":Profile.row,"Collumn":Collumn + 1}
            elif Collumn == 5: #Scans of the card
                CardScans = {"Amount":int(Info),"Row":Profile.row,"Collumn":Collumn + 1}
            
            #Incriment the placements
            Collumn += 1     
        try:
            User = UserClass(CardScans,ConfirmedOrders,FirstName,UserProfile,StudentID,(FirstName + " " + LastName))
        except:
            ConfirmedOrders
            = {"Amount":int(0),"Row":Profile.row,"Collumn":UserPage.find("Verified Purchases").col}
            CardScans = {"Amount":int(0),"Row":Profile.row,"Collumn":UserPage.find("Barcode Scans").col}
            User = UserClass(CardScans,ConfirmedOrders,FirstName,UserProfile,StudentID,(FirstName + " " + LastName))
            
        Profile = ProfilePage.find(User.profile)

        for Info in ProfilePage.row_values(Profile.row)[1:]:
            User.buttonList.append(Info)
            if Info:
                User.buttonCount += 1
                
        #Update the spreadsheet
        User.ScanUpdateSheet()
        print(User.fullname)
        
    UserDefault = GetDefaultUser()
    return ConnectionTest(), Delay, User, UserDefault, time.time()

#Some base variables before the loop begins
Connected = ConnectionTest() #Initial connection test
Angle = 0
StudentID = ""

start_new_thread(ThreadedTimeChecker,())
UserDefault = GetDefaultUser()
ScanTime = 0
ErrorTime = 0
CardError = False
Scanned = False
DrawingName = False


while True:
    CurrentTime = time.time()
    #Connected = ConnectionTest()
    
    DrawBeforeEnter(Angle)
    if Connected:
        #For every event that pygame detects:
        for event in pygame.event.get():
            if event.type == KEYDOWN: #If a key was pressed
                if event.key == K_RETURN: #If the key was ENTER
                    Connected, Delay, User, UserDefault, ScanTime = main(StudentID) #Take the StudentID to set buttons and such
                    print(UserDefault.buttonList)
                    if User != None: 
                        Scanned = True
                    else:
                        CardError
                        ErrorTime = time.time()
                    StudentID = "" #Reset the Student ID as it was taken in by the main() function                   
                elif event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                else:
                    StudentID += (pygame.key.name(event.key)) #Add all other inputs to the StudentID
        
        if Scanned and (CurrentTime - (ScanTime + 4) <= Delay) and User != None:
            DrawingName = True
            if User.buttonCount >= UserDefault.buttonCount:
                Placement = 0
                for LED in LEDPinList:
                    if User.buttonList[Placement]:
                        GPIO.output(LED, Active)
                    else:
                        GPIO.output(LED, Inactive)
                    #print(User.buttonList[Placement])
                    Placement += 1
                          
                Placement = 0
                for Button in SODAPinList:
                    if User.buttonList[Placement]:
                        GPIO.output(Button, Active)
                    else:
                        GPIO.output(Button, Inactive)
                    Placement += 1
            
            else:
                Placement = 0
                for LED in LEDPinList:
                    if UserDefault.buttonList[Placement]:
                        GPIO.output(LED, Active)
                    else:
                        GPIO.output(LED, Inactive)
                    Placement += 1

                Placement = 0
                for Button in SODAPinList:
                    if UserDefault.buttonList[Placement]:
                        GPIO.output(Button, Active)
                    else:
                        GPIO.output(Button, Inactive)
                        
                    #print(UserDefault.buttonList[Placement])
                    Placement += 1

            #Update the metrics page if the sensor pin is triggered with a True
            if GPIO.input(40):
                User.OrderUpdateSheet()
                Scanned = False
        else:
            DrawingName = False
            Placement = 0
            for LED in LEDPinList:
                if UserDefault.buttonList[Placement]:
                    GPIO.output(LED, Active)
                else:
                    GPIO.output(LED, Inactive)
                Placement += 1
                
            Placement = 0
            for Button in SODAPinList:
                if UserDefault.buttonList[Placement]:
                    GPIO.output(Button, Active)
                else:
                    GPIO.output(Button, Inactive)            
                
                #print(UserDefault.buttonList[Placement])
                Placement += 1
                
                
        if CurrentTime - ErrorTime <= 2 and not CardError:
            DrawCardError()
        else:
            CardError = False
            if DrawingName:
                DrawWelcome(User.firstname)
            else:
                DrawBeforeEnter(Angle)
                
        #Uncomment these 2 lines and the one mentioned in the DrawBeforeEnter() function to have the start screen rotate cause I'm a weezord
        #Angle += 5
        #pygame.time.Clock().tick(15)

    else:
        DrawSOSNoConnection()

    pygame.display.flip()
