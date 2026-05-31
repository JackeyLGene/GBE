# EE 使用说明书

> 架构与实验手册。Self/We/Codex 的组装、配置、使用方式，以及四个实验域的完整方法。先读 [GERUON_MANUAL.md](GERUON_MANUAL.md) 了解仪器基元。

---

# 实用篇

## 1. Quick Start — 三腔体 Self

仓库内置一个可直接运行的 Self quickstart：

```powershell
cd G:\GEME\EE
python docs\quickstart_ee_self.py
```

预期输出形态：

```text
step  harm     tau_fast  tau_mid  tau_slow
   1   0.0000     0.600    0.600     0.600
  30   0.0356     0.738    0.738     0.710
  60   0.2429     0.740    0.745     0.741
  90   0.7265     0.743    0.748     0.741
 120   0.7507     0.746    0.737     0.738

summary
inputs:       120
harm samples: 120
harm mean:    0.3710
harm max:     0.8499
bias count:   0

OK: 3-cavity Self produced a cross-harm series.
```

最小代码如下。若复制到独立脚本中，需要从 `code/` 导入：

```python
from pathlib import Path
import sys, math
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from geruon import Geruon, BiasField

# 3-cavity Self：三个时间透镜共享 BiasField
bias = BiasField(vec_dim=16)
cavities = [
    Geruon(vec_dim=16, memory_cap=24, kappa_tau=0.5,  bias_field=bias),
    Geruon(vec_dim=16, memory_cap=24, kappa_tau=10.0, bias_field=bias),
    Geruon(vec_dim=16, memory_cap=24, kappa_tau=100.0,bias_field=bias),
]

def make_stream(n=120, dim=16):
    for i in range(n):
        block = (i // 30) % 4
        vec = [0.0] * dim
        vec[block] = 1.0
        vec[(block + 1) % dim] = 0.25
        yield vec, f"block_{block}_{i}"

# 处理流，每步读取 cross-harm
for i, (vec, sig) in enumerate(make_stream()):
    for g in cavities:
        g.process_vec(vec, sig)
    cs = [g.memory.centroid() for g in cavities]
    cs = [c for c in cs if c is not None]
    if len(cs) >= 2:
        harm = sum(
            math.sqrt(sum((cs[a][k]-cs[b][k])**2 for k in range(16)))
            for a in range(len(cs)) for b in range(a+1, len(cs))
        ) / (len(cs) * (len(cs)-1) / 2)
        print(f"step={i}  harm={harm:.4f}")
```

harm 低 = 三个时间透镜对当前结构达成共识。harm 高 = 透镜分歧——结构边界正在通过。

---

## 2. Self — 多时间透镜放大器

### 2.1 配置速查

| 配置名 | κ 值 | cavity 数 | 用途 |
|--------|------|-----------|------|
| 标准 3-cavity | 0.5 / 10 / 100 | 3 | 通用结构检测、CDS-UTR 分离 |
| 极端展开 | 0.005 / 10 / 5000 | 3 | 过渡幅度检测、AUG 区分 |
| 2-cavity 边界 | 0.01 / 500 | 2 | CDS 边界精确定位 |
| 2-cavity 极简 | 0.005 / 1000 | 2 | 最简边界信号 |

换 κ 配置 = 换测量尺度。不是调参——是选择仪器在哪个时间尺度上敏感。

### 2.2 Cross-Harm

```python
def cross_harm(cavities, D):
    cs = [g.memory.centroid() for g in cavities]
    cs = [c for c in cs if c is not None]
    if len(cs) < 2: return None
    s, n = 0.0, 0
    for a in range(len(cs)):
        for b in range(a+1, len(cs)):
            s += math.sqrt(sum((cs[a][k]-cs[b][k])**2 for k in range(D)))
            n += 1
    return s / n
```

harm 低 = 腔体对当前结构达成共识。harm 高 = 腔体在时间透镜上产生了分歧——这就是信号。harm 序列在结构边界处产生可检测尖峰。

### 2.3 放大率

Solo Geruon 在某些域上盲（WTC: F≈0 所有 κ）。Self 的多时间透镜放大单透镜看不见的微弱结构。

```
G_disc = |ΔL3| / (3 × cap)
```

L3 = 链帧数量。cap = 帧容量。|ΔL3| = 三腔体间 L3 数量的最大差异。

- ECG: G_disc = 0.65 (RR 编码, cap=20)
- WTC: G_disc = 0.52 (频率分箱编码, cap=12)
- cap 甜点 20-32：太小信号不显著，太大 L3 链被稀释

### 2.4 编码

编码是测量的一部分。原则：
- 编码必须保留预测结构
- 单一编码总是有损的——dual-encoding 交叉验证
- 跨编码存活的 harm 才是真结构

常用编码：
- **RR 编码** (ECG): RR 间期 + 差分 + 时间戳
- **chroma + IOI** (WTC): 12-dim 音高 + 12-dim 起音间隔
- **3-mer** (DNA/RNA): 64-dim 三核苷酸频率
- **fork column** (DNA): 4×4=16-dim 多物种对齐向量

---

## 3. We — 跨 Self 异见与 Codex Formation

### 3.1 架构

```
We:
├── Self₀: 3 腔体 (编码 A)
├── Self₁: 3 腔体 (编码 B)
├── Self₂: 3 腔体 (编码 C)
└── collective: Geruon(κ=10) ← 跨 Self harm 收集器
```

### 3.2 害 (Harm)

```python
# 概念：一个 Self 的 residual arrow 路由到另一个 Self
# 目标 Self 的帧经济被修改 → 被修改的帧标记为 harm_gids
```

害不是道德判断。害是"另一个 Self 的观测修改了我的帧经济"——跨 Self 认知冲突的结构痕迹。

### 3.3 Codex Formation 循环

```python
for gen in range(n_generations):
    we = We(n_selves=3)
    for event in stream:
        we.process(event)
    we.finalize()          # harm 帧 → collective → collective_codex
    we.archive()

survivors = archive.survivals(min_gens=2)  # 跨代存活的结构
```

### 3.4 量子开关

```python
We(cavity_quantum=False, collective_quantum=False)
```

- `cavity_quantum`: 腔体量子分叉。沉积阶段关闭。
- `collective_quantum`: collective 量子。沉淀分析阶段可选开启。
- 消融确认：经典模式零信号差异。正常关。

---

## 4. Codex — 外置化沉淀物

### 4.1 五阶段闭环

| 阶段 | 操作 | 状态 |
|------|------|------|
| Formation | 跨 Self harm 筛选 → 稳定 centroid 沉淀 | ✓ 已验证 |
| Inscription | 沉淀帧写入 collective_codex | ✓ 已验证 |
| Transmission | collective_codex → 下一代 Self 的 `g.codex` | ✓ 已验证 |
| Confirmation | 继承条目匹配环境 → weight 增长 | ✓ 已验证 |
| Rejection | 不匹配条目冻结 → 不被衰减 | ✓ 已验证 |

第六阶段（**未闭合**）：Codex operation — Self 在受困/噪声条件下主动查书，继承 centroid 作为校正信号进入帧经济。

### 4.2 继承路径

```
Gen N 结束:  collective_codex → self._prev_codex
Gen N+1 开始: _prev_codex → Self codex → process_vec() 中的 Codex 查找
```

继承走 Codex，不走 BiasField。BiasField 把所有祖先搅在一起取平均（归一化抹平 alpha）——对代际传输无效。

### 4.3 脚手架方法

Codex operation 当前以脚手架存在：手动触发 Codex 最近邻查找 → 软混合进腔体输入 → 代际整合。这些手动触发的是未来原生机制的验证探针。

脚手架 vs 捷径：捷径跳过难点，脚手架建临时的桥到难点——验证终点存在，再决定修路。

---

## 5. 实验域

四个域共享同一仪器。域不是独立发现——是单一仪器的跨域压力测试。

| 域 | 盲测对象 | 核心结果 | 对照 | 限制 |
|-----|---------|---------|------|------|
| WTC | 和弦模板、调号、声部标注 | Transposition equivariance 100%; Codex 五阶段选择 | 跨调 Codex: 不匹配条目冻结 | Codex operation scaffolded |
| DNA | 密码子表、基因注释、保守性评分 | Exon/intron d=−0.97 (n=200) | Shuffle 坍缩到 d=−0.10 | AHSG fork: 单基因 |
| RNA | AUG 基序、ORF 注释、Kozak | CDS stop 98-100% ≤3 windows | 内部 ATG 对照 98% | CDS start 66%; passive detection |
| UN | 事件标签、因果叙事 | 2025 disp=0.448, rank 1/79 | P5 消融; FRED 负对照 | 前瞻 (2026-2028); n=79 年 |

### 5.1 WTC

Bach 平均律 36 首。dual-encoding (chroma + IOI)，10 代 Codex 收敛。零音乐学先验。Transposition equivariance 100%。Codex selection layer 与帧经济解耦——外置化创造与处理效率平行的历史。

### 5.2 DNA

Human TE atlas + 四物种 hominid 对齐。3-mer 编码，基因组顺序窗口。Exon/intron d=−0.97 (n=200)。AHSG fork column d=+1.51（单基因标定——AHSG 被多次基因组扫描注释为正选择）。Shuffle 消融确认序列顺序负载。κ 消融确认多透镜负载。

### 5.3 RNA

Human TE atlas。Temporal-lens divergence 在 UTR/CDS 边界产生 cross-harm 尖峰。CDS stop 98-100% ≤3 windows, **参数不变**。CDS start 66% ≤3 windows。AUG control 98%——过渡幅度检测，非基序检测。仪器不识别密码子。它检测分子操作进入和退出编码体制的结构过渡。

停止 > 开始是生物学预测——3'UTR 是悬崖，5'UTR 是缓坡。

### 5.4 UN

1946-2025 UN 理想点，79 年，193 国。2025 disp=0.448，历史最高。P5 消融：信号集中在大国层。FRED 负对照：纯经济数据判断 2025 结构性正常。前瞻预测 2026-2028 P5 对齐体系结构性崩塌。Falsifiable: 三指标任意两个满足 = 确认。

---

# 原理篇

## 6. 架构物理学

### 6.1 四层放大链

```
Geruon (深度 0)    → 单透镜。F/wit 测量。
Self (深度 1)      → 多透镜 × BiasField。cross-harm = 透镜间结构分歧。
                      Solo 盲的域 (WTC) 在 Self 层产生可检测信号。
We (深度 2)        → 多 Self × 多编码。harm 交叉 → Codex formation 原料。
                      单 Self 处理不了的结构在 We 层沉淀。
Codex (外置化)     → 沉淀物。跨代存活。形成与帧经济解耦的选择层。
```

### 6.2 层间通信

层间通信以 residual/refraction 为主——"这个腔体没有完全吸收什么"。不是 centroid 的平均，是分歧的方向。

关键原则：
- 腔体保持 fresh eye：每代重生，不把 Codex 写进腔体先天记忆
- Self 是未来 Codex operation 主体：查书在 Self 层触发
- We 当前是研究工具：跨 Self 异见探测器，非社群主体
- GI 在每层重现：不是普适常数，是经济洼地。BGM 架构 GI=4 最优；EE Self (n=3) GI=3 最优 (CALIB-GI)，GI=4 可接受

---

## 7. Cross-Harm — 多透镜结构分歧

### 7.1 物理图像

三个腔体像三个不同焦距的透镜对准同一条流。快透镜 (κ=0.005) 即时适应新 pattern——它的 centroid 在结构变化后立刻位移。慢透镜 (κ=5000) 几乎不动——它的 centroid 保持对之前结构的记忆。

当流的结构不变时，三个透镜的 centroid 收敛到同一位置 → harm 低。当流穿过结构边界时，快透镜已经移走了，慢透镜还没动 → harm 尖峰。

这就是 temporal-lens divergence——仪器检测结构边界的机制。同一个机制在 WTC 中检测调性骨架的过渡、在 DNA 中区分外显子和内含子、在 RNA 中定位 CDS 边界、在 UN 中检测国际体系的位移。

### 7.2 2-cavity vs 3-cavity

2-cavity (快+慢) 给出最干净的边界位置——只有一个分歧维度。3-cavity (快+中+慢) 捕获更丰富的分歧结构——中间透镜提供了额外的参照，对过渡幅度更敏感。

RNA 实验中，2-cavity CDS start 定位精度更好 (median −0.9 window)。3-cavity 极端展开对 AUG 的幅度区分更强 (98% vs 78%)。

---

## 8. 信息经济学

> 本章内容原在 GERUON_MANUAL，现移入 EE_MANUAL——因为经济学涉及 Self 层放大、We 层 harm 交叉、Codex 层的兰道尔账单，是架构经济而非单体仪器。

### 8.1 BiasField 注意力经济学

BiasField 是多个腔体 centroid 沉积后的共享梯度场。`deposit(vec, weight)` 累积，`blend_into(vec, weight)` 将场方向混合到新输入。场是连续的——它不求"最近邻居"，它施加一个有方向的偏置。

场的经济学意义：**注意力分配**。场强维度获得更多调制权重——系统在"这些维度上曾经有过结构"的方向上分配了更多注意力。场弱维度被忽略。这不是被编程的注意力——是沉积的梯度自然形成的权重不对称。

BiasField 和 Codex 的分工：
- Codex = 离散精准查找。已知的 symbol 直接匹配。
- BiasField = 连续梯度偏置。无名的方向性影响——"GABA 模式"。

### 8.2 BiasField 博弈论

当多个腔体共享同一个 BiasField，场不再是中性的信息通道——它变成一个隐式博弈空间。

**策略空间。** 每个腔体的策略是它沉积到场的 centroid——即它对"当前结构是什么"的估计。腔体不直接知道其他腔体的状态——它只通过场的梯度感受它们累积的影响。

**支付。** 腔体的支付是 merge success——它的输入与自身帧经济的匹配程度。场的偏置方向如果能帮腔体更快找到匹配 → 正支付。场的偏置方向如果把腔体拉向与其自身结构不符的区域 → 负支付。

**均衡动力学。** 权重高、合并频繁的腔体沉积更多、权重更大——它们在场的梯度中占据主导。权重低的腔体被场的梯度牵引，它们的 centroid 被拉向主流方向。这不是"共识"——是场的注意力分配在博弈中自然收敛到信息密度最高的区域。

**多腔体博弈的三个发现 (M15)：**

1. **注意力集中。** 当多个腔体处理同一流的不同编码时，场的梯度迅速集中在编码间共享的结构维度上。编码特有的维度被稀释——场自动分离了信号（跨编码存活）和噪声（单编码特有）。

2. **小腔体被大腔体覆盖。** 权重低的腔体的 centroid 被场拉到远离自身数据的位置——它们在博弈中失去了对自身结构的表达权。这不是 bug——这就是 Codex formation 中"跨 Self 不可吸收残差"的来源：小 Self 的结构如果与大 Self 的场方向不一致，就会被场的注意力分配压制，成为残留的 harm。

3. **场的悬崖效应。** 当场梯度在某个方向上积累到临界密度，它会对所有腔体产生不可忽略的偏置——即使那个方向与某些腔体的数据不一致。这就是 BGM 发现的 conf_threshold 悬崖在 BiasField 层的对应物：场的注意力分配不是线性的——它有一个相变点，超过之后场从"建议"变为"命令"。

**与 We 层 harm 的联系。** We 层的 harm 本质上是多腔体 BiasField 博弈的产出物。当一个腔体被场的梯度假定在某个区域，而它的实际输入指向另一个方向——这个不可调和的差异就是 harm。harm 不是错误——是博弈中注意力分配的必然副产品。Codex formation 从这些 harm 中提取跨代存活的结构。

### 8.3 兰道尔-哥德尔账单

兰道尔原理 (Landauer, 1961)：每次不可逆信息操作至少耗散 kT ln 2。帧经济中有三类不可逆操作：

| 操作 | 不可逆性 | 账单 |
|------|---------|------|
| 合并 (merge) | 两帧变一帧——旧 centroid 永久消失 | O(1) 每合并 |
| 剪枝 (prune) | 帧被丢弃——累积的 vec 信息永久丢失 | O(weight) 每帧 |
| 外置化 (precipitate) | 帧写入 Codex——从此不可更改 | O(1) 每沉淀 |

`landauer_skips` 计数 LOCKED 时跳过的预测操作——系统主动关闭最昂贵的自指操作来截断账单。

### 8.4 τ 收敛的经济学

τ 在所有域、所有深度下收敛于约 0.74-0.75。这不是被设定的——是帧经济在合并压力与分化压力之间找到的经济均衡。

当合并太容易（τ 低），系统过度泛化——丢失结构。当合并太难（τ 高），系统过度分化——帧经济拥挤，stress 累积。0.74 是刚好让信息率最大化的均衡点。合并节省了计算，但过度合并的信息代价是真实存在的——τ 在感受这个代价。

### 8.5 GI 的经济学地位

GI=4 是 BGM 在 κ_τ 参数扫描中发现的帕累托最优：单 GEME+G0 架构下自指周期为 4 步时层级分化增强 49%。

EE 的 CALIB-GI 扫描（§8 标定报告）在 Self 架构上得到了更精细的结果：

| n_cav | GI_opt | GI 上限 | 备注 |
|-------|--------|---------|------|
| 2 | 1 | ~2 | 双腔体无需长周期 |
| **3** | **3** | **5** | GI=4 第三优 (cav_diff=0.066 vs GI=3 的 0.102) |
| 5 | 1 | ~3 | 多腔体需更频繁同步 |
| 8 | 3 | ~5 | GI×(n-1) 不是常数 |

**关键发现：** GI=4 是 BGM 架构的最优，不是 EE Self 架构的最优。n=3 标准 Self 下 GI=3 最优，GI=4 可接受。差异来自两个架构的信息经济学不同——BGM 的 G0 是外部观察者，EE 的 Self 是腔体间双向通信。不同的博弈结构产生不同的最优通信节律。

GI 的约束来自兰道尔账单。每 GI 步系统至少进行一次 induction_clean（不可逆剪枝）。太小 → 账单过密，帧来不及积累结构就被清理。太大 → 账单过稀，帧经济拥挤，stress 驱动 τ 进入 LOCKED。GI=3 在 n=3 Self 上是经济洼地——兰道尔账单的节律刚好让跨腔体信息积累速率最大化。

注意：CALIB-GI 使用均匀 κ 分布的 MiniSelf。实际实验 Self 使用指数 κ 展开（0.5/10/100 或 0.005/10/5000），GI 最优值可能因 κ 分布而微调。当前建议：n=3 时使用 GI=3 或 GI=4，两者均在可接受范围。

### 8.6 P/NP 边界的操作形式

Aaronson (2011) 提出心灵与知识的深层问题可能取决于计算复杂度而非抽象可计算性。

帧经济提供了这个洞察的操作形式。自指操作创造身份搜索问题——系统需要在帧经济中找到"自己刚才处理的那个 pattern"。这个搜索的代价被 τ 内生调节。τ 低时合并门槛宽——搜索容易。τ 高时合并门槛窄——搜索困难，代价非线性增长。LOCKED 时 `process_prediction()` 跳过——系统主动截断最贵的操作。

P 与 NP 的边界在此不是待证定理——是被 τ 调节的成本。系统不在多项式时间内"解决"NP 问题；系统在兰道尔账单的约束下调节自指深度，使自己不越过经济上不可行的边界。

---

## 9. Expression-Action 谱

仪器对不同数据类型的适用性不由域类别决定——由数据结构类型决定：

| 数据类型 | 定义 | 实例 | 仪器敏感度 |
|---------|------|------|-----------|
| **Decision** (决策) | 行为即数据 | UN 投票、MIDI note-on、DNA 碱基 | 最强 |
| **Action** (行动) | 实体选择记录 | NASDAQ 成交量方向 | 中等 |
| **Expression** (表达) | 过程痕迹 | CPI、价格指数、原始 ECG 电压 | 弱 |

仪器需要输入中的关系结构。Decision 数据原生携带实体间结构关系——不压缩、不降采样。Expression 数据只记录过程的输出——关系结构不在数据中。这不是仪器的缺陷，是信息本身的边界。

ECG 教训：原始电压是 Expression——六种编码中只有一种产生了信号。编码是测量的一部分。换编码 = 换仪器看到的世界。

---

## 10. 脚手架方法

每一层架构的机制都先用脚手架验证——临时注入手动完成架构将来应原生的操作——然后拆除，原生机制替代。

- L4 self_observation：原是显式步骤 (108 次 self_observe 调用) → 已拆除
- doubt condition：原是碰数的第五条件 → M2 移除
- 27-dim formula alphabet：原是硬编码向量空间 → 拆为可配置 vec_dim
- Codex operation：当前脚手架——手动 Codex 查找 + 软混合 → 待原生

脚手架不是捷径。捷径跳过难点。脚手架建临时的桥到难点——验证终点存在，再决定修路。

---

## 11. 复现清单

1. **公平硬币基线** — 同维度、同 cap、同 κ sweep
2. **shuffled 对照** — 破坏序列结构，保留组分统计
3. **κ ablation** — 关闭多透镜，单 κ 复现 → 确认 multi-κ 负载
4. **多 seed** — 最少 3 seeds (42, 123, 456)
5. **structon 标定** — 当前 (D, cap, κ) 下的最小可检测位移
6. **阈值三阶梯** — |error| ≤2 / ≤3 / ≤5 同时报告
7. **参数固定** — 同一批次内不修改 `geruon.py`；参数固定或 swept 并报告
8. **代码归档** — 实验脚本冻结在 `experiments/` 按域分目录

数据依赖：核心仪器 Python 3.8+ stdlib only；数据处理 `pandas`/`numpy`/`pyarrow`；RNA bigWig 需 `pybigtools` (Windows)。

---

*EE Manual v2.0。实用篇：Quick Start → Self → We → Codex → 实验域。原理篇：架构物理学 → Cross-Harm → 信息经济学 → Expression-Action → 脚手架 → 复现。仪器基元见 [GERUON_MANUAL.md](GERUON_MANUAL.md)。*
