#!/bin/bash

# IntelliScrape 后端服务统一启动脚本 (开发环境)
# -------------------------------------------------
# 本脚本旨在方便地在本地一键启动所有必要的后端服务。
#
# 使用方法:
# 1. 确保你已经创建了Python虚拟环境，并安装了所有在 requirements.txt 中的依赖。
#    pip install -r requirements.txt
# 2. 确保所有依赖的基础设施服务（PostgreSQL, RabbitMQ, Redis）正在运行。
#    (推荐使用 Docker Compose 来管理这些服务)
# 3. 在终端中运行此脚本: ./run_dev.sh
#
# 注意: 本脚本会启动多个后台进程。你可以使用 'jobs' 命令查看它们，
# 并使用 'kill %<job_number>' 来停止某个特定的服务。
# 或者，使用 'pkill -f uvicorn' 和 'pkill -f celery' 来停止所有相关进程。
# -------------------------------------------------

echo "🚀 开始启动 IntelliScrape 后端服务..."

# 启动 BFF 服务 (端口: 8000)
echo "启动 BFF Service (http://localhost:8000)"
uvicorn services.bff.main:app --host 0.0.0.0 --port 8000 --reload > bff_service.log 2>&1 &
BFF_PID=$!

# 启动 Discovery 服务 (端口: 8001)
echo "启动 Discovery Service (http://localhost:8001)"
uvicorn services.discovery_svc.main:app --host 0.0.0.0 --port 8001 --reload > discovery_service.log 2>&1 &
DISCOVERY_PID=$!

# 启动 Celery Worker (Orchestrator)
# a concurrency of 2 means it can run two tasks at the same time.
echo "启动 Orchestrator Service (Celery Worker)"
celery -A services.orchestrator.celery_app worker --loglevel=info -c 2 > orchestrator_worker.log 2>&1 &
CELERY_WORKER_PID=$!

# (可选) 启动 Celery Beat (用于周期性任务)
# echo "启动 Celery Beat Scheduler"
# celery -A services.orchestrator.celery_app beat --loglevel=info > celery_beat.log 2>&1 &
# CELERY_BEAT_PID=$!

# 启动 Extractor 服务 (消费者)
echo "启动 Extractor Service (Consumer)"
python services/extractor_svc/consumer.py > extractor_consumer.log 2>&1 &
EXTRACTOR_PID=$!


echo "✅ 所有后端服务已启动。"
echo "-------------------------------------------------"
echo "服务日志文件:"
echo "  - BFF Service:         bff_service.log"
echo "  - Discovery Service:   discovery_service.log"
echo "  - Orchestrator Worker: orchestrator_worker.log"
echo "  - Extractor Consumer:  extractor_consumer.log"
echo "-------------------------------------------------"
echo "前端开发提示:"
echo "1. cd services/frontend"
echo "2. npm install"
echo "3. npm run dev"
echo "-------------------------------------------------"
echo "按 [CTRL+C] 停止此脚本 (但不会停止后台服务)。"

# 等待所有后台进程，以便脚本可以被 Ctrl+C 中断
wait $BFF_PID $DISCOVERY_PID $CELERY_WORKER_PID $EXTRACTOR_PID
