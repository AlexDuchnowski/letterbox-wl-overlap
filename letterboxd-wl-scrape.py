import argparse
import math
from collections import defaultdict

from bs4 import BeautifulSoup as bs
from selenium import webdriver


def pull_url(url: str, verbose: bool) -> list[str]:
    STANDARD_PAGE_SIZE = 28

    browser = webdriver.Chrome()

    browser.get(url)
    html = browser.page_source
    soup = bs(html, "html.parser")

    total_count = int(
        soup.find("h1", attrs={"class": "section-heading"}).get_text().split()[-2]
    )

    page_count = math.ceil(total_count / STANDARD_PAGE_SIZE)

    movie_list = []

    for i in range(1, page_count + 1):
        if verbose:
            print(f"Loading page {i} of {page_count}...")
        browser.get(url + "/page/" + str(i))
        html = browser.page_source
        soup = bs(html, "html.parser")
        table = soup.find("ul", attrs={"class": "poster-list"}).find_all("li")
        for cell in table:
            movie_list.append(
                cell.find("div", attrs={"class": "poster"}).get("data-film-slug")
            )

    browser.quit()

    return movie_list


def process_friends(friend_list: list[str], verbose: bool) -> list[list[str]]:
    movie_bag = []

    for name in friend_list:
        if verbose:
            print(f"Loading {name}'s watchlist...")
        search_path = "https://letterboxd.com/" + name + "/watchlist/"
        movie_bag.append(pull_url(search_path, verbose=verbose))
        if verbose:
            print("*" * 40 + "\n")

    if verbose:
        print("Loading complete.")

    return movie_bag


def find_films_in_common(
    friends: list[str],
    film_bag: list[list[str]],
    all: bool,
    output_file: str,
    verbose: bool,
) -> None:
    film_dict = defaultdict(int)

    for friend, wishlist in zip(friends, film_bag):
        if verbose:
            print(f"Processing {friend}'s watchlist...")
        for slug in wishlist:
            film_dict[slug] += 1

    if verbose:
        print("Processing complete.")
        print("Sorting results...", end="\r")

    if all:
        overlaps = [(k, v) for k, v in film_dict.items() if v == len(film_bag)]
    else:
        overlaps = sorted(film_dict.items(), key=lambda t: t[1], reverse=True)

    if verbose:
        print("Sorting complete.".ljust(30))
        print("Writing results...", end="\r")

    with open(output_file, "w") as f:
        for slug, count in overlaps:
            f.write(
                f"{count} {slug.replace('-',' ').title()} (https://letterboxd.com/film/{slug}/)\n"
            )

    if verbose:
        print(f"Results written to {output_file}.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--friends", help="List of friends' usernames", nargs="+", required=True
    )
    parser.add_argument(
        "-o", "--output", help="Output filename", default="movies-in-common.txt"
    )
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    parser.add_argument(
        "-a",
        "--all",
        help="Only output movies that are on all lists",
        action="store_true",
    )
    args = parser.parse_args()

    bag = process_friends(args.friends, args.verbose)
    find_films_in_common(args.friends, bag, args.all, args.output, args.verbose)


if __name__ == "__main__":
    main()
