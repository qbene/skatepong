#!usr/bin/python3

#-----------------------------------------------------------------------
# IMPORTS
#-----------------------------------------------------------------------

import pygame
#from pygame.locals import *

#-----------------------------------------------------------------------
# CODE
#-----------------------------------------------------------------------

class Ball():
    """
    Defines the ball for skatepong game.
    """
    def __init__(self, win, x, y, r, color, vx_straight, vx = 0, vy=0):
        self.win = win
        self.original_x = x # Ball center on the x axis
        self.original_y = y # Ball center on the y axis
        self.color = color
        self.r = r # Ball radius (px)
        self.vx_straight = vx_straight # Ball velocity when horiz (px)
        self.vx = self.original_vx = vx # Ball velocity - x axis (px)
        self.vy = self.original_vy = vy # Ball vertical - y axis (px)
        self.rect = pygame.Rect(x - r, y - r, 2 * r, 2 * r)

    def draw(self):
        """
        Draws the ball as a circle.
        """
        pygame.draw.circle(self.win,self.color,self.rect.center,self.r)
        
    def move(self):
        """
        Moves the ball ignoring collisions.
        """
        self.rect.centerx += self.vx
        self.rect.centery += self.vy
    
    def reset(self):
        """
        Reset ball to initial state (position / speed).
        """
        self.rect.center = (self.original_x, self.original_y)
        self.vx = self.original_vx
        self.vy = self.original_vy
        
class Paddle():

    """
    Defines the paddles properties for skatepong game.
    """

    #VY_PAD_RATIO = 0.02 # Ratio to screen height
    
    def __init__(self, win, win_h, x, y, w, h, color, gyro):
        self.win = win # Surface to draw
        self.win_h = win_h # Surface height (px)
        self.x = self.original_x = x # Top left - horizontal axis
        self.y = self.original_y = y # Top left - vertical axis
        self.w = w # Paddle width (px)
        self.h = h # Paddle height (px)
        self.color = color # Paddle color
        self.gyro = gyro # Gyroscope controlling paddle displacement
        self.rect = pygame.Rect(x, y, w, h) # Rect for positionning

    def draw(self):
        """
        Draws the paddle as a rectangle.
        """        
        pygame.draw.rect(self.win, self.color, self.rect)

    def compute_pad_velocity(self):
        """
        Converts gyro angular rot. into pad displacement ignoring walls.
        """
        vy_factor = 0.5 # Factor to adjust paddle velocity [0.2 - 1]
        
        # Handling gyroscope i2c deconnection
        try:
            gyro_raw = self.gyro.get_data()
        except IOError:
            print("i2c communication with gyroscope interrupted")
            self.gyro.error = True
            self.gyro.ready_for_reinit = False
            vy = 0
        # Computing pad velocity if gyroscope is connected
        else:
            self.gyro.ready_for_reinit = True
            gyro_calib = gyro_raw - self.gyro.offset
            # vy => Negative signe added to have correct pad \
            # displacement based on physical installation on skateboards
            vy = - int(gyro_calib / self.gyro.numerical_sensitivity * \
                     self.win_h * vy_factor)
            
            """
            if gyro_calib < -200:
                vy_factor = -20
            elif  (gyro_calib >= -200 and gyro_calib < -100):
                vy_factor = -2
            elif (gyro_calib >= -50 and gyro_calib < -10): 
                vy_factor = -1  
            elif (gyro_calib >= -10 and gyro_calib < 10):
                vy_factor = 0
            elif (gyro_calib >= 10 and gyro_calib < 50):
                vy_factor = 1
            elif (gyro_calib >= 50 and gyro_calib < 200):
                vy_factor = 2
            elif gyro_calib >= 200:
                vy_factor = 3
            else:
                vy = 0
            vy = int(vy_factor * self.VY_PAD_RATIO * self.win_h)
            """
            '''
            print("Gyro (" + self.gyro.axis + " axis) => Raw data :", \
                  str(round(gyro_raw,2)), "/ Calibrated data :", \
                  str(round(gyro_calib,2)))
            '''
        return vy

    def move(self, win_h):
        """
        Moves the paddle taking into account wall collisions.
        """        
        vy_pad = self.compute_pad_velocity()        
        if self.rect.top + vy_pad < 0:
            self.rect.top = 0
        elif self.rect.bottom + vy_pad > win_h:
            self.rect.bottom = win_h
        else:
            self.rect.move_ip(0,vy_pad)
        return vy_pad
    
    def move_to_center(self, win_h):
        """
        Repositions the paddle in the center of the vertical axis.
        """
        self.rect.centery = win_h // 2
