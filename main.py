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

from flask import Flask

app = Flask(__name__)
CORS(app)
@app.route("/")
def index():
    print("start")
    take_screenshot()
    img = Image.open("./static/screenshot.png")
    size = width_height(img)
    ret = get_translation_and_vertices("./static/screenshot.png")
    print(ret)
    return {"ret": [ret, size]}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8020)
