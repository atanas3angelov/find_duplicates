import os.path
from os import scandir
from os import path
# from os import listdir  # faster but no check for file/dir like os.scandir()
from PIL import Image, ImageFile
import logging


LOG_FILE = 'find_dupes_logs.log'

logging.basicConfig(filename=LOG_FILE, encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__name__)


def scantree(p):
    """Recursively yield DirEntry objects for given directory."""
    for e in scandir(p):
        yield e
        if e.is_dir(follow_symlinks=False):
            yield from scantree(e.path)
            # for e in scantree(e.path):
            #     yield e

# def scantree(path):
#     """Recursively yield DirEntry objects for given directory."""
#     for entry in scandir(path):
#         if entry.is_dir(follow_symlinks=False):
#             # yield from scantree(entry.path)
#             yield entry
#             for entry in scantree(entry.path):
#                 yield entry
#         else:
#             yield entry


def find_duplicates_by_name(paths4dupes, stop_event, ignore_extension=False):
    # if ignore_extension False:
    #   return matches in the format:
    #    { key: <str> (filename.ext) -> [path1/filename.ext, path2/filename.ext] }
    # if ignore_extension True:
    #   return matches in the format:
    #    { key: <str> (filename) -> [path1/filename.ext, path2/filename.ext] }

    matches = {}

    # progressbar related
    progress_to_scan_completion = estimate_work(paths4dupes)
    current_entry = 0

    for p in paths4dupes:

        for entry in scantree(p):

            if stop_event.is_set():
                break

            # progressbar related
            current_entry += 1
            yield 100*current_entry/progress_to_scan_completion

            full_path = path.normpath(path.dirname(entry.path) + '/' + entry.name)

            if ignore_extension:
                f_name, f_ext = os.path.splitext(entry.name)
            else:
                f_name = entry.name

            if f_name not in matches:
                matches[f_name] = [full_path]
            else:
                matches[f_name].append(full_path)

        else:
            continue
        break

    for key in list(matches):
        if len(matches[key]) == 1:
            del matches[key]

    yield matches


def find_duplicates_by_name_and_size(paths4dupes, stop_event):
    # return matches in the format:
    #  { key: <tuple> (filename.ext, filesize) -> [path1/filename.ext, path2/filename.ext] }

    matches = {}

    # progressbar related
    progress_to_scan_completion = estimate_work(paths4dupes)
    current_entry = 0

    for p in paths4dupes:

        for entry in scantree(p):

            if stop_event.is_set():
                break

            # progressbar related
            current_entry += 1
            yield 100*current_entry/progress_to_scan_completion

            full_path = path.normpath(path.dirname(entry.path) + '/' + entry.name)

            if (entry.name, path.getsize(entry.path)) not in matches:
                matches[(entry.name, path.getsize(entry.path))] = [full_path]
            else:
                if full_path not in matches[(entry.name, path.getsize(entry.path))]:
                    matches[(entry.name, path.getsize(entry.path))].append(full_path)
        else:
            continue
        break

    for key in list(matches):
        if len(matches[key]) == 1:
            del matches[key]

    yield matches


def estimate_work(paths4dupes):
    all_work = 0
    for p in paths4dupes:
        for _entry in scantree(p):
            all_work += 1

    return all_work


def find_duplicate_images(paths4dupes, stop_event):
    # return matches in the format:
    #  { key: <tuple> ((r, g, b) x 5) -> [path1/filename.ext, path2/filename.ext] }
    # each tuple key contains 5 other tuples of 3 integers (the rgb vals of an image pixel)

    ImageFile.LOAD_TRUNCATED_IMAGES = True

    matches = {}

    # progressbar related
    progress_to_scan_completion = estimate_work(paths4dupes)
    current_entry = 0

    for p in paths4dupes:

        for entry in scantree(p):

            if stop_event.is_set():
                break

            # progressbar related
            current_entry += 1
            yield 100*current_entry/progress_to_scan_completion

            full_path = path.normpath(path.dirname(entry.path) + '/' + entry.name)

            if entry.name.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                try:
                    im = Image.open(full_path)

                except OSError:
                    print(f"Error opening: {full_path}")
                    logger.error(f"Error opening: {full_path}")
                    continue

                else:
                    im_size = im.size
                    p1 = im.getpixel((0, 0))
                    p2 = im.getpixel(((im_size[0]-1), 0))
                    p3 = im.getpixel((0, (im_size[1]-1)))
                    p4 = im.getpixel(((im_size[0]-1), (im_size[1]-1)))
                    p5 = im.getpixel(((int((im_size[0]-1)/2)), (int((im_size[1]-1)/2))))

                    if (p1, p2, p3, p4, p5) not in matches:
                        matches[(p1, p2, p3, p4, p5)] = [full_path]
                    else:
                        if full_path not in matches[(p1, p2, p3, p4, p5)]:
                            matches[(p1, p2, p3, p4, p5)].append(full_path)
        else:
            continue
        break

    for key in list(matches):
        if len(matches[key]) == 1:
            del matches[key]

    yield matches


def check_files_for_duplicates_by_name(_potentially_duped_files,
                                       _potential_paths4dupes,
                                       _size_maters=True,
                                       _search_subpaths=True):

    matches = {}

    return matches
