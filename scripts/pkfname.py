# Name decoder reimplemented from SLUS_210.41 func_0022A360
ALPHA=".0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_"
def decode(b8):
    v1=int.from_bytes(b8[0:4],'big'); v0=int.from_bytes(b8[4:8],'big')
    hi=v1>>16
    A=[v1&0xffff, v0>>16, v0&0xffff]
    B=[hi%40,(hi//40)%40,(hi//1600)%40]
    out=''
    for k in range(3):
        t=(B[k]<<16)|A[k]
        for div in (1,40,1600,64000):
            c=(t//div)%40
            out+=ALPHA[c-1] if c else '\0'
    return out.split('\0')[0] if False else out.replace('\0','')
if __name__=='__main__':
    import sys,struct
    d=open(sys.argv[1],'rb').read()
    for i in range(int(sys.argv[2]) if len(sys.argv)>2 else 40):
        e=d[16+i*16:32+i*16]; w2,w3=struct.unpack_from('<II',e,8)
        print(i,repr(decode(e[:8])),hex(w2),hex(w3))
