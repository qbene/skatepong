#!usr/bin/python3

#------------------------------------------------------------------------------
# IMPORTS
#------------------------------------------------------------------------------

import sys
import pygame
import math
import random
import time
from mpu6050 import mpu6050
from skatepong.gyro import Gyro_one_axis

#------------------------------------------------------------------------------
# DEVELOPMENT VARIABLES
#------------------------------------------------------------------------------

DEV_MODE = True # Used to avoid full screen display mode during dev phase.

#------------------------------------------------------------------------------
# INITIALIZATION
#------------------------------------------------------------------------------

#PYGAME_BLEND_ALPHA_SDL2 = 1
pygame.init()

#------------------------------------------------------------------------------
# CONSTANTS THAT CAN BE ADJUSTED
#------------------------------------------------------------------------------

# Game parameters
WINNING_SCORE = 10 # Number of goals to win the game
BALL_ANGLE_MAX = 60 # Max angle after paddle collision (degrees) [30-75]
VELOCITY_ANGLE_FACTOR = 2 # Allows to increase ball velocity when angle (longer distance) [2 - 3]
# Delays
DELAY_INACT_PLAYER = 5 # Delay after which a player is considered inactive (s)
DELAY_COUNTDOWN = 3 # Countdown initial time before starting the game (s)
DELAY_GAME_END = 60 # Delay after game ends (s)
DELAY_BEF_PAD_CALIB = 10 # Delay before paddles calibration starts (s)
DELAY_AFT_PAD_CALIB = 10 # Delay after paddles calibration is done (s)
# Technical parameters
FPS = 30 # Max number of frames per second
GYRO_SENSITIVITY = mpu6050.GYRO_RANGE_500DEG
"""Possible values:
mpu6050.GYRO_RANGE_250DEG
mpu6050.GYRO_RANGE_500DEG
mpu6050.GYRO_RANGE_1000DEG
mpu6050.GYRO_RANGE_2000DEG
"""
# Sizes ([indicates recommended values])
WELCOME_RADIUS_RATIO = 0.25 # Ratio to screen height [0.1 - 0.5]
PAD_WIDTH_RATIO = 0.015 # Ratio to screen width [0.005 - 0.1]
PAD_HEIGHT_RATIO = 0.2 # Ratio to screen height [0.05 - 0.2]
PAD_X_OFFSET_RATIO = 0.02 # Ratio to screen width [0.01 - 0.02] - Frame offset
BALL_RADIUS_RATIO = 0.02 # Ratio to min screen width/height [0.01 - 0.04]
PAD_FLAT_BOUNCE_RATIO = 0.01 # # Ratio to screen width [0.005 - 0.02]
BALL_V_RATIO = 0.025 # Ratio to min screen width [0.005 - 0.025]
MID_LINE_HEIGHT_RATIO = 0.05 # Ratio to screen height [ideally 1/x -> int]
MID_LINE_WIDTH_RATIO = 0.006 # Ratio to screen width [0.005 - 0.01]
SCORE_Y_OFFSET_RATIO = 0.02 # Ratio to screen height (to set score vertically)
CENTER_CROSS_MULTIPLIER = 3 # To be multiplied with MID_LINE_WIDTH_RATIO [2 - 5]
# Texts
FONT_NAME = "comicsans" # Font used for texts
FONT_RATIO_0_05 = 0.05 # Ratio to screen height
FONT_RATIO_0_1 = 0.1 # Ratio to screen height
FONT_RATIO_0_15 = 0.15 # Ratio to screen height
FONT_RATIO_0_2 = 0.2 # Ratio to screen height

#------------------------------------------------------------------------------
# CONSTANTS
#------------------------------------------------------------------------------

# Game scenes (used to navigate between one another) :
SCENE_WELCOME = 0
SCENE_WAITING_PLAYERS = 1
SCENE_COUNTDOWN = 2
SCENE_GAME_ONGOING = 3
SCENE_GAME_END = 4
SCENE_CALIBRATION = 5

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (127, 127, 127)

#------------------------------------------------------------------------------
# CODE
#------------------------------------------------------------------------------

class Paddle:
    COLOR = WHITE

    def __init__(self, x, y, w, h, gyro):
        self.x = self.original_x = x # Top left hand corner - horizontal axis
        self.y = self.original_y = y # Top left hand corner - vertical axis
        self.w = w # Paddle width (in pixels)
        self.h = h # Paddle height (in pixels)
        self.gyro = gyro # Gyroscope that controls the paddle displacement

    def draw(self, win):
        pygame.draw.rect(win, self.COLOR, (self.x, self.y, self.w, self.h))

    def compute_pad_velocity(self):
        
        # Handling gyroscope i2c deconnection
        try:
            gyro_raw = self.gyro.get_data()
        except IOError:
            print("i2c communication with gyroscope failed")
            self.gyro.error = True
            self.gyro.ready_for_reinit = False
            vy = 0
        # Computing pad velocity if gyroscope is connected
        else:
            self.gyro.ready_for_reinit = True
            #gyro_raw = self.gyro.get_data()
            gyro_calib = gyro_raw - self.gyro.offset
            if gyro_calib < -200:
                vy = -30
            elif  (gyro_calib >= -200 and gyro_calib < -50):
                vy = -20
            elif (gyro_calib >= -50 and gyro_calib < -10): 
                vy = -10    
            elif (gyro_calib >= -10 and gyro_calib < 10):
                vy = 0
            elif (gyro_calib >= 10 and gyro_calib < 50):
                vy = 10
            elif (gyro_calib >= 50 and gyro_calib < 200):
                vy = 20
            elif gyro_calib >= 200:
                vy = 30
            else:
                vy = 5
            #print("Gyro (" + self.gyro.axis + " axis) => Raw data :", str(round(gyro_raw,2)), "/ Calibrated data :", str(round(gyro_calib,2)))
        return vy

    def move(self, win_h):
        vy_pad = self.compute_pad_velocity()        
        if self.y + vy_pad < 0:
            self.y = 0
        elif self.y + self.h + vy_pad > win_h:
            self.y = win_h - self.h
        else:
            self.y += vy_pad
        return vy_pad
    
    def move_to_center(self, win_h):
        self.y = (win_h - self.h) // 2

class Ball:
    COLOR = WHITE

    def __init__(self, x, y, r, vx, vy):
        self.x = self.original_x = x # Ball center - horizontal axis
        self.y = self.original_y = y # Ball center - vertical axis
        self.vx = self.original_vx = vx # Ball velocity - horizontal axis (px)
        self.vy = self.original_vy = vy # Ball velocity - vertical axis (px)
        self.r = r # Ball radius (px)

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

def create_window(dev_mode = False):
    """
    Initializes game window, and adjusts size to display resolution.
    """
    #disp_w, disp_h = pygame.display.get_desktop_sizes()
    disp_w = pygame.display.Info().current_w # Display width (in pixels)
    disp_h = pygame.display.Info().current_h # Display height (in pixels)
    if dev_mode == True:
        WIN = pygame.display.set_mode([disp_w, disp_h-100])
        pygame.display.set_caption("Skatepong")         
    else:
        WIN = pygame.display.set_mode([0, 0], pygame.FULLSCREEN)
    win_w , win_h = pygame.display.get_surface().get_size()
    return WIN, win_w, win_h # Capital letters for WIN to identify main window

def draw_text(win, font_name, font_size, text, center_x, center_y, color, bg_color = None):
    """
    Draws text on a surface, text center serving as position reference.
    
    bg_color = text background color
    """
    font = pygame.font.SysFont(font_name, font_size)
    text_surf = font.render(text, True, color, bg_color)
    text_rect = text_surf.get_rect()
    text_rect.center = (center_x, center_y)
    win.blit(text_surf, text_rect)

def draw_game_objects(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, draw_pads = False, draw_ball = False, draw_scores = False, draw_line = False):
    """
    Draws on a surface the desired game elements (pads / ball / scores)
    
    Note : Each scene of the game do not require every single game object 
    """
    if draw_scores == True:
        draw_text(win, FONT_NAME, int(FONT_RATIO_0_1 * win_h), str(l_score), win_w // 4, int(FONT_RATIO_0_1 * win_h), WHITE)
        draw_text(win, FONT_NAME, int(FONT_RATIO_0_1 * win_h), str(r_score), (win_w * 3) // 4, int(FONT_RATIO_0_1 * win_h), WHITE)
    if draw_line == True:        
        draw_mid_line(win, win_w, win_h, dashed = False)
    if draw_pads == True:
        l_pad.draw(win)
        r_pad.draw(win)
    if draw_ball == True:
        ball.draw(win)

def welcome(win, win_w, win_h, game_status, clock):
    """
    Displays a welcome screen for a certain duration at program start.
    """
    start_time = time.time()
    
    # Managing display:
    win.fill(BLACK)
    pygame.draw.circle(win, WHITE, (win_w//2, win_h//2), WELCOME_RADIUS_RATIO * win_h)
    draw_text(win, FONT_NAME, int(FONT_RATIO_0_1 * win_h), "SKATEPONG", win_w // 2, win_h // 2, BLACK)
    pygame.display.update()
    
    current_time = time.time()
    while current_time - start_time < 3:

        clock.tick(FPS)

        # Closing game window if red cross clicked or ESCAPE pressed:
        keys = pygame.key.get_pressed()
        game_status = check_user_inputs(keys, game_status)
        #check_exit_game(keys)
        # Updating current time
        current_time = time.time()
        
    game_status = SCENE_WAITING_PLAYERS
    return game_status

def wait_players(win, win_w, win_h, l_pad, r_pad, l_gyro, r_gyro, ball, l_score, r_score, game_status, clock):
    """
    Enters 'standby' state before detection of actives players on each skateboard.
    
    Note : paddles active.
    """
    moving_time = time.time()
    current_time = time.time()
    left_player_ready = False
    right_player_ready = False
    ball.reset()
    
    while ((left_player_ready == False) or (right_player_ready == False)):

        clock.tick(FPS)

        # Closing game window if red cross clicked or ESCAPE pressed:        
        keys = pygame.key.get_pressed()
        game_status = check_user_inputs(keys, game_status)
        #check_exit_game(keys)

        # Reinitializing gyro if necessary (after i2c deconnection)
        reinitialize_gyro_if_needed(l_gyro, r_gyro)

        # Going to paddles calibration scene upon user request:
        #game_status = check_for_pads_calib(keys, game_status)
        if game_status == SCENE_CALIBRATION:
            return game_status

        if ((left_player_ready == False) and (right_player_ready == False)):
            message = "WAITING FOR PLAYERS"
        elif ((left_player_ready == False) and (right_player_ready == True)):
            message = "LEFT PLAYER MISSING"
        elif ((left_player_ready == True) and (right_player_ready == False)):
            message = "RIGHT PLAYER MISSING"
        
        # Managing display:
        win.fill(BLACK)
        draw_text(win, FONT_NAME, int(FONT_RATIO_0_1 * win_h), message, win_w // 2, win_h // 4, WHITE)
        draw_text(win, FONT_NAME, int(FONT_RATIO_0_05 * win_h), "MOVE SKATES TO START", win_w // 2, (win_h * 3) // 4, WHITE)
        draw_game_objects(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, draw_pads = True, draw_ball = True, draw_scores = False, draw_line = False)
        pygame.display.update()
        
        vy_l_pad = l_pad.move(win_h)
        vy_r_pad = r_pad.move(win_h)
        if abs(vy_l_pad) > 25:
            left_player_ready = True
            moving_time = time.time()
        if abs(vy_r_pad) > 25:
            right_player_ready = True
            moving_time = time.time()

        current_time = time.time()

        if current_time - moving_time > DELAY_INACT_PLAYER:
            left_player_ready = 0
            right_player_ready = 0

    game_status = SCENE_COUNTDOWN
    return game_status

def countdown(win, win_w, win_h, l_pad, r_pad, l_gyro, r_gyro, ball, l_score, r_score, game_status, clock):
    """
    Starts a countdown before the game actually begins.

    Note : paddles active.
    """
    start_time = time.time()
    current_time = time.time()
    
    while current_time - start_time < DELAY_COUNTDOWN:
        
        clock.tick(FPS)
        
        # Closing game window if red cross clicked or ESCAPE pressed:
        keys = pygame.key.get_pressed()
        #check_exit_game(keys)
        game_status = check_user_inputs(keys, game_status)
        # Reinitializing gyro if necessary (after i2c deconnection)
        reinitialize_gyro_if_needed(l_gyro, r_gyro)

        time_before_start = DELAY_COUNTDOWN - int(current_time - start_time) 

        vy_l_pad = l_pad.move(win_h)
        vy_r_pad = r_pad.move(win_h)

        # Managing display:
        win.fill(BLACK)
        draw_text(win, FONT_NAME, int(FONT_RATIO_0_2 * win_h), str(time_before_start), win_w // 2, win_h // 4, WHITE)
        draw_game_objects(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, draw_pads = True, draw_ball = True, draw_scores = False, draw_line = False)
        pygame.display.update()

        current_time = time.time()
   
    game_status = SCENE_GAME_ONGOING
    return game_status

def game_ongoing(win, l_pad, r_pad, ball, win_w, win_h, MID_LINE_HEIGHT_RATIO, l_gyro, r_gyro, ball_vx_straight, game_status, clock):
    """
    Controls the game itself.
    
    1 point each time a player shoots the ball inside the oponent's zone.
    """
    run = True    
    l_score = 0
    r_score = 0
    goal_to_be = False
    random_number = random.randint(1, 2)
    
    if random_number == 1:
        ball.vx =  ball_vx_straight # Ball going to the right at start
    else:
        ball.vx =  -ball_vx_straight # Ball going to the left at start
        
    while (l_score < WINNING_SCORE and r_score < WINNING_SCORE):

        clock.tick(FPS)
        # Closing game window if red cross clicked or ESCAPE pressed:
        keys = pygame.key.get_pressed()
        game_status = check_user_inputs(keys, game_status)
        #check_exit_game(keys)
        
        # Going to paddles calibration scene upon user request:
        #game_status = check_for_pads_calib(keys, game_status)
        if game_status == SCENE_CALIBRATION  or game_status == SCENE_WAITING_PLAYERS:
            return game_status, l_score, r_score
        
        # Reinitializing gyro if necessary (after i2c deconnection)
        reinitialize_gyro_if_needed(l_gyro, r_gyro)

        vy_l_pad = l_pad.move(win_h)
        vy_r_pad = r_pad.move(win_h)

        ball.move()
        goal_to_be = handle_collision(ball, l_pad, r_pad, win_w, win_h, ball_vx_straight, goal_to_be)
        l_score, r_score, goal_to_be = detect_goal(ball, l_score, r_score, win_w, ball_vx_straight, goal_to_be)        

        # Managing display:
        win.fill(BLACK)
        draw_game_objects(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, draw_pads = True, draw_ball = True, draw_scores = True, draw_line = True)
        pygame.display.update()   

        if (l_score >= WINNING_SCORE or r_score >= WINNING_SCORE):
            game_status = SCENE_GAME_END
            break
         
    return game_status, l_score, r_score

def game_end(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, mid_line_h_ratio, l_gyro, r_gyro, game_status, clock):
    """
    Announces the winner, with final score.
    
    Note : paddles active.
    """
    start_time = time.time()
    current_time = time.time()
    ball.reset()
    
    if (l_score == WINNING_SCORE):
        message = "LEFT PLAYER WON"
    else:
        message = "RIGHT PLAYER WON"
    
    while current_time - start_time < DELAY_GAME_END:
        
        clock.tick(FPS)

        # Closing game window if red cross clicked or ESCAPE pressed:
        keys = pygame.key.get_pressed()
        game_status = check_user_inputs(keys, game_status)
        #check_exit_game(keys)

        # Reinitializing gyro if necessary (after i2c deconnection)
        reinitialize_gyro_if_needed(l_gyro, r_gyro)

        vy_l_pad = l_pad.move(win_h)
        vy_r_pad = r_pad.move(win_h)

        # Managing display:
        win.fill(BLACK)
        draw_game_objects(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, draw_pads = True, draw_ball = False, draw_scores = True, draw_line = False)
        draw_text(win, FONT_NAME, int(FONT_RATIO_0_15 * win_h), message, win_w // 2, win_h // 2, WHITE)
        pygame.display.update()

        current_time = time.time()
    
    game_status = SCENE_WAITING_PLAYERS 
    return game_status        

def calibrate_pads(win, win_w, win_h, l_pad, r_pad, l_gyro, r_gyro, ball, l_score, r_score, game_status, clock):
    """
    Handles the paddles calibration.
    
    - A first screen indicates that calibration will take place after countdown
    => Indic
    - A second screen allows user to test the new calibration for a given time
    - Then, going back to the scene "waiting for players".
    """
    start_time = time.time()
    current_time = time.time()
    ball.reset()
    
    # Announcing that calibration is about to take place
    while current_time - start_time < DELAY_BEF_PAD_CALIB:

        clock.tick(FPS)

        # Closing game window if red cross clicked or ESCAPE pressed:
        keys = pygame.key.get_pressed()
        #check_exit_game(keys)
        game_status = check_user_inputs(keys, game_status)

        # Reinitializing gyro if necessary (after i2c deconnection)
        reinitialize_gyro_if_needed(l_gyro, r_gyro)

        time_before_start = DELAY_BEF_PAD_CALIB - int(current_time - start_time)
       
        vy_l_pad = l_pad.move(win_h)
        vy_r_pad = r_pad.move(win_h)
        
        # Managing display:
        win.fill(BLACK)
        draw_text(win, FONT_NAME, int(FONT_RATIO_0_1 * win_h), "CALIBRATION IS ABOUT TO START", win_w // 2, win_h // 4, WHITE)
        draw_text(win, FONT_NAME, int(FONT_RATIO_0_05 * win_h), "GET SKATES STEADY IN THEIR NEUTRAL POSITIONS", win_w // 2, (win_h * 3) // 4, WHITE)
        draw_text(win, FONT_NAME, int(FONT_RATIO_0_2 * win_h), str(time_before_start), win_w // 2, win_h // 2, WHITE)
        draw_game_objects(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, draw_pads = True, draw_ball = False, draw_scores = False, draw_line = False)
        pygame.display.update()
        
        current_time = time.time()
    
    clock.tick(FPS)
    
    # Managing display:
    win.fill(BLACK)
    draw_text(win, FONT_NAME, int(FONT_RATIO_0_1 * win_h), "CALIBRATION ONGOING...", win_w // 2, win_h // 4, WHITE)
    draw_text(win, FONT_NAME, int(FONT_RATIO_0_05 * win_h), "GET SKATES STEADY IN THEIR NEUTRAL POSITIONS", win_w // 2, (win_h * 3) // 4, WHITE)
    draw_game_objects(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, draw_pads = True, draw_ball = False, draw_scores = False)
    pygame.display.update()
    # Gyroscope offset measurement:
    l_gyro.offset = l_gyro.measure_gyro_offset()
    r_gyro.offset = r_gyro.measure_gyro_offset()    
    # Paddles calibration:
    l_pad.move_to_center(win_h)
    r_pad.move_to_center(win_h)


    # Annoucing that calibration has been performed :
    start_time = time.time()
    current_time = time.time()

    while current_time - start_time < DELAY_AFT_PAD_CALIB:

        clock.tick(FPS)

        # Closing game window if red cross clicked or ESCAPE pressed:
        keys = pygame.key.get_pressed()
        #check_exit_game(keys)
        game_status = check_user_inputs(keys, game_status)

        # Reinitializing gyro if necessary (after i2c deconnection)
        reinitialize_gyro_if_needed(l_gyro, r_gyro)

        time_before_start = DELAY_AFT_PAD_CALIB - int(current_time - start_time)

        vy_l_pad = l_pad.move(win_h)
        vy_r_pad = r_pad.move(win_h)
        
        # Managing display:
        win.fill(BLACK)
        draw_text(win, FONT_NAME, int(FONT_RATIO_0_1 * win_h), "CALIBRATION DONE", win_w // 2, win_h // 4, WHITE)
        draw_text(win, FONT_NAME, int(FONT_RATIO_0_05 * win_h), "MOVE SKATES TO TEST CALIBRATION", win_w // 2, (win_h * 3) // 4, WHITE)
        draw_text(win, FONT_NAME, int(FONT_RATIO_0_2 * win_h), str(time_before_start), win_w // 2, win_h // 2, WHITE)
        draw_game_objects(win, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, draw_pads = True, draw_ball = False, draw_scores = False)
        pygame.display.update()
        
        current_time = time.time()
    
    game_status = SCENE_WAITING_PLAYERS

    return game_status

def compute_elements_sizes(win_w, win_h):
    """
    Computes game elements sizes/speeds based on display resolution.
    """
    pad_w = int(win_w*PAD_WIDTH_RATIO)
    pad_h = int(win_h*PAD_HEIGHT_RATIO)
    ball_r = min(int(win_w*BALL_RADIUS_RATIO), int(win_h*BALL_RADIUS_RATIO))
    ball_vx_straight = int(BALL_V_RATIO*win_w)
    return pad_w, pad_h, ball_r, ball_vx_straight

def draw_mid_line(win, win_w, win_h, dashed = False):
    """
    Draws vertical line in the middle of the screen.
    """
    
    if dashed == True:
        # Dashed line
        dash_w = round(win_w * MID_LINE_WIDTH_RATIO)
        dash_h = round(win_h * MID_LINE_HEIGHT_RATIO)    
        nb_iterations = round(1 / MID_LINE_HEIGHT_RATIO)
        if nb_iterations % 2 == 0:
            for i in range(0, nb_iterations):
                if i % 2 == 1:
                    continue
                pygame.draw.rect(win, WHITE, ((win_w - MID_LINE_WIDTH_RATIO) // 2, i * dash_h + dash_h // 2, dash_w, dash_h))
        else:
            for i in range(0, nb_iterations):
                if i % 2 == 1:
                    continue
                pygame.draw.rect(win, WHITE, ((win_w - MID_LINE_WIDTH_RATIO) // 2, i * dash_h, dash_w, dash_h))
            
    else:
    # Straight line, with small center cross
        line_w = int(win_w * MID_LINE_WIDTH_RATIO)
        pygame.draw.rect(win, WHITE, ((win_w - line_w) // 2, 0, line_w, win_h))
        pygame.draw.rect(win, WHITE, ((win_w - CENTER_CROSS_MULTIPLIER * line_w) // 2, (win_h - line_w) // 2, CENTER_CROSS_MULTIPLIER * line_w, line_w))

def handle_top_bottom_collision(ball, win_h):
    """ Collision with top or bottom wall"""
    # Bottom wall
    if (ball.y + ball.r >= win_h):
        y_mod = win_h - ball.r  
    # Top wall
    elif (ball.y - ball.r <= 0):
        y_mod = ball.r
    x_mod = int(ball.x - ((ball.vx * (ball.y - y_mod)) / ball.vy))
    ball.x = x_mod
    ball.y = y_mod 
    ball.vy *= -1
    
def handle_left_collision(ball, l_pad, r_pad, win_w, ball_vx_straight, goal_to_be):
    #goal_to_be = False
    if ball.x - ball.r <= l_pad.x + l_pad.w:
        x_mod = l_pad.original_x + l_pad.w + ball.r
        y_mod = int(ball.y - (ball.x - x_mod) * ball.vy / ball.vx)            
        # If ball colliding with paddle:
        if y_mod >= l_pad.y and y_mod <= l_pad.y + l_pad.h:            
            y_pad_mid = l_pad.y + l_pad.h // 2
            # Bounce angle calculation
            if (y_mod < (y_pad_mid + PAD_FLAT_BOUNCE_RATIO * win_w) and y_mod > (y_pad_mid - PAD_FLAT_BOUNCE_RATIO * win_w)):
                ball.vx = ball_vx_straight                    
            else:
                angle = round((y_mod - y_pad_mid) / (l_pad.h / 2) * BALL_ANGLE_MAX)
                # Constant speed
                #vx = round(math.cos(math.radians(angle)) * BALL_V_RATIO * win_w)
                #vy = round(math.sin(math.radians(angle)) * BALL_V_RATIO * win_w)
                # Faster when there is an angle to compensate for longer distance
                vx = round(math.cos(math.radians(angle)) * ball_vx_straight) * (VELOCITY_ANGLE_FACTOR - math.cos(math.radians(angle)))
                vy = round(math.sin(math.radians(angle)) * ball_vx_straight) * (VELOCITY_ANGLE_FACTOR - math.cos(math.radians(angle)))                    
                ball.vy = vy
                ball.vx = vx
            ball.x = x_mod
            ball.y = y_mod
        else:
            goal_to_be = True
    return goal_to_be

def handle_right_collision(ball, l_pad, r_pad, win_w, ball_vx_straight, goal_to_be):
    #goal_to_be = False
    if ball.x + ball.r >= r_pad.x:
        x_mod = r_pad.original_x - ball.r
        y_mod = int(ball.y - (ball.x - x_mod) * ball.vy / ball.vx)            
        # If ball colliding with paddle:
        if y_mod >= r_pad.y and y_mod <= r_pad.y + r_pad.h:            
            y_pad_mid = r_pad.y + r_pad.h // 2
            # Bounce angle calculation
            if (y_mod < (y_pad_mid + PAD_FLAT_BOUNCE_RATIO * win_w) and y_mod > (y_pad_mid - PAD_FLAT_BOUNCE_RATIO * win_w)):
                ball.vx = -ball_vx_straight
            else:
                angle = round((y_mod - y_pad_mid) / (r_pad.h / 2) * BALL_ANGLE_MAX)
                #angle = round((ball.y - y_pad_mid) / (r_pad.h / 2) * BALL_ANGLE_MAX)
                # Constant speed
                #vx = round(math.cos(math.radians(angle)) * BALL_V_RATIO * win_w)
                #vy = round(math.sin(math.radians(angle)) * BALL_V_RATIO * win_w)
                # Faster when there is an angle to compensate for longer distance
                vx = round(math.cos(math.radians(angle)) * ball_vx_straight) * (VELOCITY_ANGLE_FACTOR - math.cos(math.radians(angle)))
                vy = round(math.sin(math.radians(angle)) * ball_vx_straight) * (VELOCITY_ANGLE_FACTOR - math.cos(math.radians(angle)))                    
                ball.vy = vy
                ball.vx = -vx
            ball.x = x_mod
            ball.y = y_mod
        else:
            goal_to_be = True
    return goal_to_be

def check_collision(ball, l_pad,r_pad, win_h):
    
    bottom_collision = False
    top_collision = False
    left_collision = False
    right_collision = False
    if (ball.y + ball.r >= win_h):
        bottom_collision = True
    elif (ball.y - ball.r <= 0):
        top_collision = True
    if ((ball.vx < 0) and (ball.x - ball.r <= l_pad.x + l_pad.w)):
        left_collision = True
    elif ((ball.vx > 0) and (ball.x + ball.r >= r_pad.x)):
        right_collision = True
            
    return bottom_collision, top_collision, left_collision, right_collision

def handle_collision(ball, l_pad,r_pad, win_w, win_h, ball_vx_straight, goal_to_be):
    """
    Handles ball collision with paddles and top/bottom walls.
    
    - Calculates ball horizontal and vertical velocities.
    - Calculates ball angle after collision with paddle depending
    ...on the collision point.
    """
    
    bottom_collision, top_collision, left_collision, right_collision = check_collision(ball, l_pad,r_pad, win_h)
    
    # Left paddle possible collision case
    if (left_collision and goal_to_be == False):
        # Ball also colliding with bottom wall
        if bottom_collision:
            y_mod = win_h - ball.r  
        # Ball also colliding with top wall
        elif top_collision:
            y_mod = ball.r
        # Neef to determine which collision would arrive first: top/bottom wall or left paddle ?
        if bottom_collision or top_collision:
            x_mod = int(ball.x - ((ball.vx * (ball.y - y_mod)) / ball.vy))
            # Top/bottom wall collision first :
            if x_mod > (l_pad.x + l_pad.w):
                handle_top_bottom_collision(ball, win_h)
            # Left padlle collision would arrive first if paddle well positioned
            else:
                goal_to_be = handle_left_collision(ball, l_pad, r_pad, win_w, ball_vx_straight, goal_to_be)
                # If left paddle not well positioned, a goal will hapen, but still needs to manage boucing on top/bottom wall
                if goal_to_be:
                    handle_top_bottom_collision(ball, win_h)
        # Left paddle collision possible and no collision with top/bottom walls
        else:
            goal_to_be = handle_left_collision(ball, l_pad, r_pad, win_w, ball_vx_straight, goal_to_be)

    # Right paddle possible collision case
    elif (right_collision and goal_to_be == False):
        # Ball also colliding with bottom wall
        if bottom_collision:
            y_mod = win_h - ball.r  
        # Ball also colliding with top wall
        elif top_collision:
            y_mod = ball.r
        # Neef to determine which collision would arrive first: top/bottom wall or right paddle ?
        if bottom_collision or top_collision:
            x_mod = int(ball.x - ((ball.vx * (ball.y - y_mod)) / ball.vy))
            # Top/bottom wall collision first :
            if x_mod < r_pad.x:
                handle_top_bottom_collision(ball, win_h)
            # Right padlle collision would arrive first if paddle well positioned
            else:        
                goal_to_be = handle_right_collision(ball, l_pad, r_pad, win_w, ball_vx_straight, goal_to_be)
                # If right paddle not well positioned, a goal will hapen, but still needs to manage boucing on top/bottom wall
                if goal_to_be:
                    handle_top_bottom_collision(ball, win_h)
        # Right paddle collision possible and no collision with top/bottom walls
        else:
            goal_to_be = handle_right_collision(ball, l_pad, r_pad, win_w, ball_vx_straight, goal_to_be)
    
    # No possible collision with paddles, but just with top or bottom walls
    elif (bottom_collision or top_collision):
        handle_top_bottom_collision(ball, win_h)

    return goal_to_be

def detect_goal(ball, l_score, r_score, win_w, ball_vx_straight, goal_to_be):
    """
    Handles when goals are scored, and updates scores.
    """
    if ball.x < 0:
        r_score += 1
        vx_direction_after_goal = 1
    elif ball.x > win_w:
        l_score += 1
        vx_direction_after_goal = -1
    if ball.x < 0 or ball.x > win_w:
        ball.reset()
        ball.vx = ball_vx_straight * vx_direction_after_goal
        goal_to_be = False
    
    return l_score, r_score, goal_to_be

def check_exit_game(keys):
    """
    Exits the game when user clicks on the red cross or presses ESCAPE. 
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
    if keys[pygame.K_ESCAPE]:
        sys.exit()
        
def check_for_pads_calib(keys, game_status):
    """
    Determines if user has requested paddles calibration.
    """
    if keys[pygame.K_p]:
        game_status = SCENE_CALIBRATION
    elif keys[pygame.K_s]:
        game_status = SCENE_WAITING_PLAYERS
    return game_status
        
def check_user_inputs(keys, game_status):
    """
    Check if user has pressed any button. 
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
    if keys[pygame.K_ESCAPE]:
        sys.exit()
    elif keys[pygame.K_c]:
        game_status = SCENE_CALIBRATION
    elif keys[pygame.K_s]:
        game_status = SCENE_WAITING_PLAYERS
    return game_status    


def initialize_game(win_w, win_h, l_gyro, r_gyro):
    """
    Creates game objects at program start.
    """
    # Creating game objects:
    # - Both paddles are centered vertically
    # - The ball is created in the center of the display, with a horizontal velovity
    mid_line_h = round(MID_LINE_HEIGHT_RATIO *  win_h)
    pad_w, pad_h, ball_r, ball_vx_straight = compute_elements_sizes(win_w, win_h)
    l_pad_x = PAD_X_OFFSET_RATIO * win_w
    r_pad_x = win_w - PAD_X_OFFSET_RATIO*win_w - pad_w
    pad_y = (win_h - pad_h) // 2
    l_pad = Paddle(l_pad_x, pad_y, pad_w, pad_h, l_gyro)
    r_pad = Paddle(r_pad_x, pad_y, pad_w, pad_h, r_gyro)
    #ball = Ball(win_w // 2, win_h // 2, ball_r, 0, 0)
    # DEV ONLY
    ball = Ball(win_w // 2, win_h // 2, ball_r, 0, 0)
    angle = round(math.atan((win_h/2)/((win_w/2)-l_pad.w-l_pad.original_x)), 3)
    Y = win_h/2
    X = (win_w/2)-l_pad.w-l_pad.original_x-ball.r
    print("angle:", angle)
    print("(X,Y) :", X, Y)
    print("X/Y :", X/Y)
    #round(math.cos(math.radians(angle))
    # Initializing game variables:
    l_score = 0
    r_score = 0
    return l_pad, r_pad, ball, mid_line_h, l_score, r_score, ball_vx_straight


def reinitialize_gyro_if_needed(l_gyro, r_gyro):
    """
    Recreate gyroscopes objects following deconnections.
    """
    if l_gyro.error == True and l_gyro.ready_for_reinit == True:
        try:
            l_gyro = Gyro_one_axis(Gyro_one_axis.I2C_ADDRESS_1, 'y', GYRO_SENSITIVITY)
        except IOError:
            pass
    if r_gyro.error == True and r_gyro.ready_for_reinit == True:
        try:
            r_gyro = Gyro_one_axis(Gyro_one_axis.I2C_ADDRESS_2, 'y', GYRO_SENSITIVITY)
        except IOError:
            pass
    return l_gyro, r_gyro

def test_gyroscope_connection(win, win_w, win_h):
    """
    Game does not start if both skateboards are not connected at startup.
    """
    
    both_gyros_connected = False
    while both_gyros_connected != True:
        
        try:
            l_gyro = Gyro_one_axis(Gyro_one_axis.I2C_ADDRESS_1, 'y', GYRO_SENSITIVITY)
        except IOError:
            l_gyro_connected = False
        else:
            l_gyro_connected = True
        
        try:
            r_gyro = Gyro_one_axis(Gyro_one_axis.I2C_ADDRESS_2, 'y', GYRO_SENSITIVITY)
        except IOError:
            r_gyro_connected = False
        else:
            r_gyro_connected = True
        
        if l_gyro_connected and r_gyro_connected:
            both_gyros_connected = True
        
        if both_gyros_connected == False:
            # Managing display:
            win.fill(BLACK)
            if l_gyro_connected == True and r_gyro_connected == False:
                message = "Right skateboard NOT connected"
            elif l_gyro_connected == False and r_gyro_connected == True:
                message = "Left skateboard NOT connected"
            else:
                message = "Please connect skateboards"
            draw_text(win, FONT_NAME, int(FONT_RATIO_0_1 * win_h), message, win_w // 2, win_h // 2, WHITE)
            pygame.display.update()
    
    return l_gyro, r_gyro

def main():
    """
    Skatepong is a pong game for 2 players, with real skateboards as actuators.
    
    - Objective : 1 point each time a player shoots the ball inside the oponent's zone.
    - End : Game stops after a given number of points has been reached.
    - The 2 paddles are controlled independently based on the movements detected
    by a gyroscope mounted under each skateboard.
    - Scenes description :
        SCENE_WELCOME : Splash screen at game start.
        SCENE_WAITING_PLAYERS : Waiting for motion on both skates.
        SCENE_COUNTDOWN : Countdown before the game actually starts.
        SCENE_GAME_ONGOING : Game itself.
        SCENE_GAME_END : Announces the winner, with final score.
        SCENE_CALIBRATION : Allows to calibrate paddles when requested by user.
    """
    clock = pygame.time.Clock()
    # Creating game window:
    WIN, win_w, win_h = create_window(DEV_MODE)
    # Creating the 2 gyroscopes objects:

    # Initializing game:
    game_status = 0
    game_status = welcome(WIN, win_w, win_h, game_status, clock)
    l_gyro, r_gyro = test_gyroscope_connection(WIN, win_w, win_h)
    l_pad, r_pad, ball, mid_line_h, l_score, r_score, ball_vx_straight = initialize_game(win_w, win_h, l_gyro, r_gyro)

    while True:

        #if game_status == SCENE_WELCOME:
        #    game_status = welcome(WIN, win_w, win_h, game_status, clock)
        if game_status == SCENE_WAITING_PLAYERS: # Waiting for players
            game_status = wait_players(WIN, win_w, win_h, l_pad, r_pad, l_gyro, r_gyro, ball, l_score, r_score, game_status, clock)
        elif game_status == SCENE_COUNTDOWN: # Countdown before start
            game_status = countdown(WIN, win_w, win_h, l_pad, r_pad, l_gyro, r_gyro, ball, l_score, r_score, game_status, clock)
        elif game_status == SCENE_GAME_ONGOING: # Game ongoing
            print ("START GAME")
            ball.vx = ball_vx_straight
            game_status, l_score, r_score = game_ongoing(WIN, l_pad, r_pad, ball, win_w, win_h, MID_LINE_HEIGHT_RATIO, l_gyro, r_gyro, ball_vx_straight, game_status, clock)
        elif game_status == SCENE_GAME_END: # Game finished
            game_status = game_end(WIN, l_pad, r_pad, ball, l_score, r_score, win_w, win_h, MID_LINE_HEIGHT_RATIO, l_gyro, r_gyro, game_status, clock)
        elif game_status == SCENE_CALIBRATION: # Paddle/Gyroscopes calibration
            game_status = calibrate_pads(WIN, win_w, win_h, l_pad, r_pad, l_gyro, r_gyro, ball, l_score, r_score, game_status, clock)
            
if __name__ == '__main__':
    main()
