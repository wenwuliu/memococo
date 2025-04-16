"""
错误处理中间件模块

提供Flask应用的错误处理中间件，用于捕获和处理Web请求中的错误
"""

import traceback
from flask import Flask, jsonify, render_template, request
from typing import Dict, Any, Callable, Optional, Type, Union

from memococo.common.error_handler import MemoCocoError, ErrorHandler

class ErrorMiddleware:
    """Flask错误处理中间件"""
    
    def __init__(self, app: Flask, logger=None):
        """初始化错误处理中间件
        
        Args:
            app: Flask应用实例
            logger: 日志记录器
        """
        self.app = app
        self.logger = logger
        self.error_handlers = {}
        self.default_handler = None
        
        # 注册错误处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认错误处理器"""
        # 注册通用错误处理器
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            return self._handle_error(e)
        
        # 注册HTTP错误处理器
        for code in [400, 401, 403, 404, 405, 500]:
            @self.app.errorhandler(code)
            def handle_http_error(e):
                return self._handle_error(e)
    
    def register_handler(self, exception_type: Type[Exception], handler: Callable[[Exception], Any]) -> None:
        """注册错误处理函数
        
        Args:
            exception_type: 异常类型
            handler: 处理函数
        """
        self.error_handlers[exception_type] = handler
    
    def set_default_handler(self, handler: Callable[[Exception], Any]) -> None:
        """设置默认错误处理函数
        
        Args:
            handler: 处理函数
        """
        self.default_handler = handler
    
    def _handle_error(self, exception: Exception) -> Union[str, Dict[str, Any]]:
        """处理错误
        
        Args:
            exception: 异常对象
            
        Returns:
            错误响应
        """
        # 记录错误日志
        if self.logger:
            self.logger.error(f"Error: {exception}")
            self.logger.debug(traceback.format_exc())
        
        # 获取请求信息
        request_info = {
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "args": dict(request.args),
            "form": dict(request.form) if request.form else None,
            "json": request.json if request.is_json else None,
        }
        
        # 使用ErrorHandler记录错误
        ErrorHandler.log_error(exception, context={"request": request_info})
        
        # 查找异常类型的处理函数
        handler = None
        for exception_type, h in self.error_handlers.items():
            if isinstance(exception, exception_type):
                handler = h
                break
        
        # 如果没有找到处理函数，使用默认处理函数
        if handler is None:
            handler = self.default_handler
        
        # 如果有处理函数，调用处理函数
        if handler is not None:
            return handler(exception)
        
        # 默认错误处理逻辑
        if request.is_json or request.headers.get('Accept') == 'application/json':
            # 返回JSON格式的错误响应
            error_response = {
                "error": str(exception),
                "type": exception.__class__.__name__,
            }
            
            # 如果是自定义异常，添加详细信息
            if isinstance(exception, MemoCocoError) and hasattr(exception, 'details'):
                error_response["details"] = exception.details
            
            return jsonify(error_response), 500
        else:
            # 返回HTML格式的错误页面
            error_info = {
                "message": str(exception),
                "type": exception.__class__.__name__,
                "traceback": traceback.format_exc() if self.app.debug else None
            }
            
            # 如果是自定义异常，添加详细信息
            if isinstance(exception, MemoCocoError) and hasattr(exception, 'details'):
                error_info["details"] = exception.details
            
            # 尝试渲染错误模板
            try:
                return render_template("error.html", error=error_info), 500
            except Exception:
                # 如果模板不存在，返回简单的错误页面
                return f"""
                <html>
                <head><title>Error</title></head>
                <body>
                    <h1>Error: {exception.__class__.__name__}</h1>
                    <p>{str(exception)}</p>
                    {'<pre>' + traceback.format_exc() + '</pre>' if self.app.debug else ''}
                </body>
                </html>
                """, 500

def setup_error_handling(app: Flask, logger=None) -> ErrorMiddleware:
    """设置Flask应用的错误处理
    
    Args:
        app: Flask应用实例
        logger: 日志记录器
        
    Returns:
        ErrorMiddleware: 错误处理中间件实例
    """
    middleware = ErrorMiddleware(app, logger)
    return middleware
