---
title: "Kubernetes 笔记"
published: 2023-09-06
categories: 
  - "kubernetes"
  - "laboratory"
---

# 1\. Kubernetes介绍

Kubernetes 是一个可移植、可扩展的开源平台，用于管理容器化的工作负载和服务，可促进声明式配置和自动化。 Kubernetes 拥有一个庞大且快速增长的生态，其服务、支持和工具的使用范围相当广泛。

**Kubernetes** 这个名字源于希腊语，意为“舵手”或“飞行员”。k8s 这个缩写是因为 k 和 s 之间有八个字符的关系。 Google 在 2014 年开源了 Kubernetes 项目。 Kubernetes 建立在 [Google 大规模运行生产工作负载十几年经验](https://research.google/pubs/pub43438)的基础上， 结合了社区中最优秀的想法和实践。

## 1.1应用部署方式演变

在部署应用程序的方式上，主要经历了三次演变：

- 传统部署：互联网早期，会直接将应用程序部署在物理机上

```
优点：简单，不需要其它技术的参与
缺点：不能为应用程序定义资源使用边界，很难合理地分配计算资源，而且程序之间容易产生影响
```

- 虚拟化部署：可以在一台物理机上运行多个虚拟机，每个虚拟机都是独立的一个环境

```
优点：程序环境不会相互产生影响，提供了一定程度的安全性
缺点：增加了操作系统，浪费了部分资源
```

- 容器化部署：与虚拟化类似，但是共享了操作系统

```
优点：可以保证每个容器拥有自己的文件系统、CPU、内存、进程空间等，运行应用程序所需要的资源都被容器包装，并和底层基础架构解耦，容器化的应用程序可以跨云服务商、跨Linux操作系统发行版进行部署
```

<picture>
    <source srcset="https://s3.catcat.blog/images/2023/09/image-22-1024x385.avif" type="image/avif">
    <source srcset="https://s3.catcat.blog/images/2023/09/image-22-1024x385.webp" type="image/webp">
    <img src="https://s3.catcat.blog/images/2023/09/image-22-1024x385.jpg" alt="" loading="lazy">
</picture>

容器化部署方式给带来很多的便利，但是也会出现一些问题，比如说：

一个容器故障停机了，怎么样让另外一个容器立刻启动去替补停机的容器？  
当并发访问量变大的时候，怎么样做到横向扩展容器数量？  
这些容器管理的问题统称为容器编排问题，为了解决这些容器编排问题，就产生了一些容器编排的软件：

- Swarm：Docker自己的容器编排工具

- Mesos：Apache的一个资源统一管控的工具，需要和Marathon结合使用

- Kubernetes：Google开源的的容器编排工具

## 1.2Kubernetes的诞生

Kubernetes，是一个全新的基于容器技术的分布式架构领先方案，是谷歌严格保密十几年的秘密武器----Borg系统的一个开源版本，于2014年9月发布第一个版本，2015年7月发布第一个正式版本。

<figure>

<picture>
    <source srcset="https://s3.catcat.blog/images/2023/09/borg.avif" type="image/avif">
    <source srcset="https://s3.catcat.blog/images/2023/09/borg.webp" type="image/webp">
    <img src="https://s3.catcat.blog/images/2023/09/borg.jpg" alt="" loading="lazy">
</picture>

<figcaption>

Borg系统

</figcaption>

</figure>

kubernetes的本质是一组服务器集群，它可以在集群的每个节点上运行特定的程序，来对节点中的容器进行管理。目的是实现资源管理的自动化，主要提供了如下的主要功能：

- 自我修复：一旦某一个容器崩溃，能够在1秒中左右迅速启动新的容器

- 弹性伸缩：可以根据需要，自动对集群中正在运行的容器数量进行调整

- 服务发现：服务可以通过自动发现的形式找到它所依赖的服务

- 负载均衡：如果一个服务起动了多个容器，能够自动实现请求的负载均衡

- 版本回退：如果发现新发布的程序版本有问题，可以立即回退到原来的版本

- 存储编排：可以根据容器自身的需求自动创建存储卷

## 1.3 Kubernetes组件

一个kubernetes集群主要是由控制节点(master)、\*\*工作节点(node)\*\*构成，每个节点上都会安装不同的组件。

**master：集群的控制平面，负责集群的决策 ( 管理 )**

```
ApiServer : 资源操作的唯一入口，接收用户输入的命令，提供认证、授权、API注册和发现等机制
Scheduler : 负责集群资源调度，按照预定的调度策略将Pod调度到相应的node节点上
ControllerManager : 负责维护集群的状态，比如程序部署安排、故障检测、自动扩展、滚动更新等
Etcd ：负责存储集群中各种资源对象的信息
```

**node：集群的数据平面，负责为容器提供运行环境 ( 干活 )**

```
Kubelet : 负责维护容器的生命周期，即通过控制docker，来创建、更新、销毁容器
KubeProxy : 负责提供集群内部的服务发现和负载均衡
Docker : 负责节点上容器的各种操作
```

<picture>
    <source srcset="https://s3.catcat.blog/images/2023/09/image-23-1024x531.avif" type="image/avif">
    <source srcset="https://s3.catcat.blog/images/2023/09/image-23-1024x531.webp" type="image/webp">
    <img src="https://s3.catcat.blog/images/2023/09/image-23-1024x531.jpg" alt="" loading="lazy">
</picture>

**下面，以部署一个nginx服务来说明kubernetes系统各个组件调用关系：**

- 首先要明确，一旦kubernetes环境启动之后，master和node都会将自身的信息存储到etcd数据库中

- 一个nginx服务的安装请求会首先被发送到master节点的apiServer组件

- apiServer组件会调用scheduler组件来决定到底应该把这个服务安装到哪个node节点上

- 在此时，它会从etcd中读取各个node节点的信息，然后按照一定的算法进行选择，并将结果告知apiServer

- apiServer调用controller-manager去调度Node节点安装nginx服务

- kubelet接收到指令后，会通知docker，然后由docker来启动一个nginx的pod

- pod是kubernetes的最小操作单元，容器必须跑在pod中至此，

- 一个nginx服务就运行了，如果需要访问nginx，就需要通过kube-proxy来对pod产生访问的代理

## 1.4Kubernetes组件核心概念

### 1.4.1 服务的分类

- 无状态应用：不会对本地环境产生任何依赖，例如不会将数据存储到磁盘

- 有状态应用：会对本地环境产生任何依赖，例如需要将数据存储到磁盘

<picture>
    <source srcset="https://s3.catcat.blog/images/2023/09/image-25-1024x393.avif" type="image/avif">
    <source srcset="https://s3.catcat.blog/images/2023/09/image-25-1024x393.webp" type="image/webp">
    <img src="https://s3.catcat.blog/images/2023/09/image-25-1024x393.jpg" alt="" loading="lazy">
</picture>

<picture>
    <source srcset="https://s3.catcat.blog/images/2023/09/image-26-1024x500.avif" type="image/avif">
    <source srcset="https://s3.catcat.blog/images/2023/09/image-26-1024x500.webp" type="image/webp">
    <img src="https://s3.catcat.blog/images/2023/09/image-26-1024x500.jpg" alt="" loading="lazy">
</picture>

### 1.4.2 资源和对象

Kubernetes 中的所有内容都被抽象为“资源”，如 Pod、Service、Node 等都是资源。“对象”就是“资源”的实例，是持久化的实体。如某个具体的 Pod、某个具体的 Node。Kubernetes 使用这些实体去表示整个集群的状态。

 对象的创建、删除、修改都是通过 “Kubernetes API”，也就是 “Api Server” 组件提供的 API 接口，这些是 RESTful 风格的 Api，与 k8s 的“万物皆对象”理念相符。命令行工具 “kubectl”，实际上也是调用kubernetes api。

 K8s 中的资源类别有很多种，kubectl 可以通过配置文件来创建这些 “对象”，配置文件更像是描述对象“属性”的文件，配置文件格式可以是 “JSON” 或 “YAML”，**常用 “YAML”**。

#### 1.4.2.1 对象规约和状态

- 规约（Spec）：“_spec_” 是 “规约”、“规格” 的意思，spec 是必需的，它描述了对象的**期望状态**（Desired State）—— 希望对象所具有的特征。当创建 Kubernetes 对象时，必须提供对象的规约，用来描述该对象的期望状态，以及关于对象的一些基本信息（例如名称）。

- 状态（Status）：表示**对象的实际状态**，该属性由 k8s 自己维护，k8s 会通过一系列的控制器对对应对象进行管理，让对象尽可能的让实际状态与期望状态重合。

#### 1.4.2.2 资源的分类

- 集群：物理意义上，作用于集群之上，集群下所有资源可以共享

- 命名空间：逻辑意义上的集群，作用于这个命名空间内，只能使用这个范围内的资源

- 元数据：对于资源的元数据描述，每一个资源都可以使用元空间的数据

<picture>
    <source srcset="https://s3.catcat.blog/images/2023/09/image-27-1024x398.avif" type="image/avif">
    <source srcset="https://s3.catcat.blog/images/2023/09/image-27-1024x398.webp" type="image/webp">
    <img src="https://s3.catcat.blog/images/2023/09/image-27-1024x398.jpg" alt="" loading="lazy">
</picture>
