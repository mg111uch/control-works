"""Main menu screen with Fog of War toggle"""
import pygame


class MainMenu:
    """Main menu screen"""
    
    def __init__(self, screen, config):
        self.screen = screen
        self.config = config
        self.running = True
        self.result = None
        
        # Fonts
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 42)
        self.font_small = pygame.font.Font(None, 32)
        
        # Config
        self.fow_enabled = config.get('fog_of_war', {}).get('enabled', True)
    
    def run(self):
        """Run the main menu"""
        clock = pygame.time.Clock()
        
        while self.running:
            self.handle_events()
            self.render()
            pygame.display.flip()
            clock.tick(30)
        
        return self.result
    
    def handle_events(self):
        """Handle menu events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.result = 'quit'
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    self.result = 'quit'
                
                elif event.key == pygame.K_RETURN:
                    # Start game
                    self.running = False
                    self.result = 'start'
                
                elif event.key == pygame.K_f:
                    # Toggle Fog of War
                    self.fow_enabled = not self.fow_enabled
                    self.config['fog_of_war']['enabled'] = self.fow_enabled
                    print(f"Fog of War: {'ON' if self.fow_enabled else 'OFF'}")
    
    def render(self):
        """Render the menu"""
        self.screen.fill((20, 20, 30))
        
        # Title
        title = self.font_large.render("DOTA2 GYM", True, (255, 255, 100))
        title_rect = title.get_rect(center=(640, 120))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.font_medium.render("Shadow Fiend 1v1", True, (200, 200, 200))
        subtitle_rect = subtitle.get_rect(center=(640, 200))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Instructions
        y_offset = 350
        instructions = [
            "PRESS ENTER - Start Local Game",
            "",
            "F - Toggle Fog of War",
            f"Fog of War: {'ON' if self.fow_enabled else 'OFF'}",
            "",
            "ESC - Exit"
        ]
        
        for i, text in enumerate(instructions):
            if text:
                color = (100, 255, 100) if "Fog of War:" in text else (180, 180, 180)
                surface = self.font_small.render(text, True, color)
                rect = surface.get_rect(center=(640, y_offset + i * 40))
                self.screen.blit(surface, rect)
        
        # Footer
        footer = self.font_small.render("Entity Component System | NumPy Physics | YAML Config", True, (100, 100, 100))
        footer_rect = footer.get_rect(center=(640, 650))
        self.screen.blit(footer, footer_rect)