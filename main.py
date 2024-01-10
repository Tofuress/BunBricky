import sys
import pygame

from settings import *
from pygame.locals import KEYDOWN, K_f


# физика движения шарика
class Ball(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites, movable_sprites, destructible_sprites, level):
        super().__init__()
        for g in groups:
            g.add(self)

        self.image = pygame.image.load('./graphics/test/ballBlue.png').convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = pygame.Rect(pos, (TILESIZE, TILESIZE)).center
        self.rect.size = self.image.get_size()
        self.hitbox = self.rect
        self.display_surface = pygame.display.get_surface()
        self.block_count = 0
        self.level = level

        self.direction = pygame.math.Vector2(-1, 1)
        if self.level == 1:
            self.speed = 7
        elif self.level == 2:
            self.speed = 8
        else:
            self.speed = 9
        self.lose = False

        self.obstacle_sprites = obstacle_sprites
        self.movable_sprites = movable_sprites
        self.destructible_sprites = destructible_sprites

    def draw_text(self, text, font, color, x, y):
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = (x, y)
        self.display_surface.blit(text_surface, text_rect)

    def move(self, speed):
        if self.hitbox.x < WIDTH:
            if self.direction.magnitude() != 0:
                self.direction = self.direction.normalize()
                # print(self.direction)

            self.hitbox.x += self.direction.x * speed
            self.collision(self.obstacle_sprites, 'horizontal')
            self.collision(self.destructible_sprites, 'horizontal', True)
            self.collision(self.movable_sprites, 'horizontal')

            if self.direction.magnitude() != 0:
                self.direction = self.direction.normalize()

            self.hitbox.y += self.direction.y * speed
            # print(self.hitbox.x, self.hitbox.y)
            self.collision(self.obstacle_sprites, 'vertical')
            self.collision(self.destructible_sprites, 'vertical', True)
            self.collision(self.movable_sprites, 'vertical')

            self.rect.center = self.hitbox.center
        else:
            # если за пределами поля
            self.lose = True
            # pygame.quit()
            # sys.exit()

    def collision(self, sprites, direction, kill=False):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

        destructible_sprites = []

        if direction == 'horizontal':
            for sprite in sprites:
                if sprite.hitbox.colliderect(self.hitbox):
                    if self.direction.x > 0:  # вправо
                        self.direction.x = -1
                        self.hitbox.right = sprite.hitbox.left
                        destructible_sprites.append(sprite)
                    elif self.direction.x < 0:  # влево
                        self.direction.x = 1
                        self.hitbox.left = sprite.hitbox.right
                        destructible_sprites.append(sprite)

        if direction == 'vertical':
            for sprite in sprites:
                if sprite.hitbox.colliderect(self.hitbox):
                    if self.direction.y > 0:  # вниз
                        self.direction.y = -1
                        self.hitbox.bottom = sprite.hitbox.top
                        destructible_sprites.append(sprite)
                    elif self.direction.y < 0:  # вверх
                        self.direction.y = 1
                        self.hitbox.top = sprite.hitbox.bottom
                        destructible_sprites.append(sprite)
        # убирает блоки
        if kill and len(destructible_sprites) > 0:
            for sprite in destructible_sprites:
                sprite.kill()
                self.block_count += 1
                # если все блоки сломаны
                if (self.level == 1 and self.block_count == 22 or self.level == 2 and self.block_count == 28 or
                        self.level == 3 and self.block_count == 50):
                    self.level += 1
                    Game(self.level).run()

    def update(self):
        self.move(self.speed)


# движение ракетки
class Paddle(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites):
        super().__init__()
        for g in groups:
            g.add(self)

        self.image = pygame.image.load('./graphics/test/paddleBlu.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (TILESIZE, self.image.get_height()))
        self.image = pygame.transform.rotate(self.image, -90)
        self.rect = self.image.get_rect()
        self.rect.center = pygame.Rect(pos, (TILESIZE, TILESIZE)).center
        self.rect.size = self.image.get_size()
        self.hitbox = self.rect

        self.direction = pygame.math.Vector2()
        self.speed = 8

        self.obstacle_sprites = obstacle_sprites

    def input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP]:
            self.direction.y = -1
        elif keys[pygame.K_DOWN]:
            self.direction.y = 1
        else:
            self.direction.y = 0

    def move(self, speed):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

        self.rect.y += self.direction.y * speed
        self.collision('vertical')

    def collision(self, direction):
        if direction == 'vertical':
            for sprite in self.obstacle_sprites:
                if sprite.rect.colliderect(self.rect):
                    if self.direction.y > 0:  # вниз
                        self.rect.bottom = sprite.rect.top
                    if self.direction.y < 0:  # вверх
                        self.rect.top = sprite.rect.bottom

    def update(self):
        self.input()
        self.move(self.speed)


# спрайты и хитбоксы для блоков
class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, filename, groups):
        super().__init__()
        for g in groups:
            g.add(self)

        self.image = pygame.image.load(filename).convert_alpha()
        self.image = pygame.transform.scale(self.image, (TILESIZE, TILESIZE))
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect


# конструктор уровней
class Level:
    def __init__(self, lvl):
        self.paddle = None
        self.ball = None
        self.level = lvl
        self.dialogue = True
        self.d_num = 0
        self.display_surface = pygame.display.get_surface()
        self.lvl1_dialogue = ['Хэй! Я - кролик по имени Роджер!', 'Сегодня я твой проводник по миру арканоида.',
                              'Просто отбивай ракеткой мячик, пока не сломаешь все блоки.',
                              'Игра будет становиться быстрее.', 'Ну что, начнём?']
        self.lvl2_dialogue = ['Ого, ты прошёл первый уровень!',
                              'Но не стоит расслабляться, вот ещё один.',
                              'Начнём!']
        self.lvl3_dialogue = ['Отлично! Ты прошёл второй уровень.',
                              'Остался последний и самый сложный уровень.',
                              'Поехали!']

        # группы спрайтов
        self.visible_sprites = pygame.sprite.Group()
        self.obstacle_sprites = pygame.sprite.Group()
        self.destructible_sprites = pygame.sprite.Group()
        self.movable_sprites = pygame.sprite.Group()

        # расстановка спрайтов
        self.create_map()

    def create_map(self):
        if self.level == 1:
            mapp = LEVEL_MAP_001

        elif self.level == 2:
            mapp = LEVEL_MAP_002
        elif self.level == 3:
            mapp = LEVEL_MAP_003
        else:
            mapp = 0
            Game(0)
        if mapp:
            for row_index, row in enumerate(mapp):
                for col_index, col in enumerate(row):
                    x = col_index * TILESIZE
                    y = row_index * TILESIZE

                    if col == '-':
                        Tile((x, y), './graphics/test/wall_horizontal.png',
                             (self.visible_sprites, self.obstacle_sprites))
                    if col == '[':
                        Tile((x, y), './graphics/test/wall_horizontal_left.png',
                             (self.visible_sprites, self.obstacle_sprites))
                    if col == ']':
                        Tile((x, y), './graphics/test/wall_horizontal_right.png',
                             (self.visible_sprites, self.obstacle_sprites))
                    if col == '|':
                        Tile((x, y), './graphics/test/wall_vertical.png',
                             (self.visible_sprites, self.obstacle_sprites))
                    if col == '/':
                        Tile((x, y), './graphics/test/wall_top_left.png',
                             (self.visible_sprites, self.obstacle_sprites))
                    if col == '\\':
                        Tile((x, y), './graphics/test/wall_bottom_left.png',
                             (self.visible_sprites, self.obstacle_sprites))
                    if col == '<':
                        Tile((x, y), './graphics/test/wall_vertical_top.png',
                             (self.visible_sprites, self.obstacle_sprites))
                    if col == '>':
                        Tile((x, y), './graphics/test/wall_vertical_bottom.png',
                             (self.visible_sprites, self.obstacle_sprites))
                    if col == 'r':
                        Tile((x, y), './graphics/test/stone_red.png',
                             (self.visible_sprites, self.destructible_sprites))
                    if col == 'y':
                        Tile((x, y), './graphics/test/stone_yellow.png',
                             (self.visible_sprites, self.destructible_sprites))

    # бегущий текст диалогов
    def draw_text(self, text, font, color, x, y, frun):
        timer = pygame.time.Clock()
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = (x - 10, y)
        counter = 0
        speed = 1

        while frun is True:
            timer.tick(60)
            if counter < speed * len(text):
                counter += 1

            text_surface = font.render(text[0:counter // speed], True, 'white')
            self.display_surface.blit(text_surface, text_rect)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == KEYDOWN and event.key == K_f:
                    self.d_num += 1
                    frun = False
                    break
                elif event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    print("terminated")
                    pygame.quit()
                    sys.exit()

    def run(self):
        self.visible_sprites.draw(self.display_surface)
        self.visible_sprites.update()
        # загрузка изображения Роджера # upd гифка не работает
        image = pygame.image.load(
            './graphics/test/ezgif-3-5db019ee2f.gif').convert_alpha()
        image_bunny = image
        image_bunny = pygame.transform.scale(image_bunny, (120, 150))
        self.display_surface.blit(image_bunny, (1000, 750))

        if self.level == 1:
            dialogue = self.lvl1_dialogue
            mapp = LEVEL_MAP_001
            ball_level = 1
        elif self.level == 2:
            dialogue = self.lvl2_dialogue
            mapp = LEVEL_MAP_002
            ball_level = 2
        elif self.level == 3:
            dialogue = self.lvl3_dialogue
            mapp = LEVEL_MAP_003
            ball_level = 3
        if self.dialogue is True:
            run = True
            font = pygame.font.Font('./graphics/test/ComicoroRu_0.ttf', 40)
            text_surface2 = font.render('Для промотки диалога нажмите f', True, '#80A268')
            text_rect1 = text_surface2.get_rect()
            text_rect1.center = (585, 880)
            self.display_surface.blit(text_surface2, text_rect1)
            # запуск диалога
            if self.d_num != len(dialogue):
                self.draw_text(dialogue[self.d_num], font, 'white', 600, 800, run)

            else:
                # после окончания диалога появляется ракетка и двигается мячик
                self.d_num = 0
                self.dialogue = False
                for row_index, row in enumerate(mapp):
                    for col_index, col in enumerate(row):
                        x = col_index * TILESIZE
                        y = row_index * TILESIZE

                        if col == 'p':
                            self.paddle = Paddle((x, y), (self.visible_sprites, self.movable_sprites),
                                                 self.obstacle_sprites)
                        if col == 'b':
                            self.ball = Ball((x, y),
                                             (self.visible_sprites,),
                                             self.obstacle_sprites,
                                             self.movable_sprites,
                                             self.destructible_sprites, ball_level)
        else:

            # если мячик за пределами площадкки
            if self.ball.lose is True:
                font = pygame.font.Font('./graphics/test/ComicoroRu_0.ttf', 40)
                text_surface = font.render('Попробуй снова!', True, 'white')
                text_rect = text_surface.get_rect()
                text_rect.center = (600, 800)
                self.display_surface.blit(text_surface, text_rect)
                self.d_num = 0
                self.dialogue = False

                # удаление оставшихся спрайтов после проигрыша и запуск новой ракетки и меча после нажатия f
                for event in pygame.event.get():
                    if event.type == KEYDOWN and event.key == K_f:
                        for i in self.destructible_sprites:
                            i.kill()
                        self.create_map()
                        for row_index, row in enumerate(mapp):
                            for col_index, col in enumerate(row):
                                x = col_index * TILESIZE
                                y = row_index * TILESIZE

                                if col == 'p':
                                    self.paddle.kill()
                                    self.paddle = Paddle((x, y),
                                                         (self.visible_sprites, self.movable_sprites),
                                                         self.obstacle_sprites)
                                if col == 'b':
                                    self.ball = Ball((x, y),
                                                     (self.visible_sprites,),
                                                     self.obstacle_sprites,
                                                     self.movable_sprites,
                                                     self.destructible_sprites, ball_level)
                        break
                    elif event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        print("terminated")
                        pygame.quit()
                        sys.exit()
        pygame.display.flip()


# основной цикл игры
class Game:
    def __init__(self, lvl):
        print("BunBricky started")
        # main
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.font = pygame.font.Font('./graphics/test/ComicoroRu_0.ttf', 40)
        pygame.display.set_caption('BunBricky')
        pygame.display.set_icon(pygame.image.load("./graphics/test/bunny-Sheet2.ico"))
        self.clock = pygame.time.Clock()
        if lvl == 0:
            self.game_over()
        else:
            self.level = Level(lvl)

    # функция для отображения текста на экране
    def draw_text(self, text, font, color, x, y):
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = (x, y)
        self.screen.blit(text_surface, text_rect)

    # главное меню
    def main_menu(self):
        while True:
            # кнопка "Начать игру"
            bg_image = pygame.image.load("./graphics/test/back1.png").convert_alpha()
            scaled_bg = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
            self.screen.blit(scaled_bg, (0, 0))
            font = pygame.font.Font('./graphics/test/ComicoroRu_0.ttf', 70)
            text_surface = font.render('BunBricky', True, 'white')
            text_rect = text_surface.get_rect()
            text_rect.center = (640, 300)
            self.screen.blit(text_surface, text_rect)
            start_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 50)
            pygame.draw.rect(self.screen, 'white', start_button)
            self.draw_text("Начать игру", self.font, 'black', start_button.centerx, start_button.centery)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if start_button.collidepoint(event.pos):
                        self.level_menu()

    # меню уровней
    def level_menu(self):
        while True:
            bg_image = pygame.image.load("./graphics/test/back2.png").convert_alpha()
            scaled_bg = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
            self.screen.blit(scaled_bg, (0, 0))
            self.draw_text("Меню уровней", self.font, 'white', WIDTH // 2, HEIGHT // 4)

            # кнопки уровней
            level_buttons = []
            for i in range(1, 4):
                level_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + i * 60, 200, 50)
                pygame.draw.rect(self.screen, 'white', level_button)
                self.draw_text(f"Уровень {i}", self.font, 'black', level_button.centerx, level_button.centery)
                level_buttons.append(level_button)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for i, button in enumerate(level_buttons):
                        if button.collidepoint(event.pos):
                            if i + 1 == 1:
                                self.level = Level(1)
                                self.run()
                            elif i + 1 == 2:
                                self.level = Level(2)
                                self.run()
                            elif i + 1 == 3:
                                self.level = Level(3)
                                self.run()
                            else:
                                self.game_over(self)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    print("terminated")
                    pygame.quit()
                    sys.exit()

            # очистить экран
            self.screen.fill('#152808')
            pygame.draw.rect(self.screen, '#132307', pygame.Rect(30, 730, WIDTH - 60, 300))
            pygame.draw.rect(self.screen, '#665D25', pygame.Rect(30, 730, WIDTH - 60, 300), 5)
            self.level.run()

            pygame.display.flip()
            self.clock.tick(FPS)

    # экран победы
    def game_over(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    print("terminated")
                    pygame.quit()
                    sys.exit()
            bg_image = pygame.image.load("./graphics/test/back3.png").convert_alpha()
            scaled_bg = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
            self.screen.blit(scaled_bg, (0, 0))
            font = pygame.font.Font('./graphics/test/ComicoroRu_0.ttf', 60)
            text_surface = font.render('Поздравляю с победой, ты настоящий мастер Арканоида!', True,
                                       'white')
            text_rect = text_surface.get_rect()
            text_rect.center = (WIDTH // 2, HEIGHT // 4)
            self.screen.blit(text_surface, text_rect)
            image = pygame.image.load(
                './graphics/test/ezgif-3-5db019ee2f.gif').convert_alpha()
            image_bunny = image
            image_bunny = pygame.transform.scale(image_bunny, (200, 300))
            self.screen.blit(image_bunny, (400, 500))
            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == '__main__':
    game = Game(1)
    game.main_menu()
