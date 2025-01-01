import pygame
import json

class TachieDisplay:
    def __init__(self):
        pygame.init()

        # Load settings from config
        self.settings = self.load_settings("./config.json")
        self.window_width = self.settings.get("window_width", 500)
        self.window_height = self.settings.get("window_height", 700)
        self.dialog_x = self.settings.get("dialog_x", self.window_width * 0.1)
        self.dialog_y = self.settings.get("dialog_y", self.window_height * 0.5)
        self.dialog_width = self.settings.get("dialog_width", self.window_width * 0.8)
        self.dialog_height = self.settings.get("dialog_height", self.window_height * 0.2)
        self.dialog_opacity = self.settings.get("dialog_opacity", 0.8)

        # Create a Pygame window
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.SRCALPHA)
        pygame.display.set_caption("Tachie Display")

        # Load character image with transparency support
        self.image_path = self.settings.get("tachie_path", "./tachie/Murasame/") + "正常.png"
        self.character_image = pygame.image.load(self.image_path).convert_alpha()

        # Scale image to fit within window size
        scale_width = self.window_width / self.character_image.get_width()
        scale_height = self.window_height / self.character_image.get_height()
        self.scale = min(scale_width, scale_height)

        self.character_image = pygame.transform.scale(self.character_image, (
            int(self.character_image.get_width() * self.scale),
            int(self.character_image.get_height() * self.scale)
        ))

        self.character_rect = self.character_image.get_rect(center=(self.window_width // 2, self.window_height // 2))

        # Dialog box
        self.dialog_font = pygame.font.SysFont('Arial', 14)
        self.dialog_text = ""
        self.dialog_rect = pygame.Rect(self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height)

        # Start the main loop
        self.running = True
        self.handle_events()

    def handle_events(self):
        while self.running:
            self.screen.fill((0, 0, 0))  # Fill background with transparent black

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:  # Send text when pressing Enter
                        self.send_text()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click to start dragging
                        self.start_drag(event)

                # Update window position on mouse drag
                elif event.type == pygame.MOUSEMOTION and self.is_dragging:
                    self.drag_window(event)

            # Draw character image
            self.screen.blit(self.character_image, self.character_rect)

            # Draw dialog box
            self.draw_dialog()

            pygame.display.update()

        pygame.quit()

    def send_text(self):
        # Placeholder for sending and displaying text
        print(f"发送的文本: {self.dialog_text}")
        self.dialog_text = ""  # Clear text after sending

    def draw_dialog(self):
        # Draw dialog box with text
        pygame.draw.rect(self.screen, (255, 255, 255), self.dialog_rect)  # White dialog box
        text_surface = self.dialog_font.render(self.dialog_text, True, (0, 0, 0))  # Black text
        self.screen.blit(text_surface, (self.dialog_rect.x + 10, self.dialog_rect.y + 10))

    def load_settings(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"未找到设置文件: {file_path}")
            return {}
        except json.JSONDecodeError:
            print(f"设置文件格式错误: {file_path}")
            return {}

    def start_drag(self, event):
        self.is_dragging = True
        self.offset_x = event.pos[0] - self.dialog_rect.x
        self.offset_y = event.pos[1] - self.dialog_rect.y

    def drag_window(self, event):
        self.dialog_rect.x = event.pos[0] - self.offset_x
        self.dialog_rect.y = event.pos[1] - self.offset_y

if __name__ == "__main__":
    app = TachieDisplay()
