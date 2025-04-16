/**
 * MemoCoco 图片懒加载和渐进式加载
 * 
 * 提供图片懒加载功能，减少初始加载时间，提高用户体验
 */

// 检查浏览器是否支持 IntersectionObserver API
const supportsIntersectionObserver = 'IntersectionObserver' in window;

// 懒加载图片类
class LazyLoader {
  constructor(options = {}) {
    this.options = {
      rootMargin: '0px 0px 200px 0px', // 提前200px加载
      threshold: 0.1,                  // 当10%的图片可见时加载
      selector: '.lazy-load',          // 懒加载图片的选择器
      ...options
    };
    
    this.images = [];
    this.observer = null;
    this.initialized = false;
  }
  
  /**
   * 初始化懒加载
   */
  init() {
    if (this.initialized) return;
    
    this.images = Array.from(document.querySelectorAll(this.options.selector));
    
    if (supportsIntersectionObserver) {
      this.observer = new IntersectionObserver(this._onIntersection.bind(this), {
        rootMargin: this.options.rootMargin,
        threshold: this.options.threshold
      });
      
      this.images.forEach(image => {
        if (image.classList.contains('loaded')) return;
        this.observer.observe(image);
      });
    } else {
      // 回退方案：立即加载所有图片
      this._loadImagesImmediately(this.images);
    }
    
    // 添加滚动事件监听（用于不支持 IntersectionObserver 的浏览器）
    if (!supportsIntersectionObserver) {
      window.addEventListener('scroll', this._throttle(this._checkImages.bind(this), 200));
      window.addEventListener('resize', this._throttle(this._checkImages.bind(this), 200));
    }
    
    this.initialized = true;
  }
  
  /**
   * 当图片进入视口时的回调
   * @param {IntersectionObserverEntry[]} entries 
   */
  _onIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        this._loadImage(entry.target);
        this.observer.unobserve(entry.target);
      }
    });
  }
  
  /**
   * 加载单个图片
   * @param {HTMLImageElement} image 
   */
  _loadImage(image) {
    const src = image.dataset.src;
    if (!src) return;
    
    // 创建新图片预加载
    const img = new Image();
    
    img.onload = () => {
      image.src = src;
      image.classList.add('loaded');
      this._removeImageFromArray(image);
    };
    
    img.onerror = () => {
      console.error('Failed to load image:', src);
      image.classList.add('error');
      this._removeImageFromArray(image);
    };
    
    img.src = src;
  }
  
  /**
   * 立即加载所有图片（不使用懒加载）
   * @param {HTMLImageElement[]} images 
   */
  _loadImagesImmediately(images) {
    images.forEach(image => this._loadImage(image));
  }
  
  /**
   * 从图片数组中移除已加载的图片
   * @param {HTMLImageElement} image 
   */
  _removeImageFromArray(image) {
    const index = this.images.indexOf(image);
    if (index !== -1) {
      this.images.splice(index, 1);
    }
  }
  
  /**
   * 检查图片是否在视口中
   */
  _checkImages() {
    if (this.images.length === 0) return;
    
    this.images.forEach(image => {
      if (this._isInViewport(image)) {
        this._loadImage(image);
      }
    });
  }
  
  /**
   * 检查元素是否在视口中
   * @param {HTMLElement} element 
   * @returns {boolean}
   */
  _isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
      rect.top <= (window.innerHeight || document.documentElement.clientHeight) + 200 &&
      rect.left <= (window.innerWidth || document.documentElement.clientWidth) &&
      rect.bottom >= 0 &&
      rect.right >= 0
    );
  }
  
  /**
   * 节流函数，限制函数调用频率
   * @param {Function} func 
   * @param {number} limit 
   * @returns {Function}
   */
  _throttle(func, limit) {
    let lastCall = 0;
    return function(...args) {
      const now = Date.now();
      if (now - lastCall >= limit) {
        lastCall = now;
        func.apply(this, args);
      }
    };
  }
  
  /**
   * 添加新图片到懒加载队列
   * @param {HTMLImageElement[]} newImages 
   */
  addImages(newImages) {
    if (!this.initialized) {
      this.init();
    }
    
    newImages.forEach(image => {
      if (!image.classList.contains('loaded') && !this.images.includes(image)) {
        this.images.push(image);
        if (this.observer) {
          this.observer.observe(image);
        } else if (this._isInViewport(image)) {
          this._loadImage(image);
        }
      }
    });
  }
  
  /**
   * 刷新所有图片
   */
  refresh() {
    if (this.observer) {
      this.images.forEach(image => {
        this.observer.unobserve(image);
      });
    }
    
    this.images = Array.from(document.querySelectorAll(this.options.selector));
    
    if (this.observer) {
      this.images.forEach(image => {
        if (!image.classList.contains('loaded')) {
          this.observer.observe(image);
        }
      });
    } else {
      this._checkImages();
    }
  }
}

// 创建全局懒加载实例
const lazyLoader = new LazyLoader();

// 当DOM加载完成后初始化懒加载
document.addEventListener('DOMContentLoaded', () => {
  lazyLoader.init();
});

// 暴露全局API
window.lazyLoader = lazyLoader;
