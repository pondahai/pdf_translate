import os
import requests
import pytesseract
from PIL import Image, ImageFilter
from pdf2image import convert_from_path
from dotenv import load_dotenv
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 載入環境變數
load_dotenv()

# OpenAI API設定
API_URL = r"https://api.groq.com/openai/v1"
API_KEY = os.getenv('API_KEY')
MODEL_NAME = 'gemma2-9b-it'

class FileProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Processor")
        self.root.geometry("400x250")

        # 新增OCR語言選項下拉選單
        self.ocr_lang_var = tk.StringVar(self.root)
        self.ocr_lang_var.set("eng")  # 預設為英文
        self.ocr_lang_options = ["", "eng", "chi_tra", "chi_sim", "jpn", "kor"]
        self.ocr_lang_dropdown = ttk.OptionMenu(self.root, self.ocr_lang_var, *self.ocr_lang_options)
        self.ocr_lang_dropdown.pack(pady=10)

        # 新增翻譯選項
        self.translate_var = tk.BooleanVar(self.root, value=True)  # 預設為勾選
        self.translate_checkbutton = ttk.Checkbutton(self.root, text="Translate to zh_TW", variable=self.translate_var)
        self.translate_checkbutton.pack(pady=5)

        self.label = tk.Label(root, text="Drag and drop a file here")
        self.label.pack(pady=20)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=20)

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

        # 這裡加入你的log框架
        self.log_frame = tk.Frame(self.root)

        scrollbar = tk.Scrollbar(self.log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text_area = tk.Text(self.log_frame)
        self.log_text_area.pack(fill=tk.BOTH, expand=1)
        self.log_text_area.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text_area.yview)

        self.log_frame.pack(pady=20)

    def log_info(self, message):
        self.log_text_area.insert(tk.END, f"[INFO] {message}\n")
        self.log_text_area.see(tk.END)  # 移動視窗到最後一行

    def replace_extension_and_avoid_duplicate(self, full_path, new_extension):
        file_name_with_extension = os.path.basename(full_path)
        file_name, _ = os.path.splitext(file_name_with_extension)
        new_file_name = file_name + new_extension
        new_full_path = os.path.join(os.path.dirname(full_path), new_file_name)

        counter = 1
        while os.path.exists(new_full_path):
            new_file_name = f"{file_name}_{counter}{new_extension}"
            new_full_path = os.path.join(os.path.dirname(full_path), new_file_name)
            counter += 1

        return new_full_path

    def on_drop(self, event):
        file_path = event.data.replace("{", '').replace("}", '')
        print(file_path)
        if os.path.isfile(file_path):
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                self.process_pdf_file(file_path)
            else:
                messagebox.showinfo("File Type", f"Unsupported file type: {file_extension}")
        else:
            messagebox.showinfo("File Type", f"Not a valid file: {file_path}")

    def pdf_to_image(self, pdf_file_path, output_dir):
        images = convert_from_path(pdf_file_path, grayscale=True, fmt='png', poppler_path=r".\bin")
        for i, image in enumerate(images):
            # 去噪
            image = image.filter(ImageFilter.MedianFilter(size=3))
            # 二值化
            image = image.convert('1')
            # 閾值化
            threshold = 128
            image = image.point(lambda p: p > threshold and 255)
            image.save(os.path.join(output_dir, f'page_{i+1:03d}.png'))

    def ocr(self, image_file_path):
        text = pytesseract.image_to_string(Image.open(image_file_path), lang=self.ocr_lang_var.get())
        return text

    def translate(self, text):
        headers = {'Authorization': f'Bearer {API_KEY}'}
        data = {'messages': [{'role': 'user', 'content': f'{text} \n Translate to zh_TW'}], 'model': f'{MODEL_NAME}'}
        retry_count = 0
        while retry_count < 3:
            try:
                response = requests.post(f'{API_URL}/chat/completions', headers=headers, json=data)
                response.raise_for_status()
                return response.json()['choices'][0]['message']['content']
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < 3:
                    print(f"遇到錯誤，重試第{retry_count+1}次...")
                    time.sleep(1)  # 等待1秒後重試
                else:
                    raise Exception(f"重試三次後仍然遇到錯誤: {e}")

    def process_pdf_file(self, file_path):
        filename_with_ext = os.path.basename(file_path)
        filename, _ = os.path.splitext(filename_with_ext)
        try:
            os.mkdir(filename)
            print(f"資料夾 {filename} 創建成功")
        except FileExistsError:
            print(f"資料夾 {filename} 已經存在")
        except OSError as e:
            print(f"錯誤：{e}")
        
        output_dir = filename

        # PDF頁面轉換圖檔
        images = convert_from_path(file_path, grayscale=True, fmt='png', poppler_path=r".\bin")
        total_pages = len(images)
        self.progress["maximum"] = total_pages

        texts = []
        translated_texts = []

        for i, image in enumerate(images):
            # 二值化
#             image = image.convert('1')
            # 閾值化
            threshold = 150
            image = image.point(lambda p: p > threshold and 255)
            image.save(os.path.join(output_dir, f'page_{i+1:03d}.png'))
            # 去噪
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            # OCR文字辨識
            image_file_path = os.path.join(output_dir, f'page_{i+1:03d}.png')
            text = self.ocr(image_file_path)
            texts.append(text)
            
            # 保存OCR結果
            txt_file_name = f'page_{i+1:03d}.txt'
            txt_file_path = os.path.join(output_dir, txt_file_name)
            with open(txt_file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # 根據選項決定是否進行翻譯
            if self.translate_var.get():
                translated_text = self.translate(text)
                translated_texts.append(translated_text)
                
                # 保存翻譯結果
                translated_txt_file_name = f'page_{i+1:03d}_translated.txt'
                translated_txt_file_path = os.path.join(output_dir, translated_txt_file_name)
                with open(translated_txt_file_path, 'w', encoding='utf-8') as f:
                    f.write(translated_text)
            
            self.progress["value"] = i + 1
            self.root.update_idletasks()
            time.sleep(1)  # 等待1秒後處理下一頁

        # 將所有文本合併到一個文件中，並使用來源檔案的名字
        output_txt_filename = f"{filename}.txt"
        output_txt_path = os.path.join(output_dir, output_txt_filename)
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(texts))

        # 如果有進行翻譯，則將所有翻譯結果合併到一個文件中
        if self.translate_var.get():
            translated_txt_filename = f"{filename}_translated.txt"
            translated_txt_path = os.path.join(output_dir, translated_txt_filename)
            with open(translated_txt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(translated_texts))

    def format_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

if __name__ == '__main__':
    root = TkinterDnD.Tk()
    app = FileProcessorApp(root)
    root.mainloop()
