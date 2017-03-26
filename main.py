import image_utils
import names
import cv2
import subprocess
import time


def main():
    t1 = time.time()
    cv_img = image_utils.fetch_screenshot(image_utils.READ_HEIGHT, image_utils.READ_WIDTH, names.TEMP_SCREENSHOT_FNAME)
    color_img = cv2.imread(names.TEMP_SCREENSHOT_FNAME)
    rects = image_utils.get_monster_pos(cv_img=cv_img, monster_name=names.get_monster_name(names.MONSTER_TOFU_INDEX),
                                        threshold=image_utils.THRESH_TOFU_POS)
    print("Detected objects:", len(rects), time.time() - t1)
    for rect in rects:
        cv2.rectangle(color_img,
                      (int(rect[0] // image_utils.SCALE_FACTOR), int(rect[1] // image_utils.SCALE_FACTOR)),
                      (int(rect[2] // image_utils.SCALE_FACTOR), int(rect[3] // image_utils.SCALE_FACTOR)),
                      (0, 0, 255),
                      2)
    cv2.imwrite('res.png', color_img)
    subprocess.call("open res.png", shell=True)


if __name__ == '__main__':
    while True:
        main()
        time.sleep(1)
