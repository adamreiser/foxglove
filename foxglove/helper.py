from os.path import join, splitext, normpath, split


def get_addon_pref_file(work_dir, addon):
    return join(work_dir, 'addon_prefs', splitext(normpath(split(
            addon)[1]))[0] + '.js')
