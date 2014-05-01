from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.scatterlayout import ScatterLayout
from os.path import isfile

from kivy.lang import Builder

Builder.load_file("editor.kv")


class LevelEditorWidget(Widget):
    def export_level(self, path):
        out = "level boats=0 flys=4 "
        # get level size
        max_x = 0
        max_y = 0
        children = self.level.children
        for c in children:
            x = int(round(c.center_x / dp(100), 0))
            if x > max_x:
                max_x = x
            y = int(round(c.y / dp(100), 0))
            if y > max_y:
                max_y = y
        out += "size={},{}\n".format(max_x + 1, max_y + 1)
        # add the objects
        for c in self.level.children:
            if type(c) == WaterLilyPH:
                tp = "waterlily"
            elif type(c) == StoneLilyPH:
                tp = "stonelily"
            elif type(c) == StartPH:
                tp = "start"
            elif type(c) == EndPH:
                tp = "end"
            else:
                continue
            x = int(round(c.center_x / dp(100), 0))
            y = int(round(c.y / dp(100), 0))
            id = c.id
            s = "{} pos={},{} id={}\n".format(tp, x, y, id)
            out += s
        # Add the player frog
        out += "frog id=player jump_img={} sit_img={} player=True place=start\n"\
            .format(
                self.level.start.frog.jump_img,
                self.level.start.frog.sit_img)
        # Add the other frogs
        for frog in [c for c in self.level.children
                     if type(c) == FrogPH]:
            out += "frog jump_img={} sit_img={} place={}\n".format(
                frog.jump_img, frog.sit_img, frog.place)
        print out
        f = open(path, "w")
        f.write(out)
        f.close()

    def next_level_name(self):
        i = 1
        LOOP = True
        while LOOP:
            if not isfile("levels/custom_level_%d3.txt" % i):
                return "levels/custom_level_%03d.txt" % i
            i += 1


class LevelScatter(Scatter):
    def __init__(self, **kwargs):
        super(LevelScatter, self).__init__(**kwargs)
        self.build_standard()

    def on_transform_with_touch(self, touch):
        if self.x > 0:
            self.x = 0
        if self.y > 0:
            self.y = 0

    def calculate_line_points(self):
        points = []
        for i in range(0, 50):
            if i % 2:
                points.extend([i * dp(100), dp(5000),
                               i * dp(100), 0])
            else:
                points.extend([i * dp(100), 0,
                               i * dp(100), dp(5000)])
        points.extend([0, 0])
        for i in range(0, 50):
            if i % 2:
                points.extend([dp(5000), i * dp(100),
                               0, i * dp(100)])
            else:
                points.extend([0, i * dp(100),
                               dp(5000), i * dp(100)])
        return points

    def add_widget(self, widget, index=0):
        """Override to set object ids"""
        if type(widget) in [WaterLilyPH,
                            StoneLilyPH]:
            widget.id = "object_{}".format(
                self.app.editor.object_count)
            self.app.editor.object_count += 1
        super(LevelScatter, self).add_widget(widget, index)

    def build_standard(self):
        self.clear_widgets()
        self.start = StartPH(id="start")
        self.add_widget(self.start)
        self.end = EndPH(id="end")
        self.add_widget(self.end)


class ToolBar(Widget):
    pass


class BackgroundPH(Image):
    pass


class PHScatter(Scatter):
    """Base class for placeholders"""
    current_touch = None

    def on_transform_with_touch(self, touch):
        self.current_touch = touch
        if not self.moved:
            index = 0
            if type(self) == FrogPH:
                index = 2
            self.parent.add_widget(type(self)(pos=self.parent.pos),
                                   index)
            self.moved = True
            self.parent.remove_widget(self)
            self.app.editor.level.add_widget(self)
            self.center_x = touch.pos[0]
            self.center_y = touch.pos[1]

    def on_touch_up(self, touch):
        if touch == self.current_touch:
            self.current_touch = None
            if self.app.editor.delete.collide_point(*touch.pos):
                self.app.editor.level.remove_widget(self)
                return True
            x = int(round(self.center_x / dp(100), 0))
            y = int(round(self.y / dp(100), 0))
            center_x = dp(100) * x
            y = dp(100) * y
            # Loop until a free place was found
            LOOP = True
            while LOOP:
                for child in self.parent.children:
                    if child.center_x == center_x and\
                       y == child.y and child != self:
                        x += 1
                        center_x = dp(100) * x
                        break
                else:
                    LOOP = False
            self.center_x = center_x
            self.y = y
            return True
        return super(PHScatter, self).on_touch_up(touch)


class WaterLilyPH(PHScatter):
    """Waterlily placeholder for the level editor"""
    pass


class StoneLilyPH(PHScatter):
    """Stonelily placeholder"""
    pass


class BasePH(PHScatter):
    def on_transform_with_touch(self, touch):
        self.current_touch = touch

    def on_touch_up(self, touch):
        if touch == self.current_touch:
            self.current_touch = None
            x = int(round(self.center_x / dp(100), 0))
            y = int(round(self.y / dp(100), 0))
            center = (dp(100) * x, dp(100) * y + dp(50))
            # Loop until a free place was found
            LOOP = True
            while LOOP:
                for child in self.parent.children:
                    if child.center == center and child != self:
                        x += 1
                        center = (dp(100) * x, dp(100) * y)
                        break
                else:
                    LOOP = False
            self.center = center
            return True
        return super(PHScatter, self).on_touch_up(touch)


class StartPH(BasePH):
    pass


class EndPH(BasePH):
    pass


class FrogPH(PHScatter):
    def on_touch_up(self, touch):
        if touch == self.current_touch:
            self.current_touch = None
            if self.app.editor.delete.collide_point(*touch.pos):
                self.app.editor.level.remove_widget(self)
                return True
            x = int(round(self.center_x / dp(100), 0))
            y = int(round(self.y / dp(100), 0))
            center_x = dp(100) * x
            y = dp(100) * y
            # Loop until a free place was found
            LOOP = True
            for child in self.parent.children:
                if child.center_x == center_x and\
                   y == child.y and child != self and\
                   type(child) != FrogPH and\
                   type(child) != StartPH:
                    for frog in [c for c in self.parent.children
                                 if type(c) == FrogPH]:
                        if frog.place == child.id:
                            break
                    else:
                        child.bind(pos=self.on_parent_pos)
                        self.center = child.center
                        self.place = child.id
                        break
            else:
                self.parent.remove_widget(self)
            return True
        return super(PHScatter, self).on_touch_up(touch)

    def on_parent_pos(self, instance, value):
        if instance.id == self.place:
            self.center = instance.center
