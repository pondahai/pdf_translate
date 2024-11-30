import os
import requests
import pytesseract
from PIL import Image
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
# API_URL = os.getenv('API_URL')
API_URL = r"https://api.groq.com/openai/v1"
# API_URL = r"http://ubuntu:1234/v1"
# API_URL = r"http://127.0.0.1:1234/v1"
API_KEY = os.getenv('API_KEY')
MODEL_NAME = 'gemma2-9b-it'
# MODEL_NAME = ''

            

class FileProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Processor")
        self.root.geometry("400x200")

        # 新增OCR語言選項下拉選單
        self.ocr_lang_var = tk.StringVar(self.root)
        self.ocr_lang_var.set("eng")  # 預設為英文
        self.ocr_lang_options = ["", "eng", "chi_tra", "chi_sim", "jpn", "kor"]
        self.ocr_lang_dropdown = ttk.OptionMenu(self.root, self.ocr_lang_var, *self.ocr_lang_options)
        self.ocr_lang_dropdown.pack(pady=10)

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
        """
        替換檔案的副檔名，並避免目的地已經有同名檔案存在。

        參數:
        full_path (str): 包含檔案名稱的全路徑字串。
        new_extension (str): 新的副檔名（包括點號，例如 '.new'）。

        回傳:
        str: 新的檔案全路徑。
        """
        # 提取檔案名稱和副檔名
        file_name_with_extension = os.path.basename(full_path)
        file_name, _ = os.path.splitext(file_name_with_extension)

        # 構建新的檔案名稱
        new_file_name = file_name + new_extension
        new_full_path = os.path.join(os.path.dirname(full_path), new_file_name)

        # 檢查目的地是否已經存在同名檔案
        counter = 1
        while os.path.exists(new_full_path):
            new_file_name = f"{file_name}_{counter}{new_extension}"
            new_full_path = os.path.join(os.path.dirname(full_path), new_file_name)
            counter += 1

        return new_full_path

    def on_drop(self, event):
        file_path = event.data
#         print(event.type)
#         file_path = file_path[1:-1]
#         file_path = file_path.replace("/", '\\')
#         file_path = file_path.replace(" ", '\ ')
        file_path = file_path.replace("{", '').replace("}", '')
#         file_path = f"{file_path}"
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
        images = convert_from_path(pdf_file_path, poppler_path = r".\bin")
        for i, image in enumerate(images):
            image.save(os.path.join(output_dir, f'page_{i+1:03d}.png'))

    def ocr(self, image_file_path):
        # 使用選擇的OCR語言進行文字辨識
        text = pytesseract.image_to_string(Image.open(image_file_path), lang=self.ocr_lang_var.get())
        return text

    # def translate(text):
    #     headers = {'Authorization': f'Bearer {API_KEY}'}
    #     data = {'messages': [{'role': 'user', 'content': f'Translate to zh_TW: {text} '}], 'model': f'{MODEL_NAME}'}
    #     response = requests.post(f'{API_URL}/chat/completions', headers=headers, json=data)
    #     if response.status_code == 200:
    #         return response.json()['choices'][0]['message']['content']
    #     else:
    #         raise Exception(f'Translation failed: {response.text}')

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
#         pdf_file_path = 'input.pdf'
        # 創建資料夾
        filename_with_ext = os.path.basename(file_path)
        filename, _ = os.path.splitext(filename_with_ext)
        try:
            os.mkdir(filename)
            print(f"資料夾 {filename} 創建成功")
        except FileExistsError:
            print(f"資料夾 {filename} 已經存在")
            pass
        except OSError as e:
            print(f"錯誤：{e}")
        
        output_dir = filename

        # PDF頁面轉換圖檔
        images = convert_from_path(file_path, poppler_path=r".\bin")
        total_pages = len(images)
        self.progress["maximum"] = total_pages  # Set the maximum value of the progress bar

        for i, image in enumerate(images):
            image.save(os.path.join(output_dir, f'page_{i+1:03d}.png'))
            self.progress["value"] = i + 1  # Update progress bar
            self.root.update_idletasks()  # Update the GUI

        # OCR文字辨識
        texts = []
        for i, file_name in enumerate(os.listdir(output_dir)):
            if file_name.endswith('.png'):
                image_file_path = os.path.join(output_dir, file_name)
                text = self.ocr(image_file_path)
                texts.append(text)
                # 將text存為檔案
                txt_file_name = file_name.replace('.png', '.txt')
                txt_file_path = os.path.join(output_dir, txt_file_name)
                with open(txt_file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.progress["value"] = i + 1  # Update progress bar
                self.root.update_idletasks()  # Update the GUI

        # 大語言模型翻譯
        translated_texts = []
        for i, text in enumerate(texts):
            translated_text = self.translate(text)
            translated_texts.append(translated_text)
            self.progress["value"] = i + 1  # Update progress bar
            self.root.update_idletasks()  # Update the GUI
            time.sleep(1)

        # 保存翻譯結果
        with open(os.path.join(output_dir, 'translated.txt'), 'w', encoding='utf-8') as f:
            for text in translated_texts:
                f.write(text + '\n')

    def update_progress(self, total_time):
        # This method is no longer needed as we update the progress bar directly in process_pdf_file
        pass


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
