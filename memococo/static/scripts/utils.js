/**
 * MemoCoco 工具函数
 * 
 * 提供通用的工具函数和辅助方法
 */

// 工具函数命名空间
const MemoCocoUtils = {
    /**
     * 格式化日期时间
     * @param {number} timestamp 时间戳（秒）
     * @param {string} format 格式化模式（'full', 'date', 'time', 'short'）
     * @returns {string} 格式化后的日期时间字符串
     */
    formatDateTime: function(timestamp, format = 'full') {
        const date = new Date(timestamp * 1000);
        
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        
        switch (format) {
            case 'date':
                return `${year}-${month}-${day}`;
            case 'time':
                return `${hours}:${minutes}:${seconds}`;
            case 'short':
                return `${month}-${day} ${hours}:${minutes}`;
            case 'full':
            default:
                return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        }
    },
    
    /**
     * 格式化文件大小
     * @param {number} bytes 字节数
     * @param {number} decimals 小数位数
     * @returns {string} 格式化后的文件大小字符串
     */
    formatFileSize: function(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    },
    
    /**
     * 获取相对时间描述
     * @param {number} timestamp 时间戳（秒）
     * @returns {string} 相对时间描述
     */
    getRelativeTimeDescription: function(timestamp) {
        const now = Math.floor(Date.now() / 1000);
        const diff = now - timestamp;
        
        if (diff < 60) {
            return '刚刚';
        } else if (diff < 3600) {
            const minutes = Math.floor(diff / 60);
            return `${minutes}分钟前`;
        } else if (diff < 86400) {
            const hours = Math.floor(diff / 3600);
            return `${hours}小时前`;
        } else if (diff < 172800) {
            return '昨天';
        } else {
            const days = Math.floor(diff / 86400);
            return `${days}天前`;
        }
    },
    
    /**
     * 防抖函数
     * @param {Function} func 要执行的函数
     * @param {number} wait 等待时间（毫秒）
     * @returns {Function} 防抖处理后的函数
     */
    debounce: function(func, wait) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    },
    
    /**
     * 节流函数
     * @param {Function} func 要执行的函数
     * @param {number} limit 限制时间（毫秒）
     * @returns {Function} 节流处理后的函数
     */
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const context = this;
            const args = arguments;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    /**
     * 复制文本到剪贴板
     * @param {string} text 要复制的文本
     * @returns {boolean} 是否复制成功
     */
    copyToClipboard: function(text) {
        try {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            const success = document.execCommand('copy');
            document.body.removeChild(textArea);
            return success;
        } catch (err) {
            console.error('Failed to copy text: ', err);
            return false;
        }
    },
    
    /**
     * 显示通知提示
     * @param {string} message 提示消息
     * @param {string} type 提示类型（'success', 'error', 'info', 'warning'）
     * @param {number} duration 显示时长（毫秒）
     */
    showToast: function(message, type = 'info', duration = 3000) {
        // 创建toast元素
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        // 设置样式
        toast.style.position = 'fixed';
        toast.style.bottom = '20px';
        toast.style.left = '50%';
        toast.style.transform = 'translateX(-50%)';
        toast.style.padding = '10px 20px';
        toast.style.borderRadius = '5px';
        toast.style.color = 'white';
        toast.style.zIndex = '9999';
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease-in-out';
        
        // 根据类型设置背景色
        switch (type) {
            case 'success':
                toast.style.backgroundColor = 'rgba(40, 167, 69, 0.9)';
                break;
            case 'error':
                toast.style.backgroundColor = 'rgba(220, 53, 69, 0.9)';
                break;
            case 'warning':
                toast.style.backgroundColor = 'rgba(255, 193, 7, 0.9)';
                break;
            case 'info':
            default:
                toast.style.backgroundColor = 'rgba(23, 162, 184, 0.9)';
                break;
        }
        
        // 添加到页面
        document.body.appendChild(toast);
        
        // 显示toast
        setTimeout(() => {
            toast.style.opacity = '1';
        }, 10);
        
        // 设置定时器，自动移除toast
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, duration);
    },
    
    /**
     * 获取URL参数
     * @param {string} name 参数名
     * @returns {string|null} 参数值，如果不存在则返回null
     */
    getUrlParameter: function(name) {
        const url = window.location.href;
        name = name.replace(/[\[\]]/g, '\\$&');
        const regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)');
        const results = regex.exec(url);
        if (!results) return null;
        if (!results[2]) return '';
        return decodeURIComponent(results[2].replace(/\+/g, ' '));
    },
    
    /**
     * 检测设备类型
     * @returns {string} 设备类型（'mobile', 'tablet', 'desktop'）
     */
    getDeviceType: function() {
        const userAgent = navigator.userAgent.toLowerCase();
        const isMobile = /iphone|ipod|android|blackberry|opera mini|iemobile|mobile/.test(userAgent);
        const isTablet = /ipad|tablet/.test(userAgent);
        
        if (isMobile) return 'mobile';
        if (isTablet) return 'tablet';
        return 'desktop';
    },
    
    /**
     * 检测浏览器类型
     * @returns {string} 浏览器类型
     */
    getBrowserType: function() {
        const userAgent = navigator.userAgent;
        
        if (userAgent.indexOf('Firefox') > -1) {
            return 'Firefox';
        } else if (userAgent.indexOf('Chrome') > -1) {
            return 'Chrome';
        } else if (userAgent.indexOf('Safari') > -1) {
            return 'Safari';
        } else if (userAgent.indexOf('MSIE') > -1 || userAgent.indexOf('Trident') > -1) {
            return 'IE';
        } else if (userAgent.indexOf('Edge') > -1) {
            return 'Edge';
        } else {
            return 'Unknown';
        }
    },
    
    /**
     * 检测是否支持WebP格式
     * @returns {Promise<boolean>} 是否支持WebP
     */
    supportsWebP: function() {
        return new Promise(resolve => {
            const webP = new Image();
            webP.onload = webP.onerror = function() {
                resolve(webP.height === 2);
            };
            webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
        });
    }
};

// 导出工具函数
window.MemoCocoUtils = MemoCocoUtils;
