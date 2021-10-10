from sr.robot3 import Robot
from sr.robot3.env import VISION_ONLY_ENVIRONMENT

R = Robot(env=VISION_ONLY_ENVIRONMENT, auto_start=False)

if __name__ == '__main__':
    while True:
        print(R.camera.see_ids())
