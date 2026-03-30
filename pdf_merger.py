import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pypdf import PdfWriter

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

BG_DARK       = "#000000"
BG_CARD       = "#0a0a0a"
BG_HOVER      = "#1a1a1a"
ACCENT        = "#ffffff"
ACCENT_LIGHT  = "#cccccc"
TEXT_PRIMARY  = "#ffffff"
TEXT_MUTED    = "#999999"
SUCCESS       = "#ffffff"
DANGER        = "#ffffff"
BORDER        = "#ffffff"

class PDFMergerApp:
    def __init__(self):
        if HAS_DND:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
        self.root.title("PDF Merger")
        self.root.geometry("780x700")
        self.root.minsize(620, 550)
        self.root.configure(bg=BG_DARK)
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - 780) // 2
        y = (self.root.winfo_screenheight() - 700) // 2
        self.root.geometry(f"+{x}+{y}")
        self.pdf_files = []
        self._setup_styles()
        self._build_ui()
        self._bind_drag_and_drop()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=BG_CARD,
            background=ACCENT,
            thickness=18,
            borderwidth=0,
        )

    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG_DARK)
        header.pack(fill="x", padx=24, pady=(18, 4))
        tk.Label(
            header, text="📄  PDF Merger", font=("Segoe UI", 22, "bold"),
            bg=BG_DARK, fg=TEXT_PRIMARY,
        ).pack(side="left")
        tk.Label(
            header, text="Merge PDFs in the order you choose",
            font=("Segoe UI", 10), bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(side="left", padx=(14, 0), pady=(6, 0))

        toolbar = tk.Frame(self.root, bg=BG_DARK)
        toolbar.pack(fill="x", padx=24, pady=(10, 4))
        self._make_button(toolbar, "＋ Add Files",  self._add_files)
        self._make_button(toolbar, "🗑 Remove",      self._remove_files)
        self._make_button(toolbar, "⬆ Move Up",     self._move_up)
        self._make_button(toolbar, "⬇ Move Down",   self._move_down)
        self._make_button(toolbar, "✖ Clear All",   self._clear_all)

        list_frame = tk.Frame(self.root, bg=BORDER, bd=1, relief="flat")
        list_frame.pack(fill="both", expand=True, padx=24, pady=(8, 4))
        inner = tk.Frame(list_frame, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        scrollbar = tk.Scrollbar(inner, orient="vertical", bg=BG_CARD, troughcolor=BG_CARD)
        scrollbar.pack(side="right", fill="y")
        self.file_listbox = tk.Listbox(
            inner,
            selectmode="extended",
            font=("Consolas", 10),
            bg=BG_CARD, fg=TEXT_PRIMARY,
            selectbackground=ACCENT, selectforeground="white",
            activestyle="none",
            highlightthickness=0, bd=0,
            yscrollcommand=scrollbar.set,
        )
        self.file_listbox.pack(fill="both", expand=True, padx=4, pady=4)
        scrollbar.config(command=self.file_listbox.yview)

        if HAS_DND:
            hint = "Drag & drop PDF files here  —  or use the Add Files button"
        else:
            hint = "Use the  ＋ Add Files  button to select PDFs"
        self.hint_label = tk.Label(
            inner, text=hint,
            font=("Segoe UI", 10), bg=BG_CARD, fg=TEXT_MUTED,
        )
        self.hint_label.place(relx=0.5, rely=0.5, anchor="center")
        self.drop_target = inner

        count_frame = tk.Frame(self.root, bg=BG_DARK)
        count_frame.pack(fill="x", padx=24)
        self.count_label = tk.Label(
            count_frame, text="0 files selected",
            font=("Segoe UI", 9), bg=BG_DARK, fg=TEXT_MUTED,
        )
        self.count_label.pack(side="left")

        progress_frame = tk.Frame(self.root, bg=BG_DARK)
        progress_frame.pack(fill="x", padx=24, pady=(6, 2))
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            style="Custom.Horizontal.TProgressbar",
            variable=self.progress_var,
            maximum=100,
        )
        self.progress_bar.pack(fill="x")

        self.status_label = tk.Label(
            self.root, text="Ready", anchor="w",
            font=("Segoe UI", 9), bg=BG_DARK, fg=TEXT_MUTED,
        )
        self.status_label.pack(fill="x", padx=24)

        merge_frame = tk.Frame(self.root, bg=BG_DARK)
        merge_frame.pack(fill="x", padx=24, pady=(8, 18))
        self.merge_btn = tk.Button(
            merge_frame,
            text="🔗  Merge PDFs",
            font=("Segoe UI", 13, "bold"),
            bg="#000000", fg="#ffffff",
            activebackground="#1a1a1a", activeforeground="#ffffff",
            relief="solid", bd=1, cursor="hand2",
            padx=20, pady=8,
            command=self._start_merge,
        )
        self.merge_btn.pack(fill="x")

    def _make_button(self, parent, text, command):
        btn = tk.Button(
            parent, text=text,
            font=("Segoe UI", 9),
            bg=BG_CARD, fg=TEXT_PRIMARY,
            activebackground=BG_HOVER, activeforeground=TEXT_PRIMARY,
            relief="solid", bd=1, cursor="hand2",
            padx=10, pady=4,
            command=command,
        )
        btn.pack(side="left", padx=(0, 6))
        return btn

    def _refresh_listbox(self):
        self.file_listbox.delete(0, tk.END)
        for index, path in enumerate(self.pdf_files, start=1):
            name = os.path.basename(path)
            self.file_listbox.insert(tk.END, f"  {index:>3}.  {name}")
        count = len(self.pdf_files)
        self.count_label.config(text=f"{count} file{'s' if count != 1 else ''} selected")
        if count > 0:
            self.hint_label.place_forget()
        else:
            self.hint_label.place(relx=0.5, rely=0.5, anchor="center")

    def _set_status(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def _set_progress(self, value):
        self.root.after(0, lambda: self.progress_var.set(value))

    def _bind_drag_and_drop(self):
        if not HAS_DND:
            return
        self.drop_target.drop_target_register(DND_FILES)
        self.drop_target.dnd_bind("<<Drop>>", self._on_drop)

    def _on_drop(self, event):
        raw = event.data
        files = []
        current = ""
        in_braces = False
        for char in raw:
            if char == "{":
                in_braces = True
            elif char == "}":
                in_braces = False
                files.append(current.strip())
                current = ""
            elif char == " " and not in_braces:
                if current.strip():
                    files.append(current.strip())
                current = ""
            else:
                current += char
        if current.strip():
            files.append(current.strip())
        added = 0
        for file_path in files:
            if file_path.lower().endswith(".pdf") and file_path not in self.pdf_files:
                self.pdf_files.append(file_path)
                added += 1
        self._refresh_listbox()
        if added:
            self._set_status(f"Dropped {added} PDF file{'s' if added != 1 else ''}")

    def _add_files(self):
        chosen = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
        )
        added = 0
        for file_path in chosen:
            if file_path not in self.pdf_files:
                self.pdf_files.append(file_path)
                added += 1
        self._refresh_listbox()
        if added:
            self._set_status(f"Added {added} file{'s' if added != 1 else ''}")

    def _remove_files(self):
        selected = list(self.file_listbox.curselection())
        if not selected:
            return
        for index in reversed(selected):
            del self.pdf_files[index]
        self._refresh_listbox()
        self._set_status(f"Removed {len(selected)} file{'s' if len(selected) != 1 else ''}")

    def _move_up(self):
        selected = list(self.file_listbox.curselection())
        if not selected or selected[0] == 0:
            return
        for index in selected:
            self.pdf_files[index], self.pdf_files[index - 1] = (
                self.pdf_files[index - 1], self.pdf_files[index]
            )
        self._refresh_listbox()
        for index in selected:
            self.file_listbox.selection_set(index - 1)

    def _move_down(self):
        selected = list(self.file_listbox.curselection())
        if not selected or selected[-1] == len(self.pdf_files) - 1:
            return
        for index in reversed(selected):
            self.pdf_files[index], self.pdf_files[index + 1] = (
                self.pdf_files[index + 1], self.pdf_files[index]
            )
        self._refresh_listbox()
        for index in selected:
            self.file_listbox.selection_set(index + 1)

    def _clear_all(self):
        if not self.pdf_files:
            return
        self.pdf_files.clear()
        self._refresh_listbox()
        self._set_progress(0)
        self._set_status("Cleared all files")

    def _start_merge(self):
        if len(self.pdf_files) < 2:
            messagebox.showwarning("PDF Merger", "Please add at least 2 PDF files to merge.")
            return
        save_path = filedialog.asksaveasfilename(
            title="Save Merged PDF As",
            defaultextension=".pdf",
            initialfile="COMPLIED_TOTAL.pdf",
            filetypes=[("PDF Files", "*.pdf")],
        )
        if not save_path:
            return
        self.merge_btn.config(state="disabled", text="⏳  Merging…")
        self._set_progress(0)
        thread = threading.Thread(target=self._merge_worker, args=(save_path,), daemon=True)
        thread.start()

    def _merge_worker(self, save_path):
        total = len(self.pdf_files)
        writer = PdfWriter()
        try:
            for index, file_path in enumerate(self.pdf_files):
                name = os.path.basename(file_path)
                self._set_status(f"Reading ({index + 1}/{total}):  {name}")
                writer.append(file_path)
                percent = ((index + 1) / total) * 90
                self._set_progress(percent)
            self._set_status("Writing merged PDF to disk…")
            with open(save_path, "wb") as output_file:
                writer.write(output_file)
            self._set_progress(100)
            self._set_status(f"✅  Done!  Saved to {os.path.basename(save_path)}")
            self.root.after(0, lambda: messagebox.showinfo(
                "PDF Merger",
                f"Successfully merged {total} files!\n\nSaved to:\n{save_path}",
            ))
        except Exception as error:
            self._set_status(f"❌  Error: {error}")
            self.root.after(0, lambda: messagebox.showerror(
                "PDF Merger – Error",
                f"An error occurred during merge:\n\n{error}",
            ))
        finally:
            writer.close()
            self.root.after(0, lambda: self.merge_btn.config(
                state="normal", text="🔗  Merge PDFs"
            ))

if __name__ == "__main__":
    app = PDFMergerApp()
    app.root.mainloop()
