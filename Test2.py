import pygame
from pygame.locals import *
pygame.init()

Window = pygame.display.set_mode((0,0))
pygame.display.toggle_fullscreen()

ScreenWidth = pygame.display.Info().current_w
ScreenHeight = pygame.display.Info().current_h

Rectrangle = pygame.Rect((ScreenWidth/2,ScreenHeight/2),(ScreenWidth/3,ScreenHeight/3))
pygame.draw.rect(Window, (255,0,0), Rectrangle)

pygame.display.flip()

print(ScreenWidth,ScreenHeight)

def main():
    while True:
        for event in pygame.event.get():
            print("TEST 1")
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                print("TEST 2")
                pygame.quit()
                return

main()
i = input()
print("END")