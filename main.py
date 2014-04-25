import kivy
kivy.require("1.8.0")
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter
from kivy.properties import ObjectProperty,\
    BooleanProperty, ListProperty, StringProperty, NumericProperty
from kivy.vector import Vector
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.uix.settings import SettingNumeric, SettingItem, SettingSpacer
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.config import Config

from math import pi
from math import atan2
from random import randint
from random import random
from random import choice
from random import shuffle

import level_parser


def only_running():
    """Check if a username exists"""
    def on_decorator(func):
        def on_call(*args):
            try:
                if args[0].app.game.running:
                    return func(*args)
                else:
                    def not_running():
                        return None
                    return not_running()
            except AttributeError:
                return func(*args)
        return on_call
    return on_decorator


class FrogApp(App):
    def __init__(self, **kwargs):
        super(FrogApp, self).__init__(**kwargs)
        # setup all sounds
        self.sounds = {
            "lost": SoundLoader.load("snd/lost.wav"),
            "won": SoundLoader.load("snd/won.wav"),
            "died": SoundLoader.load("snd/died.wav"),
            "eat": SoundLoader.load("snd/eat.wav"),
            "sink": SoundLoader.load("snd/sink.wav"),
            "jump": SoundLoader.load("snd/jump.wav"),
            "background": SoundLoader.load("snd/background.ogg")
        }

    def build(self):
        from kivy.base import EventLoop
        EventLoop.ensure_window()
        self.window = EventLoop.window
        self.window.bind(on_resize=self.on_resize)
        self.game = GameWidget(app=self)
        self.game = level_parser.build_level(
            "levels/level_001.txt", self, self.game)
        # setup scatter scale. I wanted to allow translation and scale,
        # but the user was able to rotate then too and so I left the scale
        # and made it to a setting
        self.game.game_scatter.scale = float(self.config.getfloat(
            "General", "Zoom"))
        # setup background sound
        self.sounds["background"].loop = True
        self.sounds["background"].volume = float(
            self.config.getfloat("General", "Background")) / 100.
        self.sounds["background"].play()
        # set volume for all sounds
        volume = float(self.config.getfloat("General", "Sound")) / 100.
        for sound in self.sounds.values():
            if sound != self.sounds["background"]:
                sound.volume = volume
        # add game to main widget that it gets displayed
        self.main = Widget(app=self, size=self.window.size)
        self.main.add_widget(self.game)
        return self.main

    def restart(self):
        level_parser.build_level(
            "levels/level_001.txt", self, self.game)

    def on_resize(self, instance, width, height):
        pass

    def build_config(self, config):
        config.adddefaultsection("General")
        config.setdefault("General", "Background", "50.0")
        config.setdefault("General", "Sound", "100.0")
        config.setdefault("General", "Zoom", "1.0")
        config.setdefault("General", "First", "True")

        config.add_section("Math")
        config.setdefault("Math", "Min", "-10")
        config.setdefault("Math", "Max", "10")
        config.setdefault("Math", "TypeOfCalculation", "add")
        Config = config

    def build_settings(self, settings):
        settings.register_type("numeric_range", SettingNumericRange)
        settings.register_type("half_open_numeric_range",
                               SettingHalfOpenNumericRange)
        settings.add_json_panel("Frog Settings",
                                self.config, filename="frogs.json")
        self.settings = settings

    def on_config_change(self, config, section, key, value):
        token = (section, key)
        if token == ("General", "Background"):
            self.sounds["background"].volume = float(value) / 100.
        elif token == ("General", "Sound"):
            for sound in self.sounds.values():
                if sound != self.sounds["background"]:
                    sound.volume = float(value) / 100.
        elif token == ("General", "Zoom"):
            self.game.game_scatter.scale = float(value)
        elif token == ("Math", "Min"):
            if config.getint("Math", "Max") < int(value):
                config.set("Math", "Max", int(value) + 10)
                config.write()
        elif token == ("Math", "Max"):
            if config.getint("Math", "Min") > int(value):
                config.set("Math", "Max", str(
                    int(config.getint("Math", "Min")) + 10))
                config.write()


class GameWidget(Widget):

    @only_running()
    def decrement_lives(self):
        self.lives -= 1
        self.live_imgs[self.lives].source = self.live_imgs[
            self.lives].lost_img
        if self.lives <= 0:
            self.running = False
            self.app.game.status.text = "Lost"
            self.app.sounds["lost"].play()
            Clock.schedule_once(lambda dt: self.app.restart(), 5)
        else:
            self.app.sounds["died"].play()

    @only_running()
    def level_won(self):
        self.running = False
        self.app.game.status.text = "Won"
        self.app.sounds["won"].play()
        Clock.schedule_once(lambda dt: self.app.restart(), 5)


class Background(Image):
    pass


class RandomMover(Widget):
    """Moves over the field in a random way"""
    last_rotated = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(RandomMover, self).__init__(**kwargs)
        Clock.schedule_interval(lambda dt: self.move(), 1 / 30.)

    def move(self):
        self.scatter.rotation += self.rot_change
        m = Vector(0, 2 * self.speed).rotate(self.scatter.rotation)
        self.pos[0] -= m.x
        self.pos[1] -= m.y
        # change direction in ca. every 300th frame
        if randint(0, 300) == 10:
            self.rot_change = choice([-1, 1]) * random()
        if self.pos[0] < dp(-70) or\
           self.pos[0] > self.app.game.game_scatter.width + dp(40)\
           or self.pos[1] < dp(-70) or\
           self.pos[1] > self.app.game.game_scatter.height + dp(40):
            if self.last_rotated:
                self.restart()
            else:
                self.scatter.rotation -= 180
                self.last_rotated = True
        else:
            self.last_rotated = False

    def restart(self):
        self.last_rotated = False
        self.center = (randint(dp(40), self.app.game.width - dp(40)),
                       randint(dp(40), self.app.game.height - dp(40)))
        self.scatter.rotation = randint(0, 360)


class Fly(RandomMover):
    def move(self):
        super(Fly, self).move()

    def eat(self, eater):
        self.app.game.energy += 4
        anim = Animation(center_x=eater.center_x,
                         center_y=eater.center_y,
                         duration=.2)
        anim.bind(on_complete=lambda a, b: self.restart())
        anim.start(self)
        self.app.sounds["eat"].play()


class Boat(RandomMover):
    def move(self):
        super(Boat, self).move()
        self.check_collision()

    def check_collision(self):
        for lily in self.app.game.lilys:
            if lily.collide_widget(self):
                if not lily.static:
                    lily.force_sinking()


class WaterLily(Widget):
    free = BooleanProperty(True)
    sinking = BooleanProperty(False)
    appearing = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(WaterLily, self).__init__(**kwargs)
        self.bind(free=self.on_free_changed)
        self.bind(sinking=self.on_sinking_changed)
        # scale down to simulate sinking
        self.sinking_anim = Animation(scale=.001, duration=1)
        self.sinking_anim.bind(
            on_complete=lambda a, b: self.on_sank())
        # scale up to appear again
        self.appear_anim = Animation(scale=1, duration=2)
        self.appear_anim.bind(
            on_complete=lambda a, b: self.on_appeared())

    @only_running()
    def on_free_changed(self, instance, value):
        if not value and not self.static and not self.sinking:
            # wait 4 sec until sinking starts
            Clock.unschedule(self.start_sinking)
            Clock.schedule_once(self.start_sinking, 4)

    def stop_sinking(self):
        self.sinking = False
        self.appearing = True
        Clock.unschedule(self.start_sinking)
        Animation.cancel_all(self.scatter)
        self.appear_anim.start(self.scatter)

    @only_running()
    def start_sinking(self, dt):
        if not self.free and not self.static:
            if not self.sinking and not self.appearing:
                self.sinking = True
                self.sinking_anim.start(self.scatter)

    @only_running()
    def force_sinking(self):
        if not self.sinking:
            Animation.cancel_all(self.scatter)
            self.appearing = False
            self.sinking = True
            self.sinking_anim.start(self.scatter)

    def appear(self, dt):
        self.sinking = False
        for frog in self.app.game.frogs:
            if frog.place == self:
                Clock.schedule_once(lambda dt: frog.revive(),
                                    self.appear_anim.duration)
                break
        self.appearing = True
        self.appear_anim.start(self.scatter)

    def on_sank(self):
        # kill all frogs on the lily
        reappear_after = 3
        for frog in self.app.game.frogs:
            if frog.place == self:
                frog.kill()
                # live lost, don't wait so long
                reappear_after = 1
        # wait under water, then appear again
        if self.auto_reappear or reappear_after == 1:
            Clock.schedule_once(self.appear, reappear_after)

    def on_appeared(self):
        self.appearing = False

    def on_sinking_changed(self, instance, value):
        if value:
            self.app.sounds["sink"].play()


class StoneLily(WaterLily):
    pass


class MoveableWaterLily(WaterLily):
    pass


class SwitchLily(WaterLily):
    def __init__(self, **kwargs):
        super(SwitchLily, self).__init__(**kwargs)
        self.bind(pressed=self.on_pressed)
        self.bind(controlled=self.on_controlled_change)

    def on_pressed(self, instance, value):
        if self.controlled:
            if value:
                self.controlled.appear(None)
            else:
                self.controlled.force_sinking()

    def on_controlled_change(self, instance, value):
        """
        Used to setup the controlled lily, but is not there to
        change while the game is running
        """
        self.controlled.auto_reappear = False
        self.controlled.static = True
        self.controlled.bind(free=self.on_controlled_free_changed)
        if self.pressed:
            self.controlled.appear(None)
        else:
            self.controlled.force_sinking()

    def on_controlled_free_changed(self, instance, value):
        if not self.pressed and value:
            self.controlled.force_sinking()


class JumpLine(Widget):

    @only_running()
    def set(self, point1, point2):
        """Set start and end point of the Line"""
        self.start(point1)
        self.end(point2)

    @only_running()
    def start(self, point):
        """Set the start point"""
        self.x1 = point[0]
        self.y1 = point[1]
        self.cut_to_max()

    @only_running()
    def end(self, point):
        """Set the end point"""
        self.x2 = point[0]
        self.y2 = point[1]
        self.cut_to_max()

    def cut_to_max(self):
        """
        Move the end point that the distance between
        start and end point is < max
        """
        start = Vector((self.x1, self.y1))
        end = Vector((self.x2, self.y2))
        distance = start.distance(end)
        if distance > self.max:
            dir = Vector((
                start.x - end.x, start.y - end.y))
            end = start - dir * dp(120) / distance
            self.x2 = end[0]
            self.y2 = end[1]


class Frog(Widget):
    app = ObjectProperty(None)
    scatter = ObjectProperty(None)
    jumpline = ObjectProperty(None, allownone=True)
    player = BooleanProperty(False)
    touched = BooleanProperty(False)
    anim_running = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(Frog, self).__init__(**kwargs)
        self.die_anim = Animation(scale=.001,
                                  duration=1)
        self.die_anim.bind(
            on_complete=lambda a, b:
            self.set_img(self.sit_img))
        self.jump_duration = .3
        self.revive_duration = .5
        self.stay_dead = 3

    @only_running()
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and self.alive:
            touch.ud["start_pos"] = self.center
            touch.ud["frog"] = self
            if self.jumpline:
                self.app.game.game_scatter.jumplines.remove_widget(
                    self.jumpline)
            jumpline = JumpLine()
            jumpline.set(self.center, self.center)
            touch.ud["jumpline"] = jumpline
            self.jumpline = jumpline
            self.app.game.game_scatter.jumplines.add_widget(jumpline)
            self.rotate_to(touch.pos)
            self.touched = True
            return True
        return super(Frog, self).on_touch_down(touch)

    @only_running()
    def on_touch_move(self, touch):
        if "start_pos" in touch.ud\
           and "frog" in touch.ud\
           and "jumpline" in touch.ud\
           and touch.ud["jumpline"] == self.jumpline\
           and self.jumpline\
           and touch.ud["frog"] == self:
            self.rotate_to(touch.pos)
            # update jump line
            self.jumpline.end(touch.pos)
            self.jumpline.start(self.center)
            return True
        else:
            self.touched = False
        return super(Frog, self).on_touch_move(touch)

    @only_running()
    def on_touch_up(self, touch):
        if "start_pos" in touch.ud\
           and "frog" in touch.ud\
           and "jumpline" in touch.ud\
           and touch.ud["jumpline"] == self.jumpline\
           and self.jumpline\
           and touch.ud["frog"] == self\
           and self.alive:
            self.app.game.game_scatter.jumplines.remove_widget(
                self.jumpline)
            self.jumpline = None
            self.touched = False
            start = Vector(self.center)
            end = Vector(touch.pos)
            distance = start.distance(end)
            if distance > dp(120):
                dir = Vector((
                    start.x - end.x, start.y - end.y))
                end = start - dir * dp(120) / distance
            for fly in self.app.game.flys:
                if fly.collide_point(*end):
                    fly.eat(self)
                    return True
            it = list(self.app.game.lilys[:])
            it.append(self.app.game.start)
            it.append(self.app.game.end)
            for p in self.app.game.lily_provider:
                it.extend(p.lilys)
            # you can only jump - and die - if you have energy
            die = self.app.game.energy
            for lily in it:
                collide = False
                try:
                    collide = lily.scatter.collide_point(*end)
                except AttributeError:
                    collide = lily.collide_point(*end)
                if collide:
                    if type(lily) == MoveableWaterLily:
                        if lily.text != lily.solution:
                            continue
                    die = False
                    if lily.free and self.app.game.energy:
                        self.app.game.energy -= 1
                        self.place.free = True
                        self.place = lily
                        lily.free = False
                        self.rotate_to(lily.center)
                        self.anim_running = True
                        anim = Animation(center_x=lily.center_x,
                                         center_y=lily.center_y,
                                         duration=self.jump_duration)
                        def on_anim_complete(a, b):
                            self.set_img(self.sit_img)
                            self.set_anim_running(False)
                        anim.bind(on_complete=on_anim_complete)
                        anim.start(self)
                        self.app.sounds["jump"].play()
                        Clock.schedule_once(
                            lambda dt: self.set_img(self.jump_img),
                            self.jump_duration / 3)
                        # check if player reached the end
                        if self.player and lily == self.app.game.end:
                            self.app.game.level_won()
                        break
            else:
                if die:
                    self.go_die(end)
        return super(Frog, self).on_touch_down(touch)

    @only_running()
    def go_die(self, point):
        anim = Animation(center_x=point[0],
                         center_y=point[1],
                         duration=self.jump_duration)
        anim.bind(on_complete=lambda anim,
                  widget: self.kill())
        self.anim_running = True
        anim.start(self)
        self.app.sounds["jump"].play()
        Clock.schedule_once(
            lambda dt: self.set_img(self.jump_img),
            self.jump_duration / 3)
        if not self.place.static:
            self.place.stop_sinking()
        Clock.schedule_once(
            lambda dt: self.revive(),
            self.jump_duration +
            self.die_anim.duration +
            self.stay_dead)

    @only_running()
    def kill(self):
        self.alive = False
        self.app.game.decrement_lives()
        self.anim_running = True
        self.die_anim.start(self.scatter)

    @only_running()
    def revive(self):
        scale_anim = Animation(scale=1,
                               duration=self.revive_duration)
        anim = Animation(center_x=self.place.center_x,
                         center_y=self.place.center_y,
                         duration=self.revive_duration)
        anim.bind(on_complete=lambda a, b:
                  self.set_anim_running(False))
        self.alive = True
        self.anim_running = True
        scale_anim.start(self.scatter)
        anim.start(self)
        if not self.place.static:
            self.place.stop_sinking()

    @only_running()
    def rotate_to(self, point):
        """Rotate frog to the given point"""
        dx = point[0] - self.center_x
        dy = point[1] - self.center_y
        angle = atan2(dy, dx)
        angle_changed = -(angle * (180 / pi)) + 90
        self.scatter.rotation = -angle_changed

    def set_img(self, img):
        """Method to set img in lambdas"""
        self.source = img

    def on_pos(self, instance, pos):
        if self.touched and self.jumpline:
            self.jumpline.start(self.center)

    def set_anim_running(self, b):
        """Method to set anim in lambdas"""
        self.anim_running = b


class MathWidget(Widget):
    number_range = ListProperty((-10, 10))
    type = StringProperty("add")
    count = NumericProperty(5)
    distance = NumericProperty(dp(100))
    initialized = False

    def on_pos(self, instance, pos):
        if self.initialized:
            for i in range(len(self.lilys)):
                self.lilys[i].pos = (self.pos[0] + i * self.distance,
                                     self.pos[1])
            return
        self.initialized = True
        a = randint(*self.number_range)
        b = randint(*self.number_range)
        if self.type == "random":
            self.type = choice(["add", "subtract", "multiply", "divide"])
        if self.type == "add":
            if b < 0:
                to_format = "{} + ({})"
            else:
                to_format = "{} + {}"
            self.exercise = to_format.format(a, b)
            c = a + b
            r = list(range(self.number_range[0] + self.number_range[0],
                           self.number_range[1] + self.number_range[1]))
        elif self.type == "subtract":
            if b < 0:
                to_format = "{} - ({})"
            else:
                to_format = "{} - {}"
            self.exercise = to_format.format(a, b)
            c = a - b
            r = list(range(self.number_range[0] - self.number_range[1],
                           self.number_range[1] - self.number_range[0]))
            r.remove(c)
        elif self.type == "multiply":
            if b < 0:
                to_format = "{} * ({})"
            else:
                to_format = "{} * {}"
            self.exercise = to_format.format(a, b)
            c = a * b
            if self.number_range[0] < 0 and self.number_range[1] >= 0:
                r = list(range(self.number_range[0] * self.number_range[1],
                               max(abs(number_range[0]), number_range[1])**2))
            elif self.number_range[0] < 0 and self.number_range[1] < 0:
                r = list(range(self.number_range[1]**2,
                               self.number_range[0]**2))
            elif self.number_range[0] >= 0 and self.number_range[1] >= 0:
                r = list(range(self.number_range[0]**2,
                               self.number_range[1]**2))
            r.remove(c)
        else:
            if b == 0:
                b += 1
            if b < 0:
                to_format = "{} / ({})"
            else:
                to_format = "{} / {}"
            self.exercise = to_format.format(a, b)
            c = a / float(b)
            r = [c]
            add = randint(0, 4)
            for i in range(self.count):
                r.append((a + i + add) / float(b))
        self.lilys = [MoveableWaterLily()]
        self.lilys[0].text = c
        self.lilys[0].solution = c
        for i in range(self.count - 1):
            try:
                n = r[randint(0, len(r))]
                r.remove(n)
                self.lilys.append(
                    MoveableWaterLily(text=n, solution=c))
            except IndexError:
                self.lilys.append(MoveableWaterLily(
                    text=randint(*self.number_range), solution=c))
        shuffle(self.lilys)
        for i in range(len(self.lilys)):
            self.add_widget(self.lilys[i])
            self.lilys[i].pos = (self.pos[0] + i * self.distance,
                                 self.pos[1])
        Clock.schedule_interval(lambda dt: self.move(), 1 / 30)

    def move(self):
        for lily in self.lilys:
            if self.orientation == "horizontal":
                lily.x += self.speed
                if lily.center_x >\
                   self.pos[0] + self.count * self.distance:
                    lily.center_x = self.pos[0]
            else:
                lily.y += self.speed
                if lily.center_y >\
                   self.pos[1] + self.count * self.distance:
                    lily.center_y = self.pos[1]
            for frog in self.app.game.frogs:
                if frog.place == lily:
                    if not frog.anim_running:
                        frog.center = lily.center


class GameScatter(Scatter):
    def on_transform_with_touch(self, touch):
        if self.y > 0 or self.height * self.scale < self.app.window.height:
            self.y = 0
        elif self.top < self.app.window.height:
            self.top = self.app.window.height


class SettingNumericRange(SettingItem):
    '''Implementation of an numeric range on top of a :class:`SettingItem`.
    It is visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivy.uix.popup.Popup` with a
    slider.
    '''

    min = NumericProperty(0)
    max = NumericProperty(100)
    round_to = NumericProperty(2)

    popup = ObjectProperty(None, allownone=True)
    '''(internal) Used to store the current popup when it is shown.

    :attr:`popup` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''
    label = ObjectProperty(None)

    def on_panel(self, instance, value):
        if value is None:
            return
        self.bind(on_release=self._create_popup)

    def on_value_change(self, instance, value):
        self.value = round(float(value), self.round_to)
        self.label.text = str(self.value)

    def _create_popup(self, instance):
        # create the popup
        content = BoxLayout(orientation='vertical', spacing='5dp')
        self.popup = popup = Popup(
            content=content, title=self.title, size_hint=(None, None),
            size=('400dp', '400dp'))
        popup.height = dp(200)

        # add all the options
        slider = Slider(min=self.min, max=self.max, value=float(self.value))
        slider.bind(value=self.on_value_change)
        content.add_widget(slider)

        # finally, add a cancel button to return on the previous panel
        content.add_widget(SettingSpacer())
        btn = Button(text='Ok', size_hint_y=None, height=dp(40))
        btn.bind(on_release=popup.dismiss)
        content.add_widget(btn)

        # and open the popup !
        popup.open()

    def on_pos(self, instance, value):
        if self.label is not None:
            return
        self.label = Label()
        self.label.text = str(self.value)
        self.content.add_widget(self.label)


class SettingHalfOpenNumericRange(SettingNumeric):
    limit = NumericProperty(0)
    lower = BooleanProperty(False)

    def _validate(self, instance):
        # we know the type just by checking if there is a '.' in the original
        # value
        is_float = '.' in str(self.value)
        self._dismiss()
        try:
            if is_float:
                value = text_type(float(self.textinput.text))
            else:
                value = text_type(int(self.textinput.text))
            if self.lower:
                if value > self.limit:
                    value = self.limit
            else:
                if value < self.limit:
                    value = self.limit
            self.value = value
        except ValueError:
            return


if __name__ == '__main__':
    FrogApp().run()
