import pygame
import random
import time

# Инициализация Pygame
pygame.init()

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Настройки экрана
WIDTH, HEIGHT = 600, 400
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE

# Настройки игры
FPS = 10

# Создание экрана
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Змейка')
clock = pygame.time.Clock()


class Snake:
    def __init__(self):
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = (1, 0)
        self.grow = False

    def get_head_position(self):
        return self.positions[0]

    def move(self):
        head_x, head_y = self.get_head_position()
        dir_x, dir_y = self.direction
        new_x = (head_x + dir_x) % GRID_WIDTH
        new_y = (head_y + dir_y) % GRID_HEIGHT

        # Проверка на столкновение с собой
        if (new_x, new_y) in self.positions[1:]:
            return False

        self.positions.insert(0, (new_x, new_y))
        if not self.grow:
            self.positions.pop()
        else:
            self.grow = False
        return True

    def change_direction(self, new_direction):
        # Запрет движения в противоположном направлении
        if (new_direction[0] * -1, new_direction[1] * -1) != self.direction:
            self.direction = new_direction

    def grow_snake(self):
        self.grow = True

    def draw(self, surface):
        for position in self.positions:
            rect = pygame.Rect(
                position[0] * GRID_SIZE,
                position[1] * GRID_SIZE,
                GRID_SIZE, GRID_SIZE
            )
            pygame.draw.rect(surface, GREEN, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)


class Food:
    def __init__(self, snake_positions):
        self.position = self.randomize_position(snake_positions)

    def randomize_position(self, snake_positions):
        while True:
            position = (
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1)
            )
            if position not in snake_positions:
                return position

    def draw(self, surface):
        rect = pygame.Rect(
            self.position[0] * GRID_SIZE,
            self.position[1] * GRID_SIZE,
            GRID_SIZE, GRID_SIZE
        )
        pygame.draw.rect(surface, RED, rect)
        pygame.draw.rect(surface, BLACK, rect, 1)


def draw_grid(surface):
    for y in range(0, HEIGHT, GRID_SIZE):
        for x in range(0, WIDTH, GRID_SIZE):
            rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(surface, WHITE, rect, 1)


def main():
    snake = Snake()
    food = Food(snake.positions)
    score = 0
    game_over = False

    while not game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    snake.change_direction((0, -1))
                elif event.key == pygame.K_DOWN:
                    snake.change_direction((0, 1))
                elif event.key == pygame.K_LEFT:
                    snake.change_direction((-1, 0))
                elif event.key == pygame.K_RIGHT:
                    snake.change_direction((1, 0))

        # Движение змейки
        if not snake.move():
            game_over = True

        # Проверка на съедание еды
        if snake.get_head_position() == food.position:
            snake.grow_snake()
            food = Food(snake.positions)
            score += 1

        # Отрисовка
        screen.fill(WHITE)
        draw_grid(screen)
        snake.draw(screen)
        food.draw(screen)

        # Отображение счета
        font = pygame.font.SysFont('Arial', 20, bold=True)
        score_text = font.render(f'Счет: {score}', True, GREEN)
        screen.blit(score_text, (5, 5))

        pygame.display.update()
        clock.tick(FPS)

    # Экран завершения игры
    font = pygame.font.SysFont('Arial', 30, bold=True)
    game_over_text = font.render(f'Игра окончена! Счет: {score}', True, BLACK)
    screen.blit(game_over_text, (WIDTH // 2 - 150, HEIGHT // 2 - 15))
    pygame.display.update()
    time.sleep(2)

    pygame.quit()


if __name__ == "__main__":
    main()