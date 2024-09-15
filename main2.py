import pygame
import os
import random
import aubio
import pyaudio
import numpy as np

pygame.init()

#Pygame setup
HEIGHT = 450
WIDTH = 1100
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))

RUNNING = [pygame.image.load(os.path.join("DuckAnimation/Walking", "goose_walk1.png")),
           pygame.image.load(os.path.join("DuckAnimation/Walking", "goose_walk2.png")),
           pygame.image.load(os.path.join("DuckAnimation/Walking", "goose_walk3.png")),
           pygame.image.load(os.path.join("DuckAnimation/Walking", "goose_walk4.png"))]

JUMPING = pygame.image.load(os.path.join("DuckAnimation/Jumping", "duck_jump1.png"))

CROUCHING = [pygame.image.load(os.path.join("DuckAnimation/Crouching", "goose_crouch1.png")),
             pygame.image.load(os.path.join("DuckAnimation/Crouching", "goose_crouch2.png"))]

CACTUS = [pygame.image.load(os.path.join("Assets", "cactus1.png")),
          pygame.image.load(os.path.join("Assets", "cactus2.png")),
          pygame.image.load(os.path.join("Assets", "cactus3.png"))]

BIRD = [pygame.image.load(os.path.join("Assets", "Bird1.png")),
        pygame.image.load(os.path.join("Assets", "bird2.png"))]

BG = pygame.image.load(os.path.join("Assets", "background.jpg"))

# Pitch detection setup
p = pyaudio.PyAudio()
BUFFER_SIZE = 1024
SAMPLE_RATE = 44100
pitch_threshold_jump = 300  #Adjust based on the pitch detected for a jump
pitch_threshold_crouch = 150 #Adjust based on the pitch detected for a crouch

#Aubio pitch detection object
pitch_o = aubio.pitch("default", BUFFER_SIZE, BUFFER_SIZE // 2, SAMPLE_RATE)
pitch_o.set_unit("Hz")
pitch_o.set_silence(-40)

#Start PyAudio stream
stream = p.open(format=pyaudio.paFloat32,
                channels=1, rate=SAMPLE_RATE, input=True,
                frames_per_buffer=512)
class Obstacle:
    '''
    image: denotes what obstacle it will be (cactus, bird)
    type: denotes between the different sprites of the obstacle
    '''
    def __init__(self, image, type):
        self.image = image
        self.type = type
        self.rect = self.image[self.type].get_rect()
        self.rect.x = WIDTH

    def update(self):
        self.rect.x -= game_speed
        if self.rect.x < -self.rect.width:
            obstacles.pop()

    def draw(self, SCREEN):
        SCREEN.blit(self.image[self.type], self.rect)

class Cactus(Obstacle):
    def __init__(self, image):
        self.type = random.randint(0, 2)
        super().__init__(image, self.type)
        self.rect.y = 300

class Bird(Obstacle):
    def __init__(self, image):
        self.type = 0
        super().__init__(image, self.type)
        self.rect.y = 250
        self.index = 0

    def draw(self, SCREEN):
        if self.index >= 9:
            self.index = 0
        SCREEN.blit(self.image[self.index//5], self.rect)
        self.index += 1

class Goose:
    X_POS = 80
    Y_POS = 310
    Y_POS_CROUCH = 330
    JUMP_VEL = 10

    def __init__(self):
        self.crouch_img = CROUCHING
        self.jump_img = JUMPING
        self.run_img = RUNNING

        self.goose_crouch = False
        self.goose_jump = False
        self.goose_run = True

        self.step_index = 0
        self.jump_vel = self.JUMP_VEL
        self.image = self.run_img[0]
        self.goose_rect = self.image.get_rect()
        self.goose_rect.x = self.X_POS
        self.goose_rect.y = self.Y_POS

    def update(self, pitch_value):

        if self.goose_crouch:
            self.crouch()
        if self.goose_jump:
            self.jump()
        if self.goose_run:
            self.run()

        if self.step_index >= 20:
            self.step_index = 0

        if pitch_value > pitch_threshold_jump and not self.goose_jump:
            self.goose_crouch = False
            self.goose_run = False
            self.goose_jump = True
        elif pitch_value < pitch_threshold_crouch and not self.goose_jump:
            self.goose_crouch = True
            self.goose_run = False
            self.goose_jump = False
        elif not (self.goose_jump or pitch_value < pitch_threshold_crouch):
            self.goose_crouch = False
            self.goose_run = True
            self.goose_jump = False

    def run(self):
        self.image = self.run_img[self.step_index // 5]
        self.goose_rect = self.image.get_rect()
        self.goose_rect.x = self.X_POS
        self.goose_rect.y = self.Y_POS
        self.step_index += 1

    def crouch(self):
        self.image = self.crouch_img[self.step_index // 10]
        self.goose_rect = self.image.get_rect()
        self.goose_rect.x = self.X_POS
        self.goose_rect.y = self.Y_POS_CROUCH
        self.step_index += 1

    def jump(self):
        self.image = self.jump_img
        if self.goose_jump:
            self.goose_rect.y -= self.jump_vel * 4
            self.jump_vel -= 0.8

        if self.jump_vel < -self.JUMP_VEL:
            self.goose_jump = False
            self.jump_vel = self.JUMP_VEL

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.goose_rect.x, self.goose_rect.y))

#Extract pitch from microphone input
def get_pitch():
    data = stream.read(512, exception_on_overflow=False)
    samples = np.frombuffer(data, dtype=np.float32)
    pitch = pitch_o(samples)[0]
    return pitch

def main():
    global game_speed, x_pos_bg, y_pos_bg, points, obstacles
    run = True
    clock = pygame.time.Clock()
    player = Goose()
    x_pos_bg = 0
    y_pos_bg = -750
    game_speed = 15
    points = 0
    obstacles = []
    font = pygame.font.SysFont("Arial", 20)
    death_count = 0

    def background():
        global x_pos_bg, y_pos_bg
        image_width = BG.get_width()
        SCREEN.blit(BG, (x_pos_bg, y_pos_bg))
        SCREEN.blit(BG, (image_width + x_pos_bg, y_pos_bg))
        if x_pos_bg <= -image_width:
            SCREEN.blit(BG, (image_width + x_pos_bg, y_pos_bg))
            x_pos_bg = 0
        x_pos_bg -= game_speed

    def score():
        global points, game_speed
        points += 1
        if points % 100 == 0:
            game_speed += 1

        display_score = font.render("POINTS: " + str(points), True, (0, 0, 0))
        SCREEN.blit(display_score, (950, 20))

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                run = False

        background()

        if len(obstacles) == 0:
            if random.randint(0, 2) == 0:
                obstacles.append(Cactus(CACTUS))
            elif random.randint(0, 1) == 1:
                obstacles.append(Bird(BIRD))

        collision_detected = False
        for obstacle in obstacles:
            obstacle.draw(SCREEN)
            obstacle.update()
            if player.goose_rect.colliderect(obstacle.rect):
                collision_detected = True
                break

        if collision_detected:
            for _ in range(2):  # Display collision feedback for frames
                SCREEN.fill((255, 255, 255))
                background()
                for obstacle in obstacles:
                    obstacle.draw(SCREEN)
                player.draw(SCREEN)
                pygame.display.update()
                pygame.time.delay(50)  # Delay to visualize collision before transitioning

            death_count += 1
            menu(death_count)

        pitch_value = get_pitch()  # Get pitch from microphone
        player.draw(SCREEN)
        player.update(pitch_value)
        score()

        clock.tick(30)
        pygame.display.update()

def menu(death_count):
    global points
    run = True
    font = pygame.font.Font('freesansbold.ttf', 30)

    while run:
        SCREEN.fill((255, 255, 255))

        #Determine text based on death count
        if death_count > 0:
            message = "Press any Key to Restart"
            score_text = f"Your Score: {points}"
        else:
            message = "Press any Key to Start"
            score_text = ""

        #Render text
        text_surface = font.render(message, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        SCREEN.blit(text_surface, text_rect)

        if score_text:
            score_surface = font.render(score_text, True, (0, 0, 0))
            score_rect = score_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
            SCREEN.blit(score_surface, score_rect)

        SCREEN.blit(RUNNING[0], (WIDTH // 2 - 20, HEIGHT // 2 - 140))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                run = False
            if event.type == pygame.KEYDOWN:
                main()

menu(0)
