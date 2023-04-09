#!usr/bin/python3

#------------------------------------------------------------------------------
# IMPORTS
#------------------------------------------------------------------------------

import pygame
import math
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

#------------------------------------------------------------------------------
# CONSTANTS THAT CAN BE ADJUSTED
#------------------------------------------------------------------------------

WINNING_SCORE = 5
DELAY_GAME_ENDED = 5 # Delay after game end (in s)
DELAY_COUNTDOWN = 5 # Countdown before starting the game (in s)
GYRO_SENSITIVITY = mpu6050.GYRO_RANGE_500DEG
"""Possible values:
mpu6050.GYRO_RANGE_250DEG
mpu6050.GYRO_RANGE_500DEG
mpu6050.GYRO_RANGE_1000DEG
mpu6050.GYRO_RANGE_2000DEG
"""
WELCOME_RADIUS_RATIO = 0.25 # Ratio to screen height [0.1 - 0.5]
PAD_WIDTH_RATIO = 0.02 # Ratio to screen width [0.01 - 0.1]
PAD_HEIGHT_RATIO = 0.15 # Ratio to screen height [0.05 - 0.2]
PAD_X_OFFSET_RATIO = 0.02 # Ratio to screen width [0.01 - 0.02] - Frame offset
BALL_RADIUS_RATIO = 0.02 # Ratio to min screen width/height [0.01 - 0.04]
PAD_FLAT_BOUNCE_RATIO = 0.01 # # Ratio to screen width [0.005 - 0.02]
BALL_V_RATIO = 0.025 # Ratio to min screen width [0.005 - 0.025]
BALL_ANGLE_MAX = 60 # In degrees [30-75] - Max angle after paddle collision
MID_LINE_HEIGHT_RATIO = 0.05 # Ratio to screen height  [ideally 1/x -> int]
SCORE_Y_OFFSET_RATIO = 0.02 # Ratio to screen height (to set score vertically)
FONT_NAME = "comicsans"
SCORE_FONT_RATIO = 0.1 # Ratio to screen height [0.1 - 0.2]
WELCOME_FONT_RATIO = 0.1 # Ratio to screen height 
FPS = 60

#------------------------------------------------------------------------------
# CONSTANTS
#------------------------------------------------------------------------------

# Defining the different scenes of the game :
SCENE_WELCOME = 0
SCENE_WAITING_PLAYERS = 1
SCENE_COUNTDOWN = 2
SCENE_GAME_ONGOING = 3
SCENE_GAME_END = 4

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (127, 127, 127)
#SCORE_FONT = pygame.font.SysFont(FONT_NAME, SCORE_FONT_RATIO)

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

def welcome(win, win_w, win_h):
    start_time = time.time()
    win.fill(BLACK)
    pygame.draw.circle(win, WHITE, (win_w//2, win_h//2), WELCOME_RADIUS_RATIO * win_h)
    font = pygame.font.SysFont(FONT_NAME, round(WELCOME_FONT_RATIO*win_h))
    text = font.render("SKATEPONG", 1, BLACK)
    win.blit(text, (win_w//2 - text.get_width() // 2, win_h // 2 - text.get_height() // 2))
    pygame.display.update()
    current_time = time.time()
    while current_time - start_time < 3:
        # Handle closing of game window by clicking on the red cross or ESCAPE button:
        keys = pygame.key.get_pressed()
        run = check_exit_game(keys)
        if run == False:
            break
        current_time = time.time()
    game_status = SCENE_WAITING_PLAYERS
    return run, game_status

def waiting_players(win, win_w, win_h, l_pad, r_pad, l_gyro, r_gyro, ball):
 
    run = True
    moving_time = time.time()
    current_time = time.time()
    left_player_ready = False
    right_player_ready = False
    ball.vx = 0
    font_1 = pygame.font.SysFont(FONT_NAME, round(WELCOME_FONT_RATIO*win_h))
    font_2 = pygame.font.SysFont(FONT_NAME, round(WELCOME_FONT_RATIO*1/2*win_h))
    text_2 = font_2.render("MOVE SKATES TO START", 1, WHITE)
    
    while ((left_player_ready == False) or (right_player_ready == False)):
            
        # Handle closing of game window by clicking on the red cross or ESCAPE button:        
        keys = pygame.key.get_pressed()
        run = check_exit_game(keys)
        if run == False:
            break

        if ((left_player_ready == False) and (right_player_ready == False)):
            message = "WAITING FOR PLAYERS"
        elif ((left_player_ready == False) and (right_player_ready == True)):
            message = "LEFT PLAYER MISSING"
        elif ((left_player_ready == True) and (right_player_ready == False)):
            message = "RIGHT PLAYER MISSING"
        
        text_1 = font_1.render(message, 1, WHITE)
        win.fill(BLACK)
        win.blit(text_1, (win_w//2 - text_1.get_width() // 2, win_h // 4 - text_1.get_height() // 2))
        win.blit(text_2, (win_w//2 - text_2.get_width() // 2, (win_h * 3) // 4 - text_2.get_height() // 2))
        ball.draw(win)
        l_pad.draw(win)
        r_pad.draw(win)
        pygame.display.update()
        
        vy_l_pad = l_gyro.get_gyro()
        vy_r_pad = r_gyro.get_gyro()
        if abs(vy_l_pad) > 25:
            left_player_ready = True
            moving_time = time.time()
        if abs(vy_r_pad) > 25:
            right_player_ready = True
            moving_time = time.time()
        handle_pad_movement(l_pad, win_h, vy_l_pad)
        handle_pad_movement(r_pad, win_h, vy_r_pad)

        current_time = time.time()
        print("current_time ", current_time)
        print("moving_time ", moving_time)

        if current_time - moving_time > 5:
            left_player_ready = 0
            right_player_ready = 0

    game_status = SCENE_COUNTDOWN
    return run, game_status

def countdown(win, win_w, win_h, l_pad, r_pad, l_gyro, r_gyro, ball):
    start_time = time.time()
    font = pygame.font.SysFont(FONT_NAME, round(WELCOME_FONT_RATIO*win_h))
    current_time = time.time()
    
    while current_time - start_time < DELAY_COUNTDOWN:
        
        # Handle closing of game window by clicking on the red cross or ESCAPE button:
        keys = pygame.key.get_pressed()
        run = check_exit_game(keys)
        if run == False:
            break
        
        time_before_start = DELAY_COUNTDOWN - int(current_time - start_time)        
        text = font.render(str(time_before_start), 1, WHITE)
        win.fill(BLACK)
        win.blit(text, (win_w//2 - text.get_width() // 2, win_h // 4 - text.get_height() // 2))
        ball.draw(win)
        l_pad.draw(win)
        r_pad.draw(win)
        pygame.display.update()
        
        vy_l_pad = l_gyro.get_gyro()
        vy_r_pad = r_gyro.get_gyro()
        handle_pad_movement(l_pad, win_h, vy_l_pad)
        handle_pad_movement(r_pad, win_h, vy_r_pad)
        
        current_time = time.time()
   
    game_status = SCENE_GAME_ONGOING
    return run, game_status

def game_ongoing(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, MID_LINE_HEIGHT_RATIO, win_text, won, l_gyro, r_gyro):
    clock = pygame.time.Clock()
    run = True    
    while (run and l_score < WINNING_SCORE and r_score < WINNING_SCORE):

        clock.tick(FPS)
        # Handle closing of game window by clicking on the red cross or ESCAPE button:
        keys = pygame.key.get_pressed()
        run = check_exit_game(keys)
        if run == False:
            break

        draw_game(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, MID_LINE_HEIGHT_RATIO, win_text, won)
        ball.move()

        vy_l_pad = l_gyro.get_gyro()
        vy_r_pad = r_gyro.get_gyro()

        handle_pad_movement(l_pad, win_h, vy_l_pad)
        handle_pad_movement(r_pad, win_h, vy_r_pad)

        handle_collision(ball, l_pad, r_pad, win_w, win_h)

        l_score, r_score, won, win_text = detect_goal(ball, l_score, r_score, won, win_text, win_w, win_h)
        """
        if won:
            draw_game(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, MID_LINE_HEIGHT_RATIO, win_text, won)
            pygame.time.delay(DELAY_GAME_ENDED)
            l_pad, r_pad, ball, mid_line_h, l_score, r_score, won, win_text = initialize_game(win_w, win_h)
            game_status = SCENE_GAME_END
        """
        if won:
            #l_pad, r_pad, ball, mid_line_h, l_score, r_score, won, win_text = initialize_game(win_w, win_h)
            game_status = SCENE_GAME_END
         
    return run, game_status

def game_end(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, mid_line_h_ratio, win_text, won, l_gyro, r_gyro):

    start_time = time.time()
    current_time = time.time()
    ball.vx = 0
    ball.vy = 0
    
    font = pygame.font.SysFont(FONT_NAME, round(WELCOME_FONT_RATIO*win_h))
    if (l_score == WINNING_SCORE):
        message = "LEFT PLAYER WON"
    else:
        message = "RIGHT PLAYER WON"
    
    text = font.render(message, 1, WHITE)
    
    while current_time - start_time < DELAY_GAME_ENDED:

        # Handle closing of game window by clicking on the red cross or ESCAPE button:
        keys = pygame.key.get_pressed()
        run = check_exit_game(keys)
        if run == False:
            break
    
        win.fill(BLACK)
        win.blit(text, (win_w//2 - text.get_width() // 2, win_h // 4 - text.get_height() // 2))
        ball.draw(win)
        l_pad.draw(win)
        r_pad.draw(win)
        SCORE_FONT = pygame.font.SysFont(FONT_NAME, round(SCORE_FONT_RATIO*win_h))
        l_score_text = SCORE_FONT.render(f"{l_score}", 1, WHITE)
        r_score_text = SCORE_FONT.render(f"{r_score}", 1, WHITE)
        l_score_x = win_w//4 - l_score_text.get_width()//2
        r_score_x = int(win_w*(3/4)) - r_score_text.get_width()//2
        score_y = win_h*SCORE_Y_OFFSET_RATIO
        win.blit(l_score_text, (l_score_x, score_y))
        win.blit(r_score_text, (r_score_x, score_y))
        
        pygame.display.update()
        
        vy_l_pad = l_gyro.get_gyro()
        vy_r_pad = r_gyro.get_gyro()
        handle_pad_movement(l_pad, win_h, vy_l_pad)
        handle_pad_movement(r_pad, win_h, vy_r_pad)
        
        current_time = time.time()
    
    game_status = SCENE_WAITING_PLAYERS 
    return run, game_status        

def compute_elements_sizes(win_w, win_h):
    """Compute elements sizes/speeds based on display resolution"""
    pad_w = round(win_w*PAD_WIDTH_RATIO)
    pad_h = round(win_h*PAD_HEIGHT_RATIO)
    ball_r = min(round(win_w*BALL_RADIUS_RATIO), round(win_h*BALL_RADIUS_RATIO))
    ball_vx = round(BALL_V_RATIO*win_w)
    return pad_w, pad_h, ball_r, ball_vx

def draw_game(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, mid_line_h_ratio, win_text, won):
    
    # Scores
    win.fill(BLACK)
    SCORE_FONT = pygame.font.SysFont(FONT_NAME, round(SCORE_FONT_RATIO*win_h))
    l_score_text = SCORE_FONT.render(f"{l_score}", 1, WHITE)
    r_score_text = SCORE_FONT.render(f"{r_score}", 1, WHITE)
    l_score_x = win_w//4 - l_score_text.get_width()//2
    r_score_x = int(win_w*(3/4)) - r_score_text.get_width()//2
    score_y = win_h*SCORE_Y_OFFSET_RATIO
       
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
                if (ball.y < y_pad_mid+PAD_FLAT_BOUNCE_RATIO*win_w and ball.y > y_pad_mid-PAD_FLAT_BOUNCE_RATIO*win_w):
                    ball.vx = abs(ball.original_vx)                    
                else:
                    angle = round((ball.y - y_pad_mid) / (l_pad.h / 2) * BALL_ANGLE_MAX)
                    # Constant speed
                    #vx = round(math.cos(math.radians(angle)) * BALL_V_RATIO * win_w)
                    #vy = round(math.sin(math.radians(angle)) * BALL_V_RATIO * win_w)
                    # Faster when there is an angle to compensate for longer distance
                    vx = round(math.cos(math.radians(angle)) * BALL_V_RATIO * win_w) * (2 - math.cos(math.radians(angle)))
                    vy = round(math.sin(math.radians(angle)) * BALL_V_RATIO * win_w) * (2 - math.cos(math.radians(angle)))                    
                    ball.vy = vy
                    ball.vx = vx
    # Collision with right paddle:
    else:
        if ball.x + ball.r >= r_pad.x:
            if ball.y >= r_pad.y and ball.y <= r_pad.y + r_pad.h:
                y_pad_mid = r_pad.y + r_pad.h // 2
                if (ball.y < y_pad_mid+PAD_FLAT_BOUNCE_RATIO*win_w and ball.y > y_pad_mid-PAD_FLAT_BOUNCE_RATIO*win_w):
                    ball.vx = -abs(ball.original_vx)   
                else:
                    angle = round((ball.y - y_pad_mid) / (r_pad.h / 2) * BALL_ANGLE_MAX)
                    # Constant speed
                    #vx = round(math.cos(math.radians(angle)) * BALL_V_RATIO * win_w)
                    #vy = round(math.sin(math.radians(angle)) * BALL_V_RATIO * win_w)
                    # Faster when there is an angle to compensate for longer distance
                    vx = round(math.cos(math.radians(angle)) * BALL_V_RATIO * win_w) * (2 - math.cos(math.radians(angle)))
                    vy = round(math.sin(math.radians(angle)) * BALL_V_RATIO * win_w) * (2 - math.cos(math.radians(angle)))                                        
                    ball.vy = vy
                    ball.vx = -vx

def detect_goal(ball, l_score, r_score, won, win_text, win_w, win_h):
    if ball.x < 0:
        r_score += 1
        vx_direction_after_goal = 1
    elif ball.x > win_w:
        l_score += 1
        vx_direction_after_goal = -1
    if ball.x < 0 or ball.x > win_w:
        ball.reset()
        ball.vx *= vx_direction_after_goal

    if l_score >= WINNING_SCORE:
        won = True
        win_text = "Left Player Won!"
    elif r_score >= WINNING_SCORE:
        won = True
        win_text = "Right Player Won!"
    
    return l_score, r_score, won, win_text

def check_exit_game(keys):
    run = True
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
            break
    if keys[pygame.K_ESCAPE]:
        run = False
    return run

def initialize_game(win_w, win_h):
    # Creating game objects:
    # - Both paddles are centered vertically
    # - The ball is created in the center of the display, with a horizontal velovity
    mid_line_h = round(MID_LINE_HEIGHT_RATIO *  win_h)
    pad_w, pad_h, ball_r, ball_vx = compute_elements_sizes(win_w, win_h)
    l_pad_x = PAD_X_OFFSET_RATIO * win_w
    r_pad_x = win_w - PAD_X_OFFSET_RATIO*win_w - pad_w
    pad_y = (win_h - pad_h) // 2
    l_pad = Paddle(l_pad_x, pad_y, pad_w, pad_h)
    r_pad = Paddle(r_pad_x, pad_y, pad_w, pad_h)
    ball = Ball(win_w // 2, win_h // 2, ball_r, ball_vx, 0)
    # Initializing game variables:
    l_score = 0
    r_score = 0
    won = False
    win_text = ""
    return l_pad, r_pad, ball, mid_line_h, l_score, r_score, won, win_text, ball_vx

def main():
    run = True
    #clock = pygame.time.Clock()
    # Creating game window:
    WIN, win_w, win_h = create_window(DEV_MODE)
    # Creating the 2 gyroscopes objects:
    l_gyro = Gyro(Gyro.I2C_ADDRESS_1, 'y', GYRO_SENSITIVITY)
    r_gyro = Gyro(Gyro.I2C_ADDRESS_2, 'y', GYRO_SENSITIVITY)
    # Initializing game:
    #game_status = 0
    game_status = 0
    l_pad, r_pad, ball, mid_line_h, l_score, r_score, won, win_text, ball_vx = initialize_game(win_w, win_h)

    while run == True:

        if game_status == SCENE_WELCOME:
            run, game_status = welcome(WIN, win_w, win_h)
        elif game_status == SCENE_WAITING_PLAYERS: # Waiting for players
            run, game_status = waiting_players(WIN, win_w, win_h, l_pad, r_pad, l_gyro, r_gyro, ball)
        elif game_status == SCENE_COUNTDOWN: # Countdown before start
            run, game_status = countdown(WIN, win_w, win_h, l_pad, r_pad, l_gyro, r_gyro, ball)
        elif game_status == SCENE_GAME_ONGOING: # Game ongoing
            ball.vx = ball_vx
            run, game_status = game_ongoing(WIN, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, MID_LINE_HEIGHT_RATIO, win_text, won, l_gyro, r_gyro)
        elif game_status == SCENE_GAME_END: # Game finished
            run, game_status = game_end(WIN, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, MID_LINE_HEIGHT_RATIO, win_text, won, l_gyro, r_gyro)

        """ Only valid with Python > 3.10
        match game_status:
            case SCENE_WELCOME: # Welcome screen with logo
                welcome(WIN, win_w, win_h)
            case SCENE_WAITING_PLAYERS: # Waiting for players
                waiting_players(win, win_w, win_h)
            case SCENE_COUNTDOWN: # Countdown before start
                pass
            case SCENE_GAME_ONGOING: # Game ongoing
                game_ongoing(WIN, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, MID_LINE_HEIGHT_RATIO, win_text, won)
            case SCENE_GAME_END: # Game finished
                pass
        """
        #run = False
    pygame.quit()

if __name__ == '__main__':
    main()
