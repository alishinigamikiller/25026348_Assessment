import pygame
import sys
import random

# --- Pygame Initialization ---
pygame.init()

# --- Game Configuration ---
ROWS = 16
COLS = 30
MINES = 99
CELL_SIZE = 30

SCREEN_WIDTH = COLS * CELL_SIZE
SCREEN_HEIGHT = ROWS * CELL_SIZE + 50 # Add space at the bottom for UI
TITLE = "PyMinesweeper"
FPS = 60

# --- Colors ---
COLOR_HIDDEN = (192, 192, 192)      # Light gray
COLOR_REVEALED = (220, 220, 220)    # Lighter gray
COLOR_MINE = (255, 0, 0)            # Red
COLOR_FLAG = (255, 128, 0)          # Orange
COLOR_GRID = (128, 128, 128)        # Dark gray
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
# Colors for numbers 1-8
COLOR_NUMBERS = {
    1: (0, 0, 255),   # Blue
    2: (0, 128, 0),   # Green
    3: (255, 0, 0),   # Red
    4: (0, 0, 128),   # Dark Blue
    5: (128, 0, 0),   # Maroon
    6: (0, 128, 128), # Teal
    7: (0, 0, 0),     # Black
    8: (128, 128, 128) # Gray
}

# --- Game Setup ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()
main_font = pygame.font.Font(None, 36) # Font for numbers
ui_font = pygame.font.Font(None, 42) # Font for messages

# --- Cell Class (Helper) ---
class Cell:
    """Holds all data for a single cell."""
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        
        self.is_mine = False
        self.adjacent_mines = 0
        self.is_revealed = False
        self.is_flagged = False

    def draw(self, surface):
        """Draws the cell based on its state."""
        # --- Draw Background ---
        if self.is_revealed:
            pygame.draw.rect(surface, COLOR_REVEALED, self.rect)
            # If revealed, draw what's inside
            if self.is_mine:
                # Draw a mine (red circle)
                center = self.rect.center
                pygame.draw.circle(surface, COLOR_MINE, center, CELL_SIZE // 3)
            elif self.adjacent_mines > 0:
                # Draw the number
                text_surf = main_font.render(str(self.adjacent_mines), True, COLOR_NUMBERS[self.adjacent_mines])
                text_rect = text_surf.get_rect(center=self.rect.center)
                surface.blit(text_surf, text_rect)
        else:
            # Not revealed, draw hidden
            pygame.draw.rect(surface, COLOR_HIDDEN, self.rect)
            if self.is_flagged:
                # Draw a flag (Orange 'F')
                text_surf = main_font.render("F", True, COLOR_FLAG)
                text_rect = text_surf.get_rect(center=self.rect.center)
                surface.blit(text_surf, text_rect)
        
        # --- Draw Grid Border ---
        pygame.draw.rect(surface, COLOR_GRID, self.rect, 1)

# --- Game Functions ---
def create_board():
    """Initializes the 2D grid of Cell objects."""
    board = [[Cell(row, col) for col in range(COLS)] for row in range(ROWS)]
    
    # --- 1. Place Mines ---
    placed_mines = 0
    while placed_mines < MINES:
        row = random.randint(0, ROWS - 1)
        col = random.randint(0, COLS - 1)
        
        if not board[row][col].is_mine:
            board[row][col].is_mine = True
            placed_mines += 1
            
    # --- 2. Calculate Adjacent Mines ---
    for r in range(ROWS):
        for c in range(COLS):
            if not board[r][c].is_mine:
                count = 0
                # Check all 8 neighbors
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        
                        nr, nc = r + dr, c + dc
                        
                        # Check boundaries
                        if 0 <= nr < ROWS and 0 <= nc < COLS and board[nr][nc].is_mine:
                            count += 1
                board[r][c].adjacent_mines = count
                
    return board

def reveal_cell(board, row, col):
    """
    Recursively reveals cells (flood fill).
    Returns False if a mine was hit, True otherwise.
    """
    cell = board[row][col]
    
    # --- Base cases to stop recursion ---
    if cell.is_flagged or cell.is_revealed:
        return True # Not a mine, but don't continue

    # --- Process this cell ---
    cell.is_revealed = True
    
    if cell.is_mine:
        return False # Hit a mine! Game over.

    # --- Recursive step (if cell is 0) ---
    if cell.adjacent_mines == 0:
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                
                nr, nc = row + dr, col + dc
                
                # Check boundaries and if not already revealed
                if 0 <= nr < ROWS and 0 <= nc < COLS and not board[nr][nc].is_revealed:
                    reveal_cell(board, nr, nc) # Recursive call
                    
    return True # Safe

def check_win_condition(board):
    """Checks if the player has won."""
    for row in range(ROWS):
        for col in range(COLS):
            cell = board[row][col]
            # If there's a non-mine cell that is still hidden, not a win
            if not cell.is_mine and not cell.is_revealed:
                return False
    return True # All non-mine cells are revealed

def draw_board(board):
    """Draws the entire grid."""
    for row in range(ROWS):
        for col in range(COLS):
            board[row][col].draw(screen)

def draw_ui(message, color):
    """Draws the game over/win message."""
    # Dim the screen
    dim_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    dim_surface.set_alpha(150)
    dim_surface.fill(COLOR_BLACK)
    screen.blit(dim_surface, (0, 0))

    # Draw the text
    text_surf = ui_font.render(message, True, color)
    text_rect = text_surf.get_rect(center=(SCREEN_WIDTH / 2, (ROWS * CELL_SIZE) / 2 - 40))
    screen.blit(text_surf, text_rect)
    
    text_surf_2 = ui_font.render("Press 'R' to restart", True, COLOR_WHITE)
    text_rect_2 = text_surf_2.get_rect(center=(SCREEN_WIDTH / 2, (ROWS * CELL_SIZE) / 2 + 10))
    screen.blit(text_surf_2, text_rect_2)

# --- Main Game Loop ---
def main():
    running = True
    board = create_board()
    game_over = False
    won = False
    
    flags_placed = 0

    while running:
        # --- 1. Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_r and game_over:
                    # Reset the game
                    main() # Restart by re-running main
                    return

            if game_over:
                continue # Stop processing game input if game is over

            # --- Mouse Clicks ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                # Check if click is within the grid
                if mouse_y >= ROWS * CELL_SIZE:
                    continue # Click was in the UI area, ignore

                col = mouse_x // CELL_SIZE
                row = mouse_y // CELL_SIZE
                
                cell = board[row][col]

                # --- Left Click ---
                if event.button == 1:
                    if not cell.is_flagged:
                        if not reveal_cell(board, row, col):
                            # Hit a mine!
                            game_over = True
                            won = False
                            # Reveal all other mines
                            for r in range(ROWS):
                                for c in range(COLS):
                                    if board[r][c].is_mine:
                                        board[r][c].is_revealed = True
                
                # --- Right Click ---
                elif event.button == 3:
                    if not cell.is_revealed:
                        if cell.is_flagged:
                            cell.is_flagged = False
                            flags_placed -= 1
                        else:
                            cell.is_flagged = True
                            flags_placed += 1

        # --- 2. Update (Check Win) ---
        if not game_over:
            if check_win_condition(board):
                game_over = True
                won = True

        # --- 3. Draw ---
        screen.fill(COLOR_REVEALED) # Background
        draw_board(board)
        
        # Draw UI bar at the bottom
        ui_bar_rect = pygame.Rect(0, ROWS * CELL_SIZE, SCREEN_WIDTH, 50)
        pygame.draw.rect(screen, COLOR_BLACK, ui_bar_rect)
        
        # Draw flag count
        flag_text = ui_font.render(f"Flags: {flags_placed} / {MINES}", True, COLOR_FLAG)
        flag_rect = flag_text.get_rect(midleft=(20, ui_bar_rect.centery))
        screen.blit(flag_text, flag_rect)

        if game_over:
            if won:
                draw_ui("You Win!", (0, 255, 0)) # Green
            else:
                draw_ui("You Hit a Mine!", COLOR_MINE)

        # --- 4. Flip Display ---
        pygame.display.flip()

        # --- 5. Cap Framerate ---
        clock.tick(FPS)

    # --- End of Game Loop ---
    pygame.quit()
    sys.exit()

# --- Run the Game ---
if __name__ == "__main__":
    main()
