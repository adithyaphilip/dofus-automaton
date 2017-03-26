import cv2
import image_utils
import numpy as np
import interaction_utils

import tests


def test_movement_live():
    interaction_utils.battle_move_away_from_enemy()


def test_enemy_pos():
    cv_img = image_utils.read_image(fname="test_files/before_select.png", color=True)
    tests.draw_open_rects(cv_img=cv_img, rects=image_utils.get_battle_enemy_positions(cv_img=cv_img), divide_by=1,
                          op_fname="debug.png")


def test_diff():
    cv_img = image_utils.read_image(fname="test_files/before_select.png")
    cv_img2 = image_utils.read_image(fname="test_files/after_select_4.png")

    cv2.imwrite("diff.png", cv2.absdiff(cv_img, cv_img2))


if __name__ == '__main__':
    test_movement_live()
