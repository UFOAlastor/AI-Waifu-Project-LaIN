import pygame
import json
from pygame.locals import *

class TachieDisplay:
    def __init__(self):
        # 初始化 pygame
        pygame.init()

        # 加载配置文件
        self.settings = self.load_settings("./config.json")
        self.window_width = self.settings.get("window_width", 500)
        self.window_height = self.settings.get("window_height", 700)
        self.dialog_x = self.settings.get("dialog_x", self.window_width * 0.1)
        self.dialog_y = self.settings.get("dialog_y", self.window_height * 0.5)
        self.dialog_width = self.settings.get("dialog_width", self.window_width * 0.8)
        self.dialog_height = self.settings.get(
            "dialog_height", self.window_height * 0.2
        )
        self.dialog_opacity = self.settings.get("dialog_opacity", 0.8)

        # 创建窗口
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.NOFRAME)
        pygame.display.set_caption("Tachie Display")

        # 设置窗口透明背景
        self.screen.fill((0, 0, 0))
        self.alpha_surface = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        self.alpha_surface.fill((0, 0, 0, 255))  # 黑色完全透明

        # 设置角色图像
        self.image_path = (
            self.settings.get("tachie_path", "./tachie/Murasame/") + "正常.png"
        )
        self.character_image = pygame.image.load(self.image_path).convert_alpha()

        # 缩放图像
        image_width, image_height = self.character_image.get_size()
        scale_width = self.window_width / image_width
        scale_height = self.window_height / image_height
        self.scale = min(scale_width, scale_height)
        self.character_image = pygame.transform.scale(
            self.character_image,
            (int(image_width * self.scale), int(image_height * self.scale))
        )

        # 初始位置
        self.character_rect = self.character_image.get_rect(center=(self.window_width // 2, self.window_height // 2))

        # 对话框设置
        self.font = pygame.font.SysFont("Arial", 14)
        self.dialog_surface = pygame.Surface((self.dialog_width, self.dialog_height), pygame.SRCALPHA)
        self.dialog_surface.fill((255, 255, 255, 200))  # 半透明白色背景

        self.dialog_text = ""
        self.dialog_rect = pygame.Rect(self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height)

        # 关闭按钮设置
        self.close_button = pygame.Rect(self.window_width - 30, 0, 30, 30)

        self.offset_x = 0
        self.offset_y = 0

        self.running = True
        self.clock = pygame.time.Clock()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self.dialog_rect.collidepoint(event.pos):
                        self.offset_x = event.pos[0] - self.dialog_rect.x
                        self.offset_y = event.pos[1] - self.dialog_rect.y
                if self.close_button.collidepoint(event.pos):
                    self.running = False
            elif event.type == MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:  # Left button held down
                    self.dialog_rect.x = event.pos[0] - self.offset_x
                    self.dialog_rect.y = event.pos[1] - self.offset_y
            elif event.type == KEYDOWN:
                if event.key == K_RETURN:
                    self.send_text()

    def update(self):
        pass

    def render(self):
        self.screen.fill((0, 0, 0))  # 清空屏幕
        self.screen.blit(self.alpha_surface, (0, 0))  # 透明背景
        self.screen.blit(self.character_image, self.character_rect)  # 显示角色图像

        # 显示对话框
        pygame.draw.rect(self.screen, (255, 255, 255), self.dialog_rect)
        self.screen.blit(self.dialog_surface, self.dialog_rect.topleft)

        # 显示文本
        text_surface = self.font.render(self.dialog_text, True, (0, 0, 0))
        self.screen.blit(text_surface, (self.dialog_rect.x + 10, self.dialog_rect.y + 10))

        # 关闭按钮
        pygame.draw.rect(self.screen, (255, 0, 0), self.close_button)
        close_text = self.font.render("×", True, (255, 255, 255))
        self.screen.blit(close_text, self.close_button.topleft)

        pygame.display.flip()  # 更新屏幕显示

    def send_text(self):
        print(f"发送的文本: {self.dialog_text}")
        self.dialog_text = ""  # 清空文本框

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

if __name__ == "__main__":
    app = TachieDisplay()
    app.run()
