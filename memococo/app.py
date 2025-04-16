from threading import Thread
from flask import Flask, request, send_from_directory, redirect, url_for, render_template, flash, Response, jsonify, session
import sys
import os
import datetime
import time
from multiprocessing import Manager, Event
from babel import Locale

# 导入配置模块
from memococo.config import appdata_folder, screenshots_path, app_name_cn, app_version, get_settings, save_settings, main_logger

# 导入数据库模块
from memococo.database import create_db, get_timestamps, get_unique_apps, get_ocr_text, search_entries

# 导入功能模块
from memococo.ollama import extract_keywords_to_json
from memococo.screenshot import record_screenshots_thread
from memococo.ocr_processor import start_ocr_processor
from memococo.utils import human_readable_time, timestamp_to_human_readable, ImageVideoTool, check_port, get_unbacked_up_folders, get_total_size, count_unique_keywords
from memococo.app_map import get_app_names_by_app_codes, get_app_code_by_app_name

# 导入错误处理模块
from memococo.common.error_handler import initialize_error_handler, with_error_handling, MemoCocoError, DatabaseError, FileError, SystemError
from memococo.common.error_middleware import setup_error_handling

# 导入国际化支持模块
from memococo.i18n import get_translator, set_locale, get_locale, get_available_locales
from memococo.i18n.flask_i18n import FlaskI18n

# 全局变量
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = 'uuid-14f9a9-4a8c-8e8a-9c4d-9f7b8f7b8f7b'

# 设置Jinja2过滤器
app.jinja_env.filters["human_readable_time"] = human_readable_time
app.jinja_env.filters["timestamp_to_human_readable"] = timestamp_to_human_readable

# 初始化错误处理器
initialize_error_handler(logger=main_logger, show_in_console=True, show_in_ui=True)

# 设置错误处理中间件
error_middleware = setup_error_handling(app, logger=main_logger)

# 初始化国际化支持
app.config['I18N_DEFAULT_LOCALE'] = 'zh_CN'
app.config['I18N_SESSION_KEY'] = 'locale'
i18n = FlaskI18n(app)

# 创建翻译函数
def _(key, default=None, **kwargs):
    translator = get_translator()
    return translator.translate(key, default, **kwargs)

# 注意：语言切换路由已由 FlaskI18n 扩展提供，不需要在这里重复定义

# 创建共享变量
ignored_apps = None
ignored_apps_updated = None

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
@with_error_handling({"route": "timeline"})
def timeline():
    # connect to db
    timestamps = get_timestamps()
    #todo 增加time_nodes,用于计算合适的时间节点，5分钟前，1小时前，3小时前，6小时前，12小时前，24小时前，3天前，7天前，30天前，90天前，180天前，1年前等。
    time_nodes = generate_time_nodes(timestamps)
    # 使用多线程唤醒ollama服务
    # if get_settings()["use_ollama"] == "True":
    #     Thread(target=query_ollama,args=("你好",get_settings()["model"])).start()
    return render_template("index.html",
        timestamps=timestamps,
        time_nodes=time_nodes,
        unique_apps=unique_apps,
        app_name=_('app_name'),
        locale=get_locale(),
        available_locales=get_available_locales()
    )


@app.route("/search")
@with_error_handling({"route": "search"})
def search():
    """高级搜索功能，支持关键词和应用程序过滤

    修改版本：返回所有搜索结果，不使用分页，以确保前端分页正常工作
    """
    # 获取查询参数
    q = request.args.get("q")
    app_name = request.args.get("app")

    main_logger.info(f"Searching for '{q}' in app '{app_name}'")

    # 如果没有查询参数，返回主页
    if not q and not app_name:
        return redirect("/")

    # 获取应用程序代码
    app_code = get_app_code_by_app_name(app_name) if app_name else None

    # 如果只有应用程序过滤，没有关键词
    if not q and app_code:
        # 使用search_entries函数直接过滤应用，传入空关键词列表
        # 使用大的limit值确保获取所有结果
        entries = search_entries(keywords=[], app=app_code, limit=100000, offset=0)
        search_apps = [app_name]
        keywords = []
    else:
        # 使用Ollama提取关键词
        keywords = []
        if get_settings()["use_ollama"] == "True":
            main_logger.info(f"Using Ollama model: {get_settings()['model']}")
            extracted_keywords = extract_keywords_to_json(q, model=get_settings()["model"])
            if extracted_keywords:
                keywords = extracted_keywords

        # 如果没有提取到关键词，则使用原始查询分词
        if not keywords:
            keywords = q.split()

        main_logger.info(f"Search keywords: {keywords}")

        # 使用search_entries函数进行搜索，使用大的limit值确保获取所有结果
        entries = search_entries(keywords, app=app_code, limit=100000, offset=0)

        # 如果有关键词，对搜索结果进行排序
        if keywords:
            # 创建一个包含排序信息的列表
            sorted_entries = []

            for entry in entries:
                # 获取文本内容
                text = getattr(entry, 'text', '') or ''

                # 计算不重复关键词出现次数
                unique_count = count_unique_keywords(text, keywords)

                # 计算总关键词出现次数（包括重复）
                total_count = sum(text.count(keyword) for keyword in keywords)

                # 添加到排序列表
                sorted_entries.append({
                    "entry": entry,
                    "unique_count": unique_count,
                    "total_count": total_count
                })

            # 按不重复出现次数（主要）和总出现次数（次要）排序
            sorted_entries.sort(key=lambda x: (x["unique_count"], x["total_count"]), reverse=True)

            # 提取排序后的条目
            entries = [item["entry"] for item in sorted_entries]

            # 记录排序信息
            main_logger.info(f"Sorted search results by unique keyword matches and total matches")

        # 获取搜索结果中的应用程序
        app_codes = list(set([entry.app for entry in entries if entry.app]))
        search_apps = get_app_names_by_app_codes(app_codes)

    # 记录搜索结果数量
    main_logger.info(f"Found {len(entries)} results for search query")

    # 渲染搜索结果页面
    return render_template(
        "search.html",
        entries=entries,
        keywords=keywords,
        q=q,
        unique_apps=search_apps,
        app_name=_('app_name'),
        locale=get_locale(),
        available_locales=get_available_locales()
    )


@app.route("/settings", methods=["GET", "POST"])
@with_error_handling({"route": "settings"})
def settings():
    if request.method == "POST":
        # 获取表单数据
        model = request.form.get("model")
        use_ollama = request.form.get("use_ollama")
        local_ignored_apps = request.form.getlist("ignored_apps")
        # local_ignored_apps需要转为list,将local_ignored_apps[0]转为list，每个元素以,分割
        local_ignored_apps = local_ignored_apps[0].split(",") if local_ignored_apps else []
        #将local_ignored_apps列表中每个字符串两边的空格去掉
        local_ignored_apps = [app.strip() for app in local_ignored_apps]
        main_logger.info(local_ignored_apps)

        # 注意：数据清理功能已移除，以确保数据持久保存

        # 保存设置
        save_settings({
            "use_ollama": use_ollama,
            "model": model,
            "ignored_apps": local_ignored_apps,
        })

        # 更新ignored_apps
        global ignored_apps, ignored_apps_updated
        if ignored_apps is not None and ignored_apps_updated is not None:
            ignored_apps[:] = local_ignored_apps
            ignored_apps_updated.set()
            main_logger.info("Updated ignored apps list")

        # 注意：手动清理功能已移除，以确保数据持久保存
        # 浮窗提示，保存成功
        flash(_('settings_saved'), "success")
        # 等待两秒后，重定向到 /
        time.sleep(2)
        return redirect(url_for("timeline"))
    # 获取当前设置
    current_settings = get_settings()
    return render_template(
        "settings.html",
        settings=current_settings,
        app_name=_('app_name'),
        locale=get_locale(),
        available_locales=get_available_locales()
    )


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
    #如果为空，则返回空数组
    if not data:
        return jsonify([])

    try:
        # 尝试解析jsontext字段
        import json
        jsontext = json.loads(data)
        # 如果解析成功，返回json格式
        return jsonify(jsontext)
    except Exception as e:
        main_logger.error(f"解析OCR文本失败: {e}")
        # 如果解析失败，返回空数组
        return jsonify([])

@app.route("/unbacked_up_folders")
@with_error_handling({"route": "unbacked_up_folders"})
def unbacked_up_folders():
    folder_info = get_unbacked_up_folders()
    total_size = get_total_size()
    # 将未备份的文件夹传递给模板
    return render_template(
        "unbacked_up_folders.html",
        folders=folder_info,
        totalSize=total_size,
        app_name=_('app_name'),
        locale=get_locale(),
        available_locales=get_available_locales()
    )

def compress_folder_thread(folder):
    # 创建 ImageVideoTool 实例
    tool = ImageVideoTool(folder)
    # 调用 compress 方法
    tool.images_to_video( sort_by="time")

@app.route("/compress_folder", methods=["POST"])
@with_error_handling({"route": "compress_folder"})
def compress_folder():
    # 从请求的 JSON 数据中获取文件夹路径
    data = request.get_json()
    folder = data.get("folder")
    main_logger.info(folder)
    if not folder:
        return jsonify({"error": "No folder provided"}), 400
    #使用新线程，防止阻塞
    t = Thread(target=compress_folder_thread, args=(folder,))
    t.start()
    # 重定向到未备份文件夹页面
    return redirect(url_for("unbacked_up_folders"))

def set_cpu_affinity(pid=None, cpu_list=None):
    import psutil
    """
    设置指定进程的 CPU 亲和性。
    :param pid: 进程 ID，默认为当前进程。
    :param cpu_list: 允许运行的 CPU 核心列表，例如 [0, 1, 2, 3]。
    """
    if pid is None:
        pid = os.getpid()  # 默认操作当前进程
    process = psutil.Process(pid)

    if cpu_list is None:
        cpu_list = list(range(psutil.cpu_count()))  # 默认使用所有核心

    try:
        process.cpu_affinity(cpu_list)
        print(f"Set CPU affinity for PID {pid} to cores: {cpu_list}")
    except Exception as e:
        print(f"Failed to set CPU affinity: {e}")

# 注意：自动清理功能已移除，以确保数据持久保存

@with_error_handling({"function": "initialize_app"})
def initialize_app():
    """初始化应用程序

    初始化数据库、检查端口、启动必要的后台线程
    """
    # 初始化数据库
    create_db()
    main_logger.info(f"Database initialized successfully")

    # 检查应用数据目录
    if not os.path.exists(appdata_folder):
        os.makedirs(appdata_folder)
        main_logger.info(f"Created appdata folder: {appdata_folder}")
    else:
        main_logger.info(f"Using existing appdata folder: {appdata_folder}")

    # 检查截图目录
    if not os.path.exists(screenshots_path):
        os.makedirs(screenshots_path)
        main_logger.info(f"Created screenshots folder: {screenshots_path}")

    # 检查端口可用性
    if check_port(8842):
        error_msg = "Port 8842 is already in use. Please close the program that is using this port and try again."
        main_logger.error(error_msg)
        raise SystemError(error_msg, {"port": 8842})

    return True

@with_error_handling({"function": "start_background_threads"})
def start_background_threads():
    """启动必要的后台线程

    启动截图记录线程和OCR处理线程
    """
    # 初始化共享变量
    global ignored_apps, ignored_apps_updated
    ignored_apps = Manager().list(get_settings().get("ignored_apps", []))
    ignored_apps_updated = Event()
    main_logger.info(f"Initialized shared variables with {len(ignored_apps)} ignored apps")

    # 启动截图记录线程
    try:
        screenshot_thread = Thread(
            target=record_screenshots_thread,
            args=(ignored_apps, ignored_apps_updated, True, 5, True),
            name="ScreenshotThread"
        )
        screenshot_thread.daemon = True
        screenshot_thread.start()
        main_logger.info("Screenshot recording thread started")
    except Exception as e:
        error_msg = f"Failed to start screenshot thread: {e}"
        main_logger.error(error_msg)
        raise SystemError(error_msg, {"thread": "screenshot"}, e)

    # 启动OCR处理线程
    # ocr_thread = start_ocr_processor()
    # main_logger.info("OCR processor thread started")

    # 注意：自动清理功能已移除，以确保数据持久保存

    # 设置CPU亲和性
    try:
        set_cpu_affinity()
    except Exception as e:
        # 亲和性设置失败不应该导致程序退出，只记录日志
        main_logger.warning(f"Failed to set CPU affinity: {e}")

    return True

@with_error_handling({"function": "main"})
def main():
    """主函数，用于启动应用程序

    这个函数会被 setup.py 中的 entry_points 调用
    """
    # 显示应用程序信息
    main_logger.info(f"Starting {app_name_cn} (MemoCoco) v{app_version}")

    # 初始化应用
    initialize_app()

    # 启动后台线程
    start_background_threads()

    # 启动Flask应用
    main_logger.info("Starting web server on port 8842")
    try:
        app.run(port=8842, threaded=True)
    except KeyboardInterrupt:
        main_logger.info("Application terminated by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
