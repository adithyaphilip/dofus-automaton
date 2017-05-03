import names
import math_utils
import adb_utils

import cv2
import numpy as np

import subprocess
import sys
import math
import random
import time

ORIG_HEIGHT = 900
ORIG_WIDTH = 1440

READ_HEIGHT = 450
READ_WIDTH = 720

# the aspect ratio must be maintained. Using old_width/new_width instead of old_width/old_height to mitigate potential
# floating point equality issues (as the old and new are expected to be integral multiple of each other)
assert ORIG_WIDTH / READ_WIDTH == ORIG_HEIGHT / READ_HEIGHT

THRESH_EMPTY_BOX = 0.8
THRESH_CLOSE_DIAG_BTN = 0.9
THRESH_HEALTH_FULL = 0.9
THRESH_ZAAP = 0.9

THRESH_ATTACK_DIAG_PLUS = 0.7
THRESH_ATTACK_DIAG_ATT = 0.6
THRESH_ATTACK_DIAG_CANCEL = 0.6

THRESH_TOFU_POS = 0.83

THRESH_BATTLE_AVATAR = 0.6
THRESH_BATTLE_END_TURN = 0.9
THRESH_BATTLE_READY = 0.9
THRESH_BATTLE_SPELL_COINS = 0.9  # because of the red dot that appears in the emulator
THRESH_BATTLE_SPELL_LIVING_BAG = 0.9  # because of the red dot that appears in the emulator
THRESH_BATTLE_IN_RANGE_2 = 0.6
THRESH_BATTLE_IN_RANGE_3 = 0.8
THRESH_BATTLE_IN_RANGE_RIGHT = 0.55
THRESH_BATTLE_SPELL_RANGE_SQ = 0.8
THRESH_BATTLE_ENEMY_POS = 0.8
THRESH_BATTLE_OWN_POS = 0.75
THRESH_BATTLE_AVATAR_PLUS = 0.5
THRESH_BATTLE_MOVE_SQUARE = 0.8


# TODO: ADD THRESH FOR IN_RANGE_4

def read_image(fname, color: bool = False):
    """
    to ensure all images are read the same way e.g. black and white
    :param color: whether the image read should be in color or black and white
    :param fname: the file to load the image from
    :return: an opencv image object (which is a numpy multi-array)
    """
    img = cv2.imread(fname) if color else cv2.imread(fname, 0)
    if img is None:
        raise Exception("Failed to read image from file at " + fname)
    return img


def get_filtered_image(cv_img, bgr_lower, bgr_upper):
    bound_lower = np.array(bgr_lower, dtype=np.uint8)
    bound_upper = np.array(bgr_upper, dtype=np.uint8)
    mask = cv2.inRange(cv_img, bound_lower, bound_upper)
    cv_masked_img = cv2.bitwise_and(cv_img, cv_img, mask=mask)

    return cv_masked_img


monster_image_dict = {}

empty_box_img = read_image(names.EMPTY_BOX_FNAME)
close_diag_btn_img = read_image(names.CLOSE_DIAG_BTN_FNAME, color=True)
health_full_img = read_image(names.HEALTH_FULL_FNAME, color=True)
zaap_img = read_image(names.ZAAP_IMG_FNAME, color=True)

attack_diag_att_img = read_image(names.ATTACK_DIAG_ATTACK_FNAME)
attack_diag_cancel_img = read_image(names.ATTACK_DIAG_CANCEL_FNAME)
attack_diag_plus_img = read_image(names.ATTACK_DIAG_PLUS_FNAME)

battle_end_turn_img = read_image(fname=names.BATTLE_END_TURN_FNAME, color=True)
battle_ready_img = read_image(fname=names.BATTLE_READY_FNAME, color=True)
battle_spell_coins_img = read_image(fname=names.BATTLE_SPELL_COINS_ENABLED_FNAME, color=True)
battle_spell_living_bag_img = read_image(fname=names.BATTLE_SPELL_LIVING_BAG_FNAME, color=True)
battle_in_range_sig_2_img = read_image(fname=names.BATTLE_IN_RANGE_SIG_2_FNAME, color=True)
battle_in_range_sig_3_img = read_image(fname=names.BATTLE_IN_RANGE_SIG_3_FNAME, color=True)
battle_in_range_sig_4_img = read_image(fname=names.BATTLE_IN_RANGE_SIG_4_FNAME, color=True)
battle_in_range_sig_right_img = read_image(fname=names.BATTLE_IN_RANGE_SIG_RIGHT_FNAME, color=True)
battle_spell_range_sq_sig = read_image(fname=names.BATTLE_SPELL_RANGE_SQ_SIG_FNAME, color=True)
battle_enemy_pos_sig_img = read_image(fname=names.BATTLE_ENEMY_POS_SIG_FNAME, color=True)
battle_avatar_plus_img = read_image(fname=names.BATTLE_AVATAR_PLUS_FNAME, color=True)
battle_move_sig = read_image(fname=names.BATTLE_MOVE_SQUARE_FNAME, color=True)

battle_avatar_image_dict = {name: read_image(fname=fname, color=True)
                            for name, fname in names.BATTLE_AVATAR_FNAME_DICT.items()}


def fetch_screenshot(height: int, width: int, temp_fname: str, color: bool):
    cmd = adb_utils.get_base_cmd_exec() + " screencap -p  2> /dev/null > %s" % temp_fname
    while True:
        try:
            if subprocess.call(cmd, shell=True, timeout=adb_utils.ADB_TIMEOUT_SECONDS) == 0:
                break
        except Exception:
            print("ADB TIMED OUT!!!! :O :O :O at", time.time(), "- trying again!", file=sys.stderr)
    subprocess.call("sips -z %d %d %s" % (height, width, temp_fname), shell=True)
    return read_image(temp_fname, color=color)


def get_template_match(main_cv_img, template_cv_image, threshold: float, scale: bool, many: bool, default=None):
    """

    :param default: what is returned if there is no match found
    :param main_cv_img:
    :param template_cv_image:
    :param threshold:
    :param scale: if True will scale the returned co-ords to corresponding points on the ORIG_HEIGHT and WIDTH image.
    This scale is calculated by comparing main_cv_image's height to ORIG_HEIGHT. It is assumed that aspect ratio was
    maintained
    :param many:
    :return:
    """
    if main_cv_img is None:
        raise Exception("Got None for main image")
    if template_cv_image is None:
        raise Exception("Got None for template image")

    scale_factor = ORIG_HEIGHT / main_cv_img.shape[0] if scale else 1

    rects = []
    w, h = template_cv_image.shape[1], template_cv_image.shape[0]

    res = cv2.matchTemplate(main_cv_img, template_cv_image, cv2.TM_CCOEFF_NORMED)

    if many:
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            rects.append(tuple([int(scale_factor * val) for val in (pt[0], pt[1], pt[0] + w, pt[1] + h)]))
    else:
        flat_index = np.argmax(res)
        resolved_index = np.unravel_index(flat_index, res.shape)[::-1]  # as we want x value first, then y value
        if res[resolved_index[1], resolved_index[0]] < threshold:
            return default
        return tuple(map(
            lambda x: int(scale_factor * x),
            (resolved_index[0], resolved_index[1], resolved_index[0] + w, resolved_index[1] + h)
        ))

    if len(rects) == 0:
        return default

    return math_utils.deduplicate_rects(rects)


def get_monster_pos(cv_img, monster_name: str, threshold: float):
    """
    detects all occurrences of the given monster in the given image (hopefully)
    :param cv_img: the image read in by opencv, of the main image to search in
    :param monster_name: the name of the monster to search for
    :param threshold: the minimum threshold used to determine if a region matches the monster template
    :return: a list of 4-tuples, where each tuple represents the position of the monster as (x1, y1, x2, y2) of the
    top left and bottom left corners respectively.
    """
    all_rects = []
    for template in monster_image_dict[monster_name]:
        template_rects = get_template_match(main_cv_img=cv_img, template_cv_image=template, threshold=threshold,
                                            scale=True, many=True)
        if template_rects is None:
            continue

        all_rects.extend(template_rects)
    # WE NEED TO DEDUPLICATE HERE TOO, as two templates may match the same tofu due to their small nature
    all_rects = math_utils.deduplicate_rects(all_rects)
    return None if len(all_rects) == 0 else all_rects


def get_attack_diag_info(cv_img):
    """
    detects an attack dialog if present and returns information like number of monsters in the box, rects for attack
    and cancel buttons
    :param cv_img: the main image to search in (cv image)
    :return: a tuple consisting of the number of monsters in the box, along with the rectangle for the attack,
    and the rectangle for cancel, None if no attack box is present
    """
    plus_rect = get_template_match(main_cv_img=cv_img,
                                   template_cv_image=attack_diag_plus_img,
                                   threshold=THRESH_ATTACK_DIAG_PLUS,
                                   scale=True,
                                   many=False)
    attack_rect = get_template_match(main_cv_img=cv_img,
                                     template_cv_image=attack_diag_att_img,
                                     threshold=THRESH_ATTACK_DIAG_PLUS,
                                     scale=True,
                                     many=False)
    cancel_rect = get_template_match(main_cv_img=cv_img,
                                     template_cv_image=attack_diag_cancel_img,
                                     threshold=THRESH_ATTACK_DIAG_PLUS,
                                     scale=True,
                                     many=False)

    if plus_rect is None or attack_rect is None or cancel_rect is None:
        print("Failed to detect attack because plus/attack/cancel was None:",
              plus_rect, attack_rect, cancel_rect, file=sys.stderr)
        return None

    # calculated by number of times the plus fits into the distance between top of attack and bottom of plus
    # 1 is subtracted to account for the gap between bottom of plus and start of first monster name
    # ceil because the plus is slightly larger than the text for each monster name
    plus_height = (plus_rect[3] - plus_rect[1])
    monster_number = math.floor((attack_rect[1] - plus_rect[3] - plus_height) / plus_height) + 2

    return monster_number, attack_rect, cancel_rect


def get_empty_box_pos(cv_img_black=None, many: bool = False):
    if cv_img_black is None:
        cv_img_black = fetch_screenshot(height=READ_HEIGHT, width=READ_WIDTH, color=False,
                                        temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)

    empty_box_rects = get_template_match(main_cv_img=cv_img_black,
                                         template_cv_image=empty_box_img,
                                         threshold=THRESH_EMPTY_BOX,
                                         scale=True,
                                         many=True)

    if empty_box_rects is None:
        return None

    return empty_box_rects if many else random.choice(empty_box_rects)


def get_battle_info(cv_img=None):
    """
    checks if there is a battle, and if there is, returns the monster list in-order as on screen.
    :return: None if no battle, else list of own and monsters' avatars' rects with keys used from names.py, sorted from
    left to right order of appearance on screen
    """
    sc_img = cv_img if cv_img is not None else fetch_screenshot(height=ORIG_HEIGHT, width=ORIG_WIDTH, color=True,
                                                                temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)
    avatar_tuples = [
        (
            monster_name,
            rect
        )
        for monster_name, monster_img in battle_avatar_image_dict.items()
        for rect in get_template_match(main_cv_img=sc_img,
                                       template_cv_image=monster_img,
                                       threshold=THRESH_BATTLE_AVATAR,
                                       many=True,
                                       scale=True,
                                       default=[])
        ]
    # sort by x-coordinate of top-left corner
    avatar_tuples.sort(key=lambda item: item[1][0])

    if names.OWN_NAME not in map(lambda t: t[0], avatar_tuples):
        return None

    return avatar_tuples


def get_end_turn_if_is_turn(cv_img=None):
    """
    None if not your turn, else returns the rect for the end turn button
    :param cv_img:
    :return:
    """
    sc_img = cv_img if cv_img is not None else fetch_screenshot(height=ORIG_HEIGHT, width=ORIG_WIDTH, color=True,
                                                                temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)

    end_turn_rect = get_template_match(main_cv_img=sc_img, template_cv_image=battle_end_turn_img,
                                       threshold=THRESH_BATTLE_END_TURN,
                                       many=False,
                                       scale=True)

    # this is to restrict the random click to click on ready even if the ready button has moved to the left e.g.
    # due to monster death
    if end_turn_rect is None:
        return None
    return end_turn_rect[0], end_turn_rect[1], end_turn_rect[0] + (end_turn_rect[2] - end_turn_rect[0]) // 2, \
           end_turn_rect[3]


def get_ready_button_if_battle(cv_img=None):
    """
    None if no ready button (not battle or battle has already started), else ready buttons's rect
    :param cv_img:
    :return:
    """
    sc_img = cv_img if cv_img is not None else fetch_screenshot(height=ORIG_HEIGHT, width=ORIG_WIDTH, color=True,
                                                                temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)

    ready_rect = get_template_match(main_cv_img=sc_img, template_cv_image=battle_ready_img,
                                    threshold=THRESH_BATTLE_READY,
                                    many=False,
                                    scale=True)

    return ready_rect


def get_spell_coins(cv_img=None):
    cv_img = cv_img if cv_img is not None else fetch_screenshot(height=ORIG_HEIGHT, width=ORIG_WIDTH, color=True,
                                                                temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)

    spell_rect = get_template_match(main_cv_img=cv_img, template_cv_image=battle_spell_coins_img,
                                    threshold=THRESH_BATTLE_SPELL_COINS, many=False, scale=True)

    return spell_rect


def get_spell_living_bag(cv_img=None):
    cv_img = cv_img if cv_img is not None else fetch_screenshot(height=ORIG_HEIGHT, width=ORIG_WIDTH, color=True,
                                                                temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)

    spell_rect = get_template_match(main_cv_img=cv_img, template_cv_image=battle_spell_living_bag_img,
                                    threshold=THRESH_BATTLE_SPELL_LIVING_BAG, many=False, scale=True)

    return spell_rect


def get_spell_range_empty_squares(cv_img=None):
    """
    attempts to return squares within an already displayed spell's range which are empty
    :return: list of empty squares in spell's range, if no such sqaures then None
    """
    cv_img = cv_img if cv_img is not None else fetch_screenshot(height=ORIG_HEIGHT, width=ORIG_WIDTH, color=True,
                                                                temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)

    bgr_blue = [178, 67, 73]
    # TODO: Is this really necessary? Picking a normal un-filtered template might also work
    cv_img_filtered = get_filtered_image(cv_img=cv_img, bgr_lower=bgr_blue, bgr_upper=bgr_blue)

    sq_rects = get_template_match(main_cv_img=cv_img_filtered, template_cv_image=battle_spell_range_sq_sig,
                                  threshold=THRESH_BATTLE_SPELL_RANGE_SQ, many=True, scale=True)

    return sq_rects


def get_spell_in_range_rects(cv_img=None):
    """
    returns None if no enemies in range, else returns the rects matching signature used, of all enemies in range
    NOTE: Does not return random click points instead of rects as the rects may be used to repeatedly cast on
    same enemy across multiple calls to this function
    :param cv_img:
    :return:
    """
    if cv_img is None:
        cv_img = fetch_screenshot(height=ORIG_HEIGHT, width=ORIG_WIDTH, color=True,
                                  temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)

    # cv2.imwrite("debug2.png", cv_img)

    # stored in the np array as BGR
    bgr_red_lower = np.array([0, 0, 150], dtype=np.uint8)
    bgr_red_upper = np.array([80, 80, 255], dtype=np.uint8)
    cv_img_red = get_filtered_image(cv_img=cv_img, bgr_lower=bgr_red_lower, bgr_upper=bgr_red_upper)

    # dilate image to flesh out the red rings enough to cover the blue bits used for targeting enemies
    # (this is an attempt to prevent allies from being targeted)
    kernel = np.ones((1, 12), np.uint8)
    cv_img_red = cv2.dilate(cv_img_red, kernel=kernel, iterations=3)
    # cv2.imwrite("red.png", cv_img_red)

    cv_img_orred = cv2.bitwise_or(cv_img, cv_img_red)

    # stored in the np array as BGR
    bgr_blue = [178, 67, 73]
    cv_img_blue = get_filtered_image(cv_img=cv_img_orred, bgr_lower=bgr_blue, bgr_upper=bgr_blue)
    cv2.imwrite("blue.png", cv_img_blue)

    matches_sig2 = get_template_match(main_cv_img=cv_img_blue, template_cv_image=battle_in_range_sig_2_img,
                                      threshold=THRESH_BATTLE_IN_RANGE_2, many=True, scale=True, default=[])
    matches_sig3 = get_template_match(main_cv_img=cv_img_blue, template_cv_image=battle_in_range_sig_3_img,
                                      threshold=THRESH_BATTLE_IN_RANGE_3, many=True, scale=True, default=[])
    matches_sig2.extend(matches_sig3)
    matches_sig4 = get_template_match(main_cv_img=cv_img_blue, template_cv_image=battle_in_range_sig_4_img,
                                      threshold=THRESH_BATTLE_IN_RANGE_3, many=True, scale=True, default=[])
    matches_sig2.extend(matches_sig4)
    matches_sig_right = get_template_match(main_cv_img=cv_img_blue, template_cv_image=battle_in_range_sig_right_img,
                                           threshold=THRESH_BATTLE_IN_RANGE_RIGHT, many=True, scale=True, default=[])
    matches_sig2.extend(matches_sig_right)

    matches = math_utils.deduplicate_rects(matches_sig2)

    return None if len(matches) == 0 else matches


def get_battle_movement_squares(cv_img=None):
    """
    returns None if no enemies in range, else returns the rects matching signature used, of all enemies in range
    :param cv_img:
    :return:
    """
    if cv_img is None:
        cv_img = fetch_screenshot(height=ORIG_HEIGHT, width=ORIG_WIDTH, color=True,
                                  temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)

    cv2.imwrite("debug_green.png", cv_img)

    # stored in the np array as BGR
    bgr_green = [70, 163, 103]
    cv_img_green = get_filtered_image(cv_img=cv_img, bgr_lower=bgr_green, bgr_upper=bgr_green)
    cv2.imwrite("green.png", cv_img_green)

    matches = get_template_match(main_cv_img=cv_img_green, template_cv_image=battle_move_sig,
                                 threshold=THRESH_BATTLE_MOVE_SQUARE, many=True, scale=True, default=None)

    return matches


def get_battle_enemy_positions(cv_img=None):
    if cv_img is None:
        cv_img = fetch_screenshot(height=ORIG_HEIGHT, width=ORIG_WIDTH, color=True,
                                  temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)

    matches = get_template_match(main_cv_img=cv_img, template_cv_image=battle_enemy_pos_sig_img,
                                 threshold=THRESH_BATTLE_ENEMY_POS, many=True, scale=True, default=None)

    return matches


def get_battle_own_pos(cv_img=None):
    if cv_img is None:
        cv_img = fetch_screenshot(height=ORIG_HEIGHT, width=ORIG_WIDTH, color=True,
                                  temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)

    matches = get_monster_pos(cv_img=cv_img, monster_name=names.MONSTER_SELF_NAME,
                              threshold=THRESH_BATTLE_OWN_POS)

    if matches is None:
        return None

    return random.choice(matches)


def get_battle_avatar_plus(cv_img=None):
    if cv_img is None:
        cv_img = fetch_screenshot(height=ORIG_HEIGHT, width=ORIG_WIDTH, color=True,
                                  temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)

    return get_template_match(main_cv_img=cv_img, template_cv_image=battle_avatar_plus_img,
                              threshold=THRESH_BATTLE_AVATAR_PLUS, many=False, scale=True, default=None)


def get_health_full_rect(cv_img=None):
    """
    Returns health rect if health is full, else None
    :param cv_img:
    :return:
    """
    if cv_img is None:
        cv_img = fetch_screenshot(height=ORIG_HEIGHT, width=ORIG_WIDTH, color=True,
                                  temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)

    return get_template_match(main_cv_img=cv_img, template_cv_image=health_full_img, many=False,
                              threshold=THRESH_HEALTH_FULL, scale=True)


def get_close_diag_btn(cv_img=None):
    """
    Returns None if no close dialog button detected, else returns the rect for the button
    :param cv_img:
    :return:
    """
    if cv_img is None:
        cv_img = fetch_screenshot(height=ORIG_HEIGHT, width=ORIG_WIDTH, color=True,
                                  temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)

    close_btn_rect = get_template_match(main_cv_img=cv_img, template_cv_image=close_diag_btn_img, many=False,
                                        threshold=THRESH_CLOSE_DIAG_BTN, scale=True)

    return close_btn_rect


def is_astrub_zaap(cv_img=None):
    """
    Returns False if no astrub zaap detected, else returns True
    :param cv_img:
    :return:
    """
    if cv_img is None:
        cv_img = fetch_screenshot(height=ORIG_HEIGHT, width=ORIG_WIDTH, color=True,
                                  temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)

    zaap_rect = get_template_match(main_cv_img=cv_img, template_cv_image=zaap_img, many=False,
                                   threshold=THRESH_ZAAP, scale=True)

    return zaap_rect is not None


def init():
    global monster_image_dict
    for monster_name in names.MONSTER_NAME_LIST:
        print(names.get_pos_img_names(monster_name))
        monster_image_dict[monster_name] = [read_image(fname, color=True) for fname in
                                            names.get_pos_img_names(monster_name)]


init()
