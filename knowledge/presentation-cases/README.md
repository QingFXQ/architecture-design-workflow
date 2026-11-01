# 建筑作业与表达排版案例库

首批7条：3个真实获奖学生作业图板、3个作者表达教程／跨页、1个用户视觉参考。已在原始学校出版物／作者页面核来源，6条公共图件实际打开查看；用户参考按本对话所见记录。不是收集不明来历的“免费PSD”。

| 案例 | 原始来源与可借鉴内容 |
| --- | --- |
| [PC-01](cards/PC-01.md) Maker + Market | UNL 2021 SGH Concepts / Dri-Design，PDF第17页；主透视与次级图解 |
| [PC-02](cards/PC-02.md) Canopy | 同册第34页；多层平面比较与剖面组 |
| [PC-03](cards/PC-03.md) Yankee Hill Branch Library | 同册第43页；内景与剖面成组解释空间 |
| [PC-04](cards/PC-04.md) Mountain Lodge | 作者场地跨页；地形、色彩和背景组织 |
| [PC-05](cards/PC-05.md) Desert House | 作者跨页；标题份量与斜向主图 |
| [PC-06](cards/PC-06.md) Cliff Retreat | 作者剖面跨页；场地尺度与空间剖面层级 |

## 使用

```powershell
python tools/presentation_cases/find_case.py --query "竖版 主图"
python tools/presentation_cases/find_case.py --query "剖面 高差"
python tools/presentation_cases/find_case.py --check
```

选择与纸幅／横竖／图件密度相符的少量参考，再打开原图看整版与字级。卡片只说明可迁移方法和限制，不代替看图；作品集跨页不是A1模板，出版PDF页框也不是原图板纸幅。

把自己的图按最终纸面毫米做预案，主图、图组、比例和最小字高成立后再制作分析图。参考不是复制建筑或把别人作品当装饰；公开可见不等于拥有源图／字体／PSD分发许可。

## 扩充

优先学校／赛事／学生或作者原始发布，记录作者、具体页／图、纸幅是否已知、实际看图日期、可迁移方法、不适用项和许可。新条目加入catalog并运行--check。没有看图就写待看，不伪装已视觉验证；淘汰的参考写原因，不靠“高级／简约”空词分类。

原图私有检视缓存放用户指定磁盘，本机在E盘；仓库保留来源链接与自写笔记，避免大文件和不明版权包。流程见[PRESENTATION_WORKFLOW](../../workflows/PRESENTATION_WORKFLOW.md)。
