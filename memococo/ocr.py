import requests
import base64
import cv2
import pytesseract
from pytesseract import Output
from memococo.config import logger
import json


def extract_text_from_image(image):
    # return easy_ocr(image)
    return trwebocr(image)
    # return tesseract_ocr(image)

def tesseract_ocr(image):
    # 使用Tesseract OCR进行图像文本提取
    # 这里假设你已经安装了Tesseract OCR，并且将其添加到了系统的PATH中
    # 你需要根据你的实际情况调整Tesseract的路径
    binary_image = image_preprocessing(image)
    out = pytesseract.image_to_data(binary_image, output_type=Output.DICT, lang='chi_sim+eng')
    result = []
    num_boxes = len(out['level'])
    for i in range(num_boxes):
        (x, y, w, h) = (out['left'][i], out['top'][i], out['width'][i], out['height'][i])
        text = out['text'][i]
        result.append([[x, y, w, h, 0], text ,1])
    # 将result转为json字符串，中文编码为unicode
    result_json = json.dumps(result, ensure_ascii=False)
    return result_json

def trwebocr(image):        
    #改为采用本地OCR模型，POST请求http://127.0.0.1:8089/api/tr-run/，通过表单方式，上传图片
    #image来源为screenshot = np.array(sct.grab(monitor_))，即截图的numpy数组，需要转换为base64编码的字符串
    #将图片转换为base64编码的字符串
    url = "http://127.0.0.1:8089/api/tr-run/"
    # binary_image = image_preprocessing(image)
    # _, buffer = cv2.imencode('.png', binary_image)
    _, buffer = cv2.imencode('.png', image)
    encoded_string = base64.b64encode(buffer).decode('utf-8')
    try:
        result = requests.post(url, data={"img": encoded_string,'compress':0})
        # result = requests.post(url, data={"img": encoded_string})
        result.raise_for_status()
        data = result.json()
        if "data" in data and "raw_out" in data["data"]:
            text = data["data"]["raw_out"]
            #将text转为json字符串，中文编码为unicode
            text_json = json.dumps(text,ensure_ascii=False)
            return text_json
        else:
            logger.warning("响应格式不正确")
            return None
    except Exception as e:
        logger.warning("请求发生异常：", e)
        return None

def image_preprocessing(image):
    # 图像灰度化
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray_image    
    # #图像二值化
    # _, binary_image = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY_INV)
    
    # # 返回二值化后的图像
    # return binary_image
    
    
def easy_ocr(image):
    import easyocr
    reader = easyocr.Reader(['ch_sim','en'],gpu=True)
    result = reader.readtext(image)
    return result

# main方法测试
if __name__ == "__main__":
    screenshots = []
    import mss
    import numpy as np
    with mss.mss() as sct:
        for monitor in range(len(sct.monitors)):
            logger.info(f"截取第{monitor}个屏幕")
            monitor_ = sct.monitors[monitor]
            screenshot = np.array(sct.grab(monitor_))
            screenshot = screenshot[:, :, [2, 1, 0]]
            screenshots.append(screenshot)
    for image in screenshots:
        response = extract_text_from_image(image)
        logger.info(response)
        #将json数组中所有的第二个元素抽取出来，并拼接成字符串
        text = ""
        for item in json.loads(response):
            text += item[1]
        logger.info(text)
