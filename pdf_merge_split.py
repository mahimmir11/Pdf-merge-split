import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import os


class PDFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Merger & Splitter")
        root.geometry("900x500+300+200")
        root.resizable(False, False)

        # Variables
        self.pdf_files = []
        self.output_filename = tk.StringVar(value="output.pdf")
        self.selected_pdf = tk.StringVar()
        self.split_mode = tk.StringVar(value="range")  # "range" or "pages"
        self.page_ranges = []
        self.total_pages = 0
        self.selected_pages = []

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Merge Tab
        self.merge_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.merge_tab, text="Merge PDFs")
        self.setup_merge_tab()

        # Split Tab
        self.split_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.split_tab, text="Split PDF")
        self.setup_split_tab()

        # About Tab
        self.about_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.about_tab, text="About")
        self.setup_about_tab()

    def setup_merge_tab(self):
        # File list frame
        file_frame = ttk.LabelFrame(self.merge_tab, text="PDF Files to Merge")
        file_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Listbox for files
        self.file_listbox = tk.Listbox(file_frame, selectmode=tk.SINGLE)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        # Buttons frame
        button_frame = ttk.Frame(self.merge_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        # Add/Remove buttons
        add_button = ttk.Button(button_frame, text="Add PDF", command=self.add_pdf)
        add_button.pack(side=tk.LEFT, padx=5)

        remove_button = ttk.Button(button_frame, text="Remove Selected", command=self.remove_pdf)
        remove_button.pack(side=tk.LEFT, padx=5)

        up_button = ttk.Button(button_frame, text="Move Up", command=self.move_up)
        up_button.pack(side=tk.LEFT, padx=5)

        down_button = ttk.Button(button_frame, text="Move Down", command=self.move_down)
        down_button.pack(side=tk.LEFT, padx=5)

        # Output frame
        output_frame = ttk.Frame(self.merge_tab)
        output_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(output_frame, text="Output Filename:").pack(side=tk.LEFT)
        output_entry = ttk.Entry(output_frame, textvariable=self.output_filename)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Merge button
        merge_button = ttk.Button(self.merge_tab, text="Merge PDFs", command=self.merge_pdfs)
        merge_button.pack(pady=10)

    def setup_split_tab(self):
        # Select PDF frame
        select_frame = ttk.LabelFrame(self.split_tab, text="Select PDF to Split")
        select_frame.pack(fill=tk.X, padx=10, pady=10)

        # File selection
        file_button = ttk.Button(select_frame, text="Browse PDF", command=self.select_pdf_to_split)
        file_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.selected_pdf_label = ttk.Label(select_frame, text="No file selected")
        self.selected_pdf_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Split mode selection
        mode_frame = ttk.LabelFrame(self.split_tab, text="Split Mode")
        mode_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Radiobutton(mode_frame, text="By Range", variable=self.split_mode,
                        value="range", command=self.update_split_ui).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="By Pages", variable=self.split_mode,
                        value="pages", command=self.update_split_ui).pack(anchor=tk.W)

        # Range UI Frame
        self.range_frame = ttk.LabelFrame(self.split_tab, text="Page Ranges")
        self.range_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Range input frame
        self.range_input_frame = ttk.Frame(self.range_frame)
        self.range_input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(self.range_input_frame, text="Range (e.g., 1-5):").pack(side=tk.LEFT)
        self.range_entry = ttk.Entry(self.range_input_frame)
        self.range_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        add_range_btn = ttk.Button(self.range_input_frame, text="Add Range", command=self.add_range)
        add_range_btn.pack(side=tk.LEFT, padx=5)

        # Ranges listbox
        self.ranges_listbox = tk.Listbox(self.range_frame, height=4)
        self.ranges_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Remove range button
        remove_range_btn = ttk.Button(self.range_frame, text="Remove Selected Range", command=self.remove_range)
        remove_range_btn.pack(pady=5)

        # Pages UI Frame (initially hidden)
        self.pages_frame = ttk.LabelFrame(self.split_tab, text="Select Pages")
        self.pages_canvas = tk.Canvas(self.pages_frame)
        self.scrollbar = ttk.Scrollbar(self.pages_frame, orient="vertical", command=self.pages_canvas.yview)
        self.pages_container = ttk.Frame(self.pages_canvas)

        self.pages_container.bind(
            "<Configure>",
            lambda e: self.pages_canvas.configure(
                scrollregion=self.pages_canvas.bbox("all")
            )
        )

        self.pages_canvas.create_window((0, 0), window=self.pages_container, anchor="nw")
        self.pages_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.pages_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Output frame
        output_frame = ttk.Frame(self.split_tab)
        output_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(output_frame, text="Output Filename:").pack(side=tk.LEFT)
        self.split_output_entry = ttk.Entry(output_frame, textvariable=self.output_filename)
        self.split_output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Split button
        split_button = ttk.Button(self.split_tab, text="Split PDF", command=self.split_pdf)
        split_button.pack(pady=10)

        # Initially hide pages frame
        self.pages_frame.pack_forget()

    def setup_about_tab(self):
        about_text = """
        PDF Merger & Splitter

        Version 2.0

        Features:
        - Merge multiple PDF files into one
        - Split PDF by page ranges or individual pages
        - Simple and intuitive interface

        Created with Python, Tkinter, and PyPDF2
        """

        about_label = ttk.Label(self.about_tab, text=about_text, justify=tk.LEFT)
        about_label.pack(padx=10, pady=10, anchor=tk.W)

    def update_split_ui(self):
        if self.split_mode.get() == "range":
            self.pages_frame.pack_forget()
            self.range_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        else:
            self.range_frame.pack_forget()
            self.pages_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self.update_pages_ui()

    def update_pages_ui(self):
        # Clear existing page checkboxes
        for widget in self.pages_container.winfo_children():
            widget.destroy()

        if not self.selected_pdf.get() or self.total_pages == 0:
            return

        # Create checkboxes for each page
        self.selected_pages = [1] * self.total_pages  # 1=selected, 0=not selected
        for i in range(self.total_pages):
            var = tk.IntVar(value=1)
            cb = ttk.Checkbutton(self.pages_container,
                                 text=f"Page {i + 1}",
                                 variable=var,
                                 command=lambda v=var, idx=i: self.toggle_page(v, idx))
            cb.pack(anchor=tk.W)

    def toggle_page(self, var, index):
        self.selected_pages[index] = var.get()

    def add_pdf(self):
        files = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if files:
            for file in files:
                if file not in self.pdf_files:
                    self.pdf_files.append(file)
                    self.file_listbox.insert(tk.END, os.path.basename(file))

    def remove_pdf(self):
        selected = self.file_listbox.curselection()
        if selected:
            index = selected[0]
            self.file_listbox.delete(index)
            self.pdf_files.pop(index)

    def move_up(self):
        selected = self.file_listbox.curselection()
        if selected and selected[0] > 0:
            index = selected[0]
            # Swap in list
            self.pdf_files[index], self.pdf_files[index - 1] = self.pdf_files[index - 1], self.pdf_files[index]
            # Update listbox
            item = self.file_listbox.get(index)
            self.file_listbox.delete(index)
            self.file_listbox.insert(index - 1, item)
            self.file_listbox.select_set(index - 1)

    def move_down(self):
        selected = self.file_listbox.curselection()
        if selected and selected[0] < len(self.pdf_files) - 1:
            index = selected[0]
            # Swap in list
            self.pdf_files[index], self.pdf_files[index + 1] = self.pdf_files[index + 1], self.pdf_files[index]
            # Update listbox
            item = self.file_listbox.get(index)
            self.file_listbox.delete(index)
            self.file_listbox.insert(index + 1, item)
            self.file_listbox.select_set(index + 1)

    def merge_pdfs(self):
        if not self.pdf_files:
            messagebox.showerror("Error", "No PDF files selected")
            return

        output_file = filedialog.asksaveasfilename(
            title="Save merged PDF as",
            defaultextension=".pdf",
            initialfile=self.output_filename.get(),
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if not output_file:
            return

        try:
            merger = PdfMerger()

            for pdf in self.pdf_files:
                merger.append(pdf)

            merger.write(output_file)
            merger.close()

            messagebox.showinfo("Success", f"PDFs merged successfully!\nSaved as: {output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to merge PDFs:\n{str(e)}")

    def select_pdf_to_split(self):
        file = filedialog.askopenfilename(
            title="Select PDF to split",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file:
            self.selected_pdf.set(file)
            self.selected_pdf_label.config(text=os.path.basename(file))
            try:
                with open(file, "rb") as f:
                    reader = PdfReader(f)
                    self.total_pages = len(reader.pages)
                    messagebox.showinfo("Info", f"PDF loaded with {self.total_pages} pages")
                    if self.split_mode.get() == "pages":
                        self.update_pages_ui()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read PDF:\n{str(e)}")

    def add_range(self):
        range_text = self.range_entry.get().strip()
        if not range_text:
            messagebox.showerror("Error", "Please enter a page range")
            return

        try:
            # Validate range format
            parts = range_text.split('-')
            if len(parts) != 2:
                raise ValueError("Range should be in format 'start-end'")

            start = int(parts[0])
            end = int(parts[1])

            if start < 1 or end > self.total_pages:
                raise ValueError(f"Range must be between 1 and {self.total_pages}")

            if start > end:
                raise ValueError("Start page must be less than or equal to end page")

            self.page_ranges.append((start, end))
            self.ranges_listbox.insert(tk.END, f"Pages {start}-{end}")
            self.range_entry.delete(0, tk.END)
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid range:\n{str(e)}")

    def remove_range(self):
        selected = self.ranges_listbox.curselection()
        if selected:
            index = selected[0]
            self.ranges_listbox.delete(index)
            self.page_ranges.pop(index)

    def split_pdf(self):
        if not self.selected_pdf.get():
            messagebox.showerror("Error", "No PDF file selected")
            return

        try:
            input_pdf = PdfReader(open(self.selected_pdf.get(), "rb"))
            base_name = os.path.splitext(os.path.basename(self.selected_pdf.get()))[0]
            output_dir = filedialog.askdirectory(title="Select directory to save split PDFs")

            if not output_dir:
                return

            success_count = 0
            output_files = []

            if self.split_mode.get() == "range":
                if not self.page_ranges:
                    messagebox.showerror("Error", "No page ranges specified")
                    return

                for i, (start, end) in enumerate(self.page_ranges):
                    output_name = f"{base_name}_split_{i + 1}.pdf"
                    output_path = os.path.join(output_dir, output_name)

                    # Handle duplicate filenames
                    counter = 1
                    while os.path.exists(output_path):
                        output_name = f"{base_name}_split_{i + 1}_{counter}.pdf"
                        output_path = os.path.join(output_dir, output_name)
                        counter += 1

                    writer = PdfWriter()
                    for page in range(start - 1, end):
                        if page < len(input_pdf.pages):
                            writer.add_page(input_pdf.pages[page])
                        else:
                            messagebox.showwarning("Warning", f"Page {page + 1} is beyond document length")
                            break

                    with open(output_path, "wb") as out:
                        writer.write(out)

                    output_files.append(output_name)
                    success_count += 1
            else:
                # Split by selected pages - create one PDF with all selected pages
                if not any(self.selected_pages):
                    messagebox.showerror("Error", "No pages selected")
                    return

                output_name = f"{base_name}_selected_pages.pdf"
                output_path = os.path.join(output_dir, output_name)

                # Handle duplicate filename
                counter = 1
                while os.path.exists(output_path):
                    output_name = f"{base_name}_selected_pages_{counter}.pdf"
                    output_path = os.path.join(output_dir, output_name)
                    counter += 1

                writer = PdfWriter()
                for i, selected in enumerate(self.selected_pages):
                    if selected:
                        writer.add_page(input_pdf.pages[i])

                with open(output_path, "wb") as out:
                    writer.write(out)

                output_files.append(output_name)
                success_count = 1

            # Show success message with list of created files
            if success_count > 0:
                files_list = "\n".join(output_files)
                messagebox.showinfo(
                    "Success",
                    f"PDF split successfully!\n\nCreated {success_count} file(s):\n{files_list}\n\nSaved in: {output_dir}"
                )
            else:
                messagebox.showwarning("Warning", "No files were created")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to split PDF:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFApp(root)
    root.mainloop()