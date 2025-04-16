/**
 * MemoCoco 搜索结果页面功能
 *
 * 处理搜索结果的分页、显示和导航功能
 */

// 搜索控制器命名空间
const SearchController = {
    // 配置
    config: {
        itemsPerPage: 20,
        modalNavigationEnabled: true
    },

    // 数据
    data: {
        entries: [],
        currentPage: 1,
        totalPages: 0,
        currentModalIndex: -1
    },

    // 元素引用
    elements: {
        paginationContainer: null,
        pagination: null,
        totalItems: null,
        totalPages: null,
        resultContainer: null
    },

    /**
     * 初始化搜索控制器
     * @param {Array} entries 搜索结果条目
     * @param {number} itemsPerPage 每页显示的条目数
     */
    init: function(entries, itemsPerPage) {
        // 保存数据
        this.data.entries = entries;
        if (itemsPerPage) {
            this.config.itemsPerPage = itemsPerPage;
        }

        // 计算总页数
        this.data.totalPages = Math.ceil(entries.length / this.config.itemsPerPage);

        // 获取DOM元素
        this.elements.paginationContainer = document.getElementById('pagination-container');
        this.elements.pagination = document.getElementById('pagination');
        this.elements.totalItems = document.getElementById('total-items');
        this.elements.totalPages = document.getElementById('total-pages');
        this.elements.resultContainer = document.getElementById('search-results');

        // 初始化页面
        this.renderPage(1);
        this.renderPagination();

        // 初始化键盘导航
        this.initKeyboardNavigation();

        // 初始化懒加载
        this.initLazyLoad();
    },

    /**
     * 格式化日期
     * @param {number} timestamp 时间戳
     * @returns {string} 格式化后的日期字符串
     */
    formatDate: function(timestamp) {
        const date = new Date(timestamp * 1000);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    },

    /**
     * 渲染指定页码的内容
     * @param {number} page 页码
     */
    renderPage: function(page) {
        // 更新当前页码
        this.data.currentPage = page;

        // 计算起始和结束索引
        const start = (page - 1) * this.config.itemsPerPage;
        const end = Math.min(start + this.config.itemsPerPage, this.data.entries.length);

        // 获取当前页的条目
        const paginatedItems = this.data.entries.slice(start, end);

        // 清空结果容器
        if (this.elements.resultContainer) {
            this.elements.resultContainer.innerHTML = '';
        } else {
            this.elements.resultContainer = document.createElement('div');
            this.elements.resultContainer.id = 'search-results';
            this.elements.resultContainer.className = 'row';
            this.elements.paginationContainer.parentNode.insertBefore(
                this.elements.resultContainer,
                this.elements.paginationContainer
            );
        }

        // 创建结果行
        const rowDiv = document.createElement('div');
        rowDiv.className = 'row';

        // 添加每个条目
        paginatedItems.forEach((entry, index) => {
            const colDiv = document.createElement('div');
            colDiv.className = 'col-md-3 mb-4';

            const formattedDate = this.formatDate(entry[4]);

            // 创建卡片
            colDiv.innerHTML = `
                <div class="card rounded-lg">
                    <a href="#" data-toggle="modal" data-target="#modal-${start + index}">
                        <img data-src="/pictures/${entry[4]}.webp" alt="Image" class="card-img-top lazy-load responsive-img">
                    </a>
                    <div class="card-footer text-muted text-center">
                        ${formattedDate}
                    </div>
                </div>
                <div class="modal fade" id="modal-${start + index}" tabindex="-1" role="dialog" aria-labelledby="modalLabel-${start + index}" aria-hidden="true">
                    <div class="modal-dialog modal-xl" role="document" style="max-width: none; width: 100vw; height: 100vh; padding: 20px;">
                        <div class="modal-content h-100">
                            <div class="modal-header">
                                <h5 class="modal-title" id="modalLabel-${start + index}">${formattedDate}</h5>
                                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div class="modal-body d-flex align-items-center justify-content-center h-100">
                                <div class="image-container" style="width: 100%; height: 100%;">
                                    <img src="/pictures/${entry[4]}.webp" alt="Image" class="no-lazy responsive-img" style="width: 100%; height: 100%; object-fit: contain; margin: 0 auto;">
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                                <button type="button" class="btn btn-primary prev-image" data-index="${start + index}">Previous</button>
                                <button type="button" class="btn btn-primary next-image" data-index="${start + index}">Next</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // 添加到结果行
            rowDiv.appendChild(colDiv);
        });

        // 添加结果行到容器
        this.elements.resultContainer.appendChild(rowDiv);

        // 更新总条目和总页数显示
        if (this.elements.totalItems) {
            this.elements.totalItems.textContent = `Total Items: ${this.data.entries.length}`;
        }

        if (this.elements.totalPages) {
            this.elements.totalPages.textContent = `Total Pages: ${this.data.totalPages}`;
        }

        // 添加模态框导航事件
        this.setupModalNavigation();
    },

    /**
     * 渲染分页控件
     */
    renderPagination: function() {
        if (!this.elements.pagination) return;

        // 清空分页容器
        this.elements.pagination.innerHTML = '';

        // 添加"首页"按钮
        const firstPageItem = document.createElement('li');
        firstPageItem.className = `page-item ${this.data.currentPage === 1 ? 'disabled' : ''}`;
        firstPageItem.innerHTML = `<a class="page-link" href="#" data-page="1">First</a>`;
        this.elements.pagination.appendChild(firstPageItem);

        // 添加"上一页"按钮
        const prevPageItem = document.createElement('li');
        prevPageItem.className = `page-item ${this.data.currentPage === 1 ? 'disabled' : ''}`;
        prevPageItem.innerHTML = `<a class="page-link" href="#" data-page="${this.data.currentPage - 1}">Previous</a>`;
        this.elements.pagination.appendChild(prevPageItem);

        // 计算要显示的页码范围
        let startPage = Math.max(1, this.data.currentPage - 2);
        let endPage = Math.min(this.data.totalPages, startPage + 4);

        // 调整起始页码，确保始终显示5个页码（如果有足够的页数）
        if (endPage - startPage < 4 && this.data.totalPages > 5) {
            startPage = Math.max(1, endPage - 4);
        }

        // 添加页码按钮
        for (let i = startPage; i <= endPage; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = `page-item ${i === this.data.currentPage ? 'active' : ''}`;
            pageItem.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
            this.elements.pagination.appendChild(pageItem);
        }

        // 添加"下一页"按钮
        const nextPageItem = document.createElement('li');
        nextPageItem.className = `page-item ${this.data.currentPage === this.data.totalPages ? 'disabled' : ''}`;
        nextPageItem.innerHTML = `<a class="page-link" href="#" data-page="${this.data.currentPage + 1}">Next</a>`;
        this.elements.pagination.appendChild(nextPageItem);

        // 添加"末页"按钮
        const lastPageItem = document.createElement('li');
        lastPageItem.className = `page-item ${this.data.currentPage === this.data.totalPages ? 'disabled' : ''}`;
        lastPageItem.innerHTML = `<a class="page-link" href="#" data-page="${this.data.totalPages}">Last</a>`;
        this.elements.pagination.appendChild(lastPageItem);

        // 添加页码点击事件
        const pageLinks = this.elements.pagination.querySelectorAll('.page-link');
        pageLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(link.dataset.page);
                if (page >= 1 && page <= this.data.totalPages) {
                    this.changePage(page);
                }
            });
        });
    },

    /**
     * 切换到指定页码
     * @param {number} page 页码
     */
    changePage: function(page) {
        if (page < 1 || page > this.data.totalPages) return;

        // 渲染新页面
        this.renderPage(page);

        // 更新分页控件
        this.renderPagination();

        // 滚动到页面顶部
        window.scrollTo(0, 0);

        // 刷新懒加载
        this.refreshLazyLoad();
    },

    /**
     * 设置模态框导航
     */
    setupModalNavigation: function() {
        if (!this.config.modalNavigationEnabled) return;

        // 获取所有"上一张"按钮
        const prevButtons = document.querySelectorAll('.prev-image');
        prevButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const index = parseInt(button.dataset.index);
                this.navigateModal(index, 'prev');
            });
        });

        // 获取所有"下一张"按钮
        const nextButtons = document.querySelectorAll('.next-image');
        nextButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const index = parseInt(button.dataset.index);
                this.navigateModal(index, 'next');
            });
        });

        // 为模态框添加显示事件
        const modals = document.querySelectorAll('.modal');
        modals.forEach((modal, index) => {
            modal.addEventListener('shown.bs.modal', () => {
                this.data.currentModalIndex = index;
            });
        });
    },

    /**
     * 导航到上一张或下一张图片
     * @param {number} currentIndex 当前索引
     * @param {string} direction 导航方向（'prev'或'next'）
     */
    navigateModal: function(currentIndex, direction) {
        // 计算新索引
        let newIndex;
        if (direction === 'prev') {
            newIndex = currentIndex > 0 ? currentIndex - 1 : this.data.entries.length - 1;
        } else {
            newIndex = currentIndex < this.data.entries.length - 1 ? currentIndex + 1 : 0;
        }

        // 计算新索引所在的页码
        const newPage = Math.floor(newIndex / this.config.itemsPerPage) + 1;

        // 如果需要切换页面
        if (newPage !== this.data.currentPage) {
            // 隐藏当前模态框
            $(`#modal-${currentIndex}`).modal('hide');

            // 切换到新页面
            this.changePage(newPage);

            // 显示新模态框
            setTimeout(() => {
                const newModalIndex = newIndex % this.config.itemsPerPage;
                const actualIndex = (newPage - 1) * this.config.itemsPerPage + newModalIndex;
                $(`#modal-${actualIndex}`).modal('show');
            }, 500);
        } else {
            // 在当前页面内导航
            $(`#modal-${currentIndex}`).modal('hide');
            $(`#modal-${newIndex}`).modal('show');
        }
    },

    /**
     * 初始化键盘导航
     */
    initKeyboardNavigation: function() {
        document.addEventListener('keydown', (e) => {
            // 只有当模态框打开时才处理键盘事件
            if (this.data.currentModalIndex === -1) return;

            // 左箭头：上一张
            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                this.navigateModal(this.data.currentModalIndex, 'prev');
            }

            // 右箭头：下一张
            else if (e.key === 'ArrowRight') {
                e.preventDefault();
                this.navigateModal(this.data.currentModalIndex, 'next');
            }

            // ESC键：关闭模态框
            else if (e.key === 'Escape') {
                $(`#modal-${this.data.currentModalIndex}`).modal('hide');
                this.data.currentModalIndex = -1;
            }
        });
    },

    /**
     * 初始化懒加载
     */
    initLazyLoad: function() {
        document.addEventListener('DOMContentLoaded', function() {
            if (window.lazyLoader) {
                window.lazyLoader.refresh();
            }
        });
    },

    /**
     * 刷新懒加载
     */
    refreshLazyLoad: function() {
        if (window.lazyLoader) {
            setTimeout(() => {
                window.lazyLoader.refresh();
            }, 100);
        }
    }
};

// 当DOM加载完成后初始化搜索控制器
document.addEventListener('DOMContentLoaded', function() {
    // 检查是否存在搜索结果数据
    const entriesElement = document.getElementById('search-entries-data');
    if (entriesElement && entriesElement.dataset.entries) {
        try {
            const entries = JSON.parse(entriesElement.dataset.entries);
            if (Array.isArray(entries)) {
                SearchController.init(entries);
            } else {
                console.error('Search entries data is not an array:', entries);
                SearchController.init([]);
            }
        } catch (error) {
            console.error('Error parsing search entries data:', error);
            // 初始化搜索控制器为空数组
            SearchController.init([]);
        }
    } else {
        console.warn('No search entries data found');
        SearchController.init([]);
    }
});
