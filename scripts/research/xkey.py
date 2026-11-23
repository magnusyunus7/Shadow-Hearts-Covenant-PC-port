import sys
from Xlib import X, XK, display
from Xlib.ext import xtest
d=display.Display(sys.argv[1]); key=d.keysym_to_keycode(XK.string_to_keysym(sys.argv[2]))
xtest.fake_input(d, X.KeyPress, key); d.sync(); xtest.fake_input(d, X.KeyRelease, key); d.sync()
