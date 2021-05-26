import base64
import os
import pathlib
import sys

import requests
from flask import Flask, request, send_from_directory

from nodeServerConfig import *


def get_node_id():
    """
    函数说明: 获取节点ID
    return: 当前节点的ID
    """
    if len(sys.argv) > 0:
        return int(sys.argv[1])
    return 1


# 配置
nodeID = get_node_id()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisShouldBeSecret'
app.config['UPLOAD_FOLDER'] = NODE_SERVER_UPLOAD_FOLDER_ADDRESS + '/NODE_' + str(nodeID)


#######################
# 本地功能
#######################

def get_address():
    """
    函数说明: 获取节点地址
    return: 当前节点的地址
    """
    node_id = get_node_id()
    port_num = 5000 + node_id  # 设置端口号
    return NODE_SERVER_ADDRESS + str(port_num) + "/"


def get_dict_of_files(node_address):
    """
    函数说明: 获取节点文件字典
    param nodeAddress: 节点地址
    return: 节点上所有文件的字典
    """
    files_on_node = {}
    file_list = os.listdir(app.config['UPLOAD_FOLDER'])
    # 包含这个节点文件夹里面的文件都value上这个节点的地址，以字典的形式返回
    for file_name in file_list:
        files_on_node[file_name] = node_address
    return files_on_node


def check_for_file(filename):
    """
    函数说明: 检查文件是否存在
    param filename:  文件名
    return: 文件是否存在的布尔值
    """
    return os.path.isfile(NODE_SERVER_UPLOAD_FOLDER_ADDRESS + "/NODE_" + str(nodeID) + "/" + filename)


def sent_new_file():
    """
    函数说明: 判断是否是本地文件夹和目录表上的内容，所有目录表上已有的内容不会发送过去
    return: 不在本地文件夹和目录表上的文件字典
    """
    try:
        files = requests.get(SERVER_ADDRESS + "/returnlist")
    except BaseException:
        files = requests.get(VICE_SERVER_ADDRESS + "/returnlist")
    response = files.json()
    local_file_list = os.listdir(NODE_SERVER_UPLOAD_FOLDER_ADDRESS + "/NODE_" + str(nodeID))
    file_server_new = {}
    for file_new in local_file_list:
        if file_new not in response.keys():
            with open(NODE_SERVER_UPLOAD_FOLDER_ADDRESS + "/NODE_" + str(nodeID) + "/" + file_new, 'rb') as f:
                file_byte = base64.b64encode(f.read())
            file_str = file_byte.decode('ascii')
            file_server_new[file_new] = file_str
    return file_server_new


#################
# 端点
#################

@app.route('/servercheck/<filename>', methods=['GET'])
def server_check(filename):  # 提供查询节点服务
    """
    函数说明: 服务器检查文件是否存在
    param filename: 文件名
    return: 文件是否存在的消息
    """
    file_exists = check_for_file(filename)
    # 服务器寻找文件
    print('Checking for file')
    if file_exists:
        return jsonify({'message': 'File on node.'})  # 根据当前节点的文件夹去查找，返回JSON信息
    return jsonify({'message': 'File does not exist.'})


@app.route('/removefile', methods=['POST'])
def remove_file():
    """
    函数说明: 目录服务器使用此端点来告诉节点从文件夹中删除文件
    return: 文件删除消息
    """
    message = request.get_json()  # 收到删除请求
    filename = message['fileToDelete']
    os.remove(app.config['UPLOAD_FOLDER'] + '/' + filename)  # 响应删除文件
    print("<" + filename + "> has been deleted from this node.")
    return jsonify({'message': 'File deleted.'})


@app.route('/<filename>')
def uploaded_file(filename):
    """
    函数说明: 上传文件
    param filename: 文件名
    return: 此端点上的文件
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """
    函数说明: 从客户端接收要上传到此节点的文件，上传后，向服务器发送有关文件已上载的通知
    return: 文件上传消息
    """
    if request.method == 'POST':
        # 检查POST请求是否包含文件部分
        if 'file' not in request.files:
            print('No file part')
            return "No file part"  # redirect(request.url)
        file = request.files['file']  # request是可以识别文件的，直接后面.files就可以选择
        # 如果用户未选择文件
        if file.filename == '':
            print('No selected file')
            return "NO selected file"  # redirect(request.url)
        # 如果文件不为空
        if file:
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # 将该文件上传到本节点的文件夹
            currentFiles[filename] = ""
            data_to_notify = {'nodeAddress': get_address(), 'fileName': {filename: [get_address()]},
                              'fileType': "upload"}  # 只有上传的时候给改版本号
            try:
                notify_server = requests.post(SERVER_ADDRESS + "/newfile", json=data_to_notify)  # 更新目录表
                memo = {'file': file}
                server_backup = requests.post(VICE_SERVER_ADDRESS + "/server_one_backup/" + filename,
                                              files=memo)  # 备份到服务器上
            except:
                notify_server = requests.post(VICE_SERVER_ADDRESS + "/newfile", json=data_to_notify)  # 更新目录表
                memo = {'file': file}
                server_backup = requests.post(VICE_SERVER_ADDRESS + "/server_one_backup/" + filename,
                                              files=memo)  # 备份到服务器上
            print("<" + filename + "> has been uploaded to this node.")
            return filename + " uploaded to node " + str(get_node_id())
    return "upload file"


@app.route('/backup/<filename>', methods=['GET', 'POST'])
def backup(filename):
    """
    函数说明: 备份文件
    param filename: 文件名
    return: 文件备份消息
    """
    client_id = {'clientID': -9999}
    try:
        file_check = requests.get(SERVER_ADDRESS + "/download/" + filename, json=client_id)  # 返回的是一个下载节点的地址，以及URL
        true_server_address = SERVER_ADDRESS
    except BaseException:
        file_check = requests.get(VICE_SERVER_ADDRESS + "/download/" + filename, json=client_id)  # 返回的是一个下载节点的地址，以及URL
        true_server_address = VICE_SERVER_ADDRESS
    if file_check.ok:
        server_json_response = file_check.json()
        print(server_json_response)
        if server_json_response['message'] == "File exists.":
            print("Address to get file from = ", server_json_response['address'])
            file_request = requests.get(server_json_response['address'])  # 向这个提供下载的节点发出get请求，即上面71行的交互，返回这个即将备份的文件内容
            print("Request sent to:", server_json_response['address'])
            with open(NODE_SERVER_UPLOAD_FOLDER_ADDRESS + '/NODE_' + str(nodeID) + "/" + filename, 'wb') as handler:
                handler.write(file_request.content)
            del file_request
            data_to_notify = {'nodeAddress': get_address(), 'fileName': {filename: [get_address()]},
                              'fileType': "backup"}  # 备份的时候不给改版本号
            update_server = requests.post(SERVER_ADDRESS + "/newfile", json=data_to_notify)  # 备份后更新目录表
            update_server = requests.post(VICE_SERVER_ADDRESS + "/newfile", json=data_to_notify)  # 备份后更新目录表
            if update_server.ok:  # 目录服务器那边会返回一些字符串
                print(filename + " backed up on this node.")
                return jsonify({'message': 'nice'})
            else:
                print("Could not get file to backup")
    else:
        print("File backup unsuccessful")
    return jsonify({'message': 'sorry'})


# 启动功能
if __name__ == "__main__":
    from flask import jsonify

    # 第一个节点将在端口5001上运行，并随每个节点递增
    nodeID = get_node_id()
    portNum = 5000 + nodeID
    address = (NODE_SERVER_ADDRESS + str(portNum) + "/")

    # 如果尚未为此节点创建文件夹，则创建该文件夹
    pathlib.Path('F:/Program/PythonProject/DFS/files/nodeFiles/NODE_' + str(nodeID)).mkdir(parents=True,
                                                                                           exist_ok=True)  # 为本节点建立文件夹

    currentFiles = get_dict_of_files(address)  # 都value上节点地址的文件字典
    # mainServerUrl = "http://127.0.0.1:5000/"

    joinJSON = {'message': 'I am a new node.', 'nodeID': nodeID, 'address': address, 'currentFiles': currentFiles}

    # serverbackup = requests.post(SERVER_ADDRESS + "/serverbackup")
    backupJSON = {'filedict': sent_new_file()}
    tmp = requests.post(SERVER_ADDRESS + "/server_all_backup", json=backupJSON)
    sendFlag = requests.post(SERVER_ADDRESS + "/newnode", json=joinJSON)  # 创建新节点时向目录服务器发送信息
    tmp = requests.post(VICE_SERVER_ADDRESS + "/server_all_backup", json=backupJSON)
    sendFlag = requests.post(VICE_SERVER_ADDRESS + "/newnode", json=joinJSON)  # 创建新节点时向目录服务器发送信息
    app.run(debug=True, host="0.0.0.0", port=portNum)  # 也是默认127.0.0.1地址
