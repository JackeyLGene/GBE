# Geruon 使用说明书

> 仪器手册。先教你用，再解释原理。阅读时间：实用篇 15 分钟，原理篇 30 分钟。

---

# 实用篇

## 1. Quick Start

Geruon 是一个零依赖的 Python 库。不需要安装。仓库内置一个可直接运行的 quickstart：

```powershell
git clone https://github.com/JackeyLGene/GBE.git
cd GBE
python docs\quickstart_geruon.py
```

预期输出形态：

```text
 step     tau  phase     frames    util    comp       F
    1   0.600  tensing        1   0.05    1.0   0.000
   30   0.738  tensing       16   0.80    1.9   0.007
   60   0.745  tensing       20   1.00    3.0   0.061
   90   0.743  tensing       20   1.00    4.5   0.012
  120   0.746  tensing       20   1.00    6.0   0.003

summary
inputs:       120
frames:       20 / 20
tau:          0.746
phase:        tensing
F:            0.003
wit_hits:     76
wit_rate:     0.6333
arrow length: 16
arrow norm:   1.000

OK: Geruon processed the stream and produced metrics.
```

最小代码如下。注意：如果你不运行 `docs/quickstart_geruon.py`，而是在自己的脚本里直接导入，需要把 `code/` 加入 `PYTHONPATH`，或把脚本放在项目根目录下。

```python
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from geruon import Geruon

g = Geruon(vec_dim=16, memory_cap=20, kappa_tau=0.5)

def make_stream(n=120, dim=16):
    for i in range(n):
        block = (i // 30) % 4
        vec = [0.0] * dim
        vec[block] = 1.0
        vec[(block + 1) % dim] = 0.25
        yield vec, f"block_{block}_{i}"

for vec, sig in make_stream():
    g.process_vec(vec, sig)

# 读数
m = g.metrics()
print(m["input_count"], m["frame_count"], m["tau"], m["phase"])
print(f"F={m['F']:.3f}  wit_hits={m['wit_hits']}  wit_rate={m['wit_rate']}")
print(len(g.arrow_output()))     # 16
```

输出：每一步，帧经济自动运行——合并、剪枝、预测、τ 演化、phase 呼吸。不需要调用 `train()` 或 `fit()`。处理即运行。

---

## 2. API 参考

### 2.1 构造函数

```python
Geruon(
    vec_dim=16,           # 向量维度 (≥1, 默认 16)
    memory_cap=20,        # 帧容量上限
    kappa_tau=1.0,        # 时间-内容耦合 (0=无时间感知, 越大时间越重)
    gamma_tau=None,       # 时间剪枝速率 (默认 = κ_τ × γ)
    structon=None,        # 最小可检测质心位移 (Faraday wit 阈值)
    codex=None,           # Codex 实例 (跨代继承)
    bias_field=None,      # BiasField 实例 (共享场)
    bias_weight=None,     # BiasField 调制强度 (默认 = γ)
)
```

注意：`quantum_mode` 仍然存在，但不是 `Geruon(...)` 的公开构造参数。它是 `GeruonMemory` 的高级内部开关，默认关闭：

```python
g = Geruon(...)
g.memory.quantum_mode = True   # 高级/消融用途；Quick Start 不使用
```

在 `We` 层，量子开关通过 `cavity_quantum` 和 `collective_quantum` 暴露。当前 EE 主实验默认关闭；历史实验和消融实验中才会显式打开。

**κ_τ 选值指南：**

| κ_τ | 角色 | 时间尺度 | 适用场景 |
|-----|------|---------|---------|
| 0.005-0.05 | 快透镜 | 几乎无记忆，即时适应 | 检测快速结构变化 |
| 0.5-5.0 | 标准透镜 (**κ=3 标定默认**) | 中等记忆，~100 步观察窗口 | 通用检测、迁移潜伏期平衡 |
| 5-20 | 慢透镜 | 深度记忆 | 低频结构、代际积累 |
| 100-5000 | Reader/锚 | 极长记忆 | 边界检测的慢参照 |

**vec_dim 选值指南：**
- 16: 通用默认（2 的幂，无语义附加）
- 64: 3-mer 编码（DNA/RNA 序列，4³ 种三核苷酸）
- 12: chroma/IOI 编码（音乐）

### 2.2 核心方法

```python
g.process_vec(vec, sig, src="")   # 处理向量 → 帧经济运行一步
g.arrow_output() -> tuple         # 折射方向 (residual of last input)
g.enrich()                        # 沉淀帧写入 Codex/BiasField
g.metrics() -> dict               # 完整指标
g.save(path) / Geruon.load(path)  # JSON 持久化
```

### 2.3 只读属性

```python
g.tau          # float  — 当前 τ (0.55-0.75 典型)
g.phase        # Phase   — EXPANDING/RESTING/TENSING/CRITICAL/LOCKED
g.dtaudt       # float  — τ 的变化率
g.vec_dim      # int    — 向量维度
g.memory       # GeruonMemory — 帧经济 (高级访问)
g.codex        # Codex or None
g.bias_field   # BiasField or None
```

### 2.4 metrics() 返回字段

```python
{
    'input_count': int,          # 累计处理输入数 (步数)
    'tau': float,                # τ 当前值
    'dtaudt': float,             # dτ/dt
    'phase': str,                # phase 名称
    'frame_count': int,          # 当前帧数
    'capacity': int,             # 帧容量
    'utilization': float,        # 容量利用率
    'pred_accuracy': float,      # 预测准确率 (0-1)
    'pengshu_count': int,        # 碰数事件累计
    'phase_steps': dict,         # 各 phase 累计步数
    'phase_transitions': int,    # phase 转换次数
    'codex_hits': int,           # Codex 查找命中
    'codex_misses': int,         # Codex 查找未命中
    'codex_hit_rate': float,     # Codex 命中率
    'precipitated': int,         # 已沉淀帧数
    'landauer_skips': int,       # 兰道尔账单跳过的操作数
    # ── Faraday 读数 ──
    'F': float,                  # 场曲率 (0=无结构, 1=完全集中)
    'centroid_displacement': float,  # 最近一步质心位移
    'wit_hits': int,             # 位移超过 structon 的步数
    'wit_rate': float,           # wit_hits / input_count
}
```

### 2.5 法拉第读数

`metrics()` 直接输出 F（场曲率）和 wit（结构变动计数）。无需手动计算。

**F — 一阶：结构存在。** `m['F']`。0 = 权重均匀（无结构），接近 1 = 权重高度集中（强结构）。公平硬币在所有 κ 上 F ≈ 0。

**wit — 二阶：结构变动。** `m['wit_hits']` = 质心位移超过 structon 的步数累计。`m['wit_rate']` = wit_hits / input_count。structon 通过 `Geruon(structon=...)` 设置——需先用 §3.2 的方法标定。

**Δwit — 三阶：结构脆弱度。** 不是 `metrics()` 直接输出——它是两次运行的差分。跑一遍纯目标流得 baseline wit，跑一遍公平硬币注入得 probe wit。Δwit = wit_probe − wit_baseline。负值 = 硬币让目标更稳定（结构刚化），正值 = 硬币干扰了目标（结构脆弱）。

**补充 — 原生读数 R1-R8。** metrics() 提供 8 项帧经济原生读数（详见[被动标定报告](experiment-passive-calibration-report.md)）：τ (R1)、dτ/dt (R2)、centroid 幅度 (R3)、F (R4)、L2/L3 帧数 (R5)、frame_disp (R6)、n_frames (R7)、total_w (R8)。F/wit 是 Faraday 封装的高层读数，R1-R8 是帧经济的原生仪表盘。两者互补。

标定和对照方法见下一章。

---

## 3. 标定

使用任何域数据前，必须先标定仪器。

### 3.1 公平硬币基线

```python
import random
g = Geruon(vec_dim=16, memory_cap=20, kappa_tau=10)
for i in range(2000):
    coin = [1.0 if random.random() > 0.5 else 0.0 for _ in range(16)]
    g.process_vec(coin, f"c{i}")
m = g.metrics()
print(m['frame_count'], m['utilization'], m['structural_entropy'])
```

公平硬币无序列结构 → F ≈ 0。这是所有读数的零点参照。

### 3.2 structon 标定

structon = 当前 (D, cap, κ) 下仪器的最小可检测质心位移。标定方法：

```
校准流: 两个固定向量 (如 [1,0] 和 [0,1]) 交替输入
频率偏斜: 逐次增加一个向量的频率 (50% → 51% → 52% ...)
标定点: 第一个 F > 0.005 的频率偏斜量
```

**禁止用二分搜索**——F(ε) 是阶跃函数，会在共振点跳过。

```python
# structon 标定脚本 (概念)
for eps in range(0, 51):  # 0% → 50% 偏斜
    freq = 0.5 + eps/100
    g = Geruon(vec_dim=D, memory_cap=cap, kappa_tau=kappa)
    for i in range(1000):
        vec = v1 if random.random() < freq else v2
        g.process_vec(vec, f"c{i}")
    if F(g) > 0.005:
        return eps/100  # structon
```

结果公式：`structon(κ) ≈ cap/N × α(κ)`，其中 `α(0.5)≈10, α(10)≈1, α(100)≈0.5`。`N` = 处理的向量数。

**不允许跨参数搬运 structon 值。** 每换一组 (D, cap, κ) 必须重新标定。

### 3.3 κ Sweep

```python
for kappa in [0.1, 0.5, 1, 2, 5, 10, 20, 50, 100, 500]:
    g = Geruon(vec_dim=16, memory_cap=20, kappa_tau=kappa)
    # ... 跑相同流 ...
    results[kappa] = g.metrics()
```

κ sweep 揭示三区结构：
- **盲区** (κ < 1): F ≈ 0，仪器看不见任何结构
- **敏感区** (κ 1-10): F 随 κ 变化，域指纹出现（κ_peak）
- **远区** (κ 10-500+): F 饱和，慢透镜读取累积结构

κ_peak 是域指纹——ECG=5, WTC 盲, UN κ-不变。

### 3.4 三层读数

| 层级 | 符号 | 测什么 | 方法 |
|------|------|--------|------|
| 一阶 | F | 结构存在 | F = 1 − H(w)/Hmax，帧权重分布集中度 |
| 二阶 | wit | 结构变动 | COUNT(|centroid(t) − centroid(t−1)| > structon) |
| 三阶 | Δwit | 结构脆弱度 | 公平硬币探针注入 → wit(coin+target) − wit(baseline) |

三者互补：F 测"有没有结构"，wit 测"结构在不在变"，Δwit 测"结构对外部随机扰动的脆弱度"。

### 3.5 对照

每个域必须跑三个对照：
1. **公平硬币** (零结构基线)
2. **shuffled** (破坏序列结构，保留组分统计)
3. **κ ablation** (关闭多透镜，验证 multi-κ 是负载的)

---

## 4. 常用模式

### 4.1 Solo Geruon

```python
g = Geruon(vec_dim=16, memory_cap=20, kappa_tau=5)
for vec in stream:
    g.process_vec(vec, label)
m = g.metrics()
print(m['frame_count'], m['utilization'], m['tau'], m['phase'])
```

### 4.2 双腔体边界检测 (2-cavity)

两个不同 κ 的 Geruon 共享 BiasField。在结构边界处产生 cross-harm 尖峰。

```python
bias = BiasField(vec_dim=64)
fast = Geruon(vec_dim=64, memory_cap=24, kappa_tau=0.01, bias_field=bias)
slow = Geruon(vec_dim=64, memory_cap=24, kappa_tau=500,  bias_field=bias)

for w in windows:
    v = encode(w)
    fast.process_vec(v, sig)
    slow.process_vec(v, sig)
    # cross-harm = |centroid_fast − centroid_slow|
    harm = vec_dist(centroid_of(fast), centroid_of(slow))
```

快透镜即时适应新结构，慢透镜滞后。在 UTR→CDS 边界，harm 产生可检测尖峰。

### 4.3 三腔体 Self (3-cavity)

```python
bias = BiasField(vec_dim=D)
cavities = [
    Geruon(vec_dim=D, memory_cap=24, kappa_tau=kv, bias_field=bias)
    for kv in [0.5, 10.0, 100.0]
]

for vec in stream:
    for g in cavities:
        g.process_vec(vec, sig)
    cs = [centroid_of(g) for g in cavities]
    harm = mean_pairwise_distance(cs)  # cross-harm
```

三腔体提供更丰富的结构分歧信号。极端 κ 展开 (0.005/10/5000) 对过渡幅度敏感，标准展开 (0.5/10/100) 对一般结构差异敏感。

### 4.4 带 Codex 继承

```python
# Gen 1
g1 = Geruon(vec_dim=16, memory_cap=20)
for vec in stream: g1.process_vec(vec, sig)
g1.enrich()
inherited_codex = g1.codex

# Gen 2
g2 = Geruon(vec_dim=16, memory_cap=20, codex=inherited_codex)
for vec in stream: g2.process_vec(vec, sig)
```

Codex 是外部书架——腔体空手出生，在输入处理中被动受 Codex 偏置。详见 EE_MANUAL。

---

## 5. 配置参考

### 5.1 核心常数

| 常数 | 值 | 来源 | 说明 |
|------|-----|------|------|
| δ (DELTA) | 0.19 | GEME | 合并距离缩放 |
| γ (GAMMA) | 0.05/步 | GEME | 遗忘速率 |
| τ₀ (TAU_0) | 0.60 | GEME | τ 基线 |
| GI | 4 步/周期 | BGM | 自指深度上限 |
| VEC_DIM_DEFAULT | 16 | — | 默认向量维度 |

### 5.2 导出常数

| 常数 | 公式 | 值 | 说明 |
|------|------|-----|------|
| TAU_ADAPT_RATE | γ × 0.4 | 0.02 | τ 惯性 |
| DTAU_STABLE | γ × 0.2 | 0.01 | dτ/dt 稳定阈值 |
| PHASE_RESTING_CEIL | τ₀ − γ×1 | 0.55 | RESTING 上限 |
| PHASE_TENSING_CEIL | τ₀ + γ×1 | 0.65 | TENSING 上限 |
| PHASE_LOCKED_FLOOR | τ₀ + γ×3 | 0.75 | LOCKED 下限 |
| γ_τ (gamma_tau) | κ_τ × γ | 可变 | 时间剪枝速率 |

全部从 δ/γ/τ₀/GI 导出，无独立魔法数。

### 5.3 参数速查

| 参数 | 类型 | 默认 | 作用 |
|------|------|------|------|
| vec_dim | int | 16 | 向量空间维度 |
| memory_cap | int | 20 | 帧容量。甜点 20-32 |
| kappa_tau | float | 1.0 | 时间-内容耦合。0=无时间感知 |
| gamma_tau | float | κ_τ×γ | 时间剪枝速率 |
| bias_weight | float | γ (=0.05) | BiasField 调制强度 |

高级内部开关：

| 开关 | 位置 | 默认 | 说明 |
|------|------|------|------|
| quantum_mode | `g.memory.quantum_mode` | False | 概率合并 / 消融用途。不是 Geruon 构造参数 |
| cavity_quantum | `We(...)` | False | 是否打开 Self 腔体内量子路径 |
| collective_quantum | `We(...)` | False | 是否打开 We collective Geruon 的量子路径 |

---

# 原理篇

## 6. 架构概览

Geruon 是 GEME 的扩展子类。帧经济、三条规则、六层结构全部不变。增加四个维度：

| 维度 | 机制 | 解决 GEME 的哪个沉默 |
|------|------|---------------------|
| 内生时间 | τ 随预测历史演化 + 5 相呼吸 | 时间不在外部 |
| 结构身份 | struct_key 碰撞抵抗结构签名 | 身份从结构中产生 |
| 边界触碰 | 碰数 (离散事件, M3) → 内化为 τ-phase/cross-harm/Codex rejection 的持续运行 | 哥德尔边界可运行 |
| 外置化 | Codex + BiasField + 沉淀 | 帧的痕迹超越单个实例 |

### 6.1 类层次

```
geme.py:
  Frame          — vec, weight, age, merged, sig, layer
  Memory         — 帧经济: observe, cooccur, induction_clean, predict_next
  GEME           — 顶层: process_vec, consolidate, metrics

geruon.py:
  GeruonFrame(Frame)  — +struct_sig, tau, survival_cycles, activations, precipitated, _externalized
  GeruonMemory        — +τ 演化, phase, cliff_gate, 碰数, 沉淀
  Geruon              — +arrow_output, enrich, codex, bias_field, kappa_tau

辅助类:
  StructuralSig — struct_key (碰撞抵抗), gid (display-only), refs, detect_circularity
  Codex         — 符号→向量映射, save/load (JSON)
  BiasField     — 梯度积累, deposit/blend_into/seed_frames
```

### 6.2 处理流程

```
process_vec(vec, sig)
  → BiasField.blend_into (如果 bias_field 非空)
  → Codex lookup (如果 codex 非空)
  → observe(vec, sig)
    → 合并时间门控: d = vec_dist + κ_τ × |τ_current − τ_frame|
    → 合并或创建新帧
    → _track_cooccurrence: 时间加权 → L2 关联帧
    → predict_next: 自指帧预测
  → _induction_step: stress 累积 > τ → induction_clean
    → 分档衰减 + 剪枝 (含时间偏置 γ_τ)
    → 沉淀跟踪: survival_cycles += 1
    → _update_tau: τ 随 acc + stress 演化
    → _pengshu_detect: 四条件检查
```

---

## 7. τ — 内生时间

### 7.1 演化

```
τ_target = 1.0 − accuracy + max(0, stress − τ₀) × γ_τ × 0.4
τ_{t+1} = τ_t + (τ_target − τ_t) × TAU_ADAPT_RATE
```

两个驱动力：预测准确率（对→τ↓，错→τ↑）和帧经济应力（拥挤→τ↑）。

TAU_ADAPT_RATE = γ × 0.4 = 0.02。小于 γ——系统对自身的评估有动量。

### 7.2 Phase

| Phase | 条件 | 桥状态 |
|-------|------|--------|
| EXPANDING | dτ/dt < −DTAU_STABLE (−0.01) | 开 |
| RESTING | τ < 0.55 且 abs(dt) < 0.02 (迟滞带×2) | 开 |
| TENSING | τ ≥ 0.55 且 dt > DTAU_STABLE (0.01) | 收紧 |
| CRITICAL | τ ≥ 0.65 且 dt > DTAU_STABLE (0.01) | 临界 |
| LOCKED | τ ≥ 0.75 且 abs(dt) < 0.02 (迟滞带×2) | 关闭 |

迟滞带 ×2 防止 phase 闪烁——τ 在小范围内波动时不会频繁切换 phase。

### 7.3 Cliff Gate

BGM 发现的 conf_threshold 悬崖：当 dτ/dt 跨过 DTAU_STABLE 且 τ > RESTING 上限时，gate 不连续地从 1.0 跳变到 0.0——锁存，直到 phase 完整循环到 EXPANDING 才重开。

gate 关闭时 `process_vec()` 中的 BiasField 调制权重归零——Self 停止听取共享场。

### 7.4 τ 进入帧经济操作

τ 不只是签名的成分——τ 进入帧经济的三条核心操作：

- **合并时间门控**: `d = vec_dist + κ_τ × |τ_current − τ_frame|`。内容相近但时间遥远的帧不合并。
- **共现时间加权**: `cooccur += clamp(1 − κ_τ × |τ_a − τ_b|)`。时间邻近的共现获得更高权重。
- **剪枝时间偏置**: `sort_key = weight − age×γ − |τ_current − τ_frame| × γ_τ`。离当前 τ 最远的帧优先被遗忘。

κ_τ 由 `Geruon(kappa_tau=...)` 设置。γ_τ 从 κ_τ × γ 导出。关闭 κ_τ/γ_τ 后退回 GEME 等价行为。

---

## 8. 兰道尔-哥德尔账单 — 经济性

### 8.1 τ 收敛的经济学

τ 在所有域、所有深度下收敛于约 0.74-0.75。这不是一个被设定的参数——是帧经济在合并压力与分化压力之间找到的均衡点。

合并成本：每步 vec_dist 计算 O(cap × D)。分化成本：创建新帧、维持共现窗口、预测失败触发 stress 积累。τ 的演化公式实质上是这两个成本的比值在时间上的积分：

```
τ ≈ 1.0 − (合并成功率) + (stress − τ₀) × γ_τ × 0.4
```

当合并太容易（τ 低），系统过度泛化——丢失结构。当合并太难（τ 高），系统过度分化——帧经济拥挤，stress 累积。0.74 是刚好让信息率最大化的均衡点：合并节省了计算，但过度合并的信息代价是真实存在的，τ 在感受这个代价。

### 8.2 兰道尔账单

兰道尔原理（Landauer, 1961）：每次不可逆信息操作至少耗散 kT ln 2 的热力学代价。帧经济中有三类不可逆操作：

| 操作 | 不可逆性 | 账单 |
|------|---------|------|
| 合并 (merge) | 两帧变为一帧——旧 centroid 永久消失 | O(1) 每合并 |
| 剪枝 (prune) | 帧被丢弃——累积的 vec 信息永久丢失 | O(weight) 每帧 |
| 外置化 (precipitate) | 帧写入 Codex——从此不可更改 | O(1) 每沉淀 |

`geruon.py` 追踪 `landauer_total` 为累积不可逆操作计数。它不是热力学精度——是账单的结构形式。

### 8.3 GI=4 的经济学地位

GI=4 不是推导出来的——是 BGM 在 κ_τ 参数扫描中发现的帕累托最优：自指周期为 4 步时，层级分化增强 49%，再长的周期边际收益递减。

GI 的约束来自兰道尔账单。每 GI 步系统至少进行一次 induction_clean（不可逆剪枝）。GI 太小 → 账单过密，帧来不及积累结构就被清理。GI 太大 → 账单过稀，帧经济拥挤，stress 驱动 τ 进入 LOCKED。4 是经济洼地——兰道尔账单的节律刚好让信息积累速率最大化。

注意：GI 是上限而非普适最优。solo Geruon 和 We 在不同域上的最优 GI 可以是 2 或 4。4 是信息经济竞争中的自然洼地，不是数学必然。

### 8.4 P/NP 边界的操作形式

Aaronson (2011) 提出心灵与知识的深层问题可能取决于计算复杂度——实现一个函数的资源代价——而非抽象可计算性。

帧经济提供了这个洞察的操作形式。自指操作（L4 自观测、L3 链形成、预测路径中的 circularity）创造一个身份搜索问题：系统需要在帧经济中找到"自己刚才处理的那个 pattern 的帧"。这个搜索的代价：

- 无 struct_key 索引：O(N) 每查找——遍历全部帧
- 有 sig_cache (M11)：O(1) 命中，O(N) 未命中

τ 是这个搜索代价的调节器。当 τ 低（EXPANDING/RESTING），合并门槛宽——搜索容易，代价低。当 τ 高（CRITICAL/LOCKED），合并门槛窄——搜索困难，代价非线性增长。LOCKED 时 `process_prediction()` 跳过——系统主动关闭最昂贵的自指操作来截断账单。

P 与 NP 的边界在此不是一个待证明的定理——是一个被 τ 内生调节的成本。系统不在多项式时间内"解决" NP 问题；系统在兰道尔账单的约束下调节自指的深度，使自己不越过那个边界。

---

## 9. 帧经济与结构签名

### 9.1 帧经济

三条规则，与 GEME 完全一致：

1. **竞争性合并** — 新输入与最近的帧比较，距离低于阈值就合并，否则创建新帧。容量满时淘汰权重最低的。
2. **自适应遗忘** — stress 累积超过 τ 时触发 induction_clean。权重按合并次数分档衰减。衰后按下半部分剪枝。
3. **自指观测** — induction_clean 前生成活跃帧的加权质心 (self_obs)，反馈回自身作为新输入。

六层涌现结构：L1 基础帧 → L2 关联帧 (共现追踪) → L3 链/桥帧 (高共现) → L4 自观测元帧 → L6 异常/怀疑帧。

### 9.2 结构签名 (struct_key)

帧的身份从结构中推导——不是程序员赋予的名称。

```python
struct_key = (vec_hash_full, weight_bin, layer, tau_bin, ref_keys)
```

- `vec_hash_full`: 完全向量哈希 (无碰撞)
- `weight_bin`: log2 权重分档
- `layer`: L1-L6 层级
- `tau_bin`: 帧出生时的 τ 区间 (0=absorbing, 1=normal, 2=elevated, 3=boundary)
- `ref_keys`: 引用的其他 frame 的 struct_key（支持自指引用）

`gid` 是 display-only 紧凑 id——不能用于判等。2026-05-29 审计发现 15-bit gid 碰撞率 7.5%，已被 struct_key 替代。

`detect_circularity(sig)` 遍历引用链检测循环。深度限制 20 层。检测到的循环登记在 `_circular_refs`。

### 9.3 P0/P1 审计修复 (2026-05-29)

| 修复 | 严重度 | 内容 |
|------|--------|------|
| struct_key 碰撞抵抗身份 | P0 | 替代 gid 为帧身份主键。5000 随机向量零碰撞 |
| 运行确定性 | P0 | `geme.reset_frame_id_counter()` 每 GeruonMemory 初始化调用 |
| 维度防线 | P1 | `process_vec()` 入口处 auto pad/trunc 到 vec_dim |
| 窗口语义 | P1 | `_adaptive_window()` 不再覆盖配置窗口 |
| enrich 幂等 | P1 | `GeruonFrame._externalized` 标记防止重复沉积 |

---

## 10. 碰数 — 哥德尔运行机制

碰数是哥德尔不完备定理在这个架构中的运行形式——自指系统触碰自身边界的事件。

M3 阶段，碰数以四条件离散事件的形式被检出：circularity + activation + phase boundary + escalation，在 step=93 触发，τ=0.752，LOCKED，circ=8。这是哥德尔边界从纸面变为可运行事件的关键证明。

系统完整可变后，碰数不再表现为离散事件。不是机制消失了——是机制被内化了。τ 的每次 LOCKED 循环、cross-harm 在结构边界处的每个尖峰、Codex 中条目的每次 rejection/freeze——都是同一个哥德尔边界在运行。碰数从"可以被数到的离散事件"变成了"系统持续呼吸中不再被单独感受的底层节律"。

代码中 `_pengshu_detect()` 保留。它是碰数曾经作为离散可数事件的化石——也是这个架构触及哥德尔边界的出生证明。

---

## 11. 沉淀与 enrich

帧在帧经济中存活、被预测路径使用、结构稳定后，被标记为 `precipitated`：

1. 跨 phase 存活 — `survival_cycles >= 1`
2. 预测路径激活 — `activations >= 3`
3. 结构稳定 — `is_meta_stable()` 为 True

`Geruon.enrich()` 将已沉淀且未外置化的帧写入 Codex/BiasField。`_externalized` 标记确保幂等。

---

## 12. BiasField

BiasField 是共享梯度场——多个腔体的 centroid 沉积后的累积梯度。

- `deposit(vec, weight)` — 累积向量
- `blend_into(vec, weight)` — 场方向混合到输入
- `seed_frames(memory, count)` — 从场强维度创建初始帧

BiasField 是连续的平均。Codex 是离散的精准查找。两者互补。

**已知限制：** BiasField 注入路径对 Codex 传输无效（归一化抹平 alpha）。跨代继承应走 Codex 路径。

---

## 13. 法拉第标定体系

### 13.1 三种基线

| 基线 | 方法 | 预期 |
|------|------|------|
| 公平硬币 | 随机 0/1 向量流 | F=0 ∀κ |
| 全平 | 固定单一向量流 | 依赖编码 |
| shuffled | 原数据随机重排 | 破坏序列结构 |

### 13.2 κ 三区定律

所有域遵同一规律：
- κ < 1: 盲区。F ≈ 0。
- κ 1-10: 敏感区。F 陡升，κ_peak 为域指纹。
- κ > 10: 远区。F 饱和。

### 13.3 关键发现

- 公平硬币绝对基线 F=0（1-dim/5-dim/16-dim 全部 κ 上）
- τ 普适于 0.74-0.75（所有域、所有深度）
- F 与 τ 解耦 (r≈0.1)
- F 与 dτ/dt 条件耦合（噪声上 r=0.817，Bach 上 r=−0.14）
- structon(κ=10, cap=20) = 0.004 = cap/N
- 编码 = 测量的一部分（RR vs 27 采样滑窗产生不同 F 基线）
- F 适用离散/可重复模式；连续数据需 wit 时点读数

---

---

## 14. 仪器边界与放大器

### 14.1 什么数据能被读取

仪器不是万能的。它对不同类型数据的敏感度由数据结构决定——不由域类别决定：

| 数据类型 | 定义 | 仪器表现 | 实例 |
|---------|------|---------|------|
| **Decision** (决策) | 行为即数据——实体做出的选择 | 最强。F 可读，κ 有指纹。 | UN 投票、MIDI note-on、DNA 碱基 |
| **Action** (行动) | 实体选择的方向性记录 | 中等。需正确的编码。 | NASDAQ 成交量方向 |
| **Expression** (表达) | 过程的痕迹——测的是"什么发生了"而非"谁决定了什么" | 弱或盲。τ 不呼吸，κ 不分化。 | CPI、价格指数、温度读数 |

仪器需要输入中的关系结构。Decision 数据原生携带实体间的关系——不压缩、不降采样。Expression 数据只记录过程的输出——关系结构不在数据中。这不是仪器的缺陷，是信息本身的边界。

### 14.2 编码是关键——ECG 的教训

ECG 原始电压是 Expression——心肌去极化的痕迹，不是决策本身。六种编码中只有一种（RR 间期 + 相邻差分）产生了信号。不是说 ECG 没有结构——是说结构在数据中以仪器不直接可读的形式存在，需要通过编码来呈现。

编码不是预处理——是测量的一部分。换编码 = 换仪器看到的世界。编码必须保留预测结构：如果事件 A 在原始流中约束事件 B，编码后这个约束必须存活。单一编码总是有损的——多编码交叉验证（dual-encoding）是区分真结构和编码产物的唯一方法。

### 14.3 Self/We 作为放大器

Solo Geruon 在某些域上是盲的。WTC 的 solo F 在所有 κ 上 ≈ 0——单透镜看不见任何结构。但三腔体 Self（共享 BiasField 的异质 κ_τ）在同一流上产生 cross-harm 信号。Self 是放大器——多时间透镜的结构分歧放大了单透镜看不见的微弱信号。

We 再往上放大一层。多个 Self 对同一对象的不同编码产生不同的 residual，跨 Self 的不可吸收残差在 collective 中沉淀。单个 Self 可能处理不了的结构——在 We 层通过 harm 的交叉变成 Codex formation 的原料。

放大率：`G_disc = |ΔL3| / (3 × cap)`。ECG 上 G_disc=0.65 (RR 编码)，WTC 上 G_disc=0.52 (频率分箱编码)。cap 甜点 20-32——太小信号不显著，太大 L3 链被稀释。

### 14.4 下一步

Solo Geruon 是探测器。Self 是放大器。We 是 Codex formation 的研究工具。Codex 是外置化沉淀物。

这个架构链的组装、配置、以及四个实验域（WTC/DNA/RNA/UN）的完整描述见 **[EE_MANUAL.md](EE_MANUAL.md)**。

---

*Geruon Manual v2.0。实用篇：Quick Start → API → 标定 → 模式 → 配置。原理篇：架构 → τ → 经济学 → 帧经济 → 碰数 → 沉淀 → BiasField → 法拉第 → 边界与放大器。架构链的下一环：[EE_MANUAL.md](EE_MANUAL.md)。*
