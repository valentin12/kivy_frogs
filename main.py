import kivy
kivy.require("1.8.0")
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.vector import Vector
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.audio import SoundLoader

from math import pi
from math import atan2
from random import randint
from random import random
from random import choice


def only_running():
    """Check if a username exists"""
    def on_decorator(func):
        def on_call(*args):
            try:
                if args[0].app.root.running:
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
        self.sounds = {
            "lost": SoundLoader.load("snd/lost.wav"),
            "won": SoundLoader.load("snd/won.wav"),
            "died": SoundLoader.load("snd/died.wav"),
            "eat": SoundLoader.load("snd/eat.wav"),
            "sink": SoundLoader.load("snd/sink.wav"),
            "jump": SoundLoader.load("snd/jump.wav")
        }

    def build(self):
        from kivy.base import EventLoop
        EventLoop.ensure_window()
        self.window = EventLoop.window
        self.root = MainWidget(app=self)
        self.window.size = (int(self.root.size[0]),
                            int(self.root.size[1]))
        return self.root

    def restart(self):
        self.stop()


class MainWidget(Widget):

    @only_running()
    def decrement_lives(self):
        self.lives -= 1
        self.live_imgs[self.lives].source = self.live_imgs[
            self.lives].lost_img
        if self.lives <= 0:
            self.running = False
            self.app.root.status.text = "Lost"
            self.app.sounds["lost"].play()
            Clock.schedule_once(lambda dt: self.app.restart(), 5)
        else:
            self.app.sounds["died"].play()

    @only_running()
    def level_won(self):
        self.running = False
        self.app.root.status.text = "Won"
        self.app.sounds["won"].play()
        Clock.schedule_once(lambda dt: self.app.restart(), 5)


class Background(Image):
    pass


class RandomMover(Widget):
    """Moves over the field in a random way"""
    def __init__(self, **kwargs):
        super(RandomMover, self).__init__(**kwargs)
        Clock.schedule_interval(lambda dt: self.move(), 1 / 60.)

    def move(self):
        self.scatter.rotation += self.rot_change
        m = Vector(0, self.speed).rotate(self.scatter.rotation)
        self.pos[0] -= m.x
        self.pos[1] -= m.y
        # change direction in ca. every 5000th frame
        if randint(0, 5000) == 10:
            self.rot_change = choice([-1, 1]) * random()
        if self.pos[0] < dp(-70) or\
           self.pos[0] > self.app.root.width + dp(40)\
           or self.pos[1] < dp(-70) or\
           self.pos[1] > self.app.root.height + dp(40):
            self.scatter.rotation -= 180

    def restart(self):
        self.center = (dp(-20), dp(150))


class Fly(RandomMover):
    def move(self):
        super(Fly, self).move()

    def eat(self, eater):
        self.app.root.energy += 4
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
        for lily in self.app.root.lilys:
            if lily.collide_widget(self):
                lily.force_sinking()


class WaterLily(Widget):
    free = BooleanProperty(True)
    sinking = BooleanProperty(False)
    appearing = False

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
        if not self.static and not self.sinking and not self.appearing:
            self.sinking = True
            self.sinking_anim.start(self.scatter)

    def appear(self, dt):
        self.sinking = False
        for frog in self.app.root.frogs:
            if frog.place == self:
                Clock.schedule_once(lambda dt: frog.revive(),
                                    self.appear_anim.duration)
                break
        self.appearing = True
        self.appear_anim.start(self.scatter)

    def on_sank(self):
        # kill all frogs on the lily
        reappear_after = 3
        for frog in self.app.root.frogs:
            if frog.place == self:
                frog.kill()
                # live lost, don't wait so long
                reappear_after = 1
        # wait under water, then appear again
        Clock.schedule_once(self.appear, reappear_after)

    def on_appeared(self):
        self.appearing = False

    def on_sinking_changed(self, instance, value):
        if value:
            self.app.sounds["sink"].play()


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
    player = BooleanProperty(False)

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
            self.app.root.jumpline.set(self.center, self.center)
            self.rotate_to(touch.pos)
            return True
        return super(Frog, self).on_touch_down(touch)

    @only_running()
    def on_touch_move(self, touch):
        if "start_pos" in touch.ud\
           and "frog" in touch.ud\
           and touch.ud["frog"] == self:
            self.rotate_to(touch.pos)
            # update jump line
            self.app.root.jumpline.end(touch.pos)
            return True
        return super(Frog, self).on_touch_move(touch)

    @only_running()
    def on_touch_up(self, touch):
        self.app.root.jumpline.set((0, 0), (0, 0))
        if "start_pos" in touch.ud\
           and "frog" in touch.ud\
           and touch.ud["frog"] == self\
           and self.alive:
            start = Vector(touch.ud["start_pos"])
            end = Vector(touch.pos)
            distance = start.distance(end)
            if distance > dp(120):
                dir = Vector((
                    start.x - end.x, start.y - end.y))
                end = start - dir * dp(120) / distance
            for fly in self.app.root.flys:
                if fly.collide_point(*end):
                    fly.eat(self)
                    return True
            it = list(self.app.root.lilys[:])
            it.append(self.app.root.start)
            it.append(self.app.root.end)
            # you can only jump - and die - if you have energy
            die = self.app.root.energy
            for lily in it:
                collide = False
                try:
                    collide = lily.scatter.collide_point(*end)
                except AttributeError:
                    collide = lily.collide_point(*end)
                if collide:
                    die = False
                    if lily.free and self.app.root.energy:
                        self.app.root.energy -= 1
                        self.place.free = True
                        self.place = lily
                        lily.free = False
                        self.rotate_to(lily.center)
                        anim = Animation(center_x=lily.center_x,
                                         center_y=lily.center_y,
                                         duration=self.jump_duration)
                        anim.bind(on_complete=
                                  lambda a, b:
                                  self.set_img(self.sit_img))
                        anim.start(self)
                        self.app.sounds["jump"].play()
                        Clock.schedule_once(
                            lambda dt: self.set_img(self.jump_img),
                            self.jump_duration / 3)
                        # check if player reached the end
                        if self.player and lily == self.app.root.end:
                            self.app.root.level_won()
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
        self.app.root.decrement_lives()
        self.die_anim.start(self.scatter)

    @only_running()
    def revive(self):
        scale_anim = Animation(scale=1,
                               duration=self.revive_duration)
        anim = Animation(center_x=self.place.center_x,
                         center_y=self.place.center_y,
                         duration=self.revive_duration)
        self.alive = True
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
        self.source = img


if __name__ == '__main__':
    FrogApp().run()
