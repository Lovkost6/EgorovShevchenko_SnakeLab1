import pygame
import random
import time
import json
import os
from enum import Enum

# Типы еды
class FoodType(Enum):
    NORMAL = 1
    BONUS = 2
    SPEED = 3
    SLOW = 4

class Config:
    # Цвета
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    GRAY = (200, 200, 200)
    YELLOW = (255, 255, 0)
    PURPLE = (128, 0, 128)
    ORANGE = (255, 165, 0)
    GOLD = (255, 215, 0)  # Новый цвет для счета
    
    # Настройки экрана
    WIDTH, HEIGHT = 800, 600
    GRID_SIZE = 20
    GRID_WIDTH = WIDTH // GRID_SIZE
    GRID_HEIGHT = HEIGHT // GRID_SIZE
    
    # Настройки игры
    FPS = 60
    INITIAL_SPEED = 8
    SPEED_INCREMENT = 1
    SCORE_FILE = "highscores.json"
    
    # Вероятности появления разных типов еды
    FOOD_PROBABILITIES = {
        FoodType.NORMAL: 0.7,   # 70%
        FoodType.BONUS: 0.2,    # 20%
        FoodType.SPEED: 0.05,   # 5%
        FoodType.SLOW: 0.05     # 5%
    }
    
    # Очки за разные типы еды
    FOOD_SCORES = {
        FoodType.NORMAL: 10,
        FoodType.BONUS: 30,
        FoodType.SPEED: 15,
        FoodType.SLOW: 15
    }
    
    # Длительность эффектов (в кадрах)
    EFFECT_DURATION = 150

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.load_sounds()
        
    def load_sounds(self):
        try:
            # Создаем простые звуки программно, если нет файлов
            self.create_default_sounds()
        except Exception as e:
            print(f"Ошибка загрузки звуков: {e}")
    
    def create_default_sounds(self):
        # Создаем простые звуковые эффекты
        self.sounds['eat'] = pygame.mixer.Sound(self.generate_beep(440, 0.1))
        self.sounds['bonus'] = pygame.mixer.Sound(self.generate_beep(880, 0.2))
        self.sounds['game_over'] = pygame.mixer.Sound(self.generate_beep(220, 0.5))
        self.sounds['effect'] = pygame.mixer.Sound(self.generate_beep(660, 0.3))
    
    def generate_beep(self, frequency, duration):
        sample_rate = 44100
        amplitude = 4096
        n_samples = int(round(duration * sample_rate))
        
        buf = numpy.zeros((n_samples, 2), dtype=numpy.int16)
        for s in range(n_samples):
            t = float(s) / sample_rate
            buf[s][0] = amplitude * math.sin(2 * math.pi * frequency * t)
            buf[s][1] = amplitude * math.sin(2 * math.pi * frequency * t)
        
        return pygame.sndarray.make_sound(buf)
    
    def play(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

class Obstacle:
    def __init__(self, snake_positions):
        self.positions = self.generate_obstacle(snake_positions)
        self.color = Config.BLACK
        
    def generate_obstacle(self, snake_positions):
        # Генерируем простой барьер из 3-5 блоков
        length = random.randint(3, 5)
        start_x = random.randint(5, Config.GRID_WIDTH - length - 5)
        start_y = random.randint(5, Config.GRID_HEIGHT - 5)
        
        positions = []
        for i in range(length):
            pos = (start_x + i, start_y)
            if pos not in snake_positions:
                positions.append(pos)
        
        return positions
    
    def draw(self, surface):
        for position in self.positions:
            rect = pygame.Rect(
                position[0] * Config.GRID_SIZE, 
                position[1] * Config.GRID_SIZE, 
                Config.GRID_SIZE, Config.GRID_SIZE
            )
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, Config.RED, rect, 2)  # Более толстая обводка

class Food:
    def __init__(self, snake_positions, obstacles):
        self.food_type = self.choose_food_type()
        self.position = self.randomize_position(snake_positions, obstacles)
        self.color = self.get_color()
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 5000  # 5 секунд для бонусной еды
        
    def choose_food_type(self):
        return random.choices(
            list(Config.FOOD_PROBABILITIES.keys()),
            weights=list(Config.FOOD_PROBABILITIES.values())
        )[0]
    
    def get_color(self):
        colors = {
            FoodType.NORMAL: Config.RED,
            FoodType.BONUS: Config.YELLOW,
            FoodType.SPEED: Config.BLUE,
            FoodType.SLOW: Config.PURPLE
        }
        return colors[self.food_type]
    
    def randomize_position(self, snake_positions, obstacles):
        while True:
            position = (
                random.randint(0, Config.GRID_WIDTH - 1),
                random.randint(0, Config.GRID_HEIGHT - 1)
            )
            if (position not in snake_positions and 
                not any(position in obs.positions for obs in obstacles)):
                return position
    
    def is_expired(self):
        if self.food_type != FoodType.NORMAL:
            return pygame.time.get_ticks() - self.spawn_time > self.lifetime
        return False
    
    def draw(self, surface):
        rect = pygame.Rect(
            self.position[0] * Config.GRID_SIZE, 
            self.position[1] * Config.GRID_SIZE, 
            Config.GRID_SIZE, Config.GRID_SIZE
        )
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, Config.BLACK, rect, 2)  # Более толстая обводка
        
        # Анимация мигания для бонусной еды
        if self.food_type != FoodType.NORMAL:
            if (pygame.time.get_ticks() // 200) % 2 == 0:
                inner_rect = pygame.Rect(
                    rect.x + 4, rect.y + 4,
                    Config.GRID_SIZE - 8, Config.GRID_SIZE - 8
                )
                pygame.draw.rect(surface, Config.WHITE, inner_rect)

class Snake:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.positions = [(Config.GRID_WIDTH // 2, Config.GRID_HEIGHT // 2)]
        self.direction = (1, 0)
        self.grow = False
        self.color = Config.GREEN
        self.effects = {}
        
    def add_effect(self, effect_type, duration):
        self.effects[effect_type] = duration
        
    def update_effects(self):
        for effect in list(self.effects.keys()):
            self.effects[effect] -= 1
            if self.effects[effect] <= 0:
                del self.effects[effect]
    
    def has_effect(self, effect_type):
        return effect_type in self.effects
    
    def get_head_position(self):
        return self.positions[0]
    
    def move(self, obstacles):
        head_x, head_y = self.get_head_position()
        dir_x, dir_y = self.direction
        
        # Учет эффекта скорости
        speed_multiplier = 2 if self.has_effect('speed') else 0.5 if self.has_effect('slow') else 1
        if speed_multiplier != 1:
            dir_x = int(dir_x * speed_multiplier)
            dir_y = int(dir_y * speed_multiplier)
        
        new_x = (head_x + dir_x) % Config.GRID_WIDTH
        new_y = (head_y + dir_y) % Config.GRID_HEIGHT
        
        # Проверка на столкновение с собой
        if (new_x, new_y) in self.positions[1:]:
            return False
            
        # Проверка на столкновение с препятствиями
        for obstacle in obstacles:
            if (new_x, new_y) in obstacle.positions:
                return False
        
        self.positions.insert(0, (new_x, new_y))
        if not self.grow:
            self.positions.pop()
        else:
            self.grow = False
            
        self.update_effects()
        return True
    
    def change_direction(self, new_direction):
        if (new_direction[0] * -1, new_direction[1] * -1) != self.direction:
            self.direction = new_direction
    
    def grow_snake(self, amount=1):
        self.grow = True
    
    def draw(self, surface):
        for i, position in enumerate(self.positions):
            rect = pygame.Rect(
                position[0] * Config.GRID_SIZE, 
                position[1] * Config.GRID_SIZE, 
                Config.GRID_SIZE, Config.GRID_SIZE
            )
            
            # Разные цвета для эффектов
            if self.has_effect('speed'):
                color = Config.BLUE
            elif self.has_effect('slow'):
                color = Config.PURPLE
            else:
                color = (0, 180, 0) if i == 0 else (0, 220, 0)  # Более насыщенные зеленые
                
            pygame.draw.rect(surface, color, rect)
            # Более толстая обводка для лучшей видимости без сетки
            pygame.draw.rect(surface, Config.BLACK, rect, 2)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
        pygame.display.set_caption('Змейка - Улучшенная версия')
        self.clock = pygame.time.Clock()
        
        # Увеличенные шрифты
        self.font = pygame.font.SysFont('Arial', 32)  # Было 24
        self.big_font = pygame.font.SysFont('Arial', 56)  # Было 48
        self.small_font = pygame.font.SysFont('Arial', 20)  # Было 16
        
        # Инициализация звука
        try:
            pygame.mixer.init()
            self.sound_manager = SoundManager()
        except:
            self.sound_manager = None
            print("Звук недоступен")
            
        self.reset_game()
        self.load_highscores()
        
    def reset_game(self):
        self.snake = Snake()
        self.obstacles = [Obstacle(self.snake.positions) for _ in range(3)]
        self.food = Food(self.snake.positions, self.obstacles)
        self.score = 0
        self.game_over = False
        self.paused = False
        self.in_menu = True
        self.speed = Config.INITIAL_SPEED
        self.level = 1
        self.effect_timer = 0
        
    def load_highscores(self):
        self.highscores = []
        if os.path.exists(Config.SCORE_FILE):
            try:
                with open(Config.SCORE_FILE, 'r') as f:
                    self.highscores = json.load(f)
            except:
                self.highscores = []
    
    def save_highscore(self, score):
        self.highscores.append(score)
        self.highscores.sort(reverse=True)
        self.highscores = self.highscores[:5]
        
        with open(Config.SCORE_FILE, 'w') as f:
            json.dump(self.highscores, f)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.KEYDOWN:
                if self.in_menu:
                    self.handle_menu_events(event)
                elif self.game_over:
                    self.handle_game_over_events(event)
                else:
                    self.handle_game_events(event)
        
        return True
    
    def handle_menu_events(self, event):
        if event.key == pygame.K_RETURN:
            self.in_menu = False
        elif event.key == pygame.K_ESCAPE:
            return False
        elif event.key == pygame.K_c:
            self.show_controls = not self.show_controls
    
    def handle_game_over_events(self, event):
        if event.key == pygame.K_RETURN:
            self.reset_game()
        elif event.key == pygame.K_ESCAPE:
            self.in_menu = True
    
    def handle_game_events(self, event):
        if event.key == pygame.K_UP:
            self.snake.change_direction((0, -1))
        elif event.key == pygame.K_DOWN:
            self.snake.change_direction((0, 1))
        elif event.key == pygame.K_LEFT:
            self.snake.change_direction((-1, 0))
        elif event.key == pygame.K_RIGHT:
            self.snake.change_direction((1, 0))
        elif event.key == pygame.K_p:
            self.paused = not self.paused
        elif event.key == pygame.K_ESCAPE:
            self.in_menu = True
        elif event.key == pygame.K_w:
            self.snake.change_direction((0, -1))
        elif event.key == pygame.K_s:
            self.snake.change_direction((0, 1))
        elif event.key == pygame.K_a:
            self.snake.change_direction((-1, 0))
        elif event.key == pygame.K_d:
            self.snake.change_direction((1, 0))
    
    def update(self):
        if self.paused or self.game_over or self.in_menu:
            return
            
        # Движение змейки
        if not self.snake.move(self.obstacles):
            self.game_over = True
            if self.sound_manager:
                self.sound_manager.play('game_over')
            self.save_highscore(self.score)
            return
        
        # Проверка на съедание еды
        if self.snake.get_head_position() == self.food.position:
            self.handle_food_collision()
        
        # Проверка на истечение времени жизни еды
        if self.food.is_expired():
            self.food = Food(self.snake.positions, self.obstacles)
    
    def handle_food_collision(self):
        score = Config.FOOD_SCORES[self.food.food_type]
        self.score += score
        
        if self.sound_manager:
            if self.food.food_type == FoodType.BONUS:
                self.sound_manager.play('bonus')
            else:
                self.sound_manager.play('eat')
        
        # Обработка эффектов еды
        if self.food.food_type == FoodType.SPEED:
            self.snake.add_effect('speed', Config.EFFECT_DURATION)
            if self.sound_manager:
                self.sound_manager.play('effect')
        elif self.food.food_type == FoodType.SLOW:
            self.snake.add_effect('slow', Config.EFFECT_DURATION)
            if self.sound_manager:
                self.sound_manager.play('effect')
        
        self.snake.grow_snake()
        self.food = Food(self.snake.positions, self.obstacles)
        
        # Увеличение уровня каждые 50 очков
        if self.score % 50 == 0:
            self.speed += Config.SPEED_INCREMENT
            self.level += 1
            # Добавляем новое препятствие каждый уровень
            if self.level % 2 == 0:
                self.obstacles.append(Obstacle(self.snake.positions))
    
    def draw_hud(self):
        # Счет с золотым цветом
        score_text = self.font.render(f'Счет: {self.score}', True, Config.GOLD)
        level_text = self.font.render(f'Уровень: {self.level}', True, Config.BLACK)
        
        self.screen.blit(score_text, (20, 20))  # Увеличил отступ
        self.screen.blit(level_text, (20, 60))
        
        # Информация об эффектах
        y_offset = 100
        if self.snake.has_effect('speed'):
            effect_text = self.small_font.render('УСКОРЕНИЕ!', True, Config.BLUE)
            self.screen.blit(effect_text, (20, y_offset))
            y_offset += 25
        if self.snake.has_effect('slow'):
            effect_text = self.small_font.render('ЗАМЕДЛЕНИЕ!', True, Config.PURPLE)
            self.screen.blit(effect_text, (20, y_offset))
        
        if self.paused:
            pause_text = self.big_font.render('ПАУЗА', True, Config.BLUE)
            self.screen.blit(pause_text, (Config.WIDTH//2 - 100, Config.HEIGHT//2 - 40))
            
            # Подсказки управления в паузе
            controls_text = self.small_font.render('Управление: Стрелки или WASD', True, Config.BLACK)
            self.screen.blit(controls_text, (Config.WIDTH//2 - 150, Config.HEIGHT//2 + 20))
    
    def draw_menu(self):
        # Красивый фон меню
        self.screen.fill((240, 240, 240))  # Светло-серый фон
        
        title = self.big_font.render('ЗМЕЙКА PRO', True, Config.GREEN)
        start = self.font.render('ENTER - Начать игру', True, Config.BLUE)
        exit_text = self.font.render('ESC - Выход', True, Config.RED)
        
        # Описание особенностей
        features = [
            '• Разные типы еды с эффектами',
            '• Препятствия на поле',
            '• Система уровней сложности',
            '• Топ-5 рекордов'
        ]
        
        self.screen.blit(title, (Config.WIDTH//2 - 140, 60))
        self.screen.blit(start, (Config.WIDTH//2 - 150, 180))
        self.screen.blit(exit_text, (Config.WIDTH//2 - 100, 230))
        
        # Рекорды
        highscores_text = self.font.render('ТОП-5 РЕКОРДОВ:', True, Config.GOLD)
        self.screen.blit(highscores_text, (Config.WIDTH//2 - 150, 300))
        
        for i, score in enumerate(self.highscores[:5]):
            score_text = self.font.render(f'{i+1}. {score}', True, Config.BLACK)
            self.screen.blit(score_text, (Config.WIDTH//2 - 50, 340 + i*40))
        
        # Особенности игры
        features_title = self.font.render('ОСОБЕННОСТИ:', True, Config.PURPLE)
        self.screen.blit(features_title, (Config.WIDTH//2 - 120, 550))
        
        for i, feature in enumerate(features):
            feature_text = self.small_font.render(feature, True, Config.BLACK)
            self.screen.blit(feature_text, (Config.WIDTH//2 - 150, 590 + i*25))
    
    def draw_game_over(self):
        overlay = pygame.Surface((Config.WIDTH, Config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # Более темный overlay
        self.screen.blit(overlay, (0, 0))
        
        game_over = self.big_font.render('ИГРА ОКОНЧЕНА!', True, Config.RED)
        score_text = self.font.render(f'ВАШ СЧЕТ: {self.score}', True, Config.GOLD)  # Золотой цвет счета
        restart = self.font.render('ENTER - Новая игра', True, Config.GREEN)
        menu = self.font.render('ESC - Меню', True, Config.WHITE)
        
        self.screen.blit(game_over, (Config.WIDTH//2 - 200, Config.HEIGHT//2 - 80))
        self.screen.blit(score_text, (Config.WIDTH//2 - 100, Config.HEIGHT//2 - 10))
        self.screen.blit(restart, (Config.WIDTH//2 - 150, Config.HEIGHT//2 + 50))
        self.screen.blit(menu, (Config.WIDTH//2 - 80, Config.HEIGHT//2 + 100))
    
    def draw(self):
        # Фон без сетки - просто белый
        self.screen.fill(Config.WHITE)
        
        if self.in_menu:
            self.draw_menu()
        else:
            # Рисуем препятствия
            for obstacle in self.obstacles:
                obstacle.draw(self.screen)
            
            self.snake.draw(self.screen)
            self.food.draw(self.screen)
            self.draw_hud()
            
            if self.game_over:
                self.draw_game_over()
        
        pygame.display.update()
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            
            if not self.in_menu and not self.game_over and not self.paused:
                self.update()
            
            self.draw()
            self.clock.tick(self.speed if not self.paused else Config.FPS)
        
        pygame.quit()

# Необходимые импорты для генерации звуков
import numpy
import math

def main():
    pygame.init()
    game = Game()
    game.run()

if __name__ == "__main__":
    main()