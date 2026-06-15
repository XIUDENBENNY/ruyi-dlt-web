# 如意大乐透神机妙算系统

这是一个可部署到 GitHub Pages 的静态网页版本。

## 功能

- 智能选号：奖池分段、防历史重复、红球相似度过滤
- 随机选号、热号优先、冷号优先
- 历史数据查询
- 红蓝球频率、奖池分段、近 30 期形态摘要
- GitHub Actions 定时抓取并更新数据

## 数据更新

数据更新由 `.github/workflows/update-data.yml` 执行：

- 支持手动运行 `workflow_dispatch`
- 每天北京时间 23:30 左右自动运行
- 抓取成功后更新：
  - `data/dlt_history.csv`
  - `docs/data/dlt_history.csv`
  - `docs/data/dlt_history.json`

## GitHub Pages

Pages 发布目录建议设置为：

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/docs`

网页入口为 `docs/index.html`。
