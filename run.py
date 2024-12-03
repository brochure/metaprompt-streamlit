# run.py
import os
import signal
import subprocess
import sys
import threading
import time
from typing import List

from loguru import logger


class ApplicationRunner:
    """管理前后端应用进程的运行器"""

    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.should_run = True

    def stream_process_output(self, process: subprocess.Popen, prefix: str) -> None:
        """实时流式输出进程日志"""

        def stream_output(pipe, prefix):
            for line in iter(pipe.readline, ''):
                if line.strip():
                    logger.info(f"{prefix} | {line.strip()}")

        # 创建两个线程分别处理stdout和stderr
        threading.Thread(
            target=stream_output,
            args=(process.stdout, prefix),
            daemon=True
        ).start()

        threading.Thread(
            target=stream_output,
            args=(process.stderr, prefix),
            daemon=True
        ).start()

    def start_backend(self) -> None:
        """启动FastAPI后端"""
        try:
            logger.info("Starting backend server...")
            backend_host = os.getenv("BACKEND_HOST", "0.0.0.0")
            backend_port = os.getenv("BACKEND_PORT", "8000")
            backend_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", backend_host, "--port",
                 backend_port],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # 行缓冲
                universal_newlines=True
            )
            self.processes.append(backend_process)
            self.stream_process_output(backend_process, "Backend")
            logger.info(f"Backend server started at http://{backend_host}:{backend_port}")
        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            self.cleanup()
            sys.exit(1)

    def start_frontend(self) -> None:
        """启动Streamlit前端"""
        try:
            logger.info("Starting frontend server...")
            frontend_host = os.getenv("FRONTEND_HOST", "0.0.0.0")
            frontend_port = os.getenv("FRONTEND_PORT", "8501")
            frontend_process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py", "--server.address", frontend_host, "--server.port", frontend_port],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # 行缓冲
                universal_newlines=True
            )
            self.processes.append(frontend_process)
            self.stream_process_output(frontend_process, "Frontend")
            logger.info(f"Frontend server started at http://{frontend_host}:{frontend_port}")
        except Exception as e:
            logger.error(f"Failed to start frontend: {e}")
            self.cleanup()
            sys.exit(1)

    def cleanup(self) -> None:
        """清理所有子进程"""
        logger.info("Cleaning up processes...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {process.args} did not terminate gracefully, forcing kill")
                process.kill()
            except Exception as e:
                logger.error(f"Error while terminating process: {e}")
        self.processes.clear()
        logger.info("All processes cleaned up")

    def signal_handler(self, signum, frame) -> None:
        """处理终止信号"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.should_run = False
        self.cleanup()
        sys.exit(0)

    def monitor_processes(self) -> None:
        """监控子进程状态"""
        while self.should_run:
            for process in self.processes:
                if process.poll() is not None:
                    logger.error(f"Process {process.args} terminated unexpectedly")
                    self.cleanup()
                    sys.exit(1)
            time.sleep(1)

    def run(self) -> None:
        """运行应用"""
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        try:
            # 启动服务
            self.start_backend()
            time.sleep(2)  # 等待后端启动
            self.start_frontend()

            logger.info("All services are running. Press Ctrl+C to stop.")

            # 监控进程
            self.monitor_processes()

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.cleanup()


if __name__ == "__main__":
    # 配置日志
    logger.remove()  # 移除默认的日志处理器

    # 添加控制台输出处理器
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True,
        level="INFO"
    )

    # 添加文件日志处理器
    # logger.add(
    #     "app.log",
    #     format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    #     rotation="500 MB",
    #     retention="10 days",
    #     level="INFO"
    # )

    logger.info("Starting application...")

    # 运行应用
    runner = ApplicationRunner()
    runner.run()
