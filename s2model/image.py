# (c) 2023-2026 DRX Dev Team

import os
import struct

import bpy

from s2model import sr_io
from s2model import pytxcdxtn

S3TC_DXT1 = 0x83F0
S3TC_DXT1A = 0x83F1
S3TC_DXT3 = 0x83F2
S3TC_DXT5 = 0x83F3

def toBlender(fname):
	img = None
	with open(fname, "rb") as file:
		data = file.read()
		filehead = data[0:19]
		width = sr_io.endianint(filehead[11:15])
		height = sr_io.endianint(filehead[15:])
		bmptype = sr_io.endianint(data[19:23])
		translucent = (data[23] == 1)
		sz = sr_io.endianint(data[25:29])
		bytedata = data[29:30+sz]
		pixels = []
		
		name = os.path.basename(fname)
		img = bpy.data.images.new(name, width, height, alpha=translucent)
	
		if bmptype == S3TC_DXT1:
			pixels = pytxcdxtn.load_dxt1f(bytedata, width, height)
		elif bmptype == S3TC_DXT1A:
			pixels = pytxcdxtn.load_dxt1af(bytedata, width, height)
		elif bmptype == S3TC_DXT3:
			pixels = pytxcdxtn.load_dxt3f(bytedata, width, height)
		elif bmptype == S3TC_DXT5:
			pixels = pytxcdxtn.load_dxt5f(bytedata, width, height)
		try:
			l = memoryview(pixels).cast('f')
			img.pixels = l
			with bpy.context.temp_override(edit_image=img):
				bpy.ops.image.flip(use_flip_y=True)
			img.update()
		except ValueError:
			pass
	return img