import pygame
import sys
import requests
import os
from gui_classes import Background, GUI, LabelMenu, TextBox, ButtonMenu

map_image = None
geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
toponym_to_find = None
geocoder_params = {"geocode": toponym_to_find, "format": "json"}
pygame.init()
running = True
size = width, height = 1280, 720
screen = pygame.display.set_mode(size)

class Map:
    def __init__(self, address, scale):
        if scale == "default":
            scale = 3
        self.reset = False
        self.scale = float(scale)
        self.map_file = None
        self.address = address
        self.full_address = ""
        if address[0].isalpha():
            self.coords = self.geo_coords()
        else:
            self.coords = self.address
        self.point = self.coords
        self.draw()

    def get_full_address(self):
        return self.full_address

    def get_scale(self):
        return self.scale

    def set_scale(self, value):
        self.scale = value

    def get_coords(self):
        return self.coords

    def set_coords(self, value):
        self.coords = value

    def get_reset(self):
        return self.reset

    def set_reset(self, value):
        self.reset = value

    def get_toponym(self):
        return self.toponym

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
                self.full_address = self.toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
                toponym_coords = self.toponym["Point"]["pos"]
                return toponym_coords
        except:
            print("Что-то пошло не так")
        return None

    def get_bounds(self, toponym):
        bounds = toponym["boundedBy"]["Envelope"]["lowerCorner"].split(), toponym["boundedBy"]["Envelope"][
            "upperCorner"].split()
        delta = str((float(bounds[1][0]) - float(bounds[0][0])) / self.scale)
        delta1 = str((float(bounds[1][1]) - float(bounds[0][1])) / self.scale)
        return delta, delta1

    def draw(self):
        # toponym_to_find = self.address
        req = "http://static-maps.yandex.ru/1.x/"
        self.req_params = {
            "ll" : ','.join(self.coords.split()),
            "spn": ",".join(self.get_bounds(self.toponym)),
            "l" : b.text,
            "size" : "400,400",
            "pt": ','.join(self.point.split()+["pm2ntm"])
        }
        if self.reset:
            del(self.req_params["pt"])

        try:
            response = requests.get(req, params = self.req_params)
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
                screen.blit(pygame.image.load("map.png"), (150, 200))
                # Переключаем экран и ждем закрытия окна.
                pygame.display.flip()
        except:
            pass


def terminate():
    pygame.quit()
    try:
        os.remove("map.png")
    except:
        print("ДА КАК ВЫ ПОСМЕЛИ ВЫЙТИ, НЕ ВОСПОЛЬЗОВАВШИСЬ ПРОГРАММОЙ!")
    sys.exit()

def change_centr_map(map,num,koef):
    y = map.get_bounds(map.get_toponym())[num]
    coords = [float(i) for i in map.get_coords().split()]
    coords[num] += float(y)*koef
    map.set_coords([str(i) for i in coords])
    coords = ' '.join(map.get_coords())
    return coords



b = ButtonMenu((1000, 360, 170, 50), "map", "x")
reset = ButtonMenu((700, 450, 170, 50), "Reset search request", "y")
address = LabelMenu((50, 150, 300, 50), "Address: ")

def start_screen():
    BackGround = Background()
    gui = GUI()
    box = TextBox((700, 600, 170, 50), "Enter your request here")
    scale_box = TextBox((1000, 260, 170, 50), "default")
    gui.add_element(LabelMenu((450, 30, 300, 70), "Map Reader X"))
    gui.add_element(LabelMenu((1000, 210, 170, 50), "Scale:"))
    gui.add_element(scale_box)
    gui.add_element(LabelMenu((950, 310, 170, 50), "Type of map:"))
    #b = ButtonMenu((1000, 360, 170, 50), "map", "x")
    gui.add_element(b)
    gui.add_element(box)
    gui.add_element(reset)
    gui.add_element(address)
    while True:
        for event in pygame.event.get():
            if b.pressed:
                b.index += 1
                b.text = b.liste[b.index % 3]
                map.draw()
            if box.done:
                try:
                    map = Map(box.text, scale_box.text)
                    address.text = "Address: " + map.get_full_address()
                except Exception as err:
                    address.text = "Вы что-то ввели не так!"
            if event.type == pygame.QUIT:
                terminate()
            if reset.pressed and address.text != "Address: ":
                map.set_reset(True)
                map.draw()
                address.text = "Address: "
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    map.set_coords(change_centr_map(map,1,1))
                    map.draw()
                if event.key == pygame.K_DOWN:
                    map.set_coords(change_centr_map(map,1,-1))
                    map.draw()
                if event.key == pygame.K_LEFT:
                    map.set_coords(change_centr_map(map,0,-1))
                    map.draw()
                if event.key == pygame.K_RIGHT:
                    map.set_coords(change_centr_map(map,0,1))
                    map.draw()
                if event.key == pygame.K_PAGEDOWN:
                    map.set_scale(map.get_scale() / 2)
                    if map.get_scale() < 0.007:
                        map.set_scale(map.get_scale() * 2)
                    map.draw()
                    print(map.scale)
                if event.key == pygame.K_PAGEUP:
                    map.set_scale(map.get_scale() * 2)
                    if map.get_scale() > 430:
                        map.set_scale(map.get_scale() / 2)
                    map.draw()
                    print(map.scale)
                if pygame.key == pygame.K_ESCAPE:
                    Map(box.text)
            if gui.get_event(event) == "q":
                os.remove("map.png")
                terminate()


        screen.blit(BackGround.image, BackGround.rect)
        try:
            screen.blit(pygame.image.load("map.png"), (150, 200))
        except:
            pass

        gui.render(screen)
        gui.update()
        pygame.display.flip()



start_screen()