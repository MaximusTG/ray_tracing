from math import sqrt
from PIL import Image


AMBIENT = 0.1


class Vector:
    def __init__(self,x,y,z):
        self.x = x
        self.y = y
        self.z = z

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return (self.y * other.z - self.z * other.y, self.z * other.x - self.x * other.z, self.x * other.y - self.y * other.x)

    def len(self):
        return sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normal(self):
        l = self.len()
        return Vector(self.x / l, self.y / l, self.z / l)

    def proection(self, other):
        return self.normal() * self.dot(other.normal()) * other.len()
    
    def to_ints(self):
        return Vector(int(self.x), int(self.y), int(self.z))

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        assert type(other) == float or type(other) == int
        return Vector(self.x * other, self.y * other, self.z * other)

    def __pow__(self, other):
        return Vector(self.x ** other, self.y ** other, self.z ** other)

    def __repr__(self):
        return '{' + '{}, {}, {}'.format(self.x, self.y, self.z) + '}'

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z


class Ray:
    def __init__(self, origin, direction):
        self.o = origin
        self.d = direction


class Sphere:
    def __init__(self, center, radius, color, reflective):
        self.c = center
        self.r = radius
        self.color = color
        self.reflective = reflective
    
    def intersect(self, ray):
        c_o = ray.o - self.c
        q = self.r ** 2 - (c_o.dot(c_o) - ray.d.dot(c_o) ** 2)
        if q < 0:
            return Intersection(Vector(0, 0, 0), -1, Vector(0, 0, 0), self)
        else:
            d = -ray.d.dot(c_o)
            d1 = d - sqrt(q)
            d2 = d + sqrt(q)
            
            if d1 > 0 and (d2 > d1 or d2 < 0):
                d = d1
            elif d2 > 0 and (d1 > d2 or d1 < 0):
                d = d2
            else:
                return Intersection(Vector(0, 0, 0), -1, Vector(0, 0, 0), self)
            
            point = ray.o + ray.d * d
            return Intersection(point, d, self.normal(point), self)
    
    def normal(self, other):
        return (other - self.c).normal()


class Intersection:
    def __init__(self, point, distance, normal, obj):
        self.p = point
        self.d = distance
        self.n = normal
        self.obj = obj
    
    def __eq__(self, other):
        return self.p == other.p and self.d == other.d and self.n == other.n and self.obj == other.obj
    
    def __repr__(self):
        return 'Intersection<p[{}], d[{}]>'.format(self.p, self.d)


class Camera:
    def __init__(self, origin, direction, width, height, res_x, res_y):
        self.o = origin
        self.d = direction
        self.w = width
        self.h = height
        self.res_x = res_x
        self.res_y = res_y
        
        self.left_upper = self.d + Vector(0, width/2, -height/2)
    
    def get_ray(self, x, y):
        return Ray(self.o, (self.left_upper + Vector(0, -x * self.w / self.res_x, y * self.h / self.res_y)).normal())


class Light:
    def __init__(self, origin, color):
        self.o = origin
        self.color = color


def test_ray(ray, objects):
    intersect = Intersection(Vector(0,0,0), -1, Vector(0,0,0), None)
    for obj in objects:
        cur = obj.intersect(ray)
        if intersect.d == -1 or (intersect.d > cur.d and cur.d != -1):
            intersect = cur
    return intersect


def mix(a, b, mix):
    return b * mix + a * (1 - mix)


def trace(ray, objects, lights, depth=1):
    if not depth:
        return (AMBIENT, AMBIENT, AMBIENT)
    intersection = test_ray(ray, objects)
    if intersection.d == -1:
        return (AMBIENT, AMBIENT, AMBIENT)
    else:
        color = intersection.obj.color
        if depth and intersection.obj.reflective:
            refvec = (ray.d - intersection.n * 2 * ray.d.dot(intersection.n)).normal()
            refray = Ray(intersection.p + refvec * 0.0001, refvec) # bios to prevent ray hitting itselfs origin
            refcolor = trace(refray, objects, lights, depth - 1)
            refcolor = Vector(refcolor[0], refcolor[1], refcolor[2])
            color = color + refcolor * intersection.obj.reflective
        light_effect = AMBIENT
        for light in lights:
            p_o = light.o - intersection.p
            if intersection.n.dot(p_o) < 0:
                continue
            else:
                power = max(1.3 * intersection.n.normal().dot(p_o.normal()) / p_o.len() ** 0.14, AMBIENT)
                if light_effect == AMBIENT:
                    light_effect = power
                else:
                    light_effect = 1.5 * light_effect + power * 0.5
        
        color = color * light_effect
                
    return (color.x, color.y, color.z)


def get_color(color):
    return tuple(map(lambda x: min(255, int(x * 255)), color))


BACKGROUND = Vector(AMBIENT, AMBIENT, AMBIENT)


def main():
    m = 50
    w = m
    h = m
    res = 16
    img = Image.new('RGB', (int(w * res), int(h * res)))
    c = Camera(Vector(0, 0, 0), Vector(m, 0, 0), w, h, int(w * res), int(h * res))
    
    objects = [Sphere(Vector(m + 2 * m - 10, m / 2, 0), m/3, Vector(0.3, 0.6, 0.6), 0), Sphere(Vector(m + 2 * m, m / 2, 0), m / 2, Vector(1, 0, 0), 0), Sphere(Vector(m + 2 * m, - m / 2, -m / 4), m / 4, Vector(1, 0.5, 0.25), 1), Sphere(Vector(m + 2 * m, 0, m), m / 3, Vector(0, 1, 0), 0.3)]
    lights = [Light(Vector(m + 1.3* m, 0, 0), Vector(1, 1, 1))]#, Light(Vector(m + 1.3* m, 2 * m, 0), Vector(1, 1, 1))]
    
    for y in range(c.res_y):
        if y % (c.res_y // (10)) == 0:
            print(y / (c.res_y))
        for x in range(c.res_x):
            ray = c.get_ray(y, x)
            color = trace(ray, objects, lights, depth=2)
            img.putpixel((x, y), get_color(color))
    img = img.resize((800, 800), Image.NEAREST)
    img.show()
    img.save('render.png')

main()