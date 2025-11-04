import pygame
import sys
import random

# --- Pygame Initialization ---
pygame.init()

# --- Game Configuration ---
# We no longer set ROWS, COLS, MINES here.
# Instead, we define difficulty settings.
DIFFICULTIES = {
    'easy': {'rows': 9, 'cols': 9, 'mines': 10},
    'medium': {'rows': 16, 'cols': 16, 'mines': 40},
    'hard': {'rows': 16, 'cols': 30, 'mines': 99} # Original settings
}

CELL_SIZE = 30
# SCREEN_WIDTH and SCREEN_HEIGHT are now dynamic

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
# We set up fonts and clock here, but the screen is set later
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

# --- Game Class ---
# We wrap all game logic and state in this class
class Game:
    def __init__(self):
        self.screen = None
        self.rows = 0
        self.cols = 0
        self.mines = 0
        self.screen_width = 0
        self.screen_height = 0
        
        self.board = []
        self.game_over = False
        self.won = False
        self.flags_placed = 0
        self.first_click = True # Added for "Safe First Click" logic
        self.start_time = None # Timer for tracking game duration

    def start_screen(self):
        """Displays the difficulty selection screen and waits for input."""
        # Use largest dimensions for start screen
        temp_width = DIFFICULTIES['hard']['cols'] * CELL_SIZE
        temp_height = DIFFICULTIES['hard']['rows'] * CELL_SIZE + 50
        self.screen = pygame.display.set_mode((temp_width, temp_height))
        pygame.display.set_caption("Choose Difficulty")

        # Text rendering
        title_text = ui_font.render("PyMinesweeper", True, COLOR_WHITE)
        any_key_text = main_font.render("Press any key to begin", True, COLOR_WHITE)
        easy_text = main_font.render("Press 'E' for Easy (9x9, 10 Mines)", True, COLOR_WHITE)
        medium_text = main_font.render("Press 'M' for Medium (16x16, 40 Mines)", True, COLOR_WHITE)
        hard_text = main_font.render("Press 'H' for Hard (16x30, 99 Mines)", True, COLOR_WHITE)
        
        # --- Phase 1: Welcome Screen ---
        phase = "welcome"
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYUP:
                    if phase == "welcome":
                        phase = "difficulty" # Move to next phase
                    elif phase == "difficulty":
                        settings = None
                        if event.key == pygame.K_e:
                            settings = DIFFICULTIES['easy']
                        elif event.key == pygame.K_m:
                            settings = DIFFICULTIES['medium']
                        elif event.key == pygame.K_h:
                            settings = DIFFICULTIES['hard']
                        
                        if settings:
                            self.rows = settings['rows']
                            self.cols = settings['cols']
                            self.mines = settings['mines']
                            self.screen_width = self.cols * CELL_SIZE
                            self.screen_height = self.rows * CELL_SIZE + 50
                            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
                            pygame.display.set_caption(TITLE)
                            return # Exit start screen
            
            # Draw
            self.screen.fill(COLOR_BLACK)
            self.screen.blit(title_text, (temp_width // 2 - title_text.get_width() // 2, 100))

            if phase == "welcome":
                self.screen.blit(any_key_text, (temp_width // 2 - any_key_text.get_width() // 2, 250))
            elif phase == "difficulty":
                self.screen.blit(easy_text, (temp_width // 2 - easy_text.get_width() // 2, 200))
                self.screen.blit(medium_text, (temp_width // 2 - medium_text.get_width() // 2, 250))
                self.screen.blit(hard_text, (temp_width // 2 - hard_text.get_width() // 2, 300))
            
            pygame.display.flip()
    def create_board(self, safe_row, safe_col):
        """
        Initializes the 2D grid of Cell objects, ensuring the first click is safe.
        Mines are placed *after* the first click, avoiding the safe cell and its neighbors.
        """
        board = [[Cell(row, col) for col in range(self.cols)] for row in range(self.rows)]
        
        # --- 1. Create a set of "unsafe" cells ---
        # This includes the clicked cell and its 8 neighbors
        unsafe_cells = set()
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = safe_row + dr, safe_col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    unsafe_cells.add((nr, nc))

        # --- 2. Place Mines ---
        placed_mines = 0
        while placed_mines < self.mines:
            row = random.randint(0, self.rows - 1)
            col = random.randint(0, self.cols - 1)
            
            # Place a mine only if it's not the first click spot or its neighbors
            if (row, col) not in unsafe_cells and not board[row][col].is_mine:
                board[row][col].is_mine = True
                placed_mines += 1
                
        # --- 3. Calculate Adjacent Mines ---
        for r in range(self.rows):
            for c in range(self.cols):
                if not board[r][c].is_mine:
                    count = 0
                    # Check all 8 neighbors
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            
                            nr, nc = r + dr, c + dc
                            
                            # Check boundaries
                            if 0 <= nr < self.rows and 0 <= nc < self.cols and board[nr][nc].is_mine:
                                count += 1
                    board[r][c].adjacent_mines = count
                    
        return board

    def reveal_cell(self, row, col):
        """
        Recursively reveals cells (flood fill).
        Returns False if a mine was hit, True otherwise.
        """
        cell = self.board[row][col]
        
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
                    if 0 <= nr < self.rows and 0 <= nc < self.cols and not self.board[nr][nc].is_revealed:
                        self.reveal_cell(nr, nc) # Recursive call
                        
        return True # Safe

    def check_win_condition(self):
        """Checks if the player has won."""
        # Don't check win condition if board hasn't been created yet
        if not self.board:
            return False
            
        for row in range(self.rows):
            for col in range(self.cols):
                cell = self.board[row][col]
                # If there's a non-mine cell that is still hidden, not a win
                if not cell.is_mine and not cell.is_revealed:
                    return False
        return True # All non-mine cells are revealed

    def draw_board(self):
        """Draws the entire grid."""
        # If board hasn't been created yet, draw empty grid
        if not self.board:
            self.draw_empty_grid()
            return
            
        for row in range(self.rows):
            for col in range(self.cols):
                self.board[row][col].draw(self.screen)

    def draw_empty_grid(self):
        """Draws an empty grid before the first click."""
        for row in range(self.rows):
            for col in range(self.cols):
                rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                # Draw hidden cell
                pygame.draw.rect(self.screen, COLOR_HIDDEN, rect)
                # Draw grid border
                pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)

    def draw_ui(self, message, color):
        """Draws the game over/win message."""
        # Dim the screen
        dim_surface = pygame.Surface((self.screen_width, self.screen_height))
        dim_surface.set_alpha(150)
        dim_surface.fill(COLOR_BLACK)
        self.screen.blit(dim_surface, (0, 0))

        # Draw the text
        text_surf = ui_font.render(message, True, color)
        text_rect = text_surf.get_rect(center=(self.screen_width / 2, (self.rows * CELL_SIZE) / 2 - 40))
        self.screen.blit(text_surf, text_rect)
        
        text_surf_2 = ui_font.render("Press 'R' to restart", True, COLOR_WHITE)
        text_rect_2 = text_surf_2.get_rect(center=(self.screen_width / 2, (self.rows * CELL_SIZE) / 2 + 10))
        self.screen.blit(text_surf_2, text_rect_2)

    def main_game_loop(self):
        """This is the main loop for a single game session."""
        # --- BOARD IS NOT CREATED YET ---
        self.board = [] # Start with an empty board
        self.game_over = False
        self.won = False
        self.flags_placed = 0
        self.first_click = True # Reset for each new game
        self.start_time = None # Reset timer for each new game
        
        running = True
        while running:
            # --- 1. Event Handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_r and self.game_over:
                        # Reset the game by exiting this loop
                        running = False
                        continue # Skip to next loop iteration

                if self.game_over:
                    continue # Stop processing game input if game is over

                # --- Mouse Clicks ---
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    
                    # Check if click is within the grid
                    if mouse_y >= self.rows * CELL_SIZE:
                        continue # Click was in the UI area, ignore

                    col = mouse_x // CELL_SIZE
                    row = mouse_y // CELL_SIZE
                    
                    # Check for valid cell (in case of weird clicks)
                    if 0 <= row < self.rows and 0 <= col < self.cols:
                        
                        # --- Handle First Click ---
                        if self.first_click:
                            # 1. Create the board *now*
                            self.board = self.create_board(row, col)
                            # 2. Start the timer
                            self.start_time = pygame.time.get_ticks()
                            # 3. Mark first click as done
                            self.first_click = False
                        
                        cell = self.board[row][col]

                        # --- Left Click ---
                        if event.button == 1:
                            if not cell.is_flagged:
                                if not self.reveal_cell(row, col):
                                    # Hit a mine!
                                    self.game_over = True
                                    self.won = False
                                    # Reveal all other mines
                                    for r in range(self.rows):
                                        for c in range(self.cols):
                                            if self.board[r][c].is_mine:
                                                self.board[r][c].is_revealed = True
                        
                        # --- Right Click ---
                        elif event.button == 3:
                            if not cell.is_revealed:
                                if cell.is_flagged:
                                    cell.is_flagged = False
                                    self.flags_placed -= 1
                                else:
                                    self.flags_placed += 1
                                    cell.is_flagged = True
                        
                        # --- Middle Click (Chording) ---
                        elif event.button == 2:
                            if cell.is_revealed and cell.adjacent_mines > 0:
                                # Count flagged neighbors
                                flagged_neighbors = 0
                                for dr in [-1, 0, 1]:
                                    for dc in [-1, 0, 1]:
                                        if dr == 0 and dc == 0:
                                            continue
                                        
                                        nr, nc = row + dr, col + dc
                                        
                                        # Check boundaries
                                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                                            if self.board[nr][nc].is_flagged:
                                                flagged_neighbors += 1
                                
                                # If we've flagged exactly the right number of neighbors
                                if flagged_neighbors == cell.adjacent_mines:
                                    # Reveal all unflagged, unrevealed neighbors
                                    for dr in [-1, 0, 1]:
                                        for dc in [-1, 0, 1]:
                                            if dr == 0 and dc == 0:
                                                continue
                                            
                                            nr, nc = row + dr, col + dc
                                            
                                            # Check boundaries
                                            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                                                neighbor = self.board[nr][nc]
                                                # Reveal if not flagged and not already revealed
                                                if not neighbor.is_flagged and not neighbor.is_revealed:
                                                    if not self.reveal_cell(nr, nc):
                                                        # Hit a mine! Game over
                                                        self.game_over = True
                                                        self.won = False
                                                        # Reveal all other mines
                                                        for r in range(self.rows):
                                                            for c in range(self.cols):
                                                                if self.board[r][c].is_mine:
                                                                    self.board[r][c].is_revealed = True

            # --- 2. Update (Check Win) ---
            if not self.game_over:
                if self.check_win_condition():
                    self.game_over = True
                    self.won = True

            # --- 3. Draw ---
            self.screen.fill(COLOR_REVEALED) # Background
            self.draw_board()
            
            # Draw UI bar at the bottom
            ui_bar_rect = pygame.Rect(0, self.rows * CELL_SIZE, self.screen_width, 50)
            pygame.draw.rect(self.screen, COLOR_BLACK, ui_bar_rect)
            
            # Draw flag count
            flag_text = ui_font.render(f"Flags: {self.flags_placed} / {self.mines}", True, COLOR_FLAG)
            flag_rect = flag_text.get_rect(midleft=(20, ui_bar_rect.centery))
            self.screen.blit(flag_text, flag_rect)
            
            # Draw timer
            if self.start_time is not None:
                elapsed_seconds = (pygame.time.get_ticks() - self.start_time) // 1000
                timer_text = ui_font.render(f"Time: {elapsed_seconds}s", True, COLOR_WHITE)
                timer_rect = timer_text.get_rect(center=(self.screen_width // 2, ui_bar_rect.centery))
                self.screen.blit(timer_text, timer_rect)
            
            # If it's the first click, show instruction
            if self.first_click:
                instruction_text = main_font.render("Click anywhere to start!", True, COLOR_WHITE)
                instruction_rect = instruction_text.get_rect(midright=(self.screen_width - 20, ui_bar_rect.centery))
                self.screen.blit(instruction_text, instruction_rect)

            if self.game_over:
                if self.won:
                    self.draw_ui("You Win!", (0, 255, 0)) # Green
                else:
                    self.draw_ui("You Hit a Mine!", COLOR_MINE)

            # --- 4. Flip Display ---
            pygame.display.flip()

            # --- 5. Cap Framerate ---
            clock.tick(FPS)
            
    def run(self):
        """The main entry point that controls the game flow."""
        while True:
            # 1. Show start screen and get settings
            self.start_screen()
            # 2. Run the main game loop
            self.main_game_loop()
            # 3. When main_game_loop ends (due to 'R' press),
            #    the loop repeats, showing the start screen again.

# --- Run the Game ---
if __name__ == "__main__":
    game = Game()
    game.run()


