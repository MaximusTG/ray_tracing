from math import sqrt
from PIL import Image
from time import time


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
        if l == 0:
            return Vector(0, 0, 0)
        else:
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
        if isinstance(other, Vector):
            return Vector(self.x * other.x, self.y * other.y, self.z * other.z)
        else:
            assert type(other) == float or type(other) == int
            return Vector(self.x * other, self.y * other, self.z * other)

    def __pow__(self, other):
        return Vector(self.x ** other, self.y ** other, self.z ** other)

    def __repr__(self):
        return '{' + '{}, {}, {}'.format(self.x, self.y, self.z) + '}'

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __lt__(self, other):
        return self.x < other.x or self.y < other.y or self.z < other.z

class Ray:
    def __init__(self, origin, direction):
        self.o = origin
        self.d = direction
    
    def __repr__(self):
        return self.d.__repr__()


class Sphere:
    def __init__(self, center, radius, color, reflective=0, refractive=0):
        self.c = center
        self.r = radius
        self.color = color
        self.reflective = reflective
        self.refractive = refractive
    
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


class Plane:
    def __init__(self, point, normal, color, reflective=0, refractive=0):
        self.p = point
        self.n = normal
        self.color = color
        self.reflective = reflective
        self.refractive = refractive
    
    def intersect(self, ray):
        d = self.n.dot(ray.d)
        if abs(d) < 0.000001:
            return Intersection(Vector(0, 0, 0), -1, Vector(0, 0, 0), self)
        else:
            d = (self.p - ray.o).dot(self.n) / d
            if d < 0:
                return Intersection(Vector(0, 0, 0), -1, Vector(0, 0, 0), self)
            else:
                return Intersection(ray.o + ray.d * d, d, self.n, self)


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


class Light:
    def __init__(self, origin, color, type='Mag', distance_coef=200000):
        self.o = origin
        self.color = color
        self.type = type
        self.distance_coef = distance_coef
    
    def calculate_effect(self, point, normal, obj, objects):
        p_o = self.o - point
        d = test_ray(Ray(point + p_o.normal(), p_o.normal()), objects, obj).d   
        if p_o.len() == 0:
            return self.color
        if d != -1 and d < p_o.len():
            return Vector(0, 0, 0)
        else:
            refl = obj.reflective
            intensity = self.distance_coef / (12.5 * p_o.len() ** (2 - refl / 5))
            power = max(normal.dot((p_o).normal() * intensity), AMBIENT)
            if power != AMBIENT:
                power = power + refl * normal.dot((p_o).normal()) ** (100 * refl)
            return self.color * power


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


def test_ray(ray, objects, to_ignore=None):
    intersect = Intersection(Vector(0, 0, 0), -1, Vector(0, 0, 0), None)
    for obj in objects:
        if obj is to_ignore:
            continue
        cur = obj.intersect(ray)
        if cur.d > 0 and intersect.d < 0:
            intersect = cur
        elif 0 < cur.d and cur.d < intersect.d:
            intersect = cur
    return intersect


def get_color(color):
    return tuple(map(lambda x: min(255, int(x * 255)), color))


def trace(ray, objects, lights, depth=1):
    if not depth:
        return (AMBIENT, AMBIENT, AMBIENT)
    intersection = test_ray(ray, objects)
    if intersection.d == -1:
        return (AMBIENT, AMBIENT, AMBIENT)
    else:
        obj = intersection.obj
        color = obj.color
        
        light_effect = Vector(0, 0, 0)
        for light in lights:
            light_effect += light.calculate_effect(intersection.p, intersection.n, obj, objects)
        color = color * light_effect
        
        if depth and obj.reflective:
            refvec = (ray.d - intersection.n * 2 * ray.d.dot(intersection.n)).normal()
            refray = Ray(intersection.p + refvec * 0.0001, refvec) # bios to prevent ray hitting itselfs origin
            refcolor = trace(refray, objects, lights, depth - 1)
            refcolor = Vector(refcolor[0], refcolor[1], refcolor[2])
            color = color + refcolor * intersection.obj.reflective
        if depth and obj.refractive:
            normal = intersection.n
            cosi = min(1, max(-1, ray.d.dot(normal)))
            
            etai = 1
            etat = obj.refractive
            if cosi < 0:
                cosi *= -1
            else:
                normal = normal * -1
                etai, etat = etat, etai
            eta = etai / etat
            k = -1 - eta * eta * (1 - cosi * cosi)
            k *= -1
            if k < 0:
                pass
            else:
                refvec = ray.d * eta + normal * (eta * cosi - sqrt(k))
                refray = Ray(intersection.p + refvec * 0.0001, refvec) # bios to prevent ray hitting itselfs origin
                refcolor = trace(refray, objects, lights, depth - 1)
                refcolor = Vector(refcolor[0], refcolor[1], refcolor[2])
                color = color + refcolor * obj.refractive
                
                        
    return (color.x, color.y, color.z)


def render_image(camera, objects, lights, depth, verbose=1):
    img = Image.new('RGB', (camera.res_x, camera.res_y))
    
    for y in range(camera.res_y):
        if verbose:
            if y % (camera.res_y // (10)) == 0:
                print(y / (camera.res_y))
        for x in range(camera.res_x):
            ray = camera.get_ray(y, x)
            color = trace(ray, objects, lights, depth)
            img.putpixel((x, y), get_color(color))
    
    if verbose:
        print('1.0')
    return img


def main():
    frame_count = 1
    screen_distance = 50
    width = screen_distance
    height = screen_distance
    depth = 5
    
    resolution_coef = 4
    min_frame_width = 500
    min_frame_height = 500
    
    to_show = True
    verbose = 1
    
    render_start_time = time()
    
    for frame_index in range(0, frame_count):
        if verbose:
            frame_start_time = time()
            print('Frame_{} started'.format(frame_index + 1))

        res_x = width * resolution_coef
        res_y = height * resolution_coef
        camera = Camera(Vector(0, 0, 0), Vector(screen_distance, 0, 0), width, height, res_x, res_y)
        
        m = screen_distance
        
        objects = []
        objects.append(Sphere(Vector(m + 2 * m - 14, m / 2 - 8, -4), m/3, Vector(0.3, 0.6, 0.6), 0, 1.3)) # blue sphere
        objects.append(Sphere(Vector(m + 2 * m, m / 2, 0), m / 2, Vector(1, 0, 0), 0.05)) # red sphere
        objects.append(Sphere(Vector(m + 2 * m, - m / 2, -m / 4), m / 4, Vector(0, 0, 0), 1)) # orange-mirror sphere
        objects.append(Sphere(Vector(m + 2 * m, 0.2 * m, m), m / 3, Vector(0, 1, 0), 0.1)) # green sphere
        objects.append(Plane(Vector(0, - m / 2 - m / 4, 0), Vector(0, 1, 0), Vector(1, 0, 0), 0.8))
        objects.append(Plane(Vector(4 * m + m / 3, 0, 0), Vector(-1, 0, 0), Vector(0, 1, 1), 0))
        objects.append(Plane(Vector(0, m / 2 + m / 3 + 20, 0), Vector(0, -1, 0), Vector(1, 1, 1), 0))
        
        lights = []
        lights.append(Light(Vector(20, -5, - m - 15), Vector(0.9, 0.17, 0.17)))
        lights.append(Light(Vector(20, 10, + m + 15), Vector(0.17, 0.55, 0.9)))
    
        frame = render_image(camera, objects, lights, depth, verbose)
        if res_x < min_frame_width or res_y < min_frame_height:
            frame = frame.resize((min_frame_width, min_frame_height), Image.NEAREST)
        
        if to_show:
            frame.show()
        if verbose:
            frame_finish_time = time()
            print('Frame_{} finished in {:.2f}'.format(frame_index, frame_finish_time - frame_start_time))
        frame.save('frame{}.png'.format(frame_index))

    if verbose:
        render_finish_time = time()
        print('Render finished in {:.2f}'.format(render_finish_time - render_start_time))


if __name__ == '__main__':
    main()