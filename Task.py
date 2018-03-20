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
        global map
        if event.type == pygame.MOUSEMOTION:
            self.collided = self.Rect.collidepoint(event.pos)
        if self.done:
            self.done = False
            self.request = self.text
        if event.type == pygame.KEYDOWN and self.active:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.active = False
                self.done = True
                map = Map(self.text)
            elif event.key == pygame.K_BACKSPACE and self.active:
                if len(self.text) > 0:
                    self.text = self.text[:-1]
            elif self.active:
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
        self.index = 0
        self.liste = ["map", "sat", "skl"]
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
                self.index += 1
                self.text = self.liste[self.index % 3]
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.pressed = False


class Map:
    def __init__(self, address):
        self.map_file = None
        self.address = address
        if address[0].isalpha():
            self.coords = self.geo_coords()
        else:
            self.coords = self.address
        self.draw()

    def geo_coords(self):
        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
        geocoder_params = {
            "geocode" : self.address,
            "format" : "json"
        }
        try:
            response = requests.get(geocoder_api_server, params = geocoder_params)
            if response:
                json_response = response.json()
                self.toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                toponym_coords = self.toponym["Point"]["pos"]
                return toponym_coords
        except:
            print("Что то пошло не так")
        return None

    def get_bounds(self, toponym):
        bounds = toponym["boundedBy"]["Envelope"]["lowerCorner"].split(), toponym["boundedBy"]["Envelope"][
            "upperCorner"].split()
        koef = 3  # Подобран опытным путем
        delta = str((float(bounds[1][0]) - float(bounds[0][0])) / koef)
        delta1 = str((float(bounds[1][1]) - float(bounds[0][1])) / koef)
        return delta, delta1

    def draw(self):
        # toponym_to_find = self.address
        req = "http://static-maps.yandex.ru/1.x/"
        req_params = {
            "ll" : ','.join(self.coords.split()),
            "spn": ",".join(self.get_bounds(self.toponym)),
            "l" : "map",
            "size" : "400,400"
        }

        try:
            response = requests.get(req, params = req_params)
            if response:
                self.map_file = "map.png"
                try:
                    with open(self.map_file, "wb") as file:
                        file.write(response.content)
                except IOError as ex:
                    print("Ошибка записи временного файла:", ex)
                    sys.exit(2)

                # Инициализируем pygame
                pygame.init()
                # Рисуем картинку, загружаемую из только что созданного файла.
                screen.blit(pygame.image.load(self.map_file), (150, 200))
                # Переключаем экран и ждем закрытия окна.
                pygame.display.flip()
        except:
            pass


def terminate():
    pygame.quit()
    sys.exit()


def start_screen():
    BackGround = Background()
    gui = GUI()
    box = TextBox((700, 600, 170, 50), "Enter your request here")
    gui.add_element(LabelMenu((450, 30, 300, 70), "Map Reader X"))
    gui.add_element(LabelMenu((1000, 210, 170, 50), "Scale:"))
    gui.add_element(TextBox((1000, 260, 170, 50), "default"))
    gui.add_element(LabelMenu((950, 310, 170, 50), "Type of map:"))
    gui.add_element(ButtonMenu((1000, 360, 170, 50), "map", "x"))
    gui.add_element(box)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN:
                if pygame.key == pygame.K_ESCAPE:
                    Map(box.text)
            if gui.get_event(event) == "q":
                terminate()

        screen.blit(BackGround.image, BackGround.rect)
        try:
            screen.blit(pygame.image.load(map.map_file), (150, 200))
        except:
            pass

        gui.render(screen)
        gui.update()
        pygame.display.flip()



start_screen()