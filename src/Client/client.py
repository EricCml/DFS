import requests
import os
import sys
import pathlib
import PySimpleGUI as sg
from shutil import copyfile
from datetime import datetime
from clientConfig import *


def print_list_of_files(client_id):  # 打印出客户端的文件夹中的文件
    """
    函数说明: 打印出客户端的文件夹中的文件
    param client_id: 客户端ID
    """
    file_list = os.listdir(CLIENT_FOLDER + str(client_id))
    file_list = sorted(file_list)  # 对文件夹中的文件进行分开，返回一个list
    print("Files stored in client folder.")
    print("--------------------------------")
    for fileName in file_list:
        print(fileName)
    print("\n")


def update_cache_list(client_id, cachedFilesList):
    """
    函数说明: 节点启动时，假定所有现有文件都已过期
    param client_id: 客户端ID
    param cachedFilesList: cachedFilesList是字典的形式 ，前三个为时间，后面一个为版本号
    """
    file_list = os.listdir(CLIENT_FOLDER + str(client_id))
    # fileList = sorted(fileList)
    for fileName in file_list:
        if fileName not in cachedFilesList.keys():  # 如果客户端的文件夹中的文件不在缓存文件夹上，
            cachedFilesList[fileName] = ["0", "0", "0", 0]  # 则将这些文件添加到缓存文件表找那个，并初始化，前三个为时间，后面一个为版本号


def print_server_all_backup_file():
    """
    函数说明: 获取服务器上的所有备份文件
    """
    try:
        files = requests.get(SERVER_ADDRESS + "/getserver_backupfile")
    except BaseException:
        print("主目录服务器崩溃，切换到备用服务器...")
        files = requests.get(VICE_ADDRESS + "/getserver_backupfile")
    get_files = files.json()
    print("Files all backup on the server")
    print("--------------------------------")
    for file_name in get_files.keys():
        print(file_name + ",    所在的服务器：" + get_files[file_name])
    print("\n")


def get_server_dict():
    """
    函数说明: 获取服务器文件的字典
    return: 目录服务器中的文件目录表nodeAddresses
    """
    try:
        files = requests.get(SERVER_ADDRESS + "/returnlist")
    except BaseException:
        print("主目录服务器崩溃，切换到备用服务器...")
        files = requests.get(VICE_ADDRESS + "/returnlist")
    return files.json()


def print_server_files():
    """
    函数说明: 打印存储在服务器上的所有文件
    return:  打印目录服务器中的文件目录表nodeAddresses
    """
    file_list = get_server_dict()
    print("Files stored on the server")
    print("--------------------------------")
    for file_name in file_list.keys():
        print(file_name + ",    所在的节点：" + str(file_list[file_name]) + ",     节点总数：" + str(len(file_list[file_name])))
    print("\n")


def does_cache_exists(file_name, client_id):
    """
    函数说明: 判断文件是否存在客户端的缓存文件夹中
    param file_name: 函数名
    param client_id: 客户端ID
    return: True or False
    """
    if file_name in os.listdir(CACHE_FOLDER + str(client_id)):
        return True
    return False


def does_file_exists(file_name, client_id):
    """
    函数说明: 判断文件是否在客户端的文件夹中
    param file_name: 文件名
    param client_id: 客户端ID
    return: True or False
    """
    if file_name in os.listdir(CLIENT_FOLDER + str(client_id)):
        return True
    return False


def print_download_file():
    print('\n温馨提示：此处只能解读锁，若要解写锁请执行上传文件的操作：')
    print('下面是你之前下载过的文件，且尚未解锁：')
    print("------------------------------------------")
    for file_down in local_download_file.keys():
        print(file_down + '    ,' + local_download_file[file_down])


def delete_download_lock(file_name):
    if file_name in local_download_file.keys():
        del local_download_file[file_name]
    else:
        print('你输入的文件名有误..')


def get_file_version(file_name):
    """
    函数说明: 查询文件在目录服务器上的版本号
    param file_name: 文件名
    return: 返回查询文件在目录服务器上的版本号
    """
    try:
        response = requests.get(SERVER_ADDRESS + '/version/' + file_name)
    except:
        print("主目录服务器崩溃，切换到备用服务器...")
        response = requests.get(VICE_ADDRESS + '/version/' + file_name)
    server_json_response = response.json()
    return server_json_response['fileVersion']


def create_folders(client_id):
    """
    函数说明: 创建或登录新客户端时，为其创建对应的文件夹以及缓存文件夹
    param client_id: 客户端ID
    """
    pathlib.Path(CACHE_FOLDER + str(client_id)).mkdir(parents=True, exist_ok=True)
    pathlib.Path(CLIENT_FOLDER + str(client_id)).mkdir(parents=True, exist_ok=True)
    print("Client & cache folders created.")


def get_file_from_cache(file_name, client_id):
    """
    函数说明: 从客户端的缓存文件夹中读取文件，以字典的形式返回文件
    param file_name: 文件名
    param client_id: 客户端ID
    """
    if does_cache_exists(file_name, client_id):
        files = {'file': open(CACHE_FOLDER + str(client_id) + '/' + file_name, 'rb')}  # 以二进制的方式读取
        return files
    return "File doesn't exist"


def get_file(file_name, client_id):
    """
    函数说明: 从客户端的文件夹中读取文件，以字典的形式返回文件
    param file_name: 文件名
    param client_id: 客户端ID
    """
    if does_file_exists(file_name, client_id):
        files = {'file': open(CLIENT_FOLDER + str(client_id) + '/' + file_name, 'rb')}
        return files
    return "File doesn't exist"


def parse_current_time():
    """
    函数说明: 解析当下的时间
    return: 返回日期、小时、分钟
    """
    current_time = str(datetime.now()).split()
    date = current_time[0]
    time = current_time[1].split('.')[0]
    time = time.split(":")
    hours = time[0]
    minutes = time[1]
    return date, hours, minutes


def get_cache_age(cacheTime):
    """
    函数说明: 以分钟为单位返回缓存的存在时间
    param cacheTime:  缓存时间信息
    return: 对应的文件缓存了多久
    """
    curr_date, curr_hours, curr_minutes = parse_current_time()
    curr_total_minutes = int(curr_hours) * 60 + int(curr_minutes)  # 当天当前时间的总分钟数
    cache_total_minutes = int(cacheTime[1]) * 60 + int(cacheTime[2])  # 对应的缓存文件的当天的总分钟数
    return curr_total_minutes - cache_total_minutes  # 两者相减即为对应的缓存文件的缓存时间分钟数


def create_new_file_name(file_name):
    """
    函数说明: 对文件创建一个新的名字，在原有的基础上加（1），对于一直创建则（1）（1）（1）这样加
    param file_name: 原本文件名
    return: 新建的文件名
    """
    split_name = file_name.split('.')
    return split_name[0] + '(1).' + split_name[1]


def check_if_cache_okay(file_name, cachedFilesList):
    """
    函数说明: 检查缓存是否从这一天开始，然后检查时间是否是十分钟
    param file_name: 文件名
    param cachedFilesList: 文件缓存列表
    return: True or False
    """
    if file_name in cachedFilesList.keys():
        # 看缓存表中的文件版本和服务器对应的版本是否一致
        if get_file_version(file_name) == cachedFilesList[file_name][3]:
            date, hours, minutes = parse_current_time()
            if cachedFilesList[file_name][0] == date:  # 看是否是今天的
                age = get_cache_age(cachedFilesList[file_name])  # 得到对应文件在缓存文件夹的缓存时间
                if age < CACHE_TIMEOUT:  # 如果小于设定的缓存时间，就返回TRUE
                    return True
        print("Cached file version is not up to date. Fetching updated version.")  # 即服务器上对应的文件有新版本了
    return False


def download_file(file_name, client_id, cachedFilesList):
    """
    函数说明: 下载完后，如果在10分钟以内我还想再下载一次，那么将会直接从缓存中复制
    param file_name: 要下载的文件名
    param client_id: 客户端ID
    param cachedFilesList: 缓存列表
    """
    # 如果缓存文件没超过设定的缓存时间
    if check_if_cache_okay(file_name, cachedFilesList):
        cached_file = get_file_from_cache(file_name, client_id)  # 没有被用到，直接被具体地址代替了
        # 复制客户端缓存文件中对应的文件到客户端文件夹中，check_if_cache_okay这个函数也包含了检查时间和版本的功能
        print("你下载的文件在缓存中已存在（但缓存版本不一定最新），你是否从取缓存的版本：（y/n）", end=' ')
        event, value = window.read()
        if event == '确认':
            judge = value['-input_text-'].replace("\n", "")
            print(judge)
            if judge == 'y':
                copyfile(CACHE_FOLDER + str(client_id) + "/" + file_name,
                         CLIENT_FOLDER + str(client_id) + "/" + file_name)
                prompt()
                print("downloaded from Cached file: Date:" + cachedFilesList[file_name][0] + " Time: " +
                      cachedFilesList[file_name][1] + ":" + cachedFilesList[file_name][2])
                return None

    print('你是要读文件还是写文件? (r/w):', end=' ')
    event, value = window.read()
    if event == '确认':
        kk = value['-input_text-'].replace("\n", "")
        print(kk)
    client_dict = {'clientID': client_id, 'input': kk}

    try:
        # 返回内容包含可提供下载的节点地址和端口和文件名
        file_check = requests.get(SERVER_ADDRESS + "/download/" + file_name, json=client_dict)
        true_address = SERVER_ADDRESS
    except BaseException:
        # 返回内容包含可提供下载的节点地址和端口和文件名
        print("主目录服务器崩溃，切换到备用服务器...")
        file_check = requests.get(VICE_ADDRESS + "/download/" + file_name, json=client_dict)
        true_address = VICE_ADDRESS
    if file_check.ok:
        server_json_response = file_check.json()  # 这个即为返回的json消息，服务器那边返回的是jsonify信息，这边要转换着json信息
        if server_json_response['message'] == "File locked.":
            if server_json_response['lockedBy'] == client_id:  # 如果文件已经锁了且是自己锁的，也就是之前下载过这个文件
                print("You have locked this file.")
                print("Would you like to download the server version anyway? (y/n):", end=' ')
                event, value = window.read()
                if event == '确认':
                    choice = value['-input_text-'].replace("\n", "")
                    print(choice)
                    if choice == 'y':  # 之前下载过，可能下载的文件丢了，还想下载一次，但这时下载的节点地址大概率是已经变了
                        server_json_response['message'] = "File exists."
                    elif choice == 'n':
                        print("Cancelling download.")
                        return None
            else:
                print(file_name, " is locked by client ", server_json_response['lockedBy'], ".")  # 被其他客户端锁了就下载不了咯
                return None
        if server_json_response['message'] == "File exists.":
            try:
                file_request = requests.get(server_json_response['address'])  # 得到这个文件,'address'是包括节点地址端口和文件名
            except BaseException:
                print('下载的文件的源节点可能出现故障，将到目录服务器中下载:\n')
                file_request = requests.get(true_address + '/' + file_name)
            finally:
                pass
            with open(CLIENT_FOLDER + str(client_id) + "/" + file_name, 'wb') as handler:
                handler.write(file_request.content)  # 把内容写入自己的客户端文件夹中
            with open(CACHE_FOLDER + str(client_id) + "/" + file_name, 'wb') as handler:
                handler.write(file_request.content)  # 把内容写入自己的客户端缓存文件夹中
            del file_request
            date, hours, minutes = parse_current_time()
            cachedFilesList[file_name] = [date, hours, minutes, get_file_version(file_name)]  # 马上记录好这个缓存文件的时间和版本信息
            local_download_file[file_name] = kk
            prompt()
            print(file_name, "has been downloaded and added to the cache.")
            print('\n文件已经下载了，请记得解锁哦！\n')
        else:
            print(file_name, "does not exist on server.")
    else:
        print("Request failed.")
    return None


def upload_file(file_name, client_ID, fileVersion, cachedFilesList):
    # 判断上传的文件是否在客户端的文件夹当中，如果不在则不能上传
    if not does_file_exists(file_name, client_ID):
        print(file_name + " doesn't exist in the client folder.")
        return
    overwrite_flag = False  # 用于控制死循环
    try:
        file_check = requests.get(SERVER_ADDRESS + "/uploadcheck/" + file_name, json=client_ID)  # 向目录服务器发送上传检查请求
        true_address = SERVER_ADDRESS
    except BaseException:
        print("主目录服务器崩溃，切换到备用服务器...")
        file_check = requests.get(VICE_ADDRESS + "/uploadcheck/" + file_name, json=client_ID)  # 向目录服务器发送上传检查请求
        true_address = VICE_ADDRESS
    if file_check.ok:  # 判断之前是不是你写的，如果是你写的，你就有资格去上传
        server_json_response = file_check.json()
        if server_json_response['message'] == 'File locked':
            print("File is locked")
            if server_json_response['lockedBy'] == client_ID:  # 如果是要上传的文件存在于目录服务器中，但被锁了，但是是自己锁的
                server_json_response['message'] = 'File already exists.'  # 这时允许继续上传，相当于就是更新版本了
            else:
                print("This file is locked by client", server_json_response['lockedBy'])  # 如果不是自己锁的，那就不能上传了，等着解锁后再上传吧
                return fileVersion  # 返回缓存文件的版本号？
        if server_json_response['message'] == 'File already exists.':
            server_version = get_file_version(file_name)  # 文件在目录服务器上的版本

            while not overwrite_flag:
                judge1 = requests.post(true_address + '/judge_write/' + file_name)
                judge = judge1.json()
                if judge['message'] == "1":  # 判断能不能写，前面是否读的人都解锁了
                    print("File with that name already exists on server.")
                    print("Would you like to overwrite it? (y/n):", end=' ')
                    event, value = window.read()
                    if event == '确认':
                        choice = value['-input_text-'].replace("\n", "")
                        print(choice)
                        if choice == 'y':  # 如果文件已存在，你还想覆盖，还要判断你的版本和服务器上的版本谁更新
                            files = get_file(file_name, client_ID)
                            file_version_dict = {'fileVersion': fileVersion}
                            if server_version > fileVersion:
                                print(
                                    "This file is outdated. Please download the new version from the server.\nServer "
                                    "version: " + str(
                                        server_version) + "\nYour version: " + str(fileVersion))
                                return fileVersion
                            print("Uploading to: ", server_json_response['nodeAddresses'])
                            list_of_nodes = server_json_response['nodeAddresses']  # 对目录服务器上所有拥有这个文件的节点地址
                            j = 0

                            for nodeAddress in list_of_nodes:  # 目的是将原本所有拥有这个文件的节点都更新掉
                                try:  # 在web框架通信时，因为是files中包含文件内容，不能放入json中，但可以放入files这个关键字中啊
                                    upload = requests.post(nodeAddress + 'upload', files=files, json=file_version_dict)
                                    j = j + 1
                                    print("Uploaded to " + nodeAddress)
                                    if j == len(list_of_nodes):
                                        fileVersion += 1
                                    else:
                                        print("Could not upload to " + nodeAddress)
                                    del upload
                                except BaseException:
                                    print('上传的节点可能出现故障。')
                                    upload = requests.post(true_address + '/server_one_backup/' + file_name,
                                                           files=files)
                                    j = j + 1
                                    if j == len(list_of_nodes):
                                        fileVersion += 1
                                finally:
                                    pass
                            lock_remove = requests.get(true_address + "/removelock/" + file_name,
                                                       json=client_ID)  # 因为包含自己更新文件的情况，所以不要忘记自己上传的锁要自己去掉
                            delete_download_lock(file_name)
                            if lock_remove.ok:
                                print("Lock Removed.")

                            overwrite_flag = True
                            return fileVersion  # 把它改到后面

                        elif choice == 'n':  # 文件存在但是你不想覆盖
                            new_filename = create_new_file_name(file_name)  # 该名字为新文件
                            print("Would you like to create " + new_filename + "? (y/n):", end=' ')
                            event, value = window.read()
                            if event == '确认':
                                choice = value['-input_text-'].replace("\n", "")
                                print(choice)
                                if choice == 'y':  # 你是否想再创建一个新的文件，如果想的话，首先在客户端的文件夹中就要创建出来
                                    copyfile((CLIENT_FOLDER + str(client_ID) + "/" + file_name),
                                             (CLIENT_FOLDER + str(client_ID) + "/" + new_filename))
                                    files = get_file(new_filename, client_ID)  # 从客户端文件夹中取出文件
                                    upload_address = server_json_response['addressToUploadTo']
                                    print("Uploading to ", upload_address)
                                    try:
                                        # 把新的文件名上传到制定的节点中
                                        upload = requests.post(upload_address + 'upload', files=files)
                                        if upload.ok:
                                            print("Uploaded to " + upload_address)  # 下面再次下载应该是为了改版本问题
                                            # download_file(newFilename, clientID, cachedFilesList)
                                            # 前面都复制过新文件到客户端的文件夹中了，如果没有这个download函数的话，我就不能再上传一次新文件了
                                            # 你下载的，又是你自己锁的，还要不覆盖创建一个新文件，这锁还是要你去掉
                                            lock_remove = requests.get(true_address + "/removelock/" + file_name,
                                                                       json=client_ID)
                                            delete_download_lock(file_name)
                                            if lock_remove.ok:
                                                print("Lock Removed.")
                                            return 1
                                        else:
                                            print("Could not upload to server")
                                            return 1
                                        del upload
                                    except BaseException:
                                        upload = requests.post(true_address + '/server_one_backup/' + file_name,
                                                               files=files)
                                        lock_remove = requests.get(true_address + "/removelock/" + file_name,
                                                                   json=client_ID)  # 你下载的，又是你自己锁的，还要不覆盖创建一个新文件，这锁还是要你去掉
                                        delete_download_lock(file_name)
                                        if lock_remove.ok:
                                            print("Lock Removed.")
                                        return 1
                                    finally:
                                        pass

                                # 文件已存在，不想覆盖还不想创建个新文件
                                elif choice == 'n':
                                    prompt()
                                    print("Upload cancelled.")  # 那就不上传，返回个版本号
                                    print("那你是否需要解锁这个文件:(y/n)", end=' ')
                                    event, value = window.read()
                                    if event == '确认':
                                        k = value['-input_text-'].replace("\n", "")
                                        print(k)
                                        if k == 'y':
                                            # 你下载的，又是你自己锁的，还要不覆盖创建一个新文件，这锁还是要你去掉
                                            lock_remove = requests.get(true_address + "/removelock/" + file_name,
                                                                       json=client_ID)
                                            delete_download_lock(file_name)
                                            if lock_remove.ok:
                                                print("Lock Removed.")
                                        overwrite_flag = True
                                        return fileVersion
                                print("Invalid answer.")

                        else:
                            print("Invalid answer.")

                elif judge['message'] == "0":
                    print('之前还有读的人没有解锁。')
                    overwrite_flag = 1
                    return fileVersion
                # 这是分界2
                elif judge['message'] == "2":
                    print("File with that name already exists on server.")
                    print("Would you like to overwrite it? (y/n):", end=' ')
                    event, value = window.read()
                    if event == '确认':
                        choice = value['-input_text-'].replace("\n", "")
                        print(choice)
                        if choice == 'y':  # 如果文件已存在，你还想覆盖，还要判断你的版本和服务器上的版本谁更新
                            files = get_file(file_name, client_ID)
                            file_version_dict = {'fileVersion': fileVersion}
                            if server_version > fileVersion:
                                print(
                                    "This file is outdated. Please download the new version from the server.\nServer "
                                    "version: " + str(
                                        server_version) + "\nYour version: " + str(fileVersion))
                                return fileVersion
                            print("Uploading to: ", server_json_response['nodeAddresses'])
                            list_of_nodes = server_json_response['nodeAddresses']  # 对目录服务器上所有拥有这个文件的节点地址
                            j = 0

                            for nodeAddress in list_of_nodes:  # 目的是将原本所有拥有这个文件的节点都更新掉
                                try:  # 看到没有，在web框架通信时，因为是files中包含文件内容，不能放入json中，但可以放入files这个关键字中啊
                                    upload = requests.post(nodeAddress + 'upload', files=files, json=file_version_dict)
                                    j = j + 1
                                    print("Uploaded to " + nodeAddress)
                                    if j == len(list_of_nodes):
                                        fileVersion += 1
                                    else:
                                        print("Could not upload to " + nodeAddress)
                                    del upload
                                except BaseException:
                                    print('上传的节点可能出现故障。')
                                    upload = requests.post(true_address + '/server_one_backup/' + file_name,
                                                           files=files)
                                    j = j + 1
                                    if j == len(list_of_nodes):
                                        fileVersion += 1
                                finally:
                                    pass
                            overwrite_flag = True
                            return fileVersion  # 把它改到后面

                        elif choice == 'n':  # 文件存在但是你不想覆盖
                            new_filename = create_new_file_name(file_name)  # 该名字为新文件
                            print("Would you like to create " + new_filename + "? (y/n):", end=' ')
                            event, value = window.read()
                            if event == '确认':
                                choice = value['-input_text-'].replace("\n", "")
                                print(choice)
                                if choice == 'y':  # 你是否想再创建一个新的文件，如果想的话，首先在客户端的文件夹中就要创建出来
                                    copyfile((CLIENT_FOLDER + str(client_ID) + "/" + file_name),
                                             (CLIENT_FOLDER + str(client_ID) + "/" + new_filename))
                                    files = get_file(new_filename, client_ID)  # 从客户端文件夹中取出文件
                                    upload_address = server_json_response['addressToUploadTo']
                                    print("Uploading to ", upload_address)
                                    try:
                                        upload = requests.post(upload_address + 'upload',
                                                               files=files)  # 把新的文件名上传到制定的节点中
                                        if upload.ok:
                                            print("Uploaded to " + upload_address)  # 下面再次下载应该是为了同步缓存文件夹和缓存表问题
                                            # download_file(newFilename, clientID, cachedFilesList)  # 前面都复制过新文件到客户端的文件夹中了，和上面同理
                                            return 1
                                        else:
                                            print("Could not upload to server")
                                            return 1
                                        del upload
                                    except BaseException:
                                        upload = requests.post(true_address + '/server_one_backup/' + file_name,
                                                               files=files)
                                        return 1
                                    finally:
                                        pass

                                # 文件已存在，不想覆盖还不想创建个新文件
                                elif choice == 'n':
                                    # print(chr(27) + "[2J")
                                    prompt()
                                    print("Upload cancelled.")  # 那就不上传咯，返回个版本号
                                    overwrite_flag = True
                                    return fileVersion
                                print("Invalid answer.")

                        else:
                            print("Invalid answer.")

        # 这是一般的情况
        elif server_json_response['message'] == 'File does not exist.':
            files = get_file(file_name, client_ID)  # 当上传的文件目录服务器中没有那就直接上传了
            upload_address = server_json_response['addressToUploadTo']
            try:
                upload = requests.post(upload_address + 'upload', files=files)
                if upload.ok:
                    print("Uploaded to " + upload_address)
                    return 1
                else:
                    print("Could not upload to server")
                    return 1
                del upload
            except BaseException:
                upload = requests.post(true_address + '/server_one_backup/' + file_name, files=files)
                return 1
            finally:
                pass


def remove_file(file_name):
    """
    函数说明: 向目录服务器申请删除某文件，这时目录服务器会自己询问每个拥有这个文件的节点是否删除
    param file_name: 文件名
    """
    try:
        response = requests.post(SERVER_ADDRESS + "/remove/" + file_name)
    except BaseException:
        print("主目录服务器崩溃，切换到备用服务器...")
        response = requests.post(VICE_ADDRESS + "/remove/" + file_name)
    if response.ok:
        print("<" + file_name + "> has been deleted form the server")
    else:
        print("<" + file_name + "> could not be deleted.")


def backup_file(file_name):
    """
    函数说明: 备份某文件，要先向目录服务器进行备份查询，然后再备份，一般感觉先是看了目录文件表后，发现某些文件很少节点拥有，这时为了保险起见，才执行的这个备份函数
    param file_name: 文件名
    """
    try:
        file_check = requests.get(SERVER_ADDRESS + "/backupcheck/" + file_name)
    except BaseException:
        print("主目录服务器崩溃，切换到备用服务器...")
        file_check = requests.get(VICE_ADDRESS + "/backupcheck/" + file_name)
    if file_check.ok:
        server_json_response = file_check.json()
        if server_json_response['message'] == 'File already exists.':
            addr = server_json_response['addressToUploadTo']
            print("Backing up to:", addr)
            try:
                backup = requests.get(addr[0] + "backup/" + file_name)
                temp1 = backup.json()
                temp2 = temp1['message']
                if temp2 == 'nice':
                    print("File backed up succesfully")
                else:
                    print("File backed up fail")
            except BaseException:
                print("备份的目标节点出现了故障，请稍后重试。")
            finally:
                pass
        else:
            print("Cannot backup")


def prompt():
    print("Hello. Welcome to our DFS.")
    print("--------------------------------\n")


# 返回此当前节点的ID
def get_client_id():  # 需要输入个参数，作为客户端的ID
    if len(sys.argv) > 0:
        return int(sys.argv[1])
    return 1


clientID = get_client_id()
create_folders(clientID)  # 创建客户端的文件夹和缓存文件夹

# 跟踪所有缓存的文件
# |Date[0]     |   Hour[1]|   Minute[2]|   Version[3]|
# cachedFiles['index.pdf'] = ['2017-11-30',      '13',        '03',            2]
cachedFiles = {}  # 用于记录缓存文件夹中的文件以及其时间和版本
update_cache_list(clientID, cachedFiles)  # cachedFiles表初始化和更新，将客户端文件夹中没有在缓存表中的文件记录到缓存表中

# 启动UI
sg.ChangeLookAndFeel('LightGreen')

# ------ Menu Definition ------ #
menu_def = [['文件', ['上传文件', '下载文件']],
            ['编辑', ['备份文件', '删除文件']],
            ['查看', ['查看服务器文件', '查看本地文件', '查看备份文件']],
            ['工具', '解读锁'],
            ['帮助', '关于']]

button_menu_def = ['查看文件', ['查看服务器文件', '查看本地文件', '查看备份文件']]

# ------ GUI Definition ------ #
button_size_tuple = (6, 1)  # 按钮大小
button_color_tuple = (sg.YELLOWS[0], sg.GREENS[0])  # 按钮颜色
padding = (4, 4)
layout = [[sg.Menu(menu_def, )],
          [sg.Button('上传文件', size=button_size_tuple, button_color=button_color_tuple, pad=padding),
           sg.Button('下载文件', size=button_size_tuple, button_color=button_color_tuple, pad=padding),
           sg.Button('备份文件', size=button_size_tuple, button_color=button_color_tuple, pad=padding),
           sg.Button('删除文件', size=button_size_tuple, button_color=button_color_tuple, pad=padding),
           sg.ButtonMenu('查看文件', menu_def=button_menu_def, key='-view_file-', size=button_size_tuple,
                         button_color=button_color_tuple,
                         pad=padding),
           sg.Button('解读锁', size=button_size_tuple, button_color=button_color_tuple, pad=padding)],
          [sg.InputText(size=(40, 1), default_text='请在这里输入...', key='-input_text-', do_not_clear=False, border_width=2,
                        pad=padding),
           sg.Button('确认', button_color=('white', sg.BLUES[0]), pad=padding),
           sg.Button('退出', button_color=('white', '#9B0023'), pad=padding)],
          [sg.Output(size=(80, 20), pad=padding)]]

# Create the window
window = sg.Window('DFS客户端' + str(clientID), layout, default_element_size=(30, 2))

# Display and interact with the Window using an Event Loop
while True:
    event, value = window.read()
    if event in (sg.WIN_CLOSED, '退出'):
        break
    elif event == '上传文件':
        # 每当您上载时，请刷新缓存以查看文件是否已移动到客户端文件夹
        update_cache_list(clientID, cachedFiles)  # 你平时有可能会直接把文件放入到客户端的文件中，这时更新缓存表，相当于又记录了你自己拖进文件夹的文件
        # 所以调用这个更新缓存表的函数后，此时的缓存表里面的内容相当于包含了之前到现在所有的文件夹里面的文件的信息（那些自己拖进去的文件没有时间和版本，只有文件名信息）
        print_list_of_files(clientID)  # 打印出客户端的文件名
        print("Enter file name to upload:", end=' ')
        event, value = window.read()
        if event == '确认':
            filename = value['-input_text-'].replace("\n", "")
            print(filename)
            # 相当于只有文件在缓存文件表上即在客户端文件夹上的文件才可以上传，上传后改缓存文件表中对应文件的版本号
            if filename in cachedFiles.keys():
                # 将文件上传到服务器上，返回的是文件的版本号
                cachedFiles[filename][3] = upload_file(filename, clientID, cachedFiles[filename][3], cachedFiles)
            else:
                print("That file does not exist")

    elif event == '下载文件':
        print_server_files()  # 打印出在服务器上所有文件的文件名
        print("Enter file name to download:", end=' ')
        event, value = window.read()
        if event == '确认':
            filename = value['-input_text-'].replace("\n", "")
            print(filename)
            download_file(filename, clientID, cachedFiles)  # 下载文件到客户端的文件夹中

    elif event == '备份文件':
        print_server_files()
        print("Enter file name to backup:", end=' ')
        event, value = window.read()
        if event == '确认':
            filename = value['-input_text-'].replace("\n", "")
            print(filename)
            listOfFiles = get_server_dict()  # 返回目录服务器中的文件目录表nodeAddresses
            if filename in listOfFiles.keys():
                backup_file(filename)  # 只能备份已有的文件，一般是让你看到服务器中有什么文件，然后你发现某些文件所在的节点很少，这时你才选择备份它
            else:
                print("File doesn't exsist on server.")

    elif event == '删除文件':
        print_server_files()
        print("Enter file name to delete:", end=' ')
        event, value = window.read()
        if event == '确认':
            filename = value['-input_text-'].replace("\n", "")
            print(filename)
            listOfFiles = get_server_dict()
            if filename in listOfFiles.keys():
                remove_file(filename)  # 删除文件也是你看到服务器的所有文件名后，再打算删除服务器上所有节点的这个文件，不够代码时间好像有点问题
            else:
                print("File doesn't exsist on server.")

    elif '查看服务器文件' in (event, value['-view_file-']):
        print_server_files()

    elif '查看本地文件' in (event, value['-view_file-']):
        print_list_of_files(clientID)  # 打印出你客户端文件夹中的文件

    elif '查看备份文件' in (event, value['-view_file-']):
        print_server_all_backup_file()

    elif event == '解读锁':
        print_download_file()
        print('\n请输入你要解锁的文件名:', end=' ')
        event, value = window.read()
        if event == '确认':
            filename = value['-input_text-'].replace("\n", "")
            print(filename)
            if filename in local_download_file.keys():
                if local_download_file[filename] == 'r':
                    temp1 = requests.get(SERVER_ADDRESS + '/removelock' + '/' + filename, json=clientID)
                    temp2 = temp1.json()
                    hello = temp2['message']
                    if hello == 'success':
                        delete_download_lock(filename)
                        print("输入的文件已解锁.")
                    else:
                        print('解锁失败.')
                elif local_download_file[filename] == 'w':
                    print('解锁失败，你之前对这个文件申请了写锁，请通过上传此文件去解锁.')
            else:
                print('你没有对此文件解锁或你的客户端可能重启过.')

    elif event == '关于':
        sg.popup('About this program', 'Version 1.0', 'Distributed file system', 'Author: 蔡孟栾 & 邬小军')

# Finish up by removing from the screen
window.close()
