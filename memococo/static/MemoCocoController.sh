#!/usr/bin/zsh
# author:
# desc:
# create date:2025-02-07 17:15:25

APP_NAME=memococo
# 日志文件路径
LOG_FILE="${HOME}/.local/share/MemoCoco/memococo.log"

# 如果是-h参数，则打印帮助信息
if [ "$1" = "-h" ]; then
    echo "Usage: $0 [start|stop|restart|update|status|logs]"
    exit 0
fi

#启动命令为 python3 -m memococo.app
start() {
    #检查是否已经启动，如果已经启动，则打印错误信息
    if pgrep -f ${APP_NAME}.app > /dev/null; then
        echo "${APP_NAME} is already running."
        exit 1
    fi
    echo "Starting ${APP_NAME}..."
    #后台启动，并将日志输出到.local/APP_NAME/APP_NAME.log
    nohup python3 -m ${APP_NAME}.app > /dev/null 2>&1 &
    if [ $? -ne 0 ]; then
        echo "Failed to start ${APP_NAME}."
    fi
}

#停止命令为 pkill -f memococo.app，如果停止失败，则打印错误信息
stop() {
    echo "Stopping ${APP_NAME}..."
    pkill -f ${APP_NAME}.app
    if [ $? -ne 0 ]; then
        echo "Failed to stop ${APP_NAME}."
    fi
}

#重启命令为先停止，再启动
restart() {
    stop
    start
}

#更新命令为python3 -m pip install --upgrade --no-cache-dir git+https://e.coding.net/liuwenwu/projectLiu/MemoCoco.git
update() {
    echo "Updating ${APP_NAME}..."
    python3 -m pip install --upgrade --no-cache-dir git+https://github.com/wenwuliu/memococo.git
}

#状态命令为检查是否已经启动
status() {
    if pgrep -f ${APP_NAME}.app > /dev/null; then
        echo "${APP_NAME} is running."
    else
        echo "${APP_NAME} is not running."
    fi
}

#查看日志命令
logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "Log file not found: $LOG_FILE"
    fi
}


#根据参数执行相应的命令
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    update)
        update
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "Usage: $0 [start|stop|restart|update|status|logs]"
        exit 1
        ;;
esac
