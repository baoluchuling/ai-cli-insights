from __future__ import annotations

from ..models import AnalyzedData, NarrativeBundle, ReportMeta
from .shared import achieved_counts, build_bundle, friction_text, success_domains_text, top_domains_text


def build_narrative_bundle(data: AnalyzedData, meta: ReportMeta) -> NarrativeBundle:
    claude = data.comparison.get("claude_code", {})
    codex = data.comparison.get("codex_cli", {})
    top_domains = top_domains_text(data)
    friction_line = friction_text(data, n=2, sep=" 和 ")
    efficient_domains = success_domains_text(data)
    achieved, not_achieved = achieved_counts(data)
    top_friction_line = friction_text(data, n=3, sep=", ")

    glance_sections = [
        (
            f"<strong>What's working:</strong> 你已经形成了相当稳定的双工具分工。"
            f"Claude Code 更像判断层，Codex CLI 更像执行层；这一点不只是主观感受，而是直接体现在消息密度、会话长度和工具分布上。"
            f"你最强的地方，不是单次 prompt 写得多准，而是已经在有意识地把不同模型放到不同工作位上。 <a href=\"#section-wins\" class=\"see-more\">Impressive Things You Did →</a>"
        ),
        (
            f"<strong>What's hindering you:</strong> Claude 侧最明显的问题仍是 {friction_text(data)}，"
            f"尤其在调试类任务里，模型一旦先猜再证，就会把你的时间消耗在纠偏上。"
            f"Codex 侧的问题不是不够能做，而是长会话如果没有阶段 checkpoint，回溯成本会不断变高。 <a href=\"#section-friction\" class=\"see-more\">Where Things Go Wrong →</a>"
        ),
        (
            f"<strong>Quick wins to try:</strong> 把跨仓任务统一写成“目标 + 约束 + 验证步骤”的固定模板，"
            f"先让 Claude 收敛方案，再让 Codex 执行并在每个阶段输出小结。"
            f"这类小改动对结果稳定性通常比继续堆更多上下文更有效。 <a href=\"#section-features\" class=\"see-more\">Features to Try →</a>"
        ),
        (
            f"<strong>Ambitious workflows:</strong> 当前高效 session 主要集中在 {efficient_domains}。"
            f"如果后续给 Codex 也补上 outcome/friction 标注，这份报告就能从“谁做了什么”升级成“谁在哪类任务上更稳、更省返工”。"
            f"那时你优化的就不只是使用习惯，而是真正的 AI 工程生产率。 <a href=\"#section-horizon\" class=\"see-more\">On the Horizon →</a>"
        ),
    ]

    usage_narrative = {
        "p1": (
            f"你的使用方式已经明显不是“把 AI 当成一个统一助手”，而是在把不同模型放进不同工作位。"
            f"从统计上看，Claude Code 平均每个 session 只有 {claude.get('avg_user_messages', 0)} 条用户消息，"
            f"而 Codex CLI 达到 {codex.get('avg_user_messages', 0)} 条；Claude 的平均时长是 {claude.get('avg_duration_min', 0)} 分钟，"
            f"Codex 则达到 {codex.get('avg_duration_min', 0)} 分钟。这个差距大到已经不能简单解释为“一个话多一个话少”，"
            f"更像是你有意识地把 Claude 放在判断层，把 Codex 放在执行层。前者更像帮你收敛问题、做 review、定边界，"
            f"后者更像在已经有明确目标之后，持续跑命令、改文件、做验证和推进长链路任务。"
        ),
        "p2": (
            f"这也解释了为什么你的高价值工作会集中在 {top_domains} 这些领域。"
            f"它们并不是最适合“一个模型从头做到尾”的任务，而是天然需要先分析、再施工、最后验证。"
            f"你真正擅长的地方，不是写出某一句非常完美的 prompt，而是能快速判断当前任务更需要“证明”和“约束”，"
            f"还是更需要“推进”和“落地”。这让你更像在编排一个小型工程团队，而不是单纯在和模型对话。"
            f"也正因为这样，你会持续建设 .memory、skills、测试目录和跨工具分析本身，因为你要优化的不是某一次输出，而是整套工作流的长期稳定性。"
        ),
        "p3": (
            f"不过你的使用风格里也有一个很清晰的张力：你愿意给模型高自治，但前提是它必须沿着正确的问题空间前进。"
            f"Claude 侧最明显的摩擦仍然是 {friction_line}，这说明你最不能接受的不是模型做得慢，而是它先猜再证、偏航后还继续推进。"
            f"Codex 侧的问题则不是不够能做，而是长会话一旦缺少阶段 checkpoint，真实进度、剩余风险和返工原因就会被埋进大量执行细节里。"
            f"换句话说，你并不缺工具，也不缺愿意尝试复杂工作流的意愿；你真正持续在优化的，是如何让判断层更严谨、让执行层更可回放。"
        ),
        "key": (
            "你更像一个技术要求很高的编排者，而不是被动的 AI 使用者。"
            "你会把分析、执行、验证拆开，并在模型进入错误轨道时迅速干预；这也是你当前这套双工具工作流最强、也最值得继续工程化的地方。"
        ),
    }

    wins = [
        {
            "title": "双工具协同已经成形",
            "desc": (
                f"Claude 平均每 session {claude.get('avg_user_messages', 0)} 条用户消息，"
                f"Codex 则是 {codex.get('avg_user_messages', 0)} 条。这个差异大到已经不只是使用习惯不同，而是两者天然被你放到了不同工作层。你并不是在随机切换工具，而是在做清晰的分析层与执行层拆分。"
            ),
        },
        {
            "title": "你在主动建设长期记忆和流程基建",
            "desc": "这是一种很少见但非常有效的使用方式。你不只是解决当前问题，还在持续固化 .memory、skills、测试目录规范和使用分析本身，这会直接降低模型每次重新发现项目结构和工作约束的成本。",
        },
        {
            "title": "跨仓移动端任务适合你的当前工作流",
            "desc": "从领域分布看，Flutter 多仓开发、组件化、调试与验证仍是你最值得继续投入的方向。它们本身就适合先分析、后批量执行，而不是在一个长对话里同时做判断、修改和验证。",
        },
    ]

    top_sessions = data.friction_sessions[:3]
    friction_cards = []
    if data.friction_counts:
        friction_cards.append(
            {
                "title": "Speculative Debugging 仍是最大摩擦源",
                "desc": (
                    f"Claude 侧最高频摩擦是 wrong_approach({data.friction_counts.get('wrong_approach', 0)})，"
                    f"其次是 misunderstood_request({data.friction_counts.get('misunderstood_request', 0)})。"
                    "这说明很多失败并不是因为模型完全不会做，而是因为它进入问题空间的方式不够严谨，先猜原因、再找证据，最后把你的时间消耗在纠偏上。"
                ),
                "examples": [
                    (
                        f"{item['project']} | {item['first_prompt'] or '无标题'} | "
                        f"摩擦分 {item['score']} | {item['friction_detail'][:160]}"
                    )
                    for item in top_sessions
                ],
            }
        )
    friction_cards.extend(
        [
            {
                "title": "长会话执行需要阶段性 checkpoint",
                "desc": (
                    "Codex CLI 的强项确实是长链路执行，但长并不天然等于稳。"
                    "如果没有阶段总结、风险列表和下一步确认，越长的会话越容易把真实进度、遗留风险和返工原因混在一起，最后变成难以复盘的施工日志。"
                ),
                "examples": [
                    "适合每个阶段固定输出: 已完成、待验证、阻塞点、下一步。",
                    "对跨仓修改和测试任务，建议每完成一个 repo 或模块就单独结账一次。",
                ],
            },
            {
                "title": "根目录任务会掩盖真实项目上下文",
                "desc": (
                    "很多 session 工作目录停在 home 目录或 workspace 根目录，"
                    "但实际任务落在多个 repo 上。对模型来说，这会增加上下文歧义；对报告来说，这会让项目聚类变得保守甚至失真。"
                ),
                "examples": [
                    "在 prompt 开头直接写目标 repo / 参考实现 / 验证命令。",
                    "把常见项目别名固化进 .memory 或 slash command 模板。",
                ],
            },
        ]
    )

    feature_cards = [
        {
            "title": "固定 Slash Command / Skill 模板",
            "summary": "把跨仓同步、测试校验、组件化迁移和调试起手式写成固定模板，减少每次从零描述上下文。",
            "detail": "你的高价值工作流已经足够重复，完全值得沉淀成模板。这样做的收益不是省几句话，而是把 repo、参考实现、验证命令和边界约束一次性锁死，减少模型偏航。",
            "starter": "先做 2 个最常用模板就够了: 一个给“跨仓同步修复”，一个给“测试计划驱动校验”。不要一开始做太多。",
            "prompt": "把下面这类重复任务固化成一个可复用模板：跨仓同步修复。模板必须固定这些字段：目标 repo、参考实现、改动边界、禁止项、验证命令、最终摘要格式。输出结果请直接给我可复用模板正文。",
        },
        {
            "title": "并行子任务代理",
            "summary": "跨多个 repo 的任务不适合串行硬推，应该拆成每个 repo 一个执行单元。",
            "detail": "尤其是 Flutter 多仓同步、测试比对和差异校验，这类任务最适合一个判断层工具先出统一规范，再让多个执行单元并行推进并回收差异。",
            "starter": "当任务涉及 3 个以上 repo 时，默认先拆成“统一修复说明 + 每个 repo 一个执行单元”的结构，而不是一个长会话从头推到尾。",
            "prompt": "这个任务涉及多个 repo。请先不要串行执行，而是先输出一份统一修复说明，然后把任务拆成每个 repo 一个执行单元。每个执行单元都要包含：目标文件、预期改动、验证命令、异常时的回报格式。",
        },
        {
            "title": "编译/测试门禁循环",
            "summary": "在较大批次改动后自动跑 analyze、测试计划检查和关键 grep，尽早发现回归。",
            "detail": "这类门禁最能降低“改了一堆再回头清理”的成本，也最适合和长会话执行流绑定，因为它能把返工前移到每一批次之后，而不是最后统一爆发。",
            "starter": "先把最轻的门禁加上: 每批改动后跑 `flutter analyze`，再补测试计划检查；不要一开始就上最重的全量验证。",
            "prompt": "我希望这个任务按门禁循环执行。每一批改动后必须先做这些检查：1. 运行 flutter analyze；2. 如果有测试计划，检查对应计划是否覆盖；3. 必要时做关键 grep 校验。只有当前一批检查通过后，才进入下一批修改。",
        },
    ]

    pattern_cards = [
        {
            "title": "先让 Claude 做边界收敛，再让 Codex 做连续施工",
            "summary": "把双工具分工显式化，不要让一个工具同时承担分析和执行两种角色。",
            "detail": "推荐流程: Claude 先输出目标、约束、真实根因、涉及文件和验证方法；Codex 再按这份清单执行修改、运行命令、沉淀结果。这样做的价值不只是分工更清晰，而是能同时压低 wrong_approach 和长会话返工。",
            "starter": "下次遇到跨仓任务时，先要求 Claude 输出 4 项内容: 目标 repo、参考实现、改动边界、验证命令。等这 4 项收敛后，再把同一份清单交给 Codex 执行。",
            "prompt": "先不要直接改代码。先帮我把任务收敛成一份可执行清单，只输出这 4 项：1. 目标 repo/模块；2. 参考实现或对齐来源；3. 改动边界和禁止项；4. 验证命令与通过标准。等这 4 项确认后，我会把同一份清单交给执行层工具继续施工。",
        },
        {
            "title": "调试类任务统一要求证据链",
            "summary": "先要求模型贴住日志和调用链，再进入根因和修复。",
            "detail": "对 crash、构建失败、运行时异常，先要求模型给出日志位置、调用链、相关文件、复现路径，再进入方案。这是最直接命中当前最高频摩擦模式的做法，因为它会强制模型先证明，再判断。",
            "starter": "把调试起手式固定成一句模板: “不要猜，先读实际日志、调用链和相关源代码，再给我根因与最小修复方案。”",
            "prompt": "不要猜。先读实际日志、调用链和相关源代码，再回答我这 4 件事：1. 错误发生在什么位置；2. 触发这条路径的调用链是什么；3. 哪些文件最相关；4. 最小修复方案是什么。在给出这些证据之前，不要直接提出修复建议。",
        },
        {
            "title": "把跨仓任务模板化",
            "summary": "目标 repo、参考实现、改动边界和验证命令都前置写清楚。",
            "detail": "你已经在做多 repo Flutter 协同，最适合的不是临场口述，而是固定格式模板。模板化之后，不只是模型更稳，后续报告也会更容易自动聚类、回放和比较。",
            "starter": "把最常见的 3 类任务先模板化: 多仓同步修复、组件化迁移、测试校验。每个模板至少固定 repo、参考实现、禁止项、验证步骤这四部分。",
            "prompt": "我正在做一个跨仓任务。请按固定模板帮我组织，不要自由发挥。模板必须包含：目标 repo、参考实现、需要修改的文件范围、禁止改动项、验证命令、交付摘要格式。先把模板填完整，再开始执行。",
        },
    ]

    horizon_cards = [
        {"title": "把 outcome / friction 扩展到 Codex", "desc": "只要 Codex 也有结构化成败标注，这份报告就能从“谁做了什么”升级成“谁在哪类任务上更稳、更省返工”，解释力会明显上一个层级。"},
        {"title": "让跨仓修改进入自动校验循环", "desc": "把 flutter analyze、测试计划校验和关键 grep 检查放进固定循环，意味着每次大改动后都能更早暴露回归，而不是等到最后统一返工。"},
        {"title": "做成统一模板生成器", "desc": "现在这份脚本已经把统计和叙事放到一起，下一步自然就是把它继续模板化，让 Claude-only、Codex-only、cross-tool 三类报告共用同一套样式系统和表达节奏。"},
    ]

    return build_bundle(
        glance_sections=glance_sections,
        work_intro=(
            f"你的工作内容并不是平均分布的，而是高度集中在 {top_domains}。"
            f"这很重要，因为这些都不是“问一句、答一句”能结束的任务类型，而是天然要求多阶段推进、跨仓比对、反复验证和流程约束。"
            f"从分工上看，Claude 更常出现在分析、评审和问题收敛阶段，Codex 更常出现在落地、验证和长链路推进阶段；"
            f"也正因为如此，这一节不只是告诉你“做了什么”，而是在回答“什么样的工作最值得继续交给这套双工具工作流”。"
        ),
        usage_narrative=usage_narrative,
        wins_intro="最有价值的不是单次修复本身，而是你已经把多工具、多仓库、多阶段工作流组织成了可复用的方法。",
        wins=wins,
        friction_intro=(
            f"真正拖慢你的，通常不是模型完全不会做，而是它以错误的方式进入问题空间。"
            f"当前最明显的摩擦集中在 {top_friction_line}。与此同时，Claude 侧 fully/mostly achieved 合计 {achieved} 个 session，"
            f"partially/not achieved 合计 {not_achieved} 个 session，这说明你的工作流并不是“模型总是失败”，而是“模型在高价值复杂任务里常常先走偏，再被你拉回正轨”。"
            f"因此这一节最值得看的不是绝对失败数，而是哪些偏航模式在反复出现。"
        ),
        friction_cards=friction_cards,
        feature_intro="这些不是新能力，而是把你已经明显适合的工作流进一步产品化、模板化和自动化。",
        feature_cards=feature_cards,
        pattern_intro="",
        pattern_cards=pattern_cards,
        horizon_intro="如果继续把这套工作流工程化，下一步最值得投入的是让报告、执行和验证进入同一套模板体系。",
        horizon_cards=horizon_cards,
        ending_headline="“你已经不只是把 AI 当助手，而是在把它们编排成工程系统。”",
        ending_detail="真正值得继续优化的，不是哪一个模型更聪明，而是哪一类任务该先分析、哪一类任务该直接施工，以及这些规则能不能被模板化并长期复用。",
    )

