import adb_utils
import image_utils
import math_utils
import names
import interaction_utils

import cv2

import time
import random
import sys

SPELL_LIVING_BAG_COOLDOWN = 6
TURN_TIME_LIMIT_SECONDS = 20

DEFAULT_AP = 6
SPELL_COINS_AP = 2
SPELL_LIVING_BAG_AP = 2


class Game:
    # (8, -16)
    _SKIP_COORDS = [(7, -12), (7, -10), (8, -22)]

    def __init__(self, x, y, min_x, max_x, min_y, max_y):
        self._x = x
        self._y = y
        self._min_x = min_x
        self._max_x = max_x
        self._min_y = min_y
        self._max_y = max_y
        self._visited = [(x, y)]

    def get_map_coords(self):
        return self._x, self._y

    def move_next_coords(self):
        up = self._x, max(self._y - 1, self._min_y)
        down = self._x, min(self._y + 1, self._max_y)
        right = min(self._x + 1, self._max_x), self._y
        left = max(self._x - 1, self._min_x), self._y

        possible_pts = {pt for pt in (up, right, left, down) if pt not in self._visited and pt not in Game._SKIP_COORDS}

        if len(possible_pts) == 0:
            self._visited = [(self._x, self._y)]
            possible_pts = {pt for pt in (up, right, left, down) if pt not in self._visited
                            and pt not in Game._SKIP_COORDS}

        # if for some reason it's still not resolved we're stuck
        if len(possible_pts) == 0:
            raise Exception("We've worked ourselves into a corner.. We can't go on like this.. visited:",
                            self._visited,
                            "current:", self._x,
                            self._y)

        next_pt = random.choice(list(possible_pts))

        self._visited.append(next_pt)
        self._x, self._y = next_pt

        print("Moving to:", next_pt, file=sys.stderr)

        if next_pt == right:
            interaction_utils.move_with_confirmation(interaction_utils.DIR_RIGHT)
        elif next_pt == left:
            interaction_utils.move_with_confirmation(interaction_utils.DIR_LEFT)
        if next_pt == down:
            interaction_utils.move_with_confirmation(interaction_utils.DIR_DOWN)
        if next_pt == up:
            interaction_utils.move_with_confirmation(interaction_utils.DIR_UP)

    def go_hunting_grounds_from_zaap(self):
        # moves = [interaction_utils.DIR_DOWN] * 4
        # for move in moves:
        #     interaction_utils.move_with_confirmation(move)
        #
        # # this is a special movement down to go on left side of gate
        # adb_utils.swipe(from_x=800, from_y=600, to_x=810, to_y=400)
        # time.sleep(random.randint(interaction_utils.MOVE_SLEEP_MIN, interaction_utils.MOVE_SLEEP_MAX))

        moves = [interaction_utils.DIR_RIGHT] * 4
        for move in moves:
            interaction_utils.move_with_confirmation(move)
        self._x = 8
        self._y = -19


def handle_battle():
    """
    Handles a battle from the start, including clicking the ready button and closing the victory dialog
    :return:
    """
    # we don't break if ready is not clicked so we can run this function even in middle of a battle
    interaction_utils.click_ready(wait=True, timeout=5)
    t_battle_check = time.time()
    battle_needs_to_close = False
    print("Checking if battle!")

    battle_sced = False
    battle_avatar_window_adjusted = False

    spell_coins_miss_streak = 0
    turn_ctr = 0

    cv_empty_box_rect = None
    last_attacked_rect = None

    battle_avatars = image_utils.get_battle_info()
    while battle_avatars is not None:
        if not battle_sced:
            image_utils.fetch_screenshot(height=image_utils.ORIG_HEIGHT, width=image_utils.ORIG_WIDTH,
                                         temp_fname="last_battle.png", color=True)
            battle_sced = True

        if not battle_avatar_window_adjusted:
            print("Adjusting avatar box!", file=sys.stderr)
            if interaction_utils.battle_move_avatar_box_away():
                print("Successfully adjusted avatar box!", file=sys.stderr)
                battle_avatar_window_adjusted = True
            else:
                print("ERROR: Could not detect plus for avatar box!", file=sys.stderr)

        if cv_empty_box_rect is None:
            cv_empty_box_rect = image_utils.get_empty_box_pos(many=False)
        battle_needs_to_close = True
        print("Battle check:", time.time() - t_battle_check, file=sys.stderr)
        # keep testing to see if it is your turn
        # if not your turn, try again later
        # NOTE: This rect can only be re-used if we are not moving the avatar box
        end_turn_rect = image_utils.get_end_turn_if_is_turn()
        # if not your turn, try again
        if end_turn_rect is not None:
            # if you've reached here, it's your turn.
            turn_ctr += 1
            print("Our turn has begun!", turn_ctr, file=sys.stderr)

            available_ap_expected = DEFAULT_AP

            if turn_ctr % SPELL_LIVING_BAG_COOLDOWN == 1:
                print("Casting living bag!", file=sys.stderr)
                living_bag_success = interaction_utils.cast_spell_living_bag(cv_empty_box_rect)
                if living_bag_success:
                    available_ap_expected -= SPELL_LIVING_BAG_AP
                print("Finished casting living bag!", living_bag_success, file=sys.stderr)

            # Start firing
            print("Casting coins, so far miss streak:", spell_coins_miss_streak, file=sys.stderr)
            max_coins_casts = available_ap_expected // SPELL_COINS_AP
            coins_was_cast, last_attacked_rect = interaction_utils.cast_spell_coins_repeatedly(
                empty_box_rect=cv_empty_box_rect,
                max_casts=max_coins_casts,
                preferred_rect=last_attacked_rect)
            print("Finished casting coins:", coins_was_cast, spell_coins_miss_streak, file=sys.stderr)

            if not coins_was_cast:
                spell_coins_miss_streak += 1
            else:
                spell_coins_miss_streak = 0

            # the >= is if even the turn after we move we can't see the enemy
            if spell_coins_miss_streak >= 2 and names.MONSTER_TOFU_NAME in map(lambda x: x[0], battle_avatars):
                interaction_utils.battle_move_away_from_enemy(cv_empty_box_rect)
            elif spell_coins_miss_streak >= 3:
                if turn_ctr > 5:
                    print("Can't find enemies! Moving avatar box again!", file=sys.stderr)
                    if interaction_utils.battle_move_avatar_box_away():
                        print("Moved avatar box successfully!", file=sys.stderr)
                    else:
                        print("Failed to detect avatar bix plus sign!", file=sys.stderr)

                interaction_utils.battle_move_away_from_enemy(cv_empty_box_rect)

            # End your turn. It is important to re-fetch. Death of enemy can change position.
            # Remove the wait as we accidentally end our own turn due to the delay during which our next turn
            # would start. Re-added the wait via the loop because otherwise we mess up movement which takes us to places
            # where we die
            end_turn_rect = image_utils.get_end_turn_if_is_turn()
            end_turn_wait = 2
            end_turn_wait_start = time.time()
            while end_turn_rect is not None:
                if time.time() - end_turn_wait_start >= end_turn_wait:
                    adb_utils.tap(*math_utils.get_rand_click_point(end_turn_rect))
                    break
                end_turn_rect = image_utils.get_end_turn_if_is_turn()

        battle_cv_img = image_utils.fetch_screenshot(height=image_utils.ORIG_HEIGHT, width=image_utils.ORIG_WIDTH,
                                                     temp_fname="battle_proggress.png", color=True)
        battle_avatars = image_utils.get_battle_info(battle_cv_img)

    # close the fight finished dialog box
    print("Closing fight dialog!")
    if battle_needs_to_close:
        image_utils.fetch_screenshot(image_utils.ORIG_HEIGHT, image_utils.ORIG_WIDTH, color=True,
                                     temp_fname="fight_fin_dialog.png")
        interaction_utils.close_diag(wait=True, timeout=5)
    # if there are any additional dialogs (e.g. level up), close them too
    print("Closing dialogs!")
    while interaction_utils.close_diag(wait=False):
        pass  # the function in the loop condition takes care of closing it, no-op here
        # heal up before the next fight
        # TODO: Disabled for now as fights are easy and inter-fight time is sufficient to heal
        # print("Waiting to heal!")
        # interaction_utils.heal_fully()
        # print("Healed!")
    # this is in case the clicking of "end turn" earlier accidentally started a fight
    if image_utils.get_battle_info() is not None:
        handle_battle()


def start_automaton(start_x: int, start_y: int, attack_monster_names: list):
    # IMPORTANT: Make sure you set the starting x and y values correctly!
    # NOTE: The tofu corner x and y bounds have been reduced by 1 to accommodate for erroneous movements
    # game = Game(x=start_x, y=start_y, min_x=-3, min_y=-20, max_x=-2, max_y=-13)
    # tofu corner
    # game = Game(x=start_x, y=start_y, min_x=2, min_y=-13, max_x=7, max_y=-10)
    # astrub down outskirts
    # game = Game(x=start_x, y=start_y, min_x=-3, min_y=-13, max_x=6, max_y=-13)
    # astrub right outskirts`
    game = Game(x=start_x, y=start_y, min_x=8, min_y=-23, max_x=8, max_y=-13)

    # game.go_battlefield()
    # return
    while True:
        # this is to
        # a. handle accidental battle starts due to movement attempted at the end of this loop
        # b. has added benefit of starting the automaton even if fight is already in ready screen
        if image_utils.get_battle_info() is not None:
            handle_battle()

        while interaction_utils.attempt_attack(monster_attack_names=attack_monster_names):
            # we have been taken to the "Ready" screen, hand it over to the fight handler
            handle_battle()
            # we have finished a battle, resume search

        # check if we have died. If so, move to battlefield
        if image_utils.is_astrub_zaap():
            print("Died at", time.time(), ":( Going to war again! But first let me heal.", file=sys.stderr)
            interaction_utils.heal_fully()
            print("Finished healing!", file=sys.stderr)
            game.go_hunting_grounds_from_zaap()

        # we have not been able to find a suitable fight on this map, move to the next
        print("Moving to next map", file=sys.stderr)
        game.move_next_coords()


def main():
    # for move in [interaction_utils.DIR_LEFT] * 18:
    #     interaction_utils.move_with_confirmation(move)
    # handle_battle()
    # return
    start_automaton(start_x=8, start_y=-19,
                    attack_monster_names=[names.MONSTER_GOB_NAME])


if __name__ == '__main__':
    main()
