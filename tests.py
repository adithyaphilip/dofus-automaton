import image_utils
import names
import adb_utils
import math_utils

import cv2

import time
import subprocess
import sys
import random

import driver
import interaction_utils

IS_LIVE_TEST = False


def draw_open_rects(rects, cv_img, op_fname: str, divide_by: float):
    if rects is None:
        print("No rectangles to draw! Returning!", file=sys.stderr)
        return
    for rect in rects:
        cv2.rectangle(cv_img,
                      (rect[0] // divide_by, rect[1] // divide_by),
                      (int(rect[2] // divide_by), int(rect[3] // divide_by)),
                      (0, 0, 255),
                      2)
    cv2.imwrite(op_fname, cv_img)
    subprocess.call("open " + op_fname, shell=True)


def test_in_range(fname: str):
    color_img = image_utils.read_image(fname=fname, color=True)
    draw_open_rects(rects=image_utils.get_spell_in_range_rects(color_img), cv_img=color_img, divide_by=1,
                    op_fname="in_range.png")


def test_spell_range_empty_squares(fname: str):
    color_img = image_utils.read_image(fname=fname, color=True)
    rects = image_utils.get_spell_range_empty_squares(color_img)
    draw_open_rects(rects=rects, cv_img=color_img, divide_by=1,
                    op_fname="test_op/spell_range_empty.png")
    min_click_point = math_utils.get_min_avg_dist_pt([math_utils.get_rand_click_point(rect) for rect in rects])

    draw_open_rects(rects=[(min_click_point[0], min_click_point[1], min_click_point[0]+50, min_click_point[1] + 50)],
                    cv_img=color_img, divide_by=1, op_fname="test_op/spell_range_empty_chosen.png")


def test_movement(fname: str):
    color_img = image_utils.read_image(fname=fname, color=True)
    draw_open_rects(cv_img=color_img, rects=image_utils.get_battle_movement_squares(color_img),
                    op_fname="move_test.png", divide_by=1)


def test_battle_live():
    # interaction_utils.click_ready(wait=True)
    t_battle_check = time.time()
    while image_utils.get_battle_info() is not None:
        print("Battle check:", time.time() - t_battle_check)
        # keep testing to see if it is your turn
        # if not your turn, try again later
        # NOTE: This rect can only be re-sued if we are not moving the avatar box
        end_turn_rect = image_utils.get_end_turn_if_is_turn()
        # if not your turn, try again
        if end_turn_rect is None:
            continue

        # if you've reached here, it's your turn. Start firing
        sc_img_black = image_utils.fetch_screenshot(height=image_utils.READ_HEIGHT, width=image_utils.READ_WIDTH,
                                                    color=False, temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)
        spell_rect = image_utils.get_spell_coins()
        chosen_rect = None
        while spell_rect is not None:
            adb_utils.tap(*math_utils.get_rand_click_point(image_utils.get_empty_box_pos(cv_img_black=sc_img_black,
                                                                                         many=False)))
            adb_utils.tap(*math_utils.get_rand_click_point(spell_rect))
            # wait for the range to appear
            time.sleep(1)
            rects = image_utils.get_spell_in_range_rects()
            # if no one is in range, pass your turn
            if rects is None:
                print("Nowhere to click :(")
                break
            # reaching here means some guys are in range
            # if the guy we chose last time in the same turn is not in range anymore,
            # or we're picking for the first time this turn (will be None, causing the "not in" check to succeed),
            # randomly choose a new guy.
            # else, stick to the same guy
            if chosen_rect not in rects:
                chosen_rect = random.choice(rects)

            adb_utils.tap(*math_utils.get_rand_click_point(chosen_rect))
            adb_utils.tap(*math_utils.get_rand_click_point(chosen_rect))

            # wait for the spell to be cast
            time.sleep(1)

            spell_rect = image_utils.get_spell_coins()

        # End your turn. It is important to refetch. Death of enemy can change position. Also the wait is to ensure
        # we don't accidentally click when the fight has ended
        time.sleep(2)
        end_turn_rect = image_utils.get_end_turn_if_is_turn()
        if end_turn_rect is not None:
            adb_utils.tap(*math_utils.get_rand_click_point(end_turn_rect))
    interaction_utils.close_diag(wait=True)


def test_main_driver_live():
    test_battle_live()


def test_cast_spell_live():
    spell_rect = image_utils.get_spell_coins()
    adb_utils.tap(*math_utils.get_rand_click_point(spell_rect))
    time.sleep(1)
    rects = image_utils.get_spell_in_range_rects()
    if rects is None:
        print("Nowhere to click :(")
    else:
        print("Detected", len(rects), "enemies in range!")
        chosen = random.choice(rects)
        adb_utils.tap(*math_utils.get_rand_click_point(chosen))
        adb_utils.tap(*math_utils.get_rand_click_point(chosen))


def test_empty_box(main_img_fname: str):
    color_img = cv2.imread(main_img_fname)
    cv_img = image_utils.read_image(main_img_fname)

    t1 = time.time()
    rects = image_utils.get_empty_box_pos(cv_img_black=cv_img, many=True)
    if rects is None:
        print("ERROR: Detected 0 empty boxes!", file=sys.stderr)
        return

    print("Detected objects:", len(rects), time.time() - t1)
    draw_open_rects(rects=rects, cv_img=color_img, op_fname="res_box.png", divide_by=2)


def test_tofu_detect(main_img_fname: str):
    color_img = cv2.imread(main_img_fname)
    # cv_img = image_utils.read_image(main_img_fname)
    cv_img = color_img

    t1 = time.time()
    rects = image_utils.get_monster_pos(cv_img=cv_img, monster_name=names.get_monster_name(names.MONSTER_TOFU_INDEX),
                                        threshold=image_utils.THRESH_TOFU_POS)

    if rects is None:
        print("WARNING: Detected no tofus! :(", file=sys.stderr)
        return

    print("Detected objects:", len(rects), time.time() - t1)
    draw_open_rects(rects=rects, cv_img=color_img, op_fname="res_tofu.png", divide_by=1)


def test_attack_diag_detect(main_img_fname):
    color_img = cv2.imread(main_img_fname)
    cv_img = image_utils.read_image(main_img_fname)

    t1 = time.time()
    res = image_utils.get_attack_diag_info(cv_img=cv_img)

    if res is None:
        print("No attack dialog detected!", file=sys.stderr)
        return

    print("Detected objects:", res, time.time() - t1)
    draw_open_rects(rects=res[1:], cv_img=color_img, op_fname="res_att_diag.png", divide_by=2)


def test_battle_avatar_detect(img_fname: str):
    color_img = image_utils.read_image(img_fname, color=True)
    avatar_tuples = image_utils.get_battle_info(color_img)
    if avatar_tuples is None:
        print("ERROR: Not a battle!", file=sys.stderr)
        return
    for item, index in zip(avatar_tuples, range(len(avatar_tuples))):
        print(item[0], index)
    draw_open_rects(rects=[item[1] for item in avatar_tuples], cv_img=color_img, op_fname="res_battle.png",
                    divide_by=1)


def test_health_full(img_fname: str):
    color_img = image_utils.read_image(img_fname, color=True)
    health_full = image_utils.get_health_full_rect(cv_img=color_img)
    if health_full is None:
        print("Health not full!", file=sys.stderr)
        return
    draw_open_rects(rects=[health_full], cv_img=color_img, op_fname="res_health.png", divide_by=1)


def test_end_turn_detect(img_fname: str):
    color_img = image_utils.read_image(img_fname, color=True)
    end_turn_rect = image_utils.get_end_turn_if_is_turn(cv_img=color_img)
    if end_turn_rect is None:
        print("Not your turn!", file=sys.stderr)
        return
    draw_open_rects(rects=[end_turn_rect], cv_img=color_img, op_fname="res_battle.png", divide_by=1)


def main():
    if IS_LIVE_TEST:
        # image_utils.fetch_screenshot(image_utils.ORIG_HEIGHT, image_utils.ORIG_WIDTH,
        #                              names.LARGE_TEMP_SCREENSHOT_FNAME, color=True)
        # test_tofu_detect(names.LARGE_TEMP_SCREENSHOT_FNAME)

        # image_utils.fetch_screenshot(image_utils.READ_HEIGHT, image_utils.READ_WIDTH,
        #                              names.TEMP_SCREENSHOT_FNAME, color=False)
        # test_attack_diag_detect(names.TEMP_SCREENSHOT_FNAME)
        # test_empty_box(names.TEMP_SCREENSHOT_FNAME)
        test_battle_live()
    else:
        normal_image = "test_files/normal_screen_med.png"
        normal_image_lg = "test_files/screen.png"
        att_diag_image = "test_files/attack_dialog_med.png"
        battle_range_img = "test_files/battle_screen_2_attack_range.png"
        movement_img = "test_files/movement.png"
        # test_tofu_detect(normal_image_lg)
        # test_empty_box(normal_image)
        # test_attack_diag_detect(normal_image)
        # test_attack_diag_detect(att_diag_image)

        # battle_image_fnames = ["test_files/battle_screen.png", "test_files/battle_screen_2_attack_range.png",
        #                        "test_files/battle_screen_blue_larv.png", "test_files/battle_screen_mosq.png",
        #                        "test_files/battle_screen_larvae.png"]

        # neg_battle_img_fnames = ["test_files/screen.png"]
        # for fname in neg_battle_img_fnames:
        #     test_battle_avatar_detect(fname)
        #     time.sleep(5)

        # test_end_turn_detect(img_fname="test_files/battle_screen_2_attack_range.png")
        # test_end_turn_detect(img_fname=normal_image_lg)
        # test_movement(fname=movement_img)
        # test_in_range(battle_range_img)
        test_spell_range_empty_squares(battle_range_img)


if __name__ == '__main__':
    main()
