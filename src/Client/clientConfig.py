CLIENT_FOLDER_ADDRESS = "F:/Program/PythonProject/PycharmWorkspace/DFS/files/clientFiles"
CACHE_FOLDER_ADDRESS = "F:/Program/PythonProject/PycharmWorkspace/DFS/files/clientFiles/cacheFolder"
CACHE_TIME = 10
SERVER_ADDRESS = "http://127.0.0.1:5000"  # 如："http://127.0.0.1:5000" 服务器的IP地址加端口
VICE_ADDRESS = "http://127.0.0.1:6000"

CLIENT_FOLDER = CLIENT_FOLDER_ADDRESS + '/CLIENT_'  # 客户端用于下载的文件夹
CACHE_FOLDER = CACHE_FOLDER_ADDRESS + '/CACHE_'  # 客户端用于缓存的文件夹
CACHE_TIMEOUT = CACHE_TIME  # 缓存限制时间（在某分钟内）
local_download_file = {}  # 用于记录下载的本地文件
