import pygame
import json
from PIL import Image

class TachieDisplay:
    def __init__(self):
        pygame.init()

        # Load settings
        self.settings = self.load_settings("./config.json")
        self.window_width = self.settings.get("window_width", 500)
        self.window_height = self.settings.get("window_height", 700)
        self.dialog_x = self.settings.get("dialog_x", self.window_width * 0.1)
        self.dialog_y = self.settings.get("dialog_y", self.window_height * 0.5)
        self.dialog_width = self.settings.get("dialog_width", self.window_width * 0.8)
        self.dialog_height = self.settings.get("dialog_height", self.window_height * 0.2)
        self.dialog_opacity = self.settings.get("dialog_opacity", 0.8)

        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.NOFRAME)
        pygame.display.set_caption("Tachie Display")

        # Load character image
        self.image_path = self.settings.get("tachie_path", "./tachie/Murasame/") + "正常.png"
        self.character_image = Image.open(self.image_path).convert("RGBA")

        # Scaling the image to fit within the window size while preserving transparency
        image_width, image_height = self.character_image.size
        scale_width = self.window_width / image_width
        scale_height = self.window_height / image_height
        self.scale = min(scale_width, scale_height)

        self.character_image = self.character_image.resize(
            (int(image_width * self.scale), int(image_height * self.scale))
        )
        self.character_surface = pygame.image.fromstring(
            self.character_image.tobytes(), self.character_image.size, self.character_image.mode
        )

        # Positioning and UI elements
        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False

        self.font = pygame.font.SysFont('Arial', 14)
        self.dialog_surface = pygame.Surface((self.dialog_width, self.dialog_height), pygame.SRCALPHA)
        self.dialog_surface.fill((255, 255, 255, int(self.dialog_opacity * 255)))
        self.dialog_rect = pygame.Rect(self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height)

        self.dialog_text = ""
        self.dialog_text_surface = self.font.render(self.dialog_text, True, (0, 0, 0))
        self.dialog_text_rect = self.dialog_text_surface.get_rect(topleft=(self.dialog_x + 10, self.dialog_y + 35))

        self.close_button_rect = pygame.Rect(self.window_width - (self.window_width - self.dialog_width) // 2 - 30, 0, 30, 30)

        self.running = True

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

    def display_text(self, content):
        self.dialog_text = content
        self.dialog_text_surface = self.font.render(self.dialog_text, True, (0, 0, 0))
        self.dialog_text_rect = self.dialog_text_surface.get_rect(topleft=(self.dialog_x + 10, self.dialog_y + 35))

    def start_drag(self, event):
        self.offset_x = event.pos[0]
        self.offset_y = event.pos[1]

    def drag_window(self, event):
        if self.dragging:
            mouse_x, mouse_y = event.pos
            x = mouse_x - self.offset_x
            y = mouse_y - self.offset_y
            self.dialog_rect.topleft = (x, y)

    def run(self):
        while self.running:
            self.screen.fill((0, 0, 0))

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.dialog_rect.collidepoint(event.pos):
                            self.start_drag(event)
                            self.dragging = True
                        elif self.close_button_rect.collidepoint(event.pos):
                            self.running = False
                elif event.type == pygame.MOUSEMOTION:
                    self.drag_window(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragging = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.send_text()

            # Draw character image
            char_x = (self.window_width - self.character_surface.get_width()) // 2
            char_y = (self.window_height - self.character_surface.get_height()) // 2
            self.screen.blit(self.character_surface, (char_x, char_y))

            # Draw dialog box
            self.screen.blit(self.dialog_surface, self.dialog_rect.topleft)
            self.screen.blit(self.dialog_text_surface, self.dialog_text_rect.topleft)

            # Draw close button
            pygame.draw.rect(self.screen, (255, 0, 0), self.close_button_rect)
            close_text = self.font.render("×", True, (255, 255, 255))
            self.screen.blit(close_text, self.close_button_rect.topleft)

            pygame.display.flip()

    def send_text(self):
        print(f"发送的文本: {self.dialog_text}")
        self.dialog_text = ""
        self.dialog_text_surface = self.font.render(self.dialog_text, True, (0, 0, 0))
        self.dialog_text_rect = self.dialog_text_surface.get_rect(topleft=(self.dialog_x + 10, self.dialog_y + 35))


if __name__ == "__main__":
    app = TachieDisplay()
    app.run()
