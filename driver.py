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
TURN_TIME_LIMIT_SECONDS = 18


class Game:
    _SKIP_COORDS = [(5, -12), (2, -12), (2, -10), (3, -10), (5, -10)]

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
            possible_pts = {pt for pt in (up, right, left, down) if pt not in self._visited}

        # if for some reason it's still not resolved we're stuck
        if len(possible_pts) == 0:
            raise Exception("We've worked ourselves into a corner.. We can't go on like this.. visited:",
                            self._visited,
                            "current:", self._x,
                            self._y)

        next_pt = random.choice(list(possible_pts))

        self._visited.append(next_pt)
        self._x, self._y = next_pt

        if next_pt == right:
            interaction_utils.move_with_confirmation(interaction_utils.DIR_RIGHT)
        elif next_pt == left:
            interaction_utils.move_with_confirmation(interaction_utils.DIR_LEFT)
        if next_pt == down:
            interaction_utils.move_with_confirmation(interaction_utils.DIR_DOWN)
        if next_pt == up:
            interaction_utils.move_with_confirmation(interaction_utils.DIR_UP)

    def go_battlefield(self):
        moves = [interaction_utils.DIR_DOWN] + [interaction_utils.DIR_LEFT] * 2 + [interaction_utils.DIR_DOWN] * 7
        for move in moves:
            interaction_utils.move_with_confirmation(move)
        self._x = 4
        self._y = -12


def handle_battle():
    """
    Handles a battle from the start, including clicking the ready button and closing the victory dialog
    :return:
    """
    interaction_utils.click_ready(wait=True)
    t_battle_check = time.time()
    battle_needs_to_close = False
    print("Checking if battle!")

    spell_coins_miss_streak = 0
    turn_ctr = 0

    cv_empty_box_rect = None

    battle_avatars = image_utils.get_battle_info()
    while battle_avatars is not None:
        if cv_empty_box_rect is None:
            cv_empty_box_rect = image_utils.get_empty_box_pos(many=False)
        battle_needs_to_close = True
        print("Battle check:", time.time() - t_battle_check, file=sys.stderr)
        # keep testing to see if it is your turn
        # if not your turn, try again later
        # NOTE: This rect can only be re-used if we are not moving the avatar box
        end_turn_rect = image_utils.get_end_turn_if_is_turn()
        # if not your turn, try again
        if end_turn_rect is None:
            continue

        print("Our turn has begun!", file=sys.stderr)
        turn_start_time = time.time()
        # if you've reached here, it's your turn.
        turn_ctr += 1

        if turn_ctr % SPELL_LIVING_BAG_COOLDOWN == 1:
            print("Casting living bag!", file=sys.stderr)
            living_bag_success = interaction_utils.cast_spell_living_bag(cv_empty_box_rect)
            print("Finished casting living bag!", living_bag_success, file=sys.stderr)

        # Start firing
        print("Casting coins, so far miss streak:", spell_coins_miss_streak, file=sys.stderr)
        coins_was_cast = interaction_utils.cast_spell_coins_repeatedly(cv_empty_box_rect)
        print("Finished casting coins:", coins_was_cast, spell_coins_miss_streak, file=sys.stderr)

        if not coins_was_cast:
            spell_coins_miss_streak += 1
        else:
            spell_coins_miss_streak = 0

        # the >= is if even the turn after we move we can't see the enemy
        if spell_coins_miss_streak >= 2 and names.MONSTER_TOFU_NAME in map(lambda x: x[0], battle_avatars):
            interaction_utils.battle_move_away_from_enemy(cv_empty_box_rect)

        # End your turn. It is important to re-fetch. Death of enemy can change position.
        # Remove the wait as we accidentally end our own turn due to the delay
        end_turn_rect = image_utils.get_end_turn_if_is_turn()
        if end_turn_rect is not None and time.time() - turn_start_time < TURN_TIME_LIMIT_SECONDS:
            adb_utils.tap(*math_utils.get_rand_click_point(end_turn_rect))

        battle_avatars = image_utils.get_battle_info()

    # close the fight finished dialog box
    print("Closing fight dialog!")
    if battle_needs_to_close:
        interaction_utils.close_diag(wait=True)
    # if there are any additional dialogs (e.g. level up), close them too
    print("Closing dialogs!")
    while interaction_utils.close_diag(wait=False):
        pass  # the function in the loop condition takes care of closing it, no-op here
        # heal up before the next fight TODO: Disabled for now as fights are easy and inter-fight time is sufficient to heal
        # print("Waiting to heal!")
        # interaction_utils.heal_fully()
        # print("Healed!")


def start_automaton(start_x: int, start_y: int):
    # IMPORTANT: Make sure you set the starting x and y values correctly!
    # NOTE: The tofu corner x and y bounds have been reduced by 1 to accommodate for erroneous movements
    game = Game(x=start_x, y=start_y, min_x=4, min_y=-11, max_x=6, max_y=-11)
    # game.go_battlefield()
    while True:
        while interaction_utils.attempt_attack():
            # we have been taken to the "Ready" screen, hand it over to the fight handler
            handle_battle()
            # we have finished a battle, resume search
        # we have not been able to find a suitable fight on this map, move to the next
        game.move_next_coords()


def main():
    start_automaton(start_x=4, start_y=-11)


if __name__ == '__main__':
    main()
