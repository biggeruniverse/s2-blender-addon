# (c) 2011 savagerebirth.com
# (c) 2023-2026 DRX Dev Team
# Import/Export plugin for Blender

import os
import math
from .bone import Bone
from .bone import BoneMotion
from .bone import BoneMotionKey
from ..geometry.vectors import Vec3
from s2model import sr_io
from ..geometry import matrix

import bpy

def initMotionBlock(name, keytype, idx):
        block = sr_io.FileBlock()
        block.name = b'bmtn'
        name_bytes = name[:Bone.NAME_LENGTH].encode('utf-8') if isinstance(name, str) else name[:Bone.NAME_LENGTH]
        block.data += name_bytes
        block.data += bytes(b'\0' * (Bone.NAME_LENGTH-len(name_bytes)))
        block.data += sr_io.int2str(idx)
        block.data += sr_io.int2str(keytype)
        return block

def packBlockData(name, keytype, idx, data):
        block = initMotionBlock(name, keytype, idx)
        block.data += sr_io.int2str(len(data) / 4)
        block.data += data
        return block

def createScaleBlock(boneFn, idx):
        block = initMotionBlock(boneFn, BoneMotionKey.MKEY_SCALE, idx)
        block.data += sr_io.int2str(1)
        block.data += sr_io.float2str(1.0)
        return block

def createVisibilityBlock(boneFn, idx):
        block = initMotionBlock(boneFn, BoneMotionKey.MKEY_VIS, idx)
        block.data += sr_io.int2str(1)
        block.data += sr_io.byte2str(255)
        return block

def createHeaderBlock(nFrames, nMotions):
        block = sr_io.FileBlock()
        block.name = 'head'
        block.data += sr_io.int2str(1)
        block.data += sr_io.int2str(nMotions)
        block.data += sr_io.int2str(nFrames)
        return block

def motionDataToString(data):
        dat = ''
        for d in data:
            dat += sr_io.float2str(d)
        return dat

class S2Clip:
    def __init__(self):
        self.motions = []
        self.numMotions = 0
        self.numFrames = 0

    def loadFile(self, filename):
        blocks = []
        size = os.path.getsize(filename)
        file = open(filename, "rb")
        filehead = file.read(4)
        if filehead != b'CLIP':
            raise Exception("not a valid S2 clip file!")
        # chunk the file out into blocks
        while file.tell()+8 < size:
            block = sr_io.FileBlock()
            block.read(file, size)
            blocks.append(block)
        file.close()

        #clip files have far fewer block types than model
        self.handleHeaderBlock(blocks[0])

        for block in blocks[1:]:
            if block.name == "bmtn":
                self.handleBoneMotionBlock(block)
            else:
                raise Exception("Invalid block name "+block.name)

        # 'fix' the scene root
        #self.motions[0].keys[BoneMotionKey.MKEY_YAW][0].data = 180.0
        # so confused right now

    def saveFile(self, filename):
        blocks = [createHeaderBlock(self.numFrames, len(self.motions))]
        for idx in range(0, len(self.motions)):
                bmtn = self.motions[idx]
                blocks.append(packBlockData(bmtn.name, BoneMotionKey.MKEY_X, idx, motionDataToString(bmtn.keys[BoneMotionKey.MKEY_X])))
                blocks.append(packBlockData(bmtn.name, BoneMotionKey.MKEY_Y, idx, motionDataToString(bmtn.keys[BoneMotionKey.MKEY_Y])))
                blocks.append(packBlockData(bmtn.name, BoneMotionKey.MKEY_Z, idx, motionDataToString(bmtn.keys[BoneMotionKey.MKEY_Z])))
                blocks.append(packBlockData(bmtn.name, BoneMotionKey.MKEY_PITCH, idx, motionDataToString(bmtn.keys[BoneMotionKey.MKEY_PITCH])))
                blocks.append(packBlockData(bmtn.name, BoneMotionKey.MKEY_ROLL, idx, motionDataToString(bmtn.keys[BoneMotionKey.MKEY_ROLL])))
                blocks.append(packBlockData(bmtn.name, BoneMotionKey.MKEY_YAW, idx, motionDataToString(bmtn.keys[BoneMotionKey.MKEY_YAW])))
        f = open(filename, 'wb')
        f.write(b'CLIP')
        for b in blocks:
                b.write(f)
        f.close()

    def handleHeaderBlock(self, block):
        if block.name != "head":
            raise Exception("Not a valid clip file!")
        
        ver = sr_io.endianint(block.data[0:4])
        if ver > 1:
            raise Exception("Bad version "+str(ver))

        self.numMotions = sr_io.endianint(block.data[4:8])
        self.numFrames = sr_io.endianint(block.data[8:12])
        for i in range(self.numMotions):
            self.motions.append(BoneMotion())
        
    def handleBoneMotionBlock(self, block):
        offset = 0
        name = block.data[offset:offset+Bone.NAME_LENGTH].decode('utf-8').rstrip('\x00')
        offset += Bone.NAME_LENGTH
        
        idx = sr_io.endianint(block.data[offset:offset+4])
        offset += 4

        keyType = sr_io.endianint(block.data[offset:offset+4])
        offset += 4
        
        numKeys = sr_io.endianint(block.data[offset:offset+4])
        offset += 4

        bmtn = BoneMotion()
        bmtn.name = name
        bmtn.num_keys = numKeys

        for n in range(BoneMotionKey.MKEY_SCALE+1):
            bmtn.keys[n] = [0.0] * numKeys

        for i in range(numKeys):
            data = 0.0
            if keyType == BoneMotionKey.MKEY_X or keyType == BoneMotionKey.MKEY_Y or keyType == BoneMotionKey.MKEY_Z or keyType == BoneMotionKey.MKEY_SCALE:
                data = sr_io.endianfloat(block.data[offset:offset+4])
                offset += 4
            elif keyType == BoneMotionKey.MKEY_PITCH or keyType == BoneMotionKey.MKEY_ROLL or keyType == BoneMotionKey.MKEY_YAW:
                data = sr_io.endianfloat(block.data[offset:offset+4])
                if data < 0:
                    data += 360
                if data > 360:
                    data -= 360
                offset += 4
            elif keyType == BoneMotionKey.MKEY_VIS:
                data = block.data[offset:offset+1]
                offset += 1
            bmtn.keys[keyType][i] = data
        self.motions.append(bmtn)
