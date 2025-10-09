import pygame
import time
import signal
import sys

def signal_handler(sig, frame):
    print('You pressed Ctrl+C! Exiting...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

pygame.init()

screen_info = pygame.display.Info()
screen_width, screen_height = screen_info.current_w, screen_info.current_h

screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)

colors = [
    (255, 0, 0),    
    (0, 255, 0),     
    (0, 0, 255),    
#    (255, 255, 0),  
#    (255, 0, 255), 
#    (0, 255, 255),
    (255, 255, 255), 
    (0, 0, 0) 
]

color_index = 0

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:  
                color_index = (color_index + 1) % len(colors)  
    
    if not running:
        break

    screen.fill(colors[color_index])
    pygame.display.flip()

pygame.quit()
