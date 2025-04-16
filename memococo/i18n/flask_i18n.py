"""
Flask国际化扩展

提供Flask应用的国际化支持
"""

import os
from typing import Optional, Dict, Any, List
from flask import Flask, request, session, g, render_template
from markupsafe import Markup

from memococo.i18n.translator import Translator, get_translator, set_locale, get_locale, get_available_locales
from memococo.i18n.formatter import format_date, format_time, format_datetime, format_number

class FlaskI18n:
    """Flask国际化扩展类"""

    def __init__(self, app: Optional[Flask] = None):
        """初始化扩展

        Args:
            app: Flask应用实例
        """
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """初始化Flask应用

        Args:
            app: Flask应用实例
        """
        # 添加配置默认值
        app.config.setdefault('I18N_DEFAULT_LOCALE', 'zh_CN')
        app.config.setdefault('I18N_LOCALES_DIR', os.path.join(os.path.dirname(__file__), 'locales'))
        app.config.setdefault('I18N_SESSION_KEY', 'locale')

        # 设置默认语言
        set_locale(app.config['I18N_DEFAULT_LOCALE'])

        # 注册请求处理器
        @app.before_request
        def before_request():
            # 从会话中获取语言设置
            locale = session.get(app.config['I18N_SESSION_KEY'])
            if locale:
                set_locale(locale)

            # 创建翻译器实例
            g.translator = get_translator()
            g.locale = get_locale()

        # 注册模板全局函数
        app.jinja_env.globals.update({
            '_': self._gettext,
            'gettext': self._gettext,
            'ngettext': self._ngettext,
            'format_date': format_date,
            'format_time': format_time,
            'format_datetime': format_datetime,
            'format_number': format_number,
            'get_locale': get_locale,
            'get_available_locales': get_available_locales,
        })

        # 注册语言切换路由
        @app.route('/set_locale/<locale>')
        def set_locale_route(locale):
            # 验证语言代码
            if locale in get_available_locales():
                # 保存到会话
                session[app.config['I18N_SESSION_KEY']] = locale

                # 如果有重定向URL，则重定向
                redirect_url = request.args.get('next') or request.referrer or '/'
                return app.redirect(redirect_url)

            # 如果语言代码无效，返回400错误
            return app.response_class(
                response=render_template('error.html', error='Invalid locale'),
                status=400,
            )

        # 保存扩展实例
        app.extensions['i18n'] = self

    def _gettext(self, key: str, default: str = None, **kwargs) -> str:
        """翻译文本

        Args:
            key: 文本键名
            default: 默认文本，当找不到翻译时返回
            **kwargs: 格式化参数

        Returns:
            str: 翻译后的文本
        """
        if hasattr(g, 'translator'):
            return g.translator.translate(key, default, **kwargs)

        # 如果没有请求上下文，创建一个新的翻译器
        translator = get_translator()
        return translator.translate(key, default, **kwargs)

    def _ngettext(self, singular_key: str, plural_key: str, count: int, **kwargs) -> str:
        """翻译复数形式文本

        Args:
            singular_key: 单数形式文本键名
            plural_key: 复数形式文本键名
            count: 数量
            **kwargs: 格式化参数

        Returns:
            str: 翻译后的文本
        """
        key = singular_key if count == 1 else plural_key
        kwargs['count'] = count
        return self._gettext(key, **kwargs)
