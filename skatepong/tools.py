#!usr/bin/python3

#-----------------------------------------------------------------------
# IMPORTS
#-----------------------------------------------------------------------

import pygame

#-----------------------------------------------------------------------
# CODE
#-----------------------------------------------------------------------

def draw_text(win, font_nm, font_sz, txt, x, y, color, bg_color = None):
    """
    Draws text on a surface, text center serving as position reference.
    
    bg_color = text background color
    """
    font = pygame.font.SysFont(font_nm, font_sz)
    txt_surf = font.render(txt, True, color, bg_color)
    txt_rect = txt_surf.get_rect()
    txt_rect.center = (x, y)
    win.blit(txt_surf, txt_rect)
    
def draw_mid_line(win, win_w, win_h, thick, horiz_w_factor, color):
    """
    Draws vertical and short horizontals line in the mid screen.
    """
    # Straight line, with small center cross
    vert_rect = pygame.Rect(0, 0, thick, win_h)
    horiz_rect = pygame.Rect(0, 0, horiz_w_factor * thick, thick)
    vert_rect.center = (win_w // 2, win_h //2)
    horiz_rect.center = (win_w // 2, win_h //2)
    pygame.draw.rect(win, color, horiz_rect)
    pygame.draw.rect(win, color, vert_rect)

