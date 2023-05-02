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

    def draw(self, color):
        """
        Draws the ball as a circle.
        """
        ball_rect = pygame.draw.circle(self.win, color, \
                                       self.rect.center, self.r)
        return ball_rect
        
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
    
    angle_pad_to_wall = 30 # Absolute value (in degrees)
    
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

    def draw(self, color):
        """
        Draws the paddle as a rectangle.
        """        
        pad_rect = pygame.draw.rect(self.win, color, self.rect)
        return pad_rect

    def move(self):
        """
        Moves the paddle taking into account wall collisions.
        """        
        try:
            self.gyro.get_position()
        except IOError:
            self.gyro.error = True
        else:
            #print (self.gyro.pos)
            if self.gyro.pos >= self.angle_pad_to_wall:
                self.rect.top = 0
            elif self.gyro.pos <= -self.angle_pad_to_wall:
                self.rect.bottom = self.win_h
            else:
                self.rect.centery = int(self.win_h / 2 - \
                                       (self.win_h - self.h) / 2 * \
                                        self.gyro.pos / self.angle_pad_to_wall \
                                        )
    
    def move_to_center(self):
        """
        Repositions the paddle in the center of the vertical axis.
        """
        self.rect.centery = self.win_h // 2
        self.gyro.pos = 0
