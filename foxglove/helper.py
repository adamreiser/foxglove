from os.path import join
from os.path import splitext
from os.path import normpath
from os.path import split


def get_addon_pref_file(work_dir, addon):
    return join(work_dir, 'addon_prefs', splitext(normpath(split(
            addon)[1]))[0] + '.js')
