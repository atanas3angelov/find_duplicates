# find_duplicates
Small app to find duplicate files

purpose: to free space by finding (and removing) duplicate files (and images) by providing directories to be scanned  
The app only shows potential duplicates (and their location); it does not delete them automatically.
The delete decision and action should be made by a person - the app only provides convenient way to view the files and their location (for ease of deleting).

duplicate criteria to find matches:
- filename (+/- extension, if one searches for archives that have been unpacked into a directory with the same name)
- filename and file size
- image content (5 pixels are checked - 4 corners and center)

programming language: Python + tkinter (and Pillow for opening images) - see requirements.txt  
IDE: PyCharm Community

Target OS: Windows (change the button handlers for other OS)  
The executable in dist was created using pyinstaller.
