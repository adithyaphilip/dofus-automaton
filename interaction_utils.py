import adb_utils
import image_utils
import math_utils
import names

import time
import random
import sys

MIN_MONSTER_LIMIT = 2
MAX_MONSTER_LIMIT = 7

MIN_ATTACK_TAP_DELAY = 0.3
MAX_ATTACK_TAP_DELAY = 0.5

MAX_ATTACKS_DENIED = 5
MIN_ATTACKS_DENIED = 4

MAX_NO_MONSTER_FOUND = 6
MIN_NO_MONSTER_FOUND = 4

MAX_ATTACK_NOT_FOUND = 6
MIN_ATTACK_NOT_FOUND = 5

MAX_BATTLE_CHECK_TIMES = 5
MAX_ACCIDENTAL_BATTLE_CHECK_TIMES = 2

DIR_RIGHT = 1
DIR_LEFT = 2
DIR_UP = 3
DIR_DOWN = 4

MOVE_SLEEP_MIN = 12
MOVE_SLEEP_MAX = 15

SWIPE_MIN_OFFSET = 200
SWIPE_RND_OFFSET = 100
SWIPE_WRONG_DIR_OFFSET = 80

SPELL_COINS_CAST_TIMES_LIMIT = 3

MAP_X_END_LIMIT = 1100
MAP_X_START_LIMIT = 135
MAP_Y_START_LIMIT = 130
MAP_Y_END_LIMIT = 800


def click_empty_box(empty_box_rect):
    adb_utils.tap(*math_utils.get_rand_click_point(empty_box_rect))


def battle_move_away_from_enemy(empty_box_rect):
    click_empty_box(empty_box_rect)
    # to let the green squares form properly
    time.sleep(0.5)
    cv_sc = image_utils.fetch_screenshot(height=image_utils.ORIG_HEIGHT, width=image_utils.ORIG_WIDTH,
                                         color=True, temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME)
    move_sq_rects = image_utils.get_battle_movement_squares(cv_img=cv_sc)
    enemy_pos_rects = image_utils.get_battle_enemy_positions(cv_img=cv_sc)

    if move_sq_rects is None:
        print("FAILED TO MOVE AS NO MOVEMENT SQUARES SEEN!", file=sys.stderr)
        return False

    move_click_pts = [math_utils.get_rand_click_point(rect) for rect in move_sq_rects]
    if enemy_pos_rects is None:
        print("WARNING: Failed to detect enemy, moving randomly", file=sys.stderr)
        chosen_move_pt = random.choice(move_click_pts)

    else:
        enemy_pos_pts = [math_utils.get_rand_click_point(rect) for rect in enemy_pos_rects]
        chosen_move_pt = math_utils.get_max_min_dist_pt(choose_pt_list=move_click_pts, far_from_pt_list=enemy_pos_pts)

    adb_utils.tap(*chosen_move_pt)
    adb_utils.tap(*chosen_move_pt)
    click_empty_box(empty_box_rect)

    return True


def cast_spell_coins_repeatedly(empty_box_rect):
    """
    clicks on an empty box, then the coins spell, casts if enemies in range.
    :param empty_box_rect:
    :return: True if the spell was successfully cast even once, False otherwise
    """

    spell_rect = image_utils.get_spell_coins()
    chosen_rect = None
    cast_ctr = 0
    while spell_rect is not None and cast_ctr < SPELL_COINS_CAST_TIMES_LIMIT:
        click_empty_box(empty_box_rect)
        adb_utils.tap(*math_utils.get_rand_click_point(spell_rect))
        # wait for the range to appear
        time.sleep(1)
        rects = image_utils.get_spell_in_range_rects()
        # if no one is in range, pass your turn
        if rects is None:
            print("Nowhere to click :(")
            break
        # reaching here means some guys are in range.
        # If the guy we chose last time in the same call is not in range anymore,
        # or we're picking for the first time this call (will be None, causing the "not in" check to succeed),
        # randomly choose a new guy.
        # Else, stick to the same guy
        if chosen_rect not in rects:
            chosen_rect = random.choice(rects)

        adb_utils.tap(*math_utils.get_rand_click_point(chosen_rect))
        adb_utils.tap(*math_utils.get_rand_click_point(chosen_rect))
        cast_ctr += 1

        # wait for the spell to be cast
        time.sleep(2)

    return cast_ctr > 0


def cast_spell_living_bag(empty_box_rect):
    """
    Returns true if an empty square in range of the spell was found and Living Bag was attempted to be cast on it
    :param empty_box_rect:
    :return:
    """

    click_empty_box(empty_box_rect)
    spell_rect = image_utils.get_spell_living_bag()

    if spell_rect is None:
        return False

    adb_utils.tap(*math_utils.get_rand_click_point(spell_rect))
    # wait for the range to appear
    time.sleep(1)
    rects = image_utils.get_spell_range_empty_squares()
    if rects is None:
        return False

    click_pt = math_utils.get_min_avg_dist_pt([math_utils.get_rand_click_point(rect) for rect in rects])
    adb_utils.tap(*click_pt)
    adb_utils.tap(*click_pt)


def heal_fully():
    """
    blocks until health reaches 100%
    :return:
    """
    while image_utils.get_health_full_rect() is None:
        pass


def close_diag(wait: bool):
    """

    :return: True if was able to detect close dialog button and attempted to click it, false otherwise
    """
    close_diag_rect = image_utils.get_close_diag_btn()
    if wait:
        while close_diag_rect is None:
            close_diag_rect = image_utils.get_close_diag_btn()

    if close_diag_rect is None:
        return False

    adb_utils.tap(*math_utils.get_rand_click_point(close_diag_rect))
    return True


def click_ready(wait: bool):
    """

    :return: True if was able to detect ready button and attempted to click it, false otherwise
    """
    ready_rect = image_utils.get_ready_button_if_battle()
    if wait:
        while ready_rect is None:
            ready_rect = image_utils.get_ready_button_if_battle()

    if ready_rect is None:
        return False

    adb_utils.tap(*math_utils.get_rand_click_point(ready_rect))
    return True


# TODO: APHILIP - add confirmation, currently present at just a timeout
def move_with_confirmation(direction: int):
    """
    returns only after movement is confirmed (ideally). Currently works using a random delay
    :param direction: specified using DIR_* constants in this file
    :return:
    """
    start_y = random.randint(image_utils.ORIG_HEIGHT * 2 / 5, image_utils.ORIG_HEIGHT * 3 / 5)
    start_x = random.randint(image_utils.ORIG_WIDTH * 2 / 5, image_utils.ORIG_WIDTH * 2 / 5)
    swipe_offset = SWIPE_MIN_OFFSET + random.randint(0, SWIPE_RND_OFFSET)
    swipe_wrong_dir_offset = random.randint(-SWIPE_WRONG_DIR_OFFSET, SWIPE_WRONG_DIR_OFFSET)

    sw = {
        DIR_RIGHT: (start_x, start_y, start_x - swipe_offset, start_y + swipe_wrong_dir_offset),
        DIR_LEFT: (start_x, start_y, start_x + swipe_offset, start_y + swipe_wrong_dir_offset),
        DIR_UP: (start_x, start_y, start_x + swipe_wrong_dir_offset, start_y + swipe_offset),
        DIR_DOWN: (start_x, start_y, start_x + swipe_wrong_dir_offset, start_y - swipe_offset),
    }

    if direction not in sw:
        raise Exception("Direction with value:", direction, ":not in switch with keys:", sw.keys())

    adb_utils.swipe(*sw[direction])

    # this is the "confirmation" as of now
    time.sleep(random.randint(MOVE_SLEEP_MIN, MOVE_SLEEP_MAX))


def cancel_fight_dialog():
    empty_box_pos = None
    while empty_box_pos is None:
        box_search_img = image_utils.fetch_screenshot(height=image_utils.READ_HEIGHT,
                                                      width=image_utils.READ_WIDTH,
                                                      temp_fname=names.TEMP_SCREENSHOT_FNAME, color=False)
        empty_box_pos = image_utils.get_empty_box_pos(box_search_img)
        if empty_box_pos is not None:
            adb_utils.tap(*math_utils.get_rand_click_point(empty_box_pos))
        else:
            print("ERROR: CAN'T FIND EMPTY BOX!!!!", file=sys.stderr)


def attempt_attack():
    """
    :return: True if it was able to begin a fight (takes you to the screen where you press "Ready"), False if it
    was unable to start a fight with the prescribed conditions (monster limit) within the prescribed number of retires
    for various occurrences (failed clicks/denied fights/not finding enemies). This is an indication to move to another
    map
    """
    deny_limit = random.randint(MIN_ATTACKS_DENIED, MAX_ATTACKS_DENIED)
    denied_clicks = []

    no_monster_limit = random.randint(MIN_NO_MONSTER_FOUND, MAX_NO_MONSTER_FOUND)
    no_monster_ctr = 0

    monster_click_missed_limit = random.randint(MIN_ATTACK_NOT_FOUND, MAX_ATTACK_NOT_FOUND)
    missed_clicks = []

    empty_box_rect = image_utils.get_empty_box_pos(many=False)
    click_empty_box(empty_box_rect)

    while len(denied_clicks) < deny_limit and no_monster_ctr < no_monster_limit \
            and len(missed_clicks) < monster_click_missed_limit:

        # 1. fetch image and find tofus
        sc_img = image_utils.fetch_screenshot(height=image_utils.ORIG_HEIGHT, width=image_utils.ORIG_WIDTH,
                                              temp_fname=names.LARGE_TEMP_SCREENSHOT_FNAME, color=True)
        tofu_rects = image_utils.get_monster_pos(sc_img, monster_name=names.get_monster_name(names.MONSTER_TOFU_INDEX),
                                                 threshold=image_utils.THRESH_TOFU_POS)
        if tofu_rects is None:
            no_monster_ctr += 1
            print("Found no monsters!", file=sys.stderr)
            continue

        print("Found monsters:", len(tofu_rects))

        # 2. fetch random click points
        click_pts = [math_utils.get_rand_click_point(rect) for rect in tofu_rects]
        click_pts = [pt for pt in click_pts if MAP_X_START_LIMIT <= pt[0] <= MAP_X_END_LIMIT
                     and MAP_Y_START_LIMIT < pt[1] < MAP_Y_END_LIMIT]

        if len(click_pts) == 0:
            no_monster_ctr += 1
            print("Found no clickable monsters!", file=sys.stderr)
            continue

        # 3. perform a click based on max of min distance to points already denied
        next_click_pt = math_utils.get_max_min_dist_pt(choose_pt_list=click_pts, far_from_pt_list=denied_clicks)
        adb_utils.tap(x=next_click_pt[0], y=next_click_pt[1])

        time.sleep(1)

        # 4. check if attack box came up, else repeat
        diag_img = image_utils.fetch_screenshot(height=image_utils.READ_HEIGHT, width=image_utils.READ_WIDTH,
                                                temp_fname=names.TEMP_SCREENSHOT_FNAME, color=False)
        diag_info = image_utils.get_attack_diag_info(diag_img)
        if diag_info is None:
            # check if we accidentally started a fight
            time.sleep(1)
            for _ in range(MAX_ACCIDENTAL_BATTLE_CHECK_TIMES):
                battle_info = image_utils.get_battle_info()
                if battle_info is not None:
                    return battle_info
            # phew, not an accidental battle (we could have ended up fighting a too strong mob), resume normal response

            # necessary to take care of the stupid tofu statues
            missed_clicks.append(next_click_pt)
            # in case we clicked the monster but the dialog detection failed, or we clicked on something else
            # this should follow every tap operation that fails to give the desired result, ideally
            click_empty_box(empty_box_rect)
            continue

        # 5. Measure size of fight. If fight too much, add to denied list. Else start fight.
        monster_num, attack_rect, cancel_rect = diag_info
        print("Found fight! Size:", monster_num, file=sys.stderr)

        if monster_num < MIN_MONSTER_LIMIT or monster_num > MAX_MONSTER_LIMIT:
            denied_clicks.append(next_click_pt)
            click_empty_box(empty_box_rect)
            continue

        # 6. Start the fight! :D
        time.sleep(random.uniform(MIN_ATTACK_TAP_DELAY, MAX_ATTACK_TAP_DELAY))
        adb_utils.tap(*math_utils.get_rand_click_point(attack_rect))
        # 7. Check if we started the fight. If yes, return information about it
        # the loop is just in case th fight didn't start for some reason
        for _ in range(MAX_BATTLE_CHECK_TIMES):
            battle_info = image_utils.get_battle_info()
            if battle_info is not None:
                return battle_info
            time.sleep(1)
    return None  # means we couldn't start a fight
