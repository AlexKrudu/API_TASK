import pygame
import sys
import requests

map_image = None
geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
toponym_to_find = None
geocoder_params = {"geocode": toponym_to_find, "format": "json"}
pygame.init()
running = True
size = width, height = 1280, 720
screen = pygame.display.set_mode(size)


class Background(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer
        self.image = pygame.image.load("images/background.jpg")

        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = (0, 0)


class GUI:
    def __init__(self):
        self.elements = []
        self.request = None

    def add_element(self, element):
        self.elements.append(element)

    def render(self, surface):
        for element in self.elements:
            render = getattr(element, "render", None)
            if callable(render):
                element.render(surface)

    def update(self):
        for element in self.elements:
            update = getattr(element, "update", None)
            if callable(update):
                element.update()

    def get_event(self, event):
        for element in self.elements:
            get_event = getattr(element, "get_event", None)
            if callable(get_event):
                r = element.get_event(event)
                if r:
                    return r


class LabelMenu:
    def __init__(self, rect, text):
        self.Rect = pygame.Rect(rect)
        self.text = text
        self.bgcolor = pygame.Color("white")
        self.bgcolor = None
        self.font_color = pygame.Color("black")
        self.font = pygame.font.Font("fonts/Insight_Sans.ttf", self.Rect.height - 4)
        self.rendered_text = None
        self.rendered_rect = None

    def render(self, surface):
        self.rendered_text = self.font.render(self.text, 1, self.font_color, pygame.SRCALPHA)
        self.rendered_rect = self.rendered_text.get_rect(x=self.Rect.x + 2, centery=self.Rect.centery)

        surface.blit(self.rendered_text, self.rendered_rect)


class TextBox(LabelMenu):
    def __init__(self, rect, text=""):
        super().__init__(rect, text)
        self.collided = False
        self.text = text
        self.font_color = pygame.Color("black")
        self.active = False
        self.done = False
        self.blink = False
        self.blink_timer = 0
        self.Rect.width = 600
        self.request = None

    def get_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.collided = self.Rect.collidepoint(event.pos)
        if self.done:
            self.done = False
            self.request = self.text
        if event.type == pygame.KEYDOWN and self.active:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.active = False
                self.done = True
            elif event.key == pygame.K_BACKSPACE:
                if len(self.text) > 0:
                    self.text = self.text[:-1]
            else:
                self.text += event.unicode
                if self.rendered_rect.width > self.Rect.width:
                    self.text = self.text[:-1]
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.Rect.collidepoint(*event.pos)

    def update(self):
        if pygame.time.get_ticks() - self.blink_timer > 200:
            self.blink = not self.blink
            self.blink_timer = pygame.time.get_ticks()

    def render(self, surface):
        super(TextBox, self).render(surface)
        if self.collided and not self.active:
            self.rendered_text = self.font.render(self.text, 1, pygame.Color("white"))
            self.rendered_rect = self.rendered_text.get_rect(x=self.Rect.x, y=self.Rect.y)
            surface.blit(self.rendered_text, self.rendered_rect)
        if self.active and self.blink:
            pygame.draw.line(surface, [255 - self.font_color[c] for c in range(3)],
                             (self.rendered_rect.right + 2, self.rendered_rect.top + 2),
                             (self.rendered_rect.right + 2, self.rendered_rect.bottom - 2), 2)


class ButtonMenu(LabelMenu):
    def __init__(self, rect, text, value):
        super().__init__(rect, text)
        self.bgcolor = pygame.Color("blue")
        self.pressed = False
        self.collided = False
        self.value = value
        self.font_color = {'up': pygame.Color("black"), "collide": pygame.Color("white")}

    def render(self, surface):
        if self.collided:
            self.rendered_text = self.font.render(self.text, 1, self.font_color["collide"])
            self.rendered_rect = self.rendered_text.get_rect(x=self.Rect.x, y=self.Rect.y)
            surface.blit(self.rendered_text, self.rendered_rect)
        else:
            self.rendered_text = self.font.render(self.text, 1, self.font_color["up"])
            self.rendered_rect = self.rendered_text.get_rect(x=self.Rect.x + 2, y=self.Rect.y + 2)
            surface.blit(self.rendered_text, self.rendered_rect)

    def get_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            was_collided = self.collided
            self.collided = self.Rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.pressed = self.Rect.collidepoint(event.pos)
            if self.pressed:
                return self.value
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.pressed = False


class Map:
    def __init__(self, address):
        self.address = address
        if address.split()[0].isalpha():
            self.coords = address.split()
        else:
            self.coords = self.geo_coords()
        self.draw()

    def geo_coords(self):
        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/?geocode="
        geocoder_2 = "&format=json"
        response = None
        try:
            geocoder_request = "".join([geocoder_api_server, self.address, geocoder_2])
            response = requests.get(geocoder_request)
            if response:
                json_response = response.json()
                toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                toponym_coords = toponym["Point"]["pos"]
                return toponym_coords
        except:
            pass
        return None

    def draw():
        # toponym_to_find = self.address
        map_image = None
        req = "http://static-maps.yandex.ru/1.x/?ll="
        req2 = "&spn=0.1,0.1&l=map"

        try:
            map_request = req + self.coords[1] + self.coords[0] + req2
            response = requests.get(map_request)
            if response:
                map_screen(response)
        except:
            pass

        # toponym_to_find = None
        # geocoder_params = {"geocode": toponym_to_find, "format": "json"}


def terminate():
    pygame.quit()
    sys.exit()


def start_screen():
    BackGround = Background()
    gui = GUI()
    box = TextBox((700, 400, 170, 50), "Enter your request here")
    gui.add_element(LabelMenu((450, 30, 300, 70), "Map Reader X"))
    gui.add_element(ButtonMenu((1000, 310, 170, 50), "Settings", "n"))
    gui.add_element(box)

    if box.done:
        draw_map(box.request)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN:
                if pygame.key == pygame.K_ESCAPE:
                    Map(box.text)
            if gui.get_event(event) == "q":
                terminate()

        screen.fill([255, 255, 255])
        screen.blit(BackGround.image, BackGround.rect)

        gui.render(screen)
        gui.update()
        pygame.display.flip()


def map_screen():
    map_file = "map.png"
    try:
        with open(map_file, "wb") as file:
            file.write(response.content)
    except IOError as ex:
        print("Ошибка записи временного файла:", ex)
        sys.exit(2)

    # Инициализируем pygame
    pygame.init()
    screen = pygame.display.set_mode((600, 450))
    # Рисуем картинку, загружаемую из только что созданного файла.
    screen.blit(pygame.image.load(map_file), (0, 0))
    # Переключаем экран и ждем закрытия окна.
    pygame.display.flip()
    while pygame.event.wait().type != pygame.QUIT:
        pass
    pygame.quit()

    # Удаляем за собой файл с изображением.
    os.remove(map_file)


start_screen()