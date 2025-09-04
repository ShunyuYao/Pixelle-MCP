# OSS存储配置指南

本文档介绍如何配置CreateUI-MCP项目使用阿里云OSS存储来替代本地存储，将多媒体内容（图像、视频等）上传到OSS并返回CDN URL。

## 概述

CreateUI-MCP项目支持两种存储方式：
1. **本地存储** (local) - 文件存储在本地服务器
2. **OSS存储** (oss) - 文件存储在阿里云OSS，通过CDN访问

## 配置步骤

### 1. 准备OSS资源

首先需要在阿里云OSS控制台创建以下资源：

1. **创建Bucket**
   - 登录阿里云OSS控制台
   - 创建一个新的Bucket（建议使用私有读写权限）
   - 记录Bucket名称和Endpoint

2. **创建AccessKey**
   - 在阿里云RAM控制台创建AccessKey
   - 记录AccessKey ID和AccessKey Secret
   - 确保该AccessKey有OSS读写权限

3. **配置CDN（可选但推荐）**
   - 在阿里云CDN控制台添加加速域名
   - 将OSS Bucket作为源站
   - 记录CDN域名

### 2. 修改配置文件

编辑 `config.yml` 文件，添加OSS配置：

```yaml
# Base service configuration
base:
  # ... 其他配置 ...
  
  # Storage configuration - 关键配置
  storage_type: oss     # 使用OSS存储
  
  # OSS配置
  oss_access_key_id: "your_oss_access_key_id"
  oss_access_key_secret: "your_oss_access_key_secret"
  oss_endpoint: "oss-cn-shanghai.aliyuncs.com"
  oss_bucket_name: "your_bucket_name"
  oss_cdn_domain: "your_cdn_domain.com"

# MCP Server configuration
server:
  # ... 其他配置 ...
  
  # OSS配置（与base部分保持一致）
  oss_access_key_id: "your_oss_access_key_id"
  oss_access_key_secret: "your_oss_access_key_secret"
  oss_endpoint: "oss-cn-shanghai.aliyuncs.com"
  oss_bucket_name: "your_bucket_name"
  oss_cdn_domain: "your_cdn_domain.com"
```

### 3. 安装依赖

确保安装了OSS SDK：

```bash
pip install oss2
```

### 4. 重启服务

修改配置后需要重启所有服务：

```bash
# 停止所有服务
./run.sh stop

# 启动所有服务
./run.sh start
```

## 功能说明

### 1. 文件上传流程

启用OSS存储后，文件上传流程变为：

1. **用户上传文件** → 2. **mcp-base接收** → 3. **上传到OSS** → 4. **返回CDN URL**

### 2. ComfyUI输出处理

ComfyUI生成的图像、视频等输出会自动：

1. **ComfyUI生成结果** → 2. **保存到本地ComfyUI服务器** → 3. **下载到临时文件** → 4. **上传到OSS** → 5. **返回CDN URL**

### 3. 文件组织结构

OSS中的文件按以下结构组织：

```
your_bucket/
├── mcp_base_files/          # mcp-base上传的文件
│   ├── file_id_1.jpg
│   ├── file_id_2.mp4
│   └── ...
├── comfyui_outputs/         # ComfyUI输出文件
│   ├── timestamp_1_image.png
│   ├── timestamp_2_video.mp4
│   └── ...
└── comfyui_inputs/          # ComfyUI输入文件
    ├── input_image_1.jpg
    └── ...
```

## 配置示例

参考 `config_oss_example.yml` 文件查看完整的配置示例。

## 故障排除

### 1. OSS上传失败

检查以下配置：
- AccessKey ID和Secret是否正确
- Bucket名称是否正确
- Endpoint是否正确
- 网络连接是否正常

### 2. CDN访问失败

检查以下配置：
- CDN域名是否正确
- CDN是否已配置源站
- CDN是否已启用

### 3. 权限问题

确保AccessKey具有以下权限：
- `oss:PutObject` - 上传文件
- `oss:GetObject` - 下载文件
- `oss:DeleteObject` - 删除文件
- `oss:ListObjects` - 列出文件

## 性能优化

### 1. 使用CDN

强烈建议配置CDN，可以显著提升文件访问速度。

### 2. 选择合适的OSS区域

选择离用户最近的OSS区域，减少网络延迟。

### 3. 文件压缩

对于大文件，可以考虑在上传前进行压缩。

## 安全考虑

### 1. AccessKey安全

- 定期轮换AccessKey
- 使用RAM用户而不是主账号
- 限制AccessKey的权限范围

### 2. Bucket权限

- 建议使用私有读写权限
- 通过CDN提供公开访问
- 定期检查Bucket访问日志

### 3. 文件安全

- 对敏感文件设置访问控制
- 定期清理无用文件
- 监控异常访问

## 回退方案

如果OSS配置出现问题，可以临时切换回本地存储：

```yaml
base:
  storage_type: local  # 切换回本地存储
```

系统会自动处理存储方式的切换，无需修改代码。
