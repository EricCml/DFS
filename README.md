# 分布式文件系统

## 项目环境

操作系统：Windows 10 64位

编程语言：Python 3.8

编译器：JetBrains PyCharm

配置环境：使用到的依赖包见代码目录中的requirements.txt文件

## 系统架构

​		本项目采用Client-Server(C/S)结构，即客户端-服务器模型，服务器负责数据的管理，客户机负责完成与用户的交互任务。与C/S结构通常采取的两层结构不同，本系统服务器采用两层结构，即节点服务器和目录服务器。节点服务器主要用于文件的存储和备份，与客户端直接进行文件下载、上传等操作；目录服务器主要用于收集节点服务器群的文件信息，以响应客户端的各类请求。系统整体结构如下图所示。

![系统整体结构图](C:\Users\Peace\AppData\Roaming\Typora\typora-user-images\image-20210526084625863.png)

​		目录服务器包括主目录服务器和备用目录服务器，每个目录服务器都有一个系统备份的文件夹，和目录服务器表。最核心的部分是目录服务器表的结构，因为客户端每次的交互都需先通过目录服务器。目录服务器表由节点文件信息、连接节点信息、文件读写锁信息和节点权重信息组成，具体结构如下图所示。

![目录服务器表结构图](C:\Users\Peace\AppData\Roaming\Typora\typora-user-images\image-20210526084720247.png)

​		节点服务器之间互相独立，各自存储不同的文件信息，同时节点之间也可以互相通信。针对节点服务器文件的管理，我们采用了负载均衡的算法尽量保证每个节点服务器存储文件的数量大致相同，防止某单一节点服务器压力过大而崩溃。由于节点服务器之间的独立性，那么对文件系统来说，新增或删除节点服务器就变得容易，文件系统的可扩展性强。

​		客户端我们引入了Cashing File，主要是在完成客户端的开发时，目光更多聚焦在如何让本地的读写效率更高，便采用了缓存的方式以提高客户端的读写效率。

## 项目代码结构

![项目代码结构图](C:\Users\Peace\AppData\Roaming\Typora\typora-user-images\image-20210526084603230.png)

上图为本项目的代码结构。分为两个目录。下文是每个文件的简要说明。（__init__.py为Python包的初始化文件）

1. files —— 文件存放目录

   - clientFiles —— 存放客户端文件
   - nodeFiles —— 存放节点服务器文件
   - serverFiles —— 存放目录服务器文件

2. src —— 源代码目录

   - Client包
     - client.py —— 客户端功能实现
     - clientConfig.py —— 客户端配置文件

   - DirectoryServer包
     - directoryServer.py —— 目录服务器功能实现
     - directoryServerConfig.py —— 目录服务器配置文件

   - NodeServer包
     - nodeServer.py —— 节点服务器功能实现

     - nodeServerConfig.py —— 节点服务器配置文件