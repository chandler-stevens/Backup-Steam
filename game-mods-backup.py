from shutil import copytree, copy2, rmtree
from os import walk, path, remove, system, makedirs
from filecmp import clear_cache, cmp
from tkinter import Tk, ttk, Label
from pathlib import Path
from datetime import datetime
from time import sleep

# Shows Game, Folder, and File drill-down progress bars,
#  but makes the backup take 4 times longer when set to True.
GUI = True

# Define global variable for log string variable
log_dir = str(Path(__file__).resolve().parent)+"\\logs"
log_file_path = log_dir+"\\Mods "+str(datetime.now()).split(".")[0].replace(":", "-")+".log"
log = "Backup started at "+str(datetime.now()).split(".")[0]+"\n\n"
print(log)


# Helper function to print to console and add to log file string variable
def print_and_log(text):
    global log
    log += text+"\n"
    print(text)


# Helper function to write to log file
def write_log(text):
    with open(log_file_path, "w") as log_file:
        log_file.write(text)


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
    source = "C:/Steam/steamapps/common"
    destination = "F:/Game-Mods"

    # Check paths
    if not path.exists(source):
        if GUI:
            progress.destroy()
        write_log("FATAL ERROR: Could not find source path:\n"+source+"\n")
        exit(1)
    if not path.exists(destination):
        if GUI:
            progress.destroy()
        write_log("FATAL ERROR: Could not find destination path:\n"+destination+"\n")
        exit(1)

    # Kill Steam to prevent file changes during backup
    print_and_log("Closing Steam and sleeping for 3 seconds...\n")
    system("taskkill /f /im steam.exe 2>nul")
    sleep(3)

    # Find all games in source that have a MyMods sub-folder
    src_games = []
    print_and_log("\nList of Installed Games with Mods:")
    for game in next(walk(source))[1]:
        if path.exists(source+"/"+game+"/MyMods"):
            src_games.append(game)
            print_and_log(game)
    if len(src_games) <= 0:
        print_and_log("WARNING: <No games with a MyMods sub-folder are installed currently>")

    # Find all games in destination
    dest_games = []
    stored_games = 0
    print_and_log("\nList of Stored/Uninstalled Games with Mods:")
    for game in next(walk(destination))[1]:
        if game not in src_games:
            print_and_log(game)
            stored_games += 1
        dest_games.append(game)
    if stored_games <= 0:
        print_and_log("<No games with a MyMods sub-folder are stored/uninstalled currently>")

    if GUI:
        game_progress['maximum'] = len(src_games)
        progress.update()

    # for game in C:
    print_and_log("\n--------------------------------------------------------")
    print_and_log("                Backing up Game Mods...")
    print_and_log("--------------------------------------------------------")
    for game in src_games:
        src = source + "/" + game + "/MyMods"
        dest = destination + "/" + game + "/MyMods"
        # If game not in F, then copy to F
        if game not in dest_games:
            print_and_log(" + Backing up New Game Mods: "+game)
            copytree(src, dest, dirs_exist_ok=True)
        # otherwise:
        else:
            if not path.exists(destination):
                if GUI:
                    progress.destroy()
                write_log("FATAL ERROR: Could not find dest path:\n" + dest + "\n")
                exit(1)
            print_and_log("Checking: "+game)
            # for folder in F game:
            folders = ["/"]
            find_folders(dest, folders, dest)
            if GUI:
                folder_progress['value'] = 0
                folder_progress['maximum'] = len(folders)
                progress.update()
            for folder in folders:
                # if folder not in C, then delete from F
                if not path.exists(src+folder):
                    print_and_log(" - Deleting Folder: "+dest+folder)
                    rmtree(dest+folder)
                # otherwise:
                else:
                    # for file in folder:
                    try:
                        files = next(walk(dest+folder))[2]
                    except StopIteration:
                        files = []
                    if GUI:
                        file_progress['value'] = 0
                        file_progress['maximum'] = len(files)
                        progress.update()
                    for file in files:
                        clear_cache()
                        # if file not in C, then delete from F
                        if not path.exists(src+folder+file):
                            print_and_log(" - Deleting File: "+dest+folder+file)
                            remove(dest+folder+file)
                        if GUI:
                            file_progress['value'] += 1
                            progress.update()
                if GUI:
                    folder_progress['value'] += 1
                    progress.update()
            # for folder in C game:
            folders = ["/"]
            find_folders(src, folders, src)
            if GUI:
                folder_progress['value'] = 0
                folder_progress['maximum'] = len(folders)
                progress.update()
            for folder in folders:
                # If folder not in F, then copy to F
                if not path.exists(dest+folder):
                    print_and_log(" + Copying New Folder: "+dest+folder)
                    copytree(src+folder, dest+folder, dirs_exist_ok=True)
                # otherwise:
                else:
                    # for file in folder:
                    try:
                        files = next(walk(src+folder))[2]
                    except StopIteration:
                        files = []
                    if GUI:
                        file_progress['value'] = 0
                        file_progress['maximum'] = len(files)
                        progress.update()
                    for file in files:
                        clear_cache()
                        # if file not in F, then copy to F
                        if not path.exists(dest+folder+file):
                            print_and_log(" + Copying New File: "+dest+folder+file)
                            copy2(src+folder+file, dest+folder+file)
                        # else if file in F and different, then overwrite in F
                        elif not cmp(src+folder+file, dest+folder+file, shallow=True):
                            print_and_log(" > Overwriting File: "+dest+folder+file)
                            remove(dest+folder+file)
                            copy2(src+folder+file, dest+folder+file)
                        if GUI:
                            file_progress['value'] += 1
                            progress.update()
                if GUI:
                    folder_progress['value'] += 1
                    progress.update()
        print_and_log("--------------------------------------------------------")
        if GUI:
            game_progress['value'] += 1
            progress.update()
    print_and_log("\nBackup finished at "+str(datetime.now()).split(".")[0]+"\nDone.")
    write_log(log)
    if GUI:
        progress.destroy()
    exit(0)


if GUI:
    # Initialize progress bar GUI
    progress = Tk()
    progress.title('Progress')
    progress.attributes("-topmost", True)

    (Label(progress, text="Games")).grid(column=0, row=0)
    game_progress = ttk.Progressbar(progress, orient='horizontal', length=300, mode='determinate')
    game_progress.grid(column=0, row=1)

    (Label(progress, text="Folders")).grid(column=0, row=2)
    folder_progress = ttk.Progressbar(progress, orient='horizontal', length=300, mode='determinate')
    folder_progress.grid(column=0, row=3)

    (Label(progress, text="Files")).grid(column=0, row=4)
    file_progress = ttk.Progressbar(progress, orient='horizontal', length=300, mode='determinate')
    file_progress.grid(column=0, row=5)

    progress.after(0, backup)
    progress.mainloop()
else:
    backup()
