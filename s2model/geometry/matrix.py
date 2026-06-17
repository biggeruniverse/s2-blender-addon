# (c) 2011 savagerebirth.com
# (c) 2023-2026 DRX Dev Team

# so we don't actually need most of this but it's here anyway...

import math
from .vectors import Vec3

class matrix43_t:
    def __init__(self):
        self.pos = Vec3(0, 0, 0)
        self.axis = [Vec3(1, 0, 0), Vec3(0, 1, 0), Vec3(0, 0, 1)]

    def copyFrom(self, other):
        for i in range(3):
            self.pos.data[i] = other.pos.data[i]
            for j in range(3):
                self.axis[i].data[j] = other.axis[i].data[j]

    def determinant(self):
        d = 0.0
        d  = self.axis[0][0] * self.axis[1][1] * self.axis[2][2]
        d += self.axis[0][1] * self.axis[1][2] * self.axis[2][0]
        d += self.axis[0][2] * self.axis[1][0] * self.axis[2][1]

        d -= self.axis[0][2] * self.axis[1][1] * self.axis[2][0]
        d -= self.axis[0][1] * self.axis[1][0] * self.axis[2][2]
        d -= self.axis[0][0] * self.axis[1][2] * self.axis[2][1]

        return d

    def invert(self):
        m = matrix43_t()

        det = self.determinant()

        if abs(det) < 0.00001:
            m.copyFrom(self)
            return m
        det = 1 / det

        m.axis[0][0] = self.axis[1][1] * self.axis[2][2] - self.axis[1][2] * self.axis[2][1]
        m.axis[0][1] = self.axis[0][2] * self.axis[2][1] - self.axis[0][1] * self.axis[2][2]
        m.axis[0][2] = self.axis[0][1] * self.axis[1][2] - self.axis[0][2] * self.axis[1][1]

        m.axis[1][0] = self.axis[1][2] * self.axis[2][0] - self.axis[1][0] * self.axis[2][2]
        m.axis[1][1] = self.axis[0][0] * self.axis[2][2] - self.axis[0][2] * self.axis[2][0]
        m.axis[1][2] = self.axis[0][2] * self.axis[1][0] - self.axis[0][0] * self.axis[1][2]

        m.axis[2][0] = self.axis[1][0] * self.axis[2][1] - self.axis[1][1] * self.axis[2][0]
        m.axis[2][1] = self.axis[0][1] * self.axis[2][0] - self.axis[0][0] * self.axis[2][1]
        m.axis[2][2] = self.axis[0][0] * self.axis[1][1] - self.axis[0][1] * self.axis[1][0]

        m.axis[0] = m.axis[0] * det
        m.axis[1] = m.axis[1] * det
        m.axis[2] = m.axis[2] * det

        m.pos = -translateFromMatrix(m, self.pos)

        return m

    def transpose(self):
        m = matrix43_t()

        m.axis[0][0] = self.axis[0][0]
        m.axis[0][1] = self.axis[1][0]
        m.axis[0][2] = self.axis[2][0]

        m.axis[1][0] = self.axis[0][1]
        m.axis[1][1] = self.axis[1][1]
        m.axis[1][2] = self.axis[2][1]

        m.axis[2][0] = self.axis[0][2]
        m.axis[2][1] = self.axis[1][2]
        m.axis[2][2] = self.axis[2][2]

        m.pos = self.pos

        return m

    def __inv__(self):
        return self.invert()

    def __str__(self):
        return "[" + str(self.axis[0]) + "\n "+ str(self.axis[1]) +"\n "+str(self.axis[2])+"\n"+str(self.pos)+", 1.0]"


def DEG2RAD(x):
    return (x * math.pi) / 180.0

def RAD2DEG(x):
    return (x * 180.0) / math.pi

def fromBlenderMatrix(mat):
    tmp = matrix43_t()
    for i in range(3):
        for j in range(3):
            tmp.axis[i].data[j] = mat[i][j]
    for j in range(3):
        tmp.pos.data[j] = mat[3][j]
    #tmp.axis = multiplyAxis(tmp.axis, rotateMatrix(0.0, 0.0, 180.0))
    return tmp

def multiplyAxis(a, b):
    out = [Vec3(0,0,0), Vec3(0,0,0), Vec3(0,0,0)]
    out[0].data[0] = a[0].data[0] * b[0].data[0] + a[0].data[1] * b[1].data[0] + a[0].data[2] * b[2].data[0]
    out[0].data[1] = a[0].data[0] * b[0].data[1] + a[0].data[1] * b[1].data[1] + a[0].data[2] * b[2].data[1]
    out[0].data[2] = a[0].data[0] * b[0].data[2] + a[0].data[1] * b[1].data[2] + a[0].data[2] * b[2].data[2]
    out[1].data[0] = a[1].data[0] * b[0].data[0] + a[1].data[1] * b[1].data[0] + a[1].data[2] * b[2].data[0]
    out[1].data[1] = a[1].data[0] * b[0].data[1] + a[1].data[1] * b[1].data[1] + a[1].data[2] * b[2].data[1]
    out[1].data[2] = a[1].data[0] * b[0].data[2] + a[1].data[1] * b[1].data[2] + a[1].data[2] * b[2].data[2]
    out[2].data[0] = a[2].data[0] * b[0].data[0] + a[2].data[1] * b[1].data[0] + a[2].data[2] * b[2].data[0]
    out[2].data[1] = a[2].data[0] * b[0].data[1] + a[2].data[1] * b[1].data[1] + a[2].data[2] * b[2].data[1]
    out[2].data[2] = a[2].data[0] * b[0].data[2] + a[2].data[1] * b[1].data[2] + a[2].data[2] * b[2].data[2]
    return out

def multiplyMatrix(a, b):
    out = matrix43_t()
    out.axis[0].data[0] = a.axis[0].data[0] * b.axis[0].data[0] + a.axis[1].data[0] * b.axis[0].data[1] + a.axis[2].data[0] * b.axis[0].data[2];
    out.axis[0].data[1] = a.axis[0].data[1] * b.axis[0].data[0] + a.axis[1].data[1] * b.axis[0].data[1] + a.axis[2].data[1] * b.axis[0].data[2];
    out.axis[0].data[2] = a.axis[0].data[2] * b.axis[0].data[0] + a.axis[1].data[2] * b.axis[0].data[1] + a.axis[2].data[2] * b.axis[0].data[2];
    
    out.axis[1].data[0] = a.axis[0].data[0] * b.axis[1].data[0] + a.axis[1].data[0] * b.axis[1].data[1] + a.axis[2].data[0] * b.axis[1].data[2];
    out.axis[1].data[1] = a.axis[0].data[1] * b.axis[1].data[0] + a.axis[1].data[1] * b.axis[1].data[1] + a.axis[2].data[1] * b.axis[1].data[2];
    out.axis[1].data[2] = a.axis[0].data[2] * b.axis[1].data[0] + a.axis[1].data[2] * b.axis[1].data[1] + a.axis[2].data[2] * b.axis[1].data[2];
    
    out.axis[2].data[0] = a.axis[0].data[0] * b.axis[2].data[0] + a.axis[1].data[0] * b.axis[2].data[1] + a.axis[2].data[0] * b.axis[2].data[2];
    out.axis[2].data[1] = a.axis[0].data[1] * b.axis[2].data[0] + a.axis[1].data[1] * b.axis[2].data[1] + a.axis[2].data[1] * b.axis[2].data[2];
    out.axis[2].data[2] = a.axis[0].data[2] * b.axis[2].data[0] + a.axis[1].data[2] * b.axis[2].data[1] + a.axis[2].data[2] * b.axis[2].data[2];
    
    out.pos.data[0] = a.axis[0].data[0] * b.pos.data[0] + a.axis[1].data[0] * b.pos.data[1] + a.axis[2].data[0] * b.pos.data[2] + a.pos.data[0];
    out.pos.data[1] = a.axis[0].data[1] * b.pos.data[0] + a.axis[1].data[1] * b.pos.data[1] + a.axis[2].data[1] * b.pos.data[2] + a.pos.data[1];
    out.pos.data[2] = a.axis[0].data[2] * b.pos.data[0] + a.axis[1].data[2] * b.pos.data[1] + a.axis[2].data[2] * b.pos.data[2] + a.pos.data[2];
    return out

def multiplyVector(a, v):
    out = Vec3(0,0,0)
	
    out.data[0] = a.axis[0].data[0] * v.data[0] + a.axis[1].data[0] * v.data[1] + a.axis[2].data[0] * v.data[2] + a.pos.data[0];
    out.data[1] = a.axis[0].data[1] * v.data[0] + a.axis[1].data[1] * v.data[1] + a.axis[2].data[1] * v.data[2] + a.pos.data[1];
    out.data[2] = a.axis[0].data[2] * v.data[0] + a.axis[1].data[2] * v.data[1] + a.axis[2].data[2] * v.data[2] + a.pos.data[2];
	
    return out

def rotateMatrix(pitch, roll, yaw):
    angle = DEG2RAD(pitch)
    s = math.sin(angle)
    c = math.cos(angle)
    rot_x = [
        Vec3(1, 0, 0),
    Vec3(0, c, s),
    Vec3(0, -s, c)
        ]

    angle = DEG2RAD(roll)
    s = math.sin(angle)
    c = math.cos(angle)
    rot_y = [
        Vec3(c, 0, -s),
    Vec3(0, 1, 0),
        Vec3(s, 0, c)
        ]

    angle = DEG2RAD(yaw)
    s = math.sin(angle)
    c = math.cos(angle)
    rot_z = [
        Vec3(c, s, 0),
    Vec3(-s, c, 0),
    Vec3(0, 0, 1)
        ]

    tmp = multiplyAxis(rot_y, rot_x)
    return multiplyAxis(tmp, rot_z)

def translateFromMatrix(mat, pos):
    return Vec3((pos.data[0] * mat.axis[0].data[0]) + (pos.data[1] * mat.axis[1].data[0]) + (pos.data[2] * mat.axis[2].data[0]) + mat.pos.data[0],
                            (pos.data[0] * mat.axis[0].data[1]) + (pos.data[1] * mat.axis[1].data[1]) + (pos.data[2] * mat.axis[2].data[1]) + mat.pos.data[1],
                            (pos.data[0] * mat.axis[0].data[2]) + (pos.data[1] * mat.axis[1].data[2]) + (pos.data[2] * mat.axis[2].data[2]) + mat.pos.data[2])

