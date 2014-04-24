from kivy.uix.widget import Widget
from main import GameWidget, WaterLily, StoneLily,\
    MathWidget, Frog, JumpLine, Fly, Boat, SwitchLily
from kivy.metrics import dp


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


def build_level(filename, app):
    print "build level\n---------------------------------------------"
    def calculate_point(pos, distance):
        x, y = [float(v) for v in pos]
        x *= distance
        y *= distance
        return x, y

    level = parse_level(filename)
    root = GameWidget(app=app)
    app.game = root
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
            print str(x) + " " + str(y)
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
            if "free" in lily:
                l.free = lily["free"] == "True"
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
            if "free" in lily:
                l.free = lily["free"] == "True"
            root.game_scatter.before_jumpline.add_widget(l)
            root.lilys.append(l)
    # add math widget
    if "math" in level:
        for math in level["math"]:
            m = MathWidget(app=app, root=root)
            if "id" in math:
                m.id = math["id"]
                if m.id not in root.objects:
                    root.objects[m.id] = m
            if "pos" in lily:
                x, y = calculate_point(
                    math["pos"].split(","), distance)
                m.center_x = x
                m.y = y
            root.game_scatter.before_jumpline.add_widget(m)
            root.lily_provider.append(m)
    if "switchlily" in level:
        for lily in level["switchlily"]:
            l = SwitchLily(app=app, root=root)
            if "id" in lily:
                l.id = lily["id"]
                if l.id not in root.objects:
                    root.objects[l.id] = l
            if "pos" in lily:
                x, y = calculate_point(
                    lily["pos"].split(","), distance)
                l.center_x = x
                l.y = y
            if "free" in lily:
                l.free = lily["free"] == "True"
            if "controlled" in lily:
                l.controlled = root.objects[lily["controlled"]]
            root.game_scatter.before_jumpline.add_widget(l)
            root.lilys.append(l)
    # add the flys
    for i in range(flys):
        f = Fly(app=app, root=root)
        root.flys.append(f)
        root.game_scatter.before_jumpline.add_widget(f)
    # add the boats
    for i in range(boats):
        b = Boat(app=app, root=root)
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
                f.place = root.objects[frog["place"]]
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
