# 展品目录 / Exhibit Catalog

> 本页由 `python3 scripts/catalog.py --write` 生成。请修改各展品的 `exhibit.json`，不要直接编辑表格。

## 总览

- 展品数量：**4**
- 语言数量：**2**
- 当前最高 SMI：**100**

| 编号 | 展品 | 语言 | 主要异味 | 合同 | SMI | 状态 |
|---:|---|---|---|---|---:|---|
| `000` | [`Hello Shitmountain`](../shit_demo.java) | Java | 类名小写、孤立根目录、缺少上下文 | `历史样本` | **1** | 永久陈列 |
| `001` | [`If-Else Volcano`](../exhibits/java/001-if-else-volcano/) | Java | 嵌套判断、魔法值、字符串类型系统 | `equal-output` | **73** | 活跃喷发 |
| `002` | [`One Class to Rule Them All`](../exhibits/java/002-one-class-to-rule-them-all/) | Java | God Object、共享状态、职责兼并 | `equal-output` | **100** | 王座失控 |
| `003` | [`Mutable Default Argument Swamp`](../exhibits/python/003-mutable-default-swamp/) | Python | 可变默认参数、跨调用状态污染、隐式共享状态 | `expected-difference` | **32** | 沼泽扩散 |

## 按语言浏览

### Java

#### `000` · [Hello Shitmountain](../shit_demo.java)

仓库创建时留下的祖传五行 Java 样本，作为项目历史原点永久陈列。

- 主要异味：类名小写、孤立根目录、缺少上下文
- 行为合同：`历史样本`
- SMI：**1**，轻微异味，可步行参观
- 主要计分来源：含糊命名 1
- 展区状态：永久陈列

#### `001` · [If-Else Volcano](../exhibits/java/001-if-else-volcano/)

折扣规则不断吸收会员、节日、优惠券和临时需求，最终形成条件分支火山。

- 主要异味：嵌套判断、魔法值、字符串类型系统
- 行为合同：`equal-output`
- SMI：**73**，铲屎车进入一级战备
- 主要计分来源：魔法数字 20 / 决策点 18 / 嵌套深度 12
- 展区状态：活跃喷发

#### `002` · [One Class to Rule Them All](../exhibits/java/002-one-class-to-rule-them-all/)

一个订单入口兼并库存、定价、支付、通知和审计，最终建立只有一个王座的职责帝国。

- 主要异味：God Object、共享状态、职责兼并
- 行为合同：`equal-output`
- SMI：**100**，建议原地成立事故调查组
- 主要计分来源：决策点 24 / 魔法数字 20 / 全局可变状态 18
- 展区状态：王座失控

### Python

#### `003` · [Mutable Default Argument Swamp](../exhibits/python/003-mutable-default-swamp/)

可变默认参数把前一次调用的状态带进下一次调用，形成看不见的共享沼泽。

- 主要异味：可变默认参数、跨调用状态污染、隐式共享状态
- 行为合同：`expected-difference`
- SMI：**32**，建议佩戴防护设备
- 主要计分来源：可变默认参数 30 / 决策点 2
- 展区状态：沼泽扩散

## 维护方式

新增正式展品时，只需在 `exhibit.json` 中维护 `catalog` 元数据，并执行：

```bash
python3 scripts/catalog.py --write
python3 scripts/smi.py --write
```

README 只展示固定数量的高风险展品，因此展品增长不会继续拉长项目首页。
