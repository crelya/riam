self.map = {
    tiles: [
        {
            position: [0, 0],
            status: DEAD_END,
            begin: True,
            end: False,
            input_dir: [],
            output_dirs: [],
            possible_dirs: [NORTH]
            forbidden_dirs: [WEST, SOUTH, EAST]
        }
    ]
}


# self.position = self.map["tiles"][0]

act[0,0]

def act(position):
    self.position = tile(position)
    if self.position["end"] is True:
        # notify_finish() TODO
        return True
    else:
        while self.position["possible_dirs"].length > 0:
            direction = self.position["possible_dirs"].pop()
            if check(direction):
                self.position["output_dirs"].append(direction)
                move()
                # notify_and_wait()
                if act(next_position(position, direction)):
                    return True
            else:
                self.position["forbidden_dirs"].append(direction)

        look_at(self.position["input_dir"])
        move()
        # notify_and_wait()
        return False



def next_position(position, direction):
    if direction is NORTH
        return [position[0], position[1] + 1]
    elif direction is EAST
        return [position[0] + 1, position[1]]
    elif direction is SOUTH
        return [position[0], position[1] - 1]
    elif direction is WEST
        return [position[0] - 1, position[1]]


def tile(x, y):
    #TODO return a tile in map.
    pass


def notify_and_wait:
    notify()
    self.status = WAITING
    while self.status is WAITING:
        pass

def notify:
    #TODO query master new map info
    pass

def move(steps=1):
    #TODO gpio move
    pass

def rotate(grades):
    #TODO gpio rotate
    pass

def check(direction):
    look(direction)
    return path_clear()

def path_clear:
    #TODO gpio check if front is blocked
    return True

def look_north:
    if self.direction is EAST
        rotate(90)
    elif self.direction is SOUTH
        rotate(180)
    elif self.direction is WEST
        rotate(-90)


def look_east:
    if self.direction is SOUTH
        rotate(90)
    elif self.direction is WEST
        rotate(180)
    elif self.direction is NORTH
        rotate(-90)

def look_south:
    if self.direction is WEST
        rotate(90)
    elif self.direction is NORTH
        rotate(180)
    elif self.direction is EAST
        rotate(-90)

def look_west:
    if self.direction is SOUTH
        rotate(90)
    elif self.direction is EAST
        rotate(180)
    elif self.direction is NORTH
        rotate(-90)

def look(direction):
    if direction is NORTH:
        look_north()
    elif direction is EAST:
        look_east()
    elif direction is SOUTH:
        look_south()
    else
        look_west()
