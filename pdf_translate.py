import os
import requests
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from dotenv import load_dotenv
import time

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 載入環境變數
load_dotenv()

# OpenAI API設定
# API_URL = os.getenv('API_URL')
# API_URL = r"https://api.groq.com/openai/v1"
API_URL = r"http://ubuntu:1234/v1"
# API_URL = r"http://127.0.0.1:1234/v1"
API_KEY = os.getenv('API_KEY')
MODEL_NAME = 'gemma2-9b-it'
# MODEL_NAME = ''

def pdf_to_image(pdf_file_path, output_dir):
    images = convert_from_path(pdf_file_path, poppler_path = r".\bin")
    for i, image in enumerate(images):
        image.save(os.path.join(output_dir, f'page_{i+1}.png'))

def ocr(image_file_path):
    text = pytesseract.image_to_string(Image.open(image_file_path))
    return text

def translate(text):
    headers = {'Authorization': f'Bearer {API_KEY}'}
    data = {'messages': [{'role': 'user', 'content': f'Translate to zh_TW: {text} '}], 'model': f'{MODEL_NAME}'}
    response = requests.post(f'{API_URL}/chat/completions', headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f'Translation failed: {response.text}')

def main():
    pdf_file_path = 'input.pdf'
    output_dir = 'output'

    # PDF頁面轉換圖檔
    pdf_to_image(pdf_file_path, output_dir)

    # OCR文字辨識
    texts = []
    for file_name in os.listdir(output_dir):
        if file_name.endswith('.png'):
            image_file_path = os.path.join(output_dir, file_name)
            text = ocr(image_file_path)
            texts.append(text)

    # 大語言模型翻譯
    translated_texts = []
    for text in texts:
        translated_text = translate(text)
        translated_texts.append(translated_text)
        time.sleep(1)

    # 保存翻譯結果
    with open(os.path.join(output_dir, 'translated.txt'), 'w', encoding='utf-8') as f:
        for text in translated_texts:
            f.write(text + '\n')

if __name__ == '__main__':
    main()
