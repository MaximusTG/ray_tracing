from PIL import Image
from pygame import Surface
from vector import *


EPS = 0.0001
AMBIENT = 0.1
BACKGROUND = Vector(AMBIENT, AMBIENT, AMBIENT)
MAG = 1
ANDY = 2
DISTANT = 3
FILL = 4
SQUARED = 5


def sign(x):
    if x >= 0:
        return 1
    else:
        return -1


def g(x, y, z):
    return sin(x) * sin(y) * sin(z)


class Ray:
    def __init__(self, origin, direction):
        self.o = origin
        self.d = direction
    
    def __repr__(self):
        return self.d.__repr__()


class Properties:
    def __init__(self, color=Vector(0, 0, 0), reflective=0, refractive=0, refractive_coef=1, type=FILL, scale=1,
                 rotation=(0, 0, 0), constant_color=False):
        self.color = color
        self.reflective = reflective
        self.refractive = refractive
        self.refractive_coef = refractive_coef
        self.type = type
        self.scale = scale
        self.rotation = rotation
        self.constant_color = constant_color

    def cp(self):
        return Properties(self.color,
                          self.reflective,
                          self.refractive,
                          self.refractive_coef,
                          self.type,
                          self.scale,
                          self.rotation,
                          self.constant_color)


class Sphere:
    def __init__(self, center, radius, properties):
        self.c = center
        self.r = radius

        props = properties
        self.color = props.color
        self.reflective = props.reflective
        self.refractive_coef = props.refractive_coef
        self.refractive = props.refractive
        self.properties = props

    def update_properties(self, properties=None):
        if properties:
            props = properties
        else:
            props = self.properties

        self.color = props.color
        self.reflective = props.reflective
        self.refractive_coef = props.refractive_coef
        self.refractive = props.refractive
        self.properties = props
    
    def intersect(self, ray):
        c_o = ray.o - self.c
        r_ = self.r  # modify this for weird forms of sphere
        discriminant = r_ ** 2 - (c_o.dot(c_o) - ray.d.dot(c_o) ** 2)
        if discriminant < 0:
            return Intersection(Vector(0, 0, 0), -1, Vector(0, 0, 0), self)
        else:
            b = -ray.d.dot(c_o)
            d1 = b - sqrt(discriminant)
            d2 = b + sqrt(discriminant)
            
            if d1 > 0 and (d2 > d1 or d2 < 0):
                d = d1
            elif d2 > 0 and (d1 > d2 or d1 < 0):
                d = d2
            else:
                return Intersection(Vector(0, 0, 0), -1, Vector(0, 0, 0), self)

            point = ray.o + ray.d * d
            intersection = Intersection(point, d, self.normal(point), self)
            return intersection
    
    def normal(self, other):
        return (other - self.c).normal()


class Plane:
    def __init__(self, point, normal, properties):
        self.p = point
        self.n = normal

        props = properties
        self.color = props.color
        self.reflective = props.reflective
        self.refractive_coef = props.refractive_coef
        self.refractive = props.refractive
        self.type = props.type
        self.scale = props.scale
        self.properties = props

        self.stable_normal = False

    def update_properties(self, properties=None):
        if properties:
            props = properties
        else:
            props = self.properties

        self.color = props.color
        self.reflective = props.reflective
        self.refractive_coef = props.refractive_coef
        self.refractive = props.refractive
        self.type = props.type
        self.scale = props.scale
        self.properties = props

    def __repr__(self):
        return 'Plane[{}, {}]'.format(self.p, self.n)

    def intersect(self, ray, stabilized=False):
        cs = self.n.dot(ray.d)
        if abs(cs) < EPS or cs > 0:
            if self.stable_normal or stabilized:
                return Intersection(Vector(0, 0, 0), -1, Vector(0, 0, 0), self)
            else:
                self.n *= -1
                ret = self.intersect(ray, True)
                if ret.d > 0:
                    self.stable_normal = True
                return ret

        cs = (self.p - ray.o).dot(self.n) / cs
        return Intersection(ray.o + ray.d * cs, cs, self.n, self)


class Triangle:
    def __init__(self, p1, p2, p3, properties):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.normal = (p2-p1).cross(p3-p1).normal()
        self.plane = Plane(p1, self.normal, properties)

        props = properties
        self.color = props.color
        self.reflective = props.reflective
        self.refractive_coef = props.refractive_coef
        self.refractive = props.refractive
        self.type = props.type
        self.scale = props.scale
        self.properties = props
        
        self.square = (p2 - p1).cross(p3 - p1).len() / 2

    def update_properties(self, properties=None):
        if properties:
            props = properties
        else:
            props = self.properties

        self.color = props.color
        self.reflective = props.reflective
        self.refractive_coef = props.refractive_coef
        self.refractive = props.refractive
        self.type = props.type
        self.scale = props.scale
        self.properties = props

    def __repr__(self):
        return 'Triangle[{}, {}, {}]'.format(self.p1, self.p2, self.p3)

    def is_point_inside(self, p):
        if abs((p - self.p1).dot(self.plane.n)) > EPS:
            return False
        
        p_p1 = self.p1 - p
        p_p2 = self.p2 - p
        p_p3 = self.p3 - p
        sq = (abs(p_p1.cross(p_p2).len()) + abs(p_p2.cross(p_p3).len()) + abs(p_p3.cross(p_p1).len())) / 2
        if abs(self.square - sq) > EPS:
            return False
        else:
            return True
    
    def intersect(self, ray):
        p = self.plane.intersect(ray)
        if p.d == -1:
            self.plane.n *= -1
            p = self.plane.intersect(ray)
        if p.d < 0:
            return p

        if self.is_point_inside(p.p):
            return p
        else:
            return Intersection(Vector(0, 0, 0), -1, Vector(0, 0, 0), self)


class Intersection:
    def __init__(self, point, distance, normal, obj):
        self.p = point
        self.d = distance
        self.n = normal
        self.obj = obj
    
    def __eq__(self, other):
        return self.p == other.p and self.d == other.d and self.n == other.n and self.obj == other.obj
    
    def __lt__(self, other):
        if self.d < other.d:
            return True
    
    def __repr__(self):
        return 'Intersection<p[{}], d[{}]>'.format(self.p, self.d)


class Light:
    def __init__(self, origin, color, type=MAG, distance_coef=200000):
        self.o = origin
        self.color = color
        self.type = type
        self.distance_coef = distance_coef
    
    def calculate_effect(self, point, normal, obj, objects):
        if self.type == MAG:
            p_o = self.o - point
            if p_o.len() == 0:
                return self.color
            
            intersection = test_ray(Ray(point + p_o.normal(), p_o.normal()), objects, [obj])
            dist = intersection.d            
            if dist != -1 and dist < p_o.len() and not intersection.obj.refractive:
                return Vector(0, 0, 0)
            else:
                reflection_coef = obj.reflective
                intensity = self.distance_coef / (12.5 * p_o.len() ** (2 - reflection_coef / 5))
                power = max(normal.dot(p_o.normal() * intensity), AMBIENT)
                if power != AMBIENT:
                    power = power + reflection_coef * normal.dot(p_o.normal()) ** (100 * reflection_coef)
                return self.color * power

        elif self.type == DISTANT:
            p_o = self.o.normal() * -1
            intersection = test_ray(Ray(point + p_o * 0.0001, p_o), objects, [obj])
            if intersection.d != -1:
                return Vector(0, 0, 0)
            else:
                return self.color * (-self.o.dot(normal))


def test_ray(ray, objects, to_ignore=()):
    intersection = Intersection(Vector(0, 0, 0), -1, Vector(0, 0, 0), None)
    for obj in objects:
        if obj in to_ignore:
            continue
        current_intersection = obj.intersect(ray)
        if current_intersection.d > 0 > intersection.d:
            intersection = current_intersection
        elif 0 < current_intersection.d < intersection.d:
            intersection = current_intersection
    return intersection


def get_color(color):
    return tuple(map(lambda x: min(255, int(x * 255)), [color.x, color.y, color.z]))


def trace(ray, objects, lights, depth=1):
    if not depth:
        return BACKGROUND
    intersection = test_ray(ray, objects)
    if intersection.d == -1:
        return BACKGROUND
    
    obj = intersection.obj
    point = intersection.p
    color = obj.color
    light_effect = Vector(0, 0, 0)
    reflected_color = Vector(0, 0, 0)
    refracted_color = Vector(0, 0, 0)

    if obj.properties.constant_color:
        return color

    '''
    # YOU CAN ADD SOME TEXTURES HERE! it was a nice mistake
    if isinstance(obj, Sphere) and obj == objects[0]:
        point = point + intersection.n.normal()*obj.r*abs(g(point.x * coef, point.y * coef, point.z * coef))
        intersection.d = (point - ray.o).len()
        intersection.p = point
    '''

    if isinstance(obj, Plane) and obj.type == SQUARED:
        def f(n):
            return sign(sin(n / obj.scale))
        x = f(point.x)
        y = f(point.y)
        z = f(point.z)
        color *= sign(g(x, y, z))

    for light in lights:
        light_effect += light.calculate_effect(intersection.p, intersection.n, obj, objects)
    
    if depth and obj.reflective:
        reflected_vector = (ray.d - intersection.n * 2 * ray.d.dot(intersection.n)).normal()
        reflected_ray = Ray(intersection.p + reflected_vector * EPS, reflected_vector)
        reflected_color = trace(reflected_ray, objects, lights, depth - 1)
        reflected_color *= intersection.obj.reflective

    if depth and obj.refractive:
        normal = intersection.n
        cs = ray.d.dot(normal)
        
        coef_from = 1
        coef_to = obj.refractive_coef
        if cs < 0:
            cs *= -1
        else:
            normal = normal * -1
            coef_from, coef_to = coef_to, coef_from

        ratio = coef_from / coef_to
        k = 1 - ratio * ratio * (1 - cs * cs)
        if k < 0:
            pass
        else:
            refracted_vector = ray.d * ratio + normal * (ratio * cs - sqrt(k))
            refracted_ray = Ray(intersection.p + refracted_vector * EPS, refracted_vector)
            refracted_color = trace(refracted_ray, objects, lights, depth - 1)
    color *= light_effect * (1 - obj.refractive) * (1 - obj.reflective)
    color += reflected_color + refracted_color * obj.refractive

    return color  # * abs(g(point.x * COEF, point.y * COEF, point.z * COEF)) visual effects


def render_image(camera=None, objects=None, lights=None, depth=2, verbose=1, scene=None, pygame_mode=False):
    if None in [camera, objects, lights]:
        if scene is None:
            return
        else:
            camera = scene.camera
            objects = scene.objects
            lights = scene.lights
    if pygame_mode:
        img = Surface((camera.res_x, camera.res_y))
    else:
        img = Image.new('RGB', (camera.res_x, camera.res_y))
    
    for y in range(camera.res_y):
        if verbose:
            if y % (camera.res_y // 10) == 0:
                print(y / camera.res_y)
        for x in range(camera.res_x):
            ray = camera.get_ray(y, x)
            color = trace(ray, objects, lights, depth)
            if pygame_mode:
                img.set_at((x, y), get_color(color))
            else:
                img.putpixel((x, y), get_color(color))
    
    if verbose:
        print('1.0')
    return img


class Camera:
    def __init__(self, origin, direction, distance, width, height, res_coef):
        self.o = origin
        self.d = direction.normal()
        self.dist = distance
        self.w = width
        self.h = height
        self.res_x = int(width * res_coef)
        self.res_y = int(height * res_coef)
        
        self.ort1 = Vector(-self.d.y, self.d.x, self.d.z).normal()
        self.ort2 = self.ort1.cross(self.d).normal()
        self.left_upper = self.o + self.d * distance + self.ort1 * width / 2 + self.ort2 * height / 2
    
    def get_ray(self, x, y):
        dx = self.ort1 * x * self.w / self.res_x
        dy = self.ort2 * y * self.h / self.res_y
        return Ray(self.o, (self.left_upper - dx - dy).normal())

    def update(self):
        self.ort1 = Vector(-self.d.y, abs(self.d.x), 0).normal()
        self.ort2 = self.ort1.cross(self.d).normal()
        self.left_upper = self.o + self.d * self.dist + self.ort1 * self.w / 2 + self.ort2 * self.h / 2


class Scene:
    def __init__(self, camera, objects, lights, bias=Vector(0, 0, 0)):
        self.camera = camera
        self.objects = objects
        self.lights = lights
        self.bias = bias
    
    def move(self, delta):
        self.bias += delta
    
    def rotate_camera(self, delta):
        self.camera.direction = rotx(roty(rotz(self.camera.direction, delta.z), delta.y), delta.x)


class Model:
    def __init__(self, center, coef, properties, points=(), links=(), file=None):
        self.center = center
        self.coef = coef

        if file:
            fin = open(file, 'r')
            self.points = []
            self.links = []
            for line in fin.readlines():
                s = line[:-1]
                if not s:
                    continue
                s = s.split()
                type = s[0]
                nums = s[1:]
                if type == 'p':
                    x, y, z = map(float, nums)
                    self.points.append(Vector(x, -y, z))
                elif type == 'l':
                    link = list(map(lambda index: int(index) - 1, nums))
                    self.links.append(link)
        else:
            self.points = points
            self.links = links

        props = properties
        self.color = props.color
        self.reflective = props.reflective
        self.refractive_coef = props.refractive_coef
        self.refractive = props.refractive
        self.type = props.type
        self.scale = props.scale
        self.rotation = props.rotation
        self.properties = props
    
    def get_triangles(self):
        triangles = []
        for link in self.links:
            p0 = rot(self.points[link[0]] * self.coef, rotation=self.rotation) + self.center
            for i in range(1, len(link) - 1):
                p1 = rot(self.points[link[i]] * self.coef, rotation=self.rotation) + self.center
                p2 = rot(self.points[link[i + 1]] * self.coef, rotation=self.rotation) + self.center
                triangle = Triangle(p0, p1, p2, self.properties)
                triangles.append(triangle)
        return triangles


def generate_box_for_spheres(objects, indents=(0, 0, 0, 0, 0, 0), indent=None):
    if indent:
        indents = [indent for _ in range(6)]
    right = -1000
    left = 1000
    up = -1000
    down = 1000
    back = -1000
    front = 1000
    for obj in objects:
        if not isinstance(obj, Sphere):
            continue

        right = max(right, obj.c.z + obj.r) + indents[0]
        left = min(left, obj.c.z - obj.r) - indents[1]
        up = max(up, obj.c.y + obj.r) + indents[2]
        down = min(down, obj.c.y - obj.r) - indents[3]
        back = max(back, obj.c.x + obj.r) + indents[4]
        front = max(front, obj.c.x - obj.r) + indents[5]

    right = {'p': Vector(0, 0, right), 'n': Vector(0, 0, -1)}
    left = {'p': Vector(0, 0, left), 'n': Vector(0, 0, 1)}
    up = {'p': Vector(0, up, 0), 'n': Vector(0, -1, 0)}
    down = {'p': Vector(0, down, 0), 'n': Vector(0, 1, 0)}
    back = {'p': Vector(back, 0, 0), 'n': Vector(-1, 0, 0)}
    front = {'p': Vector(front, 0, 0), 'n': Vector(1, 0, 0)}

    box = {'right': right, 'left': left, 'up': up, 'down': down, 'back': back, 'front': front}
    return box


'''
box = ray_tracer.generate_box_for_spheres(objects, indents=[5, 10, 0, -10, 5, 0])
for dr in box:
    if dr == 'front':
        continue
    plane = box[dr]
    r = random.uniform(0.3, 0.7)
    g = random.uniform(0.3, 0.7)
    b = random.uniform(0.3, 0.7)
    objects.append(ray_tracer.Plane(plane['p'], plane['n'], Vector(r, g, b)))
'''


def main():
    print('Testing triangle')
    p1 = Vector(0, 0, 0)
    p2 = Vector(0, 3, 0)
    p3 = Vector(0, 0, 5)
    t = Triangle(p1, p2, p3, Vector(1, 1, 1))
    p = Vector(0, 1, 1)
    print(t.is_point_inside(p))


if __name__ == '__main__':
    main()
