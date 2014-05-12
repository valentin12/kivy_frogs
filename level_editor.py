from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.accordion import Accordion
from kivy.properties import ObjectProperty, NumericProperty,\
    OptionProperty, StringProperty
from os.path import isfile

import level_parser

from kivy.lang import Builder

Builder.load_file("editor.kv")


class LevelEditorWidget(Widget):
    def __init__(self, **kwargs):
        super(LevelEditorWidget, self).__init__(**kwargs)
        self.export_popup = Popup(title="Export ...",
                                  content=ExportPopup(),
                                  size_hint=(.3, .3))
        self.load_dialog = LoadDialog()

    def overwrite_level(self):
        if self.last_export:
            self.export_level(self.last_export)

    def export_level(self, path):
        out = "level boats={} flys={} energy={} ".format(
            self.sidebar.level_settings.boats_count.text,
            self.sidebar.level_settings.flys_count.text,
            self.sidebar.level_settings.energy_count.text)
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
            extra_opts = " "
            if type(c) == WaterLilyPH:
                tp = "waterlily"
            elif type(c) == StoneLilyPH:
                tp = "stonelily"
            elif type(c) == SwitchLilyPH:
                if c.options.controlled:
                    tp = "switchlily"
                    extra_opts += "controlled={}".format(
                        c.options.controlled.id)
                else:
                    tp = "stonelily"
            elif type(c) == ExercisePH:
                tp = c.options.tp.lower()
                extra_opts += "count={} orientation={} ".format(
                    c.options.count, c.options.orientation.lower())
            elif type(c) == StartPH:
                tp = "start"
            elif type(c) == EndPH:
                tp = "end"
            else:
                continue
            x = int(round(c.center_x / dp(100), 0))
            y = int(round(c.y / dp(100), 0))
            id = c.id
            s = "{} pos={},{} id={}".format(tp, x, y, id)
            out += s + extra_opts + "\n"
        # Add the player frog
        out += "frog id=player jump_img={} sit_img={}"\
            .format(
                self.level.start.frog.jump_img,
                self.level.start.frog.sit_img) +\
            " player=True place=start\n"
        # Add the other frogs
        for frog in [c for c in self.level.children
                     if type(c) == FrogPH]:
            out += "frog jump_img={} sit_img={} place={}\n".format(
                frog.jump_img, frog.sit_img, frog.place)
        f = open(path, "w")
        f.write(out)
        f.close()

    def load_level(self, path):
        if not path[-13: -7] == "level_"\
           and not path[-15: -9] == "level_":
            self.last_export = path
            self.export_popup.content.overwrite_btn.disabled = False
        else:
            self.last_export = ""
            self.export_popup.content.overwrite_btn.disabled = True
        level = level_parser.parse_level(path)
        self.level.build_standard()
        # load level settings
        distance = dp(100)
        l = level["level"][0]
        if "energy" in l:
            self.sidebar.level_settings.energy_count.text = l["energy"]
        if "flys" in l:
            self.sidebar.level_settings.flys_count.text = l["flys"]
        if "boats" in l:
            self.sidebar.level_settings.boats_count.text = l["boats"]
        # start and end base
        if "start" in level:
            if "pos" in level["start"][0]:
                x, y = level_parser.calculate_point(
                    level["start"][0]["pos"].split(","), distance)
                self.level.start.center_x = x
                self.level.start.y = y
        if "end" in level:
            if "pos" in level["end"][0]:
                x, y = level_parser.calculate_point(
                    level["end"][0]["pos"].split(","), distance)
                self.level.end.center_x = x
                self.level.end.y = y
        if "waterlily" in level:
            for i in range(len(level["waterlily"])):
                lily = level["waterlily"][i]
                l = WaterLilyPH()
                l.moved = True
                if "id" in lily:
                    l.id = lily["id"]
                if "pos" in lily:
                    x, y = level_parser.calculate_point(
                        lily["pos"].split(","), distance)
                    l.center_x = x
                    l.y = y
                self.level.add_widget(l)
        if "stonelily" in level:
            for i in range(len(level["stonelily"])):
                lily = level["stonelily"][i]
                l = StoneLilyPH()
                l.moved = True
                if "id" in lily:
                    l.id = lily["id"]
                if "pos" in lily:
                    x, y = level_parser.calculate_point(
                        lily["pos"].split(","), distance)
                    l.center_x = x
                    l.y = y
                self.level.add_widget(l)
        # the exercises
        exs = []
        if "math" in level:
            exs.append("math")
        if "interval" in level:
            exs.append("interval")
        if "color" in level:
            exs.append("color")
        if "roman" in level:
            exs.append("roman")
        if "form" in level:
            exs.append("form")
        for ex in exs:
            for e in level[ex]:
                # exercise widget
                ew = ExercisePH()
                if "id" in e:
                    ew.id = e["id"]
                if "pos" in e:
                    x, y = level_parser.calculate_point(
                        e["pos"].split(","), distance)
                    ew.center_x = x
                    ew.y = y
                if ew.options:
                    ew.options.tp_input.text = ex.capitalize()
                    if "count" in e:
                        ew.options.count_input.text = e["count"]
                    if "orientation" in e:
                        ew.options.orient_input.text = e[
                            "orientation"].capitalize()
                self.level.add_widget(ew)
        if "switchlily" in level:
            for lily in level["switchlily"]:
                l = SwitchLilyPH()
                if "id" in lily:
                    l.id = lily["id"]
                if "pos" in lily:
                    x, y = level_parser.calculate_point(
                        lily["pos"].split(","), distance)
                    l.center_x = x
                    l.y = y
                if "controlled" in lily:
                    if l.options:
                        for o in self.level.children:
                            if o.id == lily["controlled"]:
                                l.options.select_btn.selected = o
                                break
                self.level.add_widget(l)
        c_dict = {"img/frog_green_sit.png": "green",
                  "img/frog_yellow_sit.png": "yellow",
                  "img/frog_black_blue_sit.png": "darkblue-black",
                  "img/frog_black_light_blue_sit.png": "lightblue-black",
                  "img/frog_black_red_sit.png": "red-black",
                  "img/frog_black_turquoise_sit.png": "turquoise-black",
                  "img/frog_rose_sit.png": "rose",
                  "img/frog_black_yellow_sit.png": "yellow-black",
                  "img/frog_blue_orange_sit.png": "blue-orange"}
        if "frog" in level:
            for frog in level["frog"]:
                if "player" in frog:
                    if frog["player"] == "True":
                        continue
                f = FrogPH()
                if "id" in frog:
                    f.id = frog["id"]
                if "place" in frog:
                    f.place = frog["place"]
                    for o in self.level.children:
                        if o.id == frog["place"]:
                            o.bind(pos=f.on_parent_pos)
                            f.center = o.center
                            break
                    else:
                        continue
                else:
                    continue
                if "sit_img" in frog:
                    try:
                        if f.options:
                            f.options.color_input.text = c_dict[
                                frog["sit_img"]].capitalize()
                    except KeyError:
                        pass
                self.level.add_widget(f)

    def next_level_name(self):
        i = 1
        LOOP = True
        while LOOP:
            if not isfile("levels/custom_level_%03d.txt" % i):
                return "levels/custom_level_%03d.txt" % i
            i += 1


class ExportPopup(Widget):
    pass


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
                            StoneLilyPH,
                            SwitchLilyPH,
                            ExercisePH]:
            if not widget.id:
                while "object_%03d" % self.app.editor.object_count\
                      in [c.id for c in self.children]:
                    self.app.editor.object_count += 1
                widget.id = "object_%03d" %\
                            self.app.editor.object_count
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


class SideBar(Accordion):
    pass


class BackgroundPH(Image):
    pass


class PHScatter(Scatter):
    """Base class for placeholders"""
    current_touch = None
    option_type = None
    options = None

    def __init__(self, **kwargs):
        super(PHScatter, self).__init__(**kwargs)
        if self.option_type is not None:
            self.options = self.option_type(obj=self)

    def on_transform_with_touch(self, touch):
        self.current_touch = touch
        self.app.editor.select.center = self.to_window(*self.center)
        if not self.moved:
            self.parent.add_widget(type(self)(pos=self.parent.pos))
            self.moved = True
            self.on_first_move()
            self.parent.remove_widget(self)
            self.app.editor.level.add_widget(self)
            self.center_x = touch.pos[0]
            self.center_y = touch.pos[1]

    def on_first_move(self):
        """
        Method to overwrite. Executed if the PH is dropped out
        of the toolbar
        """
        pass

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super(PHScatter, self).on_touch_down(touch)
        self.app.editor.select.center = self.to_window(*self.center)
        if not self.app.editor.sidebar.object_content.children\
           == [self.options]:
            self.app.editor.sidebar.object_content.clear_widgets()
            if self.options:
                self.app.editor.sidebar.object_content.add_widget(
                    self.options)
                self.options.size = self.app.editor.sidebar\
                                                   .object_content.size
        return super(PHScatter, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch == self.current_touch:
            self.current_touch = None
            if self.app.editor.delete.collide_point(
                    *self.to_window(*touch.pos)):
                for f in [frog for frog in self.parent.children
                          if type(frog) == FrogPH]:
                    if f.place == self.id:
                        self.app.editor.level.remove_widget(f)
                self.app.editor.level.remove_widget(self)
                return True
            x = int(round(self.center_x / dp(100), 0))
            y = int(round(self.y / dp(100), 0))
            x = x if x > 0 else 1
            y = y if y > 0 else 1
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
            self.app.editor.select.center = self.to_window(
                *self.center)
            return True
        return super(PHScatter, self).on_touch_up(touch)


class WaterLilyPH(PHScatter):
    """Waterlily placeholder for the level editor"""
    pass


class ExerciseOptions(Widget):
    obj = ObjectProperty(None, allownone=True)
    count = NumericProperty(5)
    tp = StringProperty("math")
    orientation = OptionProperty("horizontal", options=[
        "horizontal", "vertical"])

    def __init__(self, **kwargs):
        super(ExerciseOptions, self).__init__(**kwargs)
        self.bind(count=self.on_count_change)
        self.bind(orientation=self.on_orientation_change)

    def on_count_change(self, instance, value):
        self.obj.count = value

    def on_orientation_change(self, instance, value):
        self.obj.orientation = value


class ExercisePH(PHScatter):
    """Placeholder for an exercise"""
    option_type = ExerciseOptions
    count = NumericProperty(5)
    orientation = OptionProperty("horizontal", options=[
        "horizontal", "vertical"])

    def __init__(self, **kwargs):
        super(ExercisePH, self).__init__(**kwargs)
        self.bind(count=self.on_count_change)
        self.bind(orientation=self.on_orient_change)

    def on_first_move(self):
        self.line_points = self.real_points
        self.exercise_text = "Exercise: ..."

    def on_count_change(self, instance, value):
        self.recalculate_real_points()

    def recalculate_real_points(self):
        if self.orientation == "horizontal":
            self.real_points = [
                0 + dp(30),
                self.height / 2,
                self.count * (self.distance) + dp(30),
                self.height / 2]
        else:
            self.real_points = [
                self.width / 2,
                dp(30),
                self.width / 2,
                self.count * (self.distance) + dp(30)]
        self.line_points = self.real_points

    def on_orient_change(self, instance, value):
        self.recalculate_real_points()


class StoneLilyPH(PHScatter):
    """Stonelily placeholder"""
    pass


class SwitchLilyOptions(Widget):
    controlled = ObjectProperty(None, allownone=True)
    last_controlled = ObjectProperty(None, allownone=True)
    obj = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(SwitchLilyOptions, self).__init__(**kwargs)
        self.bind(controlled=self.on_controlled_change)

    def on_controlled_change(self, instance, value):
        if self.last_controlled:
            self.last_controlled.source = self.std_img
        self.last_controlled = value
        if value:
            self.std_img = value.source
            value.source = self.controlled_img


class SwitchLilyPH(PHScatter):
    """Switchlily placeholder"""
    option_type = SwitchLilyOptions


class BasePH(PHScatter):
    def on_transform_with_touch(self, touch):
        self.current_touch = touch
        self.app.editor.select.center = self.to_window(*self.center)

    def on_touch_up(self, touch):
        if touch == self.current_touch:
            self.current_touch = None
            x = int(round(self.center_x / dp(100), 0))
            x = x if x > -1 else 0
            y = int(round(self.y / dp(100), 0))
            y = y if y > -1 else 0
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
            self.app.editor.select.center = self.to_window(
                *self.center)
            return True
        return super(PHScatter, self).on_touch_up(touch)


class StartPH(BasePH):
    pass


class EndPH(BasePH):
    pass


class FrogOptions(Widget):
    obj = ObjectProperty(None)
    color = StringProperty("yellow")
    # the available colors with their imgs
    c_opts = {"green": ["img/frog_green_jump.png",
                        "img/frog_green_sit.png"],
              "yellow": ["img/frog_yellow_jump.png",
                         "img/frog_yellow_sit.png"],
              "darkblue-black": ["img/frog_black_blue_jump.png",
                                 "img/frog_black_blue_sit.png"],
              "lightblue-black": ["img/frog_black_light_blue_jump.png",
                                  "img/frog_black_light_blue_sit.png"],
              "red-black": ["img/frog_black_red_jump.png",
                            "img/frog_black_red_sit.png"],
              "turquoise-black": ["img/frog_black_turquoise_jump.png",
                                  "img/frog_black_turquoise_sit.png"],
              "rose": ["img/frog_rose_jump.png",
                       "img/frog_rose_sit.png"],
              "yellow-black": ["img/frog_black_yellow_jump.png",
                               "img/frog_black_yellow_sit.png"],
              "blue-orange": ["img/frog_blue_orange_jump.png",
                              "img/frog_blue_orange_sit.png"]}

    def __init__(self, **kwargs):
        super(FrogOptions, self).__init__(**kwargs)
        self.bind(color=self.on_color_changed)

    def on_color_changed(self, instance, value):
        self.obj.jump_img = self.c_opts[value.lower()][0]
        self.obj.sit_img = self.c_opts[value.lower()][1]


class FrogPH(PHScatter):
    option_type = FrogOptions

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
            for child in self.parent.children:
                if child.center_x == center_x and\
                   y == child.y and child != self and\
                   type(child) != FrogPH and\
                   type(child) != StartPH:
                    for frog in [c for c in self.parent.children
                                 if type(c) == FrogPH]:
                        if frog.place == child.id and frog != self:
                            break
                    else:
                        child.bind(pos=self.on_parent_pos)
                        self.center = child.center
                        self.app.editor.select.center = self.to_window(
                            *self.center)
                        self.place = child.id
                        break
            else:
                self.parent.remove_widget(self)
            return True
        return super(PHScatter, self).on_touch_up(touch)

    def on_parent_pos(self, instance, value):
        if instance.id == self.place:
            self.center = instance.center


class NumericInput(TextInput):
    def insert_text(self, substring, from_undo=False):
        if substring.isdigit():
            return super(NumericInput, self)\
                .insert_text(substring, from_undo=from_undo)

    def on_focus(self, instance, value):
        if not value:
            if self.text.strip() == "":
                self.insert_text("0")
        super(NumericInput, self).on_focus(instance, value)


class SelectButton(Button):
    binded = False
    selected = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(SelectButton, self).__init__(**kwargs)

    def on_press(self):
        self.selecting = True
        if not self.binded:
            self.app.editor.level.bind(on_touch_down=
                                       self.on_touch_select)

    def on_touch_select(self, instance, touch):
        if self.selecting:
            self.selecting = False
            for o in self.app.editor.level.children:
                if type(o) in [WaterLilyPH,
                               StoneLilyPH] and o.collide_point(
                        *self.app.editor.level.to_window(
                            *self.app.editor.level.to_widget(
                                *touch.pos))
                        ) and o not in self.ignore:
                    self.selected = o
                    return True
            self.selected = None
        return super(SelectButton, self).on_touch_up(touch)


class LoadDialog(Popup):
    def cancel(self):
        self.dismiss()

    def load(self, path, selection):
        self.dismiss()
        self.app.editor.load_level(selection[0])
