"""Bake view-space depth at authoring time; playback animates transform/opacity only."""
from math import sin,cos,pi

def projected(xyz, front=False):
    if front:return xyz
    x,y,z=xyz
    yaw=-17*pi/180; pitch=-17*pi/180
    x,z=x*cos(yaw)+z*sin(yaw),-x*sin(yaw)+z*cos(yaw)
    y,z=y*cos(pitch)-z*sin(pitch),y*sin(pitch)+z*cos(pitch)
    return x,y,z

def sample_depth(z):
    near=max(0,min(1,(z+230)/460))
    return .38+1.72*near,.10+.90*near
