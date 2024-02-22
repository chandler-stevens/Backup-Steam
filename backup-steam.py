from datetime import datetime
from filecmp import clear_cache, cmp
from os import makedirs, path, remove, system, walk
from pathlib import Path
from re import search
from shutil import copy2, copytree, rmtree
from time import sleep
from tkinter import Label, Tk, ttk

# Shows Game (1), Folder (2), and/or File (3) drill-down progress bars,
#  but makes the backup take up to 4 times longer than when it is Disabled (0).
GAME = 1 << 0
FOLDER = 1 << 1
FILE = 1 << 2
GUI = GAME | FOLDER

# Define global variable for log string variable
log_dir = str(Path(__file__).resolve().parent)+"\\logs"
log_file_path = log_dir+"\\Games "+str(datetime.now()).split(".")[0].replace(":", "-")+".log"
log = "Backup started at "+str(datetime.now()).split(".")[0]
print(log, end="")


# Helper function to print to console and add to log file string variable
def print_and_log(text, skip_print=False):
    global log
    log += text+"\n"
    if not skip_print:
        print(text)


# Helper function to end backup, write to log file, and exit
def end_backup(code=1):
    print_and_log("\nBackup finished at " + str(datetime.now()).split(".")[0] + "\nDone.")
    with open(log_file_path, "w") as log_file:
        log_file.write(log)
    exit(code)


# Helper function to recursively find all sub-folders
def find_folders(root, folders, src):
    for folder in next(walk(root))[1]:
        folders.append(root[len(src):]+"/"+folder+"/")
        find_folders(root+"/"+folder, folders, src)


# Primary function
def backup():
    # Setup log folder
    makedirs(log_dir, exist_ok=True)

    # Define source and destination paths
    manifests = "D:/SteamLibrary/steamapps"
    source = "D:/SteamLibrary/steamapps/common"
    destination = "E:/Steam-Games-Backup"

    # Check paths
    if not path.exists(manifests):
        if GUI:
            progress.destroy()
        print_and_log("FATAL ERROR: Could not find app manifests path:\n" + manifests + "\n")
        end_backup()
    if not path.exists(source):
        if GUI:
            progress.destroy()
        print_and_log("FATAL ERROR: Could not find source path:\n" + source + "\n")
        end_backup()
    if not path.exists(destination):
        if GUI:
            progress.destroy()
        print_and_log("FATAL ERROR: Could not find destination path:\n" + destination + "\n")
        end_backup()

    # Kill Steam to prevent file changes during backup
    print_and_log("\n\nClosing Steam and sleeping for 3 seconds...")
    system("taskkill /f /im steam.exe 2>nul")
    sleep(3)

    # Determine which games are installed (according to the Steam Client GUI)
    installed_games = []
    print_and_log("\n--------------------------------------------------------", True)
    print_and_log("List of App manifests: ", True)
    print_and_log("--------------------------------------------------------", True)
    for acf in next(walk(manifests))[2]:
        if search(r"appmanifest_[0-9]+\.acf", acf):
            with open(manifests + "/" + acf, encoding='utf8') as json_file:
                game = next((var for var in json_file if '"installdir"' in var), None).split('"')[3]
                installed_games.append(game)
                print_and_log(game + "  -  " + acf, True)
    print_and_log("--------------------------------------------------------", True)
    print_and_log("Total App manifests: " + str(len(installed_games)), True)

    # Find all games in source
    src_games = []
    zombie_games = []
    ask_user = False
    print_and_log("\n--------------------------------------------------------", True)
    print_and_log("List of Installed Games:", True)
    print_and_log("--------------------------------------------------------", True)
    for game in next(walk(source))[1]:
        src_games.append(game)
        print_and_log(game, True)
        if (game not in installed_games) and (game != "Steam Controller Configs"):
            zombie_games.append(game)
    print_and_log("--------------------------------------------------------", True)
    print_and_log("Total Installed Games: " + str(len(src_games)), True)
    if len(src_games) <= 0:
        ask_user = True
        print_and_log("\nWARNING: No game folders exist, possibly because no games are installed currently!")

    if len(zombie_games) > 0:
        ask_user = True
        print_and_log("\n--------------------------------------------------------")
        print_and_log("List of Zombie Games:")
        print_and_log("\n--------------------------------------------------------")
        for game in zombie_games:
            print_and_log(game)
        print_and_log("--------------------------------------------------------")
        print_and_log("Total Zombie Games: " + str(len(zombie_games)))
        print_and_log("\nWARNING: Some game folders still exist even though Steam thinks the game was uninstalled!")

    missing_games = []
    for game in installed_games:
        if game not in src_games:
            missing_games.append(game)
    if len(missing_games) > 0:
        ask_user = True
        print_and_log("\n--------------------------------------------------------")
        print_and_log("List of Missing Games:")
        print_and_log("--------------------------------------------------------")
        for game in missing_games:
            print_and_log(game)
        print_and_log("--------------------------------------------------------")
        print_and_log("Total Missing Games: " + str(len(missing_games)))
        print_and_log("\nWARNING: Some game folders are missing even though Steam thinks the game is still installed!")

    if ask_user:
        if GUI:
            progress.destroy()
        print_and_log("\nPlease address the warnings above.\nThe backup program will now exit...")
        end_backup()

    # Find all games in destination
    dest_games = []
    stored_games = 0
    print_and_log("\n--------------------------------------------------------", True)
    print_and_log("List of Stored/Uninstalled Games:", True)
    print_and_log("--------------------------------------------------------", True)
    for game in next(walk(destination))[1]:
        if game not in src_games:
            print_and_log(game, True)
            stored_games += 1
        dest_games.append(game)
    print_and_log("--------------------------------------------------------", True)
    print_and_log("Total Stored/Uninstalled Games: " + str(stored_games), True)

    if GUI & GAME:
        game_progress['maximum'] = len(src_games)
        progress.update()

    # Initialize totals to zero
    new_game_total = 0
    deleted_folder_total = 0
    deleted_file_total = 0
    copied_folder_total = 0
    copied_file_total = 0
    overwritten_file_total = 0

    # for game in source:
    print_and_log("\n--------------------------------------------------------")
    print_and_log("                  Backing up Games...")
    print_and_log("--------------------------------------------------------")
    for game in src_games:
        src = source + "/" + game
        dest = destination + "/" + game
        # Initialize counters to zero
        deleted_folder_count = 0
        deleted_file_count = 0
        copied_folder_count = 0
        copied_file_count = 0
        overwritten_file_count = 0
        # If game not in destination, then copy to destination
        if game not in dest_games:
            print_and_log(" + Backing up new Game: " + game)
            copytree(src, dest, dirs_exist_ok=True)
            new_game_total += 1
        # otherwise:
        else:
            print_and_log("Checking: " + game)
            # for folder in destination game:
            folders = ["/"]
            find_folders(dest, folders, dest)
            if GUI & FOLDER:
                folder_progress['value'] = 0
                folder_progress['maximum'] = len(folders)
                progress.update()
            for folder in folders:
                # if folder not in source, then delete from destination
                if not path.exists(src+folder):
                    # If the parent folder was deleted in a previous iteration, then do nothing
                    if path.exists(dest+folder):
                        print_and_log(" - Deleting Folder: " + dest+folder)
                        try:
                            rmtree(dest+folder)
                            deleted_folder_count += 1
                        except OSError as oserr:
                            print_and_log(" ! Could not delete folder: " + dest+folder)
                            print_and_log(" ! Warning message: " + str(oserr))
                # otherwise:
                else:
                    # for file in folder:
                    try:
                        files = next(walk(dest+folder))[2]
                    except StopIteration:
                        files = []
                    if GUI & FILE:
                        file_progress['value'] = 0
                        file_progress['maximum'] = len(files)
                        progress.update()
                    for file in files:
                        clear_cache()
                        # if file not in source, then delete from destination
                        if not path.exists(src+folder+file):
                            print_and_log(" - Deleting File: " + dest+folder+file)
                            remove(dest+folder+file)
                            deleted_file_count += 1
                        if GUI & FILE:
                            file_progress['value'] += 1
                            progress.update()
                if GUI & FOLDER:
                    folder_progress['value'] += 1
                    progress.update()
            # for folder in source game:
            folders = ["/"]
            find_folders(src, folders, src)
            if GUI & FOLDER:
                folder_progress['value'] = 0
                folder_progress['maximum'] = len(folders)
                progress.update()
            for folder in folders:
                # If folder not in destination, then copy to destination
                if not path.exists(dest+folder):
                    print_and_log(" + Copying new Folder: " + dest+folder)
                    copytree(src+folder, dest+folder, dirs_exist_ok=True)
                    copied_folder_count += 1
                # otherwise:
                else:
                    # for file in folder:
                    try:
                        files = next(walk(src+folder))[2]
                    except StopIteration:
                        files = []
                    if GUI & FILE:
                        file_progress['value'] = 0
                        file_progress['maximum'] = len(files)
                        progress.update()
                    for file in files:
                        clear_cache()
                        # if file not in destination, then copy to destination
                        if not path.exists(dest+folder+file):
                            print_and_log(" + Copying new File: " + dest+folder+file)
                            copy2(src+folder+file, dest+folder+file)
                            copied_file_count += 1
                        # else if file in destination and different, then overwrite in destination
                        elif not cmp(src+folder+file, dest+folder+file, shallow=True):
                            print_and_log(" > Overwriting File: " + dest+folder+file)
                            remove(dest+folder+file)
                            copy2(src+folder+file, dest+folder+file)
                            overwritten_file_count += 1
                        if GUI & FILE:
                            file_progress['value'] += 1
                            progress.update()
                if GUI & FOLDER:
                    folder_progress['value'] += 1
                    progress.update()
            # Print counters
            print_and_log("Folder deletions: " + str(deleted_folder_count) +
                          "    File deletions: " + str(deleted_file_count) +
                          "    Folders copied: " + str(copied_folder_count) +
                          "    Files copied: " + str(copied_file_count) +
                          "    Files overwritten: " + str(overwritten_file_count))
            # Increment totals by counters
            deleted_folder_total += deleted_folder_count
            deleted_file_total += deleted_file_count
            copied_folder_total += copied_folder_count
            copied_file_total += copied_file_count
            overwritten_file_total += overwritten_file_count
        print_and_log("--------------------------------------------------------")
        if GUI & GAME:
            game_progress['value'] += 1
            progress.update()
    if GUI:
        progress.destroy()
    # Print totals
    print_and_log("\nTotals:" +
                  "\nFolder deletions: " + str(deleted_folder_total) +
                  "    File deletions: " + str(deleted_file_total) +
                  "    Folders copied: " + str(copied_folder_total) +
                  "    Files copied: " + str(copied_file_total) +
                  "    Files overwritten: " + str(overwritten_file_total) +
                  "    New games: " + str(new_game_total))
    end_backup(0)


if GUI:
    progress = Tk()
    try:
        # Initialize progress bar GUI
        progress.title('Progress')
        progress.attributes("-topmost", True)

        if GUI & GAME:
            (Label(progress, text="Games")).grid(column=0, row=0)
            game_progress = ttk.Progressbar(progress, orient='horizontal', length=300, mode='determinate')
            game_progress.grid(column=0, row=1)

        if GUI & FOLDER:
            (Label(progress, text="Folders")).grid(column=0, row=2)
            folder_progress = ttk.Progressbar(progress, orient='horizontal', length=300, mode='determinate')
            folder_progress.grid(column=0, row=3)

        if GUI & FILE:
            (Label(progress, text="Files")).grid(column=0, row=4)
            file_progress = ttk.Progressbar(progress, orient='horizontal', length=300, mode='determinate')
            file_progress.grid(column=0, row=5)

        progress.after(0, backup)
        progress.mainloop()
    except Exception as err:
        progress.destroy()
        print_and_log("\nFATAL ERROR OCCURRED: " + str(err))
        end_backup()
else:
    try:
        backup()
    except Exception as err:
        print_and_log("\nFATAL ERROR OCCURRED: " + str(err))
        end_backup()
