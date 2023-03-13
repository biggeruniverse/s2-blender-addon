# (c) 2011 savagerebirth.com
# (c) 2023 DRX Dev Team

import struct

def endianint(s):
	return struct.unpack("<i", s)[0];

def endianfloat(s):
	return struct.unpack("<f", s)[0];

def int2str(i):
	return struct.pack("<i", i);

def float2str(f):
	return struct.pack("<f", f);

def byte2str(f):
        return struct.pack("B", f);

def writepadded(file, s, pad):
	file.write(s);
	for i in range(len(s), pad):
		file.write(struct.pack("B", 0));

class FileBlock:
    def __init__(self):
        self.name = b"null";
        self.length = 0;
        self.pos = 0;
        self.data = b'';

    def read(self, file, size):
        self.pos = file.tell();
        self.name = file.read(4).decode('utf-8');
        self.length = endianint(file.read(4)); #deadc0d3
        if self.pos + self.length > size:
            raise Exception("Invalid block!");
        self.data = file.read(self.length);
	
    def write(self, file):
        self.length = len(self.data)
        file.write(self.name);
        file.write(int2str(self.length));
        file.write(self.data)
        #TODO: this I guess
