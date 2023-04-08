#!usr/bin/python3

#------------------------------------------------------------------------------
# IMPORTS
#------------------------------------------------------------------------------

import pygame
import math
#import skatepong_mpu6050
from mpu6050 import mpu6050
from gyro import Gyro
import time

#------------------------------------------------------------------------------
# DEVELOPMENT VARIABLES
#------------------------------------------------------------------------------

DEV_MODE = True # Used to avoid full screen display mode during dev phase.

#------------------------------------------------------------------------------
# INITIALIZATION
#------------------------------------------------------------------------------

pygame.init()
#mpu_left = mpu6050(0x68)
#mpu_right = mpu6050(0x69)
# Defining gyroscopes sensitivity :
#mpu_left.set_gyro_range(0x10) #(250deg/s=0x00, 500deg/s=0x08, 1000deg/s=0x10, 2000deg/s=0x18)
#mpu_right.set_gyro_range(0x10) #(250deg/s=0x00, 500deg/s=0x08, 1000deg/s=0x10, 2000deg/s=0x18)

#------------------------------------------------------------------------------
# CONSTANTS THAT CAN BE ADJUSTED
#------------------------------------------------------------------------------

GYRO_SENSITIVITY = mpu6050.GYRO_RANGE_1000DEG
"""Possible values:
mpu6050.GYRO_RANGE_500DEG
mpu6050.GYRO_RANGE_500DEG
mpu6050.GYRO_RANGE_1000DEG
mpu6050.GYRO_RANGE_2000DEG
"""
PADDLE_WIDTH_RATIO = 0.02 # Ratio to screen width [0.01 - 0.1]
PADDLE_HEIGHT_RATIO = 0.15 # Ratio to screen height [0.05 - 0.2]
PADDLE_OFFSET_TO_FRAME_RATIO = 0.01 # Ratio to screen width
BALL_RADIUS_RATIO = 0.02 # Ratio to min screen width/height [0.01 - 0.04]
PADDLE_VY_RATIO = 0.03 # Ratio to screen height [0.005 - 0.04]
BALL_V_RATIO = 0.015 # Ratio to min screen width [0.005 - 0.02]
BALL_ANGLE_MAX = 60 # In degrees [30-75]
MID_LINE_HEIGHT_RATIO = 0.05 # Ratio to screen height  [ideally 1/x -> int]
SCORE_Y_RATIO = 0.02 # Ratio to screen height (to set score vertically)
FPS = 60
WINNING_SCORE = 5

#------------------------------------------------------------------------------
# CONSTANTS
#------------------------------------------------------------------------------

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SCORE_FONT = pygame.font.SysFont("comicsans", 100)

#------------------------------------------------------------------------------
# CODE
#------------------------------------------------------------------------------

class Paddle:
    COLOR = WHITE

    def __init__(self, x, y, w, h):
        self.x = self.original_x = x # Top left hand corner - horizontal axis
        self.y = self.original_y = y # Top left hand corner - vertical axis
        self.w = w # Paddle width (in pixels)
        self.h = h # Paddle height (in pixels)

    def draw(self, win):
        pygame.draw.rect(win, self.COLOR, (self.x, self.y, self.w, self.h))

class Ball:
    COLOR = WHITE

    def __init__(self, x, y, r, vx, vy):
        self.x = self.original_x = x # Ball center - horizontal axis
        self.y = self.original_y = y # Ball center - vertical axis
        self.vx = self.original_vx = vx # Ball velocity - horizontal axis (in pixels)
        self.vy = self.original_vy = vy # Ball velocity - vertical axis (in pixels)
        self.r = r # Ball radius (in pixels)

    def draw(self, win):
        pygame.draw.circle(win, self.COLOR, (self.x, self.y), self.r)

    def draw_black(self, win):
        pygame.draw.circle(win, BLACK, (self.x, self.y), self.r)    

    def move(self):
        self.x += self.vx
        self.y += self.vy
    
    def reset(self):
        self.x = self.original_x
        self.y = self.original_y
        self.vx = self.original_vx
        self.vy = self.original_vy
    
"""   
def draw_game(win, pads, ball, l_score, r_score, win_w, win_h, mid_line_h_ratio):
    
    # Scores
    win.fill(BLACK)
    l_score_text = SCORE_FONT.render(f"{l_score}", 1, WHITE)
    r_score_text = SCORE_FONT.render(f"{r_score}", 1, WHITE)
    win.blit(l_score_text, (win_w//4 - l_score_text.get_width()//2, 20))
    win.blit(r_score_text, (int(win_w*(3/4)) - r_score_text.get_width()//2, 20))
    
    # Paddles
    for pad in pads:
        pad.draw(win)

    # Ball
    ball.draw(win)
    
    # Middle line
    draw_mid_line(win, win_w,win_h,mid_line_h_ratio)
    
    pygame.display.update()

def draw_victory(win, pads, l_score, r_score, win_w, win_h, win_text):
    win.fill(BLACK)
    l_score_text = SCORE_FONT.render(f"{left_score}", 1, WHITE)
    r_score_text = SCORE_FONT.render(f"{right_score}", 1, WHITE)
    win.blit(l_score_text, (win_w//4 - l_score_text.get_width()//2, 20))
    win.blit(r_score_text, (int(win_w*(3/4)) - r_score_text.get_width()//2, 20))
    text = SCORE_FONT.render(win_text, 1, WHITE)
    win.blit(text, (win_w//2 - text.get_width() // 2, win_h//2 - text.get_height()//2))
    for pad in pads:
        pad.draw(win)
    pygame.display.update()
"""

def create_window(DEV_MODE):
    #disp_w, disp_h = pygame.display.get_desktop_sizes()
    disp_w = pygame.display.Info().current_w # Display width (in pixels)
    disp_h = pygame.display.Info().current_h # Display height (in pixels)
    if DEV_MODE == True:
        WIN = pygame.display.set_mode([disp_w, disp_h-100])
        pygame.display.set_caption("Skatepong")         
    else:
        WIN = pygame.display.set_mode([0, 0], pygame.FULLSCREEN)
    win_w , win_h = pygame.display.get_surface().get_size()
    return WIN, win_w, win_h

def compute_elements_sizes(win_w, win_h):
    """Compute elements sizes/speeds based on display resolution"""
    pad_w = round(win_w*PADDLE_WIDTH_RATIO)
    pad_h = round(win_h*PADDLE_HEIGHT_RATIO)
    ball_r = min(round(win_w*BALL_RADIUS_RATIO), round(win_h*BALL_RADIUS_RATIO))
    ball_vx = round(BALL_V_RATIO*win_w)
    # ball_vy = 0
    #pad_vy_max = round(win_h * PADDLE_VY_RATIO)
    return pad_w, pad_h, ball_r, ball_vx#, ball_vy, pad_vy_max

def draw_game(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, mid_line_h_ratio, win_text, won):

    # Scores
    win.fill(BLACK)
    l_score_text = SCORE_FONT.render(f"{l_score}", 1, WHITE)
    r_score_text = SCORE_FONT.render(f"{r_score}", 1, WHITE)
    l_score_x = win_w//4 - l_score_text.get_width()//2
    r_score_x = int(win_w*(3/4)) - r_score_text.get_width()//2
    score_y = win_h*SCORE_Y_RATIO
    win.blit(l_score_text, (l_score_x, score_y))
    win.blit(r_score_text, (r_score_x, score_y))
    # Paddles
    l_pad.draw(win)
    r_pad.draw(win)
    if won == False:
        # Ball
        ball.draw(win)
        # Middle line
        draw_mid_line(win, win_w,win_h,mid_line_h_ratio)
    else:
        text = SCORE_FONT.render(win_text, 1, WHITE)
        win.blit(text, (win_w//2 - text.get_width() // 2, win_h//2 - text.get_height()//2))

    pygame.display.update()

def draw_mid_line(win, win_width,win_height,mid_line_height_ratio):
    line_element_height = round(win_height*mid_line_height_ratio)
    nb_iterations = round(1/mid_line_height_ratio)-1
    for i in range(0, nb_iterations):
        if i % 2 == 1:
            continue
        pygame.draw.rect(win, WHITE, (win_width//2 - 5, i*line_element_height+line_element_height//2, 10, line_element_height))

def handle_pad_movement(pad, win_h, vy_pad):
    if pad.y + vy_pad < 0:
        pad.y = 0
    elif pad.y + pad.h + vy_pad > win_h:
        pad.y = win_h - pad.h
    else:
        pad.y += vy_pad

def handle_collision(ball, l_pad,r_pad, win_w, win_h):
    # Collision with top wall or bottom wall:
    if ((ball.y + ball.r >= win_h) or (ball.y - ball.r <= 0)):
        ball.vy *= -1
    # Collision with left paddle:
    elif ball.vx < 0:
        if ball.x - ball.r <= l_pad.x + l_pad.w:
            if ball.y >= l_pad.y and ball.y <= l_pad.y + l_pad.h:            
                y_pad_mid = l_pad.y + l_pad.h // 2
                if (ball.y < y_pad_mid+10 and ball.y > y_pad_mid-10):
                    ball.vx = abs(ball.original_vx)                    
                else:
                    angle = round((ball.y - y_pad_mid) / (l_pad.h / 2) * BALL_ANGLE_MAX)
                    vx = round(math.cos(math.radians(angle)) * BALL_V_RATIO * win_w)
                    vy = round(math.sin(math.radians(angle)) * BALL_V_RATIO * win_w)
                    ball.vy = vy
                    ball.vx = vx
    # Collision with right paddle:
    else:
        if ball.x + ball.r >= r_pad.x:
            if ball.y >= r_pad.y and ball.y <= r_pad.y + r_pad.h:
                y_pad_mid = r_pad.y + r_pad.h // 2
                if (ball.y < y_pad_mid+10 and ball.y > y_pad_mid-10):
                    ball.vx = -abs(ball.original_vx)   
                else:
                    angle = round((ball.y - y_pad_mid) / (r_pad.h / 2) * BALL_ANGLE_MAX)
                    vx = round(math.cos(math.radians(angle)) * BALL_V_RATIO * win_w)
                    vy = round(math.sin(math.radians(angle)) * BALL_V_RATIO * win_w)
                    ball.vy = vy
                    ball.vx = -vx

def count_score(ball, l_score, r_score, won, win_text, win_w, win_h):
    
    if ball.x < 0:
        r_score += 1
        #ball = Ball(win_w // 2, win_h // 2, ball_r, ball_vx, ball_vy)
        #draw_game(WIN, [l_pad, r_pad], ball, l_score, r_score, win_w, win_h, mid_line_h)
    elif ball.x > win_w:
        l_score += 1
        #ball = Ball(win_w // 2, win_h // 2, ball_r, -ball_vx, ball_vy)
        #draw_game(WIN, [l_pad, r_pad], ball, l_score, r_score, win_w, win_h, mid_line_h)
    if ball.x < 0 or ball.x > win_w:
        ball.reset()

    if l_score >= WINNING_SCORE:
        won = True
        win_text = "Left Player Won!"
    elif r_score >= WINNING_SCORE:
        won = True
        win_text = "Right Player Won!"
    
    return l_score, r_score, won, win_text

def check_exit_game(keys):
    if keys[pygame.K_ESCAPE]:
        pygame.quit()

def initialize_game(win_w, win_h):
    # Creating game objects:
    # - Both paddles are centered vertically
    # - The ball is created in the center of the display, with a horizontal velovity
    mid_line_h = round(MID_LINE_HEIGHT_RATIO *  win_h)
    pad_w, pad_h, ball_r, ball_vx = compute_elements_sizes(win_w, win_h)
    l_pad_x = PADDLE_OFFSET_TO_FRAME_RATIO * win_w
    r_pad_x = win_w - PADDLE_OFFSET_TO_FRAME_RATIO*win_w - pad_w
    pad_y = (win_h - pad_h) // 2
    l_pad = Paddle(l_pad_x, pad_y, pad_w, pad_h)
    r_pad = Paddle(r_pad_x, pad_y, pad_w, pad_h)
    ball = Ball(win_w // 2, win_h // 2, ball_r, ball_vx, 0)
    # Initializing game variables:
    l_score = 0
    r_score = 0
    won = False
    win_text = ""
    #first_loop = True
    return l_pad, r_pad, ball, mid_line_h, l_score, r_score, won, win_text

def main():
    run = True
    clock = pygame.time.Clock()
    # Creating game window:
    WIN, win_w, win_h = create_window(DEV_MODE)
    # Creating the 2 gyroscopes objects:
    l_gyro = Gyro(Gyro.I2C_ADDRESS_1, 'y', GYRO_SENSITIVITY)
    r_gyro = Gyro(Gyro.I2C_ADDRESS_2, 'y', GYRO_SENSITIVITY)
    # Initializing game:
    l_pad, r_pad, ball, mid_line_h, l_score, r_score, won, win_text = initialize_game(win_w, win_h)

    while run:
        
        clock.tick(FPS)
        #won = False
        #WIN.fill(BLACK)
        #ball.draw_black(WIN)
        #pygame.display.update()
        #pygame.time.delay(100)
        draw_game(WIN, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, MID_LINE_HEIGHT_RATIO, win_text, won)
        """
        if first_loop == True:
            pygame.time.delay(2000)
            first_loop = False
        """
        # Handle closing of game window by clicking on the red cross or ESCAPE button:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
        keys = pygame.key.get_pressed()
        check_exit_game(keys)            

        """
        elif event.type == pygame.VIDEORESIZE:
            win_width = event.w
            win_height = event.h
            paddle_width, paddle_height, ball_radius, vy, ball_vx, ball_vy = compute_elements_sizes(win_width, win_height)
            create_window(False)
            l_pad = Paddle(10, win_height//2 - paddle_height // 2, paddle_width, paddle_height,vy)
            r_pad = Paddle(win_width - 10 - paddle_width, win_height // 2 - paddle_height//2, paddle_width, paddle_height,vy)
            ball = Ball(win_width // 2, win_height // 2, ball_radius, ball_vx, ball_vy)
            draw_game(WIN, [l_pad, r_pad], ball, left_score, right_score,win_width, win_height,MID_LINE_HEIGHT_RATIO)
            pygame.display.update()
        """
        
        vy_l_pad = l_gyro.get_gyro()
        vy_r_pad = r_gyro.get_gyro()
        handle_pad_movement(l_pad, win_h, vy_l_pad)
        handle_pad_movement(r_pad, win_h, vy_r_pad)
        
        ball.draw_black(WIN)
        pygame.display.update()
        #pygame.time.delay(15)
        ball.move()

        handle_collision(ball, l_pad, r_pad, win_w, win_h)

        l_score, r_score, won, win_text = count_score(ball, l_score, r_score, won, win_text, win_w, win_h)

        if won:
            draw_game(WIN, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, MID_LINE_HEIGHT_RATIO, win_text, won)
            pygame.time.delay(5000)
            l_pad, r_pad, ball, mid_line_h, l_score, r_score, won, win_text = initialize_game(win_w, win_h)

    pygame.quit()

if __name__ == '__main__':
    main()
