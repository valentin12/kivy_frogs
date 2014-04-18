import kivy
kivy.require("1.8.0")
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.properties import ObjectProperty
from kivy.vector import Vector
from kivy.animation import Animation
from kivy.metrics import dp

from kivy.utils import boundary
from kivy.graphics.transformation import Matrix
from math import radians
from math import atan2
from math import pi


class FrogApp(App):
    def build(self):
        from kivy.base import EventLoop
        EventLoop.ensure_window()
        self.window = EventLoop.window
        self.root = MainWidget(app=self)
        return self.root

    def restart(self):
        print "Restart"
        self.stop()


class MainWidget(Widget):
    pass


class Background(Image):
    pass


class JumpLine(Widget):
    def set(self, point1, point2):
        """Set start and end point of the Line"""
        self.start(point1)
        self.end(point2)
        

    def start(self, point):
        """Set the start point"""
        self.x1 = point[0]
        self.y1 = point[1]
        self.cut_to_max()

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
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and self.alive:
            touch.ud["start_pos"] = self.center
            touch.ud["frog"] = self
            self.app.root.jumpline.set(self.center, self.center)
            self.rotate_to(touch.pos)
            return True
        return super(Frog, self).on_touch_down(touch)


    def on_touch_move(self, touch):
        if "start_pos" in touch.ud\
           and "frog" in touch.ud\
           and touch.ud["frog"] == self:
            self.rotate_to(touch.pos)
            self.app.root.jumpline.end(touch.pos)
            return True
        return super(Frog, self).on_touch_move(touch)


    def on_touch_up(self, touch):
        self.app.root.jumpline.set((0, 0), (0, 0))
        if "start_pos" in touch.ud\
           and "frog" in touch.ud\
           and touch.ud["frog"] == self:
            start = Vector(touch.ud["start_pos"])
            end = Vector(touch.pos)
            distance = start.distance(end)
            print "End: " + str(end)
            print "Distance: " + str(distance)
            if distance > dp(120):
                dir = Vector((
                    start.x - end.x, start.y - end.y))
                end = start - dir * dp(120) / distance
            it = list(self.app.root.lilys[:])
            it.append(self.app.root.start)
            die = True
            for lily in it:
                if lily.collide_point(*end):
                    die = False
                    if lily.free:
                        self.place.free = True
                        self.place = lily
                        lily.free = False
                        self.rotate_to(lily.center)
                        anim = Animation(center_x=lily.center_x,
                                         center_y=lily.center_y,
                                         duration = .3)
                        anim.start(self)
                        break
            else:
                if die:
                    self.place.free = True
                    self.go_die(end)
        return super(Frog, self).on_touch_down(touch)

    def go_die(self, point):
        anim = Animation(center_x=point[0],
                         center_y=point[1],
                         duration=.3)
        scale_anim = Animation(scale=.001,
                               duration=2)
        self.alive = False
        for frog in self.app.root.frogs:
            if frog.alive:
                break
        else:
            scale_anim.bind(on_complete=lambda anim,
                            widget: self.app.restart())
        anim.bind(on_complete=lambda anim,
                  widget: scale_anim.start(self.scatter))
        anim.start(self)

    def rotate_to(self, point):
        """Rotate frog to the given point"""
        dx = point[0] - self.center_x
        dy = point[1] - self.center_y
        angle = atan2(dy, dx)
        angle_changed = -(angle * (180 / pi)) + 90
        self.scatter.rotation = -angle_changed
        
            

if __name__ == '__main__':
    FrogApp().run()
