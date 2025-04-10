import pyglet
from pyglet.math import *
from math import *

GREEN = [0, 185, 0]
GREY = [128, 128, 128]

def neighbours(x: int, y: int) -> list:
    return [
        (x-1, y-1),
        (x-1, y),
        (x-1, y+1),
        (x, y-1),
        (x, y+1),
        (x+1, y-1),
        (x+1, y),
        (x+1, y+1)
    ]

class Buttons:
    def __init__(self):
        self.pressed = set()
        self.just_pressed = set()
        self.released = set()

    def is_pressed(self, key: int) -> bool:
        return key in self.pressed

    def is_just_pressed(self, key: int) -> bool:
        return key in self.just_pressed

    def is_released(self, key: int) -> bool:
        return key in self.released

    def clear(self):
        self.just_pressed.clear()
        self.released.clear()

class Camera:
    def __init__(self):
        self.position = Vec2() # x, y pos
        self.speed = 150
        self.z = 1

    def update(self, delta):
        global buttons

        # Wasd-movement
        if buttons.is_pressed(119):
            self.position -= Vec3(0, self.speed * delta)
        if buttons.is_pressed(97):
            self.position += Vec3(self.speed * delta, 0)
        if buttons.is_pressed(115):
            self.position += Vec3(0, self.speed * delta)
        if buttons.is_pressed(100):
            self.position -= Vec3(self.speed * delta, 0)

class Grid:
    def __init__(self):
        self.cell = 25 # cell size in px
        self.field = set() # points filed
        self.counts = dict() # point - count

        # render buffers
        self.lines = [None]*1000
        self.cells_data = [None]*500

        self.to_set = list()
        self.to_reset = list()

    # apply and clear buffers 
    def apply_buffers(self):
        for x, y in self.to_reset:
            self.reset(x, y)

        for x, y in self.to_set:
            self.set(x, y)

        self.to_set = list()
        self.to_reset = list()

    def increase(self, x: int, y: int):
        c = self.counts.get((x, y), 0)

        self.counts[(x, y)] = c + 1
    
    def decrease(self, x: int, y: int):
        c = self.counts.get((x, y), 0) - 1

        if c != 0:
            self.counts[(x, y)] = c
        else:
            self.counts.pop((x, y), 0)

    def set(self, x: int, y: int):
        for px, py in neighbours(x, y):
            self.increase(px, py)
        
        self.field.add((x, y))

    def reset(self, x: int, y: int):
        for px, py in neighbours(x, y):
            self.decrease(px, py)
        
        self.field.remove((x, y))

    def draw(self, width: int, height: int, camera: Camera):
        batch = pyglet.graphics.Batch()
        step = self.cell/camera.z
        px, py = camera.position.x, camera.position.y
        
        # Draw cells
        w = int(width // step)
        h = int(height // step)
        x0, y0 = int(px % step), int(py % step)
        
        c = 0
        cx, cy = int(px // step), int(py // step)
        for y in range(0, h+1):
            for x in range(0, w+1):
                if (x-cx, y-cy) in self.field:
                    self.cells_data[c] = pyglet.shapes.Rectangle(
                        x*step + x0, y*step + y0, step, step,
                        color=GREEN, batch=batch
                    )

                    c += 1

        # Draw lines
        x = x0
        i = 0
        while x <= x0 + width:
            self.lines[i] = pyglet.shapes.Line(
                x, 0,
                x, height,
                color=GREY,
                batch=batch
            )

            i += 1
            x += step

        y = y0
        while y <= y0 + width:
            self.lines[i] = pyglet.shapes.Line(
                0, y,
                width, y,
                color=GREY,
                batch=batch
            )

            i += 1
            y += step

        batch.draw()

class CellularAutomate:
    def __init__(self):
        self.grid = Grid()

    # Game of life standart realisation
    def update(self):
        for x, y in self.grid.field:
            c = self.grid.counts.get((x, y), 0)
            if c == 0 or c < 2 or c > 3: 
                self.grid.to_reset.append((x, y))
        
        for x, y in self.grid.counts.keys():
            if self.grid.counts.get((x, y), 0) == 3 and (x, y) not in self.grid.field:
                self.grid.to_set.append((x, y))

        self.grid.apply_buffers()
        

    def draw(self, width: int, height: int, camera: Camera):
        self.grid.draw(width, height, camera)

    def pressed(self, camera: Camera, x: int, y: int):
        step = self.grid.cell/camera.z
        px = int((x - camera.position.x)//step)
        py = int((y - camera.position.y)//step)

        value = (px, py) in self.grid.field

        if value:
            self.grid.reset(px, py)
        else:
            self.grid.set(px, py)
        
        
class Window(pyglet.window.Window):
    def __init__(self):
        super().__init__(caption="Cellular automates")
        pyglet.gl.glClearColor(255, 255, 255, 255)

        self.camera = Camera()
        self.automate = CellularAutomate()
        self.state = False
        # 12 / sec, delta = 1/12
        self.tick = 12
        # X2, X-3, X-4, X-10, X-20
        self.time_scale = 1.0
        self.add_hoocks()
        
        self.info = pyglet.text.Label(
            '',
            0, self.height, 1.0,
            color=(0, 0, 0),
            width=2000,
            font_size=14,
            font_name="Arial",
            multiline=True,
            anchor_x="left",
            anchor_y="top"
        )

    def update_info(self, delta: float):
        try:
            fps = 1//delta
        except: 
            fps = 'N/A'

        pos = list(floor(self.camera.position))

        self.info.y = self.height
        self.info.text = f"FPS: {fps}; \nPosition: {pos}; \nTime: x{self.time_scale}"
    
    def add_hoocks(self):
        pyglet.clock.schedule(self.update_info)
        pyglet.clock.schedule_interval(self.update, 1/(self.tick*self.time_scale))
        pyglet.clock.schedule(self.camera.update)

    def update_world_time_scale(self):
        pyglet.clock.unschedule(self.update)
        pyglet.clock.schedule_interval(self.update, 1/(self.tick*self.time_scale))

    def update(self, delta):
        if self.state:
            self.automate.update()

    def on_key_press(self, symbol, _modifiers):
        global buttons
        
        if not(buttons.is_pressed(symbol)):
            buttons.just_pressed.add(symbol)
        buttons.pressed.add(symbol)

        if symbol == 32:
            self.state = not(self.state)
        if symbol == 61:
            self.time_scale *= 2
            self.time_scale = clamp(self.time_scale, 0.25, 8.0)
            self.update_world_time_scale()
        if symbol == 45:
            self.time_scale /= 2
            self.time_scale = clamp(self.time_scale, 0.25, 8.0)
            self.update_world_time_scale()

    def on_key_release(self, symbol, _modifiers):
        global buttons

        buttons.pressed.remove(symbol)
        buttons.released.add(symbol)

    def on_mouse_scroll(self, x, y, dx, dy):
        if dy > 0:
            self.camera.z /= 2
        else:
            self.camera.z *= 2

        self.camera.z = clamp(self.camera.z, 0.25, 2.0)
        self.update_world_time_scale()

    def on_mouse_press(self, x, y, button, modifiers):
        self.automate.pressed(self.camera, x, y)

    def on_draw(self):
        self.clear()
        self.automate.draw(self.width, self.height, self.camera)

        self.info.draw()

buttons = Buttons()
window = Window()
pyglet.app.run()
