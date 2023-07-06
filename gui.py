import os
import subprocess
import threading
from tkinter import *
from tkinter import filedialog
from tkinter import ttk

import find_duplicates
import logging


LOG_FILE = 'find_dupes_logs.log'

logging.basicConfig(filename=LOG_FILE, encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__name__)


def open_log():
    try:
        os.startfile(LOG_FILE)
    except Exception as e:
        print(e)


def clear_log():
    try:
        open(LOG_FILE, 'w').close()
    except Exception as e:
        print(e)


class App:

    def __init__(self):
        self.paths = []
        self.search_mode = 'f'
        self.searching = False
        self.stop_event = None
        self.pause_event = None
        self.results = {}
        self.loading_results = False

        self.root = Tk()
        self.root.title("Find duplicates app")
        self.root.minsize(500, 400)

        self.left_frame = ttk.Frame(self.root, padding=10)
        self.left_frame.grid(row=0, column=0, sticky='n')

        self.right_frame = ttk.Frame(self.root, padding=10)
        self.right_frame.grid(row=0, column=1, sticky='n')

        # LEFT FRAME WIDGETS

        # PATHS TOOLBAR

        self.paths_toolbar = ttk.Frame(self.left_frame)
        self.paths_toolbar.grid(row=0, column=0)

        ttk.Label(self.paths_toolbar, text="Find duplicates in:")\
            .grid(row=0, column=0, sticky='w')

        self.paths_toolbar_inner = ttk.Frame(self.paths_toolbar)
        self.paths_toolbar_inner.grid(row=1, column=0, sticky='we')

        ttk.Button(self.paths_toolbar_inner, text="Add a path to search", command=self.open_path, width=20) \
            .grid(row=0, column=0, sticky='w')

        ttk.Button(self.paths_toolbar_inner, text="Clear search paths", command=self.clear_paths, width=20) \
            .grid(row=0, column=1, sticky='e')

        self.list_paths = ttk.Treeview(self.paths_toolbar, selectmode='browse', height=2)
        self.list_paths['columns'] = ("path",)
        self.list_paths.column("#0", width=0, stretch=NO)
        self.list_paths.column("path", width=300, anchor=W, stretch=False)

        self.list_paths.heading("#0", text="", anchor=W)
        self.list_paths.heading("path", text="Path", anchor=W)

        self.list_paths.grid(row=2, column=0, sticky='we')

        self.sb_y_list_paths = ttk.Scrollbar(self.paths_toolbar, orient='vertical', command=self.list_paths.yview)
        self.sb_y_list_paths.grid(row=2, column=1, sticky='ens')
        self.sb_x_list_paths = ttk.Scrollbar(self.paths_toolbar, orient='horizontal', command=self.list_paths.xview)
        self.sb_x_list_paths.grid(row=3, column=0, sticky='wens')
        self.list_paths.configure(xscrollcommand=self.sb_x_list_paths.set, yscrollcommand=self.sb_y_list_paths.set)

        self.list_paths.bind("<Delete>", self.on_delete_path)

        self.combo_items = ('by name', 'by name and size', 'by content (images only)')
        self.combo = ttk.Combobox(self.left_frame, values=self.combo_items, state='readonly', width=30)
        self.combo.set(self.combo_items[0])
        self.combo.grid(row=1, column=0, sticky='w', pady=(10, 0))

        self.combo.bind('<<ComboboxSelected>>', self.set_checkbox)

        self.no_ext = IntVar()
        self.check = ttk.Checkbutton(self.left_frame, text='ignore extensions (check for unpacked archives)',
                                     variable=self.no_ext, onvalue=1, offvalue=0)
        self.check.grid(row=2, column=0, sticky='w')

        # SEARCH TOOLBAR

        self.search_toolbar = ttk.Frame(self.left_frame)
        self.search_toolbar.grid(row=3, column=0, sticky='w', pady=(20, 0))

        self.search_button = ttk.Button(self.search_toolbar, text="Search", command=self.search, width=20)
        self.search_button.grid(row=0, column=0, sticky='w')

        self.pause_button = ttk.Button(self.search_toolbar, text="Pause", command=self.pause, width=20)
        self.pause_button.grid(row=0, column=1, sticky='w')

        ttk.Button(self.search_toolbar, text="Clear results", command=self.clear, width=20) \
            .grid(row=1, column=0, sticky='w')

        self.progressbar = ttk.Progressbar(self.search_toolbar, orient=HORIZONTAL, length=200, mode='determinate')
        self.progressbar.grid(row=2, column=0, columnspan=2, sticky='we', pady=(10, 0))

        self.progress_label = ttk.Label(self.search_toolbar, text="Ready")
        self.progress_label.grid(row=3, column=0, sticky='we')

        # IMPORT TOOLBAR

        self.import_toolbar = ttk.Frame(self.left_frame)
        self.import_toolbar.grid(row=4, column=0, sticky='w', pady=(20, 0))

        ttk.Button(self.import_toolbar, text="Save results", command=self.save_results, width=20)\
            .grid(row=0, column=0, sticky='w')

        ttk.Button(self.import_toolbar, text="Load results", command=self.load_results, width=20)\
            .grid(row=0, column=1, sticky='w')

        # LOGS TOOLBAR

        self.logs_toolbar = ttk.Frame(self.left_frame)
        self.logs_toolbar.grid(row=5, column=0, sticky='w', pady=(40, 0))

        ttk.Button(self.logs_toolbar, text="Open Logs", command=open_log, width=20) \
            .grid(row=0, column=0, sticky='w')

        ttk.Button(self.logs_toolbar, text="Clear Logs", command=clear_log, width=20) \
            .grid(row=0, column=1, sticky='w')

        # RIGHT FRAME WIDGETS

        self.tree = ttk.Treeview(self.right_frame, selectmode='browse')
        self.tree['columns'] = ("filename", "path", "key")  # key used to id item in dict in order to delete it
        self.tree.column("#0", width=0, )
        self.tree.column("filename", anchor=W, width=120)
        self.tree.column("path", anchor=W, width=500)
        self.tree.column("key", width=0, stretch=NO)

        self.tree.heading("#0", text="", anchor=W)
        self.tree.heading("filename", text="Filename", anchor=W)
        self.tree.heading("path", text="Path", anchor=CENTER)

        self.tree.grid(row=0, column=0, sticky='wens')

        self.sb_y_tree = ttk.Scrollbar(self.right_frame, orient='vertical', command=self.tree.yview)
        self.sb_y_tree.grid(row=0, column=1, sticky='ens')

        self.tree.configure(yscrollcommand=self.sb_y_tree.set)

        # bind event on clicks
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)
        self.tree.bind("<Delete>", self.on_delete)

        # RIGHT TOOLBAR

        self.toolbar2 = ttk.Frame(self.right_frame)
        self.toolbar2.grid(row=1, column=0, sticky='w')

        ttk.Label(self.toolbar2, text="Left Mouse Double Click - opens location") \
            .grid(row=0, column=0, sticky='w')

        ttk.Button(self.toolbar2, text="Open Location", command=lambda: self.open_location()) \
            .grid(row=0, column=1, sticky='wens')

        ttk.Label(self.toolbar2, text="Right Mouse Single Click - opens file") \
            .grid(row=1, column=0, sticky='w')

        ttk.Button(self.toolbar2, text="Open File", command=lambda: self.open_file()) \
            .grid(row=1, column=1, sticky='wens')

        ttk.Label(self.toolbar2, text="Delete - removes record from table (but not from disk)") \
            .grid(row=2, column=0, sticky='w')

        ttk.Button(self.toolbar2, text="Remove result", command=lambda: self.remove_result()) \
            .grid(row=2, column=1, sticky='wens')

        self.root.mainloop()

    def open_path(self):
        self.list_paths.delete(*self.list_paths.get_children())

        folder = filedialog.askdirectory(initialdir="/", title="Select file")
        if folder:
            self.paths.append(folder)

        for i in range(len(self.paths)):
            self.list_paths.insert(parent='', index='end', iid=str(i), text=self.paths[i], values=(self.paths[i],))

    def clear_paths(self):
        self.paths.clear()
        self.list_paths.delete(*self.list_paths.get_children())

    def on_delete_path(self, _event):
        if self.list_paths.selection():
            selected_item = self.list_paths.selection()[0]

            del self.paths[int(selected_item)]

            self.list_paths.delete(*self.list_paths.get_children())
            for i in range(len(self.paths)):
                self.list_paths.insert(parent='', index='end', iid=str(i), text=self.paths[i], values=(self.paths[i],))

    def set_checkbox(self, _event):
        if self.combo.get() == self.combo_items[0]:
            self.check.grid(row=2, column=0, sticky='w')
        else:
            self.check.grid_forget()

    def clear(self):
        self.results.clear()
        self.tree.delete(*self.tree.get_children())
        self.progressbar['value'] = 0
        self.progress_label['text'] = 'Ready'

    def search(self):
        # search or stop if already searching

        if self.searching:
            # trigger the stop event
            self.stop_event.set()
            return
        else:
            self.searching = True
            self.search_button["text"] = "Stop"

        self.results.clear()
        self.tree.delete(*self.tree.get_children())
        self.progress_label['text'] = 'Searching'

        if self.combo.get() == self.combo_items[0]:
            if self.no_ext.get():
                self.search_mode = 'fi'
            else:
                self.search_mode = 'f'
        elif self.combo.get() == self.combo_items[1]:
            self.search_mode = 'fs'
        else:
            self.search_mode = 'im'

        threading.Thread(target=lambda: self.search_async(self.search_mode, self.paths)).start()

    def search_async(self, mode, path):

        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()

        self.search_run(mode, path)

    def search_run(self, mode, path):

        if mode == 'fi':
            find_dupes = find_duplicates.find_duplicates_by_name(path, self.stop_event, True)
        elif mode == 'f':
            find_dupes = find_duplicates.find_duplicates_by_name(path, self.stop_event)
        elif mode == 'fs':
            find_dupes = find_duplicates.find_duplicates_by_name_and_size(path, self.stop_event)
        else:
            find_dupes = find_duplicates.find_duplicate_images(path, self.stop_event)

        for _ in find_dupes:

            self.pause_event.wait()

            if isinstance(_, dict):

                self.results = _
                self.populate_search_results()  # messy but it works
                # tkinter: not multi-threading friendly
                # generally only main Thread should make changes to widgets
                # by periodically making updates using a Queue through after()
                #
                # at least ensure that Treeview (and related widgets) aren't used with loading while searching

            else:
                self.progressbar['value'] = _
                self.root.update_idletasks()

    def populate_search_results(self):

        if self.loading_results:  # skip dict re-writing on load from file
            self.loading_results = False
        else:
            # Treeview doesn't handle tuples as values => re-write dict keys so that items can be deleted in reverse
            if self.search_mode == 'fs' or self.search_mode == 'im':
                tmp_dict = {}
                for i, k in enumerate(self.results):
                    tmp_dict[i] = self.results[k]

                self.results = tmp_dict

        i = 0
        for dupe in self.results:
            self.tree.insert(parent='', index='end', iid=i, text='', values=(dupe, ''))

            j = i + 1
            for d in self.results[dupe]:
                self.tree.insert(parent=f'{i}', index='end', iid=j, text='', values=('', d))
                j += 1
            i = j + 1

        self.progressbar['value'] = 100
        self.progress_label['text'] = 'Finished'
        self.searching = False
        self.search_button['text'] = 'Search'
        if self.stop_event:
            self.stop_event.clear()

    def pause(self):
        if self.searching:

            if self.pause_event.is_set():
                self.pause_event.clear()
                self.progress_label['text'] = 'Paused'
                self.pause_button['text'] = 'Resume'
                self.search_button['state'] = 'disabled'
            else:
                self.pause_event.set()
                self.progress_label['text'] = 'Searching'
                self.pause_button['text'] = 'Pause'
                self.search_button['state'] = 'normal'

    # TODO? add search for specific files / files from a dir (+show missing dupes)
    # TODO avoid rescanning user input subdirectories (check substring among paths)

    def on_double_click(self, _event):
        self.open_location()

    def on_right_click(self, event):
        # select row under mouse
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)

        self.open_file()

    def on_delete(self, _event):
        self.remove_result()

    def open_location(self):
        selected_item = self.tree.selection()[0]

        parent_iid = self.tree.parent(selected_item)
        if parent_iid:
            path = self.tree.item(selected_item, "values")[1]
            subprocess.Popen(r'explorer /select,' + path)

    def open_file(self):
        selected_item = self.tree.selection()[0]

        parent_iid = self.tree.parent(selected_item)
        if parent_iid:
            path = self.tree.item(selected_item, "values")[1]

            if os.path.exists(path):
                os.startfile(path)
            else:
                logger.warning(f"{path} does not exist.")

    def remove_result(self):
        if self.tree.selection():
            selected_item = self.tree.selection()[0]

            parent__iid = self.tree.parent(selected_item)
            if parent__iid:
                if self.search_mode in ['fs', 'im']:
                    k = int(self.tree.item(parent__iid, "values")[0])
                else:
                    k = self.tree.item(parent__iid, "values")[0]

                val = self.tree.item(selected_item, "values")[1]

                self.results[k].remove(val)
            else:
                if self.search_mode in ['fs', 'im']:
                    k = int(self.tree.item(selected_item, "values")[0])
                else:
                    k = self.tree.item(selected_item, "values")[0]
                self.results.pop(k, None)

            self.tree.delete(selected_item)

    def save_results(self):
        fn = filedialog.asksaveasfilename(initialdir="/", initialfile="duplicate_results.data", title="Select file")
        if fn:
            self.results['search_mode'] = self.search_mode
            with open(fn, 'w') as f:
                print(self.results, file=f)
            del self.results['search_mode']

    def load_results(self):

        if self.searching:
            return

        self.tree.delete(*self.tree.get_children())
        fn = filedialog.askopenfilename(initialdir="/", initialfile="duplicate_results.data", title="Select file")

        try:
            with open(fn, 'r') as f:
                self.results = eval(f.read())
                self.search_mode = self.results['search_mode']
                del self.results['search_mode']

                if not isinstance(self.results, dict):
                    self.results = {}

                self.loading_results = True  # skip the dict re-writing
                self.populate_search_results()

        except (OSError, SyntaxError, NameError):
            self.results = {}
        except KeyError:
            self.results = {}
            logger.warning('wrong file to load: file contents must be a python dictionary with key: search_mode')


if __name__ == "__main__":
    app = App()
