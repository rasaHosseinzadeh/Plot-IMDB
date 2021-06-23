from collections import namedtuple
from lxml import html
from pandas import DataFrame
from plotly.graph_objects import Scatter
from plotly.subplots import make_subplots
from urllib import request
import plotly.express as px
import sys


def crawle_imdb_season(base_url, season) -> list:
    url = base_url+season
    sys.stderr.write(f"Crawling Season {season}.\n")
    Episode = namedtuple('Episode', ['season', 'num', 'name', 'vote', 'rate'])
    with request.urlopen(url) as response:
        page = response.read()
        tree = html.fromstring(page)
        s_ep = (
            (int(x.text.split(",")[0][1:]),
             int(x.text.split(",")[1][3:])) for x in
            tree.xpath('//*[contains(@class,"zero-z-index")]//div'))
        name = (x.text for x in
                tree.xpath("//div[contains(@class,'eplist')]//strong/a"))
        vote = (int(x.text.translate({ord(c): None for c in "(),"})) for x in
                tree.xpath("//span[@class='ipl-rating-star__total-votes']"))
        rating = (float(x.text) for x in
                  tree.xpath("//div/div[1]/span[@class='ipl-rating-star__rating']"))
    return (Episode(s, e, n, v, r) for ((s, e), n, v, r) in
            zip(s_ep, name, vote, rating))


def crawl_imdb_series(base_url: str, season_count: int) -> list:
    return (eps for i in range(1, season_count + 1) for eps in
            crawle_imdb_season(base_url, str(i)))


def get_season_count(base_url: str) -> int:
    season_count = 0
    with request.urlopen(base_url+"0") as response:
        page = response.read()
        tree = html.fromstring(page)
        options = tree.xpath("//select[@id='bySeason']//option")
        try:
            season_count = int(options[-1].text)
        except:
            print("Can't determine season count please enter manually.\n")
            season_count = int(input())
    return season_count


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
            bgcolor="white",
            font_size=16,
        )
    )
    fig.update_layout(template="plotly_dark",
                      title=name,
                      title_font_size=30,
                      title_x=0.5,
                      colorscale_sequential=px.colors.qualitative.Light24,)
    fig.update_xaxes(title="Episode")
    fig.update_yaxes(title_text="<b>Rate</b>", secondary_y=False)
    fig.update_yaxes(title_text="<b>Vote Count</b>", secondary_y=True)
    fig.write_html(f"./{name}.html")


if __name__ == "__main__":
    series_id = sys.argv[1]
    name = sys.argv[2]
    base_url = "https://www.imdb.com/title/{}/episodes?season=".format(
        series_id)
    sys.stderr.write("Get Season count.\n")
    season_count = get_season_count(base_url)
    series = DataFrame(data=crawl_imdb_series(base_url, season_count))
    series.index += 1
    plot(series, name)
