import concurrent.futures
import time
import multiprocessing

# 获取CPU核心数
cpu_count = multiprocessing.cpu_count()
print(f"CPU核心数: {cpu_count}")

# 创建线程池
executor = concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count * 2)
print(f"创建线程池，线程数: {cpu_count * 2}")

# 模拟耗时任务
def slow_task(task_id, seconds):
    print(f"任务 {task_id} 开始执行，将耗时 {seconds} 秒")
    time.sleep(seconds)
    print(f"任务 {task_id} 执行完成")
    return f"任务 {task_id} 的结果"

# 回调函数
def task_callback(future, task_id):
    try:
        result = future.result()
        print(f"回调函数收到任务 {task_id} 的结果: {result}")
    except Exception as e:
        print(f"任务 {task_id} 执行出错: {e}")

# 提交多个任务
print("\n提交多个任务到线程池...")
futures = []
start_time = time.time()

for i in range(5):
    task_time = i + 1  # 每个任务耗时不同
    future = executor.submit(slow_task, i, task_time)
    future.add_done_callback(lambda f, task_id=i: task_callback(f, task_id))
    futures.append(future)
    print(f"任务 {i} 已提交，预计耗时 {task_time} 秒")

submit_time = time.time() - start_time
print(f"所有任务提交完成，耗时: {submit_time:.4f}秒")

# 等待所有任务完成
print("\n等待所有任务完成...")
concurrent.futures.wait(futures)
total_time = time.time() - start_time
print(f"\n所有任务已完成，总耗时: {total_time:.4f}秒")

# 如果是串行执行，总耗时应该是所有任务耗时之和
serial_time = sum(i + 1 for i in range(5))
print(f"如果串行执行，总耗时应该是: {serial_time}秒")
print(f"并行执行提速: {serial_time / total_time:.2f}倍")

# 关闭线程池
executor.shutdown()
print("线程池已关闭")
