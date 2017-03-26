import random

import collections

DEDUPLICATE_RECT_THRESH_PCTG = 0.5

RAND_CLICK_OFFSET_PCTG = 1 / 3


def euclidean(x1, y1, x2, y2):
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


def deduplicate_rects(rects: list):
    selected_rects = []
    for i in range(len(rects)):
        x11, y11, x12, y12 = rects[i]
        w1 = x12 - x11
        h1 = y12 - y11
        too_close = False
        for j in range(i + 1, len(rects)):
            x21, y21, x22, y22 = rects[j]
            w2 = x22 - x21
            h2 = y22 - y21
            # print(euclidean(x11, y11, x21, y21), DEDUPLICATE_RECT_THRESH_PCTG * min(h1, w1, h2, w2))
            too_close = euclidean(x11, y11, x21, y21) < DEDUPLICATE_RECT_THRESH_PCTG * min(h1, w1, h2, w2)
            if too_close:
                break
        if not too_close:
            selected_rects.append(rects[i])

    return selected_rects


def get_rand_click_point(rect: collections.Sequence):
    """

    :param rect: (x1, y1, x2, y2) representing top left and bottom right corners respectively (should be an indexable type)
    :return: the x,y co-ordinates of where the click should be made
    """
    w, h = rect[2] - rect[0], rect[3] - rect[1]
    left = int(rect[0] + w / 3)
    right = int(rect[0] + 2 * w / 3)
    top = int(rect[1] + h / 3)
    bottom = int(rect[1] + 2 * h / 3)

    rand_x = random.randint(left, right)
    rand_y = random.randint(top, bottom)

    return rand_x, rand_y


def get_max_min_dist_pt(choose_pt_list: list, far_from_pt_list: list):
    if len(far_from_pt_list) == 0:
        return random.choice(choose_pt_list)
    return max(choose_pt_list,
               key=lambda pt: min([euclidean(pt[0], pt[1], fpt[0], fpt[1]) for fpt in far_from_pt_list]))


def get_min_avg_dist_pt(choose_pt_list: list):
    # this will include the point itself in the distance calculation, but it doesn't matter as the distance will be 0
    # the distance is squared to increase the effect on the sum of larger distances, as the centremost can
    # be expected to have the least maximum
    return min(choose_pt_list,
               key=lambda pt: sum([euclidean(pt[0], pt[1], fpt[0], fpt[1])**2 for fpt in choose_pt_list]))
