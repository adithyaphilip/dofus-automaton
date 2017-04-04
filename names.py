MONSTER_TOFU_INDEX = 0

OWN_NAME = "me"
MONSTER_TOFU_NAME = "tofu"
MONSTER_BLACK_GOB_NAME = "black_gob"
MONSTER_WHITE_GOB_NAME = "white_gob"
MONSTER_GOB_NAME = "gobbal"
MONSTER_ARACH_NAME = "arachnee"
MONSTER_MOSQUITO_NAME = "mosquito"
MONSTER_GR_LARV_NAME = "green_larvae"
MONSTER_BL_LARV_NAME = "blue_larvae"
MONSTER_OR_LARV_NAME = "orange_larvae"
MONSTER_SELF_NAME = "enutrof"

# list of monsters for whom we have pos images to identify and start fights with
MONSTER_NAME_LIST = [MONSTER_TOFU_NAME, MONSTER_BLACK_GOB_NAME, MONSTER_WHITE_GOB_NAME, MONSTER_GOB_NAME,
                     MONSTER_SELF_NAME]

_ROOT_DIR = "/Users/aphilip/projects/dofus_automaton/python"

_POS_DIR = "pos"
_POS_FORMATS = [_POS_DIR + "/%s" + postfix for postfix in ["_tl_large.png", "_tr_large.png", "_bl_large.png",
                                                           "_br_large.png"]]

ATTACK_DIAG_ATTACK_FNAME = _POS_DIR + "/attack_diag_attack.png"
ATTACK_DIAG_PLUS_FNAME = _POS_DIR + "/attack_diag_plus.png"
ATTACK_DIAG_CANCEL_FNAME = _POS_DIR + "/attack_diag_cancel.png"

EMPTY_BOX_FNAME = _POS_DIR + "/empty_box.png"
CLOSE_DIAG_BTN_FNAME = _POS_DIR + "/close_diag_btn.png"
HEALTH_FULL_FNAME = _POS_DIR + "/full_health.png"
ZAAP_IMG_FNAME = _POS_DIR + "/zaap.png"

BATTLE_END_TURN_FNAME = _POS_DIR + "/end_turn.png"
BATTLE_READY_FNAME = _POS_DIR + "/ready_btn.png"
BATTLE_IN_RANGE_SIG_2_FNAME = _POS_DIR + "/battle_in_range_sig2.png"
BATTLE_IN_RANGE_SIG_3_FNAME = _POS_DIR + "/battle_in_range_sig3.png"
BATTLE_IN_RANGE_SIG_4_FNAME = _POS_DIR + "/battle_in_range_sig4.png"
BATTLE_IN_RANGE_SIG_RIGHT_FNAME = _POS_DIR + "/battle_in_range_sig_right.png"
BATTLE_SPELL_RANGE_SQ_SIG_FNAME = _POS_DIR + "/battle_spell_range_sq_sig.png"
BATTLE_ENEMY_POS_SIG_FNAME = _POS_DIR + "/battle_enemy_pos_sig.png"
BATTLE_AVATAR_PLUS_FNAME = _POS_DIR + "/battle_avatar_plus.png"
BATTLE_MOVE_SQUARE_FNAME = _POS_DIR + "/movement_sig.png"
BATTLE_SPELL_COINS_ENABLED_FNAME = _POS_DIR + "/spell_coins.png"
BATTLE_SPELL_LIVING_BAG_FNAME = _POS_DIR + "/spell_living_bag.png"
SPELL_COINS_DISABLED_FNAME = _POS_DIR + "/spell_coins_disabled.png"

TEMP_SCREENSHOT_FNAME = _ROOT_DIR + "/temp_sc.png"
LARGE_TEMP_SCREENSHOT_FNAME = _ROOT_DIR + "/temp_sc_large.png"

BATTLE_AVATAR_FNAME_DICT = {
    OWN_NAME: _POS_DIR + "/battle_own_avatar.png",
    MONSTER_TOFU_NAME: _POS_DIR + "/battle_tofu_avatar.png",
    MONSTER_MOSQUITO_NAME: _POS_DIR + "/battle_mosquito_avatar.png",
    MONSTER_ARACH_NAME: _POS_DIR + "/battle_arach_avatar.png",
    MONSTER_BL_LARV_NAME: _POS_DIR + "/battle_blue_larvae_avatar.png",
    MONSTER_GR_LARV_NAME: _POS_DIR + "/battle_green_larvae_avatar.png",
    MONSTER_OR_LARV_NAME: _POS_DIR + "/battle_orange_larvae_avatar.png"
}


def get_battle_avatar(name: str):
    if name not in BATTLE_AVATAR_FNAME_DICT:
        raise Exception("No battle avatar exists for name:", name)
    return BATTLE_AVATAR_FNAME_DICT[name]


def get_monster_name(index: int):
    return MONSTER_NAME_LIST[index]


def get_pos_img_names(monster_name):
    """
    returns the filenames of images of the different positions (directions) of a monster in the field (top-left,
     top-right, bottom-left, bottom-right)
    :param monster_name: the name of the monster,as defined in names.py
    :return: a list of filenames representing the different directions the monster can be looking
    """
    return [pos_format % monster_name for pos_format in _POS_FORMATS]
