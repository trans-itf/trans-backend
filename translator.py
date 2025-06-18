from google.cloud import vision
from PIL import ImageFont
from openai import OpenAI
from dotenv import load_dotenv

from concurrent.futures import ThreadPoolExecutor
import os


load_dotenv()


INT_INF = 1 << 31


def trans(text):
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": "あなたは英語の文章を日本語に翻訳するプロの翻訳者です。以下の英語の文章を日本語に翻訳してください。翻訳結果以外は一切必要ありません。なお翻訳する文章が無い時は"
                "と出力しなさい\n\n" + '"""' + text + '"""',
            }
        ],
    )
    return completion.choices[0].message.content

def get_char_height(font: ImageFont, char: str) -> int:
    if char == "":
        return 1 << 31
    return font.getbbox(char)[3]


def wrap_text(text: str, font: ImageFont, max_width: int) -> str:
    """
    バウンディングボックスの幅に収まるようにテキストを折り返す。

    Parameters
    ----------
    text : str
        折り返すテキスト
    font : ImageFont
        フォント
    max_width : int
        バウンディングボックスの幅
    """
    result = ""
    line = ""
    cur_x = 0

    for char in text:
        # フォントの幅を取得
        _, _, width, _ = font.getbbox(char)

        # はみ出す場合は改行
        if cur_x + width > max_width:
            result += line + "\n"
            cur_x = 0
            line = char
        else:
            line += char
        cur_x += width
    if line:
        result += line
    return result


def find_font_size(text: str, vertices: list[vision.Vertex]) -> tuple[int, str]:
    """
    バウンディングボックスの幅に収まるフォントサイズを二分探索で求める。

    Parameters
    ----------
    text : str
        フォントサイズを求めるテキスト
    vertices : list[vision.Vertex]
        バウンディングボックスの頂点

    Returns
    -------
    best_size, wrapped_text: tuple[int, str]
        フォントサイズ, 折り返したテキスト
    """
    top_left = vertices[0]
    bottom_right = vertices[2]

    min_size, max_size = 0, 10000
    max_width = bottom_right.x - top_left.x
    max_height = bottom_right.y - top_left.y

    wrapped_text = ""
    while max_size - min_size > 1:
        size = (min_size + max_size) // 2
        font = ImageFont.truetype("/app/fonts/mplus-2p-regular.ttf", size)
        temp_wrapped = wrap_text(text, font, max_width)

        # 高さを計算
        height = 0
        for line in temp_wrapped.split("\n"):
            if line == "":
                height += INT_INF
                continue
            height += size

        if height > max_height:
            max_size = size
        else:
            wrapped_text = temp_wrapped
            min_size = size
            best_size = min_size
    return best_size - 1, wrapped_text


def get_translation_and_vertices(img):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/app/key.json"
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=img)

    response = client.text_detection(image=image)
    ret = []
    for page in response.full_text_annotation.pages:
        def retFunc(block):
            block_text = ""
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = "".join([symbol.text for symbol in word.symbols])
                    block_text += word_text + " "
            block_text = block_text.strip()
            if len(block_text) < 6 and "+" in block_text:
                return

            translated_text = trans(block_text)
            vertices = block.bounding_box.vertices
            font_size, wrapped_text = find_font_size(translated_text, vertices)

            vertices = [{"x": vertex.x, "y": vertex.y} for vertex in vertices]
            ret.append(
                {
                    "original": block_text,
                    "translated": wrapped_text,
                    "bbox": vertices,
                    "font_size": font_size,
                }
            )

        with ThreadPoolExecutor(max_workers=50) as executor:
            for block in page.blocks:
                _ = executor.submit(retFunc, block)
    return ret
