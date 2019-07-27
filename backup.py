import subprocess
import sys
import os
import shutil
from datetime import datetime

# Ensure using Python 3.7 minimum as subprocess.Popen() does not have "text" argument in 3.6 and below.
# Will fail to run on less than Python 3 since function defs have types, but it is checked for completeness,
if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 7):
    raise Exception("Must be using Python 3.7+.")


def get_size_kilobytes(directory: str) -> int:
    """ Return total size in KB of the given directory and its subtree.

    Errors from shelling out are raised not ignored.
    Size is returned as an int.
    """

    # Use the "du" utility to get thge block size in KB ("-d") of the subtree from that directory ("-s").
    bashCommand = ["du", "-sk", directory]
    process = subprocess.Popen(bashCommand, text=True, stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error:
        raise error
    size = int(output.split()[0])
    return size


def oldest_in_directory(directory: str) -> str:
    """ Returns the full filepath of the oldest file or folder in the given directory

    Uses last metadata change time of each file to determine the least recently modified.
    Returns None if the given directory is empty.
    """
    files = sorted(os.listdir(directory), key=lambda f: os.path.getctime(
        "{}/{}".format(directory, f)))
    if len(files) == 0:
        return None
    return os.path.join(directory, files[0])


def newest_in_directory(directory: str) -> str:
    """ Returns the full filepath of the newest file or folder in the given directory

    Uses last metadata change time of each file to determine the most recently modified.
    Returns None if the given directory is empty.
    """
    files = sorted(os.listdir(directory), key=lambda f: os.path.getctime(
        "{}/{}".format(directory, f)))
    if len(files) == 0:
        return None
    return os.path.join(directory, files[-1])


def check_backup_possible(input_folder: str, backup_folder: str, max_backup_size_kilobytes: int) -> bool:
    """ Returns whether the new backup would be too large to fit at least the previous backup, according to max_backup_size_kilobytes."""
    input_folder_size_kilobytes = get_size_kilobytes(input_folder)
    backup_folder_size_kilobytes = get_size_kilobytes(backup_folder)

    newest_backup_folder = newest_in_directory(backup_folder)
    newest_backup_folder_size_kilobytes = 0
    if newest_backup_folder != None:
        newest_backup_folder_size_kilobytes = get_size_kilobytes(
            newest_backup_folder)

    return input_folder_size_kilobytes <= (max_backup_size_kilobytes - newest_backup_folder_size_kilobytes)


def purge_old_backups_as_required(input_folder: str, backup_folder: str, max_backup_size_kilobytes: int) -> None:
    """ Removes the oldest file/folder in the backup folder until there is room for the new backup."""
    input_folder_size_kilobytes = get_size_kilobytes(input_folder)
    backup_folder_size_kilobytes = get_size_kilobytes(backup_folder)
    oldest_backup_folder = oldest_in_directory(backup_folder)

    newest_backup_folder = newest_in_directory(backup_folder)
    newest_backup_folder_size_kilobytes = 0
    if newest_backup_folder != None:
        newest_backup_folder_size_kilobytes = get_size_kilobytes(
            newest_backup_folder)

    while (backup_folder_size_kilobytes + input_folder_size_kilobytes > max_backup_size_kilobytes and oldest_backup_folder != None):
        print("Purged old backup: " + oldest_backup_folder)
        if (os.path.isdir(oldest_backup_folder)):
            shutil.rmtree(oldest_backup_folder)
        else:
            os.remove(oldest_backup_folder)
        oldest_backup_folder = oldest_in_directory(backup_folder)
        backup_folder_size_kilobytes = get_size_kilobytes(backup_folder)


def create_new_backup(input_folder: str, output_folder: str):
    """ Creates a new backup which is date and time stamped. """
    if os.path.exists(output_folder):
        print("F")
    else:
        new_folder_name = shutil.copytree(input_folder, output_folder)
        print("Backup created at '" + new_folder_name + "'.")


def get_new_backup_name(backup_folder: str) -> str:
    formatted_current_datetime = datetime.now().strftime("%Y-%m-%d %Hh %Mm %Ss")
    output_folder = os.path.join(backup_folder, formatted_current_datetime)
    return output_folder


if (len(sys.argv) != 4) or not os.path.lexists(sys.argv[1]) or not os.path.lexists(sys.argv[2]) or not str(sys.argv[3]).isnumeric():
    print("Usage: python3 backup.py input_folder_path backup_folder_path max_backup_size_in_kilobytes")
    exit(1)
output_folder = get_new_backup_name(backup_folder=sys.argv[2])
if (os.path.exists(output_folder)):
    print("Folder to backup to already exists ('" +
          output_folder + "'). Please wait a second and try again."
          )
    exit(2)
if check_backup_possible(
    input_folder=sys.argv[1],
    backup_folder=sys.argv[2],
    max_backup_size_kilobytes=int(sys.argv[3])
):
    purge_old_backups_as_required(
        input_folder=sys.argv[1],
        backup_folder=sys.argv[2],
        max_backup_size_kilobytes=int(sys.argv[3])
    )
    create_new_backup(input_folder=sys.argv[1], output_folder=output_folder)
else:
    print("New backup would be too large to fit at least one previous backup. Cancelling.")
