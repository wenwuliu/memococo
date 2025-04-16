/**
 * MemoCoco 时间轴功能
 *
 * 处理时间轴滑块、时间节点和图片加载等功能
 */

// 时间轴控制器命名空间
const TimelineController = {
    // 元素引用
    elements: {
        container: null,
        slider: null,
        sliderValue: null,
        timestampImage: null,
        timeNodes: null,
        appList: null,
        toggleAppsButton: null
    },

    // 数据
    data: {
        timestamps: [],
        timeoutId: null,
        imgWidth: 0,
        imgHeight: 0
    },

    /**
     * 初始化时间轴控制器
     * @param {Array} timestamps 时间戳数组
     */
    init: function(timestamps) {
        // 保存时间戳数据
        this.data.timestamps = timestamps;

        // 获取DOM元素
        this.elements.container = document.getElementById('image-container');
        this.elements.slider = document.getElementById('discreteSlider');
        this.elements.sliderValue = document.getElementById('sliderValue');
        this.elements.timestampImage = document.getElementById('timestampImage');
        this.elements.timeNodes = document.querySelectorAll('.time-node');
        this.elements.appList = document.getElementById('app-list');
        this.elements.toggleAppsButton = document.getElementById('toggle-apps');

        // 设置初始值
        this.setInitialValues();

        // 绑定事件
        this.bindEvents();

        // 初始化时间节点
        this.initTimeNodes();

        // 初始化应用列表
        this.initAppList();
    },

    /**
     * 设置初始值
     */
    setInitialValues: function() {
        // 设置滑块初始值为最新的时间戳
        this.elements.slider.value = this.data.timestamps.length - 1;

        // 获取初始时间戳
        const initialIndex = 0; // 最新的时间戳索引
        const initialTimestamp = this.data.timestamps[initialIndex];

        // 设置时间显示
        this.elements.sliderValue.textContent = this.formatTimestamp(initialTimestamp);

        // 加载初始图片
        this.elements.timestampImage.src = `/pictures/${initialTimestamp}.webp`;
    },

    /**
     * 绑定事件
     */
    bindEvents: function() {
        // 滑块输入事件
        this.elements.slider.addEventListener('input', this.handleSliderInput.bind(this));

        // 图片加载完成事件
        this.elements.timestampImage.addEventListener('load', this.handleImageLoad.bind(this));

        // 应用列表切换事件
        if (this.elements.toggleAppsButton) {
            this.elements.toggleAppsButton.addEventListener('click', this.toggleApps.bind(this));
        }
    },

    /**
     * 处理滑块输入事件
     */
    handleSliderInput: function() {
        // 获取当前选中的时间戳
        const reversedIndex = this.data.timestamps.length - 1 - this.elements.slider.value;
        const timestamp = this.data.timestamps[reversedIndex];

        // 更新时间显示
        this.elements.sliderValue.textContent = this.formatTimestamp(timestamp);

        // 清除之前的框线
        const highlights = document.querySelectorAll('.highlight');
        highlights.forEach(highlight => highlight.remove());

        // 清除之前的文本标签
        const textLabels = document.querySelectorAll('.text-label');
        textLabels.forEach(textLabel => textLabel.remove());

        // 清除之前的定时器
        clearTimeout(this.data.timeoutId);

        // 设置新的定时器，延迟加载图片
        this.data.timeoutId = setTimeout(() => {
            this.elements.timestampImage.src = `/pictures/${timestamp}.webp`;
            // 更新时间节点位置
            this.updateTimeNodePositions();
        }, 200);
    },

    /**
     * 处理图片加载完成事件
     */
    handleImageLoad: function() {
        const reversedIndex = this.data.timestamps.length - 1 - this.elements.slider.value;
        const timestamp = this.data.timestamps[reversedIndex];

        // 保存图片尺寸
        this.data.imgWidth = this.elements.timestampImage.naturalWidth;
        this.data.imgHeight = this.elements.timestampImage.naturalHeight;

        // 延时执行，确保图片完全加载
        setTimeout(() => {
            this.updateText(timestamp);
        }, 500);
    },

    /**
     * 初始化时间节点
     */
    initTimeNodes: function() {
        // 确保所有时间节点文本可见
        this.elements.timeNodes.forEach(node => {
            node.style.opacity = '1';
            node.style.visibility = 'visible';
            node.style.display = 'block';
        });

        // 计算时间节点位置
        this.updateTimeNodePositions();

        // 为每个时间节点添加点击事件
        this.elements.timeNodes.forEach(node => {
            node.addEventListener('click', this.handleTimeNodeClick.bind(this, node));
        });
    },

    /**
     * 处理时间节点点击事件
     * @param {HTMLElement} node 被点击的时间节点元素
     */
    handleTimeNodeClick: function(node) {
        const timestamp = parseInt(node.dataset.timestamp);
        const timestampIndex = this.data.timestamps.indexOf(timestamp);

        if (timestampIndex !== -1) {
            // 计算滑块的新值
            const newSliderValue = this.data.timestamps.length - 1 - timestampIndex;

            // 设置滑块值
            this.elements.slider.value = newSliderValue;

            // 更新时间显示
            this.elements.sliderValue.textContent = this.formatTimestamp(timestamp);

            // 加载图片
            this.elements.timestampImage.src = `/pictures/${timestamp}.webp`;
        }
    },

    /**
     * 更新时间节点位置
     */
    updateTimeNodePositions: function() {
        const sliderWidth = this.elements.slider.offsetWidth;
        const timeNodesContainer = document.getElementById('timeNodes');

        if (!timeNodesContainer) return;

        this.elements.timeNodes.forEach(node => {
            const timestamp = parseInt(node.dataset.timestamp);
            const timestampIndex = this.data.timestamps.indexOf(timestamp);

            if (timestampIndex !== -1) {
                // 计算节点在滑块上的位置百分比
                const position = ((this.data.timestamps.length - 1 - timestampIndex) / (this.data.timestamps.length - 1)) * 100;

                // 设置节点位置
                node.style.left = `${position}%`;
            }
        });
    },

    /**
     * 初始化应用列表
     */
    initAppList: function() {
        if (!this.elements.appList) return;

        const apps = this.elements.appList.children;
        const maxVisibleApps = Math.min(15, apps.length);

        // 只有当应用数量超过15个时才需要隐藏和显示展开按钮
        if (apps.length <= maxVisibleApps) {
            if (this.elements.toggleAppsButton) {
                this.elements.toggleAppsButton.style.display = 'none';
            }
        } else {
            for (let i = maxVisibleApps; i < apps.length; i++) {
                apps[i].style.display = 'none';
            }
        }
    },

    /**
     * 切换应用列表展开/折叠状态
     */
    toggleApps: function() {
        const apps = this.elements.appList.children;
        const maxVisibleApps = Math.min(15, apps.length);

        // 获取展开/折叠文本
        const expandText = this.elements.toggleAppsButton.getAttribute('data-expand-text') || '展开';
        const collapseText = this.elements.toggleAppsButton.getAttribute('data-collapse-text') || '折叠';

        let isExpanded = this.elements.toggleAppsButton.textContent === collapseText;

        if (isExpanded) {
            // 折叠应用列表
            for (let i = maxVisibleApps; i < apps.length; i++) {
                apps[i].style.display = 'none';
            }
            this.elements.toggleAppsButton.textContent = expandText;
        } else {
            // 展开应用列表
            for (let i = 0; i < apps.length; i++) {
                apps[i].style.display = 'inline-block';
            }
            this.elements.toggleAppsButton.textContent = collapseText;
        }
    },

    /**
     * 格式化时间戳为本地日期时间字符串
     * @param {number} timestamp 时间戳
     * @returns {string} 格式化后的日期时间字符串
     */
    formatTimestamp: function(timestamp) {
        return new Date(timestamp * 1000).toLocaleString();
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
     * 更新文本标签
     * @param {number} timestamp 时间戳
     */
    updateText: async function(timestamp) {
        // 清除现有文本标签
        const textLabels = document.querySelectorAll('.text-label');
        textLabels.forEach(textLabel => textLabel.remove());

        // 清除现有高亮框
        const highlights = document.querySelectorAll('.highlight');
        highlights.forEach(highlight => highlight.remove());

        // 获取OCR数据
        const data = await this.fetchData(timestamp);

        // 数据为空时，不执行下面的代码
        if (!data || data.length === 0) {
            console.log('没有OCR数据');
            return;
        }

        // 获取图片容器的尺寸
        const containerRect = this.elements.container.getBoundingClientRect();
        const containerWidth = containerRect.width;
        const containerHeight = containerRect.height;

        // 计算缩放比例
        const scaleX = containerWidth / this.data.imgWidth;
        const scaleY = containerHeight / this.data.imgHeight;

        // 处理每个OCR文本框
        data.forEach(item => {
            // 兼容不同的数据格式
            let box, text;

            if (Array.isArray(item)) {
                // 如果是数组格式 [coords, text, accuracy]
                const [coords, textValue] = item;
                box = coords.slice(0, 4); // 取前4个值作为坐标
                text = textValue;
            } else if (typeof item === 'object') {
                // 如果是对象格式 {box, text}
                box = item.box;
                text = item.text;
            } else {
                // 其他格式，跳过
                return;
            }

            // 如果没有有效的box或text，跳过
            if (!box || !text) return;

            // 计算缩放后的坐标
            const scaledX = box[0] * scaleX;
            const scaledY = box[1] * scaleY;
            const scaledWidth = (box[2] - box[0]) * scaleX;
            const scaledHeight = (box[3] - box[1]) * scaleY;

            // 创建高亮框
            const highlight = document.createElement('div');
            highlight.className = 'highlight';
            highlight.style.left = `${scaledX}px`;
            highlight.style.top = `${scaledY}px`;
            highlight.style.width = `${scaledWidth}px`;
            highlight.style.height = `${scaledHeight}px`;

            // 创建文本标签
            const textLabel = document.createElement('div');
            textLabel.className = 'text-label';
            textLabel.textContent = text;
            textLabel.style.left = `${scaledX}px`;
            textLabel.style.top = `${scaledY + scaledHeight}px`;
            textLabel.style.maxWidth = `${scaledWidth * 2}px`;

            // 添加点击事件，实现复制文本功能
            textLabel.addEventListener('click', function() {
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);

                // 显示复制成功提示
                const toast = document.createElement('div');
                toast.className = 'toast';
                toast.textContent = document.body.getAttribute('data-text-copied') || '文本已复制';
                toast.style.position = 'fixed';
                toast.style.bottom = '20px';
                toast.style.left = '50%';
                toast.style.transform = 'translateX(-50%)';
                toast.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
                toast.style.color = 'white';
                toast.style.padding = '10px 20px';
                toast.style.borderRadius = '5px';
                toast.style.zIndex = '9999';
                document.body.appendChild(toast);

                // 2秒后移除提示
                setTimeout(() => {
                    document.body.removeChild(toast);
                }, 2000);
            });

            // 将元素添加到页面中
            this.elements.container.appendChild(highlight);
            this.elements.container.appendChild(textLabel);
        });
    },

    /**
     * 从后台接口获取OCR数据
     * @param {number} timestamp 时间戳
     * @returns {Promise<Array>} OCR数据数组
     */
    fetchData: async function(timestamp) {
        try {
            const response = await fetch('/get_ocr_text/' + timestamp);
            if (!response.ok) {
                const errorMessage = document.body.getAttribute('data-network-error') || '网络响应错误';
                throw new Error(errorMessage);
            }
            const data = await response.json();
            return data;
        } catch (error) {
            const errorPrefix = document.body.getAttribute('data-fetch-error') || '获取数据失败';
            console.error(`${errorPrefix}:`, error);
            return [];
        }
    }
};

// 当DOM加载完成后初始化时间轴控制器
document.addEventListener('DOMContentLoaded', function() {
    // 检查是否存在时间戳数据
    const timestampsElement = document.getElementById('timestamps-data');
    if (timestampsElement) {
        const timestamps = JSON.parse(timestampsElement.dataset.timestamps);
        TimelineController.init(timestamps);
    }

    // 显示闪屏模态框（如果存在）
    const flashModal = document.getElementById('flashModal');
    if (flashModal) {
        $('#flashModal').modal('show');
    }
});
