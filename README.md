# pdf_translate

# pdf全檔翻譯

流程：
* 將PDF每頁轉換成圖片
* 從每頁圖片中辨識出文字
* 交給大語言進行翻譯


需要預先安裝兩個工具程式  
PDF轉影像：  
https://pypi.org/project/pdf2image/  
這個工具要把解開後的bin目錄放在源碼旁邊  
然後在源碼中在API的引數中將路徑變數poppler_path指向bin所在位置  
``` python
images = convert_from_path(pdf_file_path, poppler_path = r".\bin")
```
圖片辨識文字：  
https://github.com/UB-Mannheim/tesseract/wiki  
這個工具要在源碼中指定執行檔路徑  
``` python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

```
