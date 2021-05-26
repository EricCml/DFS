MAIN_SERVER_IP = "http://127.0.0.1:"
# MAIN_SERVER_PORT = 5000
SERVER_FOLDER_ADDRESS = 'F:/Program/PythonProject/PycharmWorkspace/DFS/files/serverFiles'
VICE_SERVER_ADDRESS = "http://127.0.0.1:5000"

# 文件的上传位置，以及允许的格式
UPLOAD_FOLDER = 'F:/Program/PythonProject/PycharmWorkspace/DFS/files/serverFiles/upload'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# 服务器本地数据库 = 具有3个嵌套字典的字典
# dict - key = nodeAddress, 包含具有该文件的所有节点地址的列表
# nodeAddresses['index.jpeg'] = ["http://127.0.0.1:5002/", "http://127.0.0.1:5002/"]

# dict - key = fileVersion, 包含所有文件及其当前版本的列表
# fileVersion['index.jpeg'] = 1

# dict - key = fileAccessCount, 用于在节点之间划分工作
# fileAccessCount['index.jpeg'] = [10, 3]
# 第一个索引是它被访问的次数，第二个索引是拥有它的节点数

listOfFiles = {'nodeAddresses': {},
               'fileAccessCount': {},
               'fileVersion': {},
               'lockedFiles': {}
               }

# dict - key = nodeID, 包含所有节点地址的列表
# connectedNodes[1] = ["http://127.0.0.1:5001/", 2]
# 第一个索引是节点地址，第二个索引是节点拥有的文件数
connectedNodes = {}

# nodeWeights["http://127.0.0.1:5001/"] = [weight, effectiveWeight=weight,currentWeight=0]
nodeWeights = {}
