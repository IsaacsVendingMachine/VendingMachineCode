import pygame, sys
from pygame.locals import *

pygame.init()

while True:
    #print(len(pygame.event.get()))
    for event in pygame.event.get():
        print(KEYDOWN)
        if event.type == KEYDOWN: #If a key was pressed
            if event.key == K_ESCAPE:
                print("TEST")
                raise KeyboardInterrupt
                sys.exit()
