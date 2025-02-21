#将app code列表转换为app name列表
def get_app_names_by_app_codes(app_codes):
    app_names = []
    for app_code in app_codes:
        # 从app_map中获取app_name，如果为空，则使用app_code
        app_name = app_map.get(app_code, app_code)
        app_names.append(app_name)
    return app_names

def get_app_code_by_app_name(app_name):
    for app_code, name in app_map.items():
        if name == app_name:
            return app_code
    return None

# appname与appcode对应关系
app_map = {
    "microsoft-edge": "edge浏览器",
    "gnome-terminal-server": "终端",
    "wechat": "微信",
    "org.remmina.Remmina": "remmina",
    "code": "vscode",
    "wpsoffice": "wps",
    "bytedance-feishu": "飞书",
    "evince": "文档查看器",
    "Mail": "邮件",
    "zenity": "zenity",
    "org.gnome.Nautilus": "文件管理器",
    "gnome-system-monitor": "系统监视器",
    "wemeetapp": "腾讯会议",
    "vlc": "VLC",
    "utools": "uTools",
    "tdappdesktop": "腾讯文档",
    "crx__jmidjmfeoeoanppkhaglamohfgncdcll":"小红书",
    "gjs": "未知",
    "xdg-desktop-portal-gnome":"打开文件",
    "java":"DBeaver",
    "gnome-extensions-app":"扩展应用",
    "cursor":"cursor",
    "switchhosts":"switchhosts",
    "org.gnome.Weather":"天气",
    "motrix":"motrix",
    "gnome-power-statistics":"电源统计",
    "gnome-control-center":"设置",
    "file-roller":"归档管理器",
    "Trojan-Qt5-Linux.AppImage":"trojan",
    "xarchiver":"xarchiver",
    "spark-store":"星火应用商店",
    "org.gnome.Shell.Extensions":"gnome扩展",
    "eog":"图像查看器",
    "crx__cibpboibpedkaagmppnjeingegpoladf":"时间胶囊"
}