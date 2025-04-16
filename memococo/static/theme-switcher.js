/**
 * MemoCoco 主题切换器
 *
 * 提供明亮模式和暗黑模式的切换功能
 */

class ThemeSwitcher {
  constructor() {
    this.darkModeClass = 'dark-mode';
    this.storageKey = 'memococo-theme';
    this.themes = {
      light: 'light',
      dark: 'dark',
      system: 'system'
    };
    this.currentTheme = this._getStoredTheme() || this.themes.light;
    this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    this.initialized = false;
  }

  /**
   * 初始化主题切换器
   */
  init() {
    if (this.initialized) return;

    // 应用保存的主题或系统主题
    this._applyTheme();

    // 监听系统主题变化
    this.mediaQuery.addEventListener('change', () => {
      if (this.currentTheme === this.themes.system) {
        this._applySystemTheme();
      }
    });

    this.initialized = true;
  }

  /**
   * 切换主题
   * @param {string} theme 主题名称：'light', 'dark', 'system'
   */
  switchTheme(theme) {
    if (!Object.values(this.themes).includes(theme)) {
      console.error('Invalid theme:', theme);
      return;
    }

    this.currentTheme = theme;
    this._storeTheme(theme);
    this._applyTheme();

    // 触发主题变更事件
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  }

  /**
   * 获取当前主题
   * @returns {string} 当前主题名称
   */
  getCurrentTheme() {
    return this.currentTheme;
  }

  /**
   * 获取当前实际应用的主题（考虑系统主题）
   * @returns {string} 'light' 或 'dark'
   */
  getEffectiveTheme() {
    if (this.currentTheme === this.themes.system) {
      return this.mediaQuery.matches ? this.themes.dark : this.themes.light;
    }
    return this.currentTheme;
  }

  /**
   * 应用主题
   * @private
   */
  _applyTheme() {
    if (this.currentTheme === this.themes.system) {
      this._applySystemTheme();
    } else if (this.currentTheme === this.themes.dark) {
      document.documentElement.classList.add(this.darkModeClass);
      document.body.classList.add(this.darkModeClass);
    } else {
      document.documentElement.classList.remove(this.darkModeClass);
      document.body.classList.remove(this.darkModeClass);
    }
  }

  /**
   * 应用系统主题
   * @private
   */
  _applySystemTheme() {
    if (this.mediaQuery.matches) {
      document.documentElement.classList.add(this.darkModeClass);
      document.body.classList.add(this.darkModeClass);
    } else {
      document.documentElement.classList.remove(this.darkModeClass);
      document.body.classList.remove(this.darkModeClass);
    }
  }

  /**
   * 保存主题到本地存储
   * @param {string} theme
   * @private
   */
  _storeTheme(theme) {
    try {
      localStorage.setItem(this.storageKey, theme);
    } catch (error) {
      console.error('Failed to store theme preference:', error);
    }
  }

  /**
   * 从本地存储获取主题
   * @returns {string|null}
   * @private
   */
  _getStoredTheme() {
    try {
      return localStorage.getItem(this.storageKey);
    } catch (error) {
      console.error('Failed to get stored theme preference:', error);
      return null;
    }
  }

  /**
   * 切换到下一个主题
   * 按照 light -> dark -> system -> light 的顺序循环
   */
  toggleTheme() {
    const themes = Object.values(this.themes);
    const currentIndex = themes.indexOf(this.currentTheme);
    const nextIndex = (currentIndex + 1) % themes.length;
    this.switchTheme(themes[nextIndex]);
  }
}

// 创建全局主题切换器实例
const themeSwitcher = new ThemeSwitcher();

// 在页面加载前就应用主题，避免闪烁
(function() {
  // 获取存储的主题
  let theme;
  try {
    theme = localStorage.getItem('memococo-theme');
  } catch (e) {
    theme = 'light';
  }

  // 如果是系统主题，检查系统设置
  if (theme === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (prefersDark) {
      document.documentElement.classList.add('dark-mode');
    }
  }
  // 如果是暗色主题，直接应用
  else if (theme === 'dark') {
    document.documentElement.classList.add('dark-mode');
  }
})();

// 当DOM加载完成后初始化主题切换器
document.addEventListener('DOMContentLoaded', () => {
  themeSwitcher.init();
});

// 暴露全局API
window.themeSwitcher = themeSwitcher;
