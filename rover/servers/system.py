import platform

def is_raspberry_pi():
    uname = platform.uname()
    if 'raspberrypi' in uname.node:
        return True

    return False
