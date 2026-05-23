import pygame
import sys
import time

pygame.init()

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (135, 206, 235)
YELLOW = (255, 255, 0)
GREEN = (0, 128, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)

TOWER_WIDTH = 10
TOWER_HEIGHT = 200
DISK_HEIGHT = 20
BASE_Y = 350
TOWER_X = [150, 300, 450]

FONT = pygame.font.SysFont(None, 36)
SMALL_FONT = pygame.font.SysFont(None, 24)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tower of Hanoi")

clock = pygame.time.Clock()

def get_moves(disks, src, dest, intermediate):
    moves = []
    if not disks:
        return moves
    moves.extend(get_moves(disks[1:], src, intermediate, dest))
    moves.append((disks[0], src, dest))
    moves.extend(get_moves(disks[1:], intermediate, dest, src))
    return moves

def init_towers(num_disks):
    towers = [[], [], []]
    towers[0] = list(range(num_disks, 0, -1))
    return towers

def draw_towers(towers):
    for i in range(3):
        x = TOWER_X[i]
        pygame.draw.rect(screen, GRAY, (x - TOWER_WIDTH // 2, BASE_Y - TOWER_HEIGHT, TOWER_WIDTH, TOWER_HEIGHT))
        pygame.draw.rect(screen, GRAY, (x - 50, BASE_Y, 100, 10))
        for j, disk in enumerate(towers[i]):
            width = 20 + disk * 10
            pygame.draw.rect(screen, GREEN if disk % 2 else BLUE, (x - width // 2, BASE_Y - (j + 1) * DISK_HEIGHT, width, DISK_HEIGHT))
            pygame.draw.rect(screen, BLACK, (x - width // 2, BASE_Y - (j + 1) * DISK_HEIGHT, width, DISK_HEIGHT), 1)

def draw_buttons():
    buttons = []
    for i, num in enumerate([3, 4, 5]):
        rect = pygame.Rect(50 + i * 100, 50, 80, 40)
        pygame.draw.rect(screen, GRAY, rect)
        text = SMALL_FONT.render(f"{num} Disks", True, BLACK)
        screen.blit(text, (rect.x + 10, rect.y + 10))
        buttons.append((rect, num))
    return buttons

def draw_mode_buttons():
    manual_rect = pygame.Rect(50, 120, 80, 40)
    auto_rect = pygame.Rect(150, 120, 80, 40)
    pygame.draw.rect(screen, GRAY, manual_rect)
    pygame.draw.rect(screen, GRAY, auto_rect)
    manual_text = SMALL_FONT.render("Manual", True, BLACK)
    auto_text = SMALL_FONT.render("Auto", True, BLACK)
    screen.blit(manual_text, (manual_rect.x + 10, manual_rect.y + 10))
    screen.blit(auto_text, (auto_rect.x + 10, auto_rect.y + 10))
    return manual_rect, auto_rect

def can_move(towers, src, dest):
    if not towers[src]:
        return False
    if not towers[dest]:
        return True
    return towers[src][-1] < towers[dest][-1]

def move_disk(towers, src, dest):
    if can_move(towers, src, dest):
        disk = towers[src].pop()
        towers[dest].append(disk)
        return True
    return False

def check_win(towers, num_disks):
    return len(towers[2]) == num_disks

def draw_win_screen():
    screen.fill(BLUE)
    text = FONT.render("Solved!", True, GREEN)
    screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
    home_rect = pygame.Rect(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2, 100, 40)
    pygame.draw.rect(screen, GRAY, home_rect)
    home_text = SMALL_FONT.render("Home", True, BLACK)
    screen.blit(home_text, (home_rect.x + 25, home_rect.y + 10))
    pygame.display.flip()
    return home_rect

def main():
    num_disks = None
    mode = None
    towers = None
    selected = None
    moves = []
    move_index = 0
    last_move = 0
    running = True
    game_over = False

    while running:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if game_over:
                    home_rect = draw_win_screen()
                    if home_rect.collidepoint(pos):
                        num_disks = None
                        mode = None
                        towers = None
                        selected = None
                        moves = []
                        move_index = 0
                        last_move = 0
                        game_over = False
                elif num_disks is None:
                    buttons = draw_buttons()
                    for rect, num in buttons:
                        if rect.collidepoint(pos):
                            num_disks = num
                            break
                elif mode is None:
                    manual_rect, auto_rect = draw_mode_buttons()
                    if manual_rect.collidepoint(pos):
                        mode = 'manual'
                        towers = init_towers(num_disks)
                    elif auto_rect.collidepoint(pos):
                        mode = 'auto'
                        towers = init_towers(num_disks)
                        disks = list(range(num_disks, 0, -1))
                        moves = get_moves(disks, 0, 2, 1)
                elif mode == 'manual':
                    for i in range(3):
                        x = TOWER_X[i]
                        if x - 50 <= pos[0] <= x + 50 and BASE_Y - TOWER_HEIGHT <= pos[1] <= BASE_Y:
                            if selected is None:
                                if towers[i]:
                                    selected = i
                            else:
                                if move_disk(towers, selected, i):
                                    if check_win(towers, num_disks):
                                        game_over = True
                                selected = None
                            break

        if game_over:
            draw_win_screen()
        elif num_disks is None:
            draw_buttons()
        elif mode is None:
            draw_mode_buttons()
        elif mode == 'auto':
            draw_towers(towers)
            if move_index < len(moves) and time.time() - last_move > 1:
                disk, src, dest = moves[move_index]
                move_disk(towers, src, dest)
                move_index += 1
                last_move = time.time()
            if move_index >= len(moves):
                game_over = True
        elif mode == 'manual':
            draw_towers(towers)
            if selected is not None:
                pygame.draw.circle(screen, RED, (TOWER_X[selected], BASE_Y - TOWER_HEIGHT - 20), 10)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()