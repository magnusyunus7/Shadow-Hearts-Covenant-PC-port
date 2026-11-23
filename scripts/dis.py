import sys,struct,rabbitizer as rz
R=rz.InstrCategory.R5900
d=open(sys.argv[1],'rb').read(); OFF,VA=0x100,0x200000
a=int(sys.argv[2],16); n=int(sys.argv[3])
for k in range(n):
    x=rz.Instruction(struct.unpack_from('<I',d,a-VA+OFF+k*4)[0],a+k*4,R)
    print("%08x  %s"%(a+k*4,x.disassemble()))
