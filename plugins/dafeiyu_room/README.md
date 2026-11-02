# 大肥鱼房间

一个 3D 房间，她在里面按**时间 + 聊天状态**做不同的事。

## 状态

| 条件 | 状态 |
|---|---|
| 0–8 点 | 睡觉 |
| 8–19 点 | 电脑前 |
| 19–24 点 | 床上刷手机 |
| 你刚发消息 | 立刻拿手机 |
| 25 分钟没说话 | 回到按时段的默认 |

## 页面

3D 房间（浅色大理石、奶油沙发、深木橱柜、晨光窗）+
主体角色 + 左下角对话流 + 右上角心情条。

## 换成自己的模型

把 `.glb` 或 `.vrm` 放到 `pages/room/model/character.glb`，
页面会自动加载并挑 `idle / sleep / work / phone` 四类动画；
没有模型就用内置的卡通形象。

## 命令

`/房间` 查看当前状态。

## 常见问题

**页面一直停在「正在搭建她的房间」，黑屏**

三个东西缺一个就会卡住（浏览器控制台会有 404）：

```
pages/room/three/build/three.module.js
pages/room/three/examples/jsm/utils/BufferGeometryUtils.js
pages/room/three/examples/jsm/utils/SkeletonUtils.js
```

前两个是 three 主库，后两个是 `GLTFLoader.js` 依赖的工具模块（three r187 起 requirement）。
缺 `BufferGeometryUtils` / `SkeletonUtils` 时页面不会报错，只是永远不结束加载。

**画面里没有人，只有房间**

正常会回退到内置卡通形象；如果连卡通形象都没有，看控制台是否有 WebGL 报错。
