from kivy.uix.widget import Widget
from main import GameWidget, WaterLily, StoneLily,\
    MathWidget, Frog, JumpLine, Fly, Boat, SwitchLily, IntervalWidget
from kivy.metrics import dp
from os import listdir, getcwd


def find_levels():
    levels = []
    for file in listdir("levels"):
        if file.startswith("level_") and file.endswith(".txt"):
            levels.append("levels/" + file)
    levels.sort()
    return levels


def find_custom_levels():
    levels = []
    for file in listdir("levels"):
        if file.startswith("custom_level_") and file.endswith(".txt"):
            levels.append("levels/" + file)
    levels.sort()
    return levels


def parse_level(filepath):
    f = open(filepath)
    text = f.read()
    f.close()
    level = {}
    for line in text.split("\n"):
        opts = [opt.strip() for opt in line.split(" ")]
        d = {}
        for opt in opts:
            if "=" in opt:
                key, value = [v.strip() for v in opt.split("=")]
                d[key] = value
        if opts[0] in level:
            level[opts[0]].append(d)
        else:
            level[opts[0]] = [d]
    return level


def build_level(filename, app, root):
    def calculate_point(pos, distance):
        x, y = [float(v) for v in pos]
        x *= distance
        y *= distance
        return x, y

    # reset game to standard settings
    root.game_scatter.before_jumpline.clear_widgets()
    root.game_scatter.jumplines.clear_widgets()
    root.game_scatter.after_jumplines.clear_widgets()
    root.objects = {}
    root.frogs = []
    root.lilys = []
    root.flys = []
    for boat in root.boats:
        boat.active = False
    root.boats = []
    root.lily_provider = []
    root.lives = 3
    for i in range(root.lives):
        root.live_imgs[i].source = root.live_imgs[i].alive_img
    root.running = True
    root.game_scatter.center_x = app.window.width / 2
    root.game_scatter.y = 0
    root.energy = 4
    root.status.text = ""
    root.start.free = True
    root.end.free = True
    # load level dict
    level = parse_level(filename)
    # setup level specific things
    distance = dp(100)
    l = level["level"][0]
    if "size" in l:
        width, height = calculate_point(
            l["size"].split(","), distance)
        root.preferred_size = (width, height)
    if "energy" in l:
        root.energy = int(l["energy"])
    if "flys" in l:
        flys = int(l["flys"])
    else:
        flys = 4
    if "boats" in l:
        boats = int(l["boats"])
    else:
        boats = 0
    # background image
    if "background" in level:
        if "source" in level["background"]:
            root.background.source = level["background"]["source"]
    # start base
    if "start" in level:
        if "pos" in level["start"][0]:
            x, y = calculate_point(
                level["start"][0]["pos"].split(","), distance)
            root.start.center_x = x
            root.start.y = y
        if "source" in level["start"][0]:
            root.start.source = level["start"][0]["source"]
    # end base
    if "end" in level:
        if "pos" in level["end"][0]:
            x, y = calculate_point(
                level["end"][0]["pos"].split(","), distance)
            root.end.center_x = x
            root.end.y = y
        if "source" in level["end"][0]:
            root.end.source = level["end"][0]["source"]
    if "waterlily" in level:
        for lily in level["waterlily"]:
            l = WaterLily(app=app, root=root)
            if "id" in lily:
                l.id = lily["id"]
                if l.id not in root.objects:
                    root.objects[l.id] = l
            if "pos" in lily:
                x, y = calculate_point(
                    lily["pos"].split(","), distance)
                l.center_x = x
                l.y = y
            l.free = True
            root.game_scatter.before_jumpline.add_widget(l)
            root.lilys.append(l)
    if "stonelily" in level:
        for lily in level["stonelily"]:
            l = StoneLily(app=app, root=root)
            if "id" in lily:
                l.id = lily["id"]
                if l.id not in root.objects:
                    root.objects[l.id] = l
            if "pos" in lily:
                x, y = calculate_point(
                    lily["pos"].split(","), distance)
                l.center_x = x
                l.y = y
            root.game_scatter.before_jumpline.add_widget(l)
            root.lilys.append(l)
    # add math widget
    if "math" in level:
        for i in range(len(level["math"])):
            math = level["math"][i]
            try:
                m = [ma for ma in root.store
                     if type(ma) == MathWidget][i]
            except IndexError:
                m = MathWidget(app=app, root=root)
                root.store.append(m)
            min = int(float(app.config.getfloat(
                "Math", "Min")))
            max = int(float(app.config.getfloat(
                "Math", "Max")))
            m.number_range = (min, max)
            m.type = app.config.get(
                "Math", "TypeOfCalculation")
            if "id" in math:
                m.id = math["id"]
                if m.id not in root.objects:
                    root.objects[m.id] = m
            if "pos" in math:
                x, y = calculate_point(
                    math["pos"].split(","), distance)
                m.center_x = x
                m.y = y
            if "count" in math:
                m.count = int(math["count"])
            else:
                m.count = 5
            if "speed" in math:
                m.speed = float(math["speed"])
            else:
                m.speed = 1
            if "orientation" in math:
                m.orientation = math["orientation"]
            else:
                m.orientation = "horizontal"
            m.setup(force=True)
            root.game_scatter.before_jumpline.add_widget(m)
            root.lily_provider.append(m)
    if "interval" in level:
        for i in range(len(level["interval"])):
            interval = level["interval"][i]
            try:
                i = [iv for iv in root.store if type(iv) == IntervalWidget][i]
            except IndexError:
                i = IntervalWidget()
                root.store.append(i)
            if "id" in interval:
                i.id = interval["id"]
                if i.id not in root.objects:
                    root.objects[i.id] = i
            if "pos" in interval:
                x, y = calculate_point(
                    interval["pos"].split(","), distance)
                i.center_x = x
                i.y = y
            if "count" in interval:
                i.count = int(interval["count"])
            else:
                i.count = 5
            if "speed" in interval:
                i.speed = float(interval["speed"])
            else:
                i.speed = 1
            if "orientation" in interval:
                i.orientation = interval["orientation"]
            else:
                i.orientation = "horizontal"
            i.setup(force=True)
            root.game_scatter.before_jumpline.add_widget(i)
            root.lily_provider.append(i)
    if "switchlily" in level:
        for lily in level["switchlily"]:
            if "controlled" in lily:
                try:
                    cont = dict(root.objects.items() +
                                        root.standard_objects.items()
                                    )[lily["controlled"]]
                    l = SwitchLily(app=app, root=root)
                    l.controlled = cont
                except KeyError:
                    # if the controlled doesn't exist, make it static  
                    l = StoneLily(app=app, root=root)
            else:
                l = StoneLily(app=app, root=root)
            if "id" in lily:
                l.id = lily["id"]
                if l.id not in root.objects:
                    root.objects[l.id] = l
            if "pos" in lily:
                x, y = calculate_point(
                    lily["pos"].split(","), distance)
                l.center_x = x
                l.y = y
            root.game_scatter.before_jumpline.add_widget(l)
            root.lilys.append(l)
    # add the flys
    for i in range(flys):
        try:
            f = [fly for fly in root.store if type(fly) == Fly][i]
        except IndexError:
            f = Fly(app=app, root=root)
            root.store.append(f)
        root.flys.append(f)
        root.game_scatter.before_jumpline.add_widget(f)
    # add the boats
    for i in range(boats):
        try:
            b = [boat for boat in root.store if type(boat) == Boat][i]
            b.active = True
        except IndexError:
            b = Boat(app=app, root=root)
            root.store.append(boat)
        root.boats.append(b)
        root.game_scatter.before_jumpline.add_widget(b)
    # and the frogs
    if "frog" in level:
        for frog in level["frog"]:
            f = Frog(app=app, root=root)
            if "id" in frog:
                f.id = frog["id"]
                if f.id not in root.objects:
                    root.objects[f.id] = f
            if "place" in frog:
                f.place = dict(root.objects.items() +
                               root.standard_objects.items())[frog["place"]]
                f.place.free = False
                f.center_x = f.place.center_x
                f.center_y = f.place.center_y
            else:
                print "--------------------------------"
                print "WARNING: Frog has no place given"
                print "--------------------------------"
            if "player" in frog:
                f.player = frog["player"] == "True"
                if f.player:
                    root.player = f
            if "sit_img" in frog:
                f.sit_img = frog["sit_img"]
            if "jump_img" in frog:
                f.jump_img = frog["jump_img"]
            root.frogs.append(f)
            root.game_scatter.after_jumplines.add_widget(f)
    return root
