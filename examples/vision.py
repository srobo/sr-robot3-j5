"""Example code for vision."""
from sr.robot3 import Robot
from sr.robot3.env import CONSOLE_ENVIRONMENT_WITH_VISION

R = Robot(env=CONSOLE_ENVIRONMENT_WITH_VISION, auto_start=False)

if __name__ == '__main__':
    while True:
        markers = R.camera.see()
        print(f"I found {len(markers)} markers.")
        for m in markers:
            print(f"\tID: {m.id}")
            print(f"\t\tDistance: {m.distance}")
