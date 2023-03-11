# (c) 2011 savagerebirth.com

from ..geometry.vectors import Vec3;
import s2model.geometry.matrix as matrix

class Bone:
        NAME_LENGTH = 32
        def __init__(self):
                self.idx = -1
                self.name = 'bonesy'
                self.parent = None
                self.base = matrix.matrix43_t()
                self.localBase = matrix.matrix43_t()
                self.invBase = matrix.matrix43_t()
                self.children = []

        def add(self, bone):
                self.children.append(bone);

class BoneMotionKey:
        MKEY_X = 0;
        MKEY_Y = 1;
        MKEY_Z = 2;
        MKEY_PITCH = 3;
        MKEY_ROLL = 4;
        MKEY_YAW = 5;
        MKEY_VIS = 6;
        MKEY_SCALE = 7;

        def __init__(self):
                self.type = -1;
                self.data = None;

class BoneMotion:
        def __init__(self):
                self.name = "bmtn"
                self.keys = []
                for i in range(BoneMotionKey.MKEY_SCALE+1):
                        self.keys.append([])
