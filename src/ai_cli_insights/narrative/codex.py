from __future__ import annotations

from ..models import AnalyzedData, NarrativeBundle, ReportMeta
from .shared import build_bundle, codex_archetype_line, top_domains_text


def build_narrative_bundle(data: AnalyzedData, meta: ReportMeta) -> NarrativeBundle:
    codex = data.comparison.get("codex_cli", {})
    top_domains = top_domains_text(data)
    archetype_line = codex_archetype_line(data)

    usage_narrative = {
        "p1": (
            f"Codex 的使用画像非常明确: 它不是你的第二个聊天窗口，而是持续施工位。"
            f"平均每个 session {codex.get('avg_user_messages', 0)} 条用户消息、{codex.get('avg_duration_min', 0)} 分钟，"
            "说明你经常让它围绕同一个目标长时间推进命令、补丁和验证。"
        ),
        "p2": (
            f"从工具和 archetype 看，当前最典型的模式是 {archetype_line}。"
            "这意味着你已经在用它承担真正的实施工作，包括多文件修改、命令观察、测试和收尾，而不只是做信息查询。"
        ),
        "p3": (
            "这类使用方式的核心张力不在于分析是否正确，而在于执行是否可回放。"
            "如果阶段边界不清、总结不够硬，长会话后半段就会越来越像施工日志，而不是可复用流程。"
        ),
        "key": "Codex 的价值已经稳定在执行层；下一步最值得补的不是更多能力，而是更强的阶段协议和结构化质量标注。",
    }

    wins = [
        {
            "title": "Codex 已经进入持续施工位",
            "desc": (
                f"平均每个 session {codex.get('avg_user_messages', 0)} 条用户消息、{codex.get('avg_duration_min', 0)} 分钟，"
                "这不是问答型使用，而是明确的长链路执行流。"
            ),
        },
        {
            "title": "多文件改动和命令推进是当前强项",
            "desc": "从工具分布看，Codex 的主要价值在于命令执行、补丁落地和过程轮询。这很适合承担跨仓施工、批量修复和验证收尾。",
        },
        {
            "title": "你已经在把执行过程沉淀成可复用流程",
            "desc": "报告、模板、测试计划和阶段总结这些做法，说明你不是让 Codex 临场发挥，而是在把它工程化成可复用执行层。",
        },
    ]

    friction_cards = [
        {
            "title": "长会话执行需要阶段性 checkpoint",
            "desc": (
                "Codex CLI 的强项确实是长链路执行，但长并不天然等于稳。"
                "如果没有阶段总结、风险列表和下一步确认，越长的会话越容易把真实进度、遗留风险和返工原因混在一起。"
            ),
            "examples": [
                "适合每个阶段固定输出: 已完成、待验证、阻塞点、下一步。",
                "对跨仓修改和测试任务，建议每完成一个 repo 或模块就单独结账一次。",
            ],
        },
        {
            "title": "执行上下文如果过宽，报告解释力会变弱",
            "desc": (
                "很多 Codex session 工作目录停在 workspace 根目录，实际却在多个 repo 内推进。"
                "这会让后续回放、聚类和问题归因都变得保守。"
            ),
            "examples": [
                "任务开头显式写目标 repo、目标模块和验证命令。",
                "跨仓施工时，每个 repo 单独输出阶段结论。",
            ],
        },
    ]

    feature_cards = [
        {
            "title": "固定阶段总结协议",
            "summary": "让每段执行都能被回放，而不是只在终局汇总。",
            "detail": "这会同时提升执行可控性和报告质量，因为阶段信息不再埋在长输出里。",
            "starter": "先给所有长会话统一一个四项小结模板。",
            "prompt": "从现在开始，每完成一个阶段都输出固定小结：已完成、已验证、剩余风险、下一步。",
        },
        {
            "title": "把多 repo 执行拆成并行单元",
            "summary": "避免一个长会话同时维护多个仓库的状态。",
            "detail": "对执行层工具来说，repo 边界越清楚，返工和回放成本越低。",
            "starter": "任务涉及 3 个以上 repo 时，默认一 repo 一单元。",
            "prompt": "请先把这个多 repo 执行任务拆成并行单元，每个单元单独写目标文件、改动范围、验证命令和结束条件。",
        },
        {
            "title": "把验证前移到每批改动后",
            "summary": "不要把 analyze 和检查堆到最后一次性做。",
            "detail": "这能直接降低长链路执行后期的回归爆炸风险。",
            "starter": "先从 analyze + 关键 grep 开始，不必一上来就做最重验证。",
            "prompt": "我希望这个任务按门禁循环执行。每一批改动后先做 analyze、关键 grep 和必要检查，只有通过后才进入下一批。",
        },
    ]

    pattern_cards = [
        {
            "title": "执行前先锁定阶段边界",
            "summary": "不要让一个长会话同时承载太多目标。",
            "detail": "Codex 的优势是持续推进，但如果阶段边界不清，执行效率会被后期整理成本吃掉。",
            "starter": "把任务切成阶段，每个阶段只包含一个 repo 或一类验证。",
            "prompt": "先不要直接连做到底。先把这次执行拆成阶段列表，每个阶段写清目标文件、预期改动、验证命令和结束条件。",
        },
        {
            "title": "每批改动后强制阶段总结",
            "summary": "把可回放性嵌入执行流，而不是事后补。",
            "detail": "长执行流最大的风险不是改不完，而是事后说不清到底改了什么、验证到哪一步、风险还剩什么。",
            "starter": "每完成一批文件或一个 repo，就输出一次固定小结。",
            "prompt": "从现在开始，每完成一批改动后都输出固定小结：已改文件、已完成验证、未解决风险、下一步。",
        },
        {
            "title": "让 Codex 只负责施工，不负责改需求",
            "summary": "执行层要少做需求补全，多做约束内落地。",
            "detail": "当执行工具开始自己补全目标时，返工成本通常比分析层偏航还高，因为已经产生了真实修改和验证开销。",
            "starter": "把目标、禁止项和通过标准写死在开头。",
            "prompt": "按我给出的目标和边界执行，不要自行扩展需求。若发现边界不足，只输出缺失项和影响，不要自行决定新增改动。",
        },
    ]

    horizon_cards = [
        {"title": "给 Codex 增加 outcome / friction 标注", "desc": "一旦执行层也有结构化成败标记，你就能判断它在哪类任务上最稳，而不只是最忙。"},
        {"title": "把阶段总结变成默认协议", "desc": "如果每个长会话都自动输出阶段结论，后续复盘、切换工具和报告生成都会更准确。"},
        {"title": "让验证链路进入标准化模板", "desc": "把 analyze、测试和关键 grep 绑定到阶段边界，会让执行层更像一条稳定流水线。"},
    ]

    return build_bundle(
        glance_sections=[
            (
                f"<strong>What's working:</strong> Codex 明显已经被你用成持续施工工具。"
                f"无论是 active_minutes、命令密度还是补丁次数，都说明它承担的是推进和落地，而不是短问答。 <a href=\"#section-wins\" class=\"see-more\">Impressive Things You Did →</a>"
            ),
            (
                f"<strong>What's hindering you:</strong> 当前最大风险不是“做不动”，而是长会话里缺少阶段 checkpoint。"
                f"这会让 {archetype_line} 这种强执行模式在后半段越来越难回放。 <a href=\"#section-friction\" class=\"see-more\">Where Things Go Wrong →</a>"
            ),
            (
                f"<strong>Quick wins to try:</strong> 每完成一批文件或一个 repo，就强制输出阶段总结、验证状态和剩余风险。 <a href=\"#section-features\" class=\"see-more\">Features to Try →</a>"
            ),
            (
                f"<strong>Ambitious workflows:</strong> 如果后续补上 Codex 的 outcome/friction 标注，你就能把执行质量也结构化，而不是只看工作量。 <a href=\"#section-horizon\" class=\"see-more\">On the Horizon →</a>"
            ),
        ],
        work_intro=(
            f"Codex 参与的工作同样高度集中在 {top_domains}，但它承担的角色更偏实施与推进。"
            "这一节重点不是“你在问什么”，而是“哪些任务已经被你稳定交给执行层，以及这种分工是否足够清晰”。"
        ),
        usage_narrative=usage_narrative,
        wins_intro="这一版只看 Codex，所以这里更像一张执行看板。重点不是路线判断，而是执行层是否已经被你训练成稳定、可切换、可回放的施工系统。",
        wins=wins,
        friction_intro="Codex 当前没有和 Claude 对等的 friction / outcome 标注，所以这里更多是在根据执行形态反推风险模式。重点不是失败计数，而是哪些使用方式会让长会话越来越难回放。",
        friction_cards=friction_cards,
        feature_intro="这些建议都围绕执行层治理: 阶段边界、验证循环和回放能力。它们更像运行手册，而不是泛化建议。",
        feature_cards=feature_cards,
        pattern_intro="下面这些模式的目标是让 Codex 的长链路执行更可控，让每一段推进都更像一个可以单独结账的施工阶段。",
        pattern_cards=pattern_cards,
        horizon_intro="如果继续优化 Codex 的工作位，最值得投入的是结构化质量标注和标准化阶段协议。",
        horizon_cards=horizon_cards,
        ending_headline="“Codex 已经不只是执行工具，而是你持续施工流程里的操作层。”",
        ending_detail="下一步最重要的，不是再让它做更多，而是让每一段执行都更容易被回放、切换和评估。",
    )
