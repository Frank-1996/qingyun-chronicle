# 腾讯 EdgeOne Pages 部署

导入原有 `Frank-1996/qingyun-chronicle` GitHub仓库，生产分支 `main`，仓库根目录 `./`，静态框架选择Other／其他。

`edgeone.json`固定构建配置：

- Node.js：22.11.0，平台预装版本。
- 安装命令：`node --version`。项目没有第三方依赖，无需访问npm下载依赖。
- 构建命令：`npm test`，通过现有46项测试后发布。
- 输出目录：`dist`。只发布静态HTML、JavaScript、CSS和游戏数据。
- 环境变量：不需要。

使用GitHub原生连接，保留自动部署；后续main更新由平台自动构建和发布。首次部署后应再推送一次可审阅的文档更新，确认自动部署确实触发，而不是只完成一次手工上传。

发布验收：核对生产部署绑定的仓库与提交、HTTPS访问地址、页面v0.6.0及mobile.css／compat.js等同源资源、手机尺寸布局，以及项目设置中的Git自动部署。

中国大陆加速与默认域名的长期使用条件以控制台当前选项为准。若平台要求绑定自定义域名或ICP备案，需先满足对应条件，不能仅凭部署成功承诺中国大陆所有网络或微信均可访问。

不更改现有Vercel与GitHub Pages配置。浏览器本地存档按域名隔离，迁移到新地址时可用游戏里的JSON文本导出／导入。

参考：[EdgeOne配置文档](https://edgeone.cloud.tencent.com/pages/document/162936771610066944)、[Git构建指南](https://edgeone.cloud.tencent.com/pages/document/162936788693114880)。
