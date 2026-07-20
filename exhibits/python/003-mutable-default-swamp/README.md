# 003：Mutable Default Argument Swamp

## 沼泽入口

这个展品展示 Python 中最容易被低估的状态泄漏之一：把可变对象写进函数默认参数。

```python
def collect_task(task, tasks=[]):
    tasks.append(task)
    return tasks
```

调用者通常把 `tasks=[]` 理解为“每次调用都创建一个空列表”。实际情况是：**默认参数表达式在函数定义时求值一次，而不是在每次调用时重新求值。** 因此，同一个列表会被后续所有未显式传参的调用重复使用。

## 前一位游客留下的脚印

坏版连续执行两次：

```text
first=inspect-volcano|second=inspect-volcano,repair-bridge|contaminated=yes
```

第二位游客只提交了 `repair-bridge`，却继承了第一位游客的 `inspect-volcano`。这不是缓存功能，而是没有写在接口契约里的隐式共享状态。

## 主要罪名

1. **状态生命周期与调用生命周期不一致**
   列表在函数定义时创建，生命周期接近模块，而调用者通常预期它只活一次调用。
2. **接口制造错误直觉**
   参数看起来可选，实际却悄悄把不同调用者连接到同一容器。
3. **测试顺序污染**
   单个测试独立运行可能通过；整套测试按不同顺序运行时，历史调用会改变结果。
4. **并发与长期进程风险**
   Web 服务、任务进程和 notebook 会长期保留函数对象，使污染不断沉积。

## 沼泽为什么会形成

这类代码通常来自一个合理愿望：省掉 `None` 检查，让调用方式更短。问题不是列表本身，而是把“是否共享状态”的决策隐藏在函数定义细节中。

## 排水工程

修复版使用不可变哨兵值：

```python
def collect_task(task, tasks=None):
    current_tasks = [] if tasks is None else tasks
    current_tasks.append(task)
    return current_tasks
```

修复后输出：

```text
first=inspect-volcano|second=repair-bridge|isolated=yes
```

如果业务确实需要共享列表，调用者必须显式创建并传入同一个容器。这样共享状态从语言陷阱变成可见的接口选择。

## 取舍

- `None` 哨兵多了一行初始化代码，但明确了对象创建时机。
- 修复不要求把所有可变参数都禁止；它只要求共享行为必须显式。
- 返回副本可以减少调用者意外修改内部列表的机会，但大型数据结构可能需要重新评估复制成本。

## 运行

```bash
python3 exhibits/python/003-mutable-default-swamp/bad/mutable_default_swamp.py
python3 exhibits/python/003-mutable-default-swamp/fixed/mutable_default_swamp.py
```

完整安检：

```bash
bash scripts/validate.sh
```

## 屎山指数

SMI v2 的 Python 适配器使用 AST 识别语言专用异味，本展品得分为 **32 / 100**：

- 可变默认参数：`30`
- 决策点：`2`

主因权重较高，因为它会制造跨请求、跨测试和跨任务的隐式共享状态。评分不复用 Java 正则，也不把入口处的 `if __name__ == "__main__"` 计入复杂度。
