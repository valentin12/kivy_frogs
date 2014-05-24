#!/usr/bin/env python
# coding: utf8

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
Clock.max_iteration = 20
from kivy.core.audio import SoundLoader
from kivy.uix.settings import SettingNumeric,\
    SettingItem, SettingSpacer
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Ellipse, Color, Rectangle
from kivy.config import Config

from math import pi
from math import atan2
from random import randint
from random import random
from random import choice
from random import shuffle
from locale import getdefaultlocale
import os.path

import level_parser
from level_editor import LevelEditorWidget


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
            "died": SoundLoader.load("snd/platsch.wav"),
            "eat": SoundLoader.load("snd/eat.wav"),
            "sink": SoundLoader.load("snd/sink.wav"),
            "jump": SoundLoader.load("snd/jump.wav"),
            "background": SoundLoader.load("snd/short_background.wav"),
            "no_energy": SoundLoader.load("snd/wrong.wav"),
            "mechanical_appear": SoundLoader.load(
                "snd/mechanic_appear.wav"),
            # sounds for IntervalWidget
            "c1": SoundLoader.load("snd/c1.wav"),
            "d1": SoundLoader.load("snd/d1.wav"),
            "e1": SoundLoader.load("snd/e1.wav"),
            "f1": SoundLoader.load("snd/f1.wav"),
            "g1": SoundLoader.load("snd/g1.wav"),
            "a1": SoundLoader.load("snd/a1.wav"),
            "h1": SoundLoader.load("snd/h1.wav"),
            "c2": SoundLoader.load("snd/c2.wav")
        }

    def build(self):
        self.icon = "img/icon_blue_orange.png"
        self.title = "Ọpọlọ"
        self.levels = level_parser.find_levels()
        self.custom_levels = level_parser.find_custom_levels()
        self.level = 0
        from kivy.base import EventLoop
        EventLoop.ensure_window()
        self.window = EventLoop.window
        self.game = GameWidget(app=self)
        self.game = level_parser.build_level(
            self.levels[self.level], self, self.game)
        self.current_level = self.levels[self.level]
        self.repeat_level = False
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
        # popup to display help
        self.help_popup = Popup(title="Help",
                                attach_to=self.game)
        self.help_popup.content = HelpPopup()
        self.help_popup.bind(on_touch_down=self.help_popup.dismiss)
        self.help_popup.bind(on_open=self.pause_game)
        self.help_popup.bind(on_dismiss=self.continue_game)
        # popup to display about
        self.about_popup = Popup(title="About",
                                 attach_to=self.game)
        self.about_popup.content = AboutPopup()
        self.about_popup.bind(on_touch_down=self.about_popup.dismiss)
        self.about_popup.bind(on_open=self.pause_game)
        self.about_popup.bind(on_dismiss=self.continue_game)
        # popup to choose a level
        l = LevelChooserPopup()
        i = 1
        for level in self.levels:
            btn = Button(text=str(i), font_size=dp(25))
            btn.bind(on_press=self.load_level)
            l.levels.add_widget(btn)
            i += 1
        i = 1
        for level in self.custom_levels:
            btn = Button(text=str(i), font_size=dp(25))
            btn.bind(on_press=self.load_custom_level)
            btn.path = level
            l.custom_levels.add_widget(btn)
            i += 1
        self.level_popup = Popup(title="Choose a level",
                                 content=l,
                                 size_hint=(.5, .5))
        # level editor
        self.editor = LevelEditorWidget(app=self)
        return self.main

    def pause_game(self, *args):
        self.game.running = False

    def continue_game(self, *args):
        self.game.running = True

    def restart(self):
        level_parser.build_level(
            self.current_level, self, self.game)

    def next_level(self):
        if not self.repeat_level:
            if self.current_level in self.levels:
                try:
                    self.level += 1
                    level_parser.build_level(
                        self.levels[self.level], self, self.game)
                except IndexError:
                    self.level = 0
                    level_parser.build_level(
                        self.levels[self.level], self, self.game)
                self.current_level = self.levels[self.level]
                self.game.level_label.l = str(self.level + 1)
            elif self.current_level in self.custom_levels:
                try:
                    self.current_level = self.custom_levels[
                        self.custom_levels.index(
                            self.current_level) + 1]
                except IndexError:
                    self.current_level = self.custom_levels[0]
                level_parser.build_level(
                    self.current_level, self, self.game)
            else:
                self.restart()
        else:
            self.restart()

    def load_level(self, level):
        if not type(level) == int:
            self.level = int(level.text) - 1
            self.level_popup.dismiss()
        else:
            self.level = level
        level_parser.build_level(
            self.levels[self.level], self, self.game)
        self.game.level_label.l = str(self.level + 1)
        self.current_level = self.levels[self.level]
        self.repeat_level = False

    def load_custom_level(self, path):
        if not type(path) == str:
            path = path.path
            self.level_popup.dismiss()
        self.current_level = path
        if path.endswith("tmp_level.txt"):
            self.game.level_label.l = "Test"
        else:
            self.game.level_label.l = "Custom"
        level_parser.build_level(path, self, self.game)

    def build_config(self, config):
        config.adddefaultsection("General")
        config.setdefault("General", "Background", "50.0")
        config.setdefault("General", "Sound", "50.0")
        config.setdefault("General", "Zoom", "1.0")
        config.setdefault("General", "First", "True")

        config.add_section("Math")
        config.setdefault("Math", "Min", "-10")
        config.setdefault("Math", "Max", "10")
        config.setdefault("Math", "TypeOfCalculation", "add")
        Config = config

    def build_settings(self, settings):
        settings.register_type("numeric_range", SettingNumericRange)
        settings.add_json_panel("Ọpọlọ Settings",
                                self.config, filename="frogs.json")
        self.settings = settings
        with settings.canvas.before:
            Color(.8, .4, .2, 1)
            r = Rectangle(pos=settings.pos, size=settings.size)

            def on_settings_pos(instance, value):
                r.pos = value

            def on_settings_size(instance, value):
                r.size = value

            self.settings.bind(pos=on_settings_pos)
            self.settings.bind(size=on_settings_size)

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

    def open_level_editor(self):
        self.main.remove_widget(self.game)
        self.game.running = False
        self.main.add_widget(self.editor)

    def close_level_editor(self):
        self.main.remove_widget(self.editor)
        self.main.add_widget(self.game)
        self.game.running = True

    def add_custom_level(self, path):
        self.custom_levels.append(path)
        btn = Button(text=str(len(self.custom_levels)),
                     font_size=dp(25))
        btn.bind(on_press=self.load_custom_level)
        btn.path = path
        self.level_popup.content.custom_levels.add_widget(btn)


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
        Clock.schedule_once(lambda dt: self.app.next_level(), 2)


class Background(Image):
    pass


class Base(Image):
    pass


class RandomMover(Widget):
    """Moves over the field in a random way"""
    last_rotated = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(RandomMover, self).__init__(**kwargs)
        Clock.schedule_interval(self.move, 1 / 30.)

    def move(self, dt):
        self.scatter.rotation += self.rot_change
        m = Vector(0, dt * 60 * self.speed).rotate(self.scatter.rotation)
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
        self.center = (0 if int(dp(40)) >=
                       int(self.app.game.width - dp(40)) else
                       randint(int(dp(40)),
                               int(self.app.game.width - dp(40))),
                       0 if int(dp(40)) >=
                       int(self.app.game.height - dp(40)) else
                       randint(int(dp(40)),
                               int(self.app.game.height - dp(40))))
        self.scatter.rotation = randint(0, 360)


class Fly(RandomMover):
    def move(self, dt):
        super(Fly, self).move(dt)

    def eat(self, eater):
        self.app.game.energy += 4
        anim = Animation(center_x=eater.center_x,
                         center_y=eater.center_y,
                         duration=.2)
        anim.bind(on_complete=lambda a, b: self.restart())
        anim.start(self)
        self.app.sounds["eat"].play()

    def reset(self):
        self.speed = 1.5


class Boat(RandomMover):
    def move(self, dt):
        if self.active:
            self.check_collision()
            super(Boat, self).move(dt)

    def check_collision(self):
        for lily in self.app.game.lilys:
            if lily.collide_widget(self):
                if not lily.static:
                    lily.force_sinking()

    def reset(self):
        self.speed = -1.5


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
        # dont't call if sinking was canceled
        if self.scatter.scale > .1:
            return
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

    def reset(self):
        self.source = "img/water_lily_001.png"
        self.auto_reappear = True
        self.static = False
        self.sinking = False
        self.appearing = False
        self.free = True
        self.scatter.scale = 1


class StoneLily(WaterLily):
    def reset(self):
        super(StoneLily, self).reset()
        self.source = "img/water_lily_stone.png"
        self.auto_reappear = False
        self.static = True


class MoveableWaterLily(WaterLily):
    def reset(self):
        super(MoveableWaterLily, self).reset()
        self.auto_reappear = False
        self.static = True
        self.text = ""
        self.value = ""
        self.solution = ""
        self.custom.clear_widgets()


class SwitchLily(WaterLily):
    controlled = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(SwitchLily, self).__init__(**kwargs)
        self.bind(pressed=self.on_pressed)
        self.bind(controlled=self.on_controlled_change)

    def on_pressed(self, instance, value):
        if self.controlled:
            if value:
                self.controlled.appear(None)
                if self.controlled.scatter.scale < .1:
                    self.app.sounds["mechanical_appear"].play()
            else:
                self.controlled.force_sinking()

    def on_controlled_change(self, instance, value):
        """
        Used to setup the controlled lily, but is not there to
        change while the game is running
        """
        if not self.controlled:
            return
        self.controlled.auto_reappear = False
        self.controlled.static = True
        self.controlled.source = self.controlled_img
        self.controlled.bind(free=self.on_controlled_free_changed)
        if self.pressed:
            self.controlled.appear(None)
            if self.controlled.scatter.scale < .1:
                self.app.sounds["mechanical_appear"].play()
        else:
            self.controlled.force_sinking()

    def on_controlled_free_changed(self, instance, value):
        if not self.pressed and value and self.controlled:
            self.controlled.force_sinking()

    def reset(self):
        # don't override super to disable setting the source
        self.static = True
        self.auto_reappear = False
        self.sinking = False
        self.appearing = False
        self.free = True
        self.scatter.scale = 1
        self.pressed = False
        self.not_pressed_img = "img/lily_switch_not_pressed.png"
        self.pressed_img = "img/lily_switch_pressed.png"
        if self.controlled:
            self.controlled_img = "img/water_lily_controlled.png"
            self.controlled = None


class JumpLine(Widget):
    raw_end = (0, 0)

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
        self.raw_end = (self.x2, self.y2)
        self.cut_to_max()

    def cut_to_max(self):
        """
        Move the end point that the distance between
        start and end point is < max
        """
        start = Vector((self.x1, self.y1))
        end = Vector(self.raw_end)
        distance = start.distance(end)
        if abs(distance) > self.max:
            dir = Vector((
                start.x - end.x, start.y - end.y))
            end = start - dir * self.max / distance
            self.x2 = end[0]
            self.y2 = end[1]
        else:
            self.x2 = self.raw_end[0]
            self.y2 = self.raw_end[1]


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
            if distance > dp(125):
                dir = Vector((
                    start.x - end.x, start.y - end.y))
                end = start - dir * dp(125) / distance
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
            if not self.app.game.energy and\
               not self.place.collide_point(*end):
                self.app.sounds["no_energy"].play()
            for lily in it:
                collide = False
                try:
                    collide = lily.scatter.collide_point(*end)
                except AttributeError:
                    collide = lily.collide_point(*end)
                if collide:
                    if type(lily) == MoveableWaterLily:
                        if lily.value != lily.solution:
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
        if self.jumpline:
            self.app.game.game_scatter.jumplines.remove_widget(
                self.jumpline)
            self.jumpline = None
        if self.alive:
            self.app.game.decrement_lives()
        self.alive = False
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
            self.rotate_to((self.jumpline.x2, self.jumpline.y2))

    def set_anim_running(self, b):
        """Method to set anim in lambdas"""
        self.anim_running = b


class ExerciseWidget(Widget):
    count = NumericProperty(5)
    distance = NumericProperty(dp(100))
    initialized = False
    lilys = []

    def move(self, dt):
        for lily in self.lilys:
            if self.orientation == "horizontal":
                lily.x += self.speed * 60 * dt
                if lily.center_x >\
                   self.pos[0] + self.count * self.distance:
                    lily.center_x = self.pos[0]
            else:
                lily.y += self.speed * 60 * dt
                if lily.center_y >\
                   self.pos[1] + self.count * self.distance:
                    lily.center_y = self.pos[1]
            for frog in self.app.game.frogs:
                if frog.place == lily:
                    if not frog.anim_running:
                        frog.center = lily.center

    def on_pos(self, *args):
        self.setup()

    def setup(self):
        pass

    def reset(self):
        pass


class MathWidget(ExerciseWidget):
    number_range = ListProperty((-10, 10))
    type = StringProperty("add")

    def setup(self, force=False):
        if self.initialized and not force:
            for i in range(len(self.lilys)):
                self.lilys[i].pos = (self.pos[0] + i * self.distance,
                                     self.pos[1])
            return
        else:
            for lily in self.lilys:
                self.lily_widget.remove_widget(lily)
            self.lilys = []
        self.initialized = True
        a = randint(int(self.number_range[0]),
                    int(self.number_range[1]))
        b = randint(int(self.number_range[0]),
                    int(self.number_range[1]))
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
            try:
                r.remove(c)
            except ValueError as e:
                print e
                print self.number_range
                print c
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
        self.lilys[0].value = c
        self.lilys[0].solution = c
        for i in range(self.count - 1):
            try:
                n = r[randint(0, len(r))]
                r.remove(n)
                self.lilys.append(
                    MoveableWaterLily(text=n, value=n, solution=c))
            except IndexError:
                n = randint(*self.number_range)
                self.lilys.append(MoveableWaterLily(
                    text=n, value=n, solution=c))
        shuffle(self.lilys)
        for i in range(len(self.lilys)):
            self.lily_widget.add_widget(self.lilys[i])
            if self.orientation == "horizontal":
                self.lilys[i].pos = (self.pos[0] + i * self.distance,
                                     self.pos[1])
            else:
                self.lilys[i].pos = (self.pos[0] + dp(15),
                                     self.pos[1] + i * self.distance)
        Clock.unschedule(self.move)
        Clock.schedule_interval(self.move, 1 / 30)


class IntervalWidget(ExerciseWidget):
    intervals = [["c1", "P1"],
                 ["d1", "M2"],
                 ["e1", "M3"],
                 ["f1", "P4"],
                 ["g1", "P5"],
                 ["a1", "M6"],
                 ["h1", "M7"],
                 ["c2", "P8"]]

    def __init__(self, **kwargs):
        super(IntervalWidget, self).__init__(**kwargs)
        self.label.bind(on_touch_down=self.on_label_touched)

    def on_label_touched(self, instance, touch):
        if self.label.collide_point(*touch.pos):
            self.play_sound()

    def setup(self, force=False):
        if self.initialized and not force:
            for i in range(len(self.lilys)):
                self.lilys[i].pos = (self.pos[0] + i * self.distance,
                                     self.pos[1])
            return
        else:
            for lily in self.lilys:
                self.lily_widget.remove_widget(lily)
            self.lilys = []
        self.initialized = True
        self.solution = choice(self.intervals)
        # other posibilities
        psb = self.intervals[:]
        psb.remove(self.solution)
        self.lilys = [MoveableWaterLily()]
        self.lilys[0].text = self.solution[1]
        self.lilys[0].value = self.solution[1]
        self.lilys[0].solution = self.solution[1]
        for i in range(self.count - 1):
            try:
                n = choice(psb)
                psb.remove(n)
                self.lilys.append(
                    MoveableWaterLily(text=n[1], value=n[1],
                                      solution=self.solution[1]))
            except IndexError:
                n = choice(self.intervals)[1]
                self.lilys.append(MoveableWaterLily(
                    text=n, value=n,
                    solution=self.solution[1]))
        shuffle(self.lilys)
        for i in range(len(self.lilys)):
            self.lily_widget.add_widget(self.lilys[i])
            if self.orientation == "horizontal":
                self.lilys[i].pos = (self.pos[0] + i * self.distance,
                                     self.pos[1])
            else:
                self.lilys[i].pos = (self.pos[0] + dp(15),
                                     self.pos[1] + i * self.distance)
        Clock.unschedule(self.move)
        Clock.schedule_interval(self.move, 1 / 30)

    def play_sound(self):
        self.app.sounds["c1"].play()
        Clock.schedule_once(lambda dt:
                            self.app.sounds[self.solution[0]].play(),
                            self.app.sounds["c1"].length + .5)


class EllipseWidget(Widget):
    pass


class TriangleWidget(Widget):
    pass


class RectangleWidget(Widget):
    pass


class ColorWidget(ExerciseWidget):
    base_colors = [[1, 0, 0], [1, 1, 0], [0, 0, 1]]
    real_colors = {str([1., .5, 0.]): [1, .5, 0],
                   str([.5, 0., .5]): [.5, 0, .5],
                   str([.5, .5, .5]): [0, 1, 0],
                   str([1., 0., 0.]): [1, 0, 0],
                   str([1., 1., 0.]): [1, 1, 0],
                   str([0., 0., 1.]): [0, 0, 1]}

    def __init__(self, **kwargs):
        super(ColorWidget, self).__init__(**kwargs)

    def setup(self, force=False):
        if self.initialized and not force:
            for i in range(len(self.lilys)):
                self.lilys[i].pos = (self.pos[0] + i * self.distance,
                                     self.pos[1])
            return
        else:
            for lily in self.lilys:
                self.lily_widget.remove_widget(lily)
            self.lilys = []
            self.left_of_label.clear_widgets()
            self.right_of_label.clear_widgets()
        self.initialized = True
        choices = self.base_colors[:]
        self.a = choices.pop(randint(0, len(choices) - 1))
        self.b = choice(choices)
        self.solution = [sum(x) / 2. for x in zip(self.a, self.b)]
        self.left_of_label.add_widget(
            EllipseWidget(rgb=self.a,
                          x=self.left_of_label.center_x - dp(10),
                          y=self.right_of_label.pos[1] + dp(5),
                          size=(dp(20), dp(20))))
        self.label.text = " + "
        self.label_width = dp(20)
        self.right_of_label.add_widget(
            EllipseWidget(rgb=self.b,
                          x=self.right_of_label.center_x - dp(10),
                          y=self.right_of_label.pos[1] + dp(5),
                          size=(dp(20), dp(20))))
        # other posibilities
        self.lilys = [MoveableWaterLily()]
        self.lilys[0].solution = self.solution
        self.lilys[0].text = ""
        self.lilys[0].value = self.solution
        for i in range(self.count - 1):
            n = [sum(x) / 2. for x in
                 zip(self.base_colors[
                     randint(0, len(self.base_colors) - 1)],
                     self.base_colors[
                         randint(0, len(self.base_colors) - 1)])]
            self.lilys.append(
                MoveableWaterLily(text="",
                                  value=n,
                                  solution=self.solution))
        for lily in self.lilys:
            lily.custom.add_widget(
                EllipseWidget(rgb=self.real_colors[str(lily.value)],
                              center=lily.custom.center,
                              size=(dp(20), dp(20))))
        shuffle(self.lilys)
        for i in range(len(self.lilys)):
            self.lily_widget.add_widget(self.lilys[i])
            if self.orientation == "horizontal":
                self.lilys[i].pos = (self.pos[0] + i * self.distance,
                                     self.pos[1])
            else:
                self.lilys[i].pos = (self.pos[0] + dp(15),
                                     self.pos[1] + i * self.distance)
        Clock.unschedule(self.move)
        Clock.schedule_interval(self.move, 1 / 30)


class RomanWidget(ExerciseWidget):
    def int_to_roman(self, n):
        ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
        nums = ('M',  'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL',
                'X', 'IX', 'V', 'IV', 'I')
        result = ""
        for i in range(len(ints)):
            count = int(n / ints[i])
            result += nums[i] * count
            n -= ints[i] * count
        return result

    def setup(self, force=False):
        if self.initialized and not force:
            for i in range(len(self.lilys)):
                self.lilys[i].pos = (self.pos[0] + i * self.distance,
                                     self.pos[1])
            return
        else:
            for lily in self.lilys:
                self.lily_widget.remove_widget(lily)
            self.lilys = []
        self.initialized = True
        a = randint(0, 1500)
        n = a
        self.solution = self.int_to_roman(n)
        self.label.text = str(n)
        # other posibilities
        self.lilys = [MoveableWaterLily()]
        self.lilys[0].text = self.solution
        self.lilys[0].value = self.solution
        self.lilys[0].solution = self.solution
        for i in range(self.count - 1):
            n = self.int_to_roman(a + choice([1, -1]) * randint(1, 20))
            self.lilys.append(
                MoveableWaterLily(text=n, value=n,
                                  solution=self.solution))
        shuffle(self.lilys)
        for i in range(len(self.lilys)):
            self.lily_widget.add_widget(self.lilys[i])
            if self.orientation == "horizontal":
                self.lilys[i].pos = (self.pos[0] + i * self.distance,
                                     self.pos[1])
            else:
                self.lilys[i].pos = (self.pos[0] + dp(15),
                                     self.pos[1] + i * self.distance)
        Clock.unschedule(self.move)
        Clock.schedule_interval(self.move, 1 / 30)


class FormWidget(ExerciseWidget):
    forms = ["Circle", "Rectangle", "Triangle", "Square"]
    formulas = {"Circle": ["U=2*r*π",
                           "A=r²*π"],
                "Rectangle": ["A=a*b",
                              "U=2*(a+b)",
                              "D=√(a² + b²)"],
                "Square": ["A=a²",
                           "U=4a",
                           "D=2*√2"],
                "Triangle": ["A=(a*ha)/2"]}

    def __init__(self, **kwargs):
        super(FormWidget, self).__init__(**kwargs)

    def setup(self, force=False):
        if self.initialized and not force:
            for i in range(len(self.lilys)):
                self.lilys[i].pos = (self.pos[0] + i * self.distance,
                                     self.pos[1])
            return
        else:
            for lily in self.lilys:
                self.lily_widget.remove_widget(lily)
            self.lilys = []
            self.left_of_label.clear_widgets()
            self.right_of_label.clear_widgets()
        self.initialized = True
        choices = self.formulas.keys()[:]
        self.solution = choices.pop(randint(0, len(choices) - 1))
        self.formula = choice(self.formulas[self.solution])
        self.label.text = self.formula
        self.label_width = dp(100)
        # other posibilities
        self.lilys = [MoveableWaterLily()]
        self.lilys[0].solution = self.solution
        self.lilys[0].text = ""
        self.lilys[0].value = self.solution
        for i in range(self.count - 1):
            try:
                n = choices.pop(randint(0, len(choices) - 1))
            except ValueError:
                n = choice(self.formulas.keys())
            self.lilys.append(
                MoveableWaterLily(text="",
                                  value=n,
                                  solution=self.solution))
        for lily in self.lilys:
            if lily.value == "Circle":
                lily.custom.add_widget(
                    EllipseWidget(rgb=[1, 0, 0],
                                  center=lily.custom.center,
                                  size=(dp(20), dp(20))))
            elif lily.value == "Rectangle":
                lily.custom.add_widget(
                    RectangleWidget(rgb=[1, 1, 0],
                                    center=lily.custom.center,
                                    size=(dp(20), dp(30))))
            elif lily.value == "Square":
                lily.custom.add_widget(
                    RectangleWidget(rgb=[0, 0, 1],
                                    center=lily.custom.center,
                                    size=(dp(20), dp(20))))
            elif lily.value == "Triangle":
                lily.custom.add_widget(
                    TriangleWidget(rgb=[0, 1, 0],
                                   center=lily.custom.center,
                                   size=(dp(20), dp(20))))
        shuffle(self.lilys)
        for i in range(len(self.lilys)):
            self.lily_widget.add_widget(self.lilys[i])
            if self.orientation == "horizontal":
                self.lilys[i].pos = (self.pos[0] + i * self.distance,
                                     self.pos[1])
            else:
                self.lilys[i].pos = (self.pos[0] + dp(15),
                                     self.pos[1] + i * self.distance)
        Clock.unschedule(self.move)
        Clock.schedule_interval(self.move, 1 / 30)


class ChemistryWidget(ExerciseWidget):
    elements = {"Sauerstoff": "O",
                "Kohlenstoff": "C",
                "Stickstoff": "N",
                "Schwefel": "S",
                "Gold": "Au",
                "Kupfer": "Cu"}

    def __init__(self, **kwargs):
        super(ChemistryWidget, self).__init__(**kwargs)
        self.elements = {}
        l = getdefaultlocale()[0]
        print l
        p = "data/chemistry_symbols_{}.txt".format(l[0])
        try:
            if os.path.isfile(p):
                with open(p) as f:
                    for line in f.read().split("\n"):
                        if not line:
                            continue
                        line = line.strip()
                        key, value = line.split(" ")
                        self.elements[key] = value
        except OSError:
            pass
        if not self.elements:
            with open("data/chemistry_symbols_en.txt") as f:
                for line in f.read().split("\n"):
                    if not line:
                        continue
                    line = line.strip()
                    key, value = line.split(" ")
                    self.elements[key] = value
                        

    def setup(self, force=False):
        if self.initialized and not force:
            for i in range(len(self.lilys)):
                self.lilys[i].pos = (self.pos[0] + i * self.distance,
                                     self.pos[1])
            return
        else:
            for lily in self.lilys:
                self.lily_widget.remove_widget(lily)
            self.lilys = []
        self.initialized = True
        key = choice(self.elements.keys())
        self.exercise = key
        self.solution = self.elements[key]
        # other posibilities
        psb = self.elements.values()[:]
        psb.remove(self.solution)
        self.lilys = [MoveableWaterLily()]
        self.lilys[0].text = self.solution
        self.lilys[0].value = self.solution
        self.lilys[0].solution = self.solution
        for i in range(self.count - 1):
            try:
                n = choice(psb)
                psb.remove(n)
                self.lilys.append(
                    MoveableWaterLily(text=n, value=n,
                                      solution=self.solution))
            except IndexError:
                n = choice(self.elements.calues())
                self.lilys.append(MoveableWaterLily(
                    text=n, value=n,
                    solution=self.solution))
        shuffle(self.lilys)
        for i in range(len(self.lilys)):
            self.lily_widget.add_widget(self.lilys[i])
            if self.orientation == "horizontal":
                self.lilys[i].pos = (self.pos[0] + i * self.distance,
                                     self.pos[1])
            else:
                self.lilys[i].pos = (self.pos[0] + dp(15),
                                     self.pos[1] + i * self.distance)
        Clock.unschedule(self.move)
        Clock.schedule_interval(self.move, 1 / 30)


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


class LevelChooserPopup(Widget):
    pass


class AboutPopup(Widget):
    pass


class HelpPopup(Widget):
    pass


class OverviewWidget(Widget):
    screen = ObjectProperty(None)
    visible = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(OverviewWidget, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, .5)
        self.bind(visible=self.on_visible_changed)
        self.update(0)

    def on_visible_changed(self, instance, value):
        if not value:
            self.screen.canvas.clear()

    def set_visibility(self, b):
        self.visible = b

    def update(self, dt):
        if not self.screen or not self.visible:
            return
        with self.screen.canvas:
            self.screen.canvas.clear()
            # draw start
            Color(.2, .2, .1)
            Ellipse(pos=(
                self.app.game.standard_objects
                ["start"].x / 5.,
                self.app.game.standard_objects
                ["start"].y / 5.),
                size=(
                    self.app.game.standard_objects
                    ["start"].width / 5.,
                    self.app.game.standard_objects
                    ["start"].height / 5.))
            # draw end
            Color(.1, .8, .1)
            Ellipse(pos=(self.app.game.standard_objects
                         ["end"].x / 5.,
                         self.app.game.standard_objects
                         ["end"].y / 5.),
                    size=(self.app.game.standard_objects
                          ["end"].width / 5.,
                          self.app.game.standard_objects
                          ["end"].height / 5.))
            # draw all the other objects
            objs = self.app.game.game_scatter.before_jumpline\
                                             .children[:]
            for ls in self.app.game.lily_provider:
                objs.extend(ls.lilys[:])
            objs.extend(self.app.game.game_scatter.after_jumplines
                        .children[:])
            for o in objs:
                pos = (o.x / 5.,
                       o.y / 5.)
                size = (o.width / 5.,
                        o.height / 5.)
                try:
                    if o.source == "img/water_lily_controlled.png":
                        if o.scatter.scale < .01:
                            continue
                        Color(.81, .8, .8)
                        Ellipse(pos=pos,
                                size=size)
                        continue
                except AttributeError:
                    pass
                if type(o) == WaterLily:
                    Color(.1, .6, .1)
                    Ellipse(pos=pos,
                            size=size)
                elif type(o) == MoveableWaterLily:
                    Color(0, 1, 0)
                    Ellipse(pos=pos,
                            size=size)
                elif type(o) == StoneLily:
                    Color(.6, .6, .6)
                    Ellipse(pos=pos,
                            size=size)
                elif type(o) == SwitchLily:
                    Color(.1, .3, .1)
                    Ellipse(pos=pos,
                            size=size)
                    Color(1, 0, 0)
                    Ellipse(pos=(pos[0] + o.width / 10. - dp(2),
                                 pos[1] + o.height / 10. - dp(2)),
                            size=(dp(4), dp(4)))
                elif type(o) == Frog:
                    if o.player:
                        Color(1, .5, 0)
                    else:
                        Color(0, .2, 0)
                    Ellipse(pos=(pos[0],
                                 pos[1] + o.height / 20),
                            size=(size[0], size[1] / 2))


if __name__ == '__main__':
    FrogApp().run()
