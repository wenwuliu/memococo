import requests
import base64
from memococo.config import logger
import json
import cv2


def extract_text_from_image(image,ocr_engine='trwebocr'):
    try:
        if ocr_engine == 'tesseract':
            result = tesseract_ocr(image)
            text = ""
            for item in json.loads(result):
                text += item[1]
            return text
        elif ocr_engine == 'trwebocr':
            response = trwebocr(image)
            if response is None:
                return ""
            text = ""
            for item in json.loads(response):
                text += item[1]
            return text
        elif ocr_engine == 'rapidocr':
            result = rapid_ocr(image)
            text = ""
            for item in result:
                text += item[1]
            return text
        else:
            logger.error(f'Invalid OCR engine: {ocr_engine}')
            return None
    except Exception as e:
        logger.error(f'Error occurred while extracting text from image: {e}')
        return ""
    
def rapid_ocr(image):
    from rapidocr_onnxruntime import RapidOCR
    # 使用RapidOCR进行图像文本提取
    engine = RapidOCR(params={"Global.lang_det": "ch_server", "Global.lang_rec": "ch_server"})
    result,elapse = engine(image)
    return result

def tesseract_ocr(image):
    import pytesseract
    from pytesseract import Output
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
        logger.info("正在请求trwebocr")
        result = requests.post(url, data={"img": encoded_string,'compress':0})
        logger.info("请求trwebocr完成")
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
    
def easy_ocr(image):
    image = image_preprocessing(image)
    import easyocr
    reader = easyocr.Reader(['ch_sim','en'],gpu=True)
    result = reader.readtext(image,detail=0)
    # 将result字符串数组转为字符串，按空格分隔
    result = " ".join(result)
    return result

# main方法测试
if __name__ == "__main__":
    import time
    start_time = time.time()
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
        response = extract_text_from_image(screenshots[0],ocr_engine='rapid_ocr')
        end_time = time.time()
        logger.info("seperate")
        logger.info(response)
        logger.info(f"耗时：{end_time - start_time}")
        #将json数组中所有的第二个元素抽取出来，并拼接成字符串
