#!/usr/bin/env python2

import pygame
try:
    import pygame.gfxdraw
    NO3D = False
except:
    NO3D = True
import os
import sys
import re
import math
from pygame.locals import *
from PIL import Image
from pygame_markdown import MarkdownRenderer
import argparse

# Standard values. If settings is supplied, those present will be overwritten.
CONFIG = {
    'SCREEN': {'WIDTH': 1920, 'HEIGHT': 1080, 'FULLSCREEN': True},
    'BORDER': {'WIDTH': 40, 'COLOR': (75,75,75)},
    'BG_COLOR': (30,30,30),
    'TEXT_COLOR': (200,200,200),
    'FONT_SIZES': (48, 36, 32, 28, 28, 28),
    'TEXT_FONT_NAME': 'Ubuntu',
    'CODE_FONT_NAME': 'CourierNew',
    'IMAGE_MAX': {'WIDTH': 600, 'HEIGHT': 400},
    'FPS': 30,
    'TRANSITION_DURATION': 1.0,
}

# Load Markdown file
def load_markdown(filename):
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    return content

# Parse Markdown into slides
def parse_slides(md_text, basedir="./"):
    slides = []
    current_slide = {"title": "", "content": [], "images": [], "transition": "slide"}
    
    for line in md_text.split("\n"):
        if line.startswith("# "):  # New slide
            if current_slide["title"]:
                slides.append(current_slide)
            current_slide = {"title": line[2:], "content": [], "images": [], "transition": "slide"}
        elif re.match(r"<!--\s*transition:\s*(slide|fade|3d-rotate|3d-zoom)\s*-->", line):  
            current_slide["transition"] = line.split(":")[1].strip().replace("-->", "").strip()
        elif line.startswith("!"):  
            start = line.find("(") + 1
            end = line.find(")")
            if start > 0 and end > start:
                current_slide["images"].append(basedir + line[start:end])
        else:
            current_slide["content"].append(line)

    if current_slide["title"]:
        slides.append(current_slide)

    return slides

# Load and scale image
def load_image(path):
    if not os.path.exists(path):
        return None
    img = Image.open(path)
    img.thumbnail((CONFIG['IMAGE_MAX']['WIDTH'], CONFIG['IMAGE_MAX']['HEIGHT']))
    return pygame.image.fromstring(img.tobytes(), img.size, img.mode)

# Slide transition
def slide_transition(screen, old_slide, new_slide, direction, clock):
    steps = int(CONFIG['FPS']*CONFIG['TRANSITION_DURATION'])
    w = CONFIG['SCREEN']['WIDTH']
    offset = w if direction == "right" else -w
    for i in range(0, w, int(w/steps)):
        screen.fill(CONFIG['BORDER']['COLOR'])
        screen.blit(old_slide, (i if direction == "left" else -i, CONFIG['BORDER']['WIDTH']))
        screen.blit(new_slide, (offset - i if direction == "right" else offset + i, CONFIG['BORDER']['WIDTH']))
        pygame.display.flip()
        clock.tick(CONFIG['FPS'])

# Fade transition
def fade_transition(screen, old_slide, new_slide, clock):
    steps = int(CONFIG['FPS']*CONFIG['TRANSITION_DURATION'])
    for alpha in range(0, 256, int(255 / steps)):
        screen.fill(CONFIG['BORDER']['COLOR'])
        old_slide.set_alpha(255 - alpha)
        new_slide.set_alpha(alpha)
        screen.blit(old_slide, (CONFIG['BORDER']['WIDTH'], CONFIG['BORDER']['WIDTH']))
        screen.blit(new_slide, (CONFIG['BORDER']['WIDTH'], CONFIG['BORDER']['WIDTH']))
        pygame.display.flip()
        clock.tick(CONFIG['FPS'])


# 2D Rotate transition
def rotate_2d_transition(screen, old_slide, new_slide, clock):
    """ Flat version since pygame has no skew transform """
    steps = int(CONFIG['FPS']*CONFIG['TRANSITION_DURATION'])
    for angle in range(0, 181, int(180 / steps)):
        screen.fill(CONFIG['BORDER']['COLOR'])
        if angle <= 90:
            rotated_surface = pygame.transform.scale(old_slide, (int(WIDTH * math.cos(math.radians(angle))), HEIGHT))
            screen.blit(rotated_surface, ((WIDTH - rotated_surface.get_width()) // 2, CONFIG['BORDER']['WIDTH']))
        else:
            rotated_surface = pygame.transform.scale(new_slide, (int(WIDTH * math.cos(math.radians(180 - angle))), HEIGHT))
            screen.blit(rotated_surface, ((WIDTH - rotated_surface.get_width()) // 2, CONFIG['BORDER']['WIDTH']))
        pygame.display.flip()
        clock.tick(CONFIG['FPS'])


# 3D Rotate transition
def rotate_3d_transition(screen, old_slide, new_slide, clock):
    steps = int(CONFIG['FPS']*CONFIG['TRANSITION_DURATION'])
    w = CONFIG['SCREEN']['WIDTH']-CONFIG['BORDER']['WIDTH']
    h = CONFIG['SCREEN']['HEIGHT']-CONFIG['BORDER']['WIDTH']
    bx = CONFIG['BORDER']['WIDTH']
    by = CONFIG['BORDER']['WIDTH']

    for angle in range(0, 181, int(180 / steps)):
        screen.fill(CONFIG['BORDER']['COLOR'])
        cosd = math.cos(math.radians(angle))
        sind = math.sin(math.radians(angle))

        x1 = int(bx + (1-cosd)*w/2)
        x2 = int(bx + w - (1-cosd)*w/2)
        y1 = int(bx + sind*h/2)
        y2 = int(bx - sind*h/20)
        y3 = int(bx + h + sind*h/20)
        y4 = int(bx + h - sind*h/2)
        ty = int(sind*h/2)

        # This is as good as it gets until there is a skew-transform in pygame
        if angle <= 90:
            texture = pygame.transform.scale(old_slide, (x2-x1+bx*2, h+by*2))
        else:
            texture = pygame.transform.scale(new_slide, (x1-x2+bx*2, h+by*2))

        pygame.gfxdraw.textured_polygon(screen, [(x1, y1),
                                                 (x2, y2),
                                                 (x2, y3),
                                                 (x1, y4)],
                                         texture, min([x1,x2]), -ty)
        pygame.display.flip()
        clock.tick(CONFIG['FPS'])

# 3D Zoom transition
def zoom_3d_transition(screen, old_slide, new_slide, clock):
    steps = int(CONFIG['FPS']*CONFIG['TRANSITION_DURATION'])/2
    W = CONFIG['SCREEN']['WIDTH']-CONFIG['BORDER']['WIDTH']*2
    H = CONFIG['SCREEN']['HEIGHT']-CONFIG['BORDER']['WIDTH']*2
    B = CONFIG['BORDER']['WIDTH']

    for scale in range(100, 0, -int(100 / steps)):
        screen.fill(CONFIG['BORDER']['COLOR'])
        zoomed_surface = pygame.transform.scale(old_slide, (int(W * scale / 100), int(H * scale / 100)))
        screen.blit(zoomed_surface, ((W - zoomed_surface.get_width()) // 2 + B, (H - zoomed_surface.get_height()) // 2 + B))
        pygame.display.flip()
        clock.tick(CONFIG['FPS'])

    for scale in range(0, 100, int(100 / steps)):
        screen.fill(CONFIG['BORDER']['COLOR'])
        zoomed_surface = pygame.transform.scale(new_slide, (int(W * scale / 100), int(H * scale / 100)))
        screen.blit(zoomed_surface, ((W - zoomed_surface.get_width()) // 2 + B, (H - zoomed_surface.get_height()) // 2 + B))
        pygame.display.flip()
        clock.tick(CONFIG['FPS'])


# Render slide content to a surface
def render_slide(slide):
    W = CONFIG['SCREEN']['WIDTH']-CONFIG['BORDER']['WIDTH']*2
    H = CONFIG['SCREEN']['HEIGHT']-CONFIG['BORDER']['WIDTH']*2
    surface = pygame.Surface((W,H))
    surface.fill(CONFIG['BG_COLOR'])
    pygame.draw.rect(surface, CONFIG['BG_COLOR'], (0,0, W,H))

    md = MarkdownRenderer()
    mdtxt = "# " + slide['title'] + "\n" + "\n".join(slide['content'])
    #print(mdtxt)
    
    md.set_markdown_from_string(md_string=mdtxt)
    md.set_area(surface=surface, offset_x=0, offset_y=0, width=W//2, height=H)
    md.set_color_background(*CONFIG['BG_COLOR'])
    md.set_color_font(*CONFIG['TEXT_COLOR'])
    md.set_font_sizes(*CONFIG['FONT_SIZES'])
    md.set_font(CONFIG['TEXT_FONT_NAME'], CONFIG['CODE_FONT_NAME'])
    md.display([], 0,0, [0,0])

    y_offset = CONFIG['FONT_SIZES'][0]
    for img_path in slide["images"]:
        image = load_image(img_path)
        if image:
            surface.blit(image, (W // 2 + CONFIG['FONT_SIZES'][1], y_offset))
            y_offset += image.get_height() + 20

    return surface

# Main function
def run_slideshow(md_file):
    basedir = "./"
    if "/" in md_file:
        basedir = "/".join(md_file.split('/')[:-1]) + "/"
    pygame.init()
    if CONFIG['SCREEN']['FULLSCREEN']:
      screen = pygame.display.set_mode((CONFIG['SCREEN']['WIDTH'], CONFIG['SCREEN']['HEIGHT']), pygame.FULLSCREEN)
    else:
      screen = pygame.display.set_mode((CONFIG['SCREEN']['WIDTH'], CONFIG['SCREEN']['HEIGHT']))
    pygame.display.set_caption("Markdown Slideshow")

    md_text = load_markdown(md_file)
    slides = parse_slides(md_text, basedir)

    current_slide_idx = 0
    running = True
    clock = pygame.time.Clock()

    current_surface = render_slide(slides[current_slide_idx])

    while running:
        screen.fill(CONFIG['BORDER']['COLOR'])
        screen.blit(current_surface, (CONFIG['BORDER']['WIDTH'], CONFIG['BORDER']['WIDTH']))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False
            elif event.type == MOUSEBUTTONDOWN or (event.type == KEYDOWN and event.key == K_RIGHT):
                if current_slide_idx < len(slides) - 1:
                    next_slide_idx = current_slide_idx + 1
                    next_surface = render_slide(slides[next_slide_idx])
                    transition = slides[next_slide_idx]["transition"]
                    if transition == "fade":
                        fade_transition(screen, current_surface, next_surface, clock)
                    elif transition == "3d-rotate":
                        if NO3D:
                            rotate_2d_transition(screen, current_surface, next_surface, clock)
                        else:
                            rotate_3d_transition(screen, current_surface, next_surface, clock)
                    elif transition == "3d-zoom":
                        zoom_3d_transition(screen, current_surface, next_surface, clock)
                    else:
                        slide_transition(screen, current_surface, next_surface, "right", clock)
                    current_surface = next_surface
                    current_slide_idx = next_slide_idx
            elif event.type == KEYDOWN and event.key == K_LEFT:
                if current_slide_idx > 0:
                    prev_slide_idx = current_slide_idx - 1
                    prev_surface = render_slide(slides[prev_slide_idx])
                    transition = slides[prev_slide_idx]["transition"]
                    if transition == "fade":
                        fade_transition(screen, current_surface, prev_surface, clock)
                    elif transition == "3d-rotate":
                        if NO3D:
                            rotate_2d_transition(screen, current_surface, prev_surface, clock)
                        else:
                            rotate_3d_transition(screen, current_surface, prev_surface, clock)
                    elif transition == "3d-rotate":
                        rotate_2d_transition(screen, current_surface, prev_surface, clock)
                    elif transition == "3d-zoom":
                        zoom_3d_transition(screen, current_surface, prev_surface, clock)
                    else:
                        slide_transition(screen, current_surface, prev_surface, "left", clock)
                    current_surface = prev_surface
                    current_slide_idx = prev_slide_idx

        clock.tick(30)

    pygame.quit()
    sys.exit()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="pyslides.py")
    parser.add_argument('--style-file')

    parser.add_argument('slides_filename')
    res = parser.parse_args(sys.argv[1:])

    if res.style_file:
        import json
        try:
            newstyle = json.load(open(res.style_file,'r'))
        except:
            print("Failed to open style. using standard values")
            newstyle = False

        if newstyle:
            for key in newstyle.keys():
                if type(newstyle[key]) == dict:
                    for key2 in newstyle[key].keys():
                        CONFIG[key][key2] = newstyle[key][key2]
                else:
                    CONFIG[key] = newstyle[key]
    run_slideshow(res.slides_filename)

