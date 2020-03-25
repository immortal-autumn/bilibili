#!/usr/bin/python3
import sys



def debug(**kwargs):
    import IPython
    IPython.embed(user_ns=sys._getframe(1).f_locals, colors='Linux', **kwargs)
