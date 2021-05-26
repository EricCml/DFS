import os
import sys

import requests
import pathlib
import time
import base64
from datetime import datetime
from flask import Flask, request, send_from_directory, jsonify
from directoryServerConfig import *


def get_main_port():
    """
    函数说明: 获取命令行传入的端口号参数
    return: 端口号
    """
    if len(sys.argv) > 0:
        port = int(sys.argv[1][1:])
        return port
    return 5000


# 配置
app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisShouldBeSecret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
MAIN_SERVER_PORT = get_main_port()
SERVER_FOLDER = SERVER_FOLDER_ADDRESS + '/SERVER_' + str(MAIN_SERVER_PORT - 5000)


#######################
# 本地功能
#######################


def parse_node_id(address):
    """
    函数说明: 传递一个地址，它将返回节点ID作为一个整数
    param address: 地址
    return: 节点ID
    """
    split = address.split(':')
    port = int(split[2][:4])  # 端口号
    return port - 5000


def delete_from_dict(filename, dict_to_delete_from):
    """
    函数说明: 从字典中删除文件
    param filename: 文件名
    param dict_to_delete_from: 字典
    """
    del dict_to_delete_from[filename]


# 传递文件命令 {"index.jpeg": [address1, address2]}
# 目录服务器就只有一些表的信息，每个节点的文件可能会变化，然后就将这些变化记录回目录服务器上
def add_files_from_node(dict_of_files, node_address, upload_type):
    """
    函数说明: 从节点处添加文件
    param dict_of_files: 请求节点的文件字典
    param node_address: 请求节点的地址（包括端口号）
    param upload_type: 处理的类型
    """
    # 对于传入字典中的每个文件
    for fileName in dict_of_files:
        # 检查服务器上是否已存在具有该名称的文件
        if fileName in listOfFiles['nodeAddresses'].keys():
            if upload_type == "upload":  # 这个是用来控制版本是否需要更改，只有上传的时候才会改版本号，创建节点同步文件的时候不会更新版本
                listOfFiles['fileVersion'][fileName] += 1
            # 如果当前节点的地址尚未存储，则将其添加到与此文件关联的地址列表中
            if node_address not in listOfFiles['nodeAddresses'][fileName]:
                listOfFiles['nodeAddresses'][fileName].append(node_address)
                # 添加到具有该文件的节点总数
                listOfFiles['fileAccessCount'][fileName][1] += 1
        # 如果文件不在全局文件列表中，请使用文件名创建一个新键值对
        else:
            listOfFiles['nodeAddresses'][fileName] = [node_address]  # 增加这个文件的字典，并且存在的节点地址这有这个地址
            listOfFiles['fileAccessCount'][fileName] = [0, 1]  # 下载次数为0次，存在于总节点数为1个
            listOfFiles['fileVersion'][fileName] = 1  # 因为是新文件所以是第一个版本
            time.sleep(5)


def round_robin(filename):
    """
    函数说明: 确定文件的最新下载位置，并执行循环轮询以确保公平地从节点下载文件
    param filename: 文件名
    return: 即将从哪个节点下载的数
    """
    my_list = listOfFiles['fileAccessCount'][filename]
    index_of_node_to_use = my_list[0] % my_list[1]  # 总下载数对总结点数取余即可保证在这些节点循环
    listOfFiles['fileAccessCount'][filename][0] += 1  # 总下载数加一
    return index_of_node_to_use  # 返回即将从哪个节点下载的数


# Nginx加权轮询算法
# nodeWeights = {"http://127.0.0.1:5001/", [weight, effectiveWeight( = weight), currentWeight( = 0)]}
def nginx_robin(filename):
    """
    函数说明: 确定文件的最新下载位置，并执行加权轮询以确保公平地从节点下载文件
    param filename: 文件名
    return: 目标节点
    """
    file_nodes_list = listOfFiles['nodeAddresses'][filename]
    total_weight = 0
    target_node = "http://127.0.0.1:5000/"
    max_cur_weight = -999
    for nodeAddress in file_nodes_list:
        # print(nodeAddress)
        nodeWeights[nodeAddress][2] = nodeWeights[nodeAddress][2] + nodeWeights[nodeAddress][1]
        total_weight = total_weight + nodeWeights[nodeAddress][2]
        if nodeWeights[nodeAddress][2] > max_cur_weight:
            target_node = nodeAddress
            max_cur_weight = nodeWeights[nodeAddress][2]
    nodeWeights[target_node][2] = nodeWeights[target_node][2] - total_weight
    # print("targetNode:" + targetNode)
    # print(nodeWeights)
    return target_node


def node_to_upload_to():
    """
    函数说明: 选一个小于设定文件数的节点进行上传，相当于一直选最后一个节点直到文件数满了才换
    return: 要上传的节点地址
    """
    # 创建节点时，第一个创建的节点ID必须为1，它以后的文件数将做为参考，如果其他节点的文件数小于这个节点ID为1的文件数时，会优先在其他节点上传，直到当所有其他节点的文件数都等于这个ID为1的文件数时，才在这个ID为1的节点进行上传文件，如此循环
    min_index = 1
    min_value = connectedNodes[1][1]  # 这是之前设定的每个节点存的文件数
    for node in connectedNodes.keys():
        if connectedNodes[node][1] < min_value:
            min_index = node
            min_value = (connectedNodes[node])[1]
    # 返回要上传的节点地址
    return connectedNodes[min_index][0]


# 提供查询节点服务
@app.route('/uploadnodestate/<address>/<state>', methods=['GET'])
def server_check(address, state):
    """
    函数说明: 服务器检查文件是否存在
    param address: 节点地址
    param state: 节点状态
    """
    if state == 0:
        nodeWeights[address][1] = nodeWeights[address][1] - 1
    elif state == 1:
        if nodeWeights[address][1] < nodeWeights[address][0]:
            nodeWeights[address][1] = nodeWeights[address][1] + 1
    return "server check"


@app.route('/serverbackup', methods=['POST'])
def server_backup():
    """
    函数说明: 从目录服务器中的nodeAddresses表中逐个下载文件
    """
    for file_backup in listOfFiles['nodeAddresses'].keys():
        file_list = os.listdir(SERVER_FOLDER_ADDRESS + '/SERVER_' + str(MAIN_SERVER_PORT - 5000))
        # fileList = sorted(fileList)
        if file_backup not in file_list:
            # address = listOfFiles['nodeAddresses'][file_backup][round_robin(file_backup)]
            address = nginx_robin(file_backup)
            file_new = requests.get(address + file_backup)
            with open(SERVER_FOLDER_ADDRESS + '/SERVER_' + str(MAIN_SERVER_PORT - 5000) + "/" + file_backup,
                      'wb') as handler:
                handler.write(file_new.content)
            del file_new
    return "server backup"


@app.route('/server_one_backup/<filename>', methods=['POST'])
def server_one_backup(filename):
    """
    函数说明: 从目录服务器中的nodeAddresses表中下载指定文件
    param filename: 文件名
    """
    file_new = request.files['file']
    try:
        # address = listOfFiles['nodeAddresses'][filename][round_robin(filename)]
        address = nginx_robin(filename)
        file_new = requests.get(address + filename)
        with open(SERVER_FOLDER_ADDRESS + '/SERVER_' + str(MAIN_SERVER_PORT - 5000) + "/" + filename, 'wb') as handler:
            handler.write(file_new.content)
        del file_new
        return None
    except BaseException:
        print('该文件目前没有节点可用，将直接存到目录服务器缓存文件夹中。')
        file_new.save(os.path.join(SERVER_FOLDER, filename))
    return "server one backup"


@app.route('/server_all_backup', methods=['POST'])
def server_all_backup():
    """
    函数说明: 备份所有文件
    """
    res = request.get_json()
    new_dict = res['filedict']
    # file_list = os.listdir(SERVER_FOLDER_ADDRESS + '/SERVER_' + str(MAIN_SERVER_PORT-5000))
    for files in new_dict.keys():
        file_str = new_dict[files].encode('ascii')
        file_byte = base64.b64decode(file_str)
        with open(SERVER_FOLDER_ADDRESS + '/SERVER_' + str(MAIN_SERVER_PORT - 5000) + "/" + files, 'wb') as handler:
            handler.write(file_byte)
        # new_dict[files].save(os.path.join(SERVER_FOLDER_ADDRESS + '/SERVER_0',files))
    return "server all backup"  # 一定要返回的


@app.route('/getserver_backupfile', methods=['GET'])
def getserver_backupfile():
    """
    函数说明: 获取文件备份
    return: 文件备份表
    """
    all_file_list = os.listdir(SERVER_FOLDER_ADDRESS + '/SERVER_' + str(MAIN_SERVER_PORT - 5000))
    all_file = {}
    for filename in all_file_list:
        all_file[filename] = MAIN_SERVER_IP + str(MAIN_SERVER_PORT)
    return jsonify(all_file)


@app.route('/<filename>')
def backupserver_file(filename):
    """
    函数说明: 上传文件进行备份
    param filename: 文件名
    """
    return send_from_directory(SERVER_FOLDER, filename)


@app.route('/judge_write/<filename>', methods=['POST'])
def judge_write(filename):
    """
    函数说明: 读写锁判断
    param filename: 文件名
    return: 判断消息
    """
    if filename in listOfFiles['lockedFiles'].keys():
        for i in listOfFiles['lockedFiles'][filename].keys():
            if list(listOfFiles['lockedFiles'][filename][i])[0] == 'r':
                return jsonify({'message': '0'})
        return jsonify({'message': '1'})
    else:
        return jsonify({'message': '2'})


#######################
# 端点功能
#######################

# 创建新节点后，它将向该端点发送POST请求
# 该请求将包含一个json文件，其中包含节点的所有详细信息和文件
@app.route('/newnode', methods=['POST'])
def new_node():
    """
    函数说明: 增加一个新节点时，这个节点需自带一个ID，地址，以及它自己的文件夹，这时目录服务器会收录新节点自带的文件夹里面的文件信息
    return: 新建节点的消息
    """
    response = request.get_json()
    if response:
        new_node_id = response['nodeID']  # 请求节点的ID号，如10
        new_node_addr = response['address']  # 这是请求节点的地址以及端口号
        dict_of_files = response['currentFiles']  # 这是包含请求节点上的文件夹中文件的字典
        add_files_from_node(dict_of_files, new_node_addr, "no_upload")  # 更新目录表，新节点加进来时不给改版本号
        print("File Versions: ", listOfFiles['fileVersion'])
        # 节点文件数表也要更新，目前还没有看到对初始第一个key为1的设置
        connectedNodes[new_node_id] = [new_node_addr, len(dict_of_files)]
        # nodeWeights["http://127.0.0.1:5001/"] = [weight, effectiveWeight = weight, currentWeight = 0]
        nodeWeights[new_node_addr] = [new_node_id, new_node_id, 0]
        return jsonify({'message': 'Node successfuly set up.'})  # 返回给节点信息
    else:
        return jsonify({'message': 'Node could not be set up.'})


@app.route('/newfile', methods=['POST'])
def new_file():
    """
    函数说明: 节点在获取新文件时将访问此端点，它更新文件列表
    return: 操作消息
    """
    data = request.get_json()
    node_address = data['nodeAddress']
    dict_of_file = data['fileName']
    upload_type = data['fileType']
    # 节点得到新文件后，通过post的方式更新目录表
    add_files_from_node(dict_of_file, node_address, upload_type)
    connectedNodes[parse_node_id(node_address)][1] += 1  # 节点文件数表也要更新
    print("File Versions: ", listOfFiles['fileVersion'])
    return "File added to global list"


@app.route('/returnlist', methods=['GET'])  # 响应get请求，返回文件目录表
def return_files():
    """
    函数说明: 该端点返回存储在服务器上的所有文件的字典
    return:  返回存储在服务器上的所有文件的字典
    """
    return jsonify(listOfFiles['nodeAddresses'])


@app.route('/remove/<filename>', methods=['POST'])  # 收到POST的删除文件请求时
def remove_file(filename):
    """
    函数说明: 当收到POST的删除文件请求时，删除文件
    param filename: 要删除的文件名
    return: 文件删除操作消息
    """
    if filename in listOfFiles['nodeAddresses']:  # 判断文件是否在目录表
        i = 0
        for node in listOfFiles['nodeAddresses'][filename]:  # 遍历拥有这个文件的所有节点地址
            # 逐个询问拥有这个文件的节点是否删除此文件
            response = requests.post(
                node + "removefile", json={'fileToDelete': filename})
            if response.ok:  # 当成功收到来自节点的反馈时,这ok是什么意思？
                i = i + 1
                if i == len(listOfFiles['nodeAddresses'][filename]):
                    # 下面不应该是只删除此节点的地址吗，怎么一次性把所有的节点地址都删除了？
                    if response.json()['message'] == 'File deleted.':
                        # 有问题，这里直接得到一个节点回馈就删了全部，还跳出了
                        del listOfFiles['nodeAddresses'][filename]
                        # 相当于其他拥有这个文件的节点还没有删除这个文件
                        del listOfFiles['fileVersion'][filename]
                        del listOfFiles['fileAccessCount'][filename]
                        print(filename + " deleted from server")
                        if os.path.exists(
                                SERVER_FOLDER_ADDRESS + '/SERVER_' + str(MAIN_SERVER_PORT - 5000) + '/' + filename):
                            os.remove(SERVER_FOLDER_ADDRESS + '/SERVER_' +
                                      str(MAIN_SERVER_PORT - 5000) + '/' + filename)
                        return "File deleted"
    return "remove file"


@app.route('/uploadcheck/<filename>', methods=['GET'])
def upload_file_check(filename):  # 上传文件检查   没有对目录表进行操作，只是反馈信息而已
    """
    函数说明: 当收到GET请求时，进行上传文件检查，没有对目录表进行操作，只是反馈信息
    param filename: 要上传的文件名
    return: 存储在服务器上的所有文件的字典
    """
    client_id = request.get_json()
    print(listOfFiles['lockedFiles'])
    if filename in listOfFiles['nodeAddresses']:  # 检查上传的文件是否已经在目录表上
        if filename not in listOfFiles['lockedFiles'].keys():  # 且这个文件不在锁列表中，
            # 返回上传的文件名字已经存在了，此时还返回即将上传的节点ID
            return jsonify(
                {'message': 'File already exists.', 'nodeAddresses': ((listOfFiles['nodeAddresses'])[filename]),
                 "addressToUploadTo": node_to_upload_to()})
        elif filename in listOfFiles['lockedFiles'].keys():
            if list(listOfFiles['lockedFiles'][filename][client_id])[0] == 'w':
                return jsonify(
                    {'message': 'File already exists.', 'nodeAddresses': ((listOfFiles['nodeAddresses'])[filename]),
                     "addressToUploadTo": node_to_upload_to()})
            elif list(listOfFiles['lockedFiles'][filename][client_id])[0] == 'r':
                print('你之前选择了读这个文件，就不能上传哦！')  # -999的含义
                return jsonify({'message': 'File locked', 'lockedBy': -999,
                                'nodeAddresses': ((listOfFiles['nodeAddresses'])[filename]),
                                "addressToUploadTo": node_to_upload_to()})
    return jsonify({'message': 'File does not exist.', "addressToUploadTo": node_to_upload_to()})


@app.route("/removelock/<filename>")
def remove_def(filename):
    """
    函数说明: 对文件进行解锁操作
    param filename: 文件名
    return: 文件解锁操作消息
    """
    client_id = request.get_json()
    if filename in listOfFiles['lockedFiles'].keys():
        if client_id in listOfFiles['lockedFiles'][filename].keys():
            delete_from_dict(client_id, listOfFiles['lockedFiles'][filename])
            print("Removed lock on ")
            if len(listOfFiles['lockedFiles'][filename]) == 0:
                delete_from_dict(filename, listOfFiles['lockedFiles'])
            return jsonify({'message': 'success'})
        else:
            # print('文件上锁了，但是你没有对它上过锁，不能由你解锁')
            return jsonify({'message': 'error1'})
    else:
        # print('你输入的名字有误或没有锁')
        return jsonify({'message': 'error2'})


@app.route('/backupcheck/<filename>', methods=['GET'])
def backup_file_check(filename):
    """
    函数说明: 当收到GET请求时，进行备份文件检查
    param filename: 要手动备份的文件名
    return: 操作消息
    """
    print("\n", listOfFiles['nodeAddresses'], "\n")
    if filename in listOfFiles['nodeAddresses'].keys():  # 想要备份的文件是否在目录表中
        for address in connectedNodes.values():  # 遍历所有节点的地址和文件数目
            list_of_addresses = listOfFiles['nodeAddresses'][filename]  # 想要备份的文件所在的所有节点地址
            print("Current Address: ", address)
            if address[0] in list_of_addresses:  # 每次遍历的节点的地址是否在，已有备份文件的节点地址中
                print("File stored on:", address[0])
            else:
                print("File not stored on", address)
                # 如果找到没有备份文件的节点地址，就直接将这个节点地址返回，先找到就先返回，直接跳出这个函数
                return jsonify({'message': 'File already exists.', "addressToUploadTo": address})
    # 如果这个备份的文件没有在目录表中，就不返回节点地址，相当于就不给你备份了，因为本来就没有这个文件何谈备份，应该就是上传的功能了
    return jsonify({'message': 'File does not exist.'})


@app.route('/version/<filename>', methods=['GET'])
def get_version(filename):
    """
    函数说明: 获取文件版本号
    param filename: 文件名
    return: 收到查询文件版本的请求，返回文件的版本号
    """
    return jsonify({'fileVersion': listOfFiles['fileVersion'][filename]})


@app.route('/download/<filename>')
def download_file(filename):
    """
    函数说明: 如果客户端要获取文件，它将向该URL发送获取请求，服务器检查其文件列表，并返回下一步应访问的节点的地址
    param filename: 文件名
    return: 下一步应访问的节点的地址
    """
    client_dict = request.get_json()  # 接受下载的请求信息，其实每次请求都会附带一个JSON文件
    client_id = client_dict['clientID']
    if client_id == -9999:  # 用于备份，不需要上锁
        if filename in listOfFiles['nodeAddresses'].keys():  # 查看要下载的文件是否在目录表中
            # 给出一个拥有这个文件的节点地址，且这个节点地址是根据负载均衡函数决定后给出的
            # node_address = listOfFiles['nodeAddresses'][filename][round_robin(filename)]
            node_address = nginx_robin(filename)
            return jsonify(
                {'message': 'File exists.', 'address': (node_address + filename),
                 'nodeID': parse_node_id(node_address)})
    else:
        kk = client_dict['input']
        if filename in listOfFiles['nodeAddresses'].keys():  # 查看要下载的文件是否在目录表中
            # 给出一个拥有这个文件的节点地址，且这个节点地址是根据负载均衡函数决定后给出的
            # node_address = listOfFiles['nodeAddresses'][filename][round_robin(filename)]
            node_address = nginx_robin(filename)
            gg = 0
            if kk == 'r':
                if filename not in listOfFiles['lockedFiles'].keys():
                    current_time = str(datetime.now()).split()
                    temp = {client_id: [kk, current_time]}
                    listOfFiles['lockedFiles'][filename] = temp
                    # listOfFiles['lockedFiles'][filename][clientID] = [kk, currentTime]
                    return jsonify({'message': 'File exists.', 'address': (node_address + filename),
                                    'nodeID': parse_node_id(node_address)})
                else:
                    for i in listOfFiles['lockedFiles'][filename].keys():
                        if list(listOfFiles['lockedFiles'][filename][i])[0] == 'w':
                            gg = 1
                            print('有人下载了！')
                            return jsonify(
                                {'message': 'File locked.', 'lockedBy': i, 'address': (node_address + filename),
                                 'nodeID': parse_node_id(node_address)})
                    if gg == 0:
                        current_time = str(datetime.now()).split()
                        listOfFiles['lockedFiles'][filename][client_id] = [kk, current_time]
                        return jsonify({'message': 'File exists.', 'address': (node_address + filename),
                                        'nodeID': parse_node_id(node_address)})
            if kk == 'w':
                if filename not in listOfFiles['lockedFiles'].keys():
                    current_time = str(datetime.now()).split()
                    temp = {client_id: [kk, current_time]}
                    listOfFiles['lockedFiles'][filename] = temp
                    # list(((listOfFiles['lockedFiles'])[filename])[clientID]) = [kk,currentTime]
                    # 给你下载
                    return jsonify({'message': 'File exists.', 'address': (node_address + filename),
                                    'nodeID': parse_node_id(node_address)})
                else:
                    for i in listOfFiles['lockedFiles'][filename].keys():
                        if list(listOfFiles['lockedFiles'][filename][i])[0] == 'w':
                            gg = 1
                            print('有人下载了！')
                            return jsonify(
                                {'message': 'File locked.', 'lockedBy': i, 'address': (node_address + filename),
                                 'nodeID': parse_node_id(node_address)})
                    if gg == 0:
                        current_time = str(datetime.now()).split()
                        listOfFiles['lockedFiles'][filename][client_id] = [kk, current_time]
                        return jsonify({'message': 'File exists.', 'address': (node_address + filename),
                                        'nodeID': parse_node_id(node_address)})
                        # pass    #给你下载
        else:
            # 如果文件不存在就返回不存在
            return jsonify({'message': 'File does not exist.'})
    return "download file"


# 启动功能
if __name__ == "__main__":
    pathlib.Path(SERVER_FOLDER_ADDRESS + './SERVER_' +
                 str(MAIN_SERVER_PORT - 5000)).mkdir(parents=True, exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=MAIN_SERVER_PORT)  # 开启这个交互的框架
