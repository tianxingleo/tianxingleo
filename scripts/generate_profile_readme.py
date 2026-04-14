import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


OWNER = "tianxingleo"
ROOT = Path(__file__).resolve().parents[1]

FEATURED_REPOS = [
    {
        "name": "ACGTI",
        "title_en": "ACGTI",
        "title_zh": "ACGTI",
        "desc_en": "An ACG-themed personality test project with strong character-driven interaction and shareable product presentation.",
        "desc_zh": "一个偏角色化互动与产品表达的 ACG 主题人格测试项目。",
        "links": [("Live Demo", "https://acgti.tianxingleo.top")],
    },
    {
        "name": "BrainDance",
        "title_en": "BrainDance",
        "title_zh": "BrainDance",
        "desc_en": "An AI project line around reconstruction, semantic understanding, retrieval, and interactive memory experiences.",
        "desc_zh": "围绕重建、语义理解、检索与交互式记忆体验展开的 AI 项目方向。",
        "links": [],
    },
    {
        "name": "school-runing-dut",
        "title_en": "DUT Campus Run Script",
        "title_zh": "DUT 校园跑脚本",
        "desc_en": "A campus running automation script built for the DUT Development Zone campus, focused on practical workflow automation.",
        "desc_zh": "面向大连理工大学开发区校区校园跑场景的自动化脚本项目，强调实用性和流程自动化。",
        "links": [],
    },
    {
        "name": "Supercore-Site-Pro",
        "title_en": "Supercore Site Pro",
        "title_zh": "Supercore Site Pro",
        "desc_en": "A Swiss-style enterprise site with 3D presentation and AI-assisted product communication.",
        "desc_zh": "一个带有 3D 展示与 AI 辅助表达的瑞士风企业官网项目。",
        "links": [("Website", "https://supercore.hk")],
    },
]

RECENT_LIMIT = 5
EXCLUDED_RECENT = {"tianxingleo", "angular", "BrainDance"}


def gh_get(url: str, token: str | None):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Codex-Profile-Generator",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def badge(url: str, alt: str) -> str:
    return f'<img src="{url}" alt="{alt}" />'


def static_badge(label: str, message: str, color: str) -> str:
    label_q = urllib.parse.quote(label)
    message_q = urllib.parse.quote(message.replace("-", "--"))
    return f"https://img.shields.io/badge/{label_q}-{message_q}-{color}?style=flat-square"


def repo_card(repo: dict, config: dict, lang: str) -> str:
    name = repo["name"]
    title = config["title_en"] if lang == "en" else config["title_zh"]
    repo_url = repo["html_url"]
    homepage = repo.get("homepage") or ""
    desc = config["desc_en"] if lang == "en" else config["desc_zh"]
    primary_language = repo.get("language") or ("Unknown" if lang == "en" else "待识别")
    badges = " ".join(
        [
            badge(
                f"https://img.shields.io/github/stars/{OWNER}/{name}?style=flat-square&color=2563eb",
                f"{name} stars",
            ),
            badge(
                f"https://img.shields.io/github/last-commit/{OWNER}/{name}?style=flat-square&color=0f172a",
                f"{name} last commit",
            ),
            badge(static_badge("language", primary_language, "1d4ed8"), f"{name} language"),
        ]
    )

    link_items = [f'<a href="{repo_url}">Repository</a>' if lang == "en" else f'<a href="{repo_url}">仓库</a>']
    for label, url in config["links"]:
        link_items.append(f'<a href="{url}">{label}</a>' if lang == "en" else f'<a href="{url}">{ "在线访问" if label == "Live Demo" else "网站" }</a>')
    links_html = " · ".join(link_items)

    return f"""
<td width="50%" valign="top">
  <strong><a href="{repo_url}">{title}</a></strong><br />
  {desc}<br /><br />
  {badges}<br /><br />
  {links_html}
</td>""".strip()


def generate_featured_section(repos: list[dict], lang: str) -> str:
    cards = []
    for config in FEATURED_REPOS:
        repo = next(item for item in repos if item["name"] == config["name"])
        cards.append(repo_card(repo, config, lang))

    rows = []
    for i in range(0, len(cards), 2):
        second = cards[i + 1] if i + 1 < len(cards) else '<td width="50%"></td>'
        rows.append(f"<tr>\n{cards[i]}\n{second}\n</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def generate_recent_section(repos: list[dict], lang: str) -> str:
    items = []
    visible = [
        repo
        for repo in repos
        if not repo.get("fork")
        and repo["name"] not in EXCLUDED_RECENT
        and repo["name"] not in {cfg["name"] for cfg in FEATURED_REPOS}
    ]
    visible.sort(key=lambda repo: repo["pushed_at"], reverse=True)

    for repo in visible[:RECENT_LIMIT]:
        pushed = dt.datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00")).strftime("%Y-%m-%d")
        desc = repo.get("description") or ("No description yet." if lang == "en" else "暂时还没有补充简介。")
        if lang == "en":
            if desc.isascii():
                items.append(f'- [{repo["name"]}]({repo["html_url"]}) · updated {pushed}  \n  {desc}')
            else:
                items.append(f'- [{repo["name"]}]({repo["html_url"]}) · updated {pushed}')
        else:
            items.append(f'- [{repo["name"]}]({repo["html_url"]}) · 更新于 {pushed}  \n  {desc}')

    return "\n".join(items)


def replace_between(text: str, marker: str, content: str) -> str:
    start = f"<!-- {marker}:start -->"
    end = f"<!-- {marker}:end -->"
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    return f"{before}{start}\n{content}\n{end}{after}"


def update_file(path: Path, featured: str, recent: str):
    text = path.read_text(encoding="utf-8")
    text = replace_between(text, "featured-projects", featured)
    text = replace_between(text, "recent-activity", recent)
    path.write_text(text, encoding="utf-8")


def main():
    token = os.getenv("GITHUB_TOKEN")
    repos = gh_get(f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=updated", token)

    update_file(ROOT / "README.md", generate_featured_section(repos, "en"), generate_recent_section(repos, "en"))
    update_file(ROOT / "README.zh-CN.md", generate_featured_section(repos, "zh"), generate_recent_section(repos, "zh"))


if __name__ == "__main__":
    main()
