import pygame
import sys

def test_maximize():
    """Test simple pour vérifier la maximisation de fenêtre."""
    pygame.init()
    
    # Get screen dimensions
    info = pygame.display.Info()
    screen_w, screen_h = info.current_w, info.current_h
    
    print(f"Screen dimensions: {screen_w}x{screen_h}")
    
    # Set window to nearly full screen size (leave space for taskbar)
    window_width = screen_w - 10
    window_height = screen_h - 80  # Leave space for taskbar
    
    print(f"Window dimensions: {window_width}x{window_height}")
    
    # Create the maximized window
    screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
    pygame.display.set_caption("Test Maximisation - Appuyez sur ESC pour quitter")
    
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    BLUE = (100, 100, 200)
    
    font = pygame.font.Font(None, 48)
    
    running = True
    clock = pygame.time.Clock()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Clear screen
        screen.fill(WHITE)
        
        # Draw title
        title_text = font.render("Fenêtre Maximisée", True, BLACK)
        title_rect = title_text.get_rect(center=(window_width // 2, 100))
        screen.blit(title_text, title_rect)
        
        # Draw dimensions info
        dim_text = font.render(f"Taille: {window_width} x {window_height}", True, BLUE)
        dim_rect = dim_text.get_rect(center=(window_width // 2, 200))
        screen.blit(dim_text, dim_rect)
        
        # Draw instruction
        instruction_text = font.render("Appuyez sur ESC pour quitter", True, BLACK)
        instruction_rect = instruction_text.get_rect(center=(window_width // 2, window_height - 100))
        screen.blit(instruction_text, instruction_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    test_maximize()