import pygame
import sys
import requests
import os
from gui_classes import Background, GUI, LabelMenu, TextBox, ButtonMenu, Checkbox

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
        self.clicked = False
        self.post_index = index.get_tapped()
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
            "geocode": self.address,
            "format": "json"
        }
        try:
            response = requests.get(geocoder_api_server, params=geocoder_params)
            if response:
                json_response = response.json()
                self.toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                self.full_address = self.toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
                self.change_address()
                toponym_coords = self.toponym["Point"]["pos"]
                return toponym_coords
        except:
            print("Что-то пошло не так")
        return None

    def change_address(self, *toponym):
        self.post_index = index.get_tapped()
        try:
            self.index = self.toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]
        except Exception:
            print("Нету почтового кода")
            self.index = 'индекс не найден'
        self.full_address = self.toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
        try:
            self.full_address = toponym[0]["metaDataProperty"]["GeocoderMetaData"]["text"]
            self.index = toponym[0]["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]
        except Exception:
            print("Значит мы просто не передали параметр, все ок")
        if self.post_index:
            self.full_address += ", " + self.index

    def get_bounds(self, toponym):
        delta = ""
        delta1 = ""
        if not self.clicked:
            bounds = toponym["boundedBy"]["Envelope"]["lowerCorner"].split(), toponym["boundedBy"]["Envelope"][
                    "upperCorner"].split()
            delta = (float(bounds[1][0]) - float(bounds[0][0])) / self.scale
            delta1 = (float(bounds[1][1]) - float(bounds[0][1])) / self.scale
        return str(delta),str(delta1)

    def draw(self):
        # toponym_to_find = self.address
        req = "http://static-maps.yandex.ru/1.x/"
        self.req_params = {
            "ll" : ','.join(self.coords.split()),
            "spn": ",".join(self.get_bounds(self.toponym)),
            "l" : b.get_text(),
            "size" : "400,400",
            "pt": ','.join(self.point.split()+["pm2ntm"])
        }
        if self.reset:
            del(self.req_params["pt"])
        if self.clicked:
            self.req_params["spn"] = ",".join([str(float(i) / self.scale) for i in self.last_spn.split(",")])
        else:
            self.last_spn = self.req_params["spn"]
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
    if map.clicked:
        y = [float(i) for i in map.last_spn.split(",")][num]
    coords = [float(i) for i in map.get_coords().split()]
    coords[num] += float(y)*koef
    map.set_coords([str(i) for i in coords])
    coords = ' '.join(map.get_coords())
    return coords


def get_coords_click(pos, params):
    a, b = pos
    a = int(a) - 350
    b = int(b) - 200
    b = -b + 200
    values = [float(i) for i in params["spn"].split(",")]
    koef_a = a / 200
    koef_b = b / 200
    delta_a = values[0] / 1.9 * koef_a # Делим не на 2 , а на 1.3 из-за искажения реальных координат проекцией Меркатора
    delta_b = values[1] / 1.9 * koef_b
    result = [float(i) for i in params["ll"].split(",")]
    result[0] += delta_a
    result[1] += delta_b
    result = [str(i) for i in result]
    result =  ','.join(result)
    return result




b = ButtonMenu((1000, 360, 170, 50), "map", "x")
reset = ButtonMenu((700, 450, 170, 50), "Reset search request", "y")
index = Checkbox((600, 525, 170, 50), "Include post index in address: ")
address = LabelMenu((50, 150, 300, 50), "Address: ")

def start_screen():
    clicked = False
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
    gui.add_element(index)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if 150 <= event.pos[0] <= 550 and 200 <= event.pos[1] <= 600:
                    clicked = True
                    addressy = get_coords_click(event.pos, map.req_params)
                    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
                    geocoder_params = {
                        "geocode": addressy,
                        "format": "json"
                    }
                    try:
                        response = requests.get(geocoder_api_server, params=geocoder_params)
                        if response:
                            json_response = response.json()
                            toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0][
                                "GeoObject"]
                            map.full_address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
                    except Exception:
                        print("Упс")
                    map.point = " ".join(addressy.split(','))
                    map.draw()
                    address.set_text(map.full_address)
            try:
                if index.get_focus() and address.get_text() != "Address: ":
                    map.change_address()
                    if clicked and address.get_text() != "Address: ":
                        map.change_address(toponym)
                    address.set_text("Address: " + map.get_full_address())
            except NameError:
                pass
            if b.get_pressed() and address.get_text() != "Address: ":
                b.set_index(b.get_index() + 1)
                b.set_text(b.get_list()[b.get_index() % 3])
                map.draw()
            if box.get_done():
                try:
                    map = Map(box.text, scale_box.text)
                    address.set_text("Address: " + map.get_full_address())
                except Exception as err:
                    address.set_text("Вы что-то ввели не так!")
            if event.type == pygame.QUIT:
                terminate()
            if reset.pressed and address.get_text() != "Address: ":
                clicked = False
                try:
                    map.set_reset(True)
                    map.draw()
                except NameError:
                    pass
                address.set_text("Address: ")
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