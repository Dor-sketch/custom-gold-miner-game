"""
This module contains an implementation of the classic Gold Miner game.
It combines elements of timing, strategy, and hand-eye coordination.
The player controls a miner who must swing a claw back and forth to grab gold and other valuables.
The miner must avoid rocks, which will decrease the score and time.
The game has multiple levels, with the difficulty increasing as the player progresses.
The player's score and time are displayed on the screen.
The game ends when the player's score drops below zero or the time runs out.
The player can restart the game by refreshing the page.
The top scores are displayed at the end of the game.
The game is implemented using Pygame and asyncio.
"""
import os
import sys
import math
import random
import asyncio
import json
import platform
import pygame
from PIL import Image, ImageDraw

if "window" in platform.__dict__:
    platform.window.eval("localStorage.setItem('end', 'false');")

# Constants
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)
GREY = (128, 128, 128)
LIGHT_GREY =  (192, 192, 192)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
WIDTH, HEIGHT = 900, 600
FPS = 60
FONT_SIZE = 30
ROPE_SPEED = 5
RETURN_SPEED = 10
MAX_LENGTH = 800
SWINGING_LENGTH = 100
MIN_ANGLE = 0
MAX_ANGLE = 180
IMAGE_SIZE = 66
TRANSPARENT_BLACK = (0, 0, 0, 100)
OPEN_LEFT_CLAW_DIMENSIONS = [(10, 40), (30, 30), (20, 10)]
OPEN_RIGHT_CLAW_DIMENSIONS = [(50, 40), (30, 30), (40, 10)]
LEFT_CLAW_DIMENSIONS = [(10, 30), (30, 30), (20, 10)]
RIGHT_CLAW_DIMENSIONS = [(50, 30), (30, 30), (40, 10)]
FIRST_DEATH_HINT = "Hint: Avoid the rocks! Grabbing them will decrease your score and time! If your score drops below zero, you lose!"
FIRST_GOLD_HINT = "Hint: Nice catch! Grabbing gold increases your score and boosts your time! Grabbing enough will take you to the next level!"
FIRST_TIMES_UP_HINT = "Time's up! As you move up the levels, the penalty for grabbing rocks increases! Next time your time will end game over!"
ENDING_HINT = "Game is over! You can play again by refreshing the page!"
FONT = "Arial"
pygame.font.init()
hint_font = pygame.font.SysFont(None, 50)



def create_claw_images():
    """
    Create images for the open and closed claw.
    """
    open_claw_img = pygame.Surface((60, 60), pygame.SRCALPHA)
    closed_claw_img = pygame.Surface((60, 60), pygame.SRCALPHA)

    pygame.draw.polygon(open_claw_img, LIGHT_GREY, OPEN_LEFT_CLAW_DIMENSIONS)
    pygame.draw.polygon(open_claw_img, LIGHT_GREY, OPEN_RIGHT_CLAW_DIMENSIONS)
    open_claw_img = pygame.transform.rotate(open_claw_img, -90)

    pygame.draw.polygon(
        closed_claw_img, LIGHT_GREY, LEFT_CLAW_DIMENSIONS
    )
    pygame.draw.polygon(
        closed_claw_img, LIGHT_GREY, RIGHT_CLAW_DIMENSIONS
    )
    closed_claw_img = pygame.transform.rotate(closed_claw_img, -90)

    return open_claw_img, closed_claw_img


def load_background_random(folder):
    """
    Load a random image from the specified folder and return it as a pygame surface.
    """
    images = [img for img in os.listdir(
        folder) if img.endswith((".jpg", ".png"))]
    if images:
        random_image = random.choice(images)
        try:
            background = pygame.image.load(os.path.join(folder, random_image))
            background = pygame.transform.scale(background, (WIDTH, HEIGHT))
            dark_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dark_surface.fill(TRANSPARENT_BLACK)
            background.blit(dark_surface, (0, 0))
            return background
        except Exception as e:
            print(f"Could not load {random_image}, {e}")
    return pygame.Surface((WIDTH, HEIGHT)).fill(GREEN)


def load_background_levels(folder):
    levels = []
    for i in range(1, 6):
        background = pygame.image.load(os.path.join(folder, f"{i}.png"))
        background = pygame.transform.scale(background, (WIDTH, HEIGHT))
        dark_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dark_surface.fill(TRANSPARENT_BLACK)
        background.blit(dark_surface, (0, 0))
        levels.append(background)
    return levels


def load_main_background_image(folder="background"):
    """
    Load the main background image.
    """
    try:
        background = load_background_image(folder)
    except Exception as e:
        print(f"Error loading background image: {e}")
        background = pygame.Surface((WIDTH, HEIGHT))
        background.fill(GREEN)
    return background


def load_miner_image(file="miner.png"):
    """
    Load the miner image.
    """
    try:
        miner_img = pygame.image.load(file)
        miner_img = pygame.transform.scale(miner_img, (IMAGE_SIZE, IMAGE_SIZE))
    except Exception as e:
        print(f"Error loading miner image: {e}")
        miner_img = pygame.Surface((IMAGE_SIZE, IMAGE_SIZE))
        miner_img.fill(BLUE)
    return miner_img



def load_and_scale_image(image_path, max_size, shape="diamond"):
    """
    Load an image from a file, scale it to fit within the specified size,
    and return it as a pygame surface.
    """
    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"Could not load {image_path}")
        return pygame.Surface((IMAGE_SIZE, IMAGE_SIZE))
    scale_ratio = max_size / max(img.width, img.height)
    new_size = (int(img.width * scale_ratio), int(img.height * scale_ratio))
    img = img.resize(new_size, Image.LANCZOS)
    mask = create_diamond_mask(
        img) if shape == "diamond" else create_circle_mask(img)
    img.putalpha(mask)
    return pygame.image.fromstring(img.tobytes(), img.size, img.mode)


def create_diamond_mask(image):
    """
    Create a diamond-shaped mask for the image.
    """
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(
        [
            (image.width / 2, 0),
            (image.width, image.height / 2),
            (image.width / 2, image.height),
            (0, image.height / 2),
        ],
        fill=255,
    )
    draw.polygon(
        [
            (image.width / 2, 0),
            (image.width, image.height / 2),
            (image.width / 2, image.height),
            (0, image.height / 2),
        ],
        outline=255,
    )
    return mask


def create_circle_mask(image):
    """
    Create a circular mask for the image.
    """
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, image.width, image.height), fill=255)
    draw.ellipse((0, 0, image.width, image.height), outline=255)
    return mask


def add_golden_border(image, border_width):
    """
    Add a golden border to the image.
    """
    border_color = (255, 223, 0)
    width, height = image.get_size()
    pygame.draw.lines(
        image,
        border_color,
        True,
        [(width / 2, 0), (width, height / 2),
         (width / 2, height), (0, height / 2)],
        border_width,
    )
    return image


def add_grey_border(image, border_width):
    """
    Add a grey border to the image.
    """
    border_color = (128, 128, 128)
    width, height = image.get_size()
    pygame.draw.ellipse(image, border_color,
                        (0, 0, width, height), border_width)
    return image



class Miner(pygame.sprite.Sprite):
    def __init__(self, miner_img):
        super().__init__()
        self.image = miner_img
        self.rect = self.image.get_rect(centerx=WIDTH / 2, top=10)
        self.angle = 45
        self.length = SWINGING_LENGTH
        self.grabbing = False
        self.carrying = None
        self.retrieving = False
        self.open_claw_img, self.closed_claw_img = create_claw_images()
        self.angle_speed = 2

    def update(self):
        """
        Update the miner's position and state.
        """
        if self.retrieving:
            self.length -= RETURN_SPEED
            if self.length <= SWINGING_LENGTH:
                self.reset_state()
            else:
                if self.carrying:
                    self.carrying.rect.center = self.get_rope_end()
            return

        if self.grabbing:
            self.length += ROPE_SPEED
            if self.length > MAX_LENGTH or self.check_screen_bounds():
                self.grabbing = False
                self.retrieving = True
        else:
            self.swing()

    def draw(self, surface):
        """
        Draw the miner and the claw.
        """
        end_x, end_y = self.get_rope_end()
        pygame.draw.line(surface, BLACK, self.rect.center, (end_x, end_y), 5)
        claw_img = self.open_claw_img if self.grabbing else self.closed_claw_img
        claw_img = pygame.transform.rotate(claw_img, -self.angle)
        surface.blit(
            claw_img,
            (end_x - claw_img.get_width() // 2,
             end_y - claw_img.get_height() // 2),
        )

    def get_rope_end(self):
        """
        Return the end coordinates of the rope.
        """
        return (
            self.rect.centerx + self.length *
            math.cos(math.radians(self.angle)),
            self.rect.bottom + self.length *
            math.sin(math.radians(self.angle)),
        )

    def swing(self):
        """
        Make the miner swing back and forth.
        """
        self.angle += self.angle_speed
        if self.angle >= MAX_ANGLE or self.angle <= MIN_ANGLE:
            self.angle_speed *= -1

    def reset_state(self):
        """
        Reset the miner's state.
        """
        self.retrieving = False
        self.length = SWINGING_LENGTH
        if self.carrying:
            self.carrying.kill()
            self.carrying = None

    def check_screen_bounds(self):
        """
        Check if the rope has reached the screen bounds.
        """
        end_x, end_y = self.get_rope_end()
        return end_x <= 0 or end_x >= WIDTH or end_y <= 0 or end_y >= HEIGHT

    def grab_object(self, obj_sprites, score_value):
        """
        Grab an object from the sprite group and update the
        """
        score_dif = 0
        end_x, end_y = self.get_rope_end()
        for obj in obj_sprites:
            if obj.rect.collidepoint(end_x, end_y):
                score_dif += score_value
                self.carrying = obj
                self.grabbing = False
                self.retrieving = True
                break
        return score_dif


class Gold(pygame.sprite.Sprite):
    """
    A class representing a gold object.
    """

    def __init__(self):
        super().__init__()
        gold_folder = "gold"
        gold_img = None

        try:
            gold_images = os.listdir(gold_folder)
            if gold_images:  # Check if the directory is not empty
                random_image = random.choice(gold_images)
                try:
                    gold_img = load_and_scale_image(
                        os.path.join(gold_folder, random_image), IMAGE_SIZE
                    )
                    gold_img = add_golden_border(gold_img, 5)
                except Exception as e:
                    print(f"Error processing image: {e}")
        except FileNotFoundError:
            print(f"Directory {gold_folder} not found.")

        if gold_img is None:  # If no image was loaded, create a gold square
            gold_img = pygame.Surface((IMAGE_SIZE, IMAGE_SIZE))
            gold_img.fill(GOLD)

        self.image = gold_img
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = random.randint(HEIGHT // 2, HEIGHT - self.rect.height)


class Rock(pygame.sprite.Sprite):
    """
    A class representing a rock object.
    """

    def __init__(self):
        super().__init__()
        rock_folder = "rock"
        rock_img = None

        try:
            rock_images = [
                img for img in os.listdir(rock_folder) if img.endswith((".jpg", ".png"))
            ]
            if rock_images:  # Check if the directory is not empty
                random_image = random.choice(rock_images)
                try:
                    rock_img = load_and_scale_image(
                        os.path.join(rock_folder, random_image),
                        IMAGE_SIZE,
                        shape="circle",
                    )
                    rock_img = add_grey_border(rock_img, 5)
                except Exception as e:
                    print(f"Error processing image: {e}")
        except FileNotFoundError:
            print(f"Directory {rock_folder} not found.")

        if rock_img is None:  # If no image was loaded, create a grey square
            rock_img = pygame.Surface((IMAGE_SIZE, IMAGE_SIZE))
            rock_img.fill(GREY)

        self.image = rock_img
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = random.randint(HEIGHT // 2, HEIGHT - self.rect.height)

class Timer:
    def __init__(self):
        self.start_ticks = pygame.time.get_ticks()  # Starter tick
        self.seconds = 0

    def update(self):
        # calculate how many seconds
        seconds = (
            pygame.time.get_ticks() - self.start_ticks
        ) / 1000  # calculate how many seconds

        if seconds > self.seconds:
            self.seconds = seconds
            return True
        return False

def create_sprite_groups():
    """
    Create sprite groups for all sprites, gold sprites, and rock sprites.
    """
    all_sprites = pygame.sprite.Group()
    gold_sprites = pygame.sprite.Group()
    rock_sprites = pygame.sprite.Group()
    return all_sprites, gold_sprites, rock_sprites


def add_sprites_to_groups(
    all_sprites, gold_sprites, rock_sprites, num_gold=6, num_rocks=5
):
    """
    Add gold and rock sprites to the sprite groups.
    """
    for _ in range(num_gold):
        gold = Gold()
        gold_sprites.add(gold)
        all_sprites.add(gold)

    for _ in range(num_rocks):
        rock = Rock()
        rock_sprites.add(rock)
        all_sprites.add(rock)


def update_score(score):
    # Save the score in local storage
    if "window" in platform.__dict__:
        platform.window.eval(f"localStorage.setItem('score', '{score}');")
        platform.window.eval(f"localStorage.setItem('end', '{'true'}');")

def render_score(screen, font, score, seconds_left):
    """
    Render the score on the screen.
    """
    text = font.render(
        f"Score: {score} | Time: {seconds_left}", True, WHITE)
    text_rect = text.get_rect(topleft=(10, 10))
    screen.blit(text, text_rect)

async def draw_hint(screen, hint_text):
    """
    Draw a hint on the screen.
    """
    # Render the hint text and its background
    hint = hint_font.render(
        hint_text, True, WHITE, wraplength=WIDTH // 2)
    hint_background = hint_font.render(
        hint_text, True, (255, 0, 0), wraplength=WIDTH // 2
    )
    # Calculate the position for the hint
    hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    # Draw the hint background slightly offset to create a "shadow" effect
    screen.blit(hint_background, hint_rect.move(2, 2))
    # Draw the hint text
    screen.blit(hint, hint_rect)
    pygame.display.flip()
    await asyncio.sleep(5)

class GameState:
    def __init__(self):
        self.running = True
        self.first_event = True
        self.first_death = True
        self.first_gold = True
        self.first_times_up = True
        self.score = 0
        self.timer = Timer()
        self.levels = {
            0: [0, 0],
            30: [4, 4],
            35: [3, 7],
            40: [3, 5],
            45: [3, 5],
            30: [3, 5],
            35: [3, 6],
            40: [3, 6],
            50: [4, 12],
        }
        self.cur_level = 0
        self.seconds_left = 60 * 30
        if "window" in platform.__dict__:
            platform.window.eval("localStorage.setItem('end', 'false');")

    async def update(self, clock, all_sprites, miner, gold_sprites, rock_sprites, screen, font, background):
        while self.running:
            clock.tick(FPS)
            if self.timer.update():
                self.seconds_left -= 1
                if self.seconds_left <= 0:
                    if self.first_times_up:
                        self.first_times_up = False
                        self.seconds_left = 1000
                        await draw_hint(screen, FIRST_TIMES_UP_HINT)
                    else:
                        await draw_hint(screen, ENDING_HINT)
                        self.running = False

            events = pygame.event.get()
            for event in events:
                if self.first_event:
                    self.first_event = False
                    break
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                    if not miner.grabbing and not miner.carrying:
                        miner.grabbing = True

            all_sprites.update()
            t = self.score
            if miner.grabbing:
                self.score += miner.grab_object(gold_sprites, 10)
                self.score += miner.grab_object(rock_sprites, -10)
            if self.score in self.levels:
                add_sprites_to_groups(
                    all_sprites,
                    gold_sprites,
                    rock_sprites,
                    self.levels[self.score][0],
                    self.levels[self.score][1],
                )
                del self.levels[self.score]
                self.cur_level += 1
            elif t > self.score:
                self.seconds_left -= 60 * self.score
            elif t < self.score:
                self.seconds_left += 600
            if self.score > 0 and self.first_gold:
                self.first_gold = False
                await draw_hint(screen, FIRST_GOLD_HINT)
            if self.score < 0:
                if self.first_death:
                    self.first_death = False
                    self.score = 0
                    await draw_hint(screen, FIRST_DEATH_HINT)
                else:
                    self.running = False

            screen.blit(background[min(self.cur_level, 4)], (0, 0))
            all_sprites.draw(screen)
            miner.draw(screen)
            render_score(screen, font, self.score, self.seconds_left)
            pygame.display.flip()
            await asyncio.sleep(0)
        update_score(self.score)

async def game_loop(clock, all_sprites, miner, gold_sprites, rock_sprites, screen, font, background):
    """
    Main game loop.
    """
    game_state = GameState()
    await game_state.update(clock, all_sprites, miner, gold_sprites, rock_sprites, screen, font, background)

def setup_pygame():
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.load("music.mp3")
    pygame.mixer.music.play(-1)
    return pygame.font.SysFont(FONT, FONT_SIZE)

def setup_screen():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Gold Miner")
    return screen

async def main():
    """
    Main function.
    """
    font = setup_pygame()
    background = load_background_levels("background")
    screen = setup_screen()
    clock = pygame.time.Clock()
    miner = Miner(load_miner_image())
    all_sprites, gold_sprites, rock_sprites = create_sprite_groups()
    all_sprites.add(miner)
    add_sprites_to_groups(all_sprites, gold_sprites, rock_sprites)

    await game_loop(
        clock,
        all_sprites,
        miner,
        gold_sprites,
        rock_sprites,
        screen,
        font,
        background,
    )

    if "window" in platform.__dict__:
        platform.window.eval("localStorage.setItem('end', 'true');")
        # dim background with semi-transparent black
        dark_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dark_surface.fill(TRANSPARENT_BLACK)
        screen.blit(dark_surface, (0, 0))
        topscores = platform.window.eval("localStorage.getItem('topScores');")
        # parse the json string to a python object
        topscores = json.loads(topscores)
        SCORE_COLOR = (253, 208, 23)
        text = font.render("Top Scores", True, SCORE_COLOR)
        x = WIDTH // 2 - text.get_width() // 2
        screen.blit(text, text.get_rect(topleft=(x, 40)))
        y = 90
        x -= 40
        # Calculate the maximum length of the name part only
        max_name_length = max([len(line.split(":")[0]) for line in topscores])
        for line in topscores:
            name, score = line.split(":")
            text = font.render(name, True, SCORE_COLOR)
            screen.blit(text, text.get_rect(topleft=(x, y)))
            score_x = x + (max_name_length * font.size(" ")[0] * 2)
            text = font.render(score, True, SCORE_COLOR)
            screen.blit(text, text.get_rect(topleft=(score_x, y)))
            y += 50
        pygame.display.flip()
        pygame.display.fill(WHITE)
        pygame.display.flip()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            asyncio.sleep(1)

    pygame.quit()
    sys.exit()


# Program entry point
asyncio.run(main())
