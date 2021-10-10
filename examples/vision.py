from sr.robot3 import Robot
from sr.robot3.env import VISION_ONLY_ENVIRONMENT

R = Robot(env=VISION_ONLY_ENVIRONMENT, auto_start=False)

if __name__ == '__main__':
    while True:
        markers = R.camera.see()
        print(f"I found {len(markers)} markers.")
        for m in markers:
            print(f"\tID: {m.id}")
            print(f"\t\tDistance: {m.distance}")
            # print(f"\t\t{m.as_dict()}")
