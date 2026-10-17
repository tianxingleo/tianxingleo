import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


OWNER = "tianxingleo"
ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://tianxingleo.top"

FEATURED_REPOS = [
    {
        "name": "ACGTI",
        "title_en": "ACGTI",
        "title_zh": "ACGTI",
        "desc_en": "A playful ACG personality quiz built with Vue 3 and TypeScript. Reached millions of views and 1k+ GitHub stars.",
        "desc_zh": "基于 Vue 3 / TypeScript 的 ACG 人格测试。从一个晚上的想法开始，累计获得数百万次浏览、1k+ GitHub Stars。",
        "links": [["Live Demo","https://acgti.tianxingleo.top"]],
    },
    {
        "name": "BrainDance",
        "title_en": "BrainDance · 流光·记",
        "title_zh": "BrainDance · 流光·记",
        "desc_en": "Exploring searchable, interactive spatial memories with 3D Gaussian Splatting, scene understanding and retrieval.",
        "desc_zh": "尝试用三维高斯泼溅、场景理解与检索，把生活片段变成可以交互和探索的空间记忆。",
        "links": [],
    },
    {
        "name": "dlut-nihongo-quiz",
        "title_en": "DLUT Study Quiz",
        "title_zh": "大工多学科复习题库",
        "desc_en": "A browser-based study tool with 6,000+ questions spanning Japanese and university courses. Built with Vue 3, Vite and local storage.",
        "desc_zh": "面向日语及多门大学课程的练习工具，收录 6000+ 道题，使用 Vue 3、Vite 与浏览器本地存储。",
        "links": [],
    },
    {
        "name": "Supercore-Site-Pro",
        "title_en": "Supercore Site Pro",
        "title_zh": "Supercore Site Pro",
        "desc_en": "An enterprise website exploring Swiss-inspired design, 3D visualisation and AI-powered semantic search.",
        "desc_zh": "融合瑞士国际主义设计、3D 可视化和 AI 语义搜索的企业网站项目。",
        "links": [["Website","https://supercore.hk"]],
    },
]

RECENT_LIMIT = 5

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
        repo = next((item for item in repos if item["name"] == config["name"]), None)
        if repo is None:
            continue
        cards.append(repo_card(repo, config, lang))

    rows = []
    for i in range(0, len(cards), 2):
        second = cards[i + 1] if i + 1 < len(cards) else '<td width="50%"></td>'
        rows.append(f"<tr>\n{cards[i]}\n{second}\n</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def generate_recent_section(repos: list[dict], lang: str) -> str:
    token = os.getenv("GITHUB_TOKEN")
    items = []
    search_headers = {
        "Accept": "application/vnd.github.cloak-preview+json",
        "User-Agent": "Codex-Profile-Generator",
        **({"Authorization": f"Bearer {token}"} if token else {}),
    }
    req = urllib.request.Request(
        f"https://api.github.com/search/commits?q=author:{OWNER}+user:{OWNER}&sort=author-date&order=desc&per_page=20",
        headers=search_headers,
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        search_result = json.load(resp)

    seen_repos = set()
    recent_commits = []
    for item in search_result.get("items", []):
        repo_name = item["repository"]["name"]
        if repo_name in seen_repos:
            continue
        seen_repos.add(repo_name)
        recent_commits.append(
            {
                "repo_name": repo_name,
                "repo_url": item["repository"]["html_url"],
                "date": item["commit"]["author"]["date"],
                "message": item["commit"]["message"].strip().splitlines()[0],
            }
        )
        if len(recent_commits) >= RECENT_LIMIT:
            break

    for entry in recent_commits:
        created = dt.datetime.fromisoformat(entry["date"].replace("Z", "+00:00")).strftime("%Y-%m-%d")
        if lang == "en":
            header = f'- [{entry["repo_name"]}]({entry["repo_url"]}) · latest commit on {created}'
        else:
            header = f'- [{entry["repo_name"]}]({entry["repo_url"]}) · 最近一次提交于 {created}'
        items.append("\n".join([header, f'  - `{entry["message"]}`']))

    return "\n".join(items)


def replace_between(text: str, marker: str, content: str) -> str:
    start = f"<!-- {marker}:start -->"
    end = f"<!-- {marker}:end -->"
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    return f"{before}{start}\n{content}\n{end}{after}"


def read_existing_section(path: Path, marker: str) -> str:
    text = path.read_text(encoding="utf-8")
    start = f"<!-- {marker}:start -->"
    end = f"<!-- {marker}:end -->"
    _, rest = text.split(start, 1)
    existing, _ = rest.split(end, 1)
    return existing.strip()


def update_file(path: Path, featured: str, recent: str):
    text = path.read_text(encoding="utf-8")
    text = replace_between(text, "featured-projects", featured)
    text = replace_between(text, "recent-activity", recent)
    path.write_text(text, encoding="utf-8")


def main():
    token = os.getenv("GITHUB_TOKEN")
    repos = gh_get(f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=updated", token)
    readme_en = ROOT / "README.md"
    readme_zh = ROOT / "README.zh-CN.md"

    featured_en = generate_featured_section(repos, "en")
    featured_zh = generate_featured_section(repos, "zh")

    try:
        recent_en = generate_recent_section(repos, "en")
        recent_zh = generate_recent_section(repos, "zh")
    except Exception:
        recent_en = read_existing_section(readme_en, "recent-activity")
        recent_zh = read_existing_section(readme_zh, "recent-activity")

    update_file(readme_en, featured_en, recent_en)
    update_file(readme_zh, featured_zh, recent_zh)


if __name__ == "__main__":
    main()
