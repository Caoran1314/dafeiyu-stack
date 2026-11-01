# 在 NAS 上跑安卓（VM 路线）

目标：在 fnOS 上开一台安卓虚拟机，让她能在里面**真的刷抖音**，并截图发到你 QQ。

## 为什么不用容器化安卓

| 方案 | 需要 | 你的机器 |
|---|---|---|
| redroid / Waydroid | 宿主内核启用 `binder` | ❌ `6.18.18.c1126-trim` 没编进 binder，也没有内核头文件可补 |
| **VM + Android-x86/BlissOS** | `/dev/kvm` | ✅ 有（`kvm_intel` 已加载） |

容器化方案需要宿主内核的 `binder` 驱动，编译它又需要内核头文件——fnOS 不提供，所以走 VM。

## 硬件情况（已确认）

```
/dev/kvm          crw-rw---- root kvm      → 硬件虚拟化可用
/dev/dri/card0    UHD 770 核显              → 可给 VM 做图形加速
/dev/dri/renderD128                          → VAAPI 编解码
kvm_intel 已加载
```

## 一、创建虚拟机

fnOS → **应用中心** → 安装「虚拟机」→ 新建。

| 项 | 建议值 | 说明 |
|---|---|---|
| 系统类型 | Linux（其他） | 安卓就是 Linux 内核 |
| 固件 | UEFI | BlissOS 需要 |
| CPU | 4 核，`host-passthrough` | 型号透传性能最好 |
| 内存 | 4096 MB | 抖音吃内存，少于 3G 会卡 |
| 磁盘 | 16 GB（qcow2） | 系统 4G + 抖音 1G + 余量 |
| 显示 | virtio-gpu（有 3D/ virgl 就开） | 视频流畅的关键 |
| 网络 | **桥接**（br0） | 要给固定 IP，方便 ADB 连 |
| 光驱 | 挂 ISO | 见下 |

## 二、选镜像

| 镜像 | 优点 | 缺点 |
|---|---|---|
| **BlissOS 15.x（Android 12L）** | 对 KVM 友好，可开 virtio-gpu | ARM 翻译要选带 houdini / libndk 的构建 |
| Android-x86 9.0-r2 | 自带 `enable_nativebridge` 装 houdini | 系统老，部分新版 App 不兼容 |

**关键是 ARM 翻译**：抖音只发布 ARM 版 APK，x86 安卓必须靠 houdini / libndk 翻译才装得上。
装完后到「设置 → 关于手机」看有没有 `native bridge: houdini` 之类的字样。

## 三、装系统

1. 挂 ISO，开机选 **Installation** → 装到 16G 磁盘
2. 分区选 ext4，**勾选安装 GRUB**
3. 装完拔掉 ISO，重启进系统
4. 首次进桌面：连网 → 开发者选项（连点版本号 7 次）→ **USB 调试 + 无线调试**

## 四、开 ADB

两种方式，任选：

**方式 A：网络 ADB（推荐）**

```bash
# 在安卓里开"无线调试"，或者在终端模拟器里：
setprop service.adb.tcp.port 5555
stop adbd && start adbd
```

**方式 B：宿主直接连**

```bash
sudo apt install adb -y
adb connect <安卓VM的IP>:5555
adb devices
```

## 五、接到 AstrBot

1. 装 `astrbot_phone_control`（市场搜「手机操控」或填作者仓库）
2. 打开它的「ADB 连接」配置：

| 字段 | 值 |
|---|---|
| host | `<安卓VM的IP>`（桥接网络下的地址） |
| port | `5555` |

3. 保存 → 重载插件 → 在 QQ 发：

```
/phone status
```

能看到设备信息就通了。

4. 试刷：

```
/phone task 打开抖音刷 3 条
/phone browse douyin 3
```

## 六、接上分享桥

> 分享桥已验证可推送：23:28 实测在 QQ 收到「刚刷到这个」+ 图。
> 会话 ID 用 `napcat:FriendMessage:<你的QQ>`，不是 `aiocqhttp:...`。


她刷完会截图。把截图目录填进 `dafeiyu_douyin_bridge` 的 `watch_dirs`：

```
/AstrBot/data/plugin_data/astrbot_phone_control/shots
```

没配也能用：直接往 `data/astrbot/plugin_data/dafeiyu_douyin_bridge/inbox/` 丢图。

## 七、抖音安装

```bash
# 宿主机上
adb install douyin.apk
adb shell am start -n com.ss.android.ugc.aweme/.splash.SplashActivity
```

- 用小号登录
- 如果报 `INSTALL_FAILED_NO_MATCHING_ABIS` → ARM 翻译没生效，换带 houdini 的镜像
- 如果闪退 → 换 Android 9 的 Android-x86 或降级抖音版本

## 八、这条路的三个真实风险

| 风险 | 说明 | 退路 |
|---|---|---|
| **视频卡顿** | 无 GPU 直通时靠 virgl 软渲染 | 只看图文/滑动，不追求流畅播放 |
| **抖音识别模拟器** | 可能限流或要验证 | 小号 + 低频使用 |
| **ARM 翻译不完整** | 部分版本装不上 | 换镜像，或改走云手机 |

## 九、不想折腾的替代

| 方案 | 成本 | 上线时间 |
|---|---|---|
| 云手机（ADB 可达） | 30–60 元/月 | 半小时 |
| 先用 inbox 丢图 | 0 | 已可用 |
| 改刷 B 站（`astrbot_plugin_bili_scroll`） | 0，无需设备 | 半小时 |

## 十、验收清单

```bash
# 1. VM 起来了
adb connect <ip>:5555 && adb devices

# 2. 抖音装了
adb shell pm list packages | grep aweme

# 3. phone_control 认到设备
/phone status

# 4. 她刷了
/phone task 打开抖音刷 3 条

# 5. 分享桥推了
/刷到了          # 或等她自动发

# 6. 房间也变了
/房间
```
