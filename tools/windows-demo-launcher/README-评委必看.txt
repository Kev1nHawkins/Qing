岭潮共创 Windows 一键演示包

【运行要求】
Windows 10/11
Docker Desktop 已安装

【启动】
1. 解压整个文件夹（不要只打开压缩包内的 EXE）
2. 启动 Docker Desktop
3. 双击“岭潮共创-启动.exe”
4. 首次启动等待镜像导入，服务就绪后浏览器会自动打开

【停止】
双击“岭潮共创-停止.exe”。停止操作会保留数据库、上传文件和镜像，第二次启动更快。

【访问】
用户端：http://127.0.0.1:5173
管理端：http://127.0.0.1:5174

【提示】
首次启动需要导入本地 Docker 镜像，可能需要数分钟，不需要访问 Docker Hub。
如启动失败，请将“%LOCALAPPDATA%\LingchaoCoCreateDemo\launcher-logs”文件夹中的日志交给项目组。
