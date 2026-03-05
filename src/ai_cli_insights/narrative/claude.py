from __future__ import annotations

from ..models import AnalyzedData, NarrativeBundle, ReportMeta
from .shared import achieved_counts, build_bundle, friction_text, top_domains_text


def build_narrative_bundle(data: AnalyzedData, meta: ReportMeta) -> NarrativeBundle:
    claude = data.comparison.get("claude_code", {})
    top_domains = top_domains_text(data)
    friction_line = friction_text(data)
    achieved, not_achieved = achieved_counts(data)
    top_sessions = data.friction_sessions[:3]

    usage_narrative = {
        "p1": (
            f"从这段时间的数据看，Claude 更像你的判断层和分析入口，而不是施工主力。"
            f"它的平均时长是 {claude.get('avg_duration_min', 0)} 分钟，平均每个 session {claude.get('avg_user_messages', 0)} 条用户消息，"
            "这说明你通常不会和它维持超长执行链路，而是更倾向让它做问题收敛、约束确认、代码审阅和路线判断。"
        ),
        "p2": (
            f"这种使用方式和你的任务结构是匹配的。你做的很多事情都集中在 {top_domains}，"
            "这些任务真正难的不是写一行代码，而是先进入正确的问题空间。Claude 在这里的价值，体现在减少你自己手工梳理边界和证据的成本。"
        ),
        "p3": (
            f"但你的主要张力也几乎都落在这里。{friction_text(data, n=2, sep=' 和 ')} 说明你最不能接受的不是它慢，而是它在信息不全时过早做判断。"
            "所以 Claude 报告真正要回答的，不是“它聪不聪明”，而是“它有没有按你要求的方式先证据、后结论”。"
        ),
        "key": "Claude 最适合被你当成高约束分析层使用；一旦把输出结构和证据链模板固化，它的稳定性会明显高于现在的自由对话形态。",
    }

    wins = [
        {
            "title": "Claude 已经被你固定成判断层",
            "desc": (
                f"平均每个 session {claude.get('avg_user_messages', 0)} 条用户消息、{claude.get('avg_duration_min', 0)} 分钟，"
                "这更像高密度的问题收敛和边界判断，而不是长施工。你并不是拿它当万能工具，而是在用它做真正需要判断的部分。"
            ),
        },
        {
            "title": "高价值工作集中在复杂约束任务",
            "desc": "无论是调试、组件化还是工作流规则收口，Claude 参与的都更像路线选择题。这说明它的价值不是替你批量执行，而是提高你进入正确问题空间的速度。",
        },
        {
            "title": "你已经在围绕 Claude 建立使用护栏",
            "desc": "从 skill、.memory 到固定模板，你已经在主动减少模型偏航。这种投入会直接提升后续每次分析和 review 的稳定性。",
        },
    ]

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
                "title": "复杂约束任务里最怕默认补全你的意图",
                "desc": (
                    "Claude 在审阅和方案判断里很有价值，但一旦它在约束还没收齐前就补全你的目标，"
                    "后面即使技术能力够，也会因为问题定义偏了而返工。"
                ),
                "examples": [
                    "要求它先复述目标、约束、禁止项，再开始分析。",
                    "对调试类任务，强制先列证据链，不允许先写修复方案。",
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
            "title": "固定分析起手式",
            "summary": "把“目标、约束、证据、验证”写成 Claude 默认输入模板。",
            "detail": "对判断层工具来说，起手式越稳定，偏航率越低。尤其是调试和 review，最怕它在信息还不完整时自行补题。",
            "starter": "先做一个通用分析模板，再做一个调试专用模板。",
            "prompt": "请先按固定分析模板工作：目标、约束、证据、相关文件、验证命令。没有填满这些项之前，不要直接给结论。",
        },
        {
            "title": "给 review 输出加硬结构",
            "summary": "让结论、证据和建议稳定落在同一格式里。",
            "detail": "这会直接提升你后续把 Claude 输出转交给执行层或沉淀到报告里的效率。",
            "starter": "统一用“结论 / 证据 / 风险 / 建议 / 验证”五段式。",
            "prompt": "请按五段式输出：结论、证据、风险、建议、验证。每段都必须明确，不要省略。",
        },
        {
            "title": "把高摩擦模式直接写进约束",
            "summary": "针对 wrong_approach 和 misunderstood_request 直接立规矩。",
            "detail": "比起笼统说“更严谨一点”，把高频失败模式翻译成 prompt 规则会更有效。",
            "starter": "在调试、review 和方案判断开头都加一条：先复述约束，再分析。",
            "prompt": "先复述我的目标、约束和禁止项，再开始分析。如果你发现信息不足，只列缺失项，不要自行假设。",
        },
    ]

    pattern_cards = [
        {
            "title": "把 Claude 固定成方案收敛层",
            "summary": "先收敛目标、证据和边界，再把结果交给执行层。",
            "detail": "Claude 的最佳位置不是从头施工到尾，而是把复杂任务先压缩成可执行清单。这样做能直接压低 wrong_approach 和 misunderstood_request。",
            "starter": "遇到复杂任务时，先让 Claude 只做目标澄清、边界确认、相关文件和验证命令收集。",
            "prompt": "先不要给方案，也不要改代码。先把任务收敛成 4 项：目标、约束、相关文件、验证命令。等这 4 项确认后，再进入根因和方案。",
        },
        {
            "title": "所有调试都先走证据链模板",
            "summary": "强制它先贴住日志、调用链和真实文件。",
            "detail": "这条模式最直接命中 Claude 当前的主要摩擦源，因为它会阻止模型过早进入猜测状态。",
            "starter": "把“不要猜，先读证据链”做成默认起手式。",
            "prompt": "不要猜。先读实际日志、调用链和相关源代码，再回答：错误位置、触发路径、相关文件、最小修复方案。",
        },
        {
            "title": "把 review 结果模板化",
            "summary": "让 Claude 的输出结构稳定，减少信息过散。",
            "detail": "对分析型工具来说，稳定的输出格式和稳定的技术判断同样重要，因为后者很依赖前者的组织质量。",
            "starter": "固定输出成：结论、证据、风险、建议、验证。",
            "prompt": "请按固定格式输出：1. 结论；2. 证据；3. 风险；4. 建议；5. 验证方式。不要自由组织结构。",
        },
    ]

    horizon_cards = [
        {"title": "把 Claude 输出结构进一步硬模板化", "desc": "如果 review、调试和路线判断都统一成固定输出格式，Claude 的稳定性会比继续堆上下文更快提升。"},
        {"title": "将摩擦模式反向写进 prompt 规则", "desc": "把 wrong_approach、misunderstood_request 这些高频摩擦直接转成模板约束，能让报告和真实使用闭环。"},
        {"title": "把 Claude 变成跨工具统一入口", "desc": "先由 Claude 生成执行单，再分发给 Codex 或其他执行层，能把你的分析流程进一步产品化。"},
    ]

    return build_bundle(
        glance_sections=[
            (
                f"<strong>What's working:</strong> Claude 仍然最适合做高约束场景下的判断层工作。"
                f"从当前数据看，它更像你的问题收敛器、审阅台和路线选择器，而不是持续施工工具。 <a href=\"#section-wins\" class=\"see-more\">Impressive Things You Did →</a>"
            ),
            (
                f"<strong>What's hindering you:</strong> 最主要的阻力仍然是 {friction_line}。"
                f"一旦 Claude 在调试或复杂约束任务里先猜再证，你的时间就会消耗在纠偏而不是推进。 <a href=\"#section-friction\" class=\"see-more\">Where Things Go Wrong →</a>"
            ),
            (
                f"<strong>Quick wins to try:</strong> 把所有调试起手式都改成“先证据、后判断”，并要求它在开始前先列目标文件、调用链和验证命令。 <a href=\"#section-features\" class=\"see-more\">Features to Try →</a>"
            ),
            (
                f"<strong>Ambitious workflows:</strong> 如果把 Claude 固定为方案收敛层，并把输出格式模板化，它会更像一个稳定的技术分析入口，而不是偶尔好用的聊天窗口。 <a href=\"#section-horizon\" class=\"see-more\">On the Horizon →</a>"
            ),
        ],
        work_intro=(
            f"Claude 参与的工作高度集中在 {top_domains}。这些都不是纯执行问题，而是需要先收敛边界、识别风险、再决定是否值得继续推进的任务类型。"
            "所以这一节真正要看的，不只是它做了哪些事，而是它更适合替你承担哪些判断成本。"
        ),
        usage_narrative=usage_narrative,
        wins_intro="这一版只看 Claude，所以这里更像一份分析师报告。重点不是它做了多少执行，而是它在判断层、review 和问题收敛上到底替你节省了多少认知成本。",
        wins=wins,
        friction_intro=(
            f"真正拖慢 Claude 的，通常不是能力缺失，而是它以错误方式进入问题空间。当前最明显的摩擦集中在 {friction_text(data, n=3, sep=', ')}。"
            f"与此同时，fully/mostly achieved 合计 {achieved} 个 session，partially/not achieved 合计 {not_achieved} 个 session，"
            "说明它并不是经常彻底失败，而是常常先偏航，再被你拉回来。"
        ),
        friction_cards=friction_cards,
        feature_intro="这些建议都围绕一个目标: 让 Claude 的分析过程更稳定、更少偏航，而不是继续扩大自由发挥空间。它们更像分析规程，而不是功能清单。",
        feature_cards=feature_cards,
        pattern_intro="下面这些模式不是额外功能，而是把 Claude 明确固定到“分析层”这个角色里，让每次输出都更像有证据的判断稿。",
        pattern_cards=pattern_cards,
        horizon_intro="如果继续优化 Claude 的工作位，重点应该放在结构化输出和高摩擦模式约束，而不是单纯追加更多上下文。",
        horizon_cards=horizon_cards,
        ending_headline="“Claude 最适合做你高约束工作流里的判断层，而不是自由发挥型助手。”",
        ending_detail="继续优化它的关键，不是让它说得更多，而是让它更稳定地先复述目标、后建立证据、再给结论。",
    )
