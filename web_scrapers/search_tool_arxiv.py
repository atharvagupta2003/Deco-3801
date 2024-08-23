import arxiv


def search_arxiv(query):
    print(f"Searching ArXiv for: {query}")

    # Initialize the client
    client = arxiv.Client()

    # Perform the search
    results = client.results(arxiv.Search(
        query=query,
        max_results=5, 
        sort_by=arxiv.SortCriterion.Relevance,
    ))

    papers = []
    for result in results:
        papers.append({
            'title': result.title,
            'summary': result.summary,
            'url': result.entry_id,
            'published': result.published,
        })
    return papers


def main():
    query = input("Enter your search query: ")
    results = search_arxiv(query)

    if results:
        print("\nRelevant papers found:")
        for i, paper in enumerate(results):
            print(f"{i + 1}) {paper['title']}")
            print(f"   Summary: {paper['summary']}")
            print(f"   Published: {paper['published']}")
            print(f"   URL: {paper['url']}\n")
    else:
        print("No relevant papers found.")


if __name__ == '__main__':
    main()
