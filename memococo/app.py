from threading import Thread
from flask import Flask, request, send_from_directory,redirect, url_for,render_template,flash,Response
import sys
import os
import json,jsonify
import datetime
from multiprocessing import Manager,Event
from memococo.config import appdata_folder, screenshots_path, app_name_cn, app_version,get_settings,save_settings,logger
from memococo.database import create_db, get_all_entries, get_timestamps, get_unique_apps,get_ocr_text
from memococo.ollama import extract_keywords_to_json,query_ollama
from memococo.screenshot import record_screenshots_thread
from memococo.utils import human_readable_time, timestamp_to_human_readable,ImageVideoTool,get_folder_paths,count_unique_keywords,check_port
from memococo.app_map import get_app_names_by_app_codes,get_app_code_by_app_name
import time

app = Flask(__name__,static_folder="static",static_url_path="/static")

app.secret_key = 'uuid-14f9a9-4a8c-8e8a-9c4d-9f7b8f7b8f7b'

app.jinja_env.filters["human_readable_time"] = human_readable_time
app.jinja_env.filters["timestamp_to_human_readable"] = timestamp_to_human_readable

def generate_time_nodes(current_timestamps):
    # 定义时间间隔（单位：秒）
    intervals = [
        60 * 60,       # 1小时
        3 * 60 * 60,   # 3小时
        6 * 60 * 60,   # 6小时
        24 * 60 * 60,  # 24小时
        3 * 24 * 60 * 60,  # 3天
        7 * 24 * 60 * 60,  # 7天
        30 * 24 * 60 * 60, # 30天
    ]
    # 获取当前时间戳
    now = datetime.datetime.now().timestamp()
    
    # 生成时间节点
    time_nodes = []
    for interval in intervals:
        timestamp = now - interval
        # 如果时间节点在当前时间戳列表中，忽略秒与毫秒部分，只比较日期部分，则将时间戳列表中最接近的时间戳到时间节点列表中
        for ts in current_timestamps:
            if ts - timestamp < 60:
                time_nodes.append({'desc':human_readable_time(ts),'timestamp':ts})
                break
    # 将time_nodes倒序排列
    # time_nodes.reverse()
    # 保留最多三个，最后三个时间
    time_nodes = time_nodes[-3:]
    return time_nodes

  
@app.before_request
def load_data():
  global unique_apps
  unique_apps = get_app_names_by_app_codes(get_unique_apps())
  
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/")
def timeline():
    # connect to db
    timestamps = get_timestamps()
    #todo 增加time_nodes,用于计算合适的时间节点，5分钟前，1小时前，3小时前，6小时前，12小时前，24小时前，3天前，7天前，30天前，90天前，180天前，1年前等。
    time_nodes = generate_time_nodes(timestamps)
    # 使用多线程唤醒ollama服务
    if get_settings()["use_ollama"] == "True":
        Thread(target=query_ollama,args=("你好",get_settings()["model"])).start()
    return render_template("index.html",
        timestamps=timestamps,
        time_nodes = time_nodes,
        unique_apps = unique_apps,
        app_name = app_name_cn
    )


@app.route("/search")
def search():
    q = request.args.get("q")
    app = request.args.get("app")
    print(f"searching for {q} in {app}")
    app_code = get_app_code_by_app_name(app)
    # 如果q为空，则返主页
    if not q and not app:
        return redirect("/")
    entries = get_all_entries()
    if not q:
        # 从entries中筛选所有app字段等于app的条目，count为0
        sorted_entries = [{"entry": entry, "count": 0} for entry in entries if entry.app == app_code]
        search_apps = [app]
        keywords = []
        # sorted_entries按照entry的timestamp字段降序排列
        sorted_entries.sort(key=lambda x: x["entry"].timestamp, reverse=True)
        # 保留最多50条
        # sorted_entries = sorted_entries[:50]
    else:
        keywords = []
        logger.info(f"use ollama: {get_settings()['use_ollama']}")
        if get_settings()["use_ollama"] == "True":
            keywords = extract_keywords_to_json(q,model= get_settings()["model"])
        #将keywords从json字符串转为list
        keywords = keywords if keywords else q.split()
        sorted_entries = []
        # 遍历entries列表中的每个条目
        for entry in entries:
            # 获取条目的'text'属性，如果属性不存在，则返回空字符串
            text = getattr(entry, 'text', '') or ''
            # 如果任何一个关键词在text中，any()函数将返回True
            if any(keyword in text for keyword in keywords):
                #将entry的text字段中出现keywords的次数,同一个keyword仅统计一次,统计到数组entries_unique_count中
                unique_count = count_unique_keywords(text,keywords)
                if unique_count > 0:
                    # 将entry的text字段中出现keywords的次数,同一个keyword多次出现算多次,统计到数组entries_count中
                    unique_count = unique_count*100000
                    count = sum(text.count(keyword) for keyword in keywords) + unique_count
                    sorted_entries.append({"entry": entry, "count": count})
        #如果app不为空，则筛选app字段等于app的条目
        search_apps = get_app_names_by_app_codes(list(set([entry["entry"].app for entry in sorted_entries])))
        if app_code:
            sorted_entries = [entry for entry in sorted_entries if entry["entry"].app == app_code]
        # 将sorted_entries按count字段降序排列
        sorted_entries = sorted(sorted_entries, key=lambda x: x["count"], reverse=True)
    return render_template(
        "search.html",
        entries=[entry["entry"] for entry in sorted_entries],
        keywords=keywords,
        q=q,
        unique_apps = search_apps,
        app_name = app_name_cn
    )
    

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        # 获取表单数据
        model = request.form.get("model")
        ocr_tool = request.form.get("ocr_tool")
        use_ollama = request.form.get("use_ollama")
        local_ignored_apps = request.form.getlist("ignored_apps")
        # local_ignored_apps需要转为list,将local_ignored_apps[0]转为list，每个元素以,分割
        local_ignored_apps = local_ignored_apps[0].split(",") if local_ignored_apps else []
        #将local_ignored_apps列表中每个字符串两边的空格去掉
        local_ignored_apps = [app.strip() for app in local_ignored_apps]
        logger.info(local_ignored_apps)
        
        # 保存设置
        save_settings({
                "ocr_tool": ocr_tool,
                "use_ollama": use_ollama,
                "model": model,
                "ignored_apps": local_ignored_apps,
            })
        # 更新ignored_apps
        ignored_apps[:] = local_ignored_apps
        ignored_apps_updated.set()
        # 浮窗提示，保存成功
        flash("设置已保存", "success")
        # 等待两秒后，重定向到 /
        time.sleep(2)
        return redirect(url_for("timeline"))
    # 获取当前设置
    current_settings = get_settings()
    return render_template("settings.html", settings=current_settings)


@app.route("/pictures/<filename>")
def serve_image(filename):
    #解析文件名，获取时间戳
    timestamp = filename.split('.')[0]
    #根据时间戳，获取年月日，拼接为文件路径
    year, month, day = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y'), datetime.datetime.fromtimestamp(int(timestamp)).strftime('%m'), datetime.datetime.fromtimestamp(int(timestamp)).strftime('%d')
    dir = os.path.join(screenshots_path, year, month, day)
        
    tool = ImageVideoTool(dir)
    if tool.is_backed_up():
        byte_stream = tool.query_image(timestamp)
        response = Response(byte_stream, mimetype='image/jpeg')
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    else:
        return send_from_directory(dir, filename)

@app.route("/get_ocr_text/<timestamp>")
def get_ocr_text_by_timestamp(timestamp):
    #解析文件名，获取时间戳
    data = get_ocr_text(timestamp)
    #如果为空，则返回空字符串，否则转为json格式返回
    if not data:
        return ""
    else:
        return data
    
@app.route("/unbacked_up_folders")
def unbacked_up_folders():
    # 获取 screenshots_path 下的所有文件夹
    all_folders = get_folder_paths(screenshots_path, 0, 30)
    # 筛选出未备份的文件夹
    unbacked_up_folders = [folder for folder in all_folders if not ImageVideoTool(folder).is_backed_up()]
    total_size = ImageVideoTool(appdata_folder).get_folder_size()
    # 按照文件夹名排序
    unbacked_up_folders.sort()
    folder_info = []
    # 查询未备份文件夹的图片数量以及文件夹大小
    for folder in unbacked_up_folders:
        tool = ImageVideoTool(folder)
        folder_info.append({
            "folder": folder,
            "image_count": tool.get_image_count(),
            "folder_size": tool.get_folder_size()
        })
    # 将未备份的文件夹传递给模板
    return render_template("unbacked_up_folders.html", folders=folder_info,totalSize=total_size)

def compress_folder_thread(folder):
    # 创建 ImageVideoTool 实例
    tool = ImageVideoTool(folder)
    # 调用 compress 方法
    tool.images_to_video( sort_by="time")
    
@app.route("/compress_folder", methods=["POST"])
def compress_folder():
    # 从请求的 JSON 数据中获取文件夹路径
    data = request.get_json()
    folder = data.get("folder")
    logger.info(folder)
    if not folder:
        return jsonify({"error": "No folder provided"}), 400
    #使用新线程，防止阻塞
    t = Thread(target=compress_folder_thread, args=(folder,))
    t.start()
    # 重定向到未备份文件夹页面
    return redirect(url_for("unbacked_up_folders"))

if __name__ == "__main__":
    create_db()

    logger.info(f"app version: {app_version}")

    logger.info(f"Appdata folder: {appdata_folder}")
    
    logger.info(f"check port: {check_port(8082)}")
    
    #如果8082端口被占用，则提示并退出
    if check_port(8082):
        logger.error("Port 8082 is already in use. Please close the program that is using this port and try again.")
        sys.exit(1)

    ignored_apps = Manager().list(get_settings()["ignored_apps"])
    ignored_apps_updated = Event()
    # Start the thread to record screenshots
    t = Thread(target=record_screenshots_thread,args=(ignored_apps, ignored_apps_updated,True,3,True))
    t.start()

    app.run(port=8082)
