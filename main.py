import pyautogui
from PIL import Image
import pyocr
import re
from dotenv import load_dotenv
from openai import OpenAI
import os
from google.cloud import vision
from PIL import ImageDraw, ImageFont
import textwrap
from PIL import ImageFont
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

def take_screenshot():
    file_name = "./static/screenshot.png"
    wh = pyautogui.size()
    pyautogui.screenshot(
        file_name,
        region=(0, int(wh.height / 10), int(wh.width / 2), int(wh.height * 8 / 10)),
    )
    return Image.open(file_name)

def trans(text):
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": "あなたは英語の文章を日本語に翻訳するプロの翻訳者です。以下の英語の文章を日本語に翻訳してください。翻訳結果以外は一切必要ありません。なお翻訳する文章が無い時は""と出力しなさい\n\n"
                + '"""'
                + text
                + '"""',
            }
        ],
    )
    return completion.choices[0].message.content




def width_height(img):
    width, height = img.size
    return [width, height]






def get_translation_and_vertices(file_name):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./key.json"
    client = vision.ImageAnnotatorClient()
    with open(file_name, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    ret = []
    response = client.text_detection(image=image)
    for page in response.full_text_annotation.pages:
        print("page")
        def retFunc(block):
            block_text = ""
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = ''.join([symbol.text for symbol in word.symbols])
                    block_text += word_text + ' '
            block_text = block_text.strip()
            if len(block_text) < 6 and "+" in block_text:
                return
            print(block_text)
            translated_text = trans(block_text)

            print(translated_text)
            vertices = block.bounding_box.vertices
            vertices = [(vertex.x, vertex.y) for vertex in vertices]
            ret.append([block_text, translated_text, vertices])
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            for block in page.blocks:
                print("block")
                f = executor.submit(retFunc, block)
        """
        for block in page.blocks:
            print("block")
            retFunc(block)
        """
    return ret

"""
take_screenshot()
img = Image.open("my_screenshot.png")
print(width_height(img))
ret = get_translation_and_vertices("my_screenshot.png") 
print(ret)
"""



from PIL import Image
import numpy as np

def calculate_white_black_ratio(img_old, img_new, threshold: int = 128):
    arr_new = np.array(img_new)
    arr_old = np.array(img_old)

    white_ratio_new = np.sum(arr_new >= threshold) / arr_new.size
    white_ratio_old = np.sum(arr_old >= threshold) / arr_old.size

    return [white_ratio_new, white_ratio_old]




from flask import Flask

app = Flask(__name__)
CORS(app)
@app.route("/")
def index():
    print("start")
    if not os.path.exists("./static/screenshot.png"):
        ## 空の画像を作成
        img = Image.new("RGB", (100, 100), (255, 255, 255))
        img.save("./static/screenshot.png")
    img_old = Image.open("./static/screenshot.png").copy()
    take_screenshot()
    img = Image.open("./static/screenshot.png")
    #　グレースケール化
    img_old = img_old.convert("L")
    img = img.convert("L")
    #白と黒の割合を計算
    white_black_ratio = calculate_white_black_ratio(img_old, img)
    if abs(white_black_ratio[0] - white_black_ratio[1]) < 0.01:
        print("no-change")
        return {"info": "no change"}
    size = width_height(img)
    ret = get_translation_and_vertices("./static/screenshot.png")
    print(ret)
    print("change")
    return {"info": "change", "ret": [ret, size]}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8020)
