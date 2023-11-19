from collections import namedtuple
from lxml import html
from pandas import DataFrame
from plotly.graph_objects import Scatter
from plotly.subplots import make_subplots
from urllib import request
import plotly.express as px
import sys

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537'}

def crawle_imdb_season(base_url, season) -> list:
    url = base_url+season
    sys.stderr.write(f"Crawling Season {season}.\n")
    Episode = namedtuple('Episode', ['season', 'num', 'name', 'vote', 'rate'])

    req = request.Request(url=url, headers=headers)
    with request.urlopen(req) as response:
        page = response.read()
    tree = html.fromstring(page)
    s_e_n = tree.xpath("//div[@class='ipc-title__text']")
    season = [int(x.text_content().split('.')[0][1:]) for x in s_e_n]
    episode = [int(x.text_content().split('.')[1].split('∙')[0].strip()[1:]) for x in s_e_n]
    name = [x.text_content().split('.')[1].split('∙')[1].strip() for x in s_e_n]
    vote_count_translate = lambda x: int( float(x[:-1])*1000) if 'K' in x else int(x)
    vote = [vote_count_translate(v.text_content()[2:-1]) for v in tree.xpath("//span[@class='ipc-rating-star--voteCount']")]
    rate = [float(x.text_content().split('/')[0]) for x in tree.xpath("//div[@data-testid='ratingGroup--container']")]
    return [Episode(s, e, n, v, r) for (s, e, n, v, r) in
            zip(season, episode, name, vote, rate)]


def crawl_imdb_series(base_url: str, season_count: int) -> list:
    res = []
    for s in range(1, season_count + 1):
        try:
            new_season = crawle_imdb_season(base_url, str(s))
            res += new_season
        except:
            pass
    return res


def plot(series, name) -> None:
    rate_trace = Scatter(
        name='',
        x=series.index,
        y=series['rate'],
        mode='markers',
        marker_color=series['season'],
        marker=dict(size=8),
        customdata=series,
        hovertemplate="<b>%{customdata[2]}</b> <br> S%{customdata[0]}E%{customdata[1]}<br>"
                      "Rate: %{customdata[4]}<br>Vote: %{customdata[3]}",
    )
    count_trace = Scatter(
        name='',
        x=series.index,
        y=series['vote'],
        yaxis='y2',
        line=dict(width=0.6, shape='spline'),
        marker=dict(size=4),
        customdata=series,
        hovertemplate="<b>%{customdata[2]}</b> <br> S%{customdata[0]}E%{customdata[1]}<br>"
                      "Rate: %{customdata[4]}<br>Vote: %{customdata[3]}",
    )
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(rate_trace)
    fig.add_trace(count_trace, secondary_y=True)
    fig.update_traces(showlegend=False,)
    fig.update_layout(
        hoverlabel=dict(
            font_size=16,
        )
    )
    fig.update_layout(template="plotly_dark",
                      title=name,
                      title_font_size=30,
                      title_x=0.5,
                      colorscale_sequential=px.colors.qualitative.Light24
                      )
    fig.update_xaxes(title="Episode")
    fig.update_yaxes(title_text="<b>Rate</b>", secondary_y=False)
    fig.update_yaxes(title_text="<b>Vote Count</b>", secondary_y=True)
    fig.write_html(f"./{name}.html")


def get_season_count(base_url: str) -> int:
    season_count = 0
    req = request.Request(url=base_url, headers=headers)
    with request.urlopen(req) as response:
        page = response.read()
        tree = html.fromstring(page)
        options = tree.xpath("//li[@data-testid='tab-season-entry']")
        try:
            season_count = int(options[-1].text)
        except:
            print("Can't determine season count please enter manually.\n")
            season_count = int(input())
    return season_count


if __name__ == "__main__":
    series_id = sys.argv[1]
    name = sys.argv[2]
    base_url = f"https://www.imdb.com/title/{series_id}/episodes/?season="
    sys.stderr.write("Get Season count.\n")
    season_count = get_season_count(base_url)
    series = DataFrame(data=crawl_imdb_series(base_url, season_count))
    series.index += 1
    plot(series, name)
