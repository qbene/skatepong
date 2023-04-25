#!usr/bin/python3

import pygame
import sys

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
    

def draw_mid_line(win, win_w, win_h, line_thick, horizontal_line_factor, color):
    """
    Draws vertical and short horizontals line in the mid screen.
    """
    # Straight line, with small center cross
    vertical_rect = pygame.Rect(0, 0, line_thick, win_h)
    horizontal_rect = pygame.Rect(0, 0, horizontal_line_factor * line_thick, line_thick)
    vertical_rect.center = (win_w // 2, win_h //2)
    horizontal_rect.center = (win_w // 2, win_h //2)
    pygame.draw.rect(win, color, horizontal_rect)
    pygame.draw.rect(win, color, vertical_rect)

